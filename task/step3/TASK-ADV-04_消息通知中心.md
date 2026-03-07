# 任务编号：TASK-ADV-04
# 任务名称：消息通知中心
# 优先级：P1
# 预估工期：1.5天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发消息通知中心，支持邮件、短信、站内信、微信推送等多种通知渠道。

================================================================================
                              需求详情
================================================================================

## 1. 通知类型

| 类型 | 场景 | 渠道 | 优先级 |
|------|------|------|--------|
| 系统通知 | 操作成功/失败 | 站内信 | 低 |
| 任务提醒 | 待审核/待处理 | 站内信+邮件 | 中 |
| 安全提醒 | 登录异常/密码修改 | 站内信+邮件+短信 | 高 |
| 业务提醒 | 合同到期/结账提醒 | 站内信+邮件 | 中 |
| 营销通知 | 新功能/优惠活动 | 邮件 | 低 |

## 2. 数据模型

```python
class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # 接收人
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    
    # 通知内容
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(String(500), comment="摘要")
    
    # 类型
    type = Column(String(50), comment="类型: system/task/security/business/marketing")
    priority = Column(String(20), default="normal", comment="优先级: low/normal/high/urgent")
    
    # 渠道
    channels = Column(JSON, default=["in_app"], comment="发送渠道: [in_app, email, sms, wechat]")
    
    # 状态
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    # 链接
    link_type = Column(String(20), comment="链接类型: route/url")
    link_target = Column(String(500), comment="链接目标")
    
    # 发送状态
    sent_status = Column(JSON, default={}, comment="各渠道发送状态")
    # {"in_app": "sent", "email": "sent", "sms": "failed"}
    
    # 过期时间
    expires_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    
    # 各类型的通知设置
    system_enabled = Column(Boolean, default=True)
    system_channels = Column(JSON, default=["in_app"])
    
    task_enabled = Column(Boolean, default=True)
    task_channels = Column(JSON, default=["in_app", "email"])
    
    security_enabled = Column(Boolean, default=True)
    security_channels = Column(JSON, default=["in_app", "email", "sms"])
    
    business_enabled = Column(Boolean, default=True)
    business_channels = Column(JSON, default=["in_app", "email"])
    
    marketing_enabled = Column(Boolean, default=False)  # 默认关闭
    marketing_channels = Column(JSON, default=["email"])
```

## 3. 通知发送实现

```python
class NotificationService:
    """通知服务"""
    
    def __init__(self):
        self.channels = {
            "in_app": InAppChannel(),
            "email": EmailChannel(),
            "sms": SMSChannel(),
            "wechat": WechatChannel()
        }
    
    def send(self, notification: Notification):
        """发送通知"""
        
        for channel_name in notification.channels:
            channel = self.channels.get(channel_name)
            if channel:
                try:
                    channel.send(notification)
                    notification.sent_status[channel_name] = "sent"
                except Exception as e:
                    notification.sent_status[channel_name] = f"failed: {str(e)}"
        
        db.commit()


class EmailChannel:
    """邮件渠道"""
    
    def send(self, notification: Notification):
        user = db.query(User).get(notification.user_id)
        
        if not user.email:
            raise Exception("用户未设置邮箱")
        
        # 使用Jinja2模板渲染邮件
        template = get_template(f"emails/{notification.type}.html")
        html_content = template.render(
            title=notification.title,
            content=notification.content,
            link=notification.link_target
        )
        
        send_email(
            to=user.email,
            subject=notification.title,
            html=html_content
        )


class SMSChannel:
    """短信渠道"""
    
    def send(self, notification: Notification):
        user = db.query(User).get(notification.user_id)
        
        if not user.phone:
            raise Exception("用户未设置手机号")
        
        # 使用阿里云短信服务
        send_sms(
            phone=user.phone,
            template_code=get_sms_template(notification.type),
            params={
                "title": notification.title,
                "content": notification.content[:50]  # 短信内容限制
            }
        )


class InAppChannel:
    """站内信渠道"""
    
    def send(self, notification: Notification):
        # 保存到数据库（已保存）
        # 推送实时通知（WebSocket）
        websocket_manager.send_to_user(
            user_id=notification.user_id,
            message={
                "type": "notification",
                "data": {
                    "id": str(notification.id),
                    "title": notification.title,
                    "content": notification.content,
                    "link": notification.link_target
                }
            }
        )
```

## 4. 通知场景实现

```python
def notify_voucher_pending(voucher: Voucher):
    """通知有待审核凭证"""
    
    # 获取审核员
    auditors = db.query(User).filter(User.role == "auditor").all()
    
    for auditor in auditors:
        notification = Notification(
            user_id=auditor.id,
            title="有新的凭证待审核",
            content=f"客户 {voucher.customer.name} 的凭证 {voucher.voucher_no} 需要审核",
            type="task",
            priority="normal",
            channels=["in_app", "email"],
            link_type="route",
            link_target=f"/audit?voucher_id={voucher.id}"
        )
        db.add(notification)
        db.commit()
        
        # 发送
        notification_service.send(notification)


def notify_contract_expiring(contract: CustomerContract):
    """通知合同即将到期"""
    
    # 通知负责会计
    notification = Notification(
        user_id=contract.customer.assigned_accountant_id,
        title=f"【提醒】客户合同即将到期",
        content=f"客户 {contract.customer.name} 的合同将在 {contract.end_date} 到期，请及时跟进续签。",
        type="business",
        priority="high",
        channels=["in_app", "email"],
        link_type="route",
        link_target=f"/customers/{contract.customer.id}/contracts"
    )
    db.add(notification)
    db.commit()
    
    notification_service.send(notification)


def notify_security_alert(user: User, alert_type: str, details: dict):
    """安全提醒"""
    
    messages = {
        "login_from_new_device": "检测到新设备登录",
        "password_changed": "密码已修改",
        "multiple_failed_logins": "多次登录失败",
        "unusual_activity": "检测到异常操作"
    }
    
    notification = Notification(
        user_id=user.id,
        title=f"【安全提醒】{messages.get(alert_type, '安全提醒')}",
        content=f"您的账号发生了 {messages.get(alert_type)}，如非本人操作，请及时修改密码。",
        type="security",
        priority="urgent",
        channels=["in_app", "email", "sms"]
    )
    db.add(notification)
    db.commit()
    
    notification_service.send(notification)
```

## 5. WebSocket 实时推送

```python
# WebSocket 管理器
class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.connections:
            del self.connections[user_id]
    
    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.connections:
            await self.connections[user_id].send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.connections.values():
            await connection.send_json(message)

websocket_manager = WebSocketManager()

@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    # 验证token
    user = verify_token(token)
    
    await websocket_manager.connect(websocket, str(user.id))
    
    try:
        while True:
            # 保持连接
            data = await websocket.receive_text()
            # 处理心跳等
    except WebSocketDisconnect:
        websocket_manager.disconnect(str(user.id))
```

## 6. API 接口

```
GET    /api/v1/notifications            # 通知列表
GET    /api/v1/notifications/unread     # 未读通知
PUT    /api/v1/notifications/{id}/read  # 标记已读
PUT    /api/v1/notifications/read-all   # 全部已读
DELETE /api/v1/notifications/{id}       # 删除通知

GET    /api/v1/notification-preferences # 获取偏好设置
PUT    /api/v1/notification-preferences # 更新偏好设置
```

## 7. 前端通知中心

```
┌─────────────────────────────────────────────────────────────────┐
│  通知中心                                          [全部已读]    │
├─────────────────────────────────────────────────────────────────┤
│  [全部] [未读(3)] [系统] [任务] [安全]                          │
├─────────────────────────────────────────────────────────────────┤
│  ● 有新的凭证待审核                         10分钟前   [查看]  │
│    客户 XX科技 的凭证 PZ202403001 需要审核                      │
│                                                                  │
│  ○ 数据备份完成                             1小时前    [查看]  │
│                                                                  │
│  ● 【安全提醒】检测到新设备登录              2小时前   [查看]  │
│    您的账号在北京进行了登录，如非本人操作...                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

================================================================================
                              验收标准
================================================================================

1. [ ] 站内信发送/接收正常
2. [ ] 邮件发送正常
3. [ ] 短信发送正常
4. [ ] WebSocket实时推送正常
5. [ ] 通知偏好设置生效
6. [ ] 通知列表展示正常
7. [ ] 未读数实时更新
8. [ ] 不同类型通知区分展示

================================================================================
                              开发提示
================================================================================

1. 使用消息队列（如Redis）异步发送通知
2. 邮件模板使用HTML支持
3. 短信内容精简（70字限制）
4. 通知过多时分页加载
5. 支持批量操作（全部已读）
6. 夜间免打扰模式
