from sqlalchemy import Column, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class Customer(BaseModel):
    """客户表"""
    __tablename__ = "customers"
    
    # 基本信息
    code = Column(String(20), unique=True, nullable=False, comment="客户编码")
    name = Column(String(200), nullable=False, comment="客户名称")
    short_name = Column(String(50), comment="客户简称")
    
    # 企业信息
    company_type = Column(String(50), comment="企业类型")
    industry = Column(String(50), comment="所属行业")
    scale = Column(String(20), comment="企业规模")
    
    # 税务信息
    tax_no = Column(String(20), unique=True, comment="统一社会信用代码/税号")
    tax_type = Column(String(20), default="一般纳税人", comment="纳税人类型")
    
    # 联系信息
    phone = Column(String(50), comment="联系电话")
    email = Column(String(100), comment="联系邮箱")
    fax = Column(String(50), comment="传真")
    website = Column(String(200), comment="公司网站")
    
    # 状态
    status = Column(String(20), default="active", comment="状态")
    
    # 服务信息
    service_start_date = Column(Date, comment="服务开始日期")
    service_end_date = Column(Date, comment="服务结束日期")
    assigned_accountant_id = Column(ForeignKey("users.id"), comment="负责会计")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 审计字段
    created_by = Column(ForeignKey("users.id"))
    
    # 关系
    bills = relationship("Bill", back_populates="customer")
    vouchers = relationship("Voucher", back_populates="customer")
    bank_flows = relationship("BankFlow", back_populates="customer")
    contacts = relationship("CustomerContact", back_populates="customer", cascade="all, delete-orphan")
    addresses = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan")
    invoice_infos = relationship("CustomerInvoiceInfo", back_populates="customer", cascade="all, delete-orphan")
