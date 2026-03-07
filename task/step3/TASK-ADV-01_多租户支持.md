# 任务编号：TASK-ADV-01
# 任务名称：多租户支持
# 优先级：P1
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发多租户支持功能，实现数据隔离、独立配置、资源配额管理，为SaaS化部署做准备。

================================================================================
                              需求详情
================================================================================

## 1. 多租户架构方案

### 方案：独立Schema（推荐）
```
PostgreSQL 数据库
├── public schema (系统表：租户信息、用户等)
├── tenant_001 schema (租户1数据)
│   ├── customers
│   ├── bills
│   ├── vouchers
│   └── ...
├── tenant_002 schema (租户2数据)
└── tenant_003 schema (租户3数据)
```

## 2. 数据模型

### 2.1 租户表 (tenants)
```python
class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, comment="租户编码")
    name = Column(String(100), nullable=False, comment="租户名称")
    
    # 状态
    status = Column(String(20), default="active", comment="active/suspended/expired")
    
    # 数据库配置
    db_schema = Column(String(50), unique=True, comment="数据库schema名")
    
    # 资源配额
    max_customers = Column(Integer, default=10, comment="最大客户数")
    max_users = Column(Integer, default=5, comment="最大用户数")
    max_storage_mb = Column(Integer, default=1024, comment="最大存储(MB)")
    
    # 有效期
    valid_start = Column(Date, default=datetime.utcnow)
    valid_end = Column(Date)
    
    # 联系人
    contact_name = Column(String(50))
    contact_phone = Column(String(50))
    contact_email = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2.2 租户上下文
```python
from contextvars import ContextVar

tenant_ctx: ContextVar[str] = ContextVar('tenant', default=None)

def get_current_tenant() -> str:
    """获取当前租户"""
    return tenant_ctx.get()

def set_current_tenant(tenant_code: str):
    """设置当前租户"""
    tenant_ctx.set(tenant_code)
```

## 3. 数据库路由

```python
class TenantAwareEngine:
    """租户感知的数据库引擎"""
    
    def __init__(self, base_engine):
        self.base_engine = base_engine
    
    def connect(self, **kwargs):
        conn = self.base_engine.connect(**kwargs)
        tenant = get_current_tenant()
        if tenant:
            # 设置 search_path
            conn.execute(f"SET search_path TO {tenant}, public")
        return conn

# SQLAlchemy 事件监听
@event.listens_for(Session, "before_flush")
def set_tenant_schema(session, flush_context, instances):
    """刷新前设置schema"""
    tenant = get_current_tenant()
    if tenant:
        for obj in session.new | session.dirty | session.deleted:
            if hasattr(obj, '__table__'):
                obj.__table__.schema = tenant
```

## 4. 中间件实现

```python
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    """租户识别中间件"""
    
    # 从请求头或子域名获取租户
    tenant_code = request.headers.get("X-Tenant-Code")
    
    if not tenant_code:
        # 从子域名解析
        host = request.headers.get("host", "")
        tenant_code = host.split(".")[0]  # tenant1.smartledger.ai
    
    if tenant_code and tenant_code != "www":
        # 验证租户
        tenant = db.query(Tenant).filter(
            Tenant.code == tenant_code,
            Tenant.status == "active"
        ).first()
        
        if not tenant:
            return JSONResponse(
                status_code=404,
                content={"code": 404, "message": "租户不存在或已停用"}
            )
        
        # 检查有效期
        if tenant.valid_end and tenant.valid_end < datetime.now().date():
            return JSONResponse(
                status_code=403,
                content={"code": 403, "message": "租户已过期"}
            )
        
        # 设置租户上下文
        set_current_tenant(tenant.db_schema)
        request.state.tenant = tenant
    
    response = await call_next(request)
    return response
```

## 5. 资源配额检查

```python
def check_resource_quota(tenant_id: str, resource_type: str) -> bool:
    """检查资源配额"""
    
    tenant = db.query(Tenant).get(tenant_id)
    
    if resource_type == "customer":
        current = db.query(Customer).count()
        return current < tenant.max_customers
    
    elif resource_type == "user":
        current = db.query(User).count()
        return current < tenant.max_users
    
    elif resource_type == "storage":
        # 计算存储使用量
        current_mb = calculate_storage_usage(tenant_id)
        return current_mb < tenant.max_storage_mb
    
    return True

# 装饰器
def require_quota(resource_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tenant_id = get_current_tenant()
            if not check_resource_quota(tenant_id, resource_type):
                raise HTTPException(403, f"{resource_type} 配额已用完")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

## 6. API 接口

### 6.1 租户管理（超级管理员）
```
POST   /api/v1/admin/tenants          # 创建租户
GET    /api/v1/admin/tenants          # 租户列表
PUT    /api/v1/admin/tenants/{id}     # 更新租户
DELETE /api/v1/admin/tenants/{id}     # 删除租户
POST   /api/v1/admin/tenants/{id}/init  # 初始化租户数据库
```

### 6.2 创建租户
```python
@app.post("/api/v1/admin/tenants")
def create_tenant(data: TenantCreate):
    """创建新租户"""
    
    # 1. 创建租户记录
    tenant = Tenant(
        code=data.code,
        name=data.name,
        db_schema=f"tenant_{data.code}",
        max_customers=data.max_customers,
        max_users=data.max_users,
        max_storage_mb=data.max_storage_mb,
        valid_end=data.valid_end
    )
    db.add(tenant)
    db.commit()
    
    # 2. 创建schema
    db.execute(f"CREATE SCHEMA IF NOT EXISTS {tenant.db_schema}")
    
    # 3. 创建表
    create_tenant_tables(tenant.db_schema)
    
    # 4. 初始化数据
    init_tenant_data(tenant.db_schema)
    
    return tenant

def create_tenant_tables(schema: str):
    """为租户创建数据表"""
    # 复制所有业务表结构到新schema
    from sqlalchemy import DDL
    
    for table in [Customer, Bill, Voucher, ...]:
        table.__table__.schema = schema
        table.__table__.create(db.engine, checkfirst=True)

def init_tenant_data(schema: str):
    """初始化租户基础数据"""
    # 创建默认管理员账号
    # 初始化会计科目
    # 初始化系统参数
    pass
```

## 7. 前端适配

### 7.1 租户切换
```vue
<!-- 超级管理员可见 -->
<el-select v-model="currentTenant" @change="switchTenant">
  <el-option 
    v-for="tenant in tenants" 
    :key="tenant.code"
    :label="tenant.name"
    :value="tenant.code"
  />
</el-select>
```

### 7.2 租户信息展示
```vue
<div class="tenant-info">
  <span>{{ tenant.name }}</span>
  <el-tag v-if="tenant.status === 'expired'" type="danger">已过期</el-tag>
  <span>客户: {{ stats.customer_count }}/{{ tenant.max_customers }}</span>
  <el-progress :percentage="storagePercent" />
</div>
```

================================================================================
                              验收标准
================================================================================

1. [ ] 租户数据隔离（schema级别）
2. [ ] 租户识别中间件正常
3. [ ] 资源配额检查生效
4. [ ] 租户CRUD功能完整
5. [ ] 新租户初始化正常
6. [ ] 租户到期控制生效
7. [ ] 超级管理员可切换租户

================================================================================
                              开发提示
================================================================================

1. 租户编码建议使用短代码（如公司缩写）
2. 考虑使用子域名或独立域名访问
3. 备份恢复需按租户隔离
4. 日志需记录租户信息
5. 多租户架构不可逆，谨慎设计
