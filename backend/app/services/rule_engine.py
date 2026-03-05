from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class VoucherRule:
    """记账规则"""
    id: str
    name: str
    conditions: Dict
    debit_subject: str
    credit_subject: str
    priority: int = 0


class RuleEngine:
    """规则引擎"""
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[VoucherRule]:
        """加载规则"""
        return [
            VoucherRule(
                id="purchase_goods_general",
                name="采购商品-一般纳税人",
                conditions={
                    "invoice_type": ["vat_special"],
                    "business_scene": "purchase",
                    "taxpayer_type": "general"
                },
                debit_subject="1403",
                credit_subject="2202",
                priority=100
            ),
            VoucherRule(
                id="purchase_goods_small",
                name="采购商品-小规模纳税人",
                conditions={
                    "invoice_type": ["vat_normal", "vat_special"],
                    "business_scene": "purchase",
                    "taxpayer_type": "small"
                },
                debit_subject="1403",
                credit_subject="2202",
                priority=90
            ),
            VoucherRule(
                id="office_expense",
                name="办公费",
                conditions={
                    "business_scene": "expense",
                    "keywords": ["办公", "文具", "耗材"]
                },
                debit_subject="560201",
                credit_subject="2202",
                priority=80
            ),
            VoucherRule(
                id="travel_expense",
                name="差旅费",
                conditions={
                    "business_scene": "expense",
                    "keywords": ["差旅", "车票", "机票", "住宿"]
                },
                debit_subject="560202",
                credit_subject="2202",
                priority=80
            ),
            VoucherRule(
                id="entertainment_expense",
                name="业务招待费",
                conditions={
                    "business_scene": "expense",
                    "keywords": ["餐饮", "招待", "礼品"]
                },
                debit_subject="560203",
                credit_subject="2202",
                priority=80
            ),
        ]
    
    def match(self, bill_data: Dict, customer_context: Dict) -> Optional[Tuple[str, List[Dict]]]:
        """匹配规则"""
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if self._check_conditions(rule.conditions, bill_data, customer_context):
                entries = self._generate_entries(rule, bill_data, customer_context)
                return rule.id, entries
        
        return None
    
    def _check_conditions(self, conditions: Dict, bill_data: Dict, customer_context: Dict) -> bool:
        """检查条件"""
        for key, expected in conditions.items():
            if key == "keywords":
                goods_name = bill_data.get("goods_name", "")
                if not any(kw in goods_name for kw in expected):
                    return False
            elif key == "taxpayer_type":
                actual = customer_context.get("taxpayer_type")
                if actual != expected:
                    return False
            else:
                actual = bill_data.get(key)
                if isinstance(expected, list):
                    if actual not in expected:
                        return False
                else:
                    if actual != expected:
                        return False
        return True
    
    def _generate_entries(self, rule: VoucherRule, bill_data: Dict, customer_context: Dict) -> List[Dict]:
        """生成分录"""
        amount = bill_data.get("amount", 0)
        tax_amount = bill_data.get("tax_amount", 0)
        total_amount = bill_data.get("total_amount", 0)
        
        is_general = customer_context.get("taxpayer_type") == "general"
        has_tax = tax_amount and tax_amount > 0
        
        entries = []
        
        if is_general and has_tax:
            entries.append({
                "subject_code": rule.debit_subject,
                "subject_name": self._get_subject_name(rule.debit_subject),
                "debit": amount,
                "credit": 0,
                "summary": f"采购{bill_data.get('goods_name', '商品')}"
            })
            entries.append({
                "subject_code": "222101",
                "subject_name": "应交税费-应交增值税-进项税额",
                "debit": tax_amount,
                "credit": 0,
                "summary": "进项税额"
            })
        else:
            entries.append({
                "subject_code": rule.debit_subject,
                "subject_name": self._get_subject_name(rule.debit_subject),
                "debit": total_amount,
                "credit": 0,
                "summary": f"采购{bill_data.get('goods_name', '商品')}"
            })
        
        entries.append({
            "subject_code": rule.credit_subject,
            "subject_name": self._get_subject_name(rule.credit_subject),
            "debit": 0,
            "credit": total_amount,
            "summary": f"应付{bill_data.get('seller_name', '供应商')}货款"
        })
        
        return entries
    
    def _get_subject_name(self, code: str) -> str:
        """获取科目名称"""
        subject_names = {
            "1403": "原材料",
            "2202": "应付账款",
            "560201": "管理费用-办公费",
            "560202": "管理费用-差旅费",
            "560203": "管理费用-业务招待费",
            "222101": "应交税费-应交增值税-进项税额",
        }
        return subject_names.get(code, code)
