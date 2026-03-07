# 任务编号：TASK-CUSTOMER-03
# 任务名称：客户账套管理
# 优先级：P0
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发客户账套管理功能，支持多账期管理、会计期间切换、结账/反结账等操作。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

### 1.1 账套表 (accounting_sets)
```python
class AccountingSet(Base):
    __tablename__ = "accounting_sets"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    # 账套信息
    name = Column(String(100), nullable=False, comment="账套名称")
    fiscal_year = Column(Integer, nullable=False, comment="会计年度")
    
    # 会计期间设置
    start_month = Column(Integer, default=1, comment="起始月份")
    accounting_policy = Column(String(50), default="权责发生制", comment="会计政策")
    
    # 科目体系
    chart_of_accounts_id = Column(UUID, comment="科目表ID")
    
    # 状态
    status = Column(String(20), default="active", comment="active/closed/archived")
    
    # 当前期间
    current_period = Column(String(10), default="2024-01", comment="当前会计期间")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 1.2 会计期间表 (accounting_periods)
```python
class AccountingPeriod(Base):
    __tablename__ = "accounting_periods"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    accounting_set_id = Column(UUID, ForeignKey("accounting_sets.id"), nullable=False)
    
    # 期间信息
    period = Column(String(10), nullable=False, comment="期间：2024-01")
    period_name = Column(String(20), comment="期间名称：2024年1月")
    
    # 日期范围
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # 状态
    status = Column(String(20), default="open", comment="open/closed")
    is_current = Column(Boolean, default=False, comment="是否当前期间")
    
    # 结账信息
    closed_at = Column(DateTime, comment="结账时间")
    closed_by = Column(UUID, ForeignKey("users.id"), comment="结账人")
    
    # 汇兑损益
    exchange_gain_loss = Column(Numeric(15, 2), default=0, comment="汇兑损益")
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 2. API 接口

### 2.1 创建账套
```
POST /api/v1/customers/{customer_id}/accounting-sets

请求体:
{
  "name": "2024年度账套",
  "fiscal_year": 2024,
  "start_month": 1,
  "accounting_policy": "权责发生制",
  "chart_of_accounts_id": "uuid"
}

说明：创建账套时自动生成12个会计期间
```

### 2.2 获取账套列表
```
GET /api/v1/customers/{customer_id}/accounting-sets

响应:
{
  "code": 200,
  "data": [
    {
      "id": "uuid",
      "name": "2024年度账套",
      "fiscal_year": 2024,
      "current_period": "2024-03",
      "status": "active",
      "periods": [
        {"period": "2024-01", "status": "closed", "is_current": false},
        {"period": "2024-02", "status": "closed", "is_current": false},
        {"period": "2024-03", "status": "open", "is_current": true},
        ...
      ]
    }
  ]
}
```

### 2.3 结账操作
```
POST /api/v1/accounting-periods/{period_id}/close

请求体:
{
  "check_balances": true,  // 检查余额
  "generate_vouchers": true  // 自动生成结转凭证
}

响应:
{
  "code": 200,
  "data": {
    "success": true,
    "message": "2024-02期结账成功",
    "generated_vouchers": ["uuid1", "uuid2"]  // 生成的结转凭证
  }
}

错误情况:
{
  "code": 400,
  "message": "结账失败",
  "data": {
    "errors": [
      "存在未审核凭证：PZ202402001",
      "银行余额不平衡：差额 100.00"
    ]
  }
}
```

### 2.4 反结账操作
```
POST /api/v1/accounting-periods/{period_id}/reopen

说明：只允许反结账最近一个已结账期间
```

### 2.5 切换当前期间
```
POST /api/v1/accounting-sets/{set_id}/switch-period

请求体:
{
  "period": "2024-04"
}

说明：切换后所有业务操作默认在新期间
```

### 2.6 期间状态检查
```
GET /api/v1/accounting-periods/{period_id}/check

响应:
{
  "code": 200,
  "data": {
    "can_close": false,
    "checks": [
      {"item": "未审核凭证", "status": "fail", "count": 2, "details": ["PZ001", "PZ002"]},
      {"item": "银行对账", "status": "pass"},
      {"item": "损益结转", "status": "pending"}
    ]
  }
}
```

## 3. 结账检查逻辑

```python
def check_period_can_close(period_id: str) -> Tuple[bool, List[str]]:
    """检查期间是否可以结账"""
    errors = []
    
    # 1. 检查是否有未审核凭证
    unaudited = db.query(Voucher).filter(
        Voucher.period == period.period,
        Voucher.status != "approved"
    ).count()
    if unaudited > 0:
        errors.append(f"存在 {unaudited} 张未审核凭证")
    
    # 2. 检查银行余额是否平衡（可选）
    # 3. 检查往来余额（可选）
    # 4. 检查是否已结转损益
    
    return len(errors) == 0, errors

def close_period(period_id: str, user_id: str):
    """结账操作"""
    # 1. 检查
    can_close, errors = check_period_can_close(period_id)
    if not can_close:
        raise BusinessException(400, "结账检查未通过", {"errors": errors})
    
    # 2. 自动生成结转凭证
    # - 损益结转
    # - 本年利润结转
    vouchers = generate_closing_vouchers(period_id)
    
    # 3. 更新期间状态
    period.status = "closed"
    period.closed_at = datetime.utcnow()
    period.closed_by = user_id
    
    # 4. 更新下一个期间为当前期间
    next_period = get_next_period(period)
    if next_period:
        next_period.is_current = True
        period.is_current = False
    
    db.commit()
```

## 4. 前端页面设计

### 4.1 账套管理页
```
┌─────────────────────────────────────────────────────────────────┐
│  账套管理                                    [+ 新建账套]        │
├─────────────────────────────────────────────────────────────────┤
│  客户: XX科技有限公司                                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 2024年度账套                              [切换账套▼]       ││
│  │ 会计年度: 2024 | 当前期间: 2024年3月 | 状态: 启用中         ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ 会计期间:                                                    ││
│  │ [2024-01 ✅] [2024-02 ✅] [2024-03 📍] [2024-04 ○] ...     ││
│  │ (已结账)   (已结账)    (当前)     (未开启)                  ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ 操作:                                                       ││
│  │ [反结账] [检查] [期末调汇] [结转损益]                        ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 结账检查对话框
```
┌─────────────────────────────────────────────────────────────────┐
│  结账检查 - 2024年2月                                          │
├─────────────────────────────────────────────────────────────────┤
│  ❌ 未审核凭证 (2张)                                           │
│     - PZ202402001 支付办公费                                    │
│     - PZ202402015 采购原材料                                    │
│                                                                  │
│  ✅ 银行对账                                                   │
│     余额核对一致                                               │
│                                                                  │
│  ⏳ 损益结转                                                   │
│     需要生成结转凭证                                           │
│                                                                  │
│              [取消]  [一键修复]  [强制结账]                     │
└─────────────────────────────────────────────────────────────────┘
```

================================================================================
                              验收标准
================================================================================

1. [ ] 账套增删改查功能完整
2. [ ] 创建账套自动生成12个期间
3. [ ] 结账检查逻辑完整
4. [ ] 结账后期间状态正确更新
5. [ ] 反结账功能正常（仅最近期间）
6. [ ] 切换当前期间功能正常
7. [ ] 结账自动生成结转凭证
8. [ ] 期间可视化展示正确

================================================================================
                              开发提示
================================================================================

1. 一个客户可同时存在多个账套（不同年度）
2. 结账后凭证不可修改（除非反结账）
3. 支持跨期查询（查看历史期间数据）
4. 当前期间影响默认查询范围
5. 结账前备份数据（可选）
