# 任务编号：TASK-REPORT-01
# 任务名称：资产负债表
# 优先级：P0
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发资产负债表功能，支持自动生成、数据汇总、期末余额计算等。

================================================================================
                              需求详情
================================================================================

## 1. 资产负债表结构

### 1.1 资产部分
```
流动资产:
  货币资金
    库存现金
    银行存款
    其他货币资金
  应收账款
  预付账款
  其他应收款
  存货
    原材料
    库存商品
  流动资产合计

非流动资产:
  固定资产
    固定资产原值
    减：累计折旧
    固定资产净值
  无形资产
  长期待摊费用
  非流动资产合计

资产总计
```

### 1.2 负债及所有者权益部分
```
流动负债:
  短期借款
  应付账款
  预收账款
  应付职工薪酬
  应交税费
  其他应付款
  流动负债合计

非流动负债:
  长期借款
  非流动负债合计

负债合计

所有者权益:
  实收资本
  资本公积
  盈余公积
  未分配利润
  所有者权益合计

负债及所有者权益总计
```

## 2. 数据模型

### 2.1 资产负债表主表 (balance_sheets)
```python
class BalanceSheet(Base):
    __tablename__ = "balance_sheets"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    accounting_set_id = Column(UUID, ForeignKey("accounting_sets.id"), nullable=False)
    
    period = Column(String(10), nullable=False, comment="会计期间")
    
    # 资产
    current_assets = Column(Numeric(15, 2), default=0, comment="流动资产合计")
    non_current_assets = Column(Numeric(15, 2), default=0, comment="非流动资产合计")
    total_assets = Column(Numeric(15, 2), default=0, comment="资产总计")
    
    # 负债
    current_liabilities = Column(Numeric(15, 2), default=0, comment="流动负债合计")
    non_current_liabilities = Column(Numeric(15, 2), default=0, comment="非流动负债合计")
    total_liabilities = Column(Numeric(15, 2), default=0, comment="负债合计")
    
    # 所有者权益
    total_equity = Column(Numeric(15, 2), default=0, comment="所有者权益合计")
    
    # 校验
    is_balanced = Column(Boolean, default=False, comment="是否平衡")
    difference = Column(Numeric(15, 2), default=0, comment="差额")
    
    # 状态
    status = Column(String(20), default="draft", comment="draft/confirmed")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2.2 资产负债表明细表 (balance_sheet_items)
```python
class BalanceSheetItem(Base):
    __tablename__ = "balance_sheet_items"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    balance_sheet_id = Column(UUID, ForeignKey("balance_sheets.id"), nullable=False)
    
    # 科目信息
    subject_code = Column(String(20), nullable=False)
    subject_name = Column(String(100), nullable=False)
    
    # 分类
    category = Column(String(50), comment="资产/负债/权益")
    sub_category = Column(String(50), comment="流动资产/非流动资产等")
    
    # 金额
    opening_balance = Column(Numeric(15, 2), default=0, comment="期初余额")
    closing_balance = Column(Numeric(15, 2), default=0, comment="期末余额")
    
    sort_order = Column(Integer, default=0)
```

## 3. 生成逻辑

### 3.1 从凭证汇总生成
```python
def generate_balance_sheet(customer_id: str, period: str) -> BalanceSheet:
    """生成资产负债表"""
    
    # 1. 获取该期间的所有凭证
    vouchers = db.query(Voucher).filter(
        Voucher.customer_id == customer_id,
        Voucher.period == period,
        Voucher.status == "approved"  # 只统计已审核凭证
    ).all()
    
    # 2. 汇总各科目余额
    subject_balances = {}
    for voucher in vouchers:
        for item in voucher.items:
            code = item.subject_code
            if code not in subject_balances:
                subject_balances[code] = {
                    "name": item.subject_name,
                    "debit": 0,
                    "credit": 0
                }
            subject_balances[code]["debit"] += item.debit_amount or 0
            subject_balances[code]["credit"] += item.credit_amount or 0
    
    # 3. 计算期末余额（根据科目借贷方向）
    balance_data = {}
    for code, balance in subject_balances.items():
        # 资产类：借方余额
        # 负债类：贷方余额
        # 权益类：贷方余额
        subject_type = get_subject_type(code)
        
        if subject_type == "asset":
            closing = balance["debit"] - balance["credit"]
        else:
            closing = balance["credit"] - balance["debit"]
        
        balance_data[code] = {
            "name": balance["name"],
            "closing": closing
        }
    
    # 4. 填充报表数据
    report = BalanceSheet(
        customer_id=customer_id,
        period=period
    )
    
    # 按科目代码汇总到报表项目
    report.current_assets = sum([
        balance_data.get(code, {}).get("closing", 0)
        for code in CURRENT_ASSET_CODES
    ])
    
    report.non_current_assets = sum([
        balance_data.get(code, {}).get("closing", 0)
        for code in NON_CURRENT_ASSET_CODES
    ])
    
    report.total_assets = report.current_assets + report.non_current_assets
    
    # 负债和权益类似...
    report.current_liabilities = sum([...])
    report.non_current_liabilities = sum([...])
    report.total_liabilities = report.current_liabilities + report.non_current_liabilities
    
    report.total_equity = sum([...])
    
    # 5. 校验平衡
    report.difference = report.total_assets - (report.total_liabilities + report.total_equity)
    report.is_balanced = abs(report.difference) < 0.01
    
    db.add(report)
    db.commit()
    
    return report
```

## 4. API 接口

### 4.1 生成资产负债表
```
POST /api/v1/reports/balance-sheet/generate

请求体:
{
  "customer_id": "uuid",
  "period": "2024-03"
}

响应:
{
  "code": 200,
  "data": {
    "id": "uuid",
    "period": "2024-03",
    "is_balanced": true,
    "difference": 0,
    "summary": {
      "total_assets": 1000000.00,
      "total_liabilities": 400000.00,
      "total_equity": 600000.00
    }
  }
}
```

### 4.2 查询资产负债表
```
GET /api/v1/reports/balance-sheet/{id}

响应:
{
  "code": 200,
  "data": {
    "id": "uuid",
    "period": "2024-03",
    "status": "confirmed",
    "assets": {
      "current": {
        "total": 500000.00,
        "items": [
          {"subject": "货币资金", "amount": 200000.00},
          {"subject": "应收账款", "amount": 150000.00},
          {"subject": "存货", "amount": 150000.00}
        ]
      },
      "non_current": {
        "total": 500000.00,
        "items": [
          {"subject": "固定资产", "amount": 400000.00},
          {"subject": "无形资产", "amount": 100000.00}
        ]
      },
      "total": 1000000.00
    },
    "liabilities": {
      "current": {"total": 300000.00, ...},
      "non_current": {"total": 100000.00, ...},
      "total": 400000.00
    },
    "equity": {
      "total": 600000.00,
      "items": [...]
    }
  }
}
```

### 4.3 导出报表
```
GET /api/v1/reports/balance-sheet/{id}/export?format=pdf

支持格式: pdf, excel
```

## 5. 前端页面设计

### 5.1 资产负债表页面
```
┌─────────────────────────────────────────────────────────────────┐
│  资产负债表 - XX科技有限公司                                     │
├─────────────────────────────────────────────────────────────────┤
│  会计期间: [2024年3月 ▼]  [重新生成] [导出PDF] [导出Excel]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  编制单位: XX科技有限公司        期间: 2024年3月               │
│  单位: 元                                                       │
│                                                                  │
│  ┌─────────────────────────────┬─────────────┬─────────────┐   │
│  │           资  产            │   期初数    │   期末数    │   │
│  ├─────────────────────────────┼─────────────┼─────────────┤   │
│  │ 流动资产:                   │             │             │   │
│  │   货币资金                  │  180,000.00 │  200,000.00 │   │
│  │   应收账款                  │  120,000.00 │  150,000.00 │   │
│  │   存货                      │  130,000.00 │  150,000.00 │   │
│  │   ...                       │             │             │   │
│  │ 流动资产合计                │  430,000.00 │  500,000.00 │   │
│  ├─────────────────────────────┼─────────────┼─────────────┤   │
│  │ 非流动资产:                 │             │             │   │
│  │   固定资产                  │  420,000.00 │  400,000.00 │   │
│  │   ...                       │             │             │   │
│  │ 非流动资产合计              │  520,000.00 │  500,000.00 │   │
│  ├─────────────────────────────┼─────────────┼─────────────┤   │
│  │ 资产总计                    │  950,000.00 │1,000,000.00 │   │
│  └─────────────────────────────┴─────────────┴─────────────┘   │
│                                                                  │
│  ┌─────────────────────────────┬─────────────┬─────────────┐   │
│  │      负债及所有者权益       │   期初数    │   期末数    │   │
│  ├─────────────────────────────┼─────────────┼─────────────┤   │
│  │ 流动负债:                   │             │             │   │
│  │   应付账款                  │  250,000.00 │  280,000.00 │   │
│  │   应交税费                  │   15,000.00 │   20,000.00 │   │
│  │   ...                       │             │             │   │
│  │ 流动负债合计                │  265,000.00 │  300,000.00 │   │
│  ├─────────────────────────────┼─────────────┼─────────────┤   │
│  │ 负债合计                    │  365,000.00 │  400,000.00 │   │
│  ├─────────────────────────────┼─────────────┼─────────────┤   │
│  │ 所有者权益:                 │             │             │   │
│  │   实收资本                  │  500,000.00 │  500,000.00 │   │
│  │   未分配利润                │   85,000.00 │  100,000.00 │   │
│  │ 所有者权益合计              │  585,000.00 │  600,000.00 │   │
│  ├─────────────────────────────┼─────────────┼─────────────┤   │
│  │ 负债及所有者权益总计        │  950,000.00 │1,000,000.00 │   │
│  └─────────────────────────────┴─────────────┴─────────────┘   │
│                                                                  │
│  ✅ 资产 = 负债 + 权益 (已平衡)                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 6. 校验规则

```python
def validate_balance_sheet(sheet: BalanceSheet) -> Tuple[bool, str]:
    """校验资产负债表"""
    
    # 1. 资产 = 负债 + 权益
    total_right = sheet.total_liabilities + sheet.total_equity
    if abs(sheet.total_assets - total_right) > 0.01:
        return False, f"资产({sheet.total_assets}) ≠ 负债+权益({total_right})"
    
    # 2. 资产 = 流动资产 + 非流动资产
    if abs(sheet.total_assets - (sheet.current_assets + sheet.non_current_assets)) > 0.01:
        return False, "资产合计计算错误"
    
    # 3. 负债 = 流动负债 + 非流动负债
    if abs(sheet.total_liabilities - (sheet.current_liabilities + sheet.non_current_liabilities)) > 0.01:
        return False, "负债合计计算错误"
    
    return True, "校验通过"
```

================================================================================
                              验收标准
================================================================================

1. [ ] 资产负债表自动生成
2. [ ] 科目余额计算正确
3. [ ] 资产 = 负债 + 权益 平衡
4. [ ] 期初/期末余额显示正确
5. [ ] 报表导出 PDF/Excel 正常
6. [ ] 报表可确认归档
7. [ ] 历史期间报表可查询

================================================================================
                              开发提示
================================================================================

1. 科目代码需按照会计制度标准（如企业会计准则）
2. 期初余额从上期期末余额继承
3. 首次使用需录入期初余额
4. 报表生成后如凭证有变更需重新生成
5. 确认后的报表不可修改（需反确认）
