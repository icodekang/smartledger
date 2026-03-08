from sqlalchemy import Column, String, Date, Text, Numeric, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import BaseModel


class CustomerContract(BaseModel):
    """客户合同"""
    __tablename__ = "customer_contracts"
    
    customer_id = Column(ForeignKey("customers.id"), nullable=False)
    contract_no = Column(String(50), unique=True, nullable=False, comment="合同编号")
    contract_name = Column(String(200), comment="合同名称")
    
    start_date = Column(Date, nullable=False, comment="开始日期")
    end_date = Column(Date, nullable=False, comment="结束日期")
    
    service_type = Column(String(50), comment="服务类型")
    service_content = Column(Text, comment="服务内容描述")
    
    billing_cycle = Column(String(20), default="monthly", comment="计费周期")
    billing_amount = Column(Numeric(15, 2), nullable=False, comment="计费金额")
    currency = Column(String(10), default="CNY", comment="币种")
    
    payment_terms = Column(String(50), comment="付款条件")
    payment_day = Column(Integer, default=5, comment="每月付款日")
    
    status = Column(String(20), default="active", comment="状态")
    attachment_url = Column(String(500), comment="合同附件URL")
    remark = Column(Text, comment="备注")
    
    created_by = Column(ForeignKey("users.id"))
    
    # 关系
    customer = relationship("Customer", back_populates="contracts")
    payments = relationship("ContractPayment", back_populates="contract", cascade="all, delete-orphan")


class ContractPayment(BaseModel):
    """合同收费记录"""
    __tablename__ = "contract_payments"
    
    contract_id = Column(ForeignKey("customer_contracts.id"), nullable=False)
    period = Column(String(10), nullable=False, comment="账期")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default="pending", comment="状态")
    
    paid_at = Column(DateTime, comment="付款时间")
    paid_by = Column(String(50), comment="付款人")
    payment_method = Column(String(50), comment="付款方式")
    transaction_no = Column(String(100), comment="交易流水号")
    
    invoice_no = Column(String(50), comment="发票号码")
    invoiced_at = Column(DateTime, comment="开票时间")
    remark = Column(String(500), comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    contract = relationship("CustomerContract", back_populates="payments")
