from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.response import success_response, error_response, ResponseModel
from app.core.permissions import require_permission
from app.models.voucher import Voucher
from app.models.user import User
from app.repositories.base import BaseRepository

router = APIRouter(prefix="/audit", tags=["审核工作台"])
voucher_repo = BaseRepository(Voucher)


class AuditTaskItem(BaseModel):
    """审核任务项"""
    voucher_id: str
    voucher_no: Optional[str] = None
    voucher_date: Optional[str] = None
    summary: Optional[str] = None
    total_amount: float
    status: str
    created_at: str
    submitter: str
    customer_name: Optional[str] = None


class AuditTaskListData(BaseModel):
    """审核任务列表数据"""
    items: List[AuditTaskItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    stats: dict


class BatchAuditRequest(BaseModel):
    """批量审核请求"""
    voucher_ids: List[str]
    action: str  # approve, reject
    note: Optional[str] = None


class BatchAuditData(BaseModel):
    """批量审核响应数据"""
    updated_count: int
    failed_count: int
    failed_items: List[dict]
    action: str


class AuditAssignmentRequest(BaseModel):
    """审核分配请求"""
    voucher_ids: List[str]
    auditor_id: str


class AssignmentData(BaseModel):
    """分配响应数据"""
    assigned_count: int
    auditor_id: str
    auditor_name: str
    failed_count: int
    failed_items: List[dict]


class AutoAssignData(BaseModel):
    """自动分配响应数据"""
    assigned_count: int
    auditor_id: str
    message: str


class AuditStatisticsData(BaseModel):
    """审核统计数据"""
    overview: dict
    performance: dict


@router.get("/pending")
async def get_pending_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态过滤: pending, assigned"),
    current_user=Depends(require_permission("audit:read")),
    db: Session = Depends(get_db)
):
    """获取待审核任务列表"""
    skip = (page - 1) * page_size

    # 构建查询
    query = db.query(Voucher, User).join(User, Voucher.customer_id == User.id)

    # 审核员只能看到分配给自己的或待分配的
    if current_user.role == "auditor":
        query = query.filter(
            (Voucher.assigned_to == current_user.id) |
            (Voucher.assigned_to.is_(None))
        )

    # 状态过滤
    if status == "pending":
        query = query.filter(Voucher.status == "draft")
    elif status == "assigned":
        query = query.filter(Voucher.status == "pending")
    else:
        query = query.filter(Voucher.status.in_(["draft", "pending"]))

    # 提交人不能审核自己的单据
    query = query.filter(Voucher.customer_id != current_user.id)

    # 排序和分页
    total = query.count()
    results = query.order_by(Voucher.created_at.desc()).offset(skip).limit(page_size).all()

    # 构建响应
    items = []
    for voucher, submitter in results:
        # 计算凭证总金额
        total_amount = sum(
            float(item.debit_amount or 0)
            for item in voucher.items
        ) if voucher.items else 0

        items.append(AuditTaskItem(
            voucher_id=str(voucher.id),
            voucher_no=voucher.voucher_no,
            voucher_date=voucher.voucher_date.isoformat() if voucher.voucher_date else None,
            summary=voucher.summary,
            total_amount=total_amount,
            status=voucher.status,
            created_at=voucher.created_at.isoformat() if voucher.created_at else "",
            submitter=submitter.name or submitter.username,
            customer_name=submitter.name
        ))

    # 统计信息
    stats_query = db.query(Voucher)
    if current_user.role == "auditor":
        stats_query = stats_query.filter(
            (Voucher.assigned_to == current_user.id) |
            (Voucher.assigned_to.is_(None))
        )
    stats_query = stats_query.filter(Voucher.customer_id != current_user.id)

    pending_count = stats_query.filter(Voucher.status == "draft").count()
    assigned_count = stats_query.filter(Voucher.status == "pending").count()
    my_assigned = stats_query.filter(Voucher.assigned_to == current_user.id).count()

    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "stats": {
            "pending_count": pending_count,
            "assigned_count": assigned_count,
            "my_assigned": my_assigned
        }
    })


@router.post("/batch-audit")
async def batch_audit(
    request: BatchAuditRequest,
    current_user=Depends(require_permission("audit:approve")),
    db: Session = Depends(get_db)
):
    """批量审核"""
    if request.action not in ["approve", "reject"]:
        return error_response(400, "无效的审核动作")

    new_status = "approved" if request.action == "approve" else "rejected"
    updated_count = 0
    failed_ids = []

    for voucher_id in request.voucher_ids:
        voucher = voucher_repo.get(db, voucher_id)
        if not voucher:
            failed_ids.append({"id": voucher_id, "reason": "凭证不存在"})
            continue

        # 检查权限
        if str(voucher.assigned_to) != str(current_user.id) and current_user.role != "admin":
            failed_ids.append({"id": voucher_id, "reason": "无权审核此凭证"})
            continue

        # 提交人不能审核自己的单据
        if str(voucher.customer_id) == str(current_user.id):
            failed_ids.append({"id": voucher_id, "reason": "不能审核自己的单据"})
            continue

        # 检查状态
        if voucher.status not in ["draft", "pending"]:
            failed_ids.append({"id": voucher_id, "reason": f"当前状态不允许审核: {voucher.status}"})
            continue

        # 更新状态
        voucher_repo.update(db, db_obj=voucher, obj_in={
            "status": new_status,
            "auditor_id": current_user.id,
            "audit_note": request.note,
            "audited_at": datetime.now()
        })
        updated_count += 1

    return success_response(data={
        "updated_count": updated_count,
        "failed_count": len(failed_ids),
        "failed_items": failed_ids,
        "action": request.action
    })


@router.post("/assign")
async def assign_tasks(
    request: AuditAssignmentRequest,
    current_user=Depends(require_permission("audit:assign")),
    db: Session = Depends(get_db)
):
    """分配审核任务"""
    # 验证审核人存在
    auditor = db.query(User).filter(User.id == request.auditor_id).first()
    if not auditor:
        return error_response(404, "审核人不存在")

    assigned_count = 0
    failed_ids = []

    for voucher_id in request.voucher_ids:
        voucher = voucher_repo.get(db, voucher_id)
        if not voucher:
            failed_ids.append({"id": voucher_id, "reason": "凭证不存在"})
            continue

        if voucher.status != "draft":
            failed_ids.append({"id": voucher_id, "reason": f"当前状态不允许分配: {voucher.status}"})
            continue

        # 分配任务
        voucher_repo.update(db, db_obj=voucher, obj_in={
            "assigned_to": request.auditor_id,
            "status": "pending"
        })
        assigned_count += 1

    return success_response(data={
        "assigned_count": assigned_count,
        "auditor_id": request.auditor_id,
        "auditor_name": auditor.name or auditor.username,
        "failed_count": len(failed_ids),
        "failed_items": failed_ids
    })


@router.post("/auto-assign")
async def auto_assign_tasks(
    count: int = Query(10, ge=1, le=100, description="分配数量"),
    current_user=Depends(require_permission("audit:assign")),
    db: Session = Depends(get_db)
):
    """自动分配待审核任务给当前审核人"""
    # 获取待分配的凭证
    vouchers = db.query(Voucher).filter(
        Voucher.status == "draft",
        Voucher.assigned_to.is_(None),
        Voucher.customer_id != current_user.id  # 排除自己的
    ).order_by(Voucher.created_at.asc()).limit(count).all()

    assigned_count = 0
    for voucher in vouchers:
        voucher_repo.update(db, db_obj=voucher, obj_in={
            "assigned_to": current_user.id,
            "status": "pending"
        })
        assigned_count += 1

    return success_response(data={
        "assigned_count": assigned_count,
        "auditor_id": str(current_user.id),
        "message": f"成功分配 {assigned_count} 条审核任务"
    })


@router.get("/statistics")
async def get_audit_statistics(
    current_user=Depends(require_permission("audit:read")),
    db: Session = Depends(get_db)
):
    """获取审核统计信息"""
    # 基础查询
    base_query = db.query(Voucher)

    # 审核员只能看到自己的统计
    if current_user.role == "auditor":
        base_query = base_query.filter(Voucher.assigned_to == current_user.id)

    # 各状态统计
    draft_count = base_query.filter(Voucher.status == "draft").count()
    pending_count = base_query.filter(Voucher.status == "pending").count()
    approved_count = base_query.filter(Voucher.status == "approved").count()
    rejected_count = base_query.filter(Voucher.status == "rejected").count()

    # 今日审核数量
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_approved = base_query.filter(
        Voucher.status == "approved",
        Voucher.audited_at >= today
    ).count()

    # 本月审核数量
    this_month = today.replace(day=1)
    month_approved = base_query.filter(
        Voucher.status == "approved",
        Voucher.audited_at >= this_month
    ).count()

    # 平均审核时间（简化计算）
    audited_vouchers = base_query.filter(Voucher.status.in_(["approved", "rejected"])).all()
    avg_audit_time = 0
    if audited_vouchers:
        total_seconds = sum(
            (v.audited_at - v.created_at).total_seconds()
            for v in audited_vouchers if v.audited_at
        )
        avg_audit_time = total_seconds / len(audited_vouchers) / 3600  # 转换为小时

    return success_response(data={
        "overview": {
            "draft_count": draft_count,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count
        },
        "performance": {
            "today_approved": today_approved,
            "month_approved": month_approved,
            "avg_audit_time_hours": round(avg_audit_time, 2)
        }
    })


@router.get("/tasks")
async def get_all_tasks(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_permission("audit:read")),
    db: Session = Depends(get_db)
):
    """获取所有审核任务"""
    skip = (page - 1) * page_size

    query = db.query(Voucher).filter(
        Voucher.status.in_(["draft", "pending", "approved", "rejected"])
    )

    if status:
        query = query.filter(Voucher.status == status)

    total = query.count()
    vouchers = query.order_by(Voucher.created_at.desc()).offset(skip).limit(page_size).all()

    items = []
    for v in vouchers:
        items.append({
            "id": str(v.id),
            "voucher_no": v.voucher_no,
            "voucher_date": v.voucher_date.isoformat() if v.voucher_date else None,
            "summary": v.summary,
            "status": v.status,
            "assigned_to": str(v.assigned_to) if v.assigned_to else None,
            "auditor_id": str(v.auditor_id) if v.auditor_id else None,
            "created_at": v.created_at.isoformat() if v.created_at else ""
        })

    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/my-tasks")
async def get_my_tasks(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_permission("audit:read")),
    db: Session = Depends(get_db)
):
    """获取我的审核任务"""
    skip = (page - 1) * page_size

    query = db.query(Voucher).filter(
        Voucher.assigned_to == current_user.id
    )

    if status:
        query = query.filter(Voucher.status == status)
    else:
        query = query.filter(Voucher.status.in_(["pending", "approved", "rejected"]))

    total = query.count()
    vouchers = query.order_by(Voucher.created_at.desc()).offset(skip).limit(page_size).all()

    items = []
    for v in vouchers:
        items.append({
            "id": str(v.id),
            "voucher_no": v.voucher_no,
            "voucher_date": v.voucher_date.isoformat() if v.voucher_date else None,
            "summary": v.summary,
            "status": v.status,
            "ai_confidence": float(v.ai_confidence) if v.ai_confidence else None,
            "created_at": v.created_at.isoformat() if v.created_at else "",
            "audited_at": v.audited_at.isoformat() if v.audited_at else None
        })

    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/statistics")
async def get_audit_statistics(
    current_user=Depends(require_permission("audit:read")),
    db: Session = Depends(get_db)
):
    """获取审核统计信息"""
    # 获取各类状态的凭证数量
    draft_count = db.query(Voucher).filter(Voucher.status == "draft").count()
    pending_count = db.query(Voucher).filter(Voucher.status == "pending").count()
    approved_count = db.query(Voucher).filter(Voucher.status == "approved").count()
    rejected_count = db.query(Voucher).filter(Voucher.status == "rejected").count()
    
    # 今日审核通过数量
    from datetime import date
    today = date.today()
    today_approved = db.query(Voucher).filter(
        Voucher.status == "approved",
        Voucher.audited_at >= today
    ).count()
    
    # 本月审核通过数量
    month_approved = db.query(Voucher).filter(
        Voucher.status == "approved",
        Voucher.audited_at >= today.replace(day=1)
    ).count()
    
    # 平均审核时间
    avg_audit_time = 0
    audited_vouchers = db.query(Voucher).filter(
        Voucher.status.in_(["approved", "rejected"]),
        Voucher.audited_at.isnot(None)
    ).all()
    
    if audited_vouchers:
        total_seconds = sum(
            (v.audited_at - v.created_at).total_seconds()
            for v in audited_vouchers
            if v.audited_at
        )
        avg_audit_time = total_seconds / len(audited_vouchers) / 3600  # 转换为小时
    
    return success_response(data={
        "overview": {
            "draft_count": draft_count,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count
        },
        "performance": {
            "today_approved": today_approved,
            "month_approved": month_approved,
            "avg_audit_time_hours": round(avg_audit_time, 2)
        }
    })
