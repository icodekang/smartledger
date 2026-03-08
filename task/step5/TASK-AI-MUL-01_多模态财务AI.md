# 任务编号：TASK-AI-MUL-01
# 任务名称：多模态财务AI
# 优先级：P2
# 预估工期：8天
# 负责人：后端/AI工程师

================================================================================
                              任务描述
================================================================================

开发多模态财务AI能力，支持语音交互、图像识别（票据、合同）、文档解析（PDF、Excel）等多种输入方式，提升用户体验和操作效率。

================================================================================
                              需求详情
================================================================================

## 1. 核心能力

### 1.1 语音交互
- 语音记账（语音转记账分录）
- 语音查询（语音问财务数据）
- 语音审批（语音审批单据）
- 实时语音转写

### 1.2 图像识别
- 票据OCR（发票、收据、银行回单）
- 票据智能分类（自动识别票据类型）
- 票据真伪检测（防伪特征识别）
- 票据信息结构化（提取关键字段）

### 1.3 文档解析
- PDF财报解析（资产负债表、利润表）
- 银行对账单导入（自动解析流水）
- 合同关键信息提取（金额、日期、条款）
- Excel模板识别

### 1.4 智能生成
- 报表转图表（数据可视化）
- 语音播报（报表语音朗读）
- 智能摘要（长文档摘要）

## 2. 数据模型

```python
class VoiceInteraction(Base):
    """语音交互记录"""
    __tablename__ = "ai_voice_interactions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    
    # 音频信息
    audio_url = Column(String(500))
    audio_duration_ms = Column(Integer)
    
    # 识别结果
    recognized_text = Column(Text)
    recognition_confidence = Column(Numeric(5, 4))
    
    # 语义理解
    intent = Column(String(50))
    entities = Column(JSON)
    
    # 执行结果
    action_type = Column(String(50))  # bookkeeping/query/approval
    action_result = Column(JSON)
    
    # 反馈
    user_feedback = Column(String(20))  # correct/incorrect
    
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentParsing(Base):
    """文档解析记录"""
    __tablename__ = "ai_document_parsings"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    
    # 文档信息
    document_url = Column(String(500))
    document_type = Column(String(50))  # pdf/excel/image
    file_name = Column(String(255))
    file_size = Column(Integer)
    
    # 解析配置
    parse_type = Column(String(50))  # statement/report/contract/bill
    
    # 解析结果
    parsed_data = Column(JSON)
    extracted_tables = Column(JSON)
    confidence_score = Column(Numeric(5, 4))
    
    # 处理状态
    status = Column(String(20), default="processing")  # processing/completed/failed
    error_message = Column(Text)
    
    # 关联生成的数据
    generated_records = Column(JSON)  # 生成的记账凭证/银行流水等ID
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class ImageRecognition(Base):
    """图像识别记录"""
    __tablename__ = "ai_image_recognitions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    
    # 图片信息
    image_url = Column(String(500))
    image_type = Column(String(50))  # invoice/receipt/contract/bank_slip
    
    # OCR结果
    ocr_text = Column(Text)
    ocr_confidence = Column(Numeric(5, 4))
    
    # 结构化数据
    extracted_fields = Column(JSON)  # {
        # "invoice_code": "...",
        # "invoice_number": "...",
        # "amount": 1000.00,
        # "date": "2024-01-15",
        # "seller_name": "..."
    # }
    
    # 真伪检测
    authenticity_check = Column(JSON)  # {
        # "is_authentic": true,
        # "confidence": 0.98,
        # "checks": [...]
    # }
    
    # 票据查验
    verification_result = Column(JSON)  # 税局查验结果
    
    # 关联业务
    linked_transaction_id = Column(UUID)
    linked_voucher_id = Column(UUID)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│  输入层                                                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  语音    │ │  图像    │ │  PDF     │ │  Excel   │          │
│  │  (音频)  │ │  (票据)  │ │  (财报)  │ │  (对账单)│          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  预处理层                                                      │
│  - 音频：降噪、分割、格式转换                                  │
│  - 图像：校正、增强、去噪                                      │
│  - 文档：解析、提取、格式化                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  AI处理层                                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │
│  │  ASR         │ │  OCR         │ │  VLM         │          │
│  │  (语音识别)  │ │  (文字识别)  │ │  (多模态)    │          │
│  └──────────────┘ └──────────────┘ └──────────────┘          │
│  ┌──────────────┐ ┌──────────────┐                            │
│  │  NLP         │ │  Layout      │                            │
│  │  (语义理解)  │ │  (版面分析)  │                            │
│  └──────────────┘ └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  业务处理层                                                    │
│  - 记账凭证生成                                                │
│  - 银行流水导入                                                │
│  - 数据查询                                                    │
│  - 审批处理                                                    │
└─────────────────────────────────────────────────────────────────┘
```

## 4. 核心实现

### 4.1 语音记账

```python
class VoiceBookkeepingService:
    """语音记账服务"""
    
    def __init__(self):
        self.asr = ASRService()
        self.nlp = NLPEngine()
        self.booking_engine = BookingEngine()
    
    async def process_voice_booking(
        self, 
        audio_data: bytes,
        user_id: str,
        context: dict = None
    ) -> BookingResult:
        """
        处理语音记账请求
        """
        # 1. 语音识别
        asr_result = await self.asr.recognize(audio_data)
        text = asr_result["text"]
        confidence = asr_result["confidence"]
        
        if confidence < 0.7:
            return BookingResult(
                success=False,
                error="语音识别置信度低，请重新录制",
                recognized_text=text
            )
        
        # 2. 语义理解 - 提取记账要素
        booking_entities = await self.nlp.extract_booking_entities(text)
        
        # 3. 补全信息
        if context:
            booking_entities = self._enrich_with_context(booking_entities, context)
        
        # 4. 生成记账建议
        suggestion = await self.booking_engine.generate_suggestion(
            user_id=user_id,
            entities=booking_entities
        )
        
        # 5. 返回结果
        return BookingResult(
            success=True,
            recognized_text=text,
            extracted_entities=booking_entities,
            suggestion=suggestion,
            requires_confirmation=True  # 需要用户确认
        )
    
    async def extract_booking_entities(self, text: str) -> dict:
        """
        从文本中提取记账要素
        
        示例输入：
        "今天收入一万块货款，客户是ABC公司"
        
        示例输出：
        {
            "date": "2024-01-15",
            "type": "income",
            "amount": 10000.00,
            "currency": "CNY",
            "counterparty": "ABC公司",
            "category": "货款",
            "description": "货款收入"
        }
        """
        prompt = f"""
        从以下文本中提取记账要素，返回JSON格式：
        
        文本："{text}"
        
        需要提取的字段：
        - date: 日期（默认今天）
        - type: 类型（income/expense/transfer）
        - amount: 金额（数字）
        - currency: 币种（默认CNY）
        - counterparty: 交易对手（公司/个人名称）
        - category: 业务类别（如货款、差旅费、工资等）
        - description: 描述
        - payment_method: 支付方式（现金/银行/微信/支付宝）
        
        返回JSON，不确定的字段用null。
        """
        
        result = self.llm.generate(prompt, response_format="json")
        return json.loads(result)
```

### 4.2 票据OCR识别

```python
class BillOCRService:
    """票据OCR服务"""
    
    def __init__(self):
        self.ocr_engine = PaddleOCR()
        self.layout_analyzer = LayoutAnalyzer()
        self.field_extractor = FieldExtractor()
    
    async def recognize_bill(
        self, 
        image_data: bytes,
        bill_type_hint: str = None
    ) -> BillRecognitionResult:
        """
        识别票据
        """
        # 1. 图像预处理
        preprocessed_image = self._preprocess_image(image_data)
        
        # 2. OCR识别
        ocr_result = self.ocr_engine.ocr(preprocessed_image)
        raw_text = "\n".join([line[1][0] for line in ocr_result])
        
        # 3. 票据类型识别（如果未提供）
        if not bill_type_hint:
            bill_type = self._classify_bill_type(raw_text, ocr_result)
        else:
            bill_type = bill_type_hint
        
        # 4. 版面分析
        layout = self.layout_analyzer.analyze(ocr_result, bill_type)
        
        # 5. 字段提取
        fields = self.field_extractor.extract(
            ocr_result=ocr_result,
            layout=layout,
            bill_type=bill_type
        )
        
        # 6. 数据校验
        validation_result = self._validate_fields(fields, bill_type)
        
        # 7. 真伪检测（仅发票）
        authenticity = None
        if bill_type in ["vat_invoice", "general_invoice"]:
            authenticity = await self._check_authenticity(fields)
        
        return BillRecognitionResult(
            bill_type=bill_type,
            raw_text=raw_text,
            extracted_fields=fields,
            confidence=self._calc_confidence(ocr_result, validation_result),
            validation=validation_result,
            authenticity=authenticity
        )
    
    def _classify_bill_type(self, text: str, ocr_result: list) -> str:
        """分类票据类型"""
        text_lower = text.lower()
        
        # 关键词匹配
        if "增值税专用发票" in text or "增值税普通发票" in text:
            return "vat_invoice"
        elif "收据" in text:
            return "receipt"
        elif "银行" in text and ("回单" in text or "回执" in text):
            return "bank_slip"
        elif "出租车" in text or "行程单" in text:
            return "taxi_receipt"
        elif "火车票" in text or "铁路" in text:
            return "train_ticket"
        elif "飞机" in text or "航空" in text:
            return "flight_itinerary"
        else:
            return "general_invoice"
    
    async def _check_authenticity(self, fields: dict) -> dict:
        """
        票据真伪检测
        """
        checks = []
        
        # 1. 发票代码格式检查
        invoice_code = fields.get("invoice_code", "")
        if invoice_code:
            code_valid = len(invoice_code) == 10 or len(invoice_code) == 12
            checks.append({
                "check": "发票代码格式",
                "passed": code_valid,
                "detail": f"代码长度{len(invoice_code)}位"
            })
        
        # 2. 发票号码格式检查
        invoice_number = fields.get("invoice_number", "")
        if invoice_number:
            number_valid = len(invoice_number) == 8
            checks.append({
                "check": "发票号码格式",
                "passed": number_valid
            })
        
        # 3. 金额逻辑检查
        amount = fields.get("amount", 0)
        tax_amount = fields.get("tax_amount", 0)
        total_amount = fields.get("total_amount", 0)
        
        if amount and tax_amount and total_amount:
            amount_check = abs(amount + tax_amount - total_amount) < 0.01
            checks.append({
                "check": "金额逻辑",
                "passed": amount_check,
                "detail": f"{amount} + {tax_amount} = {total_amount}"
            })
        
        # 4. 税局查验（可选）
        verification_available = fields.get("invoice_code") and fields.get("invoice_number")
        
        all_passed = all(c["passed"] for c in checks)
        
        return {
            "is_authentic": all_passed,
            "confidence": sum(c["passed"] for c in checks) / len(checks),
            "checks": checks,
            "verification_available": verification_available
        }
```

### 4.3 银行对账单解析

```python
class BankStatementParser:
    """银行对账单解析器"""
    
    SUPPORTED_FORMATS = ["pdf", "excel", "csv", "ofx"]
    
    async def parse(
        self, 
        file_data: bytes,
        file_type: str,
        bank_hint: str = None
    ) -> StatementParseResult:
        """
        解析银行对账单
        """
        if file_type == "pdf":
            return await self._parse_pdf(file_data, bank_hint)
        elif file_type in ["xlsx", "xls"]:
            return await self._parse_excel(file_data, bank_hint)
        elif file_type == "csv":
            return await self._parse_csv(file_data, bank_hint)
        elif file_type == "ofx":
            return await self._parse_ofx(file_data)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    async def _parse_excel(
        self, 
        file_data: bytes,
        bank_hint: str
    ) -> StatementParseResult:
        """
        解析Excel对账单
        """
        import pandas as pd
        
        # 读取Excel
        df = pd.read_excel(BytesIO(file_data), sheet_name=0)
        
        # 识别银行（如果未提供）
        bank_name = bank_hint or self._identify_bank_from_excel(df)
        
        # 识别表头
        header_mapping = self._identify_headers(df, bank_name)
        
        # 提取交易记录
        transactions = []
        for idx, row in df.iterrows():
            # 跳过表头和空行
            if pd.isna(row[0]):
                continue
            
            # 提取字段
            trans = self._extract_transaction(row, header_mapping)
            if trans:
                transactions.append(trans)
        
        # 识别账户信息
        account_info = self._extract_account_info(df, bank_name)
        
        return StatementParseResult(
            bank_name=bank_name,
            account_info=account_info,
            transactions=transactions,
            period=self._detect_period(transactions),
            opening_balance=self._get_opening_balance(df),
            closing_balance=self._get_closing_balance(df),
            parsed_count=len(transactions)
        )
    
    def _identify_headers(self, df: pd.DataFrame, bank_name: str) -> dict:
        """
        识别Excel表头
        """
        # 获取第一行（可能是表头）
        first_row = df.iloc[0].astype(str).tolist()
        
        # 常见表头关键词映射
        header_keywords = {
            "date": ["日期", "交易日期", "记账日期", "Date", "Transaction Date"],
            "time": ["时间", "交易时间", "Time"],
            "description": ["摘要", "交易说明", "用途", "Description", "Notes", "Remark"],
            "counterparty": ["对方户名", "交易对手", "对方账户", "Counterparty", "Payee"],
            "income": ["收入", "借方", "存入", "Income", "Credit", "Deposit"],
            "expense": ["支出", "贷方", "取出", "Expense", "Debit", "Withdrawal"],
            "balance": ["余额", "账户余额", "Balance"],
            "reference": ["流水号", "交易号", "Reference", "Transaction ID"]
        }
        
        mapping = {}
        for col_idx, cell_value in enumerate(first_row):
            for field, keywords in header_keywords.items():
                if any(kw in str(cell_value) for kw in keywords):
                    mapping[field] = col_idx
                    break
        
        return mapping
    
    def _extract_transaction(self, row: pd.Series, header_mapping: dict) -> dict:
        """提取单笔交易"""
        try:
            return {
                "date": self._parse_date(row[header_mapping.get("date", 0)]),
                "time": row.get(header_mapping.get("time")),
                "description": str(row.get(header_mapping.get("description"), "")),
                "counterparty": str(row.get(header_mapping.get("counterparty"), "")),
                "income": self._parse_amount(row.get(header_mapping.get("income"))),
                "expense": self._parse_amount(row.get(header_mapping.get("expense"))),
                "balance": self._parse_amount(row.get(header_mapping.get("balance"))),
                "reference": str(row.get(header_mapping.get("reference"), ""))
            }
        except Exception as e:
            logger.warning(f"Failed to extract transaction: {e}")
            return None
```

### 4.4 合同信息提取

```python
class ContractParser:
    """合同信息提取器"""
    
    async def parse_contract(
        self, 
        pdf_data: bytes
    ) -> ContractParseResult:
        """
        解析合同，提取关键信息
        """
        # 1. PDF转文本
        text = await self._pdf_to_text(pdf_data)
        
        # 2. 使用LLM提取关键信息
        prompt = f"""
        从以下合同文本中提取关键信息，返回JSON格式：
        
        合同文本：
        {text[:8000]}  # 限制长度
        
        需要提取的字段：
        - contract_type: 合同类型（销售/采购/服务/租赁等）
        - contract_title: 合同标题
        - party_a: 甲方名称
        - party_b: 乙方名称
        - contract_amount: 合同金额（数字）
        - contract_currency: 币种（默认CNY）
        - start_date: 开始日期
        - end_date: 结束日期
        - payment_terms: 付款条款
        - payment_schedule: 付款计划（如有分期）
        - key_clauses: 关键条款摘要
        - termination_conditions: 终止条件
        - renewal_terms: 续约条款
        
        如果某些字段未找到，设为null。
        """
        
        result = self.llm.generate(prompt, response_format="json")
        extracted_info = json.loads(result)
        
        # 3. 金额校验
        if extracted_info.get("contract_amount"):
            # 从文本中搜索金额进行二次验证
            amount_in_text = self._extract_amount_from_text(text)
            if amount_in_text:
                extracted_info["amount_verified"] = abs(
                    extracted_info["contract_amount"] - amount_in_text
                ) < 0.01
        
        return ContractParseResult(
            extracted_info=extracted_info,
            full_text=text,
            confidence=self._calc_extraction_confidence(extracted_info)
        )
```

## 5. 接口设计

### 5.1 语音记账

```http
POST /api/v1/ai/voice/booking
Content-Type: multipart/form-data

Request:
{
    "audio": [音频文件],
    "context": {
        "customer_id": "cus_xxx",
        "default_date": "2024-01-15"
    }
}

Response:
{
    "recognized_text": "今天收入一万块货款，客户是ABC公司",
    "extracted_entities": {
        "date": "2024-01-15",
        "type": "income",
        "amount": 10000.00,
        "counterparty": "ABC公司",
        "category": "货款"
    },
    "suggestion": {
        "subject_code": "6001",
        "subject_name": "主营业务收入",
        "entries": [...]
    },
    "requires_confirmation": true
}
```

### 5.2 票据OCR

```http
POST /api/v1/ai/ocr/bill
Content-Type: multipart/form-data

Request:
{
    "image": [图片文件],
    "bill_type_hint": "vat_invoice"  // 可选
}

Response:
{
    "bill_type": "vat_invoice",
    "extracted_fields": {
        "invoice_code": "011001900211",
        "invoice_number": "12345678",
        "date": "2024-01-15",
        "amount": 10000.00,
        "tax_amount": 1300.00,
        "total_amount": 11300.00,
        "seller_name": "销售方公司",
        "buyer_name": "购买方公司"
    },
    "confidence": 0.95,
    "authenticity": {
        "is_authentic": true,
        "confidence": 0.98
    },
    "booking_suggestion": {
        "subject_code": "2202",
        "description": "应付账款-XX供应商"
    }
}
```

### 5.3 银行对账单导入

```http
POST /api/v1/ai/document/parse-statement
Content-Type: multipart/form-data

Request:
{
    "file": [Excel/PDF文件],
    "bank_hint": "工商银行",
    "account_id": "acc_xxx"  // 目标账户
}

Response:
{
    "parse_id": "par_xxx",
    "status": "completed",
    "bank_name": "工商银行",
    "account_info": {
        "account_number": "6222****1234",
        "account_name": "基本户"
    },
    "transactions": [
        {
            "date": "2024-01-15",
            "description": "货款",
            "counterparty": "ABC公司",
            "income": 50000.00,
            "expense": null,
            "balance": 150000.00
        }
    ],
    "summary": {
        "total_count": 45,
        "total_income": 200000.00,
        "total_expense": 150000.00,
        "new_transactions": 5  // 已去重
    },
    "preview_url": "/api/v1/ai/document/parse-statement/par_xxx/preview"
}
```

## 6. 前端交互

### 6.1 语音记账界面

```
┌─────────────────────────────────────────┐
│  🎤 语音记账                             │
├─────────────────────────────────────────┤
│                                         │
│     ┌─────────────────────────┐        │
│     │                         │        │
│     │    🎙️ 按住说话          │        │
│     │                         │        │
│     │   松开结束，上滑取消     │        │
│     │                         │        │
│     └─────────────────────────┘        │
│                                         │
│  识别结果：                              │
│  "今天收入一万块货款，客户是ABC公司"     │
│                                         │
│  解析：                                  │
│  📅 日期：2024-01-15                    │
│  💰 金额：10,000.00（收入）              │
│  👤 客户：ABC公司                        │
│  📝 类别：货款                           │
│                                         │
│  记账建议：                              │
│  借：银行存款 10,000                    │
│  贷：主营业务收入 8,849.56              │
│      应交税费-销项 1,150.44             │
│                                         │
│  [确认记账]  [修改]  [取消]              │
│                                         │
└─────────────────────────────────────────┘
```

### 6.2 票据拍照界面

```
┌─────────────────────────────────────────┐
│  📷 票据识别                             │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │                                 │   │
│  │     [相机取景框]                │   │
│  │                                 │   │
│  │  ┌─────────────────────────┐   │   │
│  │  │  将票据放入框内          │   │   │
│  │  │  自动识别                │   │   │
│  │  └─────────────────────────┘   │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  📁 从相册选择    ⚡ 自动连拍           │
│                                         │
│  最近识别：                              │
│  • 增值税专用发票 ¥11,300 ✅            │
│  • 出租车发票 ¥85 ✅                    │
│                                         │
└─────────────────────────────────────────┘
```

## 7. 性能要求

| 功能 | 目标响应时间 | 说明 |
|------|-------------|------|
| 语音识别 | ≤ 2秒 | 短语音（<10秒） |
| 票据OCR | ≤ 3秒 | 单张票据 |
| PDF解析 | ≤ 10秒 | 10页以内 |
| Excel解析 | ≤ 5秒 | 1000行以内 |

## 8. 验收标准

- [ ] 语音识别准确率 ≥ 95%（标准普通话）
- [ ] 票据OCR准确率 ≥ 90%（字段级）
- [ ] 支持10+种票据类型
- [ ] 银行对账单解析支持5+家银行
- [ ] 支持PDF/Excel/CSV对账单导入
- [ ] 用户满意度 ≥ 4.5/5

================================================================================
                              任务依赖
================================================================================

- 依赖：ASR服务（科大讯飞/百度/阿里云）
- 依赖：OCR服务（PaddleOCR/百度OCR）
- 依赖：LLM能力（用于语义理解）

================================================================================
                              风险与应对
================================================================================

| 风险 | 影响 | 应对 |
|------|------|------|
| 语音识别方言不准确 | 中 | 明确支持范围，提示使用普通话 |
| OCR识别率低 | 中 | 图像预处理优化，人工纠错机制 |
| 大文件解析超时 | 中 | 异步处理，进度反馈 |
