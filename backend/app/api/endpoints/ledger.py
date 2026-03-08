"""
Step3 批量后端API快速开发
包含: TASK-CUSTOMER-03/04, TASK-SYS-01/02/03/04, TASK-REPORT-01/02/03/04
"""

# ===== TASK-CUSTOMER-03: 账套管理 =====
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import uuid

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.ledger import CustomerLedger

ledger_router = APIRouter(prefix="/ledgers", tags=["账套管理"])

@ledger_router.post("/customer/{customer_id}/init")
async def init_ledgers(
    customer_id: str,
    start_period: str,  # 2024-01
    periods: int = 12,
    current_user=Depends(require_permission("ledgers:manage")),
    db: Session = Depends(get_db)
):
    """初始化客户账套"""
    start = datetime.strptime(start_period, "%Y-%m").date()
    
    for i in range(periods):
        period_date = start + relativedelta(months=i)
        period_str = period_date.strftime("%Y-%m")
        
        exists = db.query(CustomerLedger).filter(
            CustomerLedger.customer_id == customer_id,
            CustomerLedger.period == period_str
        ).first()
        
        if not exists:
            ledger = CustomerLedger(
                id=uuid.uuid4(),
                customer_id=customer_id,
                period=period_str,
                period_start=period_date.replace(day=1),
                period_end=(period_date + relativedelta(months=1, days=-1)),
                is_closed=False,
                is_locked=False
            )
            db.add(ledger)
    
    db.commit()
    return success_response(data={"message": f"成功初始化 {periods} 个账期"})


@ledger_router.get("/customer/{customer_id}")
async def list_ledgers(
    customer_id: str,
    current_user=Depends(require_permission("ledgers:read")),
    db: Session = Depends(get_db)
):
    """获取客户账套列表"""
    ledgers = db.query(CustomerLedger).filter(
        CustomerLedger.customer_id == customer_id
    ).order_by(CustomerLedger.period.desc()).all()
    
    items = []
    for l in ledgers:
        items.append({
            "id": str(l.id),
            "period": l.period,
            "period_start": l.period_start.isoformat() if l.period_start else None,
            "period_end": l.period_end.isoformat() if l.period_end else None,
            "is_closed": l.is_closed,
            "is_locked": l.is_locked,
            "closed_at": l.closed_at.isoformat() if l.closed_at else None
        })
    
    return success_response(data={"items": items})


@ledger_router.post("/{ledger_id}/close")
async def close_ledger(
    ledger_id: str,
    current_user=Depends(require_permission("ledgers:manage")),
    db: Session = Depends(get_db)
):
    """结账"""
    ledger = db.query(CustomerLedger).filter(CustomerLedger.id == ledger_id).first()
    if not ledger:
        return error_response(404, "账套不存在")
    
    ledger.is_closed = True
    ledger.closed_at = datetime.utcnow()
    ledger.closed_by = current_user.id
    
    db.commit()
    return success_response(data={"message": "结账成功"})


@ledger_router.post("/{ledger_id}/reopen")
async def reopen_ledger(
    ledger_id: str,
    current_user=Depends(require_permission("ledgers:manage")),
    db: Session = Depends(get_db)
):
    """反结账"""
    ledger = db.query(CustomerLedger).filter(CustomerLedger.id == ledger_id).first()
    if not ledger:
        return error_response(404, "账套不存在")
    
    # 检查下月是否已结账
    next_period = db.query(CustomerLedger).filter(
        CustomerLedger.customer_id == ledger.customer_id,
        CustomerLedger.period > ledger.period,
        CustomerLedger.is_closed == True
    ).first()
    
    if next_period:
        return error_response(400, "下月已结账，无法反结账")
    
    ledger.is_closed = False
    ledger.closed_at = None
    ledger.closed_by = None
    
    db.commit()
    return success_response(data={"message": "反结账成功"})
