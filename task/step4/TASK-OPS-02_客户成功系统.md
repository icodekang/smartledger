# 任务编号：TASK-OPS-02
# 任务名称：客户成功系统
# 优先级：P1
# 预估工期：2天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发客户成功系统，包括客户健康度评分、流失预警、自动化运营等功能，提升客户留存。

================================================================================
                              需求详情
================================================================================

## 1. 健康度评分

### 1.1 评分维度
| 维度 | 权重 | 指标 |
|------|------|------|
| 使用活跃度 | 30% | 登录频率、功能使用深度 |
| 数据完整度 | 20% | 票据上传及时性、数据质量 |
| 服务满意度 | 20% | 客服评分、投诉记录 |
| 财务健康 | 20% | 付费及时性、续费意向 |
| 互动参与度 | 10% | 培训参与、反馈提交 |

### 1.2 评分计算
```python
def calculate_health_score(customer_id: str) -> dict:
    """计算客户健康度"""
    
    scores = {}
    
    # 1. 使用活跃度 (30%)
    login_freq = get_login_frequency(customer_id, days=30)
    feature_usage = get_feature_usage_depth(customer_id)
    scores['activity'] = min(100, (login_freq / 20) * 50 + feature_usage * 50)
    
    # 2. 数据完整度 (20%)
    bill_timeliness = get_bill_upload_timeliness(customer_id)
    data_quality = get_data_quality_score(customer_id)
    scores['data'] = (bill_timeliness + data_quality) / 2
    
    # 3. 服务满意度 (20%)
    support_rating = get_support_rating(customer_id)
    complaint_count = get_complaint_count(customer_id, days=90)
    scores['satisfaction'] = max(0, support_rating - complaint_count * 10)
    
    # 4. 财务健康 (20%)
    payment_on_time = get_payment_timeliness(customer_id)
    renewal_intent = get_renewal_intent(customer_id)
    scores['financial'] = (payment_on_time + renewal_intent) / 2
    
    # 5. 互动参与度 (10%)
    training_participation = get_training_participation(customer_id)
    feedback_submitted = get_feedback_count(customer_id, days=90)
    scores['engagement'] = min(100, training_participation * 60 + feedback_submitted * 10)
    
    # 加权总分
    weights = {
        'activity': 0.3,
        'data': 0.2,
        'satisfaction': 0.2,
        'financial': 0.2,
        'engagement': 0.1
    }
    
    total_score = sum(scores[k] * weights[k] for k in scores)
    
    return {
        'total_score': round(total_score, 1),
        'health_level': get_health_level(total_score),
        'dimensions': scores,
        'calculated_at': datetime.utcnow()
    }


def get_health_level(score: float) -> str:
    """获取健康等级"""
    if score >= 80:
        return "healthy"  # 健康 - 绿色
    elif score >= 60:
        return "at_risk"  # 风险 - 黄色
    else:
        return "critical"  # 危险 - 红色
```

## 2. 流失预警

```python
class ChurnPrediction:
    """流失预测"""
    
    def predict(self, customer_id: str) -> dict:
        """预测流失风险"""
        
        risk_factors = []
        risk_score = 0
        
        # 1. 登录频率下降
        recent_logins = get_login_count(customer_id, days=7)
        if recent_logins == 0:
            risk_factors.append("7天未登录")
            risk_score += 30
        elif recent_logins < 3:
            risk_factors.append("登录频率低")
            risk_score += 15
        
        # 2. 票据上传延迟
        last_bill = get_last_bill_upload(customer_id)
        if last_bill and (datetime.now() - last_bill).days > 15:
            risk_factors.append("票据上传延迟")
            risk_score += 20
        
        # 3. 客服投诉增加
        recent_complaints = get_complaint_count(customer_id, days=30)
        if recent_complaints >= 2:
            risk_factors.append("近期投诉较多")
            risk_score += 20
        
        # 4. 合同即将到期
        contract = get_active_contract(customer_id)
        if contract:
            days_to_expire = (contract.end_date - datetime.now().date()).days
            if days_to_expire <= 30:
                risk_factors.append("合同即将到期")
                risk_score += 25
        
        # 5. 系统功能使用减少
        feature_decline = check_feature_usage_decline(customer_id)
        if feature_decline:
            risk_factors.append("功能使用减少")
            risk_score += 15
        
        return {
            'risk_score': min(100, risk_score),
            'risk_level': 'high' if risk_score >= 60 else 'medium' if risk_score >= 30 else 'low',
            'risk_factors': risk_factors,
            'predicted_churn_probability': min(100, risk_score * 1.2)
        }


@celery.task
def churn_risk_monitor():
    """流失风险监控"""
    
    customers = db.query(Customer).filter(Customer.status == "active").all()
    
    for customer in customers:
        prediction = ChurnPrediction().predict(customer.id)
        
        if prediction['risk_level'] in ['high', 'medium']:
            # 创建预警
            alert = ChurnAlert(
                customer_id=customer.id,
                risk_score=prediction['risk_score'],
                risk_factors=prediction['risk_factors'],
                status="new"
            )
            db.add(alert)
            
            # 通知客户成功经理
            send_notification(
                user_id=customer.assigned_accountant_id,
                title=f"【流失预警】{customer.name}",
                content=f"流失风险: {prediction['risk_score']}分，因素: {', '.join(prediction['risk_factors'])}",
                type="warning"
            )
    
    db.commit()
```

## 3. 自动化运营

```python
class AutomatedPlaybook:
    """自动化运营剧本"""
    
    def run_onboarding(self, customer_id: str):
        """新客引导"""
        
        # Day 1: 欢迎邮件
        send_email(customer_id, "welcome")
        
        # Day 3: 功能引导（未上传票据）
        if not has_uploaded_bill(customer_id):
            send_in_app_message(customer_id, "引导上传票据")
        
        # Day 7: 培训邀请
        send_training_invite(customer_id)
        
        # Day 14: 满意度调查
        send_satisfaction_survey(customer_id)
    
    def run_retention(self, customer_id: str):
        """留存剧本"""
        
        # 检测到低活跃度
        if get_health_score(customer_id)['total_score'] < 60:
            # 发送关怀邮件
            send_email(customer_id, "关怀邮件")
            
            # 客户成功经理介入
            assign_csm(customer_id)
            
            # 提供专属培训
            offer_personal_training(customer_id)
    
    def run_expansion(self, customer_id: str):
        """扩容剧本"""
        
        # 检测到高健康度 + 使用量接近上限
        health = get_health_score(customer_id)
        usage = get_usage_stats(customer_id)
        
        if health['total_score'] > 80 and usage['approaching_limit']:
            # 推送升级优惠
            send_upgrade_offer(customer_id)
```

## 4. API接口

```
GET    /api/v1/customer-success/health-scores          # 健康度列表
GET    /api/v1/customer-success/health-scores/{id}    # 客户健康度
GET    /api/v1/customer-success/churn-alerts          # 流失预警
POST   /api/v1/customer-success/churn-alerts/{id}/resolve  # 处理预警
GET    /api/v1/customer-success/playbooks            # 运营剧本
POST   /api/v1/customer-success/playbooks/{id}/run   # 执行剧本
GET    /api/v1/customer-success/metrics              # 成功指标
```

## 5. 前端界面

```
┌─────────────────────────────────────────────────────────────────┐
│  客户成功                                                      │
├─────────────────────────────────────────────────────────────────┤
│  概览:                                                          │
│  健康客户: 50  风险客户: 10  危险客户: 5                        │
├─────────────────────────────────────────────────────────────────┤
│  流失预警:                                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ⚠️ XX科技有限公司                    风险分: 75   [处理]    ││
│  │    风险因素: 7天未登录, 合同即将到期                         ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ ⚠️ YY贸易有限公司                    风险分: 60   [处理]    ││
│  │    风险因素: 近期投诉较多                                      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  健康度趋势:                                                    │
│  [折线图展示近6个月健康度变化]                                  │
└─────────────────────────────────────────────────────────────────┘
```

================================================================================
                              验收标准
================================================================================

1. [ ] 健康度评分计算准确
2. [ ] 流失预警及时
3. [ ] 自动化剧本执行
4. [ ] 预警处理流程
5. [ ] 数据可视化展示
6. [ ] 通知提醒到达

================================================================================
                              开发提示
================================================================================

1. 评分模型持续优化
2. 预警阈值可配置
3. 人工介入与自动化结合
4. 客户反馈闭环
5. 保护客户隐私
