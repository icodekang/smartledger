# 任务编号：TASK-SYS-02
# 任务名称：角色权限管理
# 优先级：P0
# 预估工期：1.5天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发角色权限管理功能，实现基于 RBAC 的细粒度权限控制，包括菜单权限和数据权限。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

### 1.1 角色表 (roles)
```python
class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, comment="角色编码")
    name = Column(String(50), nullable=False, comment="角色名称")
    description = Column(String(200), comment="描述")
    
    is_system = Column(Boolean, default=False, comment="是否系统内置")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 1.2 权限表 (permissions)
```python
class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    code = Column(String(100), unique=True, nullable=False, comment="权限编码")
    name = Column(String(100), nullable=False, comment="权限名称")
    type = Column(String(20), nullable=False, comment="类型: menu/api/data")
    
    # 菜单权限
    parent_id = Column(UUID, ForeignKey("permissions.id"), comment="父权限ID")
    path = Column(String(200), comment="前端路由路径")
    icon = Column(String(50), comment="图标")
    sort_order = Column(Integer, default=0, comment="排序")
    
    # API权限
    method = Column(String(10), comment="HTTP方法")
    api_path = Column(String(200), comment="API路径")
    
    is_enabled = Column(Boolean, default=True)
```

### 1.3 角色-权限关联表 (role_permissions)
```python
class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(UUID, ForeignKey("permissions.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 2. 权限体系设计

### 2.1 菜单权限
```
仪表盘
  └─ 首页

票据管理
  ├─ 票据列表 (view)
  ├─ 上传票据 (create)
  ├─ 编辑票据 (edit)
  └─ 删除票据 (delete)

凭证管理
  ├─ 凭证列表 (view)
  ├─ 生成凭证 (create)
  ├─ 编辑凭证 (edit)
  └─ 审核凭证 (audit)

银行流水
  ├─ 流水列表 (view)
  ├─ 导入流水 (import)
  └─ 匹配票据 (match)

客户管理
  ├─ 客户列表 (view)
  ├─ 新建客户 (create)
  ├─ 编辑客户 (edit)
  └─ 删除客户 (delete)

系统管理 (仅admin)
  ├─ 用户管理
  ├─ 角色权限
  └─ 系统配置
```

### 2.2 API 权限
```python
PERMISSIONS = [
    # 票据
    {"code": "bill:view", "name": "查看票据", "type": "api"},
    {"code": "bill:create", "name": "创建票据", "type": "api"},
    {"code": "bill:edit", "name": "编辑票据", "type": "api"},
    {"code": "bill:delete", "name": "删除票据", "type": "api"},
    
    # 凭证
    {"code": "voucher:view", "name": "查看凭证", "type": "api"},
    {"code": "voucher:create", "name": "创建凭证", "type": "api"},
    {"code": "voucher:edit", "name": "编辑凭证", "type": "api"},
    {"code": "voucher:audit", "name": "审核凭证", "type": "api"},
    
    # 客户数据权限
    {"code": "data:customer:all", "name": "查看所有客户", "type": "data"},
    {"code": "data:customer:assigned", "name": "查看分配客户", "type": "data"},
    {"code": "data:customer:none", "name": "不可查看客户", "type": "data"},
]
```

### 2.3 数据权限
- **全部数据**：可查看所有客户数据（管理员）
- **分配数据**：只能查看分配给自己的客户（会计）
- **仅自己**：只能查看自己创建的数据
- **无权限**：不可查看

## 3. API 接口

### 3.1 获取权限树
```
GET /api/v1/admin/permissions/tree

响应:
{
  "code": 200,
  "data": [
    {
      "id": "uuid",
      "code": "dashboard",
      "name": "仪表盘",
      "type": "menu",
      "icon": "Dashboard",
      "children": [
        {"id": "uuid", "code": "dashboard:home", "name": "首页", "type": "menu", "path": "/dashboard"}
      ]
    },
    {
      "id": "uuid",
      "code": "bill",
      "name": "票据管理",
      "type": "menu",
      "icon": "Document",
      "children": [
        {"id": "uuid", "code": "bill:list", "name": "票据列表", "type": "menu", "path": "/bills"},
        {"id": "uuid", "code": "bill:create", "name": "上传票据", "type": "api"},
        {"id": "uuid", "code": "bill:edit", "name": "编辑票据", "type": "api"},
        {"id": "uuid", "code": "bill:delete", "name": "删除票据", "type": "api"}
      ]
    }
  ]
}
```

### 3.2 角色列表
```
GET /api/v1/admin/roles

响应:
{
  "code": 200,
  "data": [
    {
      "id": "uuid",
      "code": "admin",
      "name": "管理员",
      "description": "系统管理员，拥有所有权限",
      "is_system": true,
      "user_count": 2,
      "permission_count": 50
    },
    {
      "id": "uuid",
      "code": "accountant",
      "name": "会计",
      "description": "负责客户记账工作",
      "is_system": true,
      "user_count": 15,
      "permission_count": 20
    }
  ]
}
```

### 3.3 创建角色
```
POST /api/v1/admin/roles

请求体:
{
  "code": "senior_accountant",
  "name": "高级会计",
  "description": "可审核凭证的高级会计",
  "permission_ids": ["uuid1", "uuid2", "uuid3"]
}
```

### 3.4 更新角色权限
```
PUT /api/v1/admin/roles/{id}/permissions

请求体:
{
  "permission_ids": ["uuid1", "uuid2", "uuid3", "uuid4"]
}

说明：更新后立即生效，已登录用户下次请求时生效
```

### 3.5 获取当前用户权限
```
GET /api/v1/auth/permissions

响应:
{
  "code": 200,
  "data": {
    "menus": [...],  // 有权限的菜单
    "apis": [...],   // 有权限的API
    "data_scope": "assigned"  // 数据权限范围
  }
}
```

## 4. 权限校验实现

### 4.1 API 权限校验
```python
def require_permission(permission_code: str):
    """API权限校验装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            # 获取用户权限
            user_permissions = await get_user_permissions(current_user.id)
            
            if permission_code not in user_permissions:
                raise HTTPException(403, f"缺少权限: {permission_code}")
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# 使用
@app.post("/api/v1/invoices")
@require_permission("bill:create")
def create_bill(...):
    ...
```

### 4.2 数据权限过滤
```python
def filter_by_data_permission(query, user: User, model):
    """根据数据权限过滤查询"""
    
    # 管理员 - 查看所有
    if user.role == "admin":
        return query
    
    # 会计 - 查看分配的客户
    if user.role == "accountant":
        assigned_customer_ids = [c.id for c in user.assigned_customers]
        return query.filter(model.customer_id.in_(assigned_customer_ids))
    
    # 审核员 - 查看待审核（不限制客户）
    if user.role == "auditor":
        if hasattr(model, 'status'):
            return query.filter(model.status == "pending")
        return query
    
    # 其他 - 无权限
    return query.filter(False)
```

## 5. 前端权限控制

### 5.1 菜单权限
```typescript
// 根据权限动态生成菜单
const menus = computed(() => {
  const allMenus = [...]
  return filterMenusByPermission(allMenus, userPermissions.value)
})
```

### 5.2 按钮权限
```vue
<el-button v-permission="'bill:delete'">删除</el-button>

// 自定义指令
vPermission = {
  mounted(el, binding) {
    if (!hasPermission(binding.value)) {
      el.remove()  // 或 el.disabled = true
    }
  }
}
```

### 5.3 路由权限
```typescript
// router.beforeEach
router.beforeEach((to, from, next) => {
  if (to.meta.permission && !hasPermission(to.meta.permission)) {
    next('/403')
  } else {
    next()
  }
})
```

================================================================================
                              验收标准
================================================================================

1. [ ] 权限树正常展示
2. [ ] 角色增删改查功能完整
3. [ ] 角色权限分配功能正常
4. [ ] 菜单根据权限动态显示
5. [ ] API 权限校验生效
6. [ ] 数据权限过滤正确
7. [ ] 权限变更实时生效（或下次请求生效）
8. [ ] 前端按钮权限控制正常

================================================================================
                              开发提示
================================================================================

1. 系统内置角色不可删除
2. 权限缓存使用 Redis，过期时间 5 分钟
3. 超级管理员拥有所有权限
4. 权限变更后清除相关用户缓存
5. 支持按部门配置数据权限（扩展）
