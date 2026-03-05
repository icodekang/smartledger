from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.services.state_machine import VoucherStateMachine
from app.models.voucher import Voucher

router = APIRouter(prefix="/vouchers", tags=["凭证审核"])


@router.post("/{voucher_id}/audit")
async def audit_voucher(
    voucher_id: str,
    action: str,
    note: str = "",
    current_user=Depends(require_permission("vouchers:audit")),
    db: Session = Depends(get_db)
):
    """凭证审核"""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        return error_response(404, "Voucher not found")
    
    # 确定目标状态
    status_map = {
        "approve": "approved",
        "reject": "rejected",
        "post": "posted"
    }
    
    to_status = status_map.get(action)
    if not to_status:
        return error_response(400, f"Invalid action: {action}")
    
    # 验证状态流转
    valid, message = VoucherStateMachine.validate_transition(
        voucher.status, to_status
    )
    if not valid:
        return error_response(400, message)
    
    # 更新状态
    voucher.status = to_status
    voucher.auditor_id = current_user.id
    from datetime import datetime
    voucher.audited_at = datetime.utcnow()
    
    db.commit()
    db.refresh(voucher)
    
    return success_response(data={
        "voucher_id": str(voucher.id),
        "status": voucher.status,
        "auditor_id": str(current_user.id)
    })


@router.get("/workbench/pending")
async def get_pending_vouchers(
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(require_permission("vouchers:audit")),
    db: Session = Depends(get_db)
):
    """获取待审凭证列表"""
    from sqlalchemy import func
    
    query = db.query(Voucher).filter(Voucher.status == "pending")
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return success_response(data={
        "items": [
            {
                "id": str(v.id),
                "voucher_no": v.voucher_no,
                "summary": v.summary,
                "ai_confidence": float(v.ai_confidence) if v.ai_confidence else 0,
                "status": v.status
            }
            for v in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    })
