from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.voucher import Voucher, VoucherItem
from app.models.bill import Bill
from app.repositories.base import BaseRepository
from app.services.state_machine import VoucherStateMachine
from app.agents.voucher_agent import VoucherAgent
from app.schemas.voucher import (
    VoucherCreate, VoucherUpdate, VoucherResponse,
    VoucherListResponse, VoucherGenerateRequest
)

router = APIRouter(prefix="/vouchers", tags=["凭证"])
voucher_repo = BaseRepository(Voucher)


# 会计科目数据
ACCOUNTS = [
    {"code": "1001", "name": "库存现金", "category": "资产"},
    {"code": "1002", "name": "银行存款", "category": "资产"},
    {"code": "1122", "name": "应收账款", "category": "资产"},
    {"code": "1403", "name": "原材料", "category": "资产"},
    {"code": "1405", "name": "库存商品", "category": "资产"},
    {"code": "1601", "name": "固定资产", "category": "资产"},
    {"code": "2001", "name": "短期借款", "category": "负债"},
    {"code": "2202", "name": "应付账款", "category": "负债"},
    {"code": "2221", "name": "应交税费", "category": "负债"},
    {"code": "4001", "name": "实收资本", "category": "权益"},
    {"code": "4103", "name": "本年利润", "category": "权益"},
    {"code": "4104", "name": "利润分配", "category": "权益"},
    {"code": "5001", "name": "生产成本", "category": "成本"},
    {"code": "6001", "name": "主营业务收入", "category": "损益"},
    {"code": "6051", "name": "其他业务收入", "category": "损益"},
    {"code": "6401", "name": "主营业务成本", "category": "损益"},
    {"code": "6403", "name": "税金及附加", "category": "损益"},
    {"code": "6601", "name": "销售费用", "category": "损益"},
    {"code": "6602", "name": "管理费用", "category": "损益"},
    {"code": "6603", "name": "财务费用", "category": "损益"},
]


# 记账规则数据
RULES = [
    {"id": "rule_001", "name": "采购入库", "description": "采购商品入库", "entries": [
        {"subject_code": "1405", "subject_name": "库存商品", "debit": "{amount}", "credit": "0", "summary": "采购商品"},
        {"subject_code": "2221", "subject_name": "应交税费", "debit": "{tax}", "credit": "0", "summary": "进项税额"},
        {"subject_code": "2202", "subject_name": "应付账款", "debit": "0", "credit": "{total}", "summary": "应付货款"}
    ]},
    {"id": "rule_002", "name": "销售出库", "description": "销售商品出库", "entries": [
        {"subject_code": "1122", "subject_name": "应收账款", "debit": "{total}", "credit": "0", "summary": "应收货款"},
        {"subject_code": "6001", "subject_name": "主营业务收入", "debit": "0", "credit": "{amount}", "summary": "销售收入"},
        {"subject_code": "2221", "subject_name": "应交税费", "debit": "0", "credit": "{tax}", "summary": "销项税额"}
    ]},
    {"id": "rule_003", "name": "费用报销", "description": "管理费用报销", "entries": [
        {"subject_code": "6602", "subject_name": "管理费用", "debit": "{amount}", "credit": "0", "summary": "管理费用"},
        {"subject_code": "1001", "subject_name": "库存现金", "debit": "0", "credit": "{amount}", "summary": "现金支付"}
    ]},
]


@router.get("/accounts")
async def get_accounts(
    category: Optional[str] = None,
    current_user=Depends(require_permission("vouchers:read"))
):
    """获取会计科目列表"""
    items = ACCOUNTS
    if category:
        items = [a for a in items if a["category"] == category]
    return success_response(data={"items": items})


@router.get("/rules")
async def get_rules(
    current_user=Depends(require_permission("vouchers:read"))
):
    """获取记账规则列表"""
    return success_response(data={"items": RULES})


@router.get("")
async def list_vouchers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态过滤"),
    period: Optional[str] = Query(None, description="会计期间"),
    current_user=Depends(require_permission("vouchers:read")),
    db: Session = Depends(get_db)
):
    """获取凭证列表"""
    skip = (page - 1) * page_size
    
    # 构建过滤器
    filters = {}
    if current_user.role != "admin":
        filters["customer_id"] = current_user.customer_id
    if status:
        filters["status"] = status
    if period:
        filters["period"] = period
    
    # 查询数据
    vouchers = voucher_repo.get_multi(
        db, skip=skip, limit=page_size,
        filters=filters, order_by="created_at"
    )
    total = voucher_repo.count(db, filters=filters)
    
    # 转换为响应格式
    items = []
    for voucher in vouchers:
        items.append({
            "id": str(voucher.id),
            "customer_id": str(voucher.customer_id) if voucher.customer_id else None,
            "voucher_no": voucher.voucher_no,
            "voucher_date": voucher.voucher_date.isoformat() if voucher.voucher_date else None,
            "period": voucher.period,
            "summary": voucher.summary,
            "ai_confidence": float(voucher.ai_confidence) if voucher.ai_confidence else None,
            "ai_reason": voucher.ai_reason,
            "status": voucher.status,
            "assigned_to": str(voucher.assigned_to) if voucher.assigned_to else None,
            "auditor_id": str(voucher.auditor_id) if voucher.auditor_id else None,
            "audited_at": voucher.audited_at.isoformat() if voucher.audited_at else None,
            "created_at": voucher.created_at.isoformat() if voucher.created_at else "",
            "updated_at": voucher.updated_at.isoformat() if voucher.updated_at else ""
        })
    
    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    })


@router.get("/{voucher_id}")
async def get_voucher(
    voucher_id: str,
    current_user=Depends(require_permission("vouchers:read")),
    db: Session = Depends(get_db)
):
    """获取凭证详情"""
    voucher = voucher_repo.get(db, voucher_id)
    if not voucher:
        return error_response(404, "凭证不存在")
    
    # 检查权限
    if str(voucher.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权访问此凭证")
    
    # 构建明细项
    items = []
    for item in voucher.items:
        items.append({
            "id": str(item.id),
            "voucher_id": str(item.voucher_id),
            "line_no": item.line_no,
            "subject_code": item.subject_code,
            "subject_name": item.subject_name,
            "debit_amount": float(item.debit_amount) if item.debit_amount else 0,
            "credit_amount": float(item.credit_amount) if item.credit_amount else 0,
            "summary": item.summary
        })
    
    return success_response(data={
        "id": str(voucher.id),
        "customer_id": str(voucher.customer_id) if voucher.customer_id else None,
        "voucher_no": voucher.voucher_no,
        "voucher_date": voucher.voucher_date.isoformat() if voucher.voucher_date else None,
        "period": voucher.period,
        "summary": voucher.summary,
        "ai_confidence": float(voucher.ai_confidence) if voucher.ai_confidence else None,
        "ai_reason": voucher.ai_reason,
        "status": voucher.status,
        "assigned_to": str(voucher.assigned_to) if voucher.assigned_to else None,
        "auditor_id": str(voucher.auditor_id) if voucher.auditor_id else None,
        "audited_at": voucher.audited_at.isoformat() if voucher.audited_at else None,
        "items": items,
        "created_at": voucher.created_at.isoformat() if voucher.created_at else "",
        "updated_at": voucher.updated_at.isoformat() if voucher.updated_at else ""
    })


@router.post("/generate")
async def generate_vouchers(
    request: VoucherGenerateRequest,
    current_user=Depends(require_permission("vouchers:create")),
    db: Session = Depends(get_db)
):
    """从票据批量生成凭证"""
    voucher_agent = VoucherAgent()
    generated_ids = []
    failed_items = []
    
    for bill_id in request.bill_ids:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            failed_items.append({"id": bill_id, "reason": "票据不存在"})
            continue
        
        # 检查权限
        if str(bill.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
            failed_items.append({"id": bill_id, "reason": "无权访问此票据"})
            continue
        
        try:
            # 使用AI生成凭证
            voucher_data = await voucher_agent.generate_voucher_from_bill(bill, db)
            
            # 生成凭证编号
            period = datetime.now().strftime("%Y%m")
            count = db.query(Voucher).filter(Voucher.period == period).count() + 1
            voucher_no = f"PZ{period}{count:04d}"
            
            # 使用票据日期作为凭证日期，如果没有则使用当前日期
            voucher_date = bill.invoice_date if bill.invoice_date else datetime.now().date()
            voucher_period = voucher_date.strftime("%Y%m") if voucher_date else period
            
            # 创建凭证
            voucher = Voucher(
                customer_id=bill.customer_id,
                voucher_no=voucher_no,
                voucher_date=voucher_date,
                period=voucher_period,
                summary=voucher_data.get("summary", "自动生成的凭证"),
                ai_confidence=voucher_data.get("confidence", 0.8),
                ai_reason=voucher_data.get("reason", ""),
                status="draft"
            )
            db.add(voucher)
            db.flush()
            
            # 创建凭证明细
            for idx, entry in enumerate(voucher_data.get("entries", [])):
                item = VoucherItem(
                    voucher_id=voucher.id,
                    line_no=idx + 1,
                    subject_code=entry.get("subject_code", ""),
                    subject_name=entry.get("subject_name", ""),
                    debit_amount=entry.get("debit", 0),
                    credit_amount=entry.get("credit", 0),
                    summary=entry.get("summary", "")
                )
                db.add(item)
            
            # 更新票据状态
            bill.process_status = "voucher_generated"
            bill.voucher_id = voucher.id
            
            db.commit()
            generated_ids.append(str(voucher.id))
            
        except Exception as e:
            failed_items.append({"id": bill_id, "reason": str(e)})
            db.rollback()
    
    return success_response(data={
        "voucher_ids": generated_ids,
        "generated_count": len(generated_ids),
        "failed_count": len(failed_items),
        "failed_items": failed_items,
        "message": f"成功生成 {len(generated_ids)} 张凭证"
    })


class AuditRequest(BaseModel):
    """审核请求"""
    action: str
    note: Optional[str] = None
    modified_entries: Optional[List[dict]] = None


@router.post("/{voucher_id}/audit")
async def audit_voucher(
    voucher_id: str,
    request: AuditRequest,
    current_user=Depends(require_permission("vouchers:audit")),
    db: Session = Depends(get_db)
):
    """审核凭证"""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        return error_response(404, "Voucher not found")
    
    # 检查权限
    if str(voucher.assigned_to) != str(current_user.id) and current_user.role != "admin":
        return error_response(403, "Permission denied")
    
    # 状态流转映射
    action_to_status = {
        "approve": "approved",
        "reject": "rejected",
        "modify": "approved"
    }
    
    new_status = action_to_status.get(request.action)
    if not new_status:
        return error_response(400, f"Invalid action: {request.action}")
    
    # 验证状态流转
    is_valid, error_msg = VoucherStateMachine.validate_transition(
        voucher.status, new_status
    )
    if not is_valid:
        return error_response(400, error_msg)
    
    # 如果是修改，更新分录
    if request.action == "modify" and request.modified_entries:
        db.query(VoucherItem).filter(VoucherItem.voucher_id == voucher_id).delete()
        
        for entry_data in request.modified_entries:
            item = VoucherItem(
                voucher_id=voucher_id,
                line_no=entry_data.get("line_no", 0),
                subject_code=entry_data.get("subject_code", ""),
                subject_name=entry_data.get("subject_name", ""),
                debit_amount=entry_data.get("debit", 0),
                credit_amount=entry_data.get("credit", 0),
                summary=entry_data.get("summary", "")
            )
            db.add(item)
    
    # 更新凭证状态
    voucher.status = new_status
    voucher.auditor_id = current_user.id
    voucher.audit_note = request.note
    voucher.audited_at = datetime.now()
    
    db.commit()
    
    return success_response(data={
        "voucher_id": voucher_id,
        "status": new_status,
        "auditor": current_user.username,
        "audited_at": voucher.audited_at.isoformat() if voucher.audited_at else None
    })


@router.get("/{voucher_id}/detail")
async def get_voucher_detail(
    voucher_id: str,
    current_user=Depends(require_permission("vouchers:read")),
    db: Session = Depends(get_db)
):
    """获取凭证详情（含分录明细和合计）"""
    voucher = voucher_repo.get(db, voucher_id)
    if not voucher:
        return error_response(404, "凭证不存在")
    
    if str(voucher.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权访问此凭证")
    
    # 构建明细项
    items = []
    total_debit = 0
    total_credit = 0
    
    for item in voucher.items:
        debit = float(item.debit_amount) if item.debit_amount else 0
        credit = float(item.credit_amount) if item.credit_amount else 0
        total_debit += debit
        total_credit += credit
        
        items.append({
            "id": str(item.id),
            "line_no": item.line_no,
            "subject_code": item.subject_code,
            "subject_name": item.subject_name,
            "summary": item.summary,
            "debit_amount": debit,
            "credit_amount": credit
        })
    
    return success_response(data={
        "id": str(voucher.id),
        "voucher_no": voucher.voucher_no,
        "voucher_date": voucher.voucher_date.isoformat() if voucher.voucher_date else None,
        "period": voucher.period,
        "summary": voucher.summary,
        "status": voucher.status,
        "ai_confidence": float(voucher.ai_confidence) if voucher.ai_confidence else None,
        "items": items,
        "totals": {
            "debit": total_debit,
            "credit": total_credit,
            "is_balanced": abs(total_debit - total_credit) < 0.01
        },
        "created_at": voucher.created_at.isoformat() if voucher.created_at else ""
    })


class UpdateVoucherRequest(BaseModel):
    """更新凭证请求"""
    voucher_date: Optional[str] = None
    summary: Optional[str] = None
    items: Optional[List[dict]] = None


@router.put("/{voucher_id}")
async def update_voucher(
    voucher_id: str,
    request: UpdateVoucherRequest,
    current_user=Depends(require_permission("vouchers:update")),
    db: Session = Depends(get_db)
):
    """更新凭证（仅草稿状态可编辑）"""
    from decimal import Decimal
    
    voucher = voucher_repo.get(db, voucher_id)
    if not voucher:
        return error_response(404, "凭证不存在")
    
    if str(voucher.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权更新此凭证")
    
    # 仅草稿状态可编辑
    if voucher.status != "draft":
        return error_response(400, "仅草稿状态的凭证可编辑")
    
    # 更新基本信息
    update_data = {}
    if request.voucher_date:
        from datetime import datetime as dt
        update_data["voucher_date"] = dt.strptime(request.voucher_date, "%Y-%m-%d").date()
    if request.summary is not None:
        update_data["summary"] = request.summary
    
    if update_data:
        voucher_repo.update(db, db_obj=voucher, obj_in=update_data)
    
    # 更新分录
    if request.items is not None:
        # 校验借贷平衡
        total_debit = sum(Decimal(str(item.get("debit_amount", 0))) for item in request.items)
        total_credit = sum(Decimal(str(item.get("credit_amount", 0))) for item in request.items)
        
        if abs(total_debit - total_credit) > Decimal("0.01"):
            return error_response(400, f"借贷不平衡：借方{total_debit} ≠ 贷方{total_credit}")
        
        if len(request.items) < 2:
            return error_response(400, "凭证至少需要两条分录")
        
        # 删除旧分录
        db.query(VoucherItem).filter(VoucherItem.voucher_id == voucher_id).delete()
        
        # 创建新分录
        for idx, item_data in enumerate(request.items):
            # 校验单条分录
            debit = Decimal(str(item_data.get("debit_amount", 0)))
            credit = Decimal(str(item_data.get("credit_amount", 0)))
            
            if debit > 0 and credit > 0:
                return error_response(400, f"第{idx+1}行：借贷方不能同时有金额")
            
            if debit == 0 and credit == 0:
                return error_response(400, f"第{idx+1}行：借贷方必须输入一个金额")
            
            item = VoucherItem(
                voucher_id=voucher_id,
                line_no=idx + 1,
                subject_code=item_data.get("subject_code", ""),
                subject_name=item_data.get("subject_name", ""),
                summary=item_data.get("summary", ""),
                debit_amount=debit,
                credit_amount=credit
            )
            db.add(item)
    
    db.commit()
    return success_response(data={"message": "凭证更新成功"})
