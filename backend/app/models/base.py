import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def generate_uuid():
    """生成UUID字符串"""
    return str(uuid.uuid4())


class BaseModel(Base):
    """基础模型 - 兼容SQLite和PostgreSQL"""
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
