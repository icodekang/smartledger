# 任务编号：TASK-REPORT-02
# 任务名称：利润表
# 优先级：P0
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发利润表功能，支持收入支出汇总、利润计算、多期对比等。

================================================================================
                              需求详情
================================================================================

## 1. 利润表结构

```
一、营业收入
    主营业务收入
    其他业务收入
    减：销售折扣与折让

二、营业成本
    主营业务成本
    其他业务成本

三、税金及附加

四、期间费用
    销售费用
    管理费用
    财务费用
    研发费用

五、营业利润
    加：其他收益
    加：投资收益
    减：资产减值损失

六、利润总额
    加：营业外收入
    减：营业外支出

七、所得税费用

八、净利润
```

## 2. 数据模型

### 2.1 利润表主表 (income_statements)
```python
class IncomeStatement(Base):
    __tablename__ = "income_statements"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    period = Column(String(10), nullable=False, comment="会计期间")
    
    # 收入
    main_revenue = Column(Numeric(15, 2), default=0, comment="主营业务收入")
    other_revenue = Column(Numeric(15, 2), default=0, comment="其他业务收入")
    total_revenue = Column(Numeric(15, 2), default=0, comment="营业收入合计")
    
    # 成本
    main_cost = Column(Numeric(15, 2), default=0, comment="主营业务成本")
    other_cost = Column(Numeric(15, 2), default=0, comment="其他业务成本")
    total_cost = Column(Numeric(15, 2), default=0, comment="营业成本合计")
    
    # 税金及附加
    taxes_and_surcharges = Column(Numeric(15, 2), default=0)
    
    # 期间费用
    selling_expenses = Column(Numeric(15, 2), default=0, comment="销售费用")
    admin_expenses = Column(Numeric(15, 2), default=0, comment="管理费用")
    financial_expenses = Column(Numeric(15, 2), default=0, comment="财务费用")
    rd_expenses = Column(Numeric(15, 2), default=0, comment="研发费用")
    total_expenses = Column(Numeric(15, 2), default=0, comment="期间费用合计")
    
    # 利润
    operating_profit = Column(Numeric(15, 2), default=0, comment="营业利润")
    other_income = Column(Numeric(15, 2), default=0, comment="其他收益")
    investment_income = Column(Numeric(15, 2), default=0, comment="投资收益")
    
    total_profit = Column(Numeric(15, 2), default=0, comment="利润总额")
    non_operating_income = Column(Numeric(15, 2), default=0, comment="营业外收入")
    non_operating_expenses = Column(Numeric(15, 2), default=0, comment="营业外支出")
    
    income_tax = Column(Numeric(15, 2), default=0, comment="所得税费用")
    net_profit = Column(Numeric(15, 2), default=0, comment="净利润")
    
    # 利润率
    gross_margin_rate = Column(Numeric(5, 2), default=0, comment="毛利率%")
    net_margin_rate = Column(Numeric(5, 2), default=0, comment="净利率%")
    
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 3. 生成逻辑

```python
def generate_income_statement(customer_id: str, period: str) -> IncomeStatement:
    """生成利润表"""
    
    # 1. 获取该期间凭证
    vouchers = db.query(Voucher).filter(
        Voucher.customer_id == customer_id,
        Voucher.period == period,
        Voucher.status == "approved"
    ).all()
    
    # 2. 按科目汇总
    statement = IncomeStatement(
        customer_id=customer_id,
        period=period
    )
    
    for voucher in vouchers:
        for item in voucher.items:
            code = item.subject_code
            
            # 收入类科目（贷方发生额）
            if code.startswith("6001"):  # 主营业务收入
                statement.main_revenue += item.credit_amount or 0
            elif code.startswith("6051"):  # 其他业务收入
                statement.other_revenue += item.credit_amount or 0
            
            # 成本类科目（借方发生额）
            elif code.startswith("6401"):  # 主营业务成本
                statement.main_cost += item.debit_amount or 0
            elif code.startswith("6402"):  # 其他业务成本
                statement.other_cost += item.debit_amount or 0
            
            # 费用类科目
            elif code.startswith("6601"):  # 销售费用
                statement.selling_expenses += item.debit_amount or 0
            elif code.startswith("6602"):  # 管理费用
                statement.admin_expenses += item.debit_amount or 0
            elif code.startswith("6603"):  # 财务费用
                statement.financial_expenses += item.debit_amount or 0
            elif code.startswith("5301"):  # 研发费用
                statement.rd_expenses += item.debit_amount or 0
            
            # 其他
            elif code.startswith("6403"):  # 税金及附加
                statement.taxes_and_surcharges += item.debit_amount or 0
            elif code.startswith("6111"):  # 投资收益
                statement.investment_income += item.credit_amount or 0
            elif code.startswith("6301"):  # 营业外收入
                statement.non_operating_income += item.credit_amount or 0
            elif code.startswith("6711"):  # 营业外支出
                statement.non_operating_expenses += item.debit_amount or 0
            elif code.startswith("6801"):  # 所得税费用
                statement.income_tax += item.debit_amount or 0
    
    # 3. 计算合计
    statement.total_revenue = statement.main_revenue + statement.other_revenue
    statement.total_cost = statement.main_cost + statement.other_cost
    statement.total_expenses = (
        statement.selling_expenses + 
        statement.admin_expenses + 
        statement.financial_expenses + 
        statement.rd_expenses
    )
    
    # 4. 计算利润
    statement.operating_profit = (
        statement.total_revenue - 
        statement.total_cost - 
        statement.taxes_and_surcharges - 
        statement.total_expenses
    )
    
    statement.total_profit = (
        statement.operating_profit + 
        statement.other_income + 
        statement.investment_income +
        statement.non_operating_income - 
        statement.non_operating_expenses
    )
    
    statement.net_profit = statement.total_profit - statement.income_tax
    
    # 5. 计算利润率
    if statement.total_revenue > 0:
        statement.gross_margin_rate = (
            (statement.total_revenue - statement.total_cost) / statement.total_revenue * 100
        )
        statement.net_margin_rate = (statement.net_profit / statement.total_revenue * 100)
    
    db.add(statement)
    db.commit()
    
    return statement
```

## 4. API 接口

### 4.1 生成利润表
```
POST /api/v1/reports/income-statement/generate

请求体:
{
  "customer_id": "uuid",
  "period": "2024-03"
}
```

### 4.2 查询利润表
```
GET /api/v1/reports/income-statement/{id}

响应:
{
  "code": 200,
  "data": {
    "id": "uuid",
    "period": "2024-03",
    "revenue": {
      "main": 800000.00,
      "other": 50000.00,
      "total": 850000.00
    },
    "cost": {
      "main": 500000.00,
      "other": 30000.00,
      "total": 530000.00
    },
    "expenses": {
      "selling": 50000.00,
      "admin": 80000.00,
      "financial": 10000.00,
      "rd": 20000.00,
      "total": 160000.00
    },
    "profits": {
      "operating": 150000.00,
      "total": 155000.00,
      "net": 120000.00
    },
    "margins": {
      "gross": 37.65,
      "net": 14.12
    }
  }
}
```

### 4.3 多期对比
```
GET /api/v1/reports/income-statement/compare?
  customer_id=uuid&
  periods=2024-01,2024-02,2024-03

响应包含各期对比数据
```

## 5. 前端页面设计

```
┌─────────────────────────────────────────────────────────────────┐
│  利润表 - XX科技有限公司                                         │
├─────────────────────────────────────────────────────────────────┤
│  会计期间: [2024年3月 ▼]  [重新生成] [导出] [多期对比]         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────┬─────────────┐     │
│  │               项  目                   │   本期金额  │     │
│  ├─────────────────────────────────────────┼─────────────┤     │
│  │ 一、营业收入                            │   850,000.00│     │
│  │   其中：主营业务收入                    │   800,000.00│     │
│  │         其他业务收入                    │    50,000.00│     │
│  ├─────────────────────────────────────────┼─────────────┤     │
│  │ 减：营业成本                            │   530,000.00│     │
│  │     税金及附加                          │    10,000.00│     │
│  ├─────────────────────────────────────────┼─────────────┤     │
│  │ 减：期间费用                            │   160,000.00│     │
│  │     销售费用                            │    50,000.00│     │
│  │     管理费用                            │    80,000.00│     │
│  │     财务费用                            │    10,000.00│     │
│  │     研发费用                            │    20,000.00│     │
│  ├─────────────────────────────────────────┼─────────────┤     │
│  │ 二、营业利润                            │   150,000.00│     │
│  ├─────────────────────────────────────────┼─────────────┤     │
│  │ 加：营业外收入                          │    10,000.00│     │
│  │ 减：营业外支出                          │     5,000.00│     │
│  ├─────────────────────────────────────────┼─────────────┤     │
│  │ 三、利润总额                            │   155,000.00│     │
│  ├─────────────────────────────────────────┼─────────────┤     │
│  │ 减：所得税费用                          │    35,000.00│     │
│  ├─────────────────────────────────────────┼─────────────┤     │
│  │ 四、净利润                              │   120,000.00│     │
│  └─────────────────────────────────────────┴─────────────┘     │
│                                                                  │
│  财务指标:                                                       │
│  毛利率: 37.65%    净利率: 14.12%                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

================================================================================
                              验收标准
================================================================================

1. [ ] 利润表自动生成
2. [ ] 收入/成本/费用分类正确
3. [ ] 利润计算准确
4. [ ] 毛利率/净利率计算正确
5. [ ] 多期对比功能正常
6. [ ] 报表导出正常
7. [ ] 图表展示收入趋势

================================================================================
                              开发提示
================================================================================

1. 科目代码需符合企业会计准则
2. 注意借贷方向（收入贷方，费用借方）
3. 期间费用需进一步细分可配置
4. 支持同比/环比分析
5. 与资产负债表数据勾稽
