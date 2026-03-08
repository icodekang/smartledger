# 任务编号：TASK-SEC-02
# 任务名称：数据安全加固
# 优先级：P0
# 预估工期：2天
# 负责人：后端

================================================================================
                              任务描述
================================================================================

对系统进行全面数据安全加固，包括数据加密、脱敏、备份、审计等，满足金融级安全要求。

================================================================================
                              需求详情
================================================================================

## 1. 数据加密体系

### 1.1 传输加密
```python
# 强制HTTPS
@app.middleware("http")
async def force_https(request: Request, call_next):
    """强制HTTPS访问"""
    if request.headers.get("X-Forwarded-Proto") != "https" and not settings.DEBUG:
        return RedirectResponse(
            url=f"https://{request.headers['host']}{request.url.path}",
            status_code=301
        )
    return await call_next(request)

# TLS配置
SSL_CONFIG = {
    "min_version": "TLSv1.2",
    "cipher_suites": [
        "ECDHE-RSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES128-GCM-SHA256",
    ],
    "hsts_max_age": 31536000,
    "hsts_include_subdomains": True
}
```

### 1.2 存储加密
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

class FieldEncryption:
    """字段级加密"""
    
    def __init__(self, master_key: bytes):
        self.master_key = master_key
        
    def encrypt(self, plaintext: str, field_name: str) -> str:
        """加密字段值"""
        # 使用字段名作为额外关联数据(AAD)
        key = self._derive_key(field_name)
        aesgcm = AESGCM(key)
        
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(
            nonce,
            plaintext.encode(),
            field_name.encode()  # AAD
        )
        
        # 返回: nonce + ciphertext (base64)
        return base64.b64encode(nonce + ciphertext).decode()
    
    def decrypt(self, ciphertext: str, field_name: str) -> str:
        """解密字段值"""
        data = base64.b64decode(ciphertext.encode())
        nonce = data[:12]
        encrypted = data[12:]
        
        key = self._derive_key(field_name)
        aesgcm = AESGCM(key)
        
        plaintext = aesgcm.decrypt(
            nonce,
            encrypted,
            field_name.encode()
        )
        
        return plaintext.decode()
    
    def _derive_key(self, field_name: str) -> bytes:
        """派生字段密钥"""
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes
        
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=field_name.encode()
        ).derive(self.master_key)


# 应用字段加密
field_encryptor = FieldEncryption(settings.ENCRYPTION_KEY)

class Customer(Base):
    __tablename__ = "customers"
    
    # 加密存储敏感字段
    _bank_account_encrypted = Column("bank_account", Text)
    _phone_encrypted = Column("phone", Text)
    
    @property
    def bank_account(self) -> str:
        return field_encryptor.decrypt(self._bank_account_encrypted, "bank_account")
    
    @bank_account.setter
    def bank_account(self, value: str):
        self._bank_account_encrypted = field_encryptor.encrypt(value, "bank_account")
```

### 1.3 数据库加密
```python
# PostgreSQL透明数据加密(TDE)配置
# 或使用pgcrypto扩展

# 列级加密示例
"""
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 插入加密数据
INSERT INTO customers (tax_no) 
VALUES (pgp_sym_encrypt('91110108MA001234', 'secret-key'));

-- 查询解密数据
SELECT pgp_sym_decrypt(tax_no, 'secret-key') FROM customers;
"""
```

## 2. 数据脱敏

```python
class DataMasking:
    """数据脱敏"""
    
    @staticmethod
    def mask_bank_account(account: str) -> str:
        """银行账号脱敏"""
        if len(account) < 8:
            return "****"
        return account[:4] + " **** **** " + account[-4:]
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """手机号脱敏"""
        if len(phone) != 11:
            return phone
        return phone[:3] + " **** " + phone[-4:]
    
    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """身份证号脱敏"""
        if len(id_card) != 18:
            return id_card
        return id_card[:6] + " ******** " + id_card[-4:]
    
    @staticmethod
    def mask_email(email: str) -> str:
        """邮箱脱敏"""
        if "@" not in email:
            return email
        local, domain = email.split("@")
        masked_local = local[:2] + "***" if len(local) > 2 else "***"
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_company_name(name: str) -> str:
        """企业名称脱敏"""
        if len(name) <= 4:
            return name
        return name[:2] + "**" + name[-2:]


# 自动脱敏中间件
@app.middleware("http")
async def auto_masking(request: Request, call_next):
    response = await call_next(request)
    
    # 检查是否需要脱敏（非管理员）
    user = request.state.user
    if user and user.role != "admin":
        if response.headers.get("content-type") == "application/json":
            body = json.loads(response.body)
            masked_body = apply_masking(body)
            response.body = json.dumps(masked_body).encode()
    
    return response
```

## 3. 数据备份安全

```python
class SecureBackup:
    """安全备份"""
    
    def backup_with_encryption(self, output_path: str):
        """加密备份"""
        
        # 1. 创建临时备份文件
        temp_file = f"/tmp/backup_{uuid.uuid4()}.sql"
        self._create_backup(temp_file)
        
        # 2. 压缩
        compressed = f"{temp_file}.gz"
        self._compress(temp_file, compressed)
        
        # 3. 加密
        encrypted = f"{compressed}.enc"
        self._encrypt_file(compressed, encrypted)
        
        # 4. 计算校验和
        checksum = self._calculate_checksum(encrypted)
        
        # 5. 移动到目标位置
        shutil.move(encrypted, output_path)
        
        # 6. 清理临时文件
        os.remove(temp_file)
        os.remove(compressed)
        
        return {"path": output_path, "checksum": checksum}
    
    def _encrypt_file(self, input_path: str, output_path: str):
        """加密文件"""
        from cryptography.fernet import Fernet
        
        key = settings.BACKUP_ENCRYPTION_KEY
        f = Fernet(key)
        
        with open(input_path, 'rb') as infile:
            data = infile.read()
            encrypted = f.encrypt(data)
        
        with open(output_path, 'wb') as outfile:
            outfile.write(encrypted)
```

## 4. 数据访问审计

```python
class DataAccessAudit:
    """数据访问审计"""
    
    def log_access(
        self,
        user_id: str,
        operation: str,  # SELECT/INSERT/UPDATE/DELETE
        table_name: str,
        record_id: str = None,
        fields_accessed: List[str] = None,
        rows_affected: int = 0
    ):
        """记录数据访问"""
        
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "operation": operation,
            "table": table_name,
            "record_id": record_id,
            "fields": fields_accessed,
            "rows_affected": rows_affected,
            "ip_address": get_client_ip(),
            "session_id": get_session_id(),
            "user_agent": get_user_agent()
        }
        
        # 写入审计日志（独立存储，不可修改）
        self._write_audit_log(audit_record)
        
        # 敏感操作实时告警
        if self._is_sensitive_operation(operation, table_name):
            self._send_alert(audit_record)
    
    def _is_sensitive_operation(self, operation: str, table: str) -> bool:
        """判断是否敏感操作"""
        sensitive_tables = ["bank_accounts", "tax_auths", "user_credentials"]
        sensitive_operations = ["DELETE", "UPDATE"]
        
        return table in sensitive_tables and operation in sensitive_operations
```

## 5. 数据销毁

```python
class SecureDataDeletion:
    """安全数据销毁"""
    
    def secure_delete(self, file_path: str, passes: int = 3):
        """安全删除文件（覆写）"""
        
        if not os.path.exists(file_path):
            return
        
        file_size = os.path.getsize(file_path)
        
        with open(file_path, 'r+b') as f:
            for pass_num in range(passes):
                # 覆写不同模式
                if pass_num == 0:
                    pattern = b'\x00'  # 零
                elif pass_num == 1:
                    pattern = b'\xff'  # 一
                else:
                    pattern = os.urandom(1)  # 随机
                
                f.seek(0)
                f.write(pattern * file_size)
                f.flush()
                os.fsync(f.fileno())
        
        # 重命名后删除
        temp_name = f"/tmp/{uuid.uuid4()}"
        os.rename(file_path, temp_name)
        os.remove(temp_name)
    
    def anonymize_customer_data(self, customer_id: str):
        """客户数据匿名化（注销账户）"""
        
        customer = db.query(Customer).get(customer_id)
        
        # 保留业务统计所需的最少信息
        # 删除或匿名化个人身份信息
        
        customer.name = f"USER_{customer_id[:8]}"
        customer.phone = None
        customer.email = None
        customer.contact_person = None
        
        # 标记为已注销
        customer.status = "deleted"
        customer.deleted_at = datetime.utcnow()
        
        db.commit()
```

================================================================================
                              验收标准
================================================================================

1. [ ] 敏感字段加密存储
2. [ ] 传输全程HTTPS
3. [ ] 数据脱敏展示
4. [ ] 备份文件加密
5. [ ] 访问日志完整
6. [ ] 数据销毁可追溯
7. [ ] 通过安全渗透测试

================================================================================
                              开发提示
================================================================================

1. 密钥管理使用KMS服务
2. 定期轮换加密密钥
3. 审计日志定期归档
4. 数据分类分级管理
5. 建立数据安全应急响应流程
