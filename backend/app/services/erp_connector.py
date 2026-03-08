"""
ERP连接器实现
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import random
import uuid


@dataclass
class ERPSubject:
    """ERP科目"""
    code: str
    name: str
    category: str
    parent_code: str = None


@dataclass
class ERPVoucher:
    """ERP凭证"""
    voucher_no: str
    voucher_date: date
    period: str
    summary: str
    entries: List[Dict]


class ERPConnector(ABC):
    """ERP连接器基类"""
    
    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接"""
        pass
    
    @abstractmethod
    def get_subjects(self) -> List[ERPSubject]:
        """获取科目列表"""
        pass
    
    @abstractmethod
    def export_vouchers(self, start_date: date, end_date: date) -> List[ERPVoucher]:
        """导出凭证"""
        pass
    
    @abstractmethod
    def import_vouchers(self, vouchers: List[ERPVoucher]) -> bool:
        """导入凭证"""
        pass


class KingdeeK3Connector(ERPConnector):
    """金蝶K3连接器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.erp_type = "kingdee"
    
    def test_connection(self) -> bool:
        """测试连接"""
        # 模拟连接测试
        return True
    
    def get_subjects(self) -> List[ERPSubject]:
        """获取金蝶K3科目"""
        # 模拟科目数据
        return [
            ERPSubject("1001", "库存现金", "资产"),
            ERPSubject("1002", "银行存款", "资产"),
            ERPSubject("1122", "应收账款", "资产"),
            ERPSubject("1403", "原材料", "资产"),
            ERPSubject("1405", "库存商品", "资产"),
            ERPSubject("1601", "固定资产", "资产"),
            ERPSubject("2001", "短期借款", "负债"),
            ERPSubject("2202", "应付账款", "负债"),
            ERPSubject("2221", "应交税费", "负债"),
            ERPSubject("4001", "实收资本", "权益"),
            ERPSubject("6001", "主营业务收入", "损益"),
            ERPSubject("6401", "主营业务成本", "损益"),
            ERPSubject("6601", "销售费用", "损益"),
            ERPSubject("6602", "管理费用", "损益"),
            ERPSubject("6603", "财务费用", "损益"),
        ]
    
    def export_vouchers(self, start_date: date, end_date: date) -> List[ERPVoucher]:
        """从K3导出凭证"""
        # 模拟导出凭证
        vouchers = []
        for i in range(random.randint(5, 15)):
            vouchers.append(ERPVoucher(
                voucher_no=f"K3-{start_date.strftime('%Y%m')}-{i+1:04d}",
                voucher_date=start_date,
                period=start_date.strftime("%Y%m"),
                summary=f"模拟凭证-{i+1}",
                entries=[
                    {"subject_code": "1001", "subject_name": "库存现金", "debit": 1000.00, "credit": 0},
                    {"subject_code": "6001", "subject_name": "主营业务收入", "debit": 0, "credit": 1000.00},
                ]
            ))
        return vouchers
    
    def import_vouchers(self, vouchers: List[ERPVoucher]) -> bool:
        """导入凭证到K3"""
        # 模拟导入成功
        return True


class YonyouU8Connector(ERPConnector):
    """用友U8连接器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.erp_type = "yonyou"
    
    def test_connection(self) -> bool:
        return True
    
    def get_subjects(self) -> List[ERPSubject]:
        return [
            ERPSubject("1001", "库存现金", "资产"),
            ERPSubject("1002", "银行存款", "资产"),
            ERPSubject("1131", "应收账款", "资产"),
            ERPSubject("1201", "物资采购", "资产"),
            ERPSubject("1243", "库存商品", "资产"),
            ERPSubject("1501", "固定资产", "资产"),
            ERPSubject("2101", "短期借款", "负债"),
            ERPSubject("2121", "应付账款", "负债"),
            ERPSubject("2171", "应交税费", "负债"),
            ERPSubject("3101", "实收资本", "权益"),
            ERPSubject("5101", "主营业务收入", "损益"),
            ERPSubject("5401", "主营业务成本", "损益"),
            ERPSubject("5501", "营业费用", "损益"),
            ERPSubject("5502", "管理费用", "损益"),
            ERPSubject("5503", "财务费用", "损益"),
        ]
    
    def export_vouchers(self, start_date: date, end_date: date) -> List[ERPVoucher]:
        vouchers = []
        for i in range(random.randint(5, 15)):
            vouchers.append(ERPVoucher(
                voucher_no=f"U8-{start_date.strftime('%Y%m')}-{i+1:04d}",
                voucher_date=start_date,
                period=start_date.strftime("%Y%m"),
                summary=f"模拟凭证-{i+1}",
                entries=[
                    {"subject_code": "1002", "subject_name": "银行存款", "debit": 5000.00, "credit": 0},
                    {"subject_code": "5101", "subject_name": "主营业务收入", "debit": 0, "credit": 5000.00},
                ]
            ))
        return vouchers
    
    def import_vouchers(self, vouchers: List[ERPVoucher]) -> bool:
        return True


class SAPConnector(ERPConnector):
    """SAP连接器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.erp_type = "sap"
    
    def test_connection(self) -> bool:
        return True
    
    def get_subjects(self) -> List[ERPSubject]:
        return [
            ERPSubject("100000", "现金", "资产"),
            ERPSubject("110000", "银行存款", "资产"),
            ERPSubject("140000", "应收账款", "资产"),
            ERPSubject("300000", "原材料", "资产"),
            ERPSubject("500000", "库存商品", "资产"),
            ERPSubject("800000", "固定资产", "资产"),
        ]
    
    def export_vouchers(self, start_date: date, end_date: date) -> List[ERPVoucher]:
        return []
    
    def import_vouchers(self, vouchers: List[ERPVoucher]) -> bool:
        return True


class ERPConnectorFactory:
    """ERP连接器工厂"""
    
    _connectors = {
        "kingdee": KingdeeK3Connector,
        "yonyou": YonyouU8Connector,
        "sap": SAPConnector,
    }
    
    @classmethod
    def get_connector(cls, erp_type: str, config: Dict) -> ERPConnector:
        """获取ERP连接器"""
        connector_class = cls._connectors.get(erp_type)
        if not connector_class:
            raise ValueError(f"不支持的ERP类型: {erp_type}")
        return connector_class(config)
    
    @classmethod
    def get_supported_erps(cls) -> List[Dict]:
        """获取支持的ERP列表"""
        return [
            {"code": "kingdee", "name": "金蝶K3/KIS", "versions": ["K3 WISE", "KIS专业版"]},
            {"code": "yonyou", "name": "用友U8/T+", "versions": ["U8+", "T+"]},
            {"code": "sap", "name": "SAP", "versions": ["S/4HANA", "ECC"]},
        ]


class SubjectMappingService:
    """科目映射服务"""
    
    @staticmethod
    def auto_match(erp_subjects: List[ERPSubject], local_subjects: List[Dict]) -> Dict[str, str]:
        """自动匹配科目"""
        from difflib import SequenceMatcher
        
        mapping = {}
        
        for erp_subj in erp_subjects:
            best_match = None
            best_score = 0
            
            for local_subj in local_subjects:
                # 名称相似度
                name_sim = SequenceMatcher(
                    None,
                    erp_subj.name,
                    local_subj.get("name", "")
                ).ratio()
                
                # 代码相同增加权重
                code_sim = 1.0 if erp_subj.code == local_subj.get("code") else 0.0
                
                # 综合得分
                score = name_sim * 0.7 + code_sim * 0.3
                
                if score > best_score and score > 0.6:
                    best_score = score
                    best_match = local_subj
            
            if best_match:
                mapping[erp_subj.code] = best_match.get("code")
        
        return mapping
