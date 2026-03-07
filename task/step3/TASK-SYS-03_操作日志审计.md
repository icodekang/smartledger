# 任务编号：TASK-SYS-03
# 任务名称：操作日志审计
# 优先级：P0
# 预估工期：1.5天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发操作日志审计功能，记录用户登录、操作行为、异常事件，支持安全监控和合规审计。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

### 1.1 操作日志表 (operation_logs)
```python
class OperationLog(Base):
    __tablename__ = "operation_logs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # 操作人信息
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), comment="用户名")
    
    # 操作信息
    operation_type = Column(String(50), nullable=False, comment="操作类型")
    # login/logout/create/update/delete/export/login_failed
    
    module = Column(String(50), comment="功能模块")
    # bill/voucher/customer/user/system
    
    resource_type = Column(String(50), comment="资源类型")
    resource_id = Column(String(50), comment="资源ID")
    resource_name = Column(String(200), comment="资源名称")
    
    # 操作详情
    operation_desc = Column(String(500), comment="操作描述")
    request_method = Column(String(10), comment="请求方法")
    request_path = Column(String(500), comment="请求路径")
    request_params = Column(JSON, comment="请求参数")
    response_code = Column(Integer, comment="响应状态码")
    
    # 变更内容（用于数据修改）
    old_values = Column(JSON, comment="修改前值")
    new_values = Column(JSON, comment="修改后值")
    
    # 客户端信息
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="User-Agent")
    browser = Column(String(50), comment="浏览器")
    os = Column(String(50), comment="操作系统")
    
    # 执行时间
    execution_time = Column(Integer, comment="执行时长(ms)")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 索引优化
    __table_args__ = (
        Index('idx_operation_logs_user', 'user_id'),
        Index('idx_operation_logs_type', 'operation_type'),
        Index('idx_operation_logs_module', 'module'),
        Index('idx_operation_logs_created', 'created_at'),
    )
```

### 1.2 登录日志表 (login_logs)
```python
class LoginLog(Base):
    __tablename__ = "login_logs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=False)
    
    login_type = Column(String(20), default="password", comment="登录方式")
    # password/sms/wechat
    
    status = Column(String(20), nullable=False, comment="状态")
    # success/failed
    
    fail_reason = Column(String(200), comment="失败原因")
    
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    location = Column(String(100), comment="登录地点")
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 2. 日志记录实现

### 2.1 自动记录（使用 SQLAlchemy 事件）
```python
@event.listens_for(Bill, 'after_insert')
def log_bill_create(mapper, connection, target):
    """记录票据创建"""
    log = OperationLog(
        user_id=get_current_user_id(),
        username=get_current_username(),
        operation_type="create",
        module="bill",
        resource_type="bill",
        resource_id=str(target.id),
        resource_name=f"发票{target.invoice_no}",
        operation_desc=f"创建票据: {target.seller_name}",
        request_path="/api/v1/invoices",
        request_method="POST",
        response_code=200,
        ip_address=get_client_ip(),
        user_agent=get_user_agent()
    )
    connection.execute(OperationLog.__table__.insert(), log.__dict__)

@event.listens_for(Bill, 'after_update')
def log_bill_update(mapper, connection, target):
    """记录票据修改"""
    # 获取历史值（需要配合 history_meta）
    history = get_history(target, 'amount')
    if history.has_changes():
        log = OperationLog(
            operation_type="update",
            module="bill",
            resource_type="bill",
            resource_id=str(target.id),
            operation_desc="修改票据金额",
            old_values={"amount": history.deleted[0] if history.deleted else None},
            new_values={"amount": history.added[0] if history.added else None}
        )
```

### 2.2 中间件记录 API 调用
```python
@app.middleware("http")
async def operation_log_middleware(request: Request, call_next):
    start_time = time.time()
    
    # 记录请求信息
    log_data = {
        "request_path": request.url.path,
        "request_method": request.method,
        "request_params": dict(request.query_params),
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent")
    }
    
    response = await call_next(request)
    
    # 计算执行时间
    execution_time = int((time.time() - start_time) * 1000)
    log_data["execution_time"] = execution_time
    log_data["response_code"] = response.status_code
    
    # 异步保存日志（不阻塞响应）
    if should_log(request, response):
        asyncio.create_task(save_operation_log(log_data))
    
    return response
```

### 2.3 登录日志记录
```python
@app.post("/api/v1/auth/login")
def login(data: LoginData):
    user = authenticate(data.username, data.password)
    
    if user:
        # 记录成功登录
        record_login_log(user, status="success")
        return {"token": create_token(user)}
    else:
        # 记录失败登录
        record_login_log(username=data.username, status="failed", fail_reason="密码错误")
        raise HTTPException(401, "登录失败")
```

## 3. API 接口

### 3.1 操作日志列表
```
GET /api/v1/admin/operation-logs?
  user_id=uuid&
  operation_type=create&
  module=bill&
  start_date=2024-03-01&
  end_date=2024-03-07&
  page=1&page_size=20

响应:
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "uuid",
        "username": "张三",
        "operation_type": "create",
        "operation_type_name": "创建",
        "module": "bill",
        "module_name": "票据管理",
        "resource_name": "发票12345678",
        "operation_desc": "创建票据: XX科技有限公司",
        "ip_address": "192.168.1.100",
        "execution_time": 150,
        "created_at": "2024-03-07T10:00:00"
      }
    ],
    "total": 1000
  }
}
```

### 3.2 登录日志列表
```
GET /api/v1/admin/login-logs?
  username=zhangsan&
  status=failed&
  page=1

响应:
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "uuid",
        "username": "zhangsan",
        "login_type": "password",
        "status": "failed",
        "fail_reason": "密码错误",
        "ip_address": "192.168.1.100",
        "location": "北京市",
        "created_at": "2024-03-07T09:00:00"
      }
    ]
  }
}
```

### 3.3 安全统计
```
GET /api/v1/admin/security-stats

响应:
{
  "code": 200,
  "data": {
    "login_stats": {
      "today_total": 50,
      "today_success": 48,
      "today_failed": 2,
      "failed_users": ["zhangsan", "lisi"]
    },
    "operation_stats": {
      "today_total": 500,
      "by_module": {
        "bill": 200,
        "voucher": 150,
        "customer": 100
      }
    },
    "abnormal_events": [
      {
        "type": "brute_force",
        "description": "用户 zhangsan 5分钟内登录失败5次",
        "time": "2024-03-07T09:30:00"
      }
    ]
  }
}
```

## 4. 前端页面设计

### 4.1 操作日志列表
```
┌─────────────────────────────────────────────────────────────────┐
│  操作日志                                                      │
├─────────────────────────────────────────────────────────────────┤
│  筛选: [用户 ▼] [操作类型 ▼] [模块 ▼] [日期范围] [查询][重置]   │
├─────────────────────────────────────────────────────────────────┤
│  操作人 | 操作类型 | 模块 | 操作内容 | IP地址 | 时间 | 耗时    │
│  张三   | 创建    | 票据 | 创建票据...| 192... | 10:00 | 150ms │
│  ...                                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 日志详情对话框
```
┌─────────────────────────────────────────────────────────────────┐
│  日志详情                                                      │
├─────────────────────────────────────────────────────────────────┤
│  操作人: 张三                                                   │
│  操作类型: 更新                                                 │
│  功能模块: 票据管理                                             │
│  资源: 发票12345678 (XX科技有限公司)                            │
│  操作描述: 修改票据金额                                         │
│                                                                  │
│  变更内容:                                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 字段    | 修改前      | 修改后                               ││
│  │ 金额    | ¥10,000.00 | ¥12,000.00                          ││
│  │ 销售方  | XX科技      | XX科技有限公司                     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  请求信息:                                                      │
│  IP: 192.168.1.100                                             │
│  浏览器: Chrome 120 / Windows 10                               │
│  执行时长: 150ms                                               │
│  时间: 2024-03-07 10:00:00                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 安全监控仪表盘
```
┌─────────────────────────────────────────────────────────────────┐
│  安全监控                                                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ 今日登录    │ │ 登录成功    │ │ 登录失败    │ │ 异常事件    ││
│  │     50     │ │     48     │ │      2     │ │      0     ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  最近异常事件:                                                  │
│  [暂无异常事件] 或                                             │
│  ⚠️ 用户 zhangsan 登录失败次数过多 (10:00)                     │
└─────────────────────────────────────────────────────────────────┘
```

## 5. 日志清理策略

```python
@celery.task
def cleanup_old_logs():
    """定期清理旧日志"""
    # 操作日志保留 180 天
    cutoff_date = datetime.now() - timedelta(days=180)
    db.query(OperationLog).filter(
        OperationLog.created_at < cutoff_date
    ).delete()
    
    # 登录日志保留 90 天
    cutoff_date = datetime.now() - timedelta(days=90)
    db.query(LoginLog).filter(
        LoginLog.created_at < cutoff_date
    ).delete()
    
    db.commit()
```

================================================================================
                              验收标准
================================================================================

1. [ ] 操作日志自动记录完整
2. [ ] 登录日志记录完整
3. [ ] 数据修改记录变更前后值
4. [ ] 日志列表查询正常
5. [ ] 日志详情展示完整
6. [ ] 安全统计准确
7. [ ] 异常事件检测正常
8. [ ] 日志定期清理正常

================================================================================
                              开发提示
================================================================================

1. 日志记录使用异步方式，不阻塞业务响应
2. 敏感信息（密码）脱敏后记录
3. 大数据量时考虑分表或归档
4. 重要操作（删除）需二次确认并记录
5. 支持日志导出（审计需要）
