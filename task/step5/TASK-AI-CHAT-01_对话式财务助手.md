# 任务编号：TASK-AI-CHAT-01
# 任务名称：对话式财务助手
# 优先级：P1
# 预估工期：10天
# 负责人：后端/AI工程师

================================================================================
                              任务描述
================================================================================

开发对话式财务AI助手，支持自然语言查询财务数据、财税知识问答、多轮对话交互，实现"零门槛"使用财务系统。

================================================================================
                              需求详情
================================================================================

## 1. 核心能力

### 1.1 自然语言数据查询
- 用大白话查询财务数据，如"上个月收入多少"、"Top10客户有哪些"
- 支持多轮追问，如"环比呢"、"按产品分一下"
- 自动理解时间范围、维度、筛选条件

### 1.2 财税知识问答
- 回答税收政策、会计准则、实务操作问题
- 基于RAG检索最新政策，避免知识过时
- 对不确定问题坦诚说明，不编造

### 1.3 多轮对话上下文
- 支持上下文理解，追问无需重复背景
- 对话状态管理，支持会话恢复
- 长对话保持连贯性

### 1.4 智能推荐
- 根据查询意图推荐相关问题
- 推荐下一步操作建议

## 2. 数据模型

```python
class ConversationSession(Base):
    """对话会话"""
    __tablename__ = "ai_conversation_sessions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    customer_id = Column(UUID, ForeignKey("customers.id"))
    
    title = Column(String(200))  # 会话标题（自动生成）
    status = Column(String(20), default="active")  # active/archived
    
    context_summary = Column(Text)  # 对话上下文摘要（用于恢复）
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime)


class ConversationMessage(Base):
    """对话消息"""
    __tablename__ = "ai_conversation_messages"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID, ForeignKey("ai_conversation_sessions.id"))
    
    role = Column(String(20), nullable=False)  # user/assistant/system
    content = Column(Text, nullable=False)
    
    # 元数据
    message_type = Column(String(50))  # text/query/knowledge/action
    intent = Column(String(50))  # 识别出的意图
    
    # 数据来源（如果是数据查询）
    source_sql = Column(Text)  # 生成的SQL
    source_data = Column(JSON)  # 查询结果
    
    # 性能指标
    response_time_ms = Column(Integer)
    token_usage = Column(JSON)  # {prompt_tokens, completion_tokens}
    
    created_at = Column(DateTime, default=datetime.utcnow)


class NL2SQLOptimization(Base):
    """NL2SQL优化记录（用于持续改进）"""
    __tablename__ = "ai_nl2sql_optimizations"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    natural_query = Column(Text, nullable=False)  # 自然语言查询
    generated_sql = Column(Text)  # 生成的SQL
    optimized_sql = Column(Text)  # 人工优化的SQL
    
    is_correct = Column(Boolean)  # 是否正确
    confidence = Column(Numeric(3, 2))  # 置信度
    
    feedback_type = Column(String(20))  # correct/wrong/needs_improvement
    feedback_comment = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│  API层                                                       │
│  POST /api/v1/ai/chat                     # 发送消息        │
│  GET  /api/v1/ai/chat/sessions            # 获取会话列表    │
│  GET  /api/v1/ai/chat/sessions/{id}       # 获取会话详情    │
│  DELETE /api/v1/ai/chat/sessions/{id}     # 删除会话        │
│  POST /api/v1/ai/chat/sessions/{id}/clear # 清空上下文      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  对话引擎 (ConversationalEngine)                            │
│  - 意图识别 (IntentClassifier)                              │
│  - 上下文管理 (ContextManager)                              │
│  - 回复生成 (ResponseGenerator)                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  NL2SQL模块   │    │  RAG知识库    │    │  Action模块   │
│  (数据查询)   │    │  (知识问答)   │    │  (操作执行)   │
└───────────────┘    └───────────────┘    └───────────────┘
```

## 4. 核心实现

### 4.1 意图识别

```python
class IntentClassifier:
    """意图分类器"""
    
    INTENTS = [
        "data_query",       # 数据查询：收入多少？
        "knowledge_qa",     # 知识问答：加计扣除是什么？
        "analysis_request", # 分析请求：分析一下利润下降原因
        "action_request",   # 操作请求：帮我生成凭证
        "comparison",       # 对比查询：和上月比如何？
        "clarification",    # 澄清追问：具体指哪个？
        "greeting",         # 问候：你好
        "other"             # 其他
    ]
    
    def classify(self, query: str, context: dict) -> IntentResult:
        """
        使用LLM进行意图分类
        """
        prompt = f"""
        分析用户输入的意图，从以下选项中选择：
        {self.INTENTS}
        
        对话上下文：{context}
        用户输入：{query}
        
        返回JSON格式：
        {{
            "intent": "意图类型",
            "confidence": 0.95,
            "entities": ["提取的实体"],
            "time_range": "时间范围",
            "metrics": ["涉及的指标"]
        }}
        """
        
        result = self.llm.generate(prompt, response_format="json")
        return IntentResult(**json.loads(result))
```

### 4.2 NL2SQL转换

```python
class NL2SQLConverter:
    """自然语言转SQL"""
    
    def __init__(self):
        self.schema_embedder = SchemaEmbedder()
        self.example_selector = ExampleSelector()
    
    def convert(
        self, 
        query: str, 
        context: dict, 
        schema: dict, 
        user_permissions: dict
    ) -> ConversionResult:
        """
        自然语言 → SQL
        """
        # 1. Schema Linking - 找出相关表和字段
        relevant_schema = self._schema_linking(query, schema)
        
        # 2. Few-shot示例选择
        examples = self.example_selector.select_similar(query, top_k=3)
        
        # 3. 构建Prompt
        prompt = self._build_prompt(
            query=query,
            schema=relevant_schema,
            examples=examples,
            dialect="postgresql"
        )
        
        # 4. LLM生成SQL
        sql = self.llm.generate(prompt)
        
        # 5. 安全校验
        safe_sql = self._validate_and_secure(sql, user_permissions)
        
        # 6. 置信度评估
        confidence = self._estimate_confidence(query, safe_sql)
        
        return ConversionResult(
            sql=safe_sql,
            confidence=confidence,
            explanation=self._explain_sql(safe_sql)
        )
    
    def _validate_and_secure(self, sql: str, user_permissions: dict) -> str:
        """SQL安全校验"""
        # 1. 只允许SELECT
        if not sql.strip().upper().startswith("SELECT"):
            raise SecurityError("只允许查询操作")
        
        # 2. 注入检测
        forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
        upper_sql = sql.upper()
        for keyword in forbidden_keywords:
            if keyword in upper_sql:
                raise SecurityError(f"检测到危险关键字: {keyword}")
        
        # 3. 权限过滤 - 自动添加customer_id过滤
        sql = self._inject_permission_filter(sql, user_permissions)
        
        # 4. 添加LIMIT
        if "LIMIT" not in sql.upper():
            sql += " LIMIT 1000"
        
        return sql
```

### 4.3 RAG知识库

```python
class FinancialRAG:
    """财务知识RAG系统"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_model = EmbeddingModel()
        self.reranker = Reranker()
    
    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """
        检索相关知识
        """
        # 1. Query理解优化
        optimized_query = self._optimize_query(query)
        
        # 2. 向量检索
        query_vector = self.embedding_model.encode(optimized_query)
        candidates = self.vector_store.similarity_search(
            vector=query_vector,
            top_k=top_k * 2  # 先检索更多，再重排序
        )
        
        # 3. 重排序
        reranked = self.reranker.rerank(
            query=optimized_query,
            documents=candidates
        )
        
        # 4. 返回TopK
        return reranked[:top_k]
    
    def generate_answer(self, query: str, documents: List[Document]) -> str:
        """
        基于检索结果生成回答
        """
        context = "\n\n".join([
            f"[文档{i+1}] {doc.title}\n{doc.content}"
            for i, doc in enumerate(documents)
        ])
        
        prompt = f"""
        基于以下参考资料，回答用户问题。
        如果参考资料不足以回答问题，请明确说明。
        
        参考资料：
        {context}
        
        用户问题：{query}
        
        回答要求：
        1. 准确、专业、简洁
        2. 如有政策时效性需注明
        3. 涉及金额计算需说明适用条件
        4. 必要时建议咨询专业人士
        """
        
        return self.llm.generate(prompt)
```

### 4.4 对话管理

```python
class ConversationalEngine:
    """对话引擎"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.nl2sql = NL2SQLConverter()
        self.rag = FinancialRAG()
        self.context_manager = ContextManager()
    
    async def process_message(
        self, 
        session_id: str, 
        user_message: str,
        user_id: str
    ) -> AssistantResponse:
        """
        处理用户消息
        """
        start_time = time.time()
        
        # 1. 获取上下文
        context = self.context_manager.get_context(session_id)
        
        # 2. 意图识别
        intent = self.intent_classifier.classify(user_message, context)
        
        # 3. 根据意图路由处理
        if intent.type == "data_query":
            response = await self._handle_data_query(
                user_message, context, user_id
            )
        elif intent.type == "knowledge_qa":
            response = await self._handle_knowledge_qa(user_message)
        elif intent.type == "analysis_request":
            response = await self._handle_analysis_request(
                user_message, context, user_id
            )
        elif intent.type == "comparison":
            response = await self._handle_comparison(
                user_message, context, user_id
            )
        else:
            response = await self._handle_general_chat(user_message, context)
        
        # 4. 保存消息记录
        await self._save_message(session_id, user_message, response)
        
        # 5. 更新上下文
        self.context_manager.update_context(session_id, user_message, response)
        
        response.response_time_ms = int((time.time() - start_time) * 1000)
        return response
    
    async def _handle_data_query(
        self, 
        query: str, 
        context: dict, 
        user_id: str
    ) -> AssistantResponse:
        """处理数据查询"""
        
        # 1. NL2SQL转换
        user_perms = self._get_user_permissions(user_id)
        schema = self._get_db_schema()
        
        conversion = self.nl2sql.convert(query, context, schema, user_perms)
        
        if conversion.confidence < 0.7:
            # 置信度低，请求澄清
            return AssistantResponse(
                content="请问您是想查询以下哪种情况？",
                suggestions=conversion.possible_interpretations,
                requires_clarification=True
            )
        
        # 2. 执行查询
        try:
            data = self._execute_query(conversion.sql)
        except Exception as e:
            return AssistantResponse(
                content=f"查询执行失败，请换一种方式提问。错误：{str(e)}",
                suggestions=["查看示例问题"]
            )
        
        # 3. 生成自然语言回复
        reply = self._generate_data_reply(query, data, conversion.sql)
        
        # 4. 推荐后续问题
        suggestions = self._suggest_followups(query, data)
        
        return AssistantResponse(
            content=reply,
            data=data,
            sql=conversion.sql,
            suggestions=suggestions
        )
```

## 5. 知识库设计

### 5.1 知识分类

```yaml
知识库分类:
  - 税收政策:
      - 增值税政策
      - 企业所得税政策
      - 个人所得税政策
      - 地方性税收优惠
      - 政策解读与实务
  
  - 会计准则:
      - 企业会计准则
      - 小企业会计准则
      - 准则解读与应用
      - 常见会计处理
  
  - 实务操作:
      - 记账规范
      - 报税流程
      - 发票管理
      - 银行对账
      - 期末处理
  
  - 系统使用:
      - 功能说明
      - 操作指南
      - 常见问题
      - 最佳实践
```

### 5.2 数据处理流程

```
原始文档
    ↓
文档解析（PDF/Word/HTML）
    ↓
文本清洗与格式化
    ↓
语义分块（Chunking）
    ↓
向量化（Embedding）
    ↓
存入向量数据库
    ↓
建立索引（可选：知识图谱关联）
```

## 6. 接口设计

### 6.1 发送消息

```http
POST /api/v1/ai/chat
Request:
{
    "session_id": "可选，不传则创建新会话",
    "message": "上个月收入多少",
    "context": {
        "customer_id": "当前查看的客户"
    }
}

Response:
{
    "session_id": "sess_xxx",
    "message_id": "msg_xxx",
    "content": "上个月收入为 1,234,567 元，较上月增长 15%...",
    "type": "data_response",
    "data": {
        "revenue": 1234567,
        "growth": 0.15
    },
    "sql": "SELECT SUM(amount) FROM...",
    "suggestions": [
        "环比数据如何？",
        "按产品分类看一下",
        "Top10客户有哪些"
    ],
    "response_time_ms": 1200
}
```

### 6.2 获取会话历史

```http
GET /api/v1/ai/chat/sessions/{session_id}
Response:
{
    "id": "sess_xxx",
    "title": "收入分析对话",
    "messages": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "created_at": "2024-01-15T10:00:00Z"
}
```

## 7. 前端交互设计

### 7.1 聊天界面

```
┌─────────────────────────────────────────┐
│  💬 智能财务助手                         │
├─────────────────────────────────────────┤
│                                         │
│  AI: 您好！我是您的财务助手，有什么可    │
│      以帮您的？                         │
│                                         │
│  我: 上个月收入多少？                   │
│                                         │
│  AI: 上月收入为 1,234,567 元            │
│      📈 环比增长 15%                    │
│      📊 同比增长 23%                    │
│      [查看详情] [下载报表]              │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 环比数据如何？               🔥 │   │
│  │ 按产品分类看一下                │   │
│  │ Top10客户有哪些                 │   │
│  └─────────────────────────────────┘   │
│                                         │
├─────────────────────────────────────────┤
│  🎤 [输入消息...]              [发送]   │
└─────────────────────────────────────────┘
```

### 7.2 消息类型

- **文本消息**：普通对话
- **数据卡片**：查询结果展示
- **图表消息**：可视化数据
- **操作按钮**：快速操作入口
- **来源标注**：显示数据来源

## 8. 性能要求

| 指标 | 目标 | 说明 |
|------|------|------|
| 首次响应 | ≤ 1.5秒 | 用户发送消息到首字出现 |
| 完整回复 | ≤ 3秒 | 完整响应生成时间 |
| 并发支持 | 100 QPS | 单实例支持 |
| 上下文长度 | 10轮 | 保持上下文理解的对话轮数 |

## 9. 安全与隐私

- **数据隔离**：只能查询授权范围内的数据
- **SQL注入防护**：严格的SQL生成和校验
- **敏感信息脱敏**：对话中涉及敏感数据自动脱敏
- **审计日志**：记录所有AI交互日志
- **内容安全**：过滤不当内容，合规审查

## 10. 验收标准

### 10.1 功能验收
- [ ] 支持50种以上常见财务查询意图
- [ ] NL2SQL准确率 ≥ 85%
- [ ] 知识问答准确率 ≥ 90%
- [ ] 多轮对话上下文保持正确

### 10.2 性能验收
- [ ] 平均响应时间 ≤ 3秒
- [ ] 支持100并发用户
- [ ] 系统稳定性99.9%

### 10.3 用户体验
- [ ] 用户满意度评分 ≥ 4.5/5
- [ ] 主动推荐采纳率 ≥ 40%

================================================================================
                              任务依赖
================================================================================

- 依赖：Step4 AI基础能力（已完成）
- 依赖：向量数据库部署
- 依赖：LLM API接入

================================================================================
                              风险与应对
================================================================================

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| NL2SQL准确率不达预期 | 高 | 准备规则兜底，人机协作审核 |
| LLM响应慢 | 中 | 流式输出，优先展示骨架 |
| 知识库覆盖不足 | 中 | 优先覆盖高频问题，持续迭代 |
| 用户隐私顾虑 | 中 | 本地化部署选项，数据加密 |
