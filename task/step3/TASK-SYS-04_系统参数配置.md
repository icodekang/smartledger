# 任务编号：TASK-SYS-04
# 任务名称：系统参数配置
# 优先级：P1
# 预估工期：1.5天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发系统参数配置功能，支持系统设置、邮件配置、数据备份策略等运维管理。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

### 1.1 系统参数表 (system_configs)
```python
class SystemConfig(Base):
    __tablename__ = "system_configs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    config_key = Column(String(100), unique=True, nullable=False, comment="配置键")
    config_value = Column(Text, comment="配置值")
    config_type = Column(String(20), default="string", comment="类型: string/int/bool/json")
    
    category = Column(String(50), comment="分类: general/email/security/backup")
    description = Column(String(200), comment="描述")
    
    is_editable = Column(Boolean, default=True, comment="是否可编辑")
    is_visible = Column(Boolean, default=True, comment="是否可见")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID, ForeignKey("users.id"))
```

## 2. 配置项设计

### 2.1 通用配置 (general)
```python
GENERAL_CONFIGS = [
    {
        "key": "system.name",
        "value": "SmartLedger AI",
        "type": "string",
        "description": "系统名称"
    },
    {
        "key": "system.logo",
        "value": "/logo.png",
        "type": "string",
        "description": "系统Logo"
    },
    {
        "key": "system.login_background",
        "value": "/login-bg.jpg",
        "type": "string",
        "description": "登录页背景"
    },
    {
        "key": "system.default_page_size",
        "value": "20",
        "type": "int",
        "description": "默认分页大小"
    },
    {
        "key": "system.session_timeout",
        "value": "1440",
        "type": "int",
        "description": "会话超时时间(分钟)"
    },
    {
        "key": "system.allow_registration",
        "value": "false",
        "type": "bool",
        "description": "是否允许注册"
    }
]
```

### 2.2 邮件配置 (email)
```python
EMAIL_CONFIGS = [
    {
        "key": "email.smtp_host",
        "value": "smtp.example.com",
        "type": "string",
        "description": "SMTP服务器"
    },
    {
        "key": "email.smtp_port",
        "value": "587",
        "type": "int",
        "description": "SMTP端口"
    },
    {
        "key": "email.smtp_ssl",
        "value": "true",
        "type": "bool",
        "description": "使用SSL"
    },
    {
        "key": "email.username",
        "value": "noreply@example.com",
        "type": "string",
        "description": "发件人邮箱"
    },
    {
        "key": "email.password",
        "value": "encrypted_password",
        "type": "string",
        "description": "邮箱密码(加密存储)"
    },
    {
        "key": "email.sender_name",
        "value": "SmartLedger",
        "type": "string",
        "description": "发件人名称"
    }
]
```

### 2.3 安全配置 (security)
```python
SECURITY_CONFIGS = [
    {
        "key": "security.password_min_length",
        "value": "8",
        "type": "int",
        "description": "密码最小长度"
    },
    {
        "key": "security.password_complexity",
        "value": "true",
        "type": "bool",
        "description": "密码复杂度要求"
    },
    {
        "key": "security.login_max_attempts",
        "value": "5",
        "type": "int",
        "description": "最大登录尝试次数"
    },
    {
        "key": "security.login_lock_duration",
        "value": "30",
        "type": "int",
        "description": "登录锁定时间(分钟)"
    },
    {
        "key": "security.token_expire_hours",
        "value": "24",
        "type": "int",
        "description": "Token过期时间(小时)"
    }
]
```

### 2.4 备份配置 (backup)
```python
BACKUP_CONFIGS = [
    {
        "key": "backup.enabled",
        "value": "true",
        "type": "bool",
        "description": "启用自动备份"
    },
    {
        "key": "backup.schedule",
        "value": "0 2 * * *",
        "type": "string",
        "description": "备份定时(Cron)"
    },
    {
        "key": "backup.retention_days",
        "value": "30",
        "type": "int",
        "description": "备份保留天数"
    },
    {
        "key": "backup.storage_type",
        "value": "local",
        "type": "string",
        "description": "存储类型: local/s3/oss"
    },
    {
        "key": "backup.storage_path",
        "value": "/backups",
        "type": "string",
        "description": "备份存储路径"
    }
]
```

## 3. API 接口

### 3.1 获取配置列表
```
GET /api/v1/admin/configs?category=email

响应:
{
  "code": 200,
  "data": {
    "category": "email",
    "items": [
      {
        "key": "email.smtp_host",
        "value": "smtp.example.com",
        "type": "string",
        "description": "SMTP服务器"
      },
      ...
    ]
  }
}
```

### 3.2 更新配置
```
PUT /api/v1/admin/configs

请求体:
{
  "configs": [
    {"key": "email.smtp_host", "value": "smtp.new.com"},
    {"key": "email.smtp_port", "value": "465"}
  ]
}

说明：批量更新配置
```

### 3.3 测试邮件配置
```
POST /api/v1/admin/configs/test-email

请求体:
{
  "test_email": "test@example.com"
}

响应:
{
  "code": 200,
  "message": "测试邮件已发送，请查收"
}
```

### 3.4 手动备份
```
POST /api/v1/admin/backup/now

响应:
{
  "code": 200,
  "data": {
    "backup_id": "uuid",
    "status": "running",
    "started_at": "2024-03-07T10:00:00"
  }
}
```

### 3.5 获取备份列表
```
GET /api/v1/admin/backups

响应:
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "uuid",
        "filename": "backup_20240307_020000.sql.gz",
        "size": 1024000,
        "status": "completed",
        "created_at": "2024-03-07T02:00:00",
        "expires_at": "2024-04-06T02:00:00"
      }
    ]
  }
}
```

### 3.6 恢复备份
```
POST /api/v1/admin/backups/{id}/restore

警告：恢复操作会覆盖当前数据
```

## 4. 前端页面设计

### 4.1 系统设置页
```
┌─────────────────────────────────────────────────────────────────┐
│  系统设置                                                      │
├─────────────────────────────────────────────────────────────────┤
│  [通用设置] [邮件设置] [安全设置] [备份设置]                    │
├─────────────────────────────────────────────────────────────────┤
│  通用设置:                                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 系统名称: [SmartLedger AI                               ]  ││
│  │ 系统Logo: [选择文件]  [预览]                               ││
│  │ 默认分页: [20 ▼]                                           ││
│  │ 会话超时: [1440 ] 分钟                                     ││
│  │                                                             ││
│  │ ☑ 允许用户注册                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│              [恢复默认]  [保存设置]                             │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 邮件设置页
```
┌─────────────────────────────────────────────────────────────────┐
│  邮件设置                                                      │
├─────────────────────────────────────────────────────────────────┤
│  SMTP服务器: [smtp.example.com                             ]    │
│  SMTP端口:   [587                                          ]    │
│  使用SSL:    ☑                                                │
│  发件人邮箱: [noreply@example.com                          ]    │
│  邮箱密码:   [••••••••                                     ]    │
│  发件人名称: [SmartLedger                                  ]    │
│                                                                  │
│  [发送测试邮件]                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 备份管理页
```
┌─────────────────────────────────────────────────────────────────┐
│  备份管理                                    [立即备份]        │
├─────────────────────────────────────────────────────────────────┤
│  自动备份: ● 开启  定时: 每天 02:00  保留: 30天                 │
├─────────────────────────────────────────────────────────────────┤
│  备份文件列表:                                                  │
│  文件名 | 大小 | 创建时间 | 过期时间 | 状态 | 操作            │
│  backup_20240307... | 100MB | 2024-03-07 | 2024-04-06 | ✓ | [下载][恢复][删除]│
└─────────────────────────────────────────────────────────────────┘
```

## 5. 备份实现

### 5.1 数据库备份
```python
@celery.task
def backup_database():
    """备份数据库"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql.gz"
    filepath = f"/backups/{filename}"
    
    # 执行 pg_dump
    command = f"pg_dump -h {DB_HOST} -U {DB_USER} {DB_NAME} | gzip > {filepath}"
    subprocess.run(command, shell=True, check=True)
    
    # 记录备份信息
    backup = Backup(
        filename=filename,
        size=os.path.getsize(filepath),
        status="completed"
    )
    db.add(backup)
    db.commit()
    
    # 清理旧备份
    cleanup_old_backups()
```

### 5.2 文件备份
```python
def backup_files():
    """备份上传的文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"files_backup_{timestamp}.tar.gz"
    
    # 打包上传目录
    command = f"tar -czf /backups/{filename} -C {UPLOAD_DIR} ."
    subprocess.run(command, shell=True, check=True)
```

================================================================================
                              验收标准
================================================================================

1. [ ] 配置项分类展示正常
2. [ ] 配置项编辑保存正常
3. [ ] 密码等敏感信息加密存储
4. [ ] 邮件配置测试功能正常
5. [ ] 手动备份功能正常
6. [ ] 自动备份定时执行正常
7. [ ] 备份文件列表展示正常
8. [ ] 恢复备份功能正常（谨慎测试）

================================================================================
                              开发提示
================================================================================

1. 配置变更后可能需要重启服务才生效（文档说明）
2. 敏感配置（密码）前端显示为掩码
3. 备份文件存储到独立磁盘或云存储
4. 恢复备份前要求二次确认
5. 定期验证备份文件可恢复性
