# 任务编号：TASK-AI-FOR-01
# 任务名称：预测性财务分析
# 优先级：P1
# 预估工期：10天
# 负责人：后端/数据科学家

================================================================================
                              任务描述
================================================================================

开发预测性财务分析引擎，利用机器学习和时序分析技术，实现收入预测、现金流预测、客户流失预警、坏账风险预测等能力，从"看过去"转变为"知未来"。

================================================================================
                              需求详情
================================================================================

## 1. 核心能力

### 1.1 收入预测
- 多维度收入预测（按产品/客户/渠道）
- 季节性波动建模
- 短期/中期/长期预测
- 置信区间展示

### 1.2 现金流预测
- 现金流入/流出分项预测
- 应收账款回收预测
- 资金缺口预警
- 滚动预测更新

### 1.3 客户流失预警
- 客户健康度评分
- 流失风险分级
- 预警提前期（30/60/90天）
- 挽留策略推荐

### 1.4 坏账风险预测
- 应收账款风险评分
- 逾期概率预测
- 催收优先级排序
- 坏账准备金建议

### 1.5 库存需求预测（可选）
- 基于销售预测的需求计划
- 安全库存建议
- 采购时机优化

## 2. 数据模型

```python
class RevenueForecast(Base):
    """收入预测"""
    __tablename__ = "ai_revenue_forecasts"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    # 预测参数
    forecast_type = Column(String(50))  # total/by_product/by_customer
    horizon_months = Column(Integer)
    
    # 预测结果
    forecast_data = Column(JSON)  # [{
        # "period": "2024-02",
        # "predicted_value": 1500000,
        # "lower_bound": 1400000,
        # "upper_bound": 1600000,
        # "confidence": 0.85
    # }]
    
    # 关键驱动因素
    key_drivers = Column(JSON)  # [{
        # "factor": "季节性",
        # "impact": 0.15,
        # "description": "春节后通常是淡季"
    # }]
    
    # 模型信息
    model_version = Column(String(50))
    model_accuracy = Column(Numeric(5, 2))  # 历史准确率
    
    generated_at = Column(DateTime, default=datetime.utcnow)


class CashFlowForecast(Base):
    """现金流预测"""
    __tablename__ = "ai_cashflow_forecasts"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    # 预测粒度
    granularity = Column(String(20))  # daily/weekly/monthly
    horizon_periods = Column(Integer)  # 预测期数
    
    # 分项预测
    inflow_forecast = Column(JSON)  # {
        # "accounts_receivable": [...],
        # "recurring_revenue": [...],
        # "other": [...]
    # }
    
    outflow_forecast = Column(JSON)  # {
        # "accounts_payable": [...],
        # "payroll": [...],
        # "tax": [...],
        # "opex": [...]
    # }
    
    # 净现金流预测
    net_cashflow = Column(JSON)  # [{period, inflow, outflow, net, balance}]
    
    # 风险点
    shortfall_periods = Column(JSON)  # 资金缺口期间
    risk_analysis = Column(Text)
    
    generated_at = Column(DateTime, default=datetime.utcnow)


class ChurnRiskPrediction(Base):
    """客户流失风险预测"""
    __tablename__ = "ai_churn_risk_predictions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"))
    
    # 预测对象（代账公司的客户）
    target_customer_id = Column(UUID, ForeignKey("customers.id"))
    
    # 风险评分
    churn_probability = Column(Numeric(5, 4))  # 0-1
    risk_level = Column(String(20))  # high/medium/low
    
    # 预测期
    prediction_horizon_days = Column(Integer)  # 30/60/90
    
    # 影响因素
    contributing_factors = Column(JSON)  # [{
        # "factor": "登录频率下降",
        # "weight": 0.35,
        # "trend": "declining"
    # }]
    
    # 建议
    recommended_actions = Column(JSON)  # ["主动联系", "提供培训", "优惠续费"]
    
    # 实际结果（用于模型反馈）
    actual_outcome = Column(String(20))  # churned/retained
    outcome_recorded_at = Column(DateTime)
    
    predicted_at = Column(DateTime, default=datetime.utcnow)


class BadDebtRisk(Base):
    """坏账风险预测"""
    __tablename__ = "ai_bad_debt_risks"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"))
    
    # 应收账款
    receivable_id = Column(UUID, ForeignKey("accounts_receivable.id"))
    
    # 风险评分
    default_probability = Column(Numeric(5, 4))  # 违约概率
    risk_score = Column(Integer)  # 0-100
    risk_level = Column(String(20))  # high/medium/low
    
    # 预测结果
    predicted_days_to_payment = Column(Integer)
    predicted_loss_amount = Column(Numeric(15, 2))
    
    # 建议
    recommended_collection_strategy = Column(Text)
    suggested_provision_rate = Column(Numeric(5, 4))  # 建议计提比例
    
    predicted_at = Column(DateTime, default=datetime.utcnow)
```

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│  数据层                                                        │
│  - 历史交易数据                                                │
│  - 客户行为数据                                                │
│  - 外部数据源（市场、季节等）                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  特征工程层                                                    │
│  - 时序特征提取（趋势、季节性、周期性）                        │
│  - 统计特征（均值、方差、分位数）                              │
│  - 滞后特征                                                    │
│  - 聚合特征                                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  模型层                                                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ Prophet     │ │ LSTM/Transformer│ │ XGBoost    │              │
│  │ (时序分解)  │ │ (深度学习)   │ │ (特征模型) │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│  ┌─────────────┐ ┌─────────────┐                              │
│  │ 集成模型    │ │ 规则引擎    │                              │
│  │ (Ensemble)  │ │ (业务规则)  │                              │
│  └─────────────┘ └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  预测服务层                                                    │
│  - 预测生成                                                    │
│  - 置信区间计算                                                │
│  - 模型解释                                                    │
│  - A/B测试                                                     │
└─────────────────────────────────────────────────────────────────┘
```

## 4. 核心实现

### 4.1 收入预测引擎

```python
class RevenueForecastingEngine:
    """收入预测引擎"""
    
    def __init__(self):
        self.prophet_model = ProphetModel()
        self.lstm_model = LSTMModel()
        self.ensemble = EnsembleModel()
    
    async def forecast(
        self, 
        customer_id: str,
        horizon_months: int = 3,
        granularity: str = "monthly"
    ) -> RevenueForecast:
        """
        收入预测主入口
        """
        # 1. 获取历史数据
        historical_data = await self._get_historical_revenue(
            customer_id, months=24
        )
        
        # 2. 特征工程
        features = self._engineer_features(historical_data)
        
        # 3. 多模型预测
        prophet_forecast = self.prophet_model.predict(
            historical_data, horizon_months
        )
        
        lstm_forecast = self.lstm_model.predict(
            features, horizon_months
        )
        
        # 4. 集成融合
        ensemble_forecast = self.ensemble.combine(
            [prophet_forecast, lstm_forecast],
            weights=[0.6, 0.4]
        )
        
        # 5. 计算置信区间
        forecast_with_ci = self._calculate_confidence_intervals(
            ensemble_forecast, historical_data
        )
        
        # 6. 识别关键驱动因素
        drivers = self._identify_key_drivers(historical_data, features)
        
        # 7. 计算模型准确率
        accuracy = self._calculate_historical_accuracy(customer_id)
        
        return RevenueForecast(
            customer_id=customer_id,
            forecast_type="total",
            horizon_months=horizon_months,
            forecast_data=forecast_with_ci,
            key_drivers=drivers,
            model_version="v2.1",
            model_accuracy=accuracy
        )
    
    def _engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """特征工程"""
        df = data.copy()
        
        # 时间特征
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['year'] = df['date'].dt.year
        
        # 滞后特征
        for lag in [1, 2, 3, 6, 12]:
            df[f'revenue_lag_{lag}'] = df['revenue'].shift(lag)
        
        # 滚动统计
        for window in [3, 6, 12]:
            df[f'revenue_ma_{window}'] = df['revenue'].rolling(window).mean()
            df[f'revenue_std_{window}'] = df['revenue'].rolling(window).std()
        
        # 同比增长
        df['yoy_growth'] = df['revenue'] / df['revenue_lag_12'] - 1
        
        # 环比增长率
        df['mom_growth'] = df['revenue'] / df['revenue_lag_1'] - 1
        
        # 季节性指数
        df['seasonal_index'] = df['revenue'] / df['revenue_ma_12']
        
        return df.dropna()
    
    def _identify_key_drivers(self, historical_data: pd.DataFrame, features: pd.DataFrame) -> List[dict]:
        """识别影响收入的关键驱动因素"""
        drivers = []
        
        # 1. 季节性影响
        seasonal_variance = historical_data.groupby('month')['revenue'].mean().var()
        if seasonal_variance > historical_data['revenue'].mean() * 0.1:
            peak_months = historical_data.groupby('month')['revenue'].mean().nlargest(3).index.tolist()
            drivers.append({
                "factor": "季节性波动",
                "impact": 0.25,
                "description": f"收入呈现明显季节性，{peak_months}月为旺季",
                "trend": "stable"
            })
        
        # 2. 趋势影响
        recent_trend = features['revenue'].iloc[-6:].mean() / features['revenue'].iloc[-12:-6].mean() - 1
        if abs(recent_trend) > 0.1:
            drivers.append({
                "factor": "增长趋势",
                "impact": abs(recent_trend),
                "description": f"近半年收入{'增长' if recent_trend > 0 else '下降'}{abs(recent_trend):.1%}",
                "trend": "up" if recent_trend > 0 else "down"
            })
        
        # 3. 客户集中度
        customer_concentration = self._calculate_customer_concentration(historical_data)
        if customer_concentration > 0.5:
            drivers.append({
                "factor": "大客户依赖",
                "impact": customer_concentration,
                "description": f"Top3客户贡献{customer_concentration:.0%}收入",
                "trend": "stable"
            })
        
        return sorted(drivers, key=lambda x: x['impact'], reverse=True)
```

### 4.2 Prophet模型实现

```python
from prophet import Prophet

class ProphetModel:
    """基于Prophet的时序预测"""
    
    def __init__(self):
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0
        )
        
        # 添加节假日效应
        self.model.add_country_holidays(country_name='CN')
    
    def fit(self, df: pd.DataFrame) -> 'ProphetModel':
        """
        训练模型
        df格式：ds(日期), y(数值)
        """
        self.model.fit(df)
        return self
    
    def predict(self, historical_data: pd.DataFrame, periods: int) -> pd.DataFrame:
        """预测未来"""
        # 准备历史数据
        df = historical_data.rename(columns={
            'date': 'ds',
            'revenue': 'y'
        })
        
        # 训练
        self.fit(df)
        
        # 生成未来日期
        future = self.model.make_future_dataframe(periods=periods, freq='M')
        
        # 预测
        forecast = self.model.predict(future)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
```

### 4.3 客户流失预测

```python
class ChurnPredictionModel:
    """客户流失预测模型"""
    
    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            objective='binary:logistic'
        )
    
    async def predict(
        self, 
        customer_id: str,
        target_customer_id: str,
        horizon_days: int = 30
    ) -> ChurnRiskPrediction:
        """
        预测客户流失风险
        """
        # 1. 构建特征
        features = await self._build_churn_features(
            customer_id, target_customer_id
        )
        
        # 2. 模型预测
        churn_prob = self.model.predict_proba([features])[0][1]
        
        # 3. 风险分级
        risk_level = self._classify_risk(churn_prob)
        
        # 4. 解释预测原因
        factors = self._explain_prediction(features, churn_prob)
        
        # 5. 生成建议
        actions = self._generate_retention_actions(churn_prob, factors)
        
        return ChurnRiskPrediction(
            customer_id=customer_id,
            target_customer_id=target_customer_id,
            churn_probability=churn_prob,
            risk_level=risk_level,
            prediction_horizon_days=horizon_days,
            contributing_factors=factors,
            recommended_actions=actions
        )
    
    async def _build_churn_features(
        self, 
        customer_id: str, 
        target_customer_id: str
    ) -> List[float]:
        """
        构建流失预测特征
        """
        features = {}
        
        # R - Recency (最近活跃度)
        last_login = await self._get_last_login(target_customer_id)
        features['days_since_last_login'] = (datetime.now() - last_login).days
        
        # F - Frequency (使用频率)
        login_history = await self._get_login_history(target_customer_id, days=30)
        features['login_frequency_30d'] = len(login_history)
        features['avg_session_duration'] = np.mean([s['duration'] for s in login_history])
        
        # M - Monetary (价值)
        revenue_contribution = await self._get_revenue_contribution(target_customer_id)
        features['revenue_12m'] = revenue_contribution
        features['profit_margin'] = await self._get_profit_margin(target_customer_id)
        
        # 产品使用深度
        features['feature_usage_breadth'] = await self._count_used_features(target_customer_id)
        features['data_upload_consistency'] = await self._calc_upload_consistency(target_customer_id)
        
        # 服务交互
        support_tickets = await self._get_support_tickets(target_customer_id, months=6)
        features['support_ticket_count_6m'] = len(support_tickets)
        features['avg_ticket_resolution_time'] = np.mean([t['resolution_time'] for t in support_tickets])
        
        # 满意度
        features['nps_score'] = await self._get_latest_nps(target_customer_id)
        
        # 合同状态
        contract = await self._get_contract_info(target_customer_id)
        features['days_to_contract_expiry'] = (contract['end_date'] - datetime.now().date()).days
        features['contract_value'] = contract['value']
        
        # 财务行为
        features['payment_delay_avg'] = await self._calc_avg_payment_delay(target_customer_id)
        features['late_payment_count_12m'] = await self._count_late_payments(target_customer_id, months=12)
        
        return list(features.values())
```

### 4.4 坏账风险预测

```python
class BadDebtPredictionModel:
    """坏账风险预测模型"""
    
    async def predict_risk(
        self, 
        customer_id: str,
        receivable_id: str
    ) -> BadDebtRisk:
        """
        预测应收账款坏账风险
        """
        # 1. 获取应收账款信息
        receivable = await self._get_receivable(receivable_id)
        debtor_id = receivable['debtor_customer_id']
        
        # 2. 构建特征
        features = await self._build_features(customer_id, debtor_id, receivable)
        
        # 3. 预测违约概率
        default_prob = self._predict_default_probability(features)
        
        # 4. 预测回收时间和金额
        days_to_payment = self._predict_payment_timing(features)
        loss_amount = receivable['amount'] * default_prob
        
        # 5. 确定风险等级
        risk_level = self._classify_bad_debt_risk(default_prob)
        
        # 6. 生成催收策略建议
        strategy = self._generate_collection_strategy(
            risk_level, receivable, features
        )
        
        # 7. 建议计提比例
        provision_rate = self._suggest_provision_rate(default_prob, receivable)
        
        return BadDebtRisk(
            customer_id=customer_id,
            receivable_id=receivable_id,
            default_probability=default_prob,
            risk_score=int(default_prob * 100),
            risk_level=risk_level,
            predicted_days_to_payment=days_to_payment,
            predicted_loss_amount=loss_amount,
            recommended_collection_strategy=strategy,
            suggested_provision_rate=provision_rate
        )
```

## 5. 接口设计

### 5.1 收入预测

```http
GET /api/v1/ai/forecast/revenue?horizon=3
Response:
{
    "forecast_id": "for_xxx",
    "horizon_months": 3,
    "forecast": [
        {
            "period": "2024-02",
            "predicted_value": 1500000,
            "lower_bound": 1400000,
            "upper_bound": 1600000,
            "confidence": 0.85
        },
        {
            "period": "2024-03",
            "predicted_value": 1650000,
            "lower_bound": 1500000,
            "upper_bound": 1800000,
            "confidence": 0.80
        }
    ],
    "key_drivers": [
        {
            "factor": "季节性",
            "impact": 0.25,
            "description": "春节后通常是淡季"
        },
        {
            "factor": "增长趋势",
            "impact": 0.15,
            "description": "近半年收入稳步增长"
        }
    ],
    "model_accuracy": 0.92
}
```

### 5.2 客户流失风险

```http
GET /api/v1/ai/predictions/churn-risk
Response:
{
    "predictions": [
        {
            "customer_id": "cus_xxx",
            "customer_name": "ABC科技",
            "churn_probability": 0.75,
            "risk_level": "high",
            "prediction_horizon_days": 30,
            "contributing_factors": [
                {"factor": "登录频率下降", "weight": 0.35},
                {"factor": "合同即将到期", "weight": 0.25},
                {"factor": "近期有投诉", "weight": 0.20}
            ],
            "recommended_actions": [
                "主动联系，了解满意度",
                "提供续费优惠",
                "安排客户成功经理跟进"
            ]
        }
    ],
    "summary": {
        "high_risk_count": 5,
        "medium_risk_count": 12,
        "low_risk_count": 83
    }
}
```

## 6. 模型评估与监控

```python
class ModelMonitoringService:
    """模型监控服务"""
    
    async def evaluate_forecast_accuracy(self, forecast_id: str):
        """评估预测准确度"""
        forecast = await self._get_forecast(forecast_id)
        actuals = await self._get_actual_values(forecast)
        
        # MAPE计算
        mape = np.mean(np.abs((actuals - forecast.values) / actuals)) * 100
        
        # 准确率
        accuracy = 1 - mape / 100
        
        # 记录指标
        await self._record_metrics(forecast_id, {
            "mape": mape,
            "accuracy": accuracy,
            "bias": np.mean(forecast.values - actuals)
        })
        
        # 如果准确率下降，触发告警
        if accuracy < 0.7:
            await self._trigger_model_retraining(forecast.model_type)
```

## 7. 验收标准

- [ ] 收入预测MAPE ≤ 15%（3个月预测）
- [ ] 现金流预测准确率 ≥ 80%
- [ ] 客户流失预测AUC ≥ 0.8
- [ ] 坏账风险预测准确率 ≥ 75%
- [ ] 预测响应时间 ≤ 5秒
- [ ] 支持实时滚动预测更新

================================================================================
                              任务依赖
================================================================================

- 依赖：历史数据积累（至少12个月）
- 依赖：特征平台建设
- 依赖：模型训练基础设施

================================================================================
                              风险与应对
================================================================================

| 风险 | 影响 | 应对 |
|------|------|------|
| 数据质量不足 | 高 | 数据清洗，异常值处理 |
| 模型准确率低 | 中 | 多模型融合，持续优化 |
| 外部因素影响 | 中 | 引入外部数据源，事件标记 |
