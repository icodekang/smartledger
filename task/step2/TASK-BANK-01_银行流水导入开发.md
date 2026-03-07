# 任务编号：TASK-BANK-01
# 任务名称：银行流水导入开发
# 优先级：P0
# 预估工期：2天
# 负责人：后端开发

================================================================================
                              任务描述
================================================================================

开发银行流水导入功能的后端接口，支持从 CSV/Excel 文件导入银行交易记录。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

### 1.1 银行流水表 (bank_flows)
```python
class BankFlow(Base):
    __tablename__ = "bank_flows"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    # 交易信息
    transaction_date = Column(Date, nullable=False, comment="交易日期")
    transaction_time = Column(Time, nullable=True, comment="交易时间")
    
    # 金额（收入为正，支出为负）
    amount = Column(Numeric(15, 2), nullable=False, comment="交易金额")
    balance = Column(Numeric(15, 2), nullable=True, comment="账户余额")
    
    # 交易对手
    counterparty_name = Column(String(200), nullable=True, comment="对方户名")
    counterparty_account = Column(String(50), nullable=True, comment="对方账号")
    counterparty_bank = Column(String(100), nullable=True, comment="对方开户行")
    
    # 交易详情
    summary = Column(String(500), nullable=True, comment="摘要/用途")
    transaction_type = Column(String(50), nullable=True, comment="交易类型")
    transaction_channel = Column(String(50), nullable=True, comment="交易渠道")
    
    # 匹配状态
    match_status = Column(String(20), default="unmatched", comment="匹配状态: unmatched/matched/ignored")
    matched_bill_id = Column(UUID, ForeignKey("bills.id"), nullable=True)
    
    # 原始数据
    raw_data = Column(JSON, nullable=True, comment="原始行数据")
    source_file = Column(String(255), nullable=True, comment="源文件名")
    
    # 状态
    status = Column(String(20), default="active", comment="状态: active/deleted")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## 2. API 接口

### 2.1 上传并解析银行流水文件
```
POST /api/v1/bank-flows/upload
Content-Type: multipart/form-data

请求参数:
- file: File (CSV/Excel文件, 最大 10MB)
- bank_type: String (银行类型: icbc/ccb/abc/boc/comm 等，用于解析规则)
- account_id: String (可选，关联的账户ID)

响应:
{
  "code": 200,
  "message": "解析成功",
  "data": {
    "preview": [
      {
        "row_number": 1,
        "transaction_date": "2024-03-01",
        "amount": 15000.00,
        "counterparty_name": "XX科技有限公司",
        "summary": "货款",
        "balance": 125000.50
      }
    ],
    "total_count": 50,
    "date_range": {"start": "2024-03-01", "end": "2024-03-31"},
    "amount_summary": {"income": 100000, "expense": 50000}
  }
}
```

### 2.2 确认导入
```
POST /api/v1/bank-flows/import

请求体:
{
  "preview_token": "string",  // 上传时返回的临时token
  "selected_rows": [1, 2, 3], // 选择导入的行号，空数组表示全部
  "customer_id": "uuid"
}

响应:
{
  "code": 200,
  "message": "导入成功",
  "data": {
    "imported_count": 50,
    "skipped_count": 0,
    "import_id": "uuid"  // 用于查询导入批次
  }
}
```

### 2.3 获取银行流水列表
```
GET /api/v1/bank-flows?
  customer_id=uuid&
  start_date=2024-03-01&
  end_date=2024-03-31&
  match_status=unmatched&
  keyword=XX公司&
  page=1&
  page_size=20

响应:
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 100,
    "summary": {
      "total_income": 500000,
      "total_expense": 300000,
      "unmatched_count": 20
    }
  }
}
```

### 2.4 删除银行流水
```
DELETE /api/v1/bank-flows/{id}

响应: 标准响应格式
```

## 3. 文件解析规则

### 3.1 支持的银行格式

| 银行 | 文件格式 | 特征识别 |
|------|----------|----------|
| 工商银行 | CSV/Excel | 表头含"交易日期"、"收入"、"支出" |
| 建设银行 | Excel | 表头含"日期"、"贷方发生额"、"借方发生额" |
| 农业银行 | CSV | 表头含"交易时间"、"交易金额" |
| 中国银行 | Excel | 表头含"交易日期"、"交易金额"、"余额" |
| 交通银行 | CSV | 表头含"记账日期"、"交易金额" |
| 招商银行 | CSV | 表头含"交易日期"、"收入"、"支出" |

### 3.2 字段映射逻辑

```python
# 核心字段识别关键词
DATE_FIELDS = ['交易日期', '日期', '记账日期', '交易时间', 'Date']
AMOUNT_FIELDS = {
    'income': ['收入', '贷方发生额', '贷方金额', 'Income', 'Credit'],
    'expense': ['支出', '借方发生额', '借方金额', 'Expense', 'Debit'],
    'amount': ['交易金额', '金额', 'Amount']  # 带符号的金额
}
COUNTERPARTY_FIELDS = ['对方户名', '对方名称', '交易对手', 'Counterparty', '对方账号']
SUMMARY_FIELDS = ['摘要', '用途', '备注', '交易说明', 'Summary', 'Purpose']
BALANCE_FIELDS = ['余额', '账户余额', 'Balance']
```

### 3.3 数据清洗规则

1. **日期解析**
   - 支持格式: `2024-03-01`, `2024/03/01`, `01/03/2024`, `2024年03月01日`
   - 时间解析: `14:30:00`, `14:30`

2. **金额解析**
   - 去除千分位逗号
   - 处理括号表示负数: `(1000)` → `-1000`
   - 统一转为 Decimal 类型

3. **文本清洗**
   - 去除首尾空格
   - 去除多余空格
   - 限制字段长度

## 4. 去重逻辑

导入时自动检测重复记录（同一客户+日期+金额+对方户名），提示用户是否跳过。

```python
def check_duplicate(customer_id, transaction_date, amount, counterparty_name):
    """检查是否已存在相同记录"""
    existing = session.query(BankFlow).filter(
        BankFlow.customer_id == customer_id,
        BankFlow.transaction_date == transaction_date,
        BankFlow.amount == amount,
        BankFlow.counterparty_name == counterparty_name,
        BankFlow.status == "active"
    ).first()
    return existing is not None
```

## 5. 错误处理

| 错误码 | 场景 | 处理方式 |
|--------|------|----------|
| 4001 | 文件格式不支持 | 返回支持的格式列表 |
| 4002 | 文件内容为空 | 提示检查文件 |
| 4003 | 无法识别银行格式 | 返回手动映射界面 |
| 4004 | 日期格式无法解析 | 返回预览，标记错误行 |
| 4005 | 金额格式错误 | 返回预览，标记错误行 |

================================================================================
                              验收标准
================================================================================

1. [ ] 支持至少 5 种主流银行的 CSV/Excel 导入
2. [ ] 10MB 文件解析时间 < 5 秒
3. [ ] 预览功能正常，显示解析结果摘要
4. [ ] 重复数据检测准确
5. [ ] 错误行标记清晰，用户可单独选择导入
6. [ ] 单元测试覆盖率 > 80%

================================================================================
                              开发提示
================================================================================

1. 使用 pandas 读取 Excel/CSV
2. 使用 chardet 自动检测文件编码
3. 大文件使用流式处理，避免内存溢出
4. 预览阶段不实际写入数据库，使用 Redis 缓存预览数据
