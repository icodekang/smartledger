# 任务编号：TASK-INT-04
# 任务名称：企业微信钉钉对接
# 优先级：P1
# 预估工期：2天
# 负责人：后端

================================================================================
                              任务描述
================================================================================

实现与企业微信、钉钉对接，支持组织架构同步、消息通知、单点登录、审批集成等功能。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

```python
class WorkPlatformIntegration(Base):
    """办公平台集成"""
    __tablename__ = "work_platform_integrations"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    platform_type = Column(String(20), nullable=False)  # wecom/dingtalk/feishu
    
    # 平台配置
    corp_id = Column(String(100), comment="企业ID")
    agent_id = Column(String(100), comment="应用ID")
    app_key = Column(String(100))
    app_secret = Column(Text)
    
    # 功能开关
    sync_org = Column(Boolean, default=True, comment="同步组织架构")
    sync_message = Column(Boolean, default=True, comment"消息通知")
    sso_enabled = Column(Boolean, default=False, comment="单点登录")
    
    # 同步状态
    last_sync_at = Column(DateTime)
    sync_status = Column(String(20), default="idle")
    
    is_enabled = Column(Boolean, default=True)
```

## 2. 企业微信对接

```python
class WeComAPI:
    """企业微信API"""
    
    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"
    
    def __init__(self, corp_id: str, corp_secret: str):
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.access_token = self._get_access_token()
    
    def _get_access_token(self) -> str:
        """获取access_token"""
        url = f"{self.BASE_URL}/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret
        }
        resp = requests.get(url, params=params).json()
        return resp["access_token"]
    
    def get_department_list(self) -> List[dict]:
        """获取部门列表"""
        url = f"{self.BASE_URL}/department/list"
        params = {"access_token": self.access_token}
        resp = requests.get(url, params=params).json()
        return resp.get("department", [])
    
    def get_user_list(self, department_id: int) -> List[dict]:
        """获取部门成员"""
        url = f"{self.BASE_URL}/user/simplelist"
        params = {
            "access_token": self.access_token,
            "department_id": department_id,
            "fetch_child": 1
        }
        resp = requests.get(url, params=params).json()
        return resp.get("userlist", [])
    
    def send_message(self, user_id: str, message: dict):
        """发送应用消息"""
        url = f"{self.BASE_URL}/message/send"
        params = {"access_token": self.access_token}
        
        data = {
            "touser": user_id,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {"content": message["content"]},
            "safe": 0
        }
        
        resp = requests.post(url, params=params, json=data).json()
        return resp["errcode"] == 0
```

## 3. 钉钉对接

```python
class DingTalkAPI:
    """钉钉API"""
    
    BASE_URL = "https://oapi.dingtalk.com"
    
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = self._get_access_token()
    
    def _get_access_token(self) -> str:
        """获取access_token"""
        url = f"{self.BASE_URL}/gettoken"
        params = {
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        resp = requests.get(url, params=params).json()
        return resp["access_token"]
    
    def get_department_list(self) -> List[dict]:
        """获取部门列表"""
        url = f"{self.BASE_URL}/department/list"
        params = {"access_token": self.access_token}
        resp = requests.get(url, params=params).json()
        return resp.get("department", [])
    
    def get_user_list(self, dept_id: int) -> List[dict]:
        """获取部门用户"""
        url = f"{self.BASE_URL}/user/list"
        params = {
            "access_token": self.access_token,
            "department_id": dept_id
        }
        resp = requests.get(url, params=params).json()
        return resp.get("userlist", [])
    
    def send_message(self, user_id: str, message: dict):
        """发送工作通知"""
        url = f"{self.BASE_URL}/topapi/message/corpconversation/asyncsend_v2"
        params = {"access_token": self.access_token}
        
        data = {
            "userid_list": user_id,
            "agent_id": self.agent_id,
            "msg": {
                "msgtype": "text",
                "text": {"content": message["content"]}
            }
        }
        
        resp = requests.post(url, params=params, json=data).json()
        return resp["errcode"] == 0
```

## 4. 组织架构同步

```python
@celery.task
def sync_organization(integration_id: str):
    """同步组织架构"""
    
    integration = db.query(WorkPlatformIntegration).get(integration_id)
    
    if integration.platform_type == "wecom":
        api = WeComAPI(integration.corp_id, integration.app_secret)
    elif integration.platform_type == "dingtalk":
        api = DingTalkAPI(integration.app_key, integration.app_secret)
    
    # 获取平台部门列表
    platform_depts = api.get_department_list()
    
    # 同步部门
    for dept in platform_depts:
        sync_department(integration.customer_id, dept)
        
        # 获取部门成员
        users = api.get_user_list(dept["id"])
        for user in users:
            sync_user(integration.customer_id, user, dept["id"])
    
    integration.last_sync_at = datetime.utcnow()
    integration.sync_status = "success"
    db.commit()


def sync_department(customer_id: str, dept_data: dict):
    """同步部门"""
    
    dept = db.query(Department).filter(
        Department.customer_id == customer_id,
        Department.platform_id == str(dept_data["id"])
    ).first()
    
    if not dept:
        dept = Department(
            customer_id=customer_id,
            platform_id=str(dept_data["id"])
        )
        db.add(dept)
    
    dept.name = dept_data["name"]
    dept.parent_id = str(dept_data.get("parentid", ""))
    dept.order = dept_data.get("order", 0)


def sync_user(customer_id: str, user_data: dict, dept_id: str):
    """同步用户"""
    
    # 查找或创建用户
    user = db.query(User).filter(
        User.customer_id == customer_id,
        User.platform_id == user_data["userid"]
    ).first()
    
    if not user:
        user = User(
            customer_id=customer_id,
            platform_id=user_data["userid"],
            username=user_data["userid"]
        )
        db.add(user)
    
    user.name = user_data.get("name", "")
    user.phone = user_data.get("mobile", "")
    user.email = user_data.get("email", "")
    user.department_id = dept_id
    user.avatar = user_data.get("avatar", "")
```

## 5. 单点登录

```python
@app.get("/api/v1/auth/wecom/callback")
def wecom_auth_callback(code: str, state: str):
    """企业微信OAuth回调"""
    
    # 获取用户信息
    api = WeComAPI(corp_id, corp_secret)
    user_info = api.get_user_info(code)
    
    # 查找系统用户
    user = db.query(User).filter(
        User.platform_id == user_info["UserId"]
    ).first()
    
    if not user:
        raise HTTPException(404, "用户未同步到系统")
    
    # 颁发token
    return {"token": create_token(user)}
```

## 6. 消息推送

```python
def send_work_message(user_id: str, title: str, content: str, url: str = None):
    """发送工作消息"""
    
    user = db.query(User).get(user_id)
    if not user or not user.platform_id:
        return False
    
    integration = db.query(WorkPlatformIntegration).filter(
        WorkPlatformIntegration.customer_id == user.customer_id,
        WorkPlatformIntegration.is_enabled == True
    ).first()
    
    if not integration:
        return False
    
    if integration.platform_type == "wecom":
        api = WeComAPI(integration.corp_id, integration.app_secret)
        message = {
            "title": title,
            "content": content,
            "url": url
        }
        return api.send_message(user.platform_id, message)
    
    elif integration.platform_type == "dingtalk":
        api = DingTalkAPI(integration.app_key, integration.app_secret)
        return api.send_message(user.platform_id, {"content": content})
```

## 7. API接口

```
POST   /api/v1/work-platforms                    # 创建集成
PUT    /api/v1/work-platforms/{id}              # 更新配置
DELETE /api/v1/work-platforms/{id}              # 删除集成
POST   /api/v1/work-platforms/{id}/test         # 测试连接
POST   /api/v1/work-platforms/{id}/sync         # 手动同步
GET    /api/v1/work-platforms/{id}/sync-logs    # 同步日志
```

================================================================================
                              验收标准
================================================================================

1. [ ] 企业微信对接正常
2. [ ] 钉钉对接正常
3. [ ] 组织架构同步准确
4. [ ] 消息推送到达
5. [ ] 单点登录可用
6. [ ] 同步日志完整

================================================================================
                              开发提示
================================================================================

1. 需要企业管理员授权
2. 通讯录同步需要相应权限
3. 注意用户隐私保护
4. 同步失败要有重试机制
5. 定期全量同步保持数据一致
