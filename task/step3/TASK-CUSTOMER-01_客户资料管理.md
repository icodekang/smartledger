# 任务编号：TASK-CUSTOMER-01
# 任务名称：客户资料管理
# 优先级：P0
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发客户资料管理功能，包括客户基本信息、联系人、地址、开票信息等完整档案管理。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

### 1.1 客户主表 (customers)
```python
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # 基本信息
    code = Column(String(20), unique=True, nullable=False, comment="客户编码")
    name = Column(String(200), nullable=False, comment="客户名称")
    short_name = Column(String(50), comment="客户简称")
    
    # 企业信息
    company_type = Column(String(50), comment="企业类型：有限责任公司/股份有限公司/个体户等")
    industry = Column(String(50), comment="所属行业")
    scale = Column(String(20), comment="企业规模：小型/中型/大型")
    
    # 税务信息
    tax_no = Column(String(20), unique=True, comment="统一社会信用代码/税号")
    tax_type = Column(String(20), default="一般纳税人", comment="纳税人类型")
    
    # 联系信息
    phone = Column(String(50), comment="联系电话")
    email = Column(String(100), comment="联系邮箱")
    fax = Column(String(50), comment="传真")
    website = Column(String(200), comment="公司网站")
    
    # 状态
    status = Column(String(20), default="active", comment="状态：active/inactive")
    
    # 服务信息
    service_start_date = Column(Date, comment="服务开始日期")
    service_end_date = Column(Date, comment="服务结束日期")
    assigned_accountant_id = Column(UUID, ForeignKey("users.id"), comment="负责会计")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID, ForeignKey("users.id"))
```

### 1.2 客户联系人表 (customer_contacts)
```python
class CustomerContact(Base):
    __tablename__ = "customer_contacts"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    name = Column(String(50), nullable=False, comment="联系人姓名")
    title = Column(String(50), comment="职位")
    department = Column(String(50), comment="部门")
    
    phone = Column(String(50), comment="手机")
    tel = Column(String(50), comment="固定电话")
    email = Column(String(100), comment="邮箱")
    wechat = Column(String(50), comment="微信号")
    
    is_primary = Column(Boolean, default=False, comment="是否主要联系人")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    
    remark = Column(String(500), comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 1.3 客户地址表 (customer_addresses)
```python
class CustomerAddress(Base):
    __tablename__ = "customer_addresses"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    address_type = Column(String(20), nullable=False, comment="地址类型：注册地址/办公地址/仓库地址")
    province = Column(String(50), comment="省")
    city = Column(String(50), comment="市")
    district = Column(String(50), comment="区")
    detail = Column(String(200), comment="详细地址")
    postcode = Column(String(10), comment="邮编")
    
    is_primary = Column(Boolean, default=False, comment="是否主要地址")
```

### 1.4 客户开票信息表 (customer_invoice_info)
```python
class CustomerInvoiceInfo(Base):
    __tablename__ = "customer_invoice_info"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    title = Column(String(200), nullable=False, comment="发票抬头")
    tax_no = Column(String(20), nullable=False, comment="税号")
    address = Column(String(200), comment="注册地址")
    phone = Column(String(50), comment="注册电话")
    bank_name = Column(String(100), comment="开户银行")
    bank_account = Column(String(50), comment="银行账号")
    
    is_default = Column(Boolean, default=True, comment="是否默认")
```

## 2. API 接口

### 2.1 客户列表查询
```
GET /api/v1/customers?
  keyword=XX公司&
  status=active&
  industry=科技&
  assigned_accountant_id=uuid&
  page=1&
  page_size=20

响应:
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "uuid",
        "code": "C2024001",
        "name": "XX科技有限公司",
        "short_name": "XX科技",
        "tax_no": "91110108XXXXXXXX",
        "phone": "010-12345678",
        "status": "active",
        "assigned_accountant": {
          "id": "uuid",
          "name": "张三"
        },
        "service_end_date": "2024-12-31",
        "created_at": "2024-01-15T10:00:00"
      }
    ],
    "total": 100,
    "summary": {
      "active_count": 80,
      "inactive_count": 20,
      "expiring_soon": 5  // 即将到期（30天内）
    }
  }
}
```

### 2.2 创建客户
```
POST /api/v1/customers

请求体:
{
  "code": "C2024001",
  "name": "XX科技有限公司",
  "short_name": "XX科技",
  "company_type": "有限责任公司",
  "industry": "软件和信息技术服务业",
  "tax_no": "91110108XXXXXXXX",
  "tax_type": "一般纳税人",
  "phone": "010-12345678",
  "email": "contact@xxtech.com",
  "service_start_date": "2024-01-01",
  "assigned_accountant_id": "uuid",
  "remark": "重要客户"
}

响应: 标准响应，返回创建的客户ID
```

### 2.3 获取客户详情
```
GET /api/v1/customers/{id}

响应:
{
  "code": 200,
  "data": {
    "id": "uuid",
    "code": "C2024001",
    "name": "XX科技有限公司",
    // ... 基本信息
    "contacts": [
      {
        "id": "uuid",
        "name": "李经理",
        "title": "财务经理",
        "phone": "13800138000",
        "is_primary": true
      }
    ],
    "addresses": [
      {
        "id": "uuid",
        "address_type": "注册地址",
        "province": "北京市",
        "city": "北京市",
        "district": "海淀区",
        "detail": "XX路XX号XX大厦",
        "is_primary": true
      }
    ],
    "invoice_infos": [
      {
        "id": "uuid",
        "title": "XX科技有限公司",
        "tax_no": "91110108XXXXXXXX",
        "bank_name": "工商银行北京分行",
        "bank_account": "6222XXXXXXXXXXXX",
        "is_default": true
      }
    ],
    "statistics": {
      "total_bills": 150,
      "total_vouchers": 120,
      "monthly_avg_amount": 50000.00
    }
  }
}
```

### 2.4 更新客户
```
PUT /api/v1/customers/{id}

请求体: 同创建，字段可选
```

### 2.5 删除客户
```
DELETE /api/v1/customers/{id}

说明：仅允许删除无关联数据的客户（无票据、无凭证）
```

### 2.6 联系人管理接口
```
POST   /api/v1/customers/{id}/contacts       # 添加联系人
PUT    /api/v1/customers/contacts/{contact_id}  # 更新联系人
DELETE /api/v1/customers/contacts/{contact_id}  # 删除联系人
```

### 2.7 地址管理接口
```
POST   /api/v1/customers/{id}/addresses
PUT    /api/v1/customers/addresses/{address_id}
DELETE /api/v1/customers/addresses/{address_id}
```

### 2.8 开票信息管理接口
```
POST   /api/v1/customers/{id}/invoice-infos
PUT    /api/v1/customers/invoice-infos/{info_id}
DELETE /api/v1/customers/invoice-infos/{info_id}
```

## 3. 前端页面设计

### 3.1 客户列表页
```
┌─────────────────────────────────────────────────────────────────┐
│  客户管理                                    [+ 新建客户]        │
├─────────────────────────────────────────────────────────────────┤
│  筛选: [关键词 🔍] [状态 ▼] [行业 ▼] [负责会计 ▼] [查询][重置]  │
├─────────────────────────────────────────────────────────────────┤
│  统计: 总客户 100 | 活跃 80 | 停用 20 | 即将到期 5               │
├─────────────────────────────────────────────────────────────────┤
│  表格:                                                           │
│  客户编码 | 客户名称 | 税号 | 联系电话 | 负责会计 | 状态 | 操作 │
│  C2024001 | XX科技   | 9111... | 010-... | 张三 | 活跃 | [查看] │
│  ...                                                             │
├─────────────────────────────────────────────────────────────────┤
│  分页                                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 客户详情/编辑页（标签页形式）
```
┌─────────────────────────────────────────────────────────────────┐
│  XX科技有限公司                              [保存] [取消]       │
├─────────────────────────────────────────────────────────────────┤
│  [基本信息] [联系人] [地址] [开票信息] [服务记录]               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  基本信息页:                                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 客户编码: [C2024001        ]  客户名称: [XX科技有限公司   ] ││
│  │ 客户简称: [XX科技          ]  企业类型: [有限责任公司   ▼] ││
│  │ 所属行业: [科技 ▼]            企业规模: [中型 ▼]           ││
│  │                                                             ││
│  │ 统一社会信用代码: [91110108XXXXXXXX                       ] ││
│  │ 纳税人类型: [一般纳税人 ▼]                                  ││
│  │                                                             ││
│  │ 联系电话: [010-12345678    ]  联系邮箱: [contact@xx.com   ] ││
│  │ 公司网站: [www.xxtech.com  ]  传真:     [010-87654321    ] ││
│  │                                                             ││
│  │ 服务开始日期: [2024-01-01  ]  服务结束日期: [2024-12-31  ] ││
│  │ 负责会计: [张三 ▼]                                          ││
│  │                                                             ││
│  │ 备注:                                                       ││
│  │ [                                                          ]│
│  │ [                                                          ]│
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 联系人标签页
```
┌─────────────────────────────────────────────────────────────────┐
│  联系人列表                              [+ 添加联系人]          │
├─────────────────────────────────────────────────────────────────┤
│  姓名 | 职位 | 部门 | 手机 | 邮箱 | 主要联系人 | 操作           │
│  李经理 | 财务经理 | 财务部 | 138... | li@... | ⭐ | [编辑][删除]│
│  ...                                                             │
└─────────────────────────────────────────────────────────────────┘
```

## 4. 关键业务逻辑

### 4.1 客户编码自动生成
```python
def generate_customer_code() -> str:
    """生成客户编码: C + 年份 + 4位序号"""
    year = datetime.now().strftime("%Y")
    # 查询当年最大序号
    last = db.query(Customer).filter(
        Customer.code.like(f"C{year}%")
    ).order_by(Customer.code.desc()).first()
    
    if last:
        seq = int(last.code[5:]) + 1
    else:
        seq = 1
    
    return f"C{year}{seq:04d}"
```

### 4.2 客户删除限制
```python
def can_delete_customer(customer_id: str) -> Tuple[bool, str]:
    """检查客户是否可以删除"""
    # 检查是否有票据
    bill_count = db.query(Bill).filter(Bill.customer_id == customer_id).count()
    if bill_count > 0:
        return False, f"该客户存在 {bill_count} 张票据，无法删除"
    
    # 检查是否有凭证
    voucher_count = db.query(Voucher).filter(Voucher.customer_id == customer_id).count()
    if voucher_count > 0:
        return False, f"该客户存在 {voucher_count} 张凭证，无法删除"
    
    return True, ""
```

### 4.3 即将到期提醒
```python
def get_expiring_customers(days: int = 30) -> List[Customer]:
    """获取即将到期的客户"""
    deadline = datetime.now() + timedelta(days=days)
    return db.query(Customer).filter(
        Customer.service_end_date <= deadline,
        Customer.service_end_date >= datetime.now(),
        Customer.status == "active"
    ).all()
```

================================================================================
                              验收标准
================================================================================

1. [ ] 客户列表正常展示，支持分页和筛选
2. [ ] 客户编码自动生成，格式正确
3. [ ] 客户增删改查功能完整
4. [ ] 联系人增删改查功能完整
5. [ ] 地址增删改查功能完整
6. [ ] 开票信息增删改查功能完整
7. [ ] 有数据的客户不能删除，提示正确
8. [ ] 客户详情页标签页切换正常
9. [ ] 即将到期客户统计准确
10. [ ] 客户分配会计功能正常

================================================================================
                              开发提示
================================================================================

1. 客户编码生成使用数据库事务防止重复
2. 税号使用统一社会信用代码校验算法
3. 地址信息使用级联选择器（省市区）
4. 联系人至少保留一个主要联系人
5. 考虑客户数据导入导出功能（后续迭代）
