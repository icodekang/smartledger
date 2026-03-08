from sqlalchemy import Column, String, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class CustomerLedger(BaseModel):
    """客户账套"""
    __tablename__ = "customer_ledgers"
    
    customer_id = Column(ForeignKey("customers.id"), nullable=False)
    period = Column(String(10), nullable=False, comment="账期：2024-03")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    is_closed = Column(Boolean, default=False, comment="是否已结账")
    closed_at = Column(Date, comment="结账时间")
    closed_by = Column(ForeignKey("users.id"))
    
    is_locked = Column(Boolean, default=False, comment="是否锁定")
    remark = Column(Text, comment="备注")
    
    customer = relationship("Customer")
