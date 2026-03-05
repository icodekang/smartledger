from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AccountSubject(BaseModel):
    """会计科目表"""
    __tablename__ = "account_subjects"
    
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(20))  # asset/liability/equity/cost/income/expense
    direction = Column(String(10))  # debit/credit
    parent_code = Column(String(20))
    level = Column(Integer, default=1)
    is_active = Column(Integer, default=1)
