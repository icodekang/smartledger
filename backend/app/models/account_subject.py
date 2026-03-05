from sqlalchemy import Column, String, Integer

from app.models.base import BaseModel


class AccountSubject(BaseModel):
    """会计科目表"""
    __tablename__ = "account_subjects"
    
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(20))
    direction = Column(String(10))
    parent_code = Column(String(20))
