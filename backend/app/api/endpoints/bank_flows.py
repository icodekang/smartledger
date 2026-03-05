from typing import Optional, List
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.bank_flow import BankFlow
from app.repositories.base import BaseRepository
from app.schemas.bank_flow import (
    BankFlowCreate, BankFlowUpdate, BankFlowResponse,
    BankFlowListResponse, BankFlowUploadResponse
)

router = APIRouter(prefix="/bank-flows", tags=["银行流水"])
bank_flow_repo = BaseRepository(BankFlow)


@router.get("", response_model=BankFlowListResponse)
async def list_bank_flows(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_matched: Optional[bool] = Query(None, description="是否匹配"),
    counterparty: Optional[str] = Query(None, description="交易对手"),
    current_user=Depends(require_permission("bank_flows:read")),
    db: Session = Depends(get_db)
):
    """获取银行流水列表"""
    skip = (page - 1) * page_size
    
    # 构建过滤器
    filters = {"customer_id": current_user.customer_id}
    if is_matched is not None:
        filters["is_matched"] = is_matched
    
    # 查询数据
    flows = bank_flow_repo.get_multi(
        db, skip=skip, limit=page_size,
        filters=filters, order_by="transaction_date"
    )
    total = bank_flow_repo.count(db, filters=filters)
    
    # 转换为响应格式
    items = []
    for flow in flows:
        item = BankFlowResponse(
            id=str(flow.id),
            customer_id=str(flow.customer_id) if flow.customer_id else None,
            transaction_date=flow.transaction_date.isoformat() if flow.transaction_date else None,
            transaction_time=flow.transaction_time,
            counterparty=flow.counterparty,
            debit_amount=float(flow.debit_amount) if flow.debit_amount else None,
            credit_amount=float(flow.credit_amount) if flow.credit_amount else None,
            summary=flow.summary,
            is_matched=flow.is_matched,
            matched_bill_id=str(flow.matched_bill_id) if flow.matched_bill_id else None,
            created_at=flow.created_at.isoformat() if flow.created_at else "",
            updated_at=flow.updated_at.isoformat() if flow.updated_at else ""
        )
        items.append(item)
    
    return success_response(data={
        "items": [item.dict() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    })


@router.get("/{flow_id}", response_model=BankFlowResponse)
async def get_bank_flow(
    flow_id: str,
    current_user=Depends(require_permission("bank_flows:read")),
    db: Session = Depends(get_db)
):
    """获取银行流水详情"""
    flow = bank_flow_repo.get(db, flow_id)
    if not flow:
        return error_response(404, "银行流水不存在")
    
    if str(flow.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权访问")
    
    return success_response(data=BankFlowResponse(
        id=str(flow.id),
        customer_id=str(flow.customer_id) if flow.customer_id else None,
        transaction_date=flow.transaction_date.isoformat() if flow.transaction_date else None,
        transaction_time=flow.transaction_time,
        counterparty=flow.counterparty,
        debit_amount=float(flow.debit_amount) if flow.debit_amount else None,
        credit_amount=float(flow.credit_amount) if flow.credit_amount else None,
        summary=flow.summary,
        is_matched=flow.is_matched,
        matched_bill_id=str(flow.matched_bill_id) if flow.matched_bill_id else None,
        created_at=flow.created_at.isoformat() if flow.created_at else "",
        updated_at=flow.updated_at.isoformat() if flow.updated_at else ""
    ).dict())


@router.post("", response_model=BankFlowResponse)
async def create_bank_flow(
    request: BankFlowCreate,
    current_user=Depends(require_permission("bank_flows:create")),
    db: Session = Depends(get_db)
):
    """创建银行流水记录"""
    flow_data = request.dict()
    flow_data["customer_id"] = current_user.customer_id
    flow_data["is_matched"] = False
    
    flow = bank_flow_repo.create(db, obj_in=flow_data)
    
    return success_response(data=BankFlowResponse(
        id=str(flow.id),
        customer_id=str(flow.customer_id) if flow.customer_id else None,
        transaction_date=flow.transaction_date.isoformat() if flow.transaction_date else None,
        transaction_time=flow.transaction_time,
        counterparty=flow.counterparty,
        debit_amount=float(flow.debit_amount) if flow.debit_amount else None,
        credit_amount=float(flow.credit_amount) if flow.credit_amount else None,
        summary=flow.summary,
        is_matched=flow.is_matched,
        matched_bill_id=str(flow.matched_bill_id) if flow.matched_bill_id else None,
        created_at=flow.created_at.isoformat() if flow.created_at else "",
        updated_at=flow.updated_at.isoformat() if flow.updated_at else ""
    ).dict())


@router.put("/{flow_id}", response_model=BankFlowResponse)
async def update_bank_flow(
    flow_id: str,
    request: BankFlowUpdate,
    current_user=Depends(require_permission("bank_flows:update")),
    db: Session = Depends(get_db)
):
    """更新银行流水"""
    flow = bank_flow_repo.get(db, flow_id)
    if not flow:
        return error_response(404, "银行流水不存在")
    
    if str(flow.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权更新")
    
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    flow = bank_flow_repo.update(db, db_obj=flow, obj_in=update_data)
    
    return success_response(data=BankFlowResponse(
        id=str(flow.id),
        customer_id=str(flow.customer_id) if flow.customer_id else None,
        transaction_date=flow.transaction_date.isoformat() if flow.transaction_date else None,
        transaction_time=flow.transaction_time,
        counterparty=flow.counterparty,
        debit_amount=float(flow.debit_amount) if flow.debit_amount else None,
        credit_amount=float(flow.credit_amount) if flow.credit_amount else None,
        summary=flow.summary,
        is_matched=flow.is_matched,
        matched_bill_id=str(flow.matched_bill_id) if flow.matched_bill_id else None,
        created_at=flow.created_at.isoformat() if flow.created_at else "",
        updated_at=flow.updated_at.isoformat() if flow.updated_at else ""
    ).dict())


@router.delete("/{flow_id}")
async def delete_bank_flow(
    flow_id: str,
    current_user=Depends(require_permission("bank_flows:delete")),
    db: Session = Depends(get_db)
):
    """删除银行流水"""
    flow = bank_flow_repo.get(db, flow_id)
    if not flow:
        return error_response(404, "银行流水不存在")
    
    if str(flow.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权删除")
    
    bank_flow_repo.delete(db, id=flow_id)
    return success_response(data={"message": "银行流水已删除"})


@router.post("/upload", response_model=BankFlowUploadResponse)
async def upload_bank_flows(
    file: UploadFile = File(..., description="银行流水Excel/CSV文件"),
    current_user=Depends(require_permission("bank_flows:create")),
    db: Session = Depends(get_db)
):
    """批量上传银行流水"""
    # 检查文件类型
    allowed_extensions = [".xlsx", ".xls", ".csv"]
    file_ext = file.filename.lower()
    if not any(file_ext.endswith(ext) for ext in allowed_extensions):
        return error_response(400, "仅支持Excel或CSV文件")
    
    # 读取文件内容
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        return error_response(400, "文件大小超过5MB限制")
    
    try:
        # 解析Excel/CSV
        if file_ext.endswith(".csv"):
            df = pd.read_csv(BytesIO(contents))
        else:
            df = pd.read_excel(BytesIO(contents))
        
        # 字段映射（支持常见的银行流水格式）
        column_mapping = {
            "交易日期": "transaction_date",
            "日期": "transaction_date",
            "交易时间": "transaction_time",
            "时间": "transaction_time",
            "交易对手": "counterparty",
            "对方户名": "counterparty",
            "对方账户": "counterparty",
            "借方金额": "debit_amount",
            "支出": "debit_amount",
            "贷方金额": "credit_amount",
            "收入": "credit_amount",
            "摘要": "summary",
            "用途": "summary"
        }
        
        # 尝试映射列名
        df.rename(columns=column_mapping, inplace=True)
        
        # 确保必要列存在
        required_cols = ["transaction_date", "counterparty"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return error_response(400, f"缺少必要列: {missing_cols}")
        
        # 导入数据
        uploaded_count = 0
        for _, row in df.iterrows():
            try:
                flow_data = {
                    "customer_id": current_user.customer_id,
                    "transaction_date": row.get("transaction_date"),
                    "transaction_time": str(row.get("transaction_time", ""))[:10],
                    "counterparty": str(row.get("counterparty", "")),
                    "debit_amount": float(row.get("debit_amount", 0) or 0),
                    "credit_amount": float(row.get("credit_amount", 0) or 0),
                    "summary": str(row.get("summary", "")),
                    "is_matched": False
                }
                bank_flow_repo.create(db, obj_in=flow_data)
                uploaded_count += 1
            except Exception as e:
                # 跳过有问题的行，继续处理
                continue
        
        return success_response(data={
            "uploaded_count": uploaded_count,
            "message": f"成功导入 {uploaded_count} 条银行流水记录"
        })
        
    except Exception as e:
        return error_response(500, f"文件解析失败: {str(e)}")
