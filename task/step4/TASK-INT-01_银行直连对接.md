# 任务编号：TASK-INT-01
# 任务名称：银行直连对接
# 优先级：P0
# 预估工期：3天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

实现银行直连功能，通过银行开放API自动同步银行流水，支持工商银行、建设银行、招商银行等主流银行。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

### 1.1 银行账户表 (bank_accounts)
```python
class BankAccount(Base):
    __tablename__ = "bank_accounts"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    # 银行信息
    bank_code = Column(String(20), nullable=False, comment="银行代码")
    bank_name = Column(String(50), nullable=False, comment="银行名称")
    
    # 账户信息
    account_no = Column(String(50), nullable=False, comment="银行账号")
    account_name = Column(String(100), comment="账户名称")
    account_type = Column(String(20), default="basic", comment="基本户/一般户")
    
    # 银企直连接口配置
    api_type = Column(String(20), default="open", comment="open/sdk/direct")
    api_config = Column(JSON, comment="API配置参数")
    
    # 授权信息
    auth_status = Column(String(20), default="unauthorized", comment="授权状态")
    auth_token = Column(Text, comment="访问令牌")
    refresh_token = Column(Text, comment="刷新令牌")
    token_expires_at = Column(DateTime, comment="令牌过期时间")
    
    # 同步配置
    auto_sync = Column(Boolean, default=True, comment="自动同步")
    last_sync_at = Column(DateTime, comment="最后同步时间")
    sync_range_days = Column(Integer, default=30, comment="同步范围天数")
    
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 2. 银行接口抽象层

```python
class BankAPIInterface(ABC):
    """银行API接口抽象基类"""
    
    @abstractmethod
    def authenticate(self, credentials: dict) -> AuthResult:
        """用户授权认证"""
        pass
    
    @abstractmethod
    def query_balance(self, account_no: str) -> BalanceResult:
        """查询账户余额"""
        pass
    
    @abstractmethod
    def query_transactions(
        self, 
        account_no: str, 
        start_date: date, 
        end_date: date
    ) -> List[Transaction]:
        """查询交易流水"""
        pass
    
    @abstractmethod
    def refresh_token(self, refresh_token: str) -> AuthResult:
        """刷新访问令牌"""
        pass


# 工商银行实现
class ICBCAPI(BankAPIInterface):
    """工商银行API实现"""
    
    BASE_URL = "https://api.icbc.com.cn"
    
    def authenticate(self, credentials: dict) -> AuthResult:
        # 调用工行OAuth2接口
        response = requests.post(
            f"{self.BASE_URL}/oauth2/authorize",
            json={
                "app_id": credentials["app_id"],
                "app_secret": credentials["app_secret"],
                "grant_type": "authorization_code",
                "code": credentials["auth_code"]
            }
        )
        data = response.json()
        return AuthResult(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data["expires_in"]
        )
    
    def query_transactions(
        self, 
        account_no: str, 
        start_date: date, 
        end_date: date
    ) -> List[Transaction]:
        # 调用工行交易查询接口
        response = requests.post(
            f"{self.BASE_URL}/eic/transaction/query",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "acct_no": account_no,
                "start_date": start_date.strftime("%Y%m%d"),
                "end_date": end_date.strftime("%Y%m%d"),
                "query_type": "1"  # 明细查询
            }
        )
        
        transactions = []
        for item in response.json().get("transaction_list", []):
            transactions.append(Transaction(
                transaction_date=parse_date(item["trans_date"]),
                transaction_time=parse_time(item["trans_time"]),
                amount=Decimal(item["amount"]),
                balance=Decimal(item["balance"]),
                counterparty_name=item["opp_name"],
                counterparty_account=item["opp_acct_no"],
                summary=item["summary"],
                reference_no=item["serial_no"]
            ))
        
        return transactions


# 银行API工厂
class BankAPIFactory:
    """银行API工厂"""
    
    _apis = {
        "icbc": ICBCAPI,
        "ccb": CCBAPI,
        "cmb": CMBAPI,
        # ...
    }
    
    @classmethod
    def get_api(cls, bank_code: str) -> BankAPIInterface:
        api_class = cls._apis.get(bank_code)
        if not api_class:
            raise ValueError(f"不支持的银行: {bank_code}")
        return api_class()
```

## 3. API 接口

### 3.1 添加银行账户
```
POST /api/v1/bank-accounts

请求体:
{
  "customer_id": "uuid",
  "bank_code": "icbc",
  "account_no": "6222001234567890123",
  "account_name": "XX科技有限公司",
  "account_type": "basic"
}

响应:
{
  "code": 200,
  "data": {
    "id": "uuid",
    "auth_url": "https://api.icbc.com.cn/oauth2/authorize?...",
    "message": "请前往授权页面完成银行授权"
  }
}
```

### 3.2 银行授权回调
```
GET /api/v1/bank-accounts/{id}/auth-callback?code=xxx&state=xxx

说明：银行授权完成后回调此接口
```

### 3.3 同步银行流水
```
POST /api/v1/bank-accounts/{id}/sync

请求体:
{
  "start_date": "2024-03-01",
  "end_date": "2024-03-31"
}

响应:
{
  "code": 200,
  "data": {
    "synced_count": 50,
    "new_count": 10,
    "duplicate_count": 40
  }
}
```

### 3.4 自动同步配置
```
PUT /api/v1/bank-accounts/{id}/sync-config

请求体:
{
  "auto_sync": true,
  "sync_frequency": "daily",  // daily/hourly
  "sync_range_days": 7
}
```

## 4. 定时同步任务

```python
@celery.task
def auto_sync_bank_flows():
    """自动同步银行流水"""
    
    # 获取所有启用自动同步的账户
    accounts = db.query(BankAccount).filter(
        BankAccount.auto_sync == True,
        BankAccount.auth_status == "authorized",
        BankAccount.is_enabled == True
    ).all()
    
    for account in accounts:
        try:
            # 检查token是否过期
            if account.token_expires_at < datetime.utcnow():
                # 刷新token
                api = BankAPIFactory.get_api(account.bank_code)
                auth_result = api.refresh_token(account.refresh_token)
                account.auth_token = auth_result.access_token
                account.refresh_token = auth_result.refresh_token
                account.token_expires_at = datetime.utcnow() + timedelta(seconds=auth_result.expires_in)
            
            # 同步流水
            api = BankAPIFactory.get_api(account.bank_code)
            api.access_token = account.auth_token
            
            start_date = datetime.now().date() - timedelta(days=account.sync_range_days)
            end_date = datetime.now().date()
            
            transactions = api.query_transactions(
                account.account_no,
                start_date,
                end_date
            )
            
            # 保存到银行流水表
            for trans in transactions:
                # 检查是否已存在
                exists = db.query(BankFlow).filter(
                    BankFlow.bank_account_id == account.id,
                    BankFlow.reference_no == trans.reference_no
                ).first()
                
                if not exists:
                    flow = BankFlow(
                        customer_id=account.customer_id,
                        bank_account_id=account.id,
                        transaction_date=trans.transaction_date,
                        transaction_time=trans.transaction_time,
                        amount=trans.amount,
                        balance=trans.balance,
                        counterparty_name=trans.counterparty_name,
                        counterparty_account=trans.counterparty_account,
                        summary=trans.summary,
                        reference_no=trans.reference_no,
                        match_status="unmatched"
                    )
                    db.add(flow)
            
            account.last_sync_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            logger.error(f"同步银行流水失败: {account.id}, error: {e}")
            continue
```

## 5. 前端页面设计

### 5.1 银行账户管理
```
┌─────────────────────────────────────────────────────────────────┐
│  银行账户管理                                  [+ 添加账户]      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 工商银行                    尾号0123    基本户   [已授权]   ││
│  │ 上次同步: 2小时前   余额: ¥125,000.00   [同步] [设置] [删除]││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ 建设银行                    尾号5678    一般户   [已授权]   ││
│  │ 上次同步: 1天前     余额: ¥50,000.00    [同步] [设置] [删除]││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 添加银行账户流程
```
1. 选择银行 → 2. 输入账号 → 3. 跳转银行授权页面 → 4. 授权成功 → 5. 完成
```

================================================================================
                              验收标准
================================================================================

1. [ ] 支持工行、建行、招行至少3家银行
2. [ ] 银行OAuth授权流程正常
3. [ ] 流水同步数据准确
4. [ ] 自动同步定时执行
5. [ ] Token过期自动刷新
6. [ ] 重复流水自动去重
7. [ ] 同步失败告警通知

================================================================================
                              开发提示
================================================================================

1. 使用沙箱环境开发测试
2. 敏感信息加密存储
3. 流水同步使用事务保证一致性
4. 做好限流避免触发银行风控
5. 考虑使用聚合支付服务商（如连连、通联）简化对接
