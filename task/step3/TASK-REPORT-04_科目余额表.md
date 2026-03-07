# 任务编号：TASK-REPORT-04
# 任务名称：科目余额表
# 优先级：P0
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发科目余额表功能，支持总账、明细账查询，试算平衡校验等。

================================================================================
                              需求详情
================================================================================

## 1. 科目余额表结构

```
科目代码 | 科目名称 | 期初余额借方 | 期初余额贷方 | 本期发生借方 | 本期发生贷方 | 期末余额借方 | 期末余额贷方
--------|----------|-------------|-------------|-------------|-------------|-------------|-------------
1001    | 库存现金 | 10,000.00   |             | 50,000.00   | 45,000.00   | 15,000.00   |
1002    | 银行存款 | 100,000.00  |             | 500,000.00  | 480,000.00  | 120,000.00  |
...     | ...      |             |             |             |             |             |
        | 合计     | 1,000,000.00| 1,000,000.00| 5,000,000.00| 5,000,000.00| 1,200,000.00| 1,200,000.00
```

## 2. 数据模型

```python
class SubjectBalance(Base):
    __tablename__ = "subject_balances"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    period = Column(String(10), nullable=False)
    
    subject_code = Column(String(20), nullable=False)
    subject_name = Column(String(100), nullable=False)
    subject_level = Column(Integer, default=1)  # 科目级次
    parent_code = Column(String(20))  # 上级科目
    
    # 期初余额
    opening_debit = Column(Numeric(15, 2), default=0)
    opening_credit = Column(Numeric(15, 2), default=0)
    
    # 本期发生额
    current_debit = Column(Numeric(15, 2), default=0)
    current_credit = Column(Numeric(15, 2), default=0)
    
    # 期末余额
    closing_debit = Column(Numeric(15, 2), default=0)
    closing_credit = Column(Numeric(15, 2), default=0)
    
    # 方向
    balance_direction = Column(String(10), comment="借/贷")
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 3. 生成逻辑

```python
def generate_subject_balances(customer_id: str, period: str):
    """生成科目余额表"""
    
    # 1. 获取上期期末余额作为本期期初
    last_period = get_last_period(period)
    opening_balances = {}
    
    if last_period:
        last_balances = db.query(SubjectBalance).filter(
            SubjectBalance.customer_id == customer_id,
            SubjectBalance.period == last_period
        ).all()
        
        for b in last_balances:
            opening_balances[b.subject_code] = {
                "debit": b.closing_debit,
                "credit": b.closing_credit
            }
    
    # 2. 汇总本期凭证
    voucher_items = db.query(VoucherItem).join(Voucher).filter(
        Voucher.customer_id == customer_id,
        Voucher.period == period,
        Voucher.status == "approved"
    ).all()
    
    # 按科目汇总
    subject_totals = {}
    for item in voucher_items:
        code = item.subject_code
        if code not in subject_totals:
            subject_totals[code] = {
                "name": item.subject_name,
                "debit": 0,
                "credit": 0
            }
        subject_totals[code]["debit"] += item.debit_amount or 0
        subject_totals[code]["credit"] += item.credit_amount or 0
    
    # 3. 计算余额
    for code, totals in subject_totals.items():
        opening = opening_balances.get(code, {"debit": 0, "credit": 0})
        
        # 根据科目方向计算期末余额
        subject_type = get_subject_type(code)
        
        if subject_type in ["asset", "cost", "expense"]:
            # 借方科目
            closing_debit = opening["debit"] - opening["credit"] + totals["debit"] - totals["credit"]
            closing_credit = 0 if closing_debit >= 0 else abs(closing_debit)
            closing_debit = max(0, closing_debit)
        else:
            # 贷方科目
            closing_credit = opening["credit"] - opening["debit"] + totals["credit"] - totals["debit"]
            closing_debit = 0 if closing_credit >= 0 else abs(closing_credit)
            closing_credit = max(0, closing_credit)
        
        balance = SubjectBalance(
            customer_id=customer_id,
            period=period,
            subject_code=code,
            subject_name=totals["name"],
            opening_debit=opening["debit"],
            opening_credit=opening["credit"],
            current_debit=totals["debit"],
            current_credit=totals["credit"],
            closing_debit=closing_debit,
            closing_credit=closing_credit,
            balance_direction="借" if closing_debit > 0 else "贷"
        )
        
        db.add(balance)
    
    db.commit()

# 试算平衡检查
def check_trial_balance(balances: List[SubjectBalance]) -> Tuple[bool, str]:
    """试算平衡检查"""
    
    total_opening_debit = sum(b.opening_debit for b in balances)
    total_opening_credit = sum(b.opening_credit for b in balances)
    
    total_current_debit = sum(b.current_debit for b in balances)
    total_current_credit = sum(b.current_credit for b in balances)
    
    total_closing_debit = sum(b.closing_debit for b in balances)
    total_closing_credit = sum(b.closing_credit for b in balances)
    
    errors = []
    
    if abs(total_opening_debit - total_opening_credit) > 0.01:
        errors.append(f"期初余额不平衡: 借{total_opening_debit} ≠ 贷{total_opening_credit}")
    
    if abs(total_current_debit - total_current_credit) > 0.01:
        errors.append(f"本期发生额不平衡: 借{total_current_debit} ≠ 贷{total_current_credit}")
    
    if abs(total_closing_debit - total_closing_credit) > 0.01:
        errors.append(f"期末余额不平衡: 借{total_closing_debit} ≠ 贷{total_closing_credit}")
    
    return len(errors) == 0, "; ".join(errors)
```

## 4. 前端页面

```
┌─────────────────────────────────────────────────────────────────┐
│  科目余额表                                                    │
├─────────────────────────────────────────────────────────────────┤
│  会计期间: [2024年3月 ▼]  [科目级次: [全部 ▼]]  [试算平衡]     │
├─────────────────────────────────────────────────────────────────┤
│  ✅ 试算平衡 - 期初/本期/期末均已平衡                          │
├─────────────────────────────────────────────────────────────────┤
│  科目代码 | 科目名称 | 期初借方 | 期初贷方 | 本期借方 | ...   │
│  1001     | 库存现金 | 10,000  |          | 50,000   | ...   │
│  1002     | 银行存款 | 100,000 |          | 500,000  | ...   │
│  1002.01  | ├ 工行   | 60,000  |          | 300,000  | ...   │
│  1002.02  | └ 建行   | 40,000  |          | 200,000  | ...   │
│  ...      | ...      |         |          |          |       │
│  合计     |          |1,000,000|1,000,000 |5,000,000 | ...   │
└─────────────────────────────────────────────────────────────────┘
```

## 5. 明细账查询

```python
@app.get("/api/v1/reports/subject-ledger/{subject_code}")
def get_subject_ledger(
    subject_code: str,
    period: str,
    customer_id: str
):
    """查询科目明细账"""
    
    # 获取该科目的所有凭证分录
    items = db.query(VoucherItem).join(Voucher).filter(
        VoucherItem.subject_code == subject_code,
        Voucher.customer_id == customer_id,
        Voucher.period == period,
        Voucher.status == "approved"
    ).order_by(Voucher.voucher_date, Voucher.voucher_no).all()
    
    # 计算余额
    result = []
    balance = 0
    
    for item in items:
        balance += (item.debit_amount or 0) - (item.credit_amount or 0)
        
        result.append({
            "date": item.voucher.voucher_date,
            "voucher_no": item.voucher.voucher_no,
            "summary": item.summary,
            "debit": item.debit_amount,
            "credit": item.credit_amount,
            "balance": balance
        })
    
    return {"items": result}
```

================================================================================
                              验收标准
================================================================================

1. [ ] 科目余额表自动生成
2. [ ] 期初/本期/期末余额计算正确
3. [ ] 试算平衡校验正确
4. [ ] 科目级次展示正确
5. [ ] 明细账查询正常
6. [ ] 总账查询正常
7. [ ] 支持按科目筛选

================================================================================
                              开发提示
================================================================================

1. 支持多级科目展示（可折叠）
2. 期初余额可从上期继承或手工录入
3. 不平衡时标红提示
4. 支持导出Excel
5. 与三大报表数据勾稽
