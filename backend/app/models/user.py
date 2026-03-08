from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey

from app.models.base import BaseModel


class User(BaseModel):
    """用户表"""
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    role = Column(String(20), default="viewer")
    phone = Column(String(20))
    max_daily_capacity = Column(Integer, default=50)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    customer_id = Column(ForeignKey("customers.id"), nullable=True)  # 关联客户ID
    
    # 账户锁定机制
    failed_login_attempts = Column(Integer, default=0)  # 失败登录次数
    locked_until = Column(DateTime)  # 锁定截止时间
    last_failed_login = Column(DateTime)  # 最后一次失败登录时间
