# 任务编号：TASK-OPEN-02
# 任务名称：Webhook系统
# 优先级：P1
# 预估工期：1.5天
# 负责人：后端

================================================================================
                              任务描述
================================================================================

开发Webhook系统，支持事件推送机制，让第三方应用可以实时接收系统事件通知。

================================================================================
                              需求详情
================================================================================

## 1. 事件类型

| 事件 | 说明 | 触发时机 |
|------|------|----------|
| bill.created | 票据创建 | 上传票据后 |
| bill.processed | 票据处理完成 | OCR识别完成后 |
| voucher.created | 凭证创建 | 生成凭证后 |
| voucher.audited | 凭证审核 | 审核完成后 |
| customer.created | 客户创建 | 新客户添加 |
| payment.received | 收款到账 | 合同付款后 |

## 2. 数据模型

```python
class WebhookEndpoint(Base):
    """Webhook端点"""
    __tablename__ = "webhook_endpoints"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    app_id = Column(UUID, ForeignKey("open_apps.id"), nullable=False)
    
    url = Column(String(500), nullable=False)
    secret = Column(String(64))  # 签名密钥
    
    # 订阅事件
    events = Column(JSON, default=[])
    
    # 状态
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime)
    
    # 失败统计
    failure_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class WebhookDelivery(Base):
    """Webhook投递记录"""
    __tablename__ = "webhook_deliveries"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    endpoint_id = Column(UUID, ForeignKey("webhook_endpoints.id"))
    
    event_type = Column(String(50), nullable=False)
    event_id = Column(UUID, nullable=False)
    
    payload = Column(JSON)
    
    # 投递状态
    status = Column(String(20), default="pending")  # pending/success/failed
    http_status = Column(Integer)
    response_body = Column(Text)
    
    # 重试
    attempt_count = Column(Integer, default=0)
    next_attempt_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
```

## 3. Webhook触发

```python
class WebhookService:
    """Webhook服务"""
    
    def trigger_event(self, event_type: str, event_data: dict):
        """触发事件"""
        
        # 查找订阅该事件的端点
        endpoints = db.query(WebhookEndpoint).filter(
            WebhookEndpoint.events.contains([event_type]),
            WebhookEndpoint.is_active == True
        ).all()
        
        for endpoint in endpoints:
            # 创建投递记录
            delivery = WebhookDelivery(
                endpoint_id=endpoint.id,
                event_type=event_type,
                event_id=event_data.get("id"),
                payload=event_data
            )
            db.add(delivery)
            db.commit()
            
            # 异步投递
            deliver_webhook.delay(delivery.id)
    
    def construct_payload(self, event_type: str, data: dict) -> dict:
        """构造Webhook负载"""
        
        return {
            "id": str(uuid.uuid4()),
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
    
    def generate_signature(self, payload: str, secret: str) -> str:
        """生成签名"""
        import hmac
        import hashlib
        
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"


@celery.task
def deliver_webhook(delivery_id: str):
    """投递Webhook"""
    
    delivery = db.query(WebhookDelivery).get(delivery_id)
    endpoint = db.query(WebhookEndpoint).get(delivery.endpoint_id)
    
    try:
        # 构造请求
        payload = json.dumps(delivery.payload, default=str)
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-ID": str(delivery.id),
            "X-Event-Type": delivery.event_type
        }
        
        # 添加签名
        if endpoint.secret:
            headers["X-Signature"] = WebhookService().generate_signature(
                payload, endpoint.secret
            )
        
        # 发送
        response = requests.post(
            endpoint.url,
            data=payload,
            headers=headers,
            timeout=30
        )
        
        # 记录结果
        delivery.http_status = response.status_code
        delivery.response_body = response.text[:1000]  # 限制长度
        
        if response.status_code == 200:
            delivery.status = "success"
            delivery.completed_at = datetime.utcnow()
            endpoint.failure_count = 0
        else:
            delivery.status = "failed"
            handle_failed_delivery(delivery)
        
    except Exception as e:
        delivery.status = "failed"
        delivery.response_body = str(e)[:1000]
        handle_failed_delivery(delivery)
    
    db.commit()


def handle_failed_delivery(delivery: WebhookDelivery):
    """处理失败的投递"""
    
    endpoint = db.query(WebhookEndpoint).get(delivery.endpoint_id)
    endpoint.failure_count += 1
    
    # 重试策略：指数退避
    if delivery.attempt_count < 5:
        delivery.attempt_count += 1
        delay = 2 ** delivery.attempt_count  # 2, 4, 8, 16, 32秒
        delivery.next_attempt_at = datetime.utcnow() + timedelta(seconds=delay)
        
        # 安排重试
        deliver_webhook.apply_async(
            args=[delivery.id],
            countdown=delay
        )
    else:
        # 超过重试次数，暂停端点
        if endpoint.failure_count >= 10:
            endpoint.is_active = False
            endpoint.last_error = "连续投递失败，端点已暂停"
```

## 4. API接口

```
POST   /api/v1/webhooks/endpoints         # 创建端点
GET    /api/v1/webhooks/endpoints         # 端点列表
PUT    /api/v1/webhooks/endpoints/{id}    # 更新端点
DELETE /api/v1/webhooks/endpoints/{id}    # 删除端点

GET    /api/v1/webhooks/deliveries        # 投递记录
POST   /api/v1/webhooks/{id}/test         # 测试端点
POST   /api/v1/webhooks/{id}/replay/{delivery_id}  # 重发
```

## 5. 开发者文档

```markdown
# Webhook集成指南

## 配置Webhook

1. 在开发者中心创建Webhook端点
2. 配置接收URL和订阅事件
3. 保存生成的Secret用于签名验证

## 接收Webhook

### 请求格式
```
POST https://your-domain.com/webhook
Content-Type: application/json
X-Webhook-ID: uuid
X-Event-Type: bill.created
X-Signature: sha256=xxx

{
  "id": "uuid",
  "event": "bill.created",
  "timestamp": "2024-03-07T10:00:00Z",
  "data": {
    "bill_id": "uuid",
    "customer_id": "uuid",
    "amount": 10000.00
  }
}
```

### 签名验证
```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### 响应要求
- 返回200状态码表示成功
- 5秒内响应，否则视为失败
- 失败将触发重试机制
```

================================================================================
                              验收标准
================================================================================

1. [ ] 事件触发正常
2. [ ] Webhook投递成功
3. [ ] 签名验证可用
4. [ ] 重试机制正常
5. [ ] 投递记录完整
6. [ ] 连续失败自动暂停

================================================================================
                              开发提示
================================================================================

1. 投递使用异步任务
2. 做好超时控制
3. 保护接收方服务器（限流）
4. 提供测试工具
5. 支持批量重发
