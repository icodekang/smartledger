from sqlalchemy import Column, String, Date, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class BankFlow(BaseModel):
    """银行流水表"""
    __tablename__ = "bank_flows"
    
    customer_id = Column(ForeignKey("customers.id"))
    bank_account = Column(String(50))
    transaction_date = Column(Date)
    transaction_time = Column(String(10))
    counterparty = Column(String(200))
    counterparty_account = Column(String(50))
    debit_amount = Column(Numeric(12, 2), default=0)
    credit_amount = Column(Numeric(12, 2), default=0)
    balance = Column(Numeric(12, 2))
    summary = Column(String(500))
    is_matched = Column(Boolean, default=False)
    matched_bill_id = Column(ForeignKey("bills.id"))
    
    # 关系
    customer = relationship("Customer")
