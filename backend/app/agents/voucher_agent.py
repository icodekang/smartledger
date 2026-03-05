from typing import List, Dict
from pydantic import BaseModel

from app.services.llm_service import DeepSeekService
from app.services.rule_engine import RuleEngine


class VoucherEntry(BaseModel):
    """分录项"""
    subject_code: str
    subject_name: str
    debit: float
    credit: float
    summary: str


class VoucherDraft(BaseModel):
    """凭证草稿"""
    voucher_date: str
    summary: str
    entries: List[VoucherEntry]
    confidence: float
    reason: str
    needs_review: bool


class VoucherAgent:
    """记账核算Agent"""
    
    def __init__(self):
        self.llm_service = DeepSeekService()
        self.rule_engine = RuleEngine()
    
    async def generate(self, bill_data: Dict, customer_context: Dict) -> VoucherDraft:
        """生成凭证草稿"""
        # 1. 尝试规则匹配
        rule_result = self.rule_engine.match(bill_data, customer_context)
        
        if rule_result:
            rule_id, entries = rule_result
            confidence = 95
            reason = f"规则匹配: {rule_id}"
        else:
            # 2. 使用LLM推荐
            llm_result = await self.recommend_with_llm(bill_data, customer_context)
            
            if llm_result:
                entries = llm_result.get("entries", [])
                confidence = llm_result.get("confidence", 50)
                reason = f"AI推荐: {llm_result.get('reasoning', '')}"
            else:
                entries = []
                confidence = 0
                reason = "无法生成凭证"
        
        needs_review = confidence < 85
        
        return VoucherDraft(
            voucher_date=bill_data.get('invoice_date'),
            summary=self._generate_summary(bill_data),
            entries=[VoucherEntry(**e) for e in entries],
            confidence=confidence,
            reason=reason,
            needs_review=needs_review
        )
    
    async def generate_voucher_from_bill(self, bill, db) -> Dict:
        """从票据生成凭证数据"""
        # 构建票据数据
        bill_data = {
            "invoice_type": bill.bill_type,
            "invoice_code": bill.invoice_code,
            "invoice_number": bill.invoice_number,
            "invoice_date": bill.invoice_date.isoformat() if bill.invoice_date else None,
            "seller_name": bill.seller_name,
            "amount": float(bill.amount) if bill.amount else 0,
            "tax_amount": float(bill.tax_amount) if bill.tax_amount else 0,
            "total_amount": float(bill.total_amount) if bill.total_amount else 0,
            "goods_name": bill.ocr_result.get("goods_name", "") if bill.ocr_result else ""
        }
        
        # 获取客户上下文
        from app.repositories.customer import CustomerRepository
        customer_repo = CustomerRepository()
        customer = customer_repo.get(db, bill.customer_id)
        
        customer_context = {
            "taxpayer_type": "general",  # 默认为一般纳税人
            "industry": ""
        }
        if customer:
            customer_context = {
                "taxpayer_type": getattr(customer, "taxpayer_type", "general"),
                "industry": getattr(customer, "industry", "")
            }
        
        # 生成凭证
        draft = await self.generate(bill_data, customer_context)
        
        return {
            "summary": draft.summary,
            "entries": [entry.dict() for entry in draft.entries],
            "confidence": draft.confidence,
            "reason": draft.reason
        }
    
    async def recommend_with_llm(self, bill_data: Dict, customer_context: Dict) -> Dict:
        """使用LLM推荐"""
        from app.agents.prompts.bill_prompts import VOUCHER_GENERATION_PROMPT
        
        prompt = f"""根据以下票据信息生成会计分录：
票据类型: {bill_data.get('invoice_type')}
金额: {bill_data.get('total_amount')}
商品: {bill_data.get('goods_name')}
纳税人类型: {customer_context.get('taxpayer_type', 'general')}

请以JSON格式返回：
{{
    "entries": [
        {{"subject_code": "科目代码", "subject_name": "科目名称", "debit": 借方金额, "credit": 贷方金额, "summary": "摘要"}}
    ],
    "confidence": 置信度0-100,
    "reasoning": "推理说明"
}}"""
        
        return await self.llm_service.json_completion(
            system_prompt=VOUCHER_GENERATION_PROMPT,
            user_prompt=prompt
        )
    
    def _generate_summary(self, bill_data: Dict) -> str:
        """生成摘要"""
        goods_name = bill_data.get('goods_name', '')
        seller_name = bill_data.get('seller_name', '')
        
        if goods_name:
            return f"采购{goods_name}"
        elif seller_name:
            return f"应付{seller_name}货款"
        else:
            return "采购商品"
