from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class BillBase(BaseModel):
    """票据基础模型"""
    bill_type: Optional[str] = None
    invoice_code: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    seller_name: Optional[str] = None
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None


class BillCreate(BaseModel):
    """创建票据请求"""
    bill_type: str = Field(..., description="票据类型")
    invoice_code: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    seller_name: Optional[str] = None
    amount: float = Field(..., gt=0, description="金额")
    tax_amount: Optional[float] = 0
    total_amount: float = Field(..., gt=0, description="价税合计")


class BillUpdate(BaseModel):
    """更新票据请求"""
    invoice_code: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    seller_name: Optional[str] = None
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    process_status: Optional[str] = None


class BillResponse(BillBase):
    """票据响应模型"""
    id: str
    customer_id: Optional[str] = None
    invoice_date: Optional[str] = None  # 改为 str 类型，匹配 isoformat 返回值
    storage_path: Optional[str] = None
    storage_url: Optional[str] = None
    ocr_result: Optional[dict] = None
    ocr_confidence: Optional[float] = None
    process_status: Optional[str] = None  # 改为可选
    ai_confidence: Optional[float] = None
    ai_anomalies: Optional[List[dict]] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class BillListResponse(BaseModel):
    """票据列表响应"""
    items: List[BillResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BillUploadResponse(BaseModel):
    """票据上传响应"""
    bill_id: str
    storage_url: str
    ocr_status: str
    message: str
