import re
from typing import List, Optional
from decimal import Decimal
from datetime import date, timedelta
from difflib import SequenceMatcher

from app.models.bank_flow import BankFlow
from app.models.bill import Bill


class MatchScore:
    """匹配分数结果"""
    def __init__(self, matched: bool, score: float, diff: Optional[Decimal] = None, 
                 similarity: Optional[float] = None, reasons: Optional[List[str]] = None):
        self.matched = matched
        self.score = score
        self.diff = diff
        self.similarity = similarity
        self.reasons = reasons or []


class MatchResult:
    """匹配结果"""
    def __init__(self, bill: Bill, score: float, reasons: List[str], is_auto_match: bool = False):
        self.bill = bill
        self.score = score
        self.reasons = reasons
        self.is_auto_match = is_auto_match
        
    def to_dict(self):
        return {
            "bill_id": str(self.bill.id),
            "bill_no": self.bill.invoice_number,
            "seller_name": self.bill.seller_name,
            "amount": float(self.bill.total_amount) if self.bill.total_amount else 0,
            "invoice_date": self.bill.invoice_date.isoformat() if self.bill.invoice_date else None,
            "score": round(self.score, 2),
            "reasons": self.reasons,
            "is_auto_match": self.is_auto_match
        }


class FlowBillMatcher:
    """流水-票据匹配器"""
    
    # 匹配阈值
    AUTO_MATCH_THRESHOLD = 0.85
    SUGGESTION_THRESHOLD = 0.3
    
    def __init__(self):
        self.amount_weight = 0.5
        self.date_weight = 0.3
        self.name_weight = 0.2
    
    def match(self, flow: BankFlow, bills: List[Bill]) -> List[MatchResult]:
        """
        匹配银行流水与票据列表
        返回按匹配分数排序的结果列表
        """
        results = []
        
        for bill in bills:
            score = 0.0
            reasons = []
            
            # 1. 金额匹配 (权重 50%)
            amount_match = self._match_amount(flow.amount, bill.total_amount)
            score += amount_match.score * self.amount_weight
            if amount_match.matched:
                reasons.append(f"金额匹配")
            
            # 2. 日期匹配 (权重 30%)
            date_match = self._match_date(
                flow.transaction_date,
                bill.invoice_date,
                tolerance_days=3
            )
            score += date_match.score * self.date_weight
            if date_match.matched:
                reasons.append(f"日期相近{date_match.diff}天")
            
            # 3. 对方户名匹配 (权重 20%)
            name_match = self._match_name(
                flow.counterparty_name,
                bill.seller_name
            )
            score += name_match.score * self.name_weight
            if name_match.matched:
                reasons.append(f"名称相似{name_match.similarity:.0%}")
            
            # 只有分数超过建议阈值才加入结果
            if score >= self.SUGGESTION_THRESHOLD:
                results.append(MatchResult(
                    bill=bill,
                    score=score,
                    reasons=reasons,
                    is_auto_match=score >= self.AUTO_MATCH_THRESHOLD
                ))
        
        # 按分数降序排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _match_amount(self, flow_amount: Optional[Decimal], 
                      bill_amount: Optional[Decimal]) -> MatchScore:
        """金额匹配"""
        if flow_amount is None or bill_amount is None:
            return MatchScore(matched=False, score=0.0)
        
        # 使用绝对值比较（收入/支出与票据金额）
        flow_abs = abs(flow_amount)
        bill_abs = abs(bill_amount)
        diff = abs(flow_abs - bill_abs)
        
        if diff == 0:
            return MatchScore(matched=True, score=1.0, diff=diff)
        elif diff < Decimal('0.01'):
            return MatchScore(matched=True, score=0.95, diff=diff)
        elif diff < Decimal('1'):
            return MatchScore(matched=True, score=0.8, diff=diff)
        elif diff < Decimal('10'):
            return MatchScore(matched=True, score=0.6, diff=diff)
        elif diff < Decimal('100'):
            return MatchScore(matched=False, score=0.3, diff=diff)
        else:
            return MatchScore(matched=False, score=0.0, diff=diff)
    
    def _match_date(self, flow_date: Optional[date], 
                    bill_date: Optional[date],
                    tolerance_days: int = 3) -> MatchScore:
        """日期匹配"""
        if flow_date is None or bill_date is None:
            return MatchScore(matched=False, score=0.0)
        
        diff_days = abs((flow_date - bill_date).days)
        
        if diff_days == 0:
            return MatchScore(matched=True, score=1.0, diff=0)
        elif diff_days <= tolerance_days:
            # 在容忍范围内，分数随天数递减
            score = 1.0 - (diff_days / (tolerance_days + 1))
            return MatchScore(matched=True, score=score, diff=diff_days)
        elif diff_days <= 7:
            return MatchScore(matched=False, score=0.5, diff=diff_days)
        elif diff_days <= 30:
            return MatchScore(matched=False, score=0.2, diff=diff_days)
        else:
            return MatchScore(matched=False, score=0.0, diff=diff_days)
    
    def _match_name(self, flow_name: Optional[str], 
                    bill_name: Optional[str]) -> MatchScore:
        """名称匹配"""
        if not flow_name or not bill_name:
            return MatchScore(matched=False, score=0.0)
        
        # 清洗名称
        clean_flow = self._clean_company_name(flow_name)
        clean_bill = self._clean_company_name(bill_name)
        
        if not clean_flow or not clean_bill:
            return MatchScore(matched=False, score=0.0)
        
        # 完全匹配
        if clean_flow == clean_bill:
            return MatchScore(matched=True, score=1.0, similarity=1.0)
        
        # 包含匹配
        if clean_flow in clean_bill or clean_bill in clean_flow:
            return MatchScore(matched=True, score=0.8, similarity=0.8)
        
        # 相似度计算
        similarity = self._calculate_similarity(clean_flow, clean_bill)
        
        if similarity >= 0.8:
            return MatchScore(matched=True, score=similarity * 0.7, similarity=similarity)
        elif similarity >= 0.6:
            return MatchScore(matched=False, score=similarity * 0.5, similarity=similarity)
        else:
            return MatchScore(matched=False, score=similarity * 0.3, similarity=similarity)
    
    def _clean_company_name(self, name: str) -> str:
        """清洗公司名称"""
        if not name:
            return ""
        
        # 去除常见后缀
        suffixes = ['有限公司', '有限责任公司', '股份公司', '股份有限公司', '公司', 
                    'Ltd.', 'Limited', 'Inc.', 'Corp.', 'Co.,']
        result = name
        for suffix in suffixes:
            result = result.replace(suffix, '')
        
        # 去除空格和特殊字符
        result = re.sub(r'[\s\(\)（）.,]', '', result)
        return result.lower().strip()
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度（使用SequenceMatcher）"""
        return SequenceMatcher(None, str1, str2).ratio()
    
    def find_best_match(self, flow: BankFlow, bills: List[Bill]) -> Optional[MatchResult]:
        """找到最佳匹配"""
        results = self.match(flow, bills)
        if not results:
            return None
        
        best = results[0]
        if best.score >= self.AUTO_MATCH_THRESHOLD:
            return best
        return None
