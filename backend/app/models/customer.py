from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Customer(BaseModel):
    """客户表"""
    __tablename__ = "customers"
    
    name = Column(String(200), nullable=False)
    tax_no = Column(String(20), unique=True)
    industry = Column(String(50))
    taxpayer_type = Column(String(20))
    contact_name = Column(String(100))
    contact_phone = Column(String(20))
    status = Column(String(20), default="active")
    
    # 关系
    bills = relationship("Bill", back_populates="customer")
    vouchers = relationship("Voucher", back_populates="customer")
    bank_flows = relationship("BankFlow", back_populates="customer")
