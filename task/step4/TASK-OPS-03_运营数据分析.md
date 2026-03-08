# 任务编号：TASK-OPS-03
# 任务名称：运营数据分析
# 优先级：P1
# 预估工期：1.5天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发运营数据分析系统，为平台运营团队提供全面的数据分析能力，支撑业务决策。

================================================================================
                              需求详情
================================================================================

## 1. 数据指标

### 1.1 用户指标
| 指标 | 说明 | 计算方式 |
|------|------|----------|
| DAU/MAU | 日活/月活 | 每日/每月登录用户数 |
| 新增用户 | 新注册 | 每日注册数 |
| 留存率 | 次日/7日/30日留存 | 新增用户后续登录比例 |
| 用户分层 | 高价值/普通/流失风险 | 基于活跃度、付费等 |

### 1.2 业务指标
| 指标 | 说明 |
|------|------|
| 票据处理量 | 每日/月处理票据数 |
| 凭证生成量 | 自动/手动生成凭证数 |
| 审核通过率 | 凭证审核通过比例 |
| 平均处理时长 | 票据到凭证的时间 |

### 1.3 财务指标
| 指标 | 说明 |
|------|------|
| ARR | 年度经常性收入 |
| MRR | 月度经常性收入 |
| 客户生命周期价值 | LTV |
| 获客成本 | CAC |
| 月度流失率 | Churn Rate |

## 2. 数据仓库

```python
# 数据模型设计
class FactUserActivity(Base):
    """用户行为事实表"""
    __tablename__ = "fact_user_activity"
    
    id = Column(BigInteger, primary_key=True)
    date_key = Column(Integer)  # YYYYMMDD
    user_id = Column(UUID)
    customer_id = Column(UUID)
    
    # 度量
    login_count = Column(Integer)
    page_views = Column(Integer)
    api_calls = Column(Integer)
    
    # 维度
    device_type = Column(String(20))
    channel = Column(String(50))


class FactBusinessMetric(Base):
    """业务指标事实表"""
    __tablename__ = "fact_business_metrics"
    
    date_key = Column(Integer, primary_key=True)
    customer_id = Column(UUID, primary_key=True)
    
    bills_uploaded = Column(Integer)
    bills_processed = Column(Integer)
    vouchers_created = Column(Integer)
    vouchers_audited = Column(Integer)
    
    avg_processing_time = Column(Integer)  # 分钟


# ETL任务
@celery.task
def etl_daily_metrics():
    """每日ETL"""
    
    yesterday = datetime.now() - timedelta(days=1)
    date_key = int(yesterday.strftime("%Y%m%d"))
    
    # 1. 抽取数据
    activities = extract_user_activities(yesterday)
    business = extract_business_metrics(yesterday)
    
    # 2. 转换
    transformed_activities = transform_activities(activities)
    transformed_business = transform_business(business)
    
    # 3. 加载到数仓
    load_to_warehouse(transformed_activities)
    load_to_warehouse(transformed_business)
```

## 3. 分析报表

```python
@app.get("/api/v1/ops/analytics/overview")
def get_overview_analytics(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """运营概览"""
    
    return {
        "user_metrics": {
            "dau": calculate_dau(start_date, end_date),
            "mau": calculate_mau(end_date),
            "new_users": count_new_users(start_date, end_date),
            "retention": calculate_retention(end_date)
        },
        "business_metrics": {
            "bills_processed": count_bills(start_date, end_date),
            "vouchers_created": count_vouchers(start_date, end_date),
            "avg_processing_time": calculate_avg_time(start_date, end_date)
        },
        "financial_metrics": {
            "mrr": calculate_mrr(end_date),
            "arr": calculate_mrr(end_date) * 12,
            "churn_rate": calculate_churn_rate(start_date, end_date),
            "ltv": calculate_ltv()
        }
    }


@app.get("/api/v1/ops/analytics/funnel")
def get_funnel_analytics():
    """转化漏斗"""
    
    return {
        "stages": [
            {"name": "注册", "count": 1000, "conversion": 100},
            {"name": "上传票据", "count": 600, "conversion": 60},
            {"name": "生成凭证", "count": 450, "conversion": 75},
            {"name": "付费转化", "count": 150, "conversion": 33}
        ]
    }


@app.get("/api/v1/ops/analytics/cohort")
def get_cohort_analysis():
    """留存分析"""
    
    # 同期群分析
    cohorts = []
    for month in get_last_12_months():
        cohort = {
            "cohort_month": month,
            "new_users": count_new_users_in_month(month),
            "retention": [
                calculate_retention_n(month, n) for n in range(1, 13)
            ]
        }
        cohorts.append(cohort)
    
    return {"cohorts": cohorts}
```

## 4. 可视化大屏

```
┌─────────────────────────────────────────────────────────────────┐
│  SmartLedger 运营数据大屏                    [刷新] [导出]      │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │   日活     │ │   新增     │ │   MRR      │ │   留存     │   │
│  │   1,234   │ │    56     │ │  ¥50,000  │ │   85%     │   │
│  │   ↑ 5%    │ │   ↑ 12%   │ │   ↑ 8%    │ │   ↑ 3%    │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐ ┌─────────────────────────────┐│
│  │    收入增长趋势             │ │    用户增长趋势             ││
│  │    [折线图]                 │ │    [折线图]                 ││
│  └─────────────────────────────┘ └─────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────┐ ┌─────────────────────────────┐│
│  │    转化漏斗                 │ │    用户分布                 ││
│  │    [漏斗图]                 │ │    [饼图]                   ││
│  └─────────────────────────────┘ └─────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 5. 实时监控

```python
class RealtimeMetrics:
    """实时监控指标"""
    
    def __init__(self):
        self.redis = redis_client
    
    def track_event(self, event_type: str, user_id: str = None):
        """追踪实时事件"""
        
        # 按分钟聚合
        minute_key = datetime.now().strftime("%Y%m%d%H%M")
        self.redis.hincrby(f"metrics:{event_type}", minute_key, 1)
        
        # 实时在线用户
        if user_id:
            self.redis.sadd("online_users", user_id)
            self.redis.expire("online_users", 300)  # 5分钟过期
    
    def get_realtime_stats(self) -> dict:
        """获取实时统计"""
        
        current_minute = datetime.now().strftime("%Y%m%d%H%M")
        
        return {
            "online_users": self.redis.scard("online_users"),
            "requests_per_minute": int(
                self.redis.hget("metrics:api_request", current_minute) or 0
            ),
            "bills_uploaded_per_minute": int(
                self.redis.hget("metrics:bill_upload", current_minute) or 0
            )
        }
```

## 6. API接口

```
GET    /api/v1/ops/analytics/overview      # 运营概览
GET    /api/v1/ops/analytics/trends        # 趋势分析
GET    /api/v1/ops/analytics/funnel        # 转化漏斗
GET    /api/v1/ops/analytics/cohort        # 留存分析
GET    /api/v1/ops/analytics/realtime      # 实时数据
GET    /api/v1/ops/analytics/export        # 数据导出
```

================================================================================
                              验收标准
================================================================================

1. [ ] 核心指标计算准确
2. [ ] 报表数据实时更新
3. [ ] 可视化图表展示
4. [ ] 数据可导出
5. [ ] 大屏展示正常
6. [ ] 权限控制正确

================================================================================
                              开发提示
================================================================================

1. 数据量大时使用预计算
2. 敏感数据脱敏展示
3. 支持自定义报表
4. 数据缓存优化性能
5. 数据安全保护
