"""
安全加固配置
"""

# 密码策略配置
PASSWORD_POLICY = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
    "special_chars": "!@#$%^&*(),.?\":{}|<>"
}

# 登录安全配置
LOGIN_PROTECTION = {
    "max_failures": 5,           # 最大失败次数
    "lock_duration": 1800,       # 锁定时间（秒）= 30分钟
    "window_seconds": 300        # 统计窗口（秒）= 5分钟
}

# Token 安全配置
TOKEN_CONFIG = {
    "access_token_expire_minutes": 30,
    "refresh_token_expire_days": 7,
    "algorithm": "HS256"
}

# 文件上传安全配置
UPLOAD_CONFIG = {
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_extensions": [".jpg", ".jpeg", ".png", ".pdf"],
    "allowed_mime_types": ["image/jpeg", "image/png", "application/pdf"]
}

# 安全响应头
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}
