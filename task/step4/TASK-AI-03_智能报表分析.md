# 任务编号：TASK-AI-03
# 任务名称：智能报表分析
# 优先级：P1
# 预估工期：2天
# 负责人：后端

================================================================================
                              任务描述
================================================================================

开发AI智能报表分析功能，自动生成经营分析、趋势预测、风险提示等智能报告。

================================================================================
                              需求详情
================================================================================

## 1. 智能报告类型

| 报告类型 | 内容 | 频率 |
|----------|------|------|
| 经营月报 | 收入、成本、利润分析 | 每月 |
| 趋势预测 | 未来3个月财务预测 | 每季度 |
| 风险报告 | 异常指标、风险提示 | 实时 |
| 对标分析 | 与行业/历史对比 | 每季度 |
| 税务建议 | 节税建议、税负优化 | 每月 |

## 2. 报告生成引擎

```python
class SmartReportEngine:
    """智能报告引擎"""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate_monthly_report(self, period: str) -> dict:
        """生成经营月报"""
        
        # 1. 获取财务数据
        financial_data = self._get_financial_data(period)
        
        # 2. 计算关键指标
        kpis = self._calculate_kpis(financial_data)
        
        # 3. 对比分析
        comparisons = self._do_comparisons(period)
        
        # 4. 生成AI分析
        ai_analysis = self._generate_ai_analysis(
            financial_data, kpis, comparisons
        )
        
        # 5. 生成报告
        report = {
            "title": f"{period} 经营分析报告",
            "generated_at": datetime.utcnow(),
            "sections": [
                {
                    "type": "summary",
                    "title": "经营概览",
                    "content": self._generate_summary(kpis)
                },
                {
                    "type": "kpis",
                    "title": "关键指标",
                    "data": kpis
                },
                {
                    "type": "trends",
                    "title": "趋势分析",
                    "charts": self._generate_trend_charts(period)
                },
                {
                    "type": "ai_insights",
                    "title": "AI洞察",
                    "content": ai_analysis
                },
                {
                    "type": "recommendations",
                    "title": "经营建议",
                    "items": self._generate_recommendations(financial_data)
                }
            ]
        }
        
        return report
    
    def _generate_ai_analysis(self, data: dict, kpis: dict, comparisons: dict) -> str:
        """生成AI分析文本"""
        
        prompt = f"""
作为一位资深财务分析师，请根据以下数据生成经营分析报告：

【财务数据】
营业收入: {kpis['revenue']}元
营业成本: {kpis['cost']}元
净利润: {kpis['profit']}元
毛利率: {kpis['gross_margin']}%
净利率: {kpis['net_margin']}%

【环比变化】
收入环比: {comparisons['revenue_mom']}%
利润环比: {comparisons['profit_mom']}%

【历史趋势】
近6个月收入趋势: {data['revenue_trend']}

请从以下几个方面进行分析：
1. 经营状况总体评价
2. 收入和成本变动原因分析
3. 盈利能力评估
4. 存在的主要问题
5. 改进建议

要求：专业、客观、有数据支撑，控制在800字以内。
"""
        
        response = self.llm.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一位专业的财务分析师，擅长撰写经营分析报告。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def predict_future(self, months: int = 3) -> dict:
        """预测未来财务趋势"""
        
        # 获取历史数据
        history = self._get_historical_data(months=12)
        
        # 使用时间序列模型预测
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        
        revenue_forecast = []
        for item in history:
            revenue_forecast.append(item['revenue'])
        
        # 简单指数平滑预测
        model = ExponentialSmoothing(revenue_forecast, trend='add')
        fit = model.fit()
        forecast = fit.forecast(months)
        
        # 生成预测分析
        prompt = f"""
基于历史数据，未来{months}个月的收入预测为：
{forecast}

请分析：
1. 预测趋势解读
2. 可能的风险因素
3. 应对建议
"""
        
        analysis = self.llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content
        
        return {
            "forecast_values": forecast.tolist(),
            "analysis": analysis
        }
```

## 3. 对标分析

```python
def industry_benchmark(customer_id: str, metric: str) -> dict:
    """行业对标分析"""
    
    # 获取客户数据
    customer_data = get_customer_metric(customer_id, metric)
    
    # 获取行业平均数据（脱敏聚合）
    industry_avg = get_industry_average(
        industry=customer.industry,
        scale=customer.scale,
        metric=metric
    )
    
    # 计算百分位
    percentile = calculate_percentile(customer_data, industry_avg)
    
    return {
        "metric": metric,
        "customer_value": customer_data,
        "industry_average": industry_avg,
        "industry_median": get_industry_median(...),
        "percentile": percentile,
        "ranking": f"超过{percentile}%的同行企业",
        "assessment": generate_assessment(metric, percentile)
    }
```

## 4. 报告推送

```python
@celery.task
def generate_and_send_monthly_report():
    """生成并发送月度报告"""
    
    # 获取所有活跃客户
    customers = db.query(Customer).filter(Customer.status == "active").all()
    
    last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m")
    
    for customer in customers:
        try:
            engine = SmartReportEngine(customer.id)
            report = engine.generate_monthly_report(last_month)
            
            # 保存报告
            saved_report = SmartReport(
                customer_id=customer.id,
                period=last_month,
                report_type="monthly",
                content=report
            )
            db.add(saved_report)
            db.commit()
            
            # 发送通知
            send_notification(
                user_id=customer.assigned_accountant_id,
                title=f"{customer.name} {last_month} 经营报告已生成",
                content="点击查看AI智能分析",
                link=f"/reports/smart/{saved_report.id}"
            )
            
        except Exception as e:
            logger.error(f"生成报告失败: {customer.id}, {e}")
            continue
```

## 5. API接口

```
GET    /api/v1/smart-reports                    # 智能报告列表
GET    /api/v1/smart-reports/{id}               # 报告详情
POST   /api/v1/smart-reports/generate           # 生成报告
GET    /api/v1/smart-reports/monthly            # 经营月报
GET    /api/v1/smart-reports/forecast           # 趋势预测
GET    /api/v1/smart-reports/benchmark          # 对标分析
GET    /api/v1/smart-reports/export/{id}        # 导出报告
```

## 6. 前端展示

```
┌─────────────────────────────────────────────────────────────────┐
│  AI智能经营分析 - 2024年3月                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📊 关键指标                                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ 收入 ¥100万 │ │ 成本 ¥60万  │ │ 利润 ¥40万  │               │
│  │ ↑ 15%       │ │ ↑ 10%       │ │ ↑ 25%       │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                  │
│  🤖 AI洞察                                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 本月经营状况良好，收入环比增长15%，主要得益于新客户...       ││
│  │ 成本控制在合理范围内，毛利率提升至40%...                     ││
│  │ 建议关注应收账款回收，目前有2笔大额款项逾期...               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  📈 趋势预测                                                    │
│  [折线图展示未来3个月预测]                                      │
│                                                                  │
│  💡 经营建议                                                    │
│  • 优化库存周转，降低资金占用                                  │
│  • 拓展高毛利产品线                                            │
│  • 加强应收账款管理                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

================================================================================
                              验收标准
================================================================================

1. [ ] 月报自动生成
2. [ ] AI分析文本质量高
3. [ ] 趋势预测合理
4. [ ] 对标数据准确
5. [ ] 报告可导出PDF
6. [ ] 报告推送及时

================================================================================
                              开发提示
================================================================================

1. 预测模型需要足够历史数据
2. AI分析结果需人工审核后推送
3. 对标数据需脱敏处理
4. 报告缓存减少生成时间
5. 支持自定义报告模板
