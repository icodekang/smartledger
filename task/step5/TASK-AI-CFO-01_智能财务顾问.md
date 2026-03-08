# 任务编号：TASK-AI-CFO-01
# 任务名称：智能财务顾问
# 优先级：P0
# 预估工期：15天
# 负责人：后端/AI工程师/财务专家

================================================================================
                              任务描述
================================================================================

开发AI财务顾问系统（CFO Agent），实现从"工具型AI"到"顾问型AI"的跨越。系统能够主动监控企业财务状况，发现问题，提供专业的经营优化建议，扮演企业"虚拟CFO"的角色。

================================================================================
                              需求详情
================================================================================

## 1. 核心能力

### 1.1 财务健康诊断
- 多维度财务健康评分（偿债、盈利、营运、成长）
- 行业对标分析（与同行业企业对比）
- 历史趋势分析（财务指标变化趋势）
- 风险雷达图（可视化展示各项风险）

### 1.2 主动建议系统
- 异常检测与预警（费用异常、收入波动、现金流风险）
- 优化机会发现（税收优惠、成本节约、效率提升）
- 定期健康报告（周报/月报自动生成推送）
- 紧急事项提醒（临期事项、异常情况）

### 1.3 现金流管理
- 现金流预测（未来4-13周精确预测）
- 资金缺口预警（提前识别现金流风险）
- 资金使用建议（优化资金配置）
- 融资时机建议（基于现金需求预测）

### 1.4 经营优化建议
- 成本结构分析（识别优化空间）
- 定价策略建议（基于成本和市场）
- 客户价值分析（识别高价值客户）
- 产品盈利分析（优化产品组合）

## 2. 数据模型

```python
class FinancialHealthScore(Base):
    """财务健康评分"""
    __tablename__ = "ai_financial_health_scores"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    # 综合评分
    overall_score = Column(Numeric(5, 2))  # 0-100
    grade = Column(String(10))  # A/B/C/D/F
    
    # 维度评分
    liquidity_score = Column(Numeric(5, 2))      # 偿债能力
    profitability_score = Column(Numeric(5, 2))  # 盈利能力
    efficiency_score = Column(Numeric(5, 2))     # 营运能力
    growth_score = Column(Numeric(5, 2))         # 成长能力
    cashflow_score = Column(Numeric(5, 2))       # 现金流健康
    
    # 指标详情
    indicators = Column(JSON)  # 各项财务指标详情
    
    # 行业对比
    industry_percentile = Column(Numeric(5, 2))  # 行业百分位
    industry_benchmark = Column(JSON)            # 行业基准值
    
    # 诊断结果
    strengths = Column(JSON)   # 优势项
    weaknesses = Column(JSON)  # 弱势项
    risks = Column(JSON)       # 风险点
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
    period = Column(String(20))  # 2024-01


class AIInsight(Base):
    """AI洞察建议"""
    __tablename__ = "ai_insights"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    # 洞察类型
    insight_type = Column(String(50))  # anomaly/opportunity/risk/tip
    category = Column(String(50))      # revenue/expense/cashflow/tax/etc
    
    # 内容
    title = Column(String(200), nullable=False)
    description = Column(Text)
    impact = Column(Text)  # 影响分析
    recommendation = Column(Text)  # 具体建议
    
    # 数据支持
    supporting_data = Column(JSON)  # 支撑数据
    chart_config = Column(JSON)     # 图表配置
    
    # 优先级与状态
    priority = Column(String(20), default="medium")  # low/medium/high/critical
    status = Column(String(20), default="pending")   # pending/dismissed/accepted/done
    
    # 用户反馈
    user_feedback = Column(String(50))  # helpful/not_helpful/irrelevant
    feedback_comment = Column(Text)
    
    # 定时触发
    is_scheduled = Column(Boolean, default=False)
    scheduled_for = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    dismissed_at = Column(DateTime)
    resolved_at = Column(DateTime)


class CashFlowForecast(Base):
    """现金流预测"""
    __tablename__ = "ai_cashflow_forecasts"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    # 预测参数
    forecast_period = Column(String(20))  # weekly/monthly
    horizon_weeks = Column(Integer)       # 预测周数
    
    # 预测结果
    forecast_data = Column(JSON)  # [{week: 1, inflow: 100000, outflow: 80000, net: 20000, balance: 500000}]
    
    # 关键指标
    min_balance = Column(Numeric(15, 2))
    min_balance_week = Column(Integer)
    shortfall_weeks = Column(JSON)  # 可能出现缺口的周
    
    # 置信区间
    confidence_interval = Column(JSON)  # 上下界
    
    # 优化建议
    optimization_suggestions = Column(JSON)
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class CustomerValueAnalysis(Base):
    """客户价值分析"""
    __tablename__ = "ai_customer_value_analyses"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"))
    
    # 这里customer_id是代账公司的客户（即最终企业客户）
    # 分析的是该企业客户的价值
    analyzed_customer_id = Column(UUID, ForeignKey("customers.id"))
    
    # RFM指标
    recency_days = Column(Integer)      # 最近消费距今天数
    frequency_12m = Column(Integer)     # 12个月消费频次
    monetary_12m = Column(Numeric(15, 2))  # 12个月消费金额
    
    # 价值分层
    value_tier = Column(String(20))  # high/medium/low
    churn_risk = Column(String(20))  # high/medium/low
    
    # 客户画像
    lifetime_value = Column(Numeric(15, 2))  # 生命周期价值预测
    avg_order_value = Column(Numeric(15, 2))
    profit_margin = Column(Numeric(5, 2))
    
    # 建议
    retention_strategy = Column(Text)
    upsell_opportunities = Column(JSON)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
```

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│  主动发现层 (Proactive Discovery)                               │
│  - 定时扫描器 (每日/每周运行)                                   │
│  - 实时监控器 (异常即时触发)                                    │
│  - 预测分析器 (趋势预判)                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  智能分析层 (Analysis Engine)                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ 财务健康    │ │ 异常检测    │ │ 机会挖掘    │              │
│  │ 评分模型    │ │ 引擎        │ │ 引擎        │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ 现金流      │ │ 行业对标    │ │ 预测模型    │              │
│  │ 预测模型    │ │ 分析        │ │ (收入/流失) │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  建议生成层 (Recommendation Engine)                             │
│  - 优先级排序                                                   │
│  - 个性化文案生成 (LLM)                                         │
│  - 行动方案生成                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  触达层 (Delivery)                                              │
│  - 站内消息  │  - 邮件通知  │  - IM推送  │  - 报告生成         │
└─────────────────────────────────────────────────────────────────┘
```

## 4. 核心实现

### 4.1 财务健康评分引擎

```python
class FinancialHealthEngine:
    """财务健康评分引擎"""
    
    def __init__(self):
        self.industry_benchmarks = IndustryBenchmarkService()
        self.scoring_weights = {
            "liquidity": 0.25,
            "profitability": 0.25,
            "efficiency": 0.20,
            "growth": 0.15,
            "cashflow": 0.15
        }
    
    def calculate_health_score(self, customer_id: str, period: str) -> FinancialHealthScore:
        """
        计算财务健康评分
        """
        # 1. 获取财务数据
        financial_data = self._get_financial_data(customer_id, period)
        
        # 2. 计算各维度指标
        indicators = {
            "liquidity": self._calc_liquidity_indicators(financial_data),
            "profitability": self._calc_profitability_indicators(financial_data),
            "efficiency": self._calc_efficiency_indicators(financial_data),
            "growth": self._calc_growth_indicators(customer_id, period),
            "cashflow": self._calc_cashflow_indicators(financial_data)
        }
        
        # 3. 维度评分（0-100）
        scores = {}
        for dimension, metrics in indicators.items():
            scores[dimension] = self._score_dimension(dimension, metrics)
        
        # 4. 计算综合评分
        overall_score = sum(
            scores[d] * self.scoring_weights[d] 
            for d in scores
        )
        
        # 5. 行业对比
        industry = self._get_customer_industry(customer_id)
        benchmark = self.industry_benchmarks.get_benchmark(industry, period)
        percentile = self._calc_percentile(overall_score, benchmark)
        
        # 6. 识别优劣势
        strengths, weaknesses = self._identify_strengths_weaknesses(scores, indicators)
        
        # 7. 风险识别
        risks = self._identify_risks(indicators)
        
        return FinancialHealthScore(
            customer_id=customer_id,
            period=period,
            overall_score=overall_score,
            grade=self._score_to_grade(overall_score),
            liquidity_score=scores["liquidity"],
            profitability_score=scores["profitability"],
            efficiency_score=scores["efficiency"],
            growth_score=scores["growth"],
            cashflow_score=scores["cashflow"],
            indicators=indicators,
            industry_percentile=percentile,
            industry_benchmark=benchmark,
            strengths=strengths,
            weaknesses=weaknesses,
            risks=risks
        )
    
    def _calc_liquidity_indicators(self, data: dict) -> dict:
        """计算偿债能力指标"""
        return {
            "current_ratio": data["current_assets"] / data["current_liabilities"],
            "quick_ratio": (data["current_assets"] - data["inventory"]) / data["current_liabilities"],
            "cash_ratio": data["cash"] / data["current_liabilities"],
            "debt_to_equity": data["total_liabilities"] / data["total_equity"]
        }
    
    def _calc_profitability_indicators(self, data: dict) -> dict:
        """计算盈利能力指标"""
        return {
            "gross_margin": data["gross_profit"] / data["revenue"],
            "net_margin": data["net_profit"] / data["revenue"],
            "roe": data["net_profit"] / data["total_equity"],
            "roa": data["net_profit"] / data["total_assets"]
        }
    
    def _score_dimension(self, dimension: str, metrics: dict) -> float:
        """
        对维度进行评分
        使用行业基准或经验规则
        """
        scoring_rules = {
            "liquidity": {
                "current_ratio": [(2.0, 100), (1.5, 80), (1.0, 60), (0, 0)],
                "quick_ratio": [(1.0, 100), (0.8, 80), (0.5, 60), (0, 0)],
            },
            "profitability": {
                "gross_margin": [(0.4, 100), (0.3, 80), (0.2, 60), (0, 0)],
                "net_margin": [(0.15, 100), (0.10, 80), (0.05, 60), (0, 0)],
            }
            # ... 其他维度
        }
        
        scores = []
        for metric, value in metrics.items():
            if metric in scoring_rules.get(dimension, {}):
                rule = scoring_rules[dimension][metric]
                score = self._apply_scoring_rule(value, rule)
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 50
```

### 4.2 主动发现引擎

```python
class ProactiveDiscoveryEngine:
    """主动发现引擎 - 定时扫描和实时监控"""
    
    def __init__(self):
        self.health_engine = FinancialHealthEngine()
        self.anomaly_detector = AnomalyDetector()
        self.opportunity_miner = OpportunityMiner()
    
    async def daily_scan(self, customer_id: str):
        """
        每日扫描 - 发现异常和机会
        """
        insights = []
        
        # 1. 现金流监控
        cashflow_insights = await self._monitor_cashflow(customer_id)
        insights.extend(cashflow_insights)
        
        # 2. 费用异常检测
        expense_insights = await self._detect_expense_anomalies(customer_id)
        insights.extend(expense_insights)
        
        # 3. 收入波动分析
        revenue_insights = await self._analyze_revenue_changes(customer_id)
        insights.extend(revenue_insights)
        
        # 4. 临期事项提醒
        deadline_insights = await self._check_upcoming_deadlines(customer_id)
        insights.extend(deadline_insights)
        
        # 5. 保存并推送
        for insight in insights:
            await self._save_and_notify(insight)
    
    async def weekly_analysis(self, customer_id: str):
        """
        每周分析 - 生成周报
        """
        # 1. 更新财务健康评分
        health_score = self.health_engine.calculate_health_score(
            customer_id, 
            period=self._current_period()
        )
        
        # 2. 生成周报
        weekly_report = await self._generate_weekly_report(customer_id, health_score)
        
        # 3. 推送周报
        await self._deliver_report(weekly_report, channels=["email", "in_app"])
    
    async def _monitor_cashflow(self, customer_id: str) -> List[AIInsight]:
        """监控现金流，发现风险"""
        insights = []
        
        # 获取当前余额
        current_balance = await self._get_current_balance(customer_id)
        
        # 预测未来4周现金流
        forecast = await self._forecast_cashflow(customer_id, weeks=4)
        
        # 检查资金缺口
        if forecast.min_balance < 0:
            insights.append(AIInsight(
                customer_id=customer_id,
                insight_type="risk",
                category="cashflow",
                title=f"未来4周可能出现资金缺口",
                description=f"预计第{forecast.min_balance_week}周现金流为负，缺口约{abs(forecast.min_balance)}元",
                impact="可能影响供应商付款和工资发放",
                recommendation=self._generate_cashflow_recommendation(forecast),
                priority="critical",
                supporting_data={"forecast": forecast.to_dict()}
            ))
        elif forecast.min_balance < current_balance * 0.1:
            insights.append(AIInsight(
                customer_id=customer_id,
                insight_type="risk",
                category="cashflow",
                title="现金流偏紧，建议关注",
                description=f"预计最低余额仅为当前余额的{forecast.min_balance/current_balance:.0%}",
                recommendation="建议加快应收账款回收或准备短期融资",
                priority="high"
            ))
        
        return insights
    
    async def _detect_expense_anomalies(self, customer_id: str) -> List[AIInsight]:
        """检测费用异常"""
        insights = []
        
        # 获取本月费用数据
        current_month = await self._get_expense_by_category(customer_id, period="current_month")
        last_month = await self._get_expense_by_category(customer_id, period="last_month")
        
        # 对比分析
        for category, amount in current_month.items():
            last_amount = last_month.get(category, 0)
            if last_amount > 0:
                change_pct = (amount - last_amount) / last_amount
                
                # 异常增长（超过50%）
                if change_pct > 0.5 and amount > 10000:  # 金额超过1万才提醒
                    insights.append(AIInsight(
                        customer_id=customer_id,
                        insight_type="anomaly",
                        category="expense",
                        title=f"{category}费用异常增长",
                        description=f"本月{category}费用为{amount}元，环比增长{change_pct:.0%}",
                        impact=f"增加支出{amount - last_amount:.0f}元",
                        recommendation="请核实费用发生的合理性，检查是否有重复报销或异常支出",
                        priority="high" if change_pct > 1.0 else "medium"
                    ))
        
        return insights
```

### 4.3 现金流预测模型

```python
class CashFlowPredictor:
    """现金流预测器"""
    
    def __init__(self):
        self.ar_model = ARCollectionPredictor()  # 应收账款回收预测
        self.ap_model = APPaymentPredictor()     # 应付账款支付预测
        self.recurring_model = RecurringFlowPredictor()  # 固定收支预测
    
    async def forecast(
        self, 
        customer_id: str, 
        weeks: int = 4,
        include_confidence_interval: bool = True
    ) -> CashFlowForecast:
        """
        预测现金流
        """
        # 1. 获取当前现金余额
        current_balance = await self._get_current_balance(customer_id)
        
        # 2. 预测现金流入
        inflows = {
            "accounts_receivable": await self.ar_model.predict(customer_id, weeks),
            "recurring_revenue": await self.recurring_model.predict_revenue(customer_id, weeks),
            "other_income": await self._predict_other_income(customer_id, weeks)
        }
        
        # 3. 预测现金流出
        outflows = {
            "accounts_payable": await self.ap_model.predict(customer_id, weeks),
            "payroll": await self._predict_payroll(customer_id, weeks),
            "tax_payment": await self._predict_tax_payment(customer_id, weeks),
            "operating_expenses": await self._predict_opex(customer_id, weeks)
        }
        
        # 4. 计算净现金流和余额
        forecast_data = []
        running_balance = current_balance
        
        for week in range(1, weeks + 1):
            weekly_inflow = sum(inflows[src][week-1] for src in inflows)
            weekly_outflow = sum(outflows[src][week-1] for src in outflows)
            net_flow = weekly_inflow - weekly_outflow
            running_balance += net_flow
            
            forecast_data.append({
                "week": week,
                "inflow": weekly_inflow,
                "outflow": weekly_outflow,
                "net": net_flow,
                "balance": running_balance,
                "shortfall_risk": running_balance < 0
            })
        
        # 5. 计算关键指标
        balances = [d["balance"] for d in forecast_data]
        min_balance = min(balances)
        min_balance_week = forecast_data[balances.index(min_balance)]["week"]
        shortfall_weeks = [d["week"] for d in forecast_data if d["shortfall_risk"]]
        
        # 6. 生成优化建议
        suggestions = self._generate_optimization_suggestions(
            forecast_data, inflows, outflows
        )
        
        return CashFlowForecast(
            customer_id=customer_id,
            forecast_period="weekly",
            horizon_weeks=weeks,
            forecast_data=forecast_data,
            min_balance=min_balance,
            min_balance_week=min_balance_week,
            shortfall_weeks=shortfall_weeks,
            optimization_suggestions=suggestions
        )
    
    async def _predict_payroll(self, customer_id: str, weeks: int) -> List[float]:
        """预测工资支出"""
        # 获取历史工资数据
        historical_payroll = await self._get_historical_payroll(customer_id, months=6)
        
        # 获取发薪日
        payday = await self._get_payday(customer_id)  # 如：每月15日
        
        predictions = []
        for week in range(weeks):
            week_start = self._get_week_start(week)
            week_end = week_start + timedelta(days=6)
            
            # 检查该周是否包含发薪日
            if self._contains_payday(week_start, week_end, payday):
                # 预测工资 = 历史平均 + 变动因素
                base_amount = sum(historical_payroll) / len(historical_payroll)
                
                # 考虑新员工、调薪等因素
                adjustments = await self._get_payroll_adjustments(customer_id, week)
                predictions.append(base_amount + adjustments)
            else:
                predictions.append(0)
        
        return predictions
```

## 5. 建议生成与推送

### 5.1 LLM文案生成

```python
class RecommendationGenerator:
    """建议文案生成器"""
    
    def __init__(self):
        self.llm = LargeLanguageModel()
    
    def generate(self, insight: AIInsight, user_profile: dict) -> str:
        """
        生成个性化建议文案
        """
        prompt = f"""
        作为专业财务顾问，请基于以下洞察生成建议文案：
        
        洞察类型：{insight.insight_type}
        类别：{insight.category}
        标题：{insight.title}
        描述：{insight.description}
        影响：{insight.impact}
        
        用户画像：
        - 行业：{user_profile['industry']}
        - 企业规模：{user_profile['size']}
        - 财务专业度：{user_profile['financial_expertise']}
        
        请生成：
        1. 一个简洁有力的标题（不超过20字）
        2. 通俗易懂的描述（50-100字）
        3. 具体的行动建议（2-3条，每条包含操作步骤）
        4. 预期收益（量化）
        
        语气：专业但易懂，有指导性但不生硬
        """
        
        return self.llm.generate(prompt)
```

### 5.2 推送策略

```python
class InsightDeliveryService:
    """洞察推送服务"""
    
    def __init__(self):
        self.channels = {
            "in_app": InAppNotifier(),
            "email": EmailNotifier(),
            "wechat": WechatNotifier(),
            "dingtalk": DingtalkNotifier()
        }
    
    async def deliver(self, insight: AIInsight, user_preferences: dict):
        """
        推送洞察
        """
        # 根据优先级和类型选择渠道
        channels = self._select_channels(insight, user_preferences)
        
        # 生成渠道适配内容
        for channel in channels:
            content = self._adapt_content(insight, channel)
            await self.channels[channel].send(
                user_id=insight.customer_id,
                title=insight.title,
                content=content,
                actions=self._get_actions(insight)
            )
    
    def _select_channels(self, insight: AIInsight, preferences: dict) -> List[str]:
        """选择推送渠道"""
        channels = []
        
        # 关键级：全渠道推送
        if insight.priority == "critical":
            channels = ["in_app", "email", "wechat"]
        # 高优先级：应用内+邮件
        elif insight.priority == "high":
            channels = ["in_app", "email"]
        # 中优先级：仅应用内
        elif insight.priority == "medium":
            channels = ["in_app"]
        
        # 根据用户偏好过滤
        return [c for c in channels if preferences.get(f"allow_{c}", True)]
```

## 6. 接口设计

### 6.1 获取财务健康评分

```http
GET /api/v1/ai/cfo/health-score
Response:
{
    "overall_score": 78,
    "grade": "B",
    "scores": {
        "liquidity": 85,
        "profitability": 72,
        "efficiency": 68,
        "growth": 80,
        "cashflow": 75
    },
    "industry_percentile": 72,
    "strengths": [
        {"indicator": "流动比率", "value": 2.3, "description": "短期偿债能力强"}
    ],
    "weaknesses": [
        {"indicator": "应收账款周转", "value": 68, "description": "回款周期偏长"}
    ],
    "risks": [
        {"type": "cashflow", "level": "medium", "description": "下月预计资金紧张"}
    ]
}
```

### 6.2 获取AI洞察列表

```http
GET /api/v1/ai/cfo/insights?status=pending&priority=high,critical
Response:
{
    "insights": [
        {
            "id": "ins_xxx",
            "type": "risk",
            "priority": "critical",
            "title": "未来4周可能出现资金缺口",
            "description": "预计第3周现金流为负...",
            "recommendation": "建议加快应收账款回收...",
            "created_at": "2024-01-15T10:00:00Z",
            "actions": [
                {"label": "查看详情", "action": "view_detail"},
                {"label": "忽略", "action": "dismiss"}
            ]
        }
    ],
    "summary": {
        "total": 5,
        "critical": 1,
        "high": 2,
        "medium": 2
    }
}
```

### 6.3 获取现金流预测

```http
GET /api/v1/ai/cfo/cashflow-forecast?weeks=8
Response:
{
    "current_balance": 500000,
    "forecast": [
        {"week": 1, "inflow": 200000, "outflow": 150000, "net": 50000, "balance": 550000},
        {"week": 2, "inflow": 180000, "outflow": 200000, "net": -20000, "balance": 530000},
        // ...
    ],
    "min_balance": 320000,
    "min_balance_week": 6,
    "shortfall_risk": false,
    "suggestions": [
        "第6周余额较低，建议提前催收A客户欠款"
    ]
}
```

## 7. 前端展示

### 7.1 财务健康仪表盘

```
┌─────────────────────────────────────────────────────────────┐
│  💰 财务健康评分                         [查看历史趋势]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    ┌─────────────────────────────────────────┐              │
│    │                                         │              │
│    │           综合评分                      │              │
│    │                                         │              │
│    │            ┌──────────┐                 │              │
│    │            │          │                 │              │
│    │            │    78    │    B级          │              │
│    │            │   /100   │                 │              │
│    │            │          │                 │              │
│    │            └──────────┘                 │              │
│    │                                         │              │
│    │    超过72%的同行企业                    │              │
│    └─────────────────────────────────────────┘              │
│                                                             │
│  📊 维度评分                                                 │
│  ┌────────────┬────────────┬────────────┐                  │
│  │ 偿债能力   │ 盈利能力   │ 营运能力   │                  │
│  │    85      │    72      │    68      │                  │
│  │  ████████  │  ██████    │  █████     │                  │
│  └────────────┴────────────┴────────────┘                  │
│  ┌────────────┬────────────┐                               │
│  │ 成长能力   │ 现金流     │                               │
│  │    80      │    75      │                               │
│  │  ████████  │  ███████   │                               │
│  └────────────┴────────────┘                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 8. 验收标准

### 8.1 功能验收
- [ ] 财务健康评分计算准确，5个维度评分合理
- [ ] 主动发现异常，日均发现2-5条有效洞察
- [ ] 现金流预测准确率在80%以上（4周预测）
- [ ] 支持至少10种异常检测场景
- [ ] 洞察推送渠道完整（站内、邮件、IM）

### 8.2 性能验收
- [ ] 健康评分计算时间 ≤ 2秒
- [ ] 现金流预测时间 ≤ 3秒
- [ ] 每日扫描任务30分钟内完成

### 8.3 业务验收
- [ ] 用户主动采纳建议率 ≥ 40%
- [ ] 财务健康评分与实际经营状况相关性高
- [ ] 客户满意度 ≥ 4.5/5

================================================================================
                              任务依赖
================================================================================

- 依赖：TASK-AI-CHAT-01 对话式助手（基础能力）
- 依赖：Step4 数据基础完善
- 依赖：行业基准数据准备

================================================================================
                              风险与应对
================================================================================

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 评分模型不准确 | 高 | 财务专家参与设计，A/B测试验证 |
| 建议过于泛泛 | 中 | 结合企业具体数据，提供可操作建议 |
| 用户不信任AI建议 | 中 | 提供数据支撑，可解释性强 |
