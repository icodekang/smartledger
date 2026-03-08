# 任务编号：TASK-OPEN-01
# 任务名称：开放API平台
# 优先级：P1
# 预估工期：2天
# 负责人：后端

================================================================================
                              任务描述
================================================================================

开发开放API平台，为第三方开发者提供标准API接口，支持应用注册、权限管理、流量控制等。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

```python
class OpenApp(Base):
    """开放应用"""
    __tablename__ = "open_apps"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # 应用信息
    app_name = Column(String(100), nullable=False)
    app_desc = Column(Text)
    app_icon = Column(String(500))
    
    # 开发者信息
    developer_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    developer_name = Column(String(100))
    developer_email = Column(String(100))
    
    # 凭证
    app_key = Column(String(32), unique=True, nullable=False)
    app_secret = Column(String(64), nullable=False)
    
    # 状态
    status = Column(String(20), default="pending")  # pending/active/suspended/rejected
    
    # 权限范围
    scopes = Column(JSON, default=[])  # ["read:bills", "write:vouchers"]
    
    # 限制
    rate_limit = Column(Integer, default=1000)  # 每小时请求数
    
    callback_url = Column(String(500))  # OAuth回调地址
    
    created_at = Column(DateTime, default=datetime.utcnow)


class OpenAccessToken(Base):
    """访问令牌"""
    __tablename__ = "open_access_tokens"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID, ForeignKey("open_apps.id"), nullable=False)
    
    # 授权信息
    customer_id = Column(UUID, ForeignKey("customers.id"))
    user_id = Column(UUID, ForeignKey("users.id"))
    
    access_token = Column(String(255), unique=True, nullable=False)
    refresh_token = Column(String(255), unique=True, nullable=False)
    
    expires_at = Column(DateTime, nullable=False)
    scope = Column(JSON, default=[])
    
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class OpenApiLog(Base):
    """API调用日志"""
    __tablename__ = "open_api_logs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID, ForeignKey("open_apps.id"))
    
    api_path = Column(String(200))
    method = Column(String(10))
    
    request_params = Column(JSON)
    response_code = Column(Integer)
    
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 2. 认证鉴权

```python
# API Key认证
def verify_app_key(app_key: str, app_secret: str) -> OpenApp:
    """验证应用凭证"""
    
    app = db.query(OpenApp).filter(
        OpenApp.app_key == app_key,
        OpenApp.status == "active"
    ).first()
    
    if not app:
        raise HTTPException(401, "Invalid app key")
    
    # 验证签名
    expected_secret = hashlib.sha256(
        f"{app_key}{app.app_secret}".encode()
    ).hexdigest()
    
    if not hmac.compare_digest(expected_secret, app_secret):
        raise HTTPException(401, "Invalid app secret")
    
    return app


# OAuth2授权码模式
@app.get("/oauth/authorize")
def oauth_authorize(
    response_type: str = "code",
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(...),
    state: str = Query(...)
):
    """OAuth授权页面"""
    
    # 验证应用
    app = db.query(OpenApp).filter(OpenApp.app_key == client_id).first()
    if not app or app.status != "active":
        raise HTTPException(400, "Invalid client_id")
    
    # 验证回调地址
    if redirect_uri != app.callback_url:
        raise HTTPException(400, "Invalid redirect_uri")
    
    # 显示授权页面（让用户确认授权）
    return HTMLResponse(f"""
    <html>
        <body>
            <h2>{app.app_name} 请求访问您的数据</h2>
            <p>权限范围: {scope}</p>
            <form method="post" action="/oauth/authorize">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="scope" value="{scope}">
                <input type="hidden" name="state" value="{state}">
                <button type="submit" name="action" value="allow">允许</button>
                <button type="submit" name="action" value="deny">拒绝</button>
            </form>
        </body>
    </html>
    """)


@app.post("/oauth/token")
def oauth_token(
    grant_type: str = Form(...),
    code: str = Form(None),
    refresh_token: str = Form(None),
    client_id: str = Form(...),
    client_secret: str = Form(...)
):
    """获取访问令牌"""
    
    app = verify_app_key(client_id, client_secret)
    
    if grant_type == "authorization_code":
        # 验证授权码
        auth_code = redis.get(f"oauth_code:{code}")
        if not auth_code:
            raise HTTPException(400, "Invalid or expired code")
        
        # 生成token
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        token = OpenAccessToken(
            app_id=app.id,
            customer_id=auth_code["customer_id"],
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(hours=2),
            scope=auth_code["scope"]
        )
        db.add(token)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 7200
        }
    
    elif grant_type == "refresh_token":
        # 刷新token
        old_token = db.query(OpenAccessToken).filter(
            OpenAccessToken.refresh_token == refresh_token,
            OpenAccessToken.is_revoked == False
        ).first()
        
        if not old_token:
            raise HTTPException(400, "Invalid refresh token")
        
        # 生成新token
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        old_token.is_revoked = True
        
        new_token = OpenAccessToken(
            app_id=old_token.app_id,
            customer_id=old_token.customer_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(hours=2),
            scope=old_token.scope
        )
        db.add(new_token)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 7200
        }
```

## 3. 限流控制

```python
class RateLimiter:
    """API限流器"""
    
    def __init__(self):
        self.redis = redis_client
    
    def is_allowed(self, app_id: str, limit: int = 1000, window: int = 3600) -> bool:
        """检查是否允许请求"""
        
        key = f"rate_limit:{app_id}:{datetime.now().hour}"
        current = self.redis.incr(key)
        
        if current == 1:
            self.redis.expire(key, window)
        
        return current <= limit
    
    def get_remaining(self, app_id: str, limit: int = 1000) -> int:
        """获取剩余配额"""
        key = f"rate_limit:{app_id}:{datetime.now().hour}"
        current = int(self.redis.get(key) or 0)
        return max(0, limit - current)


# 限流中间件
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 只限制开放API
    if not request.url.path.startswith("/open-api/"):
        return await call_next(request)
    
    # 获取应用信息
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        access_token = db.query(OpenAccessToken).filter(
            OpenAccessToken.access_token == token,
            OpenAccessToken.is_revoked == False
        ).first()
        
        if access_token:
            app = db.query(OpenApp).get(access_token.app_id)
            
            limiter = RateLimiter()
            if not limiter.is_allowed(str(app.id), app.rate_limit):
                return JSONResponse(
                    status_code=429,
                    content={"code": 429, "message": "Rate limit exceeded"}
                )
            
            # 设置剩余配额响应头
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(app.rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(
                limiter.get_remaining(str(app.id), app.rate_limit)
            )
            return response
    
    return await call_next(request)
```

## 4. 开放API列表

```
# 票据API
GET    /open-api/v1/bills              # 查询票据列表
GET    /open-api/v1/bills/{id}         # 获取票据详情
POST   /open-api/v1/bills              # 创建票据
PUT    /open-api/v1/bills/{id}         # 更新票据
DELETE /open-api/v1/bills/{id}         # 删除票据

# 凭证API
GET    /open-api/v1/vouchers           # 查询凭证列表
GET    /open-api/v1/vouchers/{id}      # 获取凭证详情
POST   /open-api/v1/vouchers           # 创建凭证

# 报表API
GET    /open-api/v1/reports/balance-sheet   # 资产负债表
GET    /open-api/v1/reports/income-statement # 利润表

# 客户API
GET    /open-api/v1/customers          # 查询客户列表
GET    /open-api/v1/customers/{id}     # 获取客户详情
```

## 5. 开发者文档

```markdown
# SmartLedger 开放API文档

## 快速开始

### 1. 注册应用
访问 [开发者中心](https://smartledger.ai/developer) 注册应用

### 2. 获取凭证
注册成功后获得 `app_key` 和 `app_secret`

### 3. 获取AccessToken
使用 OAuth2 授权码模式获取访问令牌

### 4. 调用API
在请求头中添加 `Authorization: Bearer {access_token}`

## API认证

### 方式一：API Key（服务器端）
```
Headers:
  X-App-Key: your_app_key
  X-App-Secret: your_app_secret
```

### 方式二：OAuth2（用户授权）
```
Headers:
  Authorization: Bearer {access_token}
```

## 错误码

| 代码 | 说明 |
|------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 认证失败 |
| 403 | 权限不足 |
| 429 | 请求过于频繁 |
| 500 | 服务器错误 |

## SDK下载

- [Java SDK](https://github.com/smartledger/java-sdk)
- [Python SDK](https://github.com/smartledger/python-sdk)
- [Node.js SDK](https://github.com/smartledger/nodejs-sdk)
```

================================================================================
                              验收标准
================================================================================

1. [ ] 应用注册审批流程正常
2. [ ] API Key认证可用
3. [ ] OAuth2授权流程正常
4. [ ] 限流控制生效
5. [ ] API文档完整
6. [ ] SDK示例可用
7. [ ] API调用日志记录

================================================================================
                              开发提示
================================================================================

1. API版本控制（v1/v2）
2. 向后兼容保证
3. 详细错误信息返回
4. SDK简化开发者接入
5. 定期API健康检查
