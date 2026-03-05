from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class BankFlow(BaseModel):
    """银行流水表"""
    __tablename__ = "bank_flows"
    
    customer_id = Column(ForeignKey("customers.id"))
    transaction_date = Column(DateTime)
    transaction_time = Column(String(10))
    counterparty = Column(String(200))
    debit_amount = Column(Numeric(12, 2))
    credit_amount = Column(Numeric(12, 2))
    summary = Column(Text)
    is_matched = Column(Boolean, default=False)
    matched_bill_id = Column(ForeignKey("bills.id"))
