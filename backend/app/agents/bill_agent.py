from typing import Optional, List
from pydantic import BaseModel

from app.services.ocr_service import OCRService
from app.services.llm_service import DeepSeekService
from app.services.matcher import BankFlowMatcher
from app.services.anomaly_detector import AnomalyDetector


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
        self.matcher = BankFlowMatcher(db) if db else None
        self.anomaly_detector = AnomalyDetector(db) if db else None
    
    async def process(self, image_path: str, customer_id: str) -> BillProcessResult:
        """处理票据全流程"""
        # 1. OCR识别
        ocr_result = await self.ocr_service.recognize_vat_invoice(image_path)
        if not ocr_result:
            raise Exception("OCR recognition failed")
        
        # 2. LLM增强理解
        enhanced = await self.enhance_understanding(ocr_result)
        
        # 3. 银行流水匹配
        matched_flow = None
        match_score = 0.0
        if self.matcher and enhanced.get('total_amount'):
            try:
                amount = float(enhanced['total_amount'])
                matched_flow, match_score = await self.matcher.match(
                    customer_id=customer_id,
                    amount=amount,
                    date=enhanced.get('invoice_date')
                )
            except (ValueError, TypeError):
                pass
        
        # 4. 异常检测
        anomalies = []
        if self.anomaly_detector:
            anomalies = await self.anomaly_detector.check(enhanced, customer_id)
        
        # 5. 判断是否需要人工审核
        needs_review = self._needs_review(enhanced, match_score, anomalies)
        
        return BillProcessResult(
            bill_data=enhanced,
            matched_flow=matched_flow,
            match_score=match_score,
            anomalies=anomalies,
            needs_review=needs_review
        )
    
    async def process_bill_image(self, image_bytes: bytes, content_type: str) -> Optional[dict]:
        """处理票据图片并返回OCR结果"""
        # 临时保存文件进行OCR
        import tempfile
        import os
        
        suffix = ".jpg" if "jpeg" in content_type else ".png" if "png" in content_type else ".pdf"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        
        try:
            ocr_result = await self.ocr_service.recognize_vat_invoice(tmp_path)
            if ocr_result:
                # 使用LLM增强
                enhanced = await self.enhance_understanding(ocr_result)
                return {
                    "invoice_code": enhanced.get("invoice_code"),
                    "invoice_number": enhanced.get("invoice_number"),
                    "invoice_date": enhanced.get("invoice_date"),
                    "seller_name": enhanced.get("seller_name"),
                    "amount": enhanced.get("amount"),
                    "tax_amount": enhanced.get("tax_amount"),
                    "total_amount": enhanced.get("total_amount"),
                    "confidence": enhanced.get("confidence", 0.9)
                }
            return None
        finally:
            os.unlink(tmp_path)
    
    async def enhance_understanding(self, ocr_result: dict) -> dict:
        """增强理解"""
        from app.agents.prompts.bill_prompts import (
            BILL_UNDERSTANDING_SYSTEM_PROMPT,
            build_bill_understanding_prompt
        )
        
        user_prompt = build_bill_understanding_prompt(ocr_result)
        
        llm_result = await self.llm_service.json_completion(
            system_prompt=BILL_UNDERSTANDING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3
        )
        
        if not llm_result:
            return {**ocr_result, "llm_enhanced": False, "confidence": 50}
        
        return {
            **ocr_result,
            **{k: v for k, v in llm_result.items() if v is not None},
            "llm_enhanced": True
        }
    
    def _needs_review(self, bill_data: dict, match_score: float, anomalies: list) -> bool:
        """判断是否需要人工审核"""
        confidence = bill_data.get('confidence', 0)
        if isinstance(confidence, str):
            try:
                confidence = float(confidence)
            except ValueError:
                confidence = 0
        
        if confidence < 90:
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
