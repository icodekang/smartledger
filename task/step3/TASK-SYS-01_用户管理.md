# 任务编号：TASK-SYS-01
# 任务名称：用户管理
# 优先级：P0
# 预估工期：1.5天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发系统用户管理功能，包括用户的增删改查、角色分配、启用禁用等。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

### 1.1 用户表扩展 (users)
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 基本信息
    name = Column(String(50), nullable=False, comment="姓名")
    phone = Column(String(50), comment="手机")
    email = Column(String(100), comment="邮箱")
    avatar = Column(String(500), comment="头像URL")
    
    # 角色
    role = Column(String(20), default="accountant", comment="角色")
    # admin: 管理员
    # accountant: 会计
    # auditor: 审核员
    # viewer: 查看者
    
    # 状态
    status = Column(String(20), default="active", comment="状态")
    # active: 正常
    # inactive: 禁用
    # locked: 锁定
    
    # 登录信息
    last_login_at = Column(DateTime, comment="最后登录时间")
    last_login_ip = Column(String(50), comment="最后登录IP")
    login_fail_count = Column(Integer, default=0, comment="登录失败次数")
    
    # 客户分配（会计角色）
    assigned_customers = relationship("Customer", secondary="user_customers")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID, ForeignKey("users.id"))
```

### 1.2 用户-客户关联表 (user_customers)
```python
class UserCustomer(Base):
    __tablename__ = "user_customers"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 2. API 接口

### 2.1 用户列表
```
GET /api/v1/admin/users?
  keyword=张三&
  role=accountant&
  status=active&
  page=1&page_size=20

响应:
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "uuid",
        "username": "zhangsan",
        "name": "张三",
        "phone": "13800138000",
        "email": "zhangsan@company.com",
        "role": "accountant",
        "status": "active",
        "last_login_at": "2024-03-07T10:00:00",
        "assigned_customer_count": 5,
        "created_at": "2024-01-15T10:00:00"
      }
    ],
    "total": 20,
    "summary": {
      "total_users": 20,
      "active_users": 18,
      "inactive_users": 2,
      "by_role": {
        "admin": 2,
        "accountant": 15,
        "auditor": 3
      }
    }
  }
}
```

### 2.2 创建用户
```
POST /api/v1/admin/users

请求体:
{
  "username": "lisi",
  "name": "李四",
  "phone": "13900139000",
  "email": "lisi@company.com",
  "role": "accountant",
  "initial_password": "TempPass123!",  // 初始密码，首次登录需修改
  "assigned_customer_ids": ["uuid1", "uuid2"]  // 分配的客户（会计角色）
}

响应: 返回创建的用户信息
```

### 2.3 更新用户
```
PUT /api/v1/admin/users/{id}

请求体:
{
  "name": "李四（改）",
  "phone": "13900139001",
  "email": "lisi-new@company.com",
  "role": "auditor",
  "assigned_customer_ids": ["uuid1", "uuid2", "uuid3"]
}
```

### 2.4 重置密码
```
POST /api/v1/admin/users/{id}/reset-password

请求体:
{
  "new_password": "NewPass123!",
  "force_change": true  // 是否强制下次登录修改
}
```

### 2.5 启用/禁用用户
```
POST /api/v1/admin/users/{id}/toggle-status

说明：在 active 和 inactive 之间切换
```

### 2.6 解锁用户
```
POST /api/v1/admin/users/{id}/unlock

说明：当用户因多次登录失败被锁定时，管理员可解锁
```

### 2.7 删除用户
```
DELETE /api/v1/admin/users/{id}

说明：
- 只有无操作记录的用户可删除
- 有数据的用户只能禁用
```

### 2.8 获取用户详情
```
GET /api/v1/admin/users/{id}

响应:
{
  "code": 200,
  "data": {
    "id": "uuid",
    "username": "zhangsan",
    "name": "张三",
    // ... 基本信息
    "assigned_customers": [
      {"id": "uuid", "name": "XX科技", "code": "C2024001"}
    ],
    "statistics": {
      "total_customers": 5,
      "total_bills_processed": 150,
      "total_vouchers_created": 120
    }
  }
}
```

## 3. 前端页面设计

### 3.1 用户列表页（管理员）
```
┌─────────────────────────────────────────────────────────────────┐
│  用户管理                                    [+ 新建用户]        │
├─────────────────────────────────────────────────────────────────┤
│  筛选: [关键词 🔍] [角色 ▼] [状态 ▼] [查询][重置]               │
├─────────────────────────────────────────────────────────────────┤
│  统计: 总用户 20 | 正常 18 | 禁用 2                             │
│        管理员 2 | 会计 15 | 审核员 3                            │
├─────────────────────────────────────────────────────────────────┤
│  表格:                                                           │
│  用户名 | 姓名 | 角色 | 手机 | 状态 | 最后登录 | 操作          │
│  zhangsan | 张三 | 会计 | 138... | ✅正常 | 2小时前 | [编辑]   │
│  lisi     | 李四 | 会计 | 139... | ❌禁用 | -       | [编辑]   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 用户编辑对话框
```
┌─────────────────────────────────────────────────────────────────┐
│  编辑用户                                                      │
├─────────────────────────────────────────────────────────────────┤
│  基本信息:                                                      │
│  用户名: [zhangsan        ] (只读)                             │
│  姓名:   [张三            ]                                     │
│  手机:   [13800138000     ]                                     │
│  邮箱:   [zhangsan@...    ]                                     │
│                                                                  │
│  角色:   [会计 ▼]                                               │
│  状态:   ● 正常  ○ 禁用                                         │
│                                                                  │
│  客户分配: (仅会计角色显示)                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ☑ XX科技有限公司                                           ││
│  │ ☑ YY贸易有限公司                                           ││
│  │ ☐ ZZ电子商行                                               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  [重置密码]  [删除用户]                                         │
│                                                                  │
│              [取消]  [保存]                                     │
└─────────────────────────────────────────────────────────────────┘
```

## 4. 权限控制

```python
# 只有管理员可以访问用户管理接口
@app.get("/api/v1/admin/users")
def list_users(current_user: User = Depends(require_admin)):
    ...

def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "需要管理员权限")
    return user
```

================================================================================
                              验收标准
================================================================================

1. [ ] 用户列表正常展示，支持筛选
2. [ ] 创建用户功能正常（含初始密码）
3. [ ] 更新用户信息功能正常
4. [ ] 角色分配功能正常
5. [ ] 会计角色可分配客户
6. [ ] 重置密码功能正常
7. [ ] 启用/禁用功能正常
8. [ ] 解锁功能正常
9. [ ] 删除权限控制正确
10. [ ] 只有管理员可访问

================================================================================
                              开发提示
================================================================================

1. 初始密码发送邮件通知用户
2. 强制修改密码时首次登录跳转修改页
3. 删除用户前检查操作记录
4. 角色变更时清理相关权限缓存
5. 批量操作支持（批量禁用、批量分配客户）
