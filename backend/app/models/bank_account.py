from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, DateTime, Date, Numeric, Integer, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import BaseModel


class BankAccount(BaseModel):
    """银行账户表"""
    __tablename__ = "bank_accounts"
    
    customer_id = Column(ForeignKey("customers.id"), nullable=False)
    
    # 银行信息
    bank_code = Column(String(20), nullable=False, comment="银行代码")
    bank_name = Column(String(50), nullable=False, comment="银行名称")
    
    # 账户信息
    account_no = Column(String(50), nullable=False, comment="银行账号")
    account_name = Column(String(100), comment="账户名称")
    account_type = Column(String(20), default="basic", comment="基本户/一般户")
    
    # API配置
    api_type = Column(String(20), default="open", comment="open/sdk/direct")
    api_config = Column(JSON, comment="API配置参数")
    
    # 授权信息
    auth_status = Column(String(20), default="unauthorized", comment="授权状态")
    auth_token = Column(Text, comment="访问令牌")
    refresh_token = Column(Text, comment="刷新令牌")
    token_expires_at = Column(DateTime, comment="令牌过期时间")
    
    # 同步配置
    auto_sync = Column(Boolean, default=True, comment="自动同步")
    last_sync_at = Column(DateTime, comment="最后同步时间")
    sync_range_days = Column(Integer, default=30, comment="同步范围天数")
    
    # 余额信息
    balance = Column(Numeric(15, 2), comment="当前余额")
    balance_updated_at = Column(DateTime, comment="余额更新时间")
    
    is_enabled = Column(Boolean, default=True)
    
    # 关系
    customer = relationship("Customer")
    bank_flows = relationship("BankFlow", back_populates="bank_account")
