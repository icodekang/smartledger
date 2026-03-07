from sqlalchemy import Column, String, Date, Numeric, ForeignKey, JSON, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Bill(BaseModel):
    """票据表"""
    __tablename__ = "bills"
    
    customer_id = Column(ForeignKey("customers.id"))
    bill_type = Column(String(20))
    storage_path = Column(String(500))
    storage_url = Column(String(500))
    
    ocr_result = Column(JSONB)
    ocr_confidence = Column(Numeric(3, 2))
    
    invoice_code = Column(String(20))
    invoice_number = Column(String(20))
    invoice_date = Column(Date)
    seller_name = Column(String(200))
    amount = Column(Numeric(12, 2))
    tax_amount = Column(Numeric(12, 2))
    total_amount = Column(Numeric(12, 2))
    
    process_status = Column(String(20), default="pending")
    ai_confidence = Column(Numeric(3, 2))
    ai_anomalies = Column(JSON)
    
    # 关联生成的凭证
    voucher_id = Column(ForeignKey("vouchers.id"), nullable=True)
    
    # 关系
    customer = relationship("Customer", back_populates="bills")
    bank_flow_matches = relationship("BankFlow", back_populates="matched_bill")
