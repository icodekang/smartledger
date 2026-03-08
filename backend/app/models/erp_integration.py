from sqlalchemy import Column, String, JSON, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import BaseModel


class ERPIntegration(BaseModel):
    """ERP集成配置"""
    __tablename__ = "erp_integrations"
    
    customer_id = Column(ForeignKey("customers.id"), nullable=False)
    
    erp_type = Column(String(50), nullable=False)  # kingdee/yonyou/sap/inspur
    erp_version = Column(String(50))
    
    # 连接配置
    connection_type = Column(String(20), default="api")  # api/database/file
    connection_config = Column(JSON, default={})
    
    # 同步配置
    sync_direction = Column(String(20), default="bidirectional")  # to_erp/from_erp/bidirectional
    sync_schedule = Column(String(50), default="daily")
    
    # 科目映射 {erp_code: local_code}
    subject_mapping = Column(JSON, default={})
    
    # 状态
    is_enabled = Column(Boolean, default=True)
    connection_status = Column(String(20), default="disconnected")
    last_sync_at = Column(DateTime)
    last_sync_result = Column(JSON)
    
    # 关系
    customer = relationship("Customer")
