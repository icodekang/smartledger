# 任务编号：TASK-CUSTOMER-04
# 任务名称：客户统计分析
# 优先级：P0
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发客户统计分析功能，包括票据统计、费用分析、趋势图表等，帮助了解客户价值和服务情况。

================================================================================
                              需求详情
================================================================================

## 1. 统计指标

### 1.1 票据统计
- 月度票据数量
- 月度票据金额
- 票据类型分布
- 处理状态分布

### 1.2 财务统计
- 月度记账凭证数量
- 月度收支金额
- 应交税费统计
- 成本费用分析

### 1.3 服务统计
- 服务响应时间
- 凭证处理时效
- 审核通过率
- 问题票据比例

## 2. API 接口

### 2.1 客户综合统计
```
GET /api/v1/customers/{id}/statistics

响应:
{
  "code": 200,
  "data": {
    "overview": {
      "total_bills": 150,
      "total_vouchers": 120,
      "total_amount": 500000.00,
      "avg_monthly_bills": 12.5
    },
    "bill_trend": [
      {"month": "2024-01", "count": 10, "amount": 30000},
      {"month": "2024-02", "count": 15, "amount": 45000},
      ...
    ],
    "bill_type_distribution": [
      {"type": "增值税专票", "count": 80, "percentage": 53.3},
      {"type": "增值税普票", "count": 50, "percentage": 33.3},
      {"type": "收据", "count": 20, "percentage": 13.4}
    ],
    "processing_status": {
      "pending": 5,
      "processing": 10,
      "completed": 135
    }
  }
}
```

### 2.2 收入支出分析
```
GET /api/v1/customers/{id}/financial-analysis?period=2024-Q1

响应:
{
  "code": 200,
  "data": {
    "income": {
      "total": 300000.00,
      "by_category": [
        {"category": "主营业务收入", "amount": 280000},
        {"category": "其他业务收入", "amount": 20000}
      ]
    },
    "expense": {
      "total": 200000.00,
      "by_category": [
        {"category": "原材料", "amount": 120000},
        {"category": "人工费", "amount": 50000},
        {"category": "办公费", "amount": 30000}
      ]
    },
    "profit": 100000.00,
    "profit_margin": 33.3
  }
}
```

### 2.3 客户对比分析（管理员）
```
GET /api/v1/customers/comparison?customer_ids=uuid1,uuid2,uuid3

响应:
{
  "code": 200,
  "data": {
    "customers": [
      {
        "id": "uuid1",
        "name": "客户A",
        "total_bills": 150,
        "total_amount": 500000,
        "avg_process_time": 2.5  // 平均处理天数
      },
      {
        "id": "uuid2",
        "name": "客户B",
        "total_bills": 80,
        "total_amount": 300000,
        "avg_process_time": 3.0
      }
    ]
  }
}
```

## 3. 前端页面设计

### 3.1 客户统计仪表盘
```
┌─────────────────────────────────────────────────────────────────┐
│  客户统计分析 - XX科技有限公司                                   │
├─────────────────────────────────────────────────────────────────┤
│  期间: [2024年 ▼] [全年 ▼]                                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │  票据总数   │ │  凭证总数   │ │  交易总额   │ │  月均票据   ││
│  │   150     │ │   120     │ │ ¥500,000 │ │    12.5   ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────┐ ┌─────────────────────────────┐   │
│  │ 票据趋势（折线图）       │ │ 票据类型分布（饼图）         │   │
│  │                         │ │                             │   │
│  │ 数量                    │ │       ████ 专票 53%         │   │
│  │  │╲    ╱│              │ │       ██    普票 33%        │   │
│  │  │ ╲  ╱ │              │ │       █     收据 14%        │   │
│  │  │  ╲╱  │              │ │                             │   │
│  │  └──────────────→ 月份  │ │                             │   │
│  └─────────────────────────┘ └─────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────┐ ┌─────────────────────────────┐   │
│  │ 收入支出对比（柱状图）   │ │ 费用构成（环形图）           │   │
│  └─────────────────────────┘ └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 客户列表增强（增加统计列）
```
客户列表增加:
- 本月票据数
- 本月金额
- 服务到期时间
- 最近操作时间
```

## 4. 统计计算逻辑

```python
def get_customer_statistics(customer_id: str, start_date: date, end_date: date):
    """获取客户统计数据"""
    
    # 票据统计
    bill_stats = db.query(
        func.count(Bill.id).label('total_count'),
        func.sum(Bill.total_amount).label('total_amount'),
        func.avg(Bill.total_amount).label('avg_amount')
    ).filter(
        Bill.customer_id == customer_id,
        Bill.invoice_date.between(start_date, end_date)
    ).first()
    
    # 月度趋势
    monthly_trend = db.query(
        func.to_char(Bill.invoice_date, 'YYYY-MM').label('month'),
        func.count(Bill.id).label('count'),
        func.sum(Bill.total_amount).label('amount')
    ).filter(
        Bill.customer_id == customer_id
    ).group_by('month').order_by('month').all()
    
    # 类型分布
    type_distribution = db.query(
        Bill.bill_type,
        func.count(Bill.id).label('count')
    ).filter(
        Bill.customer_id == customer_id
    ).group_by(Bill.bill_type).all()
    
    return {
        "overview": {
            "total_bills": bill_stats.total_count,
            "total_amount": float(bill_stats.total_amount or 0),
            "avg_amount": float(bill_stats.avg_amount or 0)
        },
        "monthly_trend": [...],
        "type_distribution": [...]
    }
```

================================================================================
                              验收标准
================================================================================

1. [ ] 客户综合统计数据准确
2. [ ] 票据趋势图表正常显示
3. [ ] 票据类型分布图表正常
4. [ ] 收入支出分析准确
5. [ ] 费用构成图表正常
6. [ ] 期间筛选功能正常
7. [ ] 客户对比功能正常
8. [ ] 图表支持导出图片

================================================================================
                              开发提示
================================================================================

1. 统计数据使用异步计算 + 缓存（Redis）
2. 图表使用 ECharts
3. 大数据量时支持按周/月聚合
4. 支持图表联动（点击图表筛选列表）
5. 支持数据导出 CSV/Excel
