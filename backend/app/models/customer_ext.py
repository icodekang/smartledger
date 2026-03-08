from sqlalchemy import Column, String, Date, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class CustomerContact(BaseModel):
    """客户联系人"""
    __tablename__ = "customer_contacts"
    
    customer_id = Column(ForeignKey("customers.id"), nullable=False)
    name = Column(String(50), nullable=False, comment="联系人姓名")
    title = Column(String(50), comment="职位")
    department = Column(String(50), comment="部门")
    phone = Column(String(50), comment="手机")
    tel = Column(String(50), comment="固定电话")
    email = Column(String(100), comment="邮箱")
    wechat = Column(String(50), comment="微信号")
    is_primary = Column(Boolean, default=False, comment="是否主要联系人")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    remark = Column(String(500), comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    customer = relationship("Customer", back_populates="contacts")


class CustomerAddress(BaseModel):
    """客户地址"""
    __tablename__ = "customer_addresses"
    
    customer_id = Column(ForeignKey("customers.id"), nullable=False)
    address_type = Column(String(20), nullable=False, comment="地址类型：注册地址/办公地址/仓库地址")
    province = Column(String(50), comment="省")
    city = Column(String(50), comment="市")
    district = Column(String(50), comment="区")
    detail = Column(String(200), comment="详细地址")
    postcode = Column(String(10), comment="邮编")
    is_primary = Column(Boolean, default=False, comment="是否主要地址")
    
    # 关系
    customer = relationship("Customer", back_populates="addresses")


class CustomerInvoiceInfo(BaseModel):
    """客户开票信息"""
    __tablename__ = "customer_invoice_info"
    
    customer_id = Column(ForeignKey("customers.id"), nullable=False)
    title = Column(String(200), nullable=False, comment="发票抬头")
    tax_no = Column(String(20), nullable=False, comment="税号")
    address = Column(String(200), comment="注册地址")
    phone = Column(String(50), comment="注册电话")
    bank_name = Column(String(100), comment="开户银行")
    bank_account = Column(String(50), comment="银行账号")
    is_default = Column(Boolean, default=True, comment="是否默认")
    
    # 关系
    customer = relationship("Customer", back_populates="invoice_infos")
