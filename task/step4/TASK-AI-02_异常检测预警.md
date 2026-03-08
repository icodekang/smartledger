# 任务编号：TASK-AI-02
# 任务名称：异常检测预警
# 优先级：P1
# 预估工期：2天
# 负责人：后端

================================================================================
                              任务描述
================================================================================

开发AI异常检测预警系统，自动识别财务数据异常、操作风险、税务风险等，及时预警。

================================================================================
                              需求详情
================================================================================

## 1. 检测类型

| 类型 | 说明 | 检测方式 |
|------|------|----------|
| 金额异常 | 大额交易、整数金额频繁 | 规则+AI |
| 科目异常 | 科目使用不当 | AI学习 |
| 时间异常 | 节假日交易、凌晨交易 | 规则 |
| 对手方异常 | 新交易对手、黑名单 | 规则+比对 |
| 税务风险 | 税负率异常、抵扣异常 | 计算分析 |
| 操作风险 | 异常登录、批量操作 | 行为分析 |

## 2. 数据模型

```python
class AnomalyRule(Base):
    """异常检测规则"""
    __tablename__ = "anomaly_rules"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)  # amount/subject/time/tax/behavior
    
    # 规则条件
    condition_type = Column(String(20))  # threshold/range/pattern/ml
    condition_config = Column(JSON)  # { "operator": ">", "value": 10000 }
    
    severity = Column(String(20), default="medium")  # low/medium/high/critical
    is_enabled = Column(Boolean, default=True)


class AnomalyDetection(Base):
    """异常检测结果"""
    __tablename__ = "anomaly_detections"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"))
    
    rule_id = Column(UUID, ForeignKey("anomaly_rules.id"))
    
    # 异常对象
    source_type = Column(String(50))  # bill/voucher/flow/user
    source_id = Column(UUID)
    
    # 异常详情
    anomaly_type = Column(String(50))
    description = Column(Text)
    severity = Column(String(20))
    
    # 状态
    status = Column(String(20), default="new")  # new/confirmed/false_positive/resolved
    confirmed_by = Column(UUID, ForeignKey("users.id"))
    confirmed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 3. 异常检测引擎

```python
class AnomalyDetectionEngine:
    """异常检测引擎"""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[AnomalyRule]:
        """加载规则"""
        return db.query(AnomalyRule).filter(
            AnomalyRule.is_enabled == True
        ).all()
    
    def detect_bill_anomalies(self, bill: Bill) -> List[AnomalyDetection]:
        """检测票据异常"""
        
        anomalies = []
        
        for rule in self.rules:
            if rule.rule_type == "amount":
                anomaly = self._check_amount_rule(bill, rule)
            elif rule.rule_type == "subject":
                anomaly = self._check_subject_rule(bill, rule)
            elif rule.rule_type == "time":
                anomaly = self._check_time_rule(bill, rule)
            elif rule.rule_type == "counterparty":
                anomaly = self._check_counterparty_rule(bill, rule)
            
            if anomaly:
                anomalies.append(anomaly)
        
        # AI模型检测
        ml_anomalies = self._ml_detection(bill)
        anomalies.extend(ml_anomalies)
        
        return anomalies
    
    def _check_amount_rule(self, bill: Bill, rule: AnomalyRule) -> Optional[AnomalyDetection]:
        """金额规则检查"""
        
        config = rule.condition_config
        amount = float(bill.total_amount)
        threshold = config.get("value", 0)
        
        if config["operator"] == ">" and amount > threshold:
            return AnomalyDetection(
                customer_id=self.customer_id,
                rule_id=rule.id,
                source_type="bill",
                source_id=bill.id,
                anomaly_type="大额交易",
                description=f"交易金额 {amount} 超过阈值 {threshold}",
                severity=rule.severity
            )
        
        return None
    
    def _check_time_rule(self, bill: Bill, rule: AnomalyRule) -> Optional[AnomalyDetection]:
        """时间规则检查"""
        
        # 检查是否节假日
        if is_holiday(bill.invoice_date):
            return AnomalyDetection(
                customer_id=self.customer_id,
                rule_id=rule.id,
                source_type="bill",
                source_id=bill.id,
                anomaly_type="节假日交易",
                description=f"发票日期 {bill.invoice_date} 为节假日",
                severity="low"
            )
        
        return None
    
    def _ml_detection(self, bill: Bill) -> List[AnomalyDetection]:
        """机器学习异常检测"""
        
        anomalies = []
        
        # 加载客户历史数据训练的特征
        features = self._extract_features(bill)
        
        # 使用Isolation Forest检测异常
        from sklearn.ensemble import IsolationForest
        
        model = self._load_isolation_forest_model()
        prediction = model.predict([features])
        
        if prediction[0] == -1:  # -1表示异常
            score = model.score_samples([features])[0]
            
            anomalies.append(AnomalyDetection(
                customer_id=self.customer_id,
                source_type="bill",
                source_id=bill.id,
                anomaly_type="AI检测到异常",
                description=f"该票据特征与历史数据不符，异常分数: {score:.4f}",
                severity="medium"
            ))
        
        return anomalies
```

## 4. 税务风险检测

```python
def detect_tax_risks(customer_id: str, period: str) -> List[dict]:
    """检测税务风险"""
    
    risks = []
    
    # 1. 税负率异常
    tax_burden = calculate_tax_burden(customer_id, period)
    industry_average = get_industry_average(customer_id)
    
    if abs(tax_burden - industry_average) > 0.05:  # 差异超过5%
        risks.append({
            "type": "税负率异常",
            "description": f"当前税负率{tax_burden:.2%}，行业平均{industry_average:.2%}",
            "severity": "high"
        })
    
    # 2. 进项抵扣异常
    input_vat_ratio = calculate_input_vat_ratio(customer_id, period)
    if input_vat_ratio > 0.95:  # 抵扣率过高
        risks.append({
            "type": "进项抵扣异常",
            "description": f"进项抵扣率{input_vat_ratio:.2%}，可能存在虚开发票风险",
            "severity": "critical"
        })
    
    # 3. 销项开票异常
    output_vat_trend = get_output_vat_trend(customer_id, 6)  # 近6个月
    if detect_sudden_drop(output_vat_trend):
        risks.append({
            "type": "销项开票异常",
            "description": "近月销项金额大幅下降，请关注",
            "severity": "medium"
        })
    
    return risks
```

## 5. 预警通知

```python
@celery.task
def send_anomaly_alerts():
    """发送异常预警"""
    
    # 获取未确认的异常
    anomalies = db.query(AnomalyDetection).filter(
        AnomalyDetection.status == "new",
        AnomalyDetection.severity.in_(["high", "critical"])
    ).all()
    
    for anomaly in anomalies:
        # 发送通知
        send_notification(
            user_id=get_customer_admin(anomaly.customer_id),
            title=f"【异常预警】{anomaly.anomaly_type}",
            content=anomaly.description,
            type="warning",
            link=f"/anomalies/{anomaly.id}"
        )
```

## 6. API接口

```
GET    /api/v1/anomaly-rules               # 规则列表
POST   /api/v1/anomaly-rules               # 创建规则
PUT    /api/v1/anomaly-rules/{id}          # 更新规则

GET    /api/v1/anomalies                   # 异常列表
GET    /api/v1/anomalies/{id}              # 异常详情
POST   /api/v1/anomalies/{id}/confirm      # 确认异常
POST   /api/v1/anomalies/{id}/false-positive # 标记误报
POST   /api/v1/anomalies/{id}/resolve      # 标记已处理

GET    /api/v1/tax-risks                   # 税务风险检测
POST   /api/v1/anomalies/detect            # 手动触发检测
```

================================================================================
                              验收标准
================================================================================

1. [ ] 规则检测准确
2. [ ] AI模型检测正常
3. [ ] 税务风险识别完整
4. [ ] 预警通知及时
5. [ ] 异常处理流程完整
6. [ ] 误报率<10%

================================================================================
                              开发提示
================================================================================

1. 模型需要持续训练优化
2. 规则需要可根据客户调整
3. 高风险异常立即通知
4. 保留异常处理历史
5. 定期生成异常分析报告
