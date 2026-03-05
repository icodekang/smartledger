from typing import Tuple, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import func

from app.models.bill import Bill


class BankFlowMatcher:
    """银行流水匹配器"""
    
    def __init__(self, db):
        self.db = db
    
    async def match(
        self,
        customer_id: str,
        amount: float,
        date,
        date_range: int = 3
    ) -> Tuple[Optional[dict], float]:
        """匹配银行流水"""
        flows = await self.get_unmatched_flows(customer_id, date, date_range)
        
        if not flows:
            return None, 0.0
        
        candidates = []
        for flow in flows:
            score = self._calculate_match_score(flow, amount, date)
            if score > 0.6:
                candidates.append((flow, score))
        
        if candidates:
            best_match = max(candidates, key=lambda x: x[1])
            return best_match
        
        return None, 0.0
    
    async def get_unmatched_flows(
        self,
        customer_id: str,
        date,
        date_range: int
    ) -> List[dict]:
        """获取待匹配的流水"""
        from app.models.bank_flow import BankFlow
        
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        start_date = date - timedelta(days=date_range)
        end_date = date + timedelta(days=date_range)
        
        flows = self.db.query(BankFlow).filter(
            BankFlow.customer_id == customer_id,
            BankFlow.is_matched == False,
            BankFlow.transaction_date >= start_date,
            BankFlow.transaction_date <= end_date
        ).all()
        
        return [self._flow_to_dict(f) for f in flows]
    
    def _calculate_match_score(
        self,
        flow: dict,
        target_amount: float,
        target_date
    ) -> float:
        """计算匹配分数"""
        score = 0.0
        
        # 金额匹配 (权重50%)
        flow_amount = flow.get('credit_amount') or flow.get('debit_amount', 0)
        if flow_amount and target_amount:
            if abs(flow_amount - target_amount) < 0.01:
                score += 0.5
            elif abs(flow_amount - target_amount) / target_amount < 0.05:
                score += 0.3
            elif abs(flow_amount - target_amount) / target_amount < 0.1:
                score += 0.1
        
        # 日期匹配 (权重30%)
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        flow_date = flow.get('transaction_date')
        if flow_date and target_date:
            if flow_date == target_date:
                score += 0.3
            else:
                day_diff = abs((flow_date - target_date).days)
                if day_diff <= 1:
                    score += 0.25
                elif day_diff <= 3:
                    score += 0.2
                elif day_diff <= 7:
                    score += 0.1
        
        # 摘要关键词匹配 (权重20%)
        summary = flow.get('summary', '')
        keywords = ['货款', '采购', '材料', '商品', '服务', '咨询']
        if any(kw in summary for kw in keywords):
            score += 0.2
        
        return min(score, 1.0)
    
    def _flow_to_dict(self, flow) -> dict:
        """转换为字典"""
        return {
            'id': str(flow.id),
            'transaction_date': flow.transaction_date,
            'transaction_time': flow.transaction_time,
            'counterparty': flow.counterparty,
            'debit_amount': float(flow.debit_amount) if flow.debit_amount else 0,
            'credit_amount': float(flow.credit_amount) if flow.credit_amount else 0,
            'summary': flow.summary
        }
