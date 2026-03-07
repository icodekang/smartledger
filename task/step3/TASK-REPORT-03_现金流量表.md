# 任务编号：TASK-REPORT-03
# 任务名称：现金流量表
# 优先级：P0
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发现金流量表功能，支持现金收支分类、净流量计算、间接法编制等。

================================================================================
                              需求详情
================================================================================

## 1. 现金流量表结构

### 1.1 直接法
```
一、经营活动产生的现金流量
    销售商品、提供劳务收到的现金
    收到的税费返还
    收到其他与经营活动有关的现金
    经营活动现金流入小计
    
    购买商品、接受劳务支付的现金
    支付给职工以及为职工支付的现金
    支付的各项税费
    支付其他与经营活动有关的现金
    经营活动现金流出小计
    
    经营活动产生的现金流量净额

二、投资活动产生的现金流量
    （流入/流出项目...）
    投资活动产生的现金流量净额

三、筹资活动产生的现金流量
    （流入/流出项目...）
    筹资活动产生的现金流量净额

四、现金及现金等价物净增加额
五、期初现金及现金等价物余额
六、期末现金及现金等价物余额
```

## 2. 数据模型

```python
class CashFlowStatement(Base):
    __tablename__ = "cash_flow_statements"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    period = Column(String(10), nullable=False)
    
    # 经营活动
    operating_inflow = Column(Numeric(15, 2), default=0, comment="经营活动流入")
    operating_outflow = Column(Numeric(15, 2), default=0, comment="经营活动流出")
    operating_net = Column(Numeric(15, 2), default=0, comment="经营活动净额")
    
    # 投资活动
    investing_inflow = Column(Numeric(15, 2), default=0)
    investing_outflow = Column(Numeric(15, 2), default=0)
    investing_net = Column(Numeric(15, 2), default=0)
    
    # 筹资活动
    financing_inflow = Column(Numeric(15, 2), default=0)
    financing_outflow = Column(Numeric(15, 2), default=0)
    financing_net = Column(Numeric(15, 2), default=0)
    
    # 净增加额
    net_increase = Column(Numeric(15, 2), default=0)
    opening_balance = Column(Numeric(15, 2), default=0, comment="期初余额")
    closing_balance = Column(Numeric(15, 2), default=0, comment="期末余额")
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 3. 生成逻辑

```python
def generate_cash_flow(customer_id: str, period: str):
    """生成现金流量表"""
    
    # 1. 从银行流水汇总
    flows = db.query(BankFlow).filter(
        BankFlow.customer_id == customer_id,
        BankFlow.transaction_date.between(start_date, end_date)
    ).all()
    
    statement = CashFlowStatement(
        customer_id=customer_id,
        period=period
    )
    
    for flow in flows:
        # 根据对方户名和摘要判断现金流量类型
        flow_type = classify_cash_flow(flow)
        
        if flow.amount > 0:  # 收入
            if flow_type == "operating":
                statement.operating_inflow += flow.amount
            elif flow_type == "investing":
                statement.investing_inflow += flow.amount
            elif flow_type == "financing":
                statement.financing_inflow += flow.amount
        else:  # 支出
            amount = abs(flow.amount)
            if flow_type == "operating":
                statement.operating_outflow += amount
            elif flow_type == "investing":
                statement.investing_outflow += amount
            elif flow_type == "financing":
                statement.financing_outflow += amount
    
    # 计算净额
    statement.operating_net = statement.operating_inflow - statement.operating_outflow
    statement.investing_net = statement.investing_inflow - statement.investing_outflow
    statement.financing_net = statement.financing_inflow - statement.financing_outflow
    statement.net_increase = statement.operating_net + statement.investing_net + statement.financing_net
    
    db.add(statement)
    db.commit()
    
    return statement

def classify_cash_flow(flow: BankFlow) -> str:
    """根据流水信息分类现金流量"""
    
    keywords = {
        "operating": ["货款", "销售", "采购", "工资", "税费", "报销", "费用"],
        "investing": ["投资", "固定资产", "购置", "处置", "股权"],
        "financing": ["借款", "还款", "贷款", "分红", "利息", "股本"]
    }
    
    text = f"{flow.summary} {flow.counterparty_name}"
    
    for flow_type, words in keywords.items():
        if any(word in text for word in words):
            return flow_type
    
    # 默认归类为经营活动
    return "operating"
```

## 4. API 接口

```
GET /api/v1/reports/cash-flow/{id}

响应:
{
  "code": 200,
  "data": {
    "period": "2024-03",
    "operating": {
      "inflow": 1000000.00,
      "outflow": 800000.00,
      "net": 200000.00
    },
    "investing": {
      "inflow": 0,
      "outflow": 100000.00,
      "net": -100000.00
    },
    "financing": {
      "inflow": 0,
      "outflow": 50000.00,
      "net": -50000.00
    },
    "summary": {
      "net_increase": 50000.00,
      "opening_balance": 200000.00,
      "closing_balance": 250000.00
    }
  }
}
```

## 5. 前端页面

```
┌─────────────────────────────────────────────────────────────────┐
│  现金流量表                                                    │
├─────────────────────────────────────────────────────────────────┤
│  会计期间: [2024年3月 ▼]                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  一、经营活动产生的现金流量                                     │
│    现金流入:   1,000,000.00                                    │
│    现金流出:   -800,000.00                                     │
│    净额:        200,000.00  [柱状图]                           │
│                                                                  │
│  二、投资活动产生的现金流量                                     │
│    净额:       -100,000.00                                     │
│                                                                  │
│  三、筹资活动产生的现金流量                                     │
│    净额:        -50,000.00                                     │
│                                                                  │
│  ├────────────────────────────────────────┤                    │
│  │ 现金净增加额:          50,000.00       │                    │
│  │ 加：期初余额:         200,000.00       │                    │
│  │ 期末余额:             250,000.00       │                    │
│  └────────────────────────────────────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

================================================================================
                              验收标准
================================================================================

1. [ ] 现金流量表自动生成
2. [ ] 经营/投资/筹资分类正确
3. [ ] 银行流水自动归类
4. [ ] 净增加额计算正确
5. [ ] 期末余额与资产负债表一致
6. [ ] 图表展示流量分布

================================================================================
                              开发提示
================================================================================

1. 支持手动调整分类
2. 提供分类规则配置
3. 与资产负债表现金项目勾稽
4. 支持间接法编制（从净利润调整）
