"""
开放平台服务
TASK-OPEN-01: 开放API平台
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid
import hashlib
import hmac


class OpenAPIPlatform:
    """开放API平台"""
    
    # API密钥管理
    @staticmethod
    def generate_api_key() -> Dict[str, str]:
        """生成API密钥对"""
        api_key = f"ak_{uuid.uuid4().hex[:24]}"
        api_secret = f"sk_{uuid.uuid4().hex}"
        
        return {
            "api_key": api_key,
            "api_secret": api_secret,
            "created_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def verify_signature(api_key: str, api_secret: str, params: Dict, signature: str) -> bool:
        """验证API签名"""
        # 按参数名排序
        sorted_params = sorted(params.items())
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        
        # 生成签名
        expected_signature = hmac.new(
            api_secret.encode(),
            param_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)


class APIDocumentation:
    """API文档生成"""
    
    API_ENDPOINTS = [
        {
            "path": "/api/v1/bills",
            "method": "GET",
            "description": "获取票据列表",
            "parameters": [
                {"name": "page", "type": "integer", "required": False, "default": 1},
                {"name": "page_size", "type": "integer", "required": False, "default": 20},
                {"name": "status", "type": "string", "required": False}
            ],
            "response": {
                "code": 200,
                "data": {
                    "items": "array",
                    "total": "integer"
                }
            }
        },
        {
            "path": "/api/v1/bills",
            "method": "POST",
            "description": "创建票据",
            "parameters": [
                {"name": "invoice_code", "type": "string", "required": True},
                {"name": "invoice_number", "type": "string", "required": True},
                {"name": "amount", "type": "number", "required": True}
            ]
        },
        {
            "path": "/api/v1/vouchers",
            "method": "GET",
            "description": "获取凭证列表",
            "parameters": [
                {"name": "period", "type": "string", "required": False},
                {"name": "status", "type": "string", "required": False}
            ]
        }
    ]
    
    @classmethod
    def get_documentation(cls) -> List[Dict]:
        """获取API文档"""
        return cls.API_ENDPOINTS


class APIRateLimiter:
    """API限流器"""
    
    # 限流配置
    RATE_LIMITS = {
        "free": {"requests": 100, "window": 3600},      # 免费版: 100次/小时
        "basic": {"requests": 1000, "window": 3600},   # 基础版: 1000次/小时
        "pro": {"requests": 10000, "window": 3600},    # 专业版: 10000次/小时
        "enterprise": {"requests": 100000, "window": 3600}  # 企业版: 100000次/小时
    }
    
    @classmethod
    def check_rate_limit(cls, api_key: str, tier: str = "free") -> tuple[bool, Dict]:
        """检查限流"""
        limit = cls.RATE_LIMITS.get(tier, cls.RATE_LIMITS["free"])
        
        # 简化的限流检查（实际应使用Redis）
        return True, {
            "limit": limit["requests"],
            "window": limit["window"],
            "remaining": limit["requests"] - 1,
            "reset_at": (datetime.utcnow() + timedelta(seconds=limit["window"])).isoformat()
        }


class SDKGenerator:
    """SDK生成器"""
    
    @staticmethod
    def generate_python_sdk() -> str:
        """生成Python SDK代码"""
        code = '''
"""
SmartLedger Python SDK
"""
import requests
from typing import Optional, Dict, List

class SmartLedgerClient:
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://api.smartledger.ai"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
    
    def _generate_signature(self, params: Dict) -> str:
        import hmac
        import hashlib
        sorted_params = sorted(params.items())
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        return hmac.new(
            self.api_secret.encode(),
            param_str.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def get_bills(self, page: int = 1, page_size: int = 20) -> List[Dict]:
        """获取票据列表"""
        params = {"page": page, "page_size": page_size}
        params["api_key"] = self.api_key
        params["signature"] = self._generate_signature(params)
        
        response = requests.get(f"{self.base_url}/api/v1/bills", params=params)
        return response.json()
    
    def create_bill(self, invoice_code: str, invoice_number: str, amount: float) -> Dict:
        """创建票据"""
        data = {
            "invoice_code": invoice_code,
            "invoice_number": invoice_number,
            "amount": amount
        }
        data["api_key"] = self.api_key
        data["signature"] = self._generate_signature(data)
        
        response = requests.post(f"{self.base_url}/api/v1/bills", json=data)
        return response.json()
'''
        return code
    
    @staticmethod
    def generate_javascript_sdk() -> str:
        """生成JavaScript SDK代码"""
        code = '''
/**
 * SmartLedger JavaScript SDK
 */
class SmartLedgerClient {
  constructor(apiKey, apiSecret, baseUrl = 'https://api.smartledger.ai') {
    this.apiKey = apiKey;
    this.apiSecret = apiSecret;
    this.baseUrl = baseUrl;
  }
  
  _generateSignature(params) {
    const sortedParams = Object.keys(params).sort().map(k => `${k}=${params[k]}`).join('&');
    // 使用 crypto-js 进行签名
    return CryptoJS.HmacSHA256(sortedParams, this.apiSecret).toString();
  }
  
  async getBills(page = 1, pageSize = 20) {
    const params = { page, page_size: pageSize, api_key: this.apiKey };
    params.signature = this._generateSignature(params);
    
    const response = await fetch(`${this.baseUrl}/api/v1/bills?${new URLSearchParams(params)}`);
    return response.json();
  }
}
'''
        return code
