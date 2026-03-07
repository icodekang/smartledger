# 任务编号：TASK-CUSTOMER-02
# 任务名称：客户合同管理
# 优先级：P0
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发客户合同管理功能，包括服务合同创建、收费标准设置、合同到期提醒等。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

### 1.1 合同主表 (customer_contracts)
```python
class CustomerContract(Base):
    __tablename__ = "customer_contracts"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    # 合同信息
    contract_no = Column(String(50), unique=True, nullable=False, comment="合同编号")
    contract_name = Column(String(200), comment="合同名称")
    
    # 合同期限
    start_date = Column(Date, nullable=False, comment="开始日期")
    end_date = Column(Date, nullable=False, comment="结束日期")
    
    # 服务信息
    service_type = Column(String(50), comment="服务类型：代理记账/税务咨询/财务顾问")
    service_content = Column(Text, comment="服务内容描述")
    
    # 收费信息
    billing_cycle = Column(String(20), default="monthly", comment="计费周期：monthly/quarterly/yearly")
    billing_amount = Column(Numeric(15, 2), nullable=False, comment="计费金额")
    currency = Column(String(10), default="CNY", comment="币种")
    
    # 付款信息
    payment_terms = Column(String(50), comment="付款条件：预付/月付/季付")
    payment_day = Column(Integer, default=5, comment="每月付款日")
    
    # 合同状态
    status = Column(String(20), default="active", comment="状态：draft/active/expired/terminated")
    
    # 附件
    attachment_url = Column(String(500), comment="合同附件URL")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID, ForeignKey("users.id"))
```

### 1.2 收费记录表 (contract_payments)
```python
class ContractPayment(Base):
    __tablename__ = "contract_payments"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID, ForeignKey("customer_contracts.id"), nullable=False)
    
    # 账期
    period = Column(String(10), nullable=False, comment="账期：2024-01")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # 金额
    amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    
    # 状态
    status = Column(String(20), default="pending", comment="pending/paid/overdue/waived")
    
    # 付款信息
    paid_at = Column(DateTime, comment="付款时间")
    paid_by = Column(String(50), comment="付款人")
    payment_method = Column(String(50), comment="付款方式")
    transaction_no = Column(String(100), comment="交易流水号")
    
    # 发票信息
    invoice_no = Column(String(50), comment="发票号码")
    invoiced_at = Column(DateTime, comment="开票时间")
    
    remark = Column(String(500), comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 2. API 接口

### 2.1 合同列表
```
GET /api/v1/customers/{customer_id}/contracts

响应:
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "uuid",
        "contract_no": "HT2024001",
        "contract_name": "2024年度代理记账服务合同",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "service_type": "代理记账",
        "billing_amount": 500.00,
        "billing_cycle": "monthly",
        "status": "active",
        "days_to_expire": 180
      }
    ]
  }
}
```

### 2.2 创建合同
```
POST /api/v1/customers/{customer_id}/contracts

请求体:
{
  "contract_name": "2024年度代理记账服务合同",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "service_type": "代理记账",
  "service_content": "提供月度记账、纳税申报、财务报表等服务",
  "billing_cycle": "monthly",
  "billing_amount": 500.00,
  "payment_terms": "月付",
  "payment_day": 5,
  "remark": ""
}

说明：创建合同时自动生成合同编号，并生成本账期的收费记录
```

### 2.3 收费记录列表
```
GET /api/v1/contracts/{contract_id}/payments

响应:
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "uuid",
        "period": "2024-03",
        "period_start": "2024-03-01",
        "period_end": "2024-03-31",
        "amount": 500.00,
        "paid_amount": 500.00,
        "status": "paid",
        "paid_at": "2024-03-05T10:00:00",
        "invoice_no": "INV202403001"
      }
    ],
    "summary": {
      "total_amount": 6000.00,
      "paid_amount": 1500.00,
      "pending_amount": 3000.00,
      "overdue_amount": 1500.00
    }
  }
}
```

### 2.4 记录付款
```
POST /api/v1/contract-payments/{payment_id}/pay

请求体:
{
  "paid_amount": 500.00,
  "paid_by": "李经理",
  "payment_method": "银行转账",
  "transaction_no": "2024030512345678",
  "remark": "3月服务费"
}
```

### 2.5 记录开票
```
POST /api/v1/contract-payments/{payment_id}/invoice

请求体:
{
  "invoice_no": "INV202403001",
  "invoiced_at": "2024-03-05"
}
```

## 3. 前端页面设计

### 3.1 合同列表
```
┌─────────────────────────────────────────────────────────────────┐
│  服务合同                                    [+ 新建合同]        │
├─────────────────────────────────────────────────────────────────┤
│  客户: XX科技有限公司                                            │
├─────────────────────────────────────────────────────────────────┤
│  合同编号 | 合同名称 | 服务期限 | 服务费 | 状态 | 操作         │
│  HT2024001 | 2024年度... | 2024-01~12 | ¥500/月 | 生效中 | ... │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 合同详情页
```
┌─────────────────────────────────────────────────────────────────┐
│  合同详情                                                      │
├─────────────────────────────────────────────────────────────────┤
│  [基本信息] [收费记录]                                          │
├─────────────────────────────────────────────────────────────────┤
│  基本信息:                                                      │
│  合同编号: HT2024001                                            │
│  合同名称: 2024年度代理记账服务合同                              │
│  服务期限: 2024-01-01 至 2024-12-31 (剩余 180 天)               │
│  服务类型: 代理记账                                             │
│  计费方式: 月付 ¥500.00                                         │
│  付款日: 每月 5 日                                              │
│  合同附件: [查看合同.pdf]                                        │
│                                                                  │
│  收费记录:                                                      │
│  账期 | 金额 | 状态 | 付款时间 | 发票 | 操作                    │
│  2024-03 | ¥500 | 已付款 | 2024-03-05 | INV001 | [标记开票]    │
│  2024-04 | ¥500 | 待付款 | - | - | [记录付款]                  │
└─────────────────────────────────────────────────────────────────┘
```

## 4. 定时任务

### 4.1 自动生成收费记录
```python
@celery.task
def generate_monthly_payments():
    """每月1号生成本月收费记录"""
    today = datetime.now()
    
    # 查找生效中的合同
    contracts = db.query(CustomerContract).filter(
        CustomerContract.status == "active",
        CustomerContract.start_date <= today,
        CustomerContract.end_date >= today
    ).all()
    
    for contract in contracts:
        # 检查是否已存在本月记录
        exists = db.query(ContractPayment).filter(
            ContractPayment.contract_id == contract.id,
            ContractPayment.period == today.strftime("%Y-%m")
        ).first()
        
        if not exists:
            # 生成收费记录
            payment = ContractPayment(
                contract_id=contract.id,
                period=today.strftime("%Y-%m"),
                period_start=today.replace(day=1),
                period_end=(today.replace(day=1) + relativedelta(months=1, days=-1)),
                amount=contract.billing_amount,
                status="pending"
            )
            db.add(payment)
    
    db.commit()
```

### 4.2 到期提醒
```python
@celery.task
def check_contract_expiry():
    """检查即将到期的合同"""
    # 30天内到期
    expiring = db.query(CustomerContract).filter(
        CustomerContract.end_date <= datetime.now() + timedelta(days=30),
        CustomerContract.end_date >= datetime.now(),
        CustomerContract.status == "active"
    ).all()
    
    for contract in expiring:
        # 发送提醒通知
        send_notification(
            user_id=contract.customer.assigned_accountant_id,
            title="合同即将到期",
            content=f"客户 {contract.customer.name} 的合同将在 {contract.end_date} 到期"
        )
```

================================================================================
                              验收标准
================================================================================

1. [ ] 合同增删改查功能完整
2. [ ] 合同编号自动生成
3. [ ] 收费记录按月自动生成
4. [ ] 付款记录功能正常
5. [ ] 开票记录功能正常
6. [ ] 合同到期提醒正常
7. [ ] 收费统计（应收/已收/逾期）准确
8. [ ] 合同附件上传/下载正常

================================================================================
                              开发提示
================================================================================

1. 合同编号格式：HT + 年份 + 4位序号
2. 收费记录提前生成（每月1号）
3. 支持多合同（一个客户可有多个合同）
4. 合同到期后可续签（复制创建新合同）
5. 逾期费用计算（可选功能）
