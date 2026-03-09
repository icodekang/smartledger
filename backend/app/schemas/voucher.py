from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class VoucherItemBase(BaseModel):
    """凭证明细基础模型"""
    line_no: int
    subject_code: str
    subject_name: str
    debit_amount: float = 0
    credit_amount: float = 0
    summary: Optional[str] = None


class VoucherItemCreate(VoucherItemBase):
    """创建凭证明细请求"""
    pass


class VoucherItemResponse(VoucherItemBase):
    """凭证明细响应模型"""
    id: str
    voucher_id: str

    class Config:
        from_attributes = True


class VoucherBase(BaseModel):
    """凭证基础模型"""
    voucher_no: Optional[str] = None
    voucher_date: Optional[date] = None
    period: Optional[str] = None
    summary: Optional[str] = None


class VoucherCreate(BaseModel):
    """创建凭证请求"""
    voucher_date: date
    period: Optional[str] = None
    summary: Optional[str] = None
    items: List[VoucherItemCreate] = Field(..., description="至少需要两条分录")


class VoucherUpdate(BaseModel):
    """更新凭证请求"""
    voucher_date: Optional[date] = None
    period: Optional[str] = None
    summary: Optional[str] = None
    items: Optional[List[VoucherItemCreate]] = None


class VoucherResponse(VoucherBase):
    """凭证响应模型"""
    id: str
    customer_id: Optional[str] = None
    voucher_no: Optional[str] = None
    voucher_date: Optional[str] = None  # 改为 str 类型，匹配 isoformat 返回值
    period: Optional[str] = None
    summary: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_reason: Optional[str] = None
    status: Optional[str] = None  # 改为可选
    assigned_to: Optional[str] = None
    auditor_id: Optional[str] = None
    audited_at: Optional[str] = None
    items: List[VoucherItemResponse] = []
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class VoucherListResponse(BaseModel):
    """凭证列表响应"""
    items: List[VoucherResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class VoucherGenerateRequest(BaseModel):
    """生成凭证请求"""
    bill_ids: List[str] = Field(..., min_length=1, description="票据ID列表")


class VoucherGenerateResponse(BaseModel):
    """生成凭证响应"""
    voucher_ids: List[str]
    generated_count: int
    message: str
