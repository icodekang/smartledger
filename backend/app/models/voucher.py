from sqlalchemy import Column, String, Date, Text, ForeignKey, Numeric, Integer, DateTime
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Voucher(BaseModel):
    """凭证表"""
    __tablename__ = "vouchers"
    
    customer_id = Column(ForeignKey("customers.id"))
    voucher_no = Column(String(20))
    voucher_date = Column(Date)
    period = Column(String(10))
    summary = Column(Text)
    
    ai_confidence = Column(Numeric(3, 2))
    ai_reason = Column(Text)
    
    status = Column(String(20), default="draft")
    assigned_to = Column(ForeignKey("users.id"))
    auditor_id = Column(ForeignKey("users.id"))
    audited_at = Column(DateTime)
    
    # 关系
    customer = relationship("Customer", back_populates="vouchers")
    items = relationship("VoucherItem", back_populates="voucher", cascade="all, delete-orphan")


class VoucherItem(BaseModel):
    """凭证明细表"""
    __tablename__ = "voucher_items"
    
    voucher_id = Column(ForeignKey("vouchers.id"))
    line_no = Column(Integer)
    subject_code = Column(String(20))
    subject_name = Column(String(100))
    debit_amount = Column(Numeric(12, 2), default=0)
    credit_amount = Column(Numeric(12, 2), default=0)
    summary = Column(Text)
    auxiliary_name = Column(String(100))  # 辅助核算项名称
    
    # 关系
    voucher = relationship("Voucher", back_populates="items")
