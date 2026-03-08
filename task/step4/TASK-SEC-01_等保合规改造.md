# 任务编号：TASK-SEC-01
# 任务名称：等保合规改造
# 优先级：P0
# 预估工期：3天
# 负责人：后端/前端/运维

================================================================================
                              任务描述
================================================================================

按照等保三级要求进行系统安全改造，包括身份鉴别、访问控制、安全审计、数据安全等方面。

================================================================================
                              需求详情
================================================================================

## 1. 身份鉴别

### 1.1 双因素认证
```python
# 短信验证码登录
@app.post("/api/v1/auth/login-sms")
def login_with_sms(data: SMSLoginRequest):
    """短信验证码登录"""
    
    # 验证图形验证码
    if not verify_captcha(data.captcha_id, data.captcha_code):
        raise HTTPException(400, "图形验证码错误")
    
    # 验证短信验证码
    if not verify_sms_code(data.phone, data.sms_code):
        raise HTTPException(400, "短信验证码错误或已过期")
    
    # 登录
    user = authenticate_by_phone(data.phone)
    return {"token": create_token(user)}


# 双因素认证开关
@app.post("/api/v1/users/{id}/mfa/enable")
def enable_mfa(user_id: str, data: MFAEnableRequest):
    """启用双因素认证"""
    
    # 生成TOTP密钥
    secret = pyotp.random_base32()
    
    # 生成二维码
    totp = pyotp.TOTP(secret)
    qr_url = totp.provisioning_uri(
        name=user.email,
        issuer_name="SmartLedger"
    )
    
    # 验证测试码
    if not totp.verify(data.test_code):
        raise HTTPException(400, "验证码错误")
    
    # 保存密钥
    user.mfa_secret = encrypt(secret)
    user.mfa_enabled = True
    db.commit()
    
    return {"message": "双因素认证已启用"}


@app.post("/api/v1/auth/mfa-verify")
def verify_mfa(data: MFAVerifyRequest):
    """验证双因素认证"""
    
    user = get_user_from_token(data.temp_token)
    
    totp = pyotp.TOTP(decrypt(user.mfa_secret))
    if not totp.verify(data.mfa_code):
        raise HTTPException(400, "双因素认证码错误")
    
    # 颁发正式token
    return {"token": create_token(user)}
```

### 1.2 生物识别支持
```python
# 指纹识别登录（移动端）
@app.post("/api/v1/auth/biometric")
def biometric_login(data: BiometricLoginRequest):
    """生物识别登录"""
    
    # 验证生物识别签名
    if not verify_biometric_signature(
        data.device_id,
        data.biometric_data,
        data.signature
    ):
        raise HTTPException(400, "生物识别验证失败")
    
    user = get_user_by_device(data.device_id)
    return {"token": create_token(user)}
```

## 2. 访问控制强化

### 2.1 基于属性的访问控制（ABAC）
```python
class ABACEngine:
    """属性访问控制引擎"""
    
    def evaluate(self, user: User, resource: Any, action: str, context: dict) -> bool:
        """评估访问权限"""
        
        # 主体属性
        subject_attrs = {
            "role": user.role,
            "department": user.department,
            "security_level": user.security_level,
            "time": datetime.now().hour
        }
        
        # 资源属性
        resource_attrs = {
            "type": resource.__class__.__name__,
            "owner": resource.created_by,
            "classification": resource.classification,
            "department": resource.department
        }
        
        # 环境属性
        env_attrs = {
            "ip": context.get("ip"),
            "location": context.get("location"),
            "device": context.get("device"),
            "time": datetime.now()
        }
        
        # 评估策略
        policies = self._load_policies()
        
        for policy in policies:
            if policy.matches(subject_attrs, resource_attrs, env_attrs, action):
                return policy.effect == "allow"
        
        return False  # 默认拒绝


# 使用示例
@require_abac(action="export", resource_type="financial_report")
def export_report(report_id: str, user: User = Depends(get_current_user)):
    """导出报表（受ABAC控制）"""
    
    report = get_report(report_id)
    context = {
        "ip": request.client.host,
        "location": get_location_by_ip(request.client.host),
        "device": request.headers.get("User-Agent")
    }
    
    engine = ABACEngine()
    if not engine.evaluate(user, report, "export", context):
        raise HTTPException(403, "当前环境不允许导出此报表")
    
    return do_export(report)
```

### 2.2 最小权限原则
```python
# 动态权限分配
def grant_temporary_permission(
    user_id: str,
    resource_id: str,
    action: str,
    duration_minutes: int
):
    """授予临时权限"""
    
    temp_grant = TemporaryPermission(
        user_id=user_id,
        resource_id=resource_id,
        action=action,
        granted_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=duration_minutes)
    )
    db.add(temp_grant)
    db.commit()
    
    # 设置过期自动清理
    revoke_task.apply_async(
        args=[temp_grant.id],
        countdown=duration_minutes * 60
    )
```

## 3. 安全审计强化

### 3.1 全量操作审计
```python
class ComprehensiveAuditLogger:
    """综合审计日志"""
    
    def log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        before_state: dict = None,
        after_state: dict = None,
        context: dict = None
    ):
        """记录审计日志"""
        
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": {
                "type": resource_type,
                "id": resource_id
            },
            "state_changes": {
                "before": self._serialize_state(before_state),
                "after": self._serialize_state(after_state)
            },
            "context": {
                "ip": context.get("ip"),
                "user_agent": context.get("user_agent"),
                "session_id": context.get("session_id"),
                "request_id": context.get("request_id")
            },
            "risk_score": self._calculate_risk_score(action, context)
        }
        
        # 写入审计日志系统（不可篡改存储）
        self._write_to_audit_system(audit_record)
        
        # 高风险操作实时告警
        if audit_record["risk_score"] > 0.8:
            self._send_security_alert(audit_record)
    
    def _calculate_risk_score(self, action: str, context: dict) -> float:
        """计算操作风险分"""
        score = 0.0
        
        # 敏感操作加权
        sensitive_actions = ["delete", "export", "modify_permission"]
        if action in sensitive_actions:
            score += 0.3
        
        # 异常时间加权
        hour = datetime.now().hour
        if hour < 6 or hour > 22:
            score += 0.2
        
        # 异地登录加权
        if context.get("location") != context.get("usual_location"):
            score += 0.3
        
        return min(score, 1.0)
```

### 3.2 审计报告生成
```python
@app.get("/api/v1/admin/audit-reports")
def generate_audit_report(
    start_date: date,
    end_date: date,
    report_type: str  # summary/detailed/compliance
):
    """生成审计报告"""
    
    if report_type == "compliance":
        # 等保合规报告
        report = {
            "period": f"{start_date} to {end_date}",
            "login_stats": get_login_stats(start_date, end_date),
            "access_violations": get_access_violations(start_date, end_date),
            "data_access_summary": get_data_access_summary(start_date, end_date),
            "privileged_operations": get_privileged_ops(start_date, end_date),
            "compliance_score": calculate_compliance_score(start_date, end_date)
        }
    
    return {"code": 200, "data": report}
```

## 4. 数据安全

### 4.1 数据分类分级
```python
class DataClassification:
    """数据分类分级"""
    
    LEVELS = {
        "public": 1,      # 公开
        "internal": 2,    # 内部
        "confidential": 3, # 秘密
        "secret": 4       # 机密
    }
    
    @classmethod
    def classify(cls, data_type: str) -> str:
        """分类数据"""
        classification_map = {
            "company_name": "public",
            "financial_report": "secret",
            "bank_account": "confidential",
            "password": "secret",
            "customer_list": "confidential",
            "voucher": "internal",
            "user_phone": "confidential"
        }
        return classification_map.get(data_type, "internal")
    
    @classmethod
    def get_protection_measures(cls, level: str) -> dict:
        """获取保护措施"""
        measures = {
            "public": {"encryption": False, "access_log": False},
            "internal": {"encryption": False, "access_log": True},
            "confidential": {"encryption": True, "access_log": True, "masking": True},
            "secret": {"encryption": True, "access_log": True, "masking": True, "integrity_check": True}
        }
        return measures.get(level, measures["internal"])
```

### 4.2 数据脱敏
```python
def desensitize_data(data: Any, user_role: str) -> Any:
    """根据用户角色脱敏数据"""
    
    if user_role == "admin":
        return data  # 管理员不脱敏
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            classification = DataClassification.classify(key)
            
            if classification == "secret" and user_role != "admin":
                result[key] = "***"
            elif classification == "confidential":
                result[key] = apply_masking(value, key)
            else:
                result[key] = value
        return result
    
    return data


def apply_masking(value: str, field_type: str) -> str:
    """应用脱敏规则"""
    
    if field_type == "bank_account" and len(value) > 8:
        return value[:4] + " **** **** " + value[-4:]
    
    if field_type == "phone" and len(value) == 11:
        return value[:3] + " **** " + value[-4:]
    
    if field_type == "id_card" and len(value) == 18:
        return value[:6] + " ******** " + value[-4:]
    
    return value[:2] + "***" + value[-2:] if len(value) > 4 else "****"
```

### 4.3 数据加密
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class DataEncryption:
    """数据加密服务"""
    
    def __init__(self):
        self.master_key = os.getenv("DATA_ENCRYPTION_KEY")
        self.kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=os.urandom(16),
            iterations=100000
        )
    
    def encrypt_field(self, value: str, field_name: str) -> str:
        """加密字段"""
        # 字段级加密
        f = Fernet(self._derive_key(field_name))
        return f.encrypt(value.encode()).decode()
    
    def decrypt_field(self, encrypted: str, field_name: str) -> str:
        """解密字段"""
        f = Fernet(self._derive_key(field_name))
        return f.decrypt(encrypted.encode()).decode()
    
    def _derive_key(self, field_name: str) -> bytes:
        """派生字段密钥"""
        from base64 import urlsafe_b64encode
        key = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=field_name.encode(),
            iterations=100000
        ).derive(self.master_key.encode())
        return urlsafe_b64encode(key)
```

## 5. 安全加固配置

### 5.1 安全响应头
```python
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # 基础安全头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # 防止信息泄露
    response.headers.pop("Server", None)
    response.headers.pop("X-Powered-By", None)
    
    return response
```

### 5.2 会话安全
```python
# Session配置
SESSION_CONFIG = {
    "session_cookie_secure": True,      # 仅HTTPS
    "session_cookie_httponly": True,    # 禁止JS访问
    "session_cookie_samesite": "Strict", # CSRF防护
    "session_timeout": 1800,            # 30分钟无操作过期
    "absolute_timeout": 28800,          # 8小时绝对过期
    "concurrent_session_control": True,  # 同账号同时登录限制
    "max_concurrent_sessions": 3
}
```

================================================================================
                              验收标准
================================================================================

1. [ ] 双因素认证可用
2. [ ] 敏感数据加密存储
3. [ ] 数据脱敏显示正常
4. [ ] 全量审计日志记录
5. [ ] 等保三级要求逐项满足
6. [ ] 通过等保测评初评
7. [ ] 安全响应头配置完整

================================================================================
                              开发提示
================================================================================

1. 等保测评需第三方机构进行
2. 保留所有安全改造文档
3. 定期进行漏洞扫描
4. 建立安全应急响应流程
5. 员工安全意识培训
