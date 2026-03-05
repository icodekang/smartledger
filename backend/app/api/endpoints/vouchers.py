from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.voucher import Voucher, VoucherItem
from app.services.state_machine import VoucherStateMachine

router = APIRouter(prefix="/vouchers", tags=["凭证"])


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
