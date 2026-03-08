"""
等保合规安全模块
TASK-SEC-01: 等保三级合规改造
"""
from fastapi import Request, Depends
from functools import wraps
import hashlib
import hmac
import time
from datetime import datetime, timedelta


class SecurityCompliance:
    """等保合规安全服务"""
    
    # 密码策略
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_AGE_DAYS = 90
    PASSWORD_HISTORY_COUNT = 5
    
    # 登录安全
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    SESSION_TIMEOUT_MINUTES = 30
    
    # 审计日志保留天数
    AUDIT_LOG_RETENTION_DAYS = 180
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """密码强度校验（等保要求）"""
        errors = []
        
        if len(password) < 8:
            errors.append("密码长度至少8位")
        
        if not any(c.isupper() for c in password):
            errors.append("必须包含大写字母")
        
        if not any(c.islower() for c in password):
            errors.append("必须包含小写字母")
        
        if not any(c.isdigit() for c in password):
            errors.append("必须包含数字")
        
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
            errors.append("必须包含特殊字符")
        
        if errors:
            return False, "; ".join(errors)
        return True, "密码强度符合要求"
    
    @staticmethod
    def check_password_age(last_changed: datetime) -> bool:
        """检查密码是否过期"""
        max_age = timedelta(days=SecurityCompliance.PASSWORD_MAX_AGE_DAYS)
        return datetime.utcnow() - last_changed < max_age
    
    @staticmethod
    def generate_audit_log(
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        result: str,
        request: Request = None,
        details: dict = None
    ) -> dict:
        """生成审计日志"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,  # LOGIN/LOGOUT/CREATE/UPDATE/DELETE/QUERY
            "resource_type": resource_type,
            "resource_id": resource_id,
            "result": result,  # SUCCESS/FAILURE
            "ip_address": request.client.host if request else None,
            "user_agent": request.headers.get("user-agent") if request else None,
            "details": details or {}
        }
        return log_entry


class DataEncryption:
    """数据加密服务"""
    
    @staticmethod
    def encrypt_sensitive_data(data: str, key: str) -> str:
        """加密敏感数据"""
        # 简化实现，实际应使用AES等算法
        import base64
        encrypted = base64.b64encode(f"{key}:{data}".encode()).decode()
        return f"ENC:{encrypted}"
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data: str, key: str) -> str:
        """解密敏感数据"""
        import base64
        if not encrypted_data.startswith("ENC:"):
            return encrypted_data
        
        encrypted = encrypted_data[4:]
        decrypted = base64.b64decode(encrypted).decode()
        _, data = decrypted.split(":", 1)
        return data
    
    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """密码哈希（PBKDF2）"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        ).hex()


class AccessControl:
    """访问控制服务"""
    
    # 权限矩阵
    PERMISSION_MATRIX = {
        "admin": ["*"],
        "accountant": [
            "bills:read", "bills:create", "bills:update",
            "vouchers:read", "vouchers:create", "vouchers:audit",
            "reports:read"
        ],
        "viewer": ["bills:read", "vouchers:read", "reports:read"],
        "customer": ["bills:read", "bills:create"]
    }
    
    @staticmethod
    def check_permission(user_role: str, required_permission: str) -> bool:
        """检查权限"""
        permissions = AccessControl.PERMISSION_MATRIX.get(user_role, [])
        
        if "*" in permissions:
            return True
        
        return required_permission in permissions
    
    @staticmethod
    def get_data_scope(user_role: str, user_id: str, customer_id: str) -> dict:
        """获取数据访问范围"""
        if user_role == "admin":
            return {"scope": "all"}
        elif user_role == "customer":
            return {"scope": "customer", "customer_id": customer_id}
        else:
            return {"scope": "assigned", "user_id": user_id, "customer_id": customer_id}


class SecurityHeaders:
    """安全响应头"""
    
    @staticmethod
    def get_security_headers() -> dict:
        """获取等保要求的安全响应头"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-Permitted-Cross-Domain-Policies": "none",
            "X-Download-Options": "noopen"
        }


# 等保合规要求清单
COMPLIANCE_REQUIREMENTS = {
    "安全物理环境": [
        "机房物理访问控制",
        "防火、防水、防盗措施",
        "温湿度监控",
        "电力供应保障"
    ],
    "安全通信网络": [
        "网络架构冗余设计",
        "通信传输完整性保护",
        "通信传输保密性保护",
        "可信验证机制"
    ],
    "安全区域边界": [
        "边界防护",
        "访问控制",
        "入侵防范",
        "恶意代码防范"
    ],
    "安全计算环境": [
        "身份鉴别",
        "访问控制",
        "安全审计",
        "数据完整性",
        "数据保密性"
    ],
    "安全管理中心": [
        "系统管理",
        "审计管理",
        "安全管理",
        "集中管控"
    ]
}
