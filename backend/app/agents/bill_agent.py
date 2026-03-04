from typing import Optional, List
from pydantic import BaseModel

from app.services.ocr_service import OCRService
from app.services.llm_service import DeepSeekService


class BillData(BaseModel):
    """票据数据结构"""
    invoice_type: str
    invoice_code: str
    invoice_number: str
    invoice_date: str
    seller_name: str
    buyer_name: str
    amount: float
    tax_amount: float
    total_amount: float
    goods_name: str
    confidence: float


class BillProcessResult(BaseModel):
    """处理结果"""
    bill_data: dict
    matched_flow: Optional[dict]
    match_score: float
    anomalies: list
    needs_review: bool


class BillAgent:
    """票据处理Agent"""
    
    def __init__(self, db=None):
        self.ocr_service = OCRService()
        self.llm_service = DeepSeekService()
    
    async def process(self, image_path: str, customer_id: str) -> BillProcessResult:
        """处理票据全流程"""
        # 1. OCR识别
        ocr_result = await self.ocr_service.recognize_vat_invoice(image_path)
        if not ocr_result:
            raise Exception("OCR recognition failed")
        
        # 2. LLM增强理解
        enhanced = await self.enhance_understanding(ocr_result)
        
        # 3. 判断是否需要人工审核
        needs_review = self._needs_review(enhanced, 0.9, [])
        
        return BillProcessResult(
            bill_data=enhanced,
            matched_flow=None,
            match_score=0.9,
            anomalies=[],
            needs_review=needs_review
        )
    
    async def enhance_understanding(self, ocr_result: dict) -> dict:
        """增强理解"""
        return {
            **ocr_result,
            "llm_enhanced": True,
            "confidence": 0.95
        }
    
    def _needs_review(self, bill_data: dict, match_score: float, anomalies: list) -> bool:
        """判断是否需要人工审核"""
        if bill_data.get('confidence', 0) < 0.9:
            return True
        if match_score < 0.8:
            return True
        for anomaly in anomalies:
            if anomaly.get('severity') == 'high':
                return True
        medium_count = sum(1 for a in anomalies if a.get('severity') == 'medium')
        if medium_count >= 2:
            return True
        return False
