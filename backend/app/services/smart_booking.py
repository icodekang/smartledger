"""
智能记账引擎
"""
from typing import Dict, List, Optional
from decimal import Decimal
import json


class SmartBookingEngine:
    """智能记账引擎"""
    
    # 科目关键词映射
    SUBJECT_KEYWORDS = {
        "1001": ["现金", "备用金"],
        "1002": ["银行", "存款", "转账"],
        "1122": ["应收", "客户", "销售"],
        "1403": ["材料", "原料", "采购"],
        "1405": ["库存", "商品", "产品"],
        "1601": ["设备", "资产", "固定资产"],
        "2001": ["借款", "贷款"],
        "2202": ["应付", "供应商", "采购款"],
        "2221": ["税费", "增值税", "所得税"],
        "4001": ["资本", "投资", "实收"],
        "5001": ["生产", "制造", "成本"],
        "6001": ["收入", "销售", "主营"],
        "6051": ["其他收入", "其他业务"],
        "6401": ["成本", "销售成本"],
        "6601": ["销售费用", "营销", "广告"],
        "6602": ["管理费用", "办公", "工资", "福利"],
        "6603": ["财务费用", "利息", "手续"],
    }
    
    # 行业模板
    INDUSTRY_TEMPLATES = {
        "trade": {
            "name": "贸易公司",
            "common_subjects": ["1405", "6001", "6401", "2202", "1122"],
            "rules": [
                {"pattern": "销售", "debit": "1122", "credit": "6001"},
                {"pattern": "采购", "debit": "1405", "credit": "2202"},
            ]
        },
        "service": {
            "name": "服务公司",
            "common_subjects": ["6602", "6001", "2202", "1122"],
            "rules": [
                {"pattern": "服务费", "debit": "1122", "credit": "6001"},
                {"pattern": "工资", "debit": "6602", "credit": "2202"},
            ]
        },
        "manufacturing": {
            "name": "制造业",
            "common_subjects": ["1403", "5001", "1405", "6001", "6401"],
            "rules": [
                {"pattern": "生产", "debit": "5001", "credit": "1403"},
                {"pattern": "完工", "debit": "1405", "credit": "5001"},
            ]
        }
    }
    
    @classmethod
    def auto_match_subject(cls, description: str) -> Optional[str]:
        """根据描述自动匹配科目"""
        description = description.lower()
        
        best_match = None
        best_score = 0
        
        for subject_code, keywords in cls.SUBJECT_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in description:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = subject_code
        
        return best_match
    
    @classmethod
    def generate_voucher_entries(cls, bill_data: Dict, industry: str = "trade") -> List[Dict]:
        """智能生成分录"""
        description = bill_data.get("summary", "")
        amount = Decimal(str(bill_data.get("total_amount", 0)))
        
        # 根据行业获取模板
        template = cls.INDUSTRY_TEMPLATES.get(industry, cls.INDUSTRY_TEMPLATES["trade"])
        
        # 匹配规则
        for rule in template["rules"]:
            if rule["pattern"] in description:
                return [
                    {"subject_code": rule["debit"], "debit": float(amount), "credit": 0},
                    {"subject_code": rule["credit"], "debit": 0, "credit": float(amount)}
                ]
        
        # 默认分录
        return [
            {"subject_code": "6602", "debit": float(amount), "credit": 0},
            {"subject_code": "1002", "debit": 0, "credit": float(amount)}
        ]
    
    @classmethod
    def analyze_business_type(cls, bill_list: List[Dict]) -> str:
        """分析业务类型"""
        keywords_count = {}
        
        for bill in bill_list:
            summary = bill.get("summary", "")
            for industry, template in cls.INDUSTRY_TEMPLATES.items():
                for rule in template["rules"]:
                    if rule["pattern"] in summary:
                        keywords_count[industry] = keywords_count.get(industry, 0) + 1
        
        if keywords_count:
            return max(keywords_count, key=keywords_count.get)
        return "trade"


class IntelligentClassification:
    """智能分类服务"""
    
    @staticmethod
    def classify_bill(bill_data: Dict) -> Dict:
        """智能分类票据"""
        seller_name = bill_data.get("seller_name", "")
        summary = bill_data.get("summary", "")
        
        # 分类规则
        categories = {
            "办公用品": ["文具", "办公", "耗材"],
            "差旅费": ["机票", "酒店", "车票", "餐饮"],
            "业务招待": ["餐饮", "礼品", "招待"],
            "固定资产": ["电脑", "打印机", "设备", "家具"],
            "原材料": ["材料", "原料", "采购"],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in seller_name or keyword in summary:
                    return {
                        "category": category,
                        "confidence": 0.85,
                        "matched_keyword": keyword
                    }
        
        return {
            "category": "其他",
            "confidence": 0.5,
            "matched_keyword": None
        }


class AnomalyDetector:
    """异常检测服务"""
    
    @staticmethod
    def detect_amount_anomaly(amount: Decimal, historical_avg: Decimal) -> Optional[Dict]:
        """检测金额异常"""
        if historical_avg == 0:
            return None
        
        ratio = amount / historical_avg
        
        if ratio > 3:
            return {
                "type": "amount_too_high",
                "severity": "high",
                "message": f"金额 {amount} 远高于历史平均值 {historical_avg}",
                "ratio": float(ratio)
            }
        elif ratio < 0.1 and amount > 100:
            return {
                "type": "amount_too_low",
                "severity": "medium",
                "message": f"金额 {amount} 远低于历史平均值 {historical_avg}",
                "ratio": float(ratio)
            }
        
        return None
    
    @staticmethod
    def detect_duplicate(bill_data: Dict, existing_bills: List[Dict]) -> Optional[Dict]:
        """检测重复票据"""
        for existing in existing_bills:
            if (existing.get("invoice_code") == bill_data.get("invoice_code") and
                existing.get("invoice_number") == bill_data.get("invoice_number")):
                return {
                    "type": "duplicate_invoice",
                    "severity": "high",
                    "message": "该发票已存在",
                    "existing_id": existing.get("id")
                }
        
        return None
    
    @staticmethod
    def detect_period_anomaly(bill_date: str, current_period: str) -> Optional[Dict]:
        """检测跨期票据"""
        from datetime import datetime
        
        bill_month = bill_date[:7] if len(bill_date) >= 7 else bill_date
        
        if bill_month != current_period:
            return {
                "type": "cross_period",
                "severity": "medium",
                "message": f"票据期间 {bill_month} 与当前账期 {current_period} 不一致",
                "suggestion": "请确认是否计入当前期间"
            }
        
        return None
