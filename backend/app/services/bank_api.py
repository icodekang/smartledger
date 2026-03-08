"""
银行API抽象层和实现
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import random
import uuid


@dataclass
class AuthResult:
    """授权结果"""
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass
class BalanceResult:
    """余额查询结果"""
    account_no: str
    balance: Decimal
    available_balance: Decimal
    currency: str


@dataclass
class Transaction:
    """交易记录"""
    transaction_date: date
    transaction_time: str
    amount: Decimal
    balance: Decimal
    counterparty_name: str
    counterparty_account: str
    summary: str
    reference_no: str


class BankAPIInterface(ABC):
    """银行API接口抽象基类"""
    
    @abstractmethod
    def authenticate(self, credentials: dict) -> AuthResult:
        """用户授权认证"""
        pass
    
    @abstractmethod
    def query_balance(self, account_no: str) -> BalanceResult:
        """查询账户余额"""
        pass
    
    @abstractmethod
    def query_transactions(
        self, 
        account_no: str, 
        start_date: date, 
        end_date: date
    ) -> List[Transaction]:
        """查询交易流水"""
        pass
    
    @abstractmethod
    def refresh_token(self, refresh_token: str) -> AuthResult:
        """刷新访问令牌"""
        pass
    
    def get_auth_url(self, redirect_uri: str, state: str = None) -> str:
        """获取授权页面URL"""
        return f"https://example.com/oauth/authorize?redirect_uri={redirect_uri}&state={state or ''}"


class MockBankAPI(BankAPIInterface):
    """模拟银行API（用于开发和测试）"""
    
    def __init__(self, bank_code: str):
        self.bank_code = bank_code
        self.access_token = None
    
    def authenticate(self, credentials: dict) -> AuthResult:
        """模拟认证"""
        return AuthResult(
            access_token=f"mock_token_{uuid.uuid4()}",
            refresh_token=f"mock_refresh_{uuid.uuid4()}",
            expires_in=7200
        )
    
    def query_balance(self, account_no: str) -> BalanceResult:
        """模拟查询余额"""
        return BalanceResult(
            account_no=account_no,
            balance=Decimal(str(random.randint(10000, 1000000))),
            available_balance=Decimal(str(random.randint(10000, 1000000))),
            currency="CNY"
        )
    
    def query_transactions(
        self, 
        account_no: str, 
        start_date: date, 
        end_date: date
    ) -> List[Transaction]:
        """模拟查询交易流水"""
        transactions = []
        days = (end_date - start_date).days
        
        for i in range(min(days * 3, 100)):  # 每天平均3笔
            amount = Decimal(str(random.uniform(-10000, 10000)))
            transactions.append(Transaction(
                transaction_date=start_date,
                transaction_time=f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}",
                amount=amount,
                balance=Decimal(str(random.randint(10000, 1000000))),
                counterparty_name=random.choice(["XX科技公司", "YY贸易公司", "ZZ服务部", ""]),
                counterparty_account=f"6222{random.randint(100000000000, 999999999999)}",
                summary=random.choice(["货款", "服务费", "转账", "报销"]),
                reference_no=f"TRX{uuid.uuid4().hex[:16].upper()}"
            ))
        
        return transactions
    
    def refresh_token(self, refresh_token: str) -> AuthResult:
        """模拟刷新token"""
        return self.authenticate({})


class ICBCAPI(MockBankAPI):
    """工商银行API实现"""
    BASE_URL = "https://api.icbc.com.cn"
    
    def __init__(self):
        super().__init__("icbc")
    
    def get_auth_url(self, redirect_uri: str, state: str = None) -> str:
        return f"{self.BASE_URL}/oauth2/authorize?app_id=ICBC_APP&redirect_uri={redirect_uri}&state={state or ''}"


class CCBAPI(MockBankAPI):
    """建设银行API实现"""
    BASE_URL = "https://api.ccb.com"
    
    def __init__(self):
        super().__init__("ccb")
    
    def get_auth_url(self, redirect_uri: str, state: str = None) -> str:
        return f"{self.BASE_URL}/oauth/authorize?client_id=CCB_APP&redirect_uri={redirect_uri}&state={state or ''}"


class CMBAPI(MockBankAPI):
    """招商银行API实现"""
    BASE_URL = "https://api.cmbchina.com"
    
    def __init__(self):
        super().__init__("cmb")
    
    def get_auth_url(self, redirect_uri: str, state: str = None) -> str:
        return f"{self.BASE_URL}/oauth2/authorize?appid=CMB_APP&redirect_uri={redirect_uri}&state={state or ''}"


# 银行API工厂
class BankAPIFactory:
    """银行API工厂"""
    
    _apis = {
        "icbc": ICBCAPI,
        "ccb": CCBAPI,
        "cmb": CMBAPI,
        "mock": MockBankAPI,
    }
    
    _bank_names = {
        "icbc": "中国工商银行",
        "ccb": "中国建设银行",
        "cmb": "招商银行",
        "mock": "模拟银行",
    }
    
    @classmethod
    def get_api(cls, bank_code: str) -> BankAPIInterface:
        """获取银行API实例"""
        api_class = cls._apis.get(bank_code)
        if not api_class:
            # 默认返回模拟API
            return MockBankAPI(bank_code)
        return api_class()
    
    @classmethod
    def get_bank_name(cls, bank_code: str) -> str:
        """获取银行名称"""
        return cls._bank_names.get(bank_code, bank_code)
    
    @classmethod
    def get_supported_banks(cls) -> List[Dict]:
        """获取支持的银行列表"""
        return [
            {"code": code, "name": name}
            for code, name in cls._bank_names.items()
        ]
