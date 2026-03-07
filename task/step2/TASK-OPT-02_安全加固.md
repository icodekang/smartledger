# 任务编号：TASK-OPT-02
# 任务名称：安全加固
# 优先级：P1
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

对系统进行安全加固，修复潜在安全漏洞，提升整体安全防护能力。

================================================================================
                              安全清单
================================================================================

## 1. 认证安全

### 1.1 密码策略
```python
# 密码复杂度校验
import re
from password_strength import PasswordPolicy

policy = PasswordPolicy.from_names(
    length=8,      # 最小长度
    uppercase=1,   # 至少1个大写
    numbers=1,     # 至少1个数字
    special=1,     # 至少1个特殊字符
    nonletters=1   # 至少1个非字母
)

def validate_password(password: str) -> bool:
    """校验密码复杂度"""
    return len(policy.test(password)) == 0

# 密码历史（防止重复使用最近5次密码）
class PasswordHistory(Base):
    __tablename__ = "password_history"
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    password_hash = Column(String(255))  # 存储历史密码哈希
    created_at = Column(DateTime)

def check_password_history(user_id: str, new_password: str) -> bool:
    """检查新密码是否在最近使用过"""
    history = db.query(PasswordHistory).filter(
        PasswordHistory.user_id == user_id
    ).order_by(PasswordHistory.created_at.desc()).limit(5).all()
    
    for old in history:
        if verify_password(new_password, old.password_hash):
            return False
    return True
```

### 1.2 登录安全
```python
# 已有限流: 登录 5次/5分钟
# 新增: 账户锁定
class LoginProtection:
    def __init__(self):
        self.max_failures = 5
        self.lock_duration = 30 * 60  # 30分钟
    
    def record_failure(self, username: str):
        """记录登录失败"""
        key = f"login_fail:{username}"
        failures = redis.incr(key)
        if failures == 1:
            redis.expire(key, self.lock_duration)
        return failures
    
    def is_locked(self, username: str) -> bool:
        """检查账户是否被锁定"""
        failures = redis.get(f"login_fail:{username}")
        return failures and int(failures) >= self.max_failures
    
    def clear_failures(self, username: str):
        """登录成功后清除失败记录"""
        redis.delete(f"login_fail:{username}")
```

### 1.3 Token 安全
```python
# JWT 改进
# 1. 使用 RS256 算法（公私钥）替代 HS256
# 2. Token 绑定设备指纹
# 3.  Refresh Token 轮换

def create_access_token(data: dict, device_fingerprint: str):
    """创建访问令牌"""
    to_encode = data.copy()
    to_encode.update({
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "device": device_fingerprint,  # 绑定设备
        "jti": str(uuid.uuid4())       # 唯一标识，用于吊销
    })
    return jwt.encode(to_encode, private_key, algorithm="RS256")

# Token 吊销列表（用于用户登出）
revoked_tokens = set()

def revoke_token(jti: str):
    revoked_tokens.add(jti)
    redis.setex(f"revoked:{jti}", 3600, "1")

def is_token_revoked(jti: str) -> bool:
    return redis.exists(f"revoked:{jti}")
```

## 2. 接口安全

### 2.1 SQL 注入防护
```python
# 已使用 SQLAlchemy ORM（自动防注入）
# 但需注意 raw SQL 场景

# ❌ 危险
sql = f"SELECT * FROM bills WHERE id = '{user_input}'"
db.execute(sql)

# ✅ 安全
sql = "SELECT * FROM bills WHERE id = :id"
db.execute(text(sql), {"id": user_input})

# ✅ 更安全（使用 ORM）
db.query(Bill).filter(Bill.id == user_input).first()
```

### 2.2 XSS 防护
```python
# 输入过滤
from bleach import clean

def sanitize_input(text: str) -> str:
    """清理用户输入"""
    return clean(text, tags=[], strip=True)

# 输出编码
from html import escape

# 前端 Vue 自动转义，但 API 返回也要注意
```

### 2.3 CSRF 防护
```python
# FastAPI 默认无状态，使用 JWT 已天然防御 CSRF
# 但表单提交场景需额外处理

# 如果使用 cookie-based session
@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    if request.method in ["POST", "PUT", "DELETE"]:
        token = request.headers.get("X-CSRF-Token")
        cookie_token = request.cookies.get("csrf_token")
        if not token or not compare_digest(token, cookie_token):
            raise HTTPException(403, "CSRF token missing or invalid")
    return await call_next(request)
```

## 3. 文件上传安全

### 3.1 文件类型校验
```python
import magic

ALLOWED_TYPES = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'application/pdf': '.pdf'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_upload(file: UploadFile) -> bool:
    """校验上传文件"""
    # 1. 检查文件大小
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {size}")
    
    # 2. 检查文件类型（magic number 检测）
    mime = magic.from_buffer(file.file.read(2048), mime=True)
    file.file.seek(0)
    
    if mime not in ALLOWED_TYPES:
        raise ValueError(f"Invalid file type: {mime}")
    
    # 3. 文件名清理
    safe_filename = secure_filename(file.filename)
    
    return True
```

### 3.2 文件存储安全
```python
# 1. 文件重命名（防止覆盖）
def save_upload_file(file: UploadFile) -> str:
    ext = ALLOWED_TYPES.get(detect_mime(file))
    filename = f"{uuid.uuid4()}{ext}"  # 随机文件名
    path = f"uploads/{datetime.now().strftime('%Y/%m')}/{filename}"
    
    # 2. 上传到对象存储（非本地）
    minio_client.put_object(
        bucket_name="bills",
        object_name=path,
        data=file.file,
        length=-1,
        part_size=10*1024*1024,
        content_type=file.content_type
    )
    return path

# 3. 下载时检查权限
@app.get("/api/v1/files/{file_id}")
def download_file(file_id: str, user: User = Depends(get_current_user)):
    file = get_file_record(file_id)
    # 检查用户是否有权限访问该文件
    if not has_permission(user, file):
        raise HTTPException(403, "Access denied")
    return redirect_to_minio(file.path)
```

## 4. 数据安全

### 4.1 敏感数据加密
```python
from cryptography.fernet import Fernet

# 数据库字段加密（如银行账号）
cipher = Fernet(os.getenv("ENCRYPTION_KEY"))

def encrypt_field(value: str) -> str:
    return cipher.encrypt(value.encode()).decode()

def decrypt_field(encrypted: str) -> str:
    return cipher.decrypt(encrypted.encode()).decode()

# 模型中使用
class BankFlow(Base):
    counterparty_account_encrypted = Column(String(255))
    
    @property
    def counterparty_account(self):
        return decrypt_field(self.counterparty_account_encrypted)
    
    @counterparty_account.setter
    def counterparty_account(self, value):
        self.counterparty_account_encrypted = encrypt_field(value)
```

### 4.2 数据脱敏
```python
def mask_sensitive_data(data: dict, user_role: str) -> dict:
    """根据用户角色脱敏数据"""
    if user_role != "admin":
        # 非管理员看不到完整税号
        if "tax_no" in data:
            data["tax_no"] = data["tax_no"][:6] + "****" + data["tax_no"][-4:]
        
        # 银行账号脱敏
        if "bank_account" in data:
            data["bank_account"] = "****" + data["bank_account"][-4:]
    
    return data
```

## 5. 日志与审计

### 5.1 安全日志
```python
import logging

security_logger = logging.getLogger("security")

# 记录安全事件
def log_security_event(event_type: str, user_id: str, details: dict):
    security_logger.info(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "details": details
    }))

# 使用场景
# 登录失败
log_security_event("login_failed", None, {"username": username, "reason": "invalid_password"})

# 权限提升
log_security_event("permission_change", admin_id, {"target_user": user_id, "new_role": "admin"})

# 敏感操作
log_security_event("data_export", user_id, {"record_count": 1000, "format": "excel"})
```

### 5.2 审计日志
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    action = Column(String(50))      # CREATE/UPDATE/DELETE/LOGIN/EXPORT
    resource_type = Column(String(50))  # bill/voucher/user
    resource_id = Column(String(50))
    old_values = Column(JSON)        # 修改前的值
    new_values = Column(JSON)        # 修改后的值
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

# 自动记录（使用 SQLAlchemy 事件）
@event.listens_for(Bill, 'after_update')
def log_bill_update(mapper, connection, target):
    audit_log = AuditLog(
        user_id=get_current_user_id(),
        action="UPDATE",
        resource_type="bill",
        resource_id=str(target.id),
        new_values={c: getattr(target, c) for c in target.__table__.columns.keys()}
    )
    connection.execute(AuditLog.__table__.insert(), audit_log.__dict__)
```

## 6. 安全配置

### 6.1 安全响应头
```python
# 已在基础框架中添加
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### 6.2 CORS 严格配置
```python
# 生产环境只允许特定域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://smartledger.yourdomain.com"],  # 不允许 *
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)
```

## 7. 安全扫描

### 7.1 依赖安全检查
```bash
# 检查依赖漏洞
pip install safety
safety check

# 或使用 pip-audit
pip install pip-audit
pip-audit
```

### 7.2 代码安全扫描
```bash
# Bandit Python 安全扫描
pip install bandit
bandit -r backend/app -f json -o security-report.json
```

================================================================================
                              验收标准
================================================================================

1. [ ] 密码策略生效（复杂度、历史）
2. [ ] 登录失败 5 次后账户锁定 30 分钟
3. [ ] Token 支持吊销机制
4. [ ] 文件上传限制类型和大小
5. [ ] SQL 注入测试通过
6. [ ] XSS 攻击测试通过
7. [ ] 敏感数据加密存储
8. [ ] 安全日志记录完整
9. [ ] 依赖漏洞扫描无高危
10. [ ] 代码安全扫描无高危

================================================================================
                              开发提示
================================================================================

1. 使用 OWASP ZAP 进行渗透测试
2. 定期更新依赖包修复安全漏洞
3. 生产环境关闭 DEBUG 模式
4. 使用专用密钥管理服务（如 Vault）
5. 建立安全事件响应流程
