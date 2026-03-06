from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class BankFlowBase(BaseModel):
    """银行流水基础模型"""
    transaction_date: Optional[datetime] = None
    transaction_time: Optional[str] = None
    counterparty: Optional[str] = None
    debit_amount: Optional[float] = None
    credit_amount: Optional[float] = None
    summary: Optional[str] = None


class BankFlowCreate(BaseModel):
    """创建银行流水请求"""
    transaction_date: datetime
    transaction_time: Optional[str] = None
    counterparty: str = Field(..., min_length=1, max_length=200)
    debit_amount: Optional[float] = 0
    credit_amount: Optional[float] = 0
    summary: Optional[str] = None


class BankFlowUpdate(BaseModel):
    """更新银行流水请求"""
    counterparty: Optional[str] = None
    debit_amount: Optional[float] = None
    credit_amount: Optional[float] = None
    summary: Optional[str] = None
    is_matched: Optional[bool] = None
    matched_bill_id: Optional[str] = None


class BankFlowResponse(BankFlowBase):
    """银行流水响应模型"""
    id: str
    customer_id: Optional[str] = None
    is_matched: bool
    matched_bill_id: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class BankFlowListResponse(BaseModel):
    """银行流水列表响应"""
    items: List[BankFlowResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BankFlowUploadResponse(BaseModel):
    """银行流水上传响应"""
    uploaded_count: int
    message: str
