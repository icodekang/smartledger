from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.contract import CustomerContract, ContractPayment
from app.models.customer import Customer

router = APIRouter(prefix="/contracts", tags=["合同管理"])


@router.get("")
async def list_all_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_permission("contracts:read")),
    db: Session = Depends(get_db)
):
    """获取所有合同列表"""
    try:
        skip = (page - 1) * page_size
        
        query = db.query(CustomerContract)
        total = query.count()
        contracts = query.order_by(CustomerContract.created_at.desc()).offset(skip).limit(page_size).all()
        
        items = []
        for c in contracts:
            try:
                days_to_expire = 0
                if c.end_date and c.status == "active":
                    if isinstance(c.end_date, str):
                        from datetime import datetime
                        end_date = datetime.strptime(c.end_date, "%Y-%m-%d").date()
                    else:
                        end_date = c.end_date
                    days_to_expire = (end_date - date.today()).days
                
                items.append({
                    "id": str(c.id),
                    "contract_no": c.contract_no,
                    "contract_name": c.contract_name,
                    "customer_id": str(c.customer_id) if c.customer_id else None,
                    "start_date": c.start_date.isoformat() if c.start_date else None,
                    "end_date": c.end_date.isoformat() if c.end_date else None,
                    "service_type": c.service_type,
                    "billing_amount": float(c.billing_amount) if c.billing_amount else 0,
                    "billing_cycle": c.billing_cycle,
                    "status": c.status,
                    "days_to_expire": max(0, days_to_expire)
                })
            except Exception as e:
                # 跳过有问题的记录，继续处理其他记录
                continue
        
        return success_response(data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        })
    except Exception as e:
        import traceback
        print(f"Error in list_all_contracts: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"获取合同列表失败: {str(e)}")


@router.get("/{contract_id}")
async def get_contract(
    contract_id: str,
    current_user=Depends(require_permission("contracts:read")),
    db: Session = Depends(get_db)
):
    """获取合同详情"""
    contract = db.query(CustomerContract).filter(CustomerContract.id == contract_id).first()
    if not contract:
        return error_response(404, "合同不存在")
    
    days_to_expire = (contract.end_date - date.today()).days if contract.end_date else 0
    
    return success_response(data={
        "id": str(contract.id),
        "contract_no": contract.contract_no,
        "contract_name": contract.contract_name,
        "customer_id": str(contract.customer_id),
        "start_date": contract.start_date.isoformat() if contract.start_date else None,
        "end_date": contract.end_date.isoformat() if contract.end_date else None,
        "service_type": contract.service_type,
        "service_content": contract.service_content,
        "billing_amount": float(contract.billing_amount) if contract.billing_amount else 0,
        "billing_cycle": contract.billing_cycle,
        "payment_terms": contract.payment_terms,
        "payment_day": contract.payment_day,
        "status": contract.status,
        "days_to_expire": days_to_expire if contract.status == "active" else 0
    })

class ContractCreateRequest(BaseModel):
    contract_name: str
    start_date: date
    end_date: date
    service_type: str
    service_content: Optional[str] = None
    billing_cycle: str = "monthly"
    billing_amount: float
    payment_terms: Optional[str] = None
    payment_day: int = 5
    remark: Optional[str] = None

class PaymentRecordRequest(BaseModel):
    paid_amount: float
    paid_by: Optional[str] = None
    payment_method: Optional[str] = None
    transaction_no: Optional[str] = None
    remark: Optional[str] = None

class InvoiceRecordRequest(BaseModel):
    invoice_no: str
    invoiced_at: date

def generate_contract_no(db: Session) -> str:
    """生成合同编号: HT + 年份 + 4位序号"""
    year = datetime.now().strftime("%Y")
    from sqlalchemy import func
    result = db.query(func.max(CustomerContract.contract_no)).filter(
        CustomerContract.contract_no.like(f"HT{year}%")
    ).scalar()
    if result:
        seq = int(result[6:]) + 1
    else:
        seq = 1
    return f"HT{year}{seq:04d}"

def create_payment_records(db: Session, contract: CustomerContract):
    """生成合同期内的收费记录"""
    from dateutil.relativedelta import relativedelta
    
    current = contract.start_date
    while current <= contract.end_date:
        period_str = current.strftime("%Y-%m")
        period_end = (current + relativedelta(months=1, days=-1))
        if period_end > contract.end_date:
            period_end = contract.end_date
            
        payment = ContractPayment(
            id=uuid.uuid4(),
            contract_id=contract.id,
            period=period_str,
            period_start=current,
            period_end=period_end,
            amount=contract.billing_amount,
            status="pending"
        )
        db.add(payment)
        current += relativedelta(months=1)

@router.get("/customer/{customer_id}")
async def list_contracts(
    customer_id: str,
    current_user=Depends(require_permission("contracts:read")),
    db: Session = Depends(get_db)
):
    """获取客户合同列表"""
    contracts = db.query(CustomerContract).filter(
        CustomerContract.customer_id == customer_id
    ).order_by(CustomerContract.created_at.desc()).all()
    
    items = []
    for c in contracts:
        days_to_expire = (c.end_date - date.today()).days if c.end_date else 0
        items.append({
            "id": str(c.id),
            "contract_no": c.contract_no,
            "contract_name": c.contract_name,
            "start_date": c.start_date.isoformat() if c.start_date else None,
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "service_type": c.service_type,
            "billing_amount": float(c.billing_amount) if c.billing_amount else 0,
            "billing_cycle": c.billing_cycle,
            "status": c.status,
            "days_to_expire": days_to_expire if c.status == "active" else 0
        })
    
    return success_response(data={"items": items})

@router.post("/customer/{customer_id}")
async def create_contract(
    customer_id: str,
    request: ContractCreateRequest,
    current_user=Depends(require_permission("contracts:create")),
    db: Session = Depends(get_db)
):
    """创建合同"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return error_response(404, "客户不存在")
    
    contract_no = generate_contract_no(db)
    
    contract = CustomerContract(
        id=uuid.uuid4(),
        customer_id=customer_id,
        contract_no=contract_no,
        contract_name=request.contract_name,
        start_date=request.start_date,
        end_date=request.end_date,
        service_type=request.service_type,
        service_content=request.service_content,
        billing_cycle=request.billing_cycle,
        billing_amount=Decimal(str(request.billing_amount)),
        payment_terms=request.payment_terms,
        payment_day=request.payment_day,
        remark=request.remark,
        status="active",
        created_by=current_user.id
    )
    
    db.add(contract)
    db.flush()
    
    # 生成本账期收费记录
    create_payment_records(db, contract)
    
    db.commit()
    
    return success_response(data={
        "id": str(contract.id),
        "contract_no": contract_no,
        "message": "合同创建成功"
    })

@router.get("/{contract_id}/payments")
async def list_payments(
    contract_id: str,
    current_user=Depends(require_permission("contracts:read")),
    db: Session = Depends(get_db)
):
    """获取收费记录列表"""
    payments = db.query(ContractPayment).filter(
        ContractPayment.contract_id == contract_id
    ).order_by(ContractPayment.period).all()
    
    items = []
    total_amount = 0
    paid_amount = 0
    pending_amount = 0
    overdue_amount = 0
    
    for p in payments:
        amount = float(p.amount) if p.amount else 0
        p_paid = float(p.paid_amount) if p.paid_amount else 0
        total_amount += amount
        
        if p.status == "paid":
            paid_amount += p_paid
        elif p.status == "pending":
            pending_amount += amount
        elif p.status == "overdue":
            overdue_amount += amount
        
        items.append({
            "id": str(p.id),
            "period": p.period,
            "period_start": p.period_start.isoformat() if p.period_start else None,
            "period_end": p.period_end.isoformat() if p.period_end else None,
            "amount": amount,
            "paid_amount": p_paid,
            "status": p.status,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "invoice_no": p.invoice_no,
            "invoiced_at": p.invoiced_at.isoformat() if p.invoiced_at else None
        })
    
    return success_response(data={
        "items": items,
        "summary": {
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "pending_amount": pending_amount,
            "overdue_amount": overdue_amount
        }
    })

@router.post("/payments/{payment_id}/pay")
async def record_payment(
    payment_id: str,
    request: PaymentRecordRequest,
    current_user=Depends(require_permission("contracts:update")),
    db: Session = Depends(get_db)
):
    """记录付款"""
    payment = db.query(ContractPayment).filter(ContractPayment.id == payment_id).first()
    if not payment:
        return error_response(404, "收费记录不存在")
    
    payment.paid_amount = Decimal(str(request.paid_amount))
    payment.paid_by = request.paid_by
    payment.payment_method = request.payment_method
    payment.transaction_no = request.transaction_no
    payment.paid_at = datetime.utcnow()
    payment.remark = request.remark
    
    # 更新状态
    if payment.paid_amount >= payment.amount:
        payment.status = "paid"
    else:
        payment.status = "partial"
    
    db.commit()
    
    return success_response(data={"message": "付款记录成功"})

@router.post("/payments/{payment_id}/invoice")
async def record_invoice(
    payment_id: str,
    request: InvoiceRecordRequest,
    current_user=Depends(require_permission("contracts:update")),
    db: Session = Depends(get_db)
):
    """记录开票"""
    payment = db.query(ContractPayment).filter(ContractPayment.id == payment_id).first()
    if not payment:
        return error_response(404, "收费记录不存在")
    
    payment.invoice_no = request.invoice_no
    payment.invoiced_at = datetime.combine(request.invoiced_at, datetime.min.time())
    
    db.commit()
    
    return success_response(data={"message": "开票记录成功"})

@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: str,
    current_user=Depends(require_permission("contracts:delete")),
    db: Session = Depends(get_db)
):
    """删除合同"""
    contract = db.query(CustomerContract).filter(CustomerContract.id == contract_id).first()
    if not contract:
        return error_response(404, "合同不存在")
    
    db.delete(contract)
    db.commit()
    
    return success_response(data={"message": "合同删除成功"})
