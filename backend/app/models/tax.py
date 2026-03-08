from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import BaseModel


class TaxAuth(BaseModel):
    """税务授权信息"""
    __tablename__ = "tax_auths"
    
    customer_id = Column(ForeignKey("customers.id"), nullable=False)
    
    tax_no = Column(String(20), nullable=False, comment="纳税人识别号")
    tax_area = Column(String(50), comment="税务地区")
    
    # 电子税务局账号
    etax_username = Column(String(50), comment="电子税务局账号")
    etax_password_encrypted = Column(Text, comment="密码(加密)")
    
    # 认证信息
    auth_status = Column(String(20), default="unauthorized")
    auth_token = Column(Text)
    auth_expires_at = Column(DateTime)
    
    is_enabled = Column(Boolean, default=True)
    
    # 关系
    customer = relationship("Customer")


class TaxDeclaration(BaseModel):
    """纳税申报记录"""
    __tablename__ = "tax_declarations"
    
    customer_id = Column(ForeignKey("customers.id"), nullable=False)
    
    period = Column(String(10), nullable=False, comment="申报期间")
    tax_type = Column(String(50), nullable=False, comment="税种")
    
    # 申报数据
    taxable_amount = Column(Numeric(15, 2), comment="应税金额")
    tax_amount = Column(Numeric(15, 2), comment="应纳税额")
    deduction_amount = Column(Numeric(15, 2), comment="抵扣金额")
    payable_amount = Column(Numeric(15, 2), comment="应缴金额")
    
    # 申报状态
    status = Column(String(20), default="draft", comment="draft/submitted/paid")
    declared_at = Column(DateTime, comment="申报时间")
    paid_at = Column(DateTime, comment="缴纳时间")
    
    # 电子税局回执
    receipt_no = Column(String(50), comment="申报回执号")
    receipt_url = Column(String(500), comment="回执文件URL")
    
    # 关系
    customer = relationship("Customer")
