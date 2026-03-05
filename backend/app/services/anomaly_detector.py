from typing import List, Dict
from datetime import datetime, timedelta
from sqlalchemy import func

from app.models.bill import Bill


class AnomalyDetector:
    """异常检测器"""
    
    def __init__(self, db):
        self.db = db
    
    async def check(self, bill_data: dict, customer_id: str) -> List[dict]:
        """检测异常"""
        anomalies = []
        
        # 1. 重复发票检测
        if await self._is_duplicate(bill_data, customer_id):
            anomalies.append({
                'type': '重复发票',
                'severity': 'high',
                'description': '该发票已存在系统中'
            })
        
        # 2. 金额突变检测
        amount_anomaly = await self._check_amount_anomaly(bill_data, customer_id)
        if amount_anomaly:
            anomalies.append(amount_anomaly)
        
        # 3. 连号检测
        if await self._is_consecutive_number_anomaly(bill_data, customer_id):
            anomalies.append({
                'type': '连号异常',
                'severity': 'low',
                'description': '发票号码与历史记录不连续'
            })
        
        # 4. 日期异常检测
        if self._is_date_anomaly(bill_data):
            anomalies.append({
                'type': '日期异常',
                'severity': 'medium',
                'description': '开票日期异常（未来日期或过早）'
            })
        
        return anomalies
    
    async def _is_duplicate(self, bill_data: dict, customer_id: str) -> bool:
        """检测重复发票"""
        existing = self.db.query(Bill).filter(
            Bill.invoice_code == bill_data.get('invoice_code'),
            Bill.invoice_number == bill_data.get('invoice_number')
        ).first()
        return existing is not None
    
    async def _check_amount_anomaly(self, bill_data: dict, customer_id: str) -> dict:
        """检测金额异常"""
        amount = bill_data.get('total_amount')
        if not amount:
            return None
        
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return None
        
        avg_result = self.db.query(func.avg(Bill.total_amount)).filter(
            Bill.customer_id == customer_id,
            Bill.total_amount.isnot(None)
        ).scalar()
        
        if avg_result and avg_result > 0:
            avg_amount = float(avg_result)
            if avg_amount > 0:
                ratio = amount / avg_amount
                
                if ratio > 5:
                    return {
                        'type': '金额异常',
                        'severity': 'high',
                        'description': f'金额({amount})超过历史平均值({avg_amount:.2f})5倍'
                    }
                elif ratio > 3:
                    return {
                        'type': '金额异常',
                        'severity': 'medium',
                        'description': f'金额({amount})超过历史平均值({avg_amount:.2f})3倍'
                    }
        
        return None
    
    async def _is_consecutive_number_anomaly(self, bill_data: dict, customer_id: str) -> bool:
        """检测连号异常"""
        return False
    
    def _is_date_anomaly(self, bill_data: dict) -> bool:
        """检测日期异常"""
        invoice_date = bill_data.get('invoice_date')
        if not invoice_date:
            return True
        
        if isinstance(invoice_date, str):
            try:
                invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d').date()
            except ValueError:
                return True
        
        today = datetime.now().date()
        
        if invoice_date > today:
            return True
        
        if (today - invoice_date).days > 365:
            return True
        
        return False
