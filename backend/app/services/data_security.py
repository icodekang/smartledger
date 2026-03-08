"""
数据安全加固服务
TASK-SEC-02: 数据安全加固
"""
import re
from typing import Optional
from datetime import datetime


class DataSecurity:
    """数据安全服务"""
    
    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """身份证号脱敏"""
        if len(id_card) != 18:
            return id_card
        return id_card[:6] + "********" + id_card[16:]
    
    @staticmethod
    def mask_bank_account(account: str) -> str:
        """银行账号脱敏"""
        if len(account) < 8:
            return account
        return account[:4] + "****" + account[-4:]
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """手机号脱敏"""
        if len(phone) != 11:
            return phone
        return phone[:3] + "****" + phone[7:]
    
    @staticmethod
    def mask_email(email: str) -> str:
        """邮箱脱敏"""
        if "@" not in email:
            return email
        local, domain = email.split("@")
        if len(local) <= 2:
            return "*@" + domain
        return local[:2] + "***@" + domain
    
    @staticmethod
    def mask_name(name: str) -> str:
        """姓名脱敏"""
        if len(name) <= 1:
            return name
        return name[0] + "*" * (len(name) - 1)


class SensitiveDataScanner:
    """敏感数据扫描器"""
    
    # 敏感数据模式
    SENSITIVE_PATTERNS = {
        "id_card": r"\d{17}[\dXx]",
        "phone": r"1[3-9]\d{9}",
        "email": r"[\w.-]+@[\w.-]+\.\w+",
        "bank_card": r"\d{16,19}",
    }
    
    @classmethod
    def scan_text(cls, text: str) -> list:
        """扫描文本中的敏感数据"""
        findings = []
        
        for data_type, pattern in cls.SENSITIVE_PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                findings.append({
                    "type": data_type,
                    "value": match.group(),
                    "position": (match.start(), match.end())
                })
        
        return findings
    
    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """清理文本中的敏感数据"""
        result = text
        
        # 身份证号
        result = re.sub(r"\d{17}[\dXx]", lambda m: DataSecurity.mask_id_card(m.group()), result)
        
        # 手机号
        result = re.sub(r"1[3-9]\d{9}", lambda m: DataSecurity.mask_phone(m.group()), result)
        
        # 邮箱
        result = re.sub(r"[\w.-]+@[\w.-]+\.\w+", lambda m: DataSecurity.mask_email(m.group()), result)
        
        return result


class DataClassification:
    """数据分类分级"""
    
    LEVELS = {
        "L1": {"name": "公开", "description": "可公开访问的数据"},
        "L2": {"name": "内部", "description": "企业内部使用"},
        "L3": {"name": "敏感", "description": "敏感业务数据"},
        "L4": {"name": "机密", "description": "高度机密数据"}
    }
    
    CLASSIFICATION_RULES = {
        "L4": ["password", "secret_key", "private_key"],
        "L3": ["bank_account", "id_card", "phone", "email", "salary"],
        "L2": ["customer_name", "address", "contract"],
        "L1": ["company_name", "product_info", "public_doc"]
    }
    
    @classmethod
    def classify_field(cls, field_name: str) -> str:
        """分类字段"""
        field_lower = field_name.lower()
        
        for level, fields in cls.CLASSIFICATION_RULES.items():
            for pattern in fields:
                if pattern in field_lower:
                    return level
        
        return "L2"  # 默认内部级别


class BackupManager:
    """备份管理"""
    
    @staticmethod
    def create_backup_schedule() -> dict:
        """创建备份计划"""
        return {
            "full_backup": {
                "frequency": "weekly",
                "day": "sunday",
                "time": "02:00",
                "retention": 4  # 保留4周
            },
            "incremental_backup": {
                "frequency": "daily",
                "time": "01:00",
                "retention": 7  # 保留7天
            },
            "transaction_log": {
                "frequency": "hourly",
                "retention": 24  # 保留24小时
            }
        }
