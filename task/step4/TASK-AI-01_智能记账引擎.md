# 任务编号：TASK-AI-01
# 任务名称：智能记账引擎
# 优先级：P0
# 预估工期：3天
# 负责人：后端

================================================================================
                              任务描述
================================================================================

开发AI智能记账引擎，实现自动科目匹配、智能分录生成、历史学习优化等功能。

================================================================================
                              需求详情
================================================================================

## 1. 核心能力

### 1.1 自动科目匹配
- 根据票据内容自动推荐会计科目
- 根据历史记账习惯学习优化
- 支持多维度匹配（金额、对方户名、商品名称等）

### 1.2 智能分录生成
- 自动识别业务场景
- 生成完整借贷分录
- 支持复杂业务（如工资、折旧、结转等）

## 2. 数据模型

```python
class AIModelConfig(Base):
    """AI模型配置"""
    __tablename__ = "ai_model_configs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"))
    
    # 学习数据
    training_data_count = Column(Integer, default=0)
    last_training_at = Column(DateTime)
    
    # 模型参数
    model_params = Column(JSON, default={})
    
    # 准确度统计
    accuracy_rate = Column(Numeric(5, 2), default=0)
    total_predictions = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)


class AISuggestion(Base):
    """AI建议记录"""
    __tablename__ = "ai_suggestions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    source_type = Column(String(50))  # bill/bank_flow
    source_id = Column(UUID)
    
    # AI建议
    suggested_subjects = Column(JSON)  # [{"code": "xxx", "name": "xxx", "confidence": 0.95}]
    suggested_entries = Column(JSON)   # 分录建议
    
    # 用户反馈
    user_accepted = Column(Boolean)
    user_modified = Column(Boolean)
    final_subjects = Column(JSON)
    
    # 模型信息
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 3. AI记账引擎实现

```python
class SmartBookingEngine:
    """智能记账引擎"""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.llm_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def analyze_bill(self, bill: Bill) -> BookingSuggestion:
        """分析票据并生成分录建议"""
        
        # 1. 构建提示词
        prompt = self._build_prompt(bill)
        
        # 2. 调用LLM
        response = self.llm_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        # 3. 解析结果
        result = json.loads(response.choices[0].message.content)
        
        # 4. 结合历史学习优化
        result = self._apply_learning(result, bill)
        
        return BookingSuggestion(**result)
    
    def _build_prompt(self, bill: Bill) -> str:
        """构建分析提示词"""
        
        # 获取客户科目体系
        subjects = self._get_customer_subjects()
        
        # 获取历史类似票据
        similar_bills = self._find_similar_bills(bill)
        
        prompt = f"""
请分析以下票据，生成会计分录：

【票据信息】
发票类型: {bill.invoice_type}
销售方: {bill.seller_name}
购买方: {bill.buyer_name}
金额: {bill.amount}
税额: {bill.tax_amount}
价税合计: {bill.total_amount}
商品名称: {bill.items[0].name if bill.items else 'N/A'}

【可用会计科目】
{json.dumps(subjects, ensure_ascii=False, indent=2)}

【历史参考】
{json.dumps([{
    "seller": b.seller_name,
    "amount": float(b.total_amount),
    "subject": b.vouchers[0].items[0].subject_code if b.vouchers else None
} for b in similar_bills[:5]], ensure_ascii=False)}

请输出JSON格式:
{{
    "business_type": "业务类型",
    "confidence": 0.95,
    "subjects": ["科目代码"],
    "entries": [
        {{"subject_code": "", "subject_name": "", "debit": 0, "credit": 0, "summary": ""}}
    ],
    "reasoning": "推理过程"
}}
"""
        return prompt
    
    def _get_system_prompt(self) -> str:
        """系统提示词"""
        return """你是一位专业的会计师，擅长根据票据信息生成准确的会计分录。

规则：
1. 借贷必相等
2. 根据业务实质选择科目
3. 增值税发票需分离税额
4. 费用类科目需按部门/项目辅助核算

输出必须是合法的JSON格式。"""
    
    def _apply_learning(self, result: dict, bill: Bill) -> dict:
        """应用历史学习优化结果"""
        
        # 查询历史相同销售方的记账习惯
        history = db.query(VoucherItem).join(Voucher).join(Bill).filter(
            Bill.customer_id == self.customer_id,
            Bill.seller_name == bill.seller_name,
            Voucher.status == "approved"
        ).all()
        
        if history:
            # 统计最常用科目
            subject_counts = {}
            for item in history:
                code = item.subject_code
                subject_counts[code] = subject_counts.get(code, 0) + 1
            
            most_common = max(subject_counts.items(), key=lambda x: x[1])
            
            # 如果AI建议与历史习惯不一致，但历史习惯置信度高，则调整
            if most_common[0] not in result["subjects"]:
                if most_common[1] / len(history) > 0.8:  # 80%以上使用同一科目
                    result["subjects"].append(most_common[0])
                    result["confidence"] = max(0.7, result["confidence"])
                    result["reasoning"] += f" (参考历史习惯，{most_common[1]}次使用{most_common[0]})"
        
        return result
    
    def learn_from_feedback(self, suggestion_id: str, accepted: bool, final_data: dict):
        """从用户反馈学习"""
        
        suggestion = db.query(AISuggestion).get(suggestion_id)
        suggestion.user_accepted = accepted
        suggestion.user_modified = (
            final_data != suggestion.suggested_entries
        )
        suggestion.final_subjects = final_data
        
        # 更新模型统计
        config = db.query(AIModelConfig).filter(
            AIModelConfig.customer_id == self.customer_id
        ).first()
        
        config.total_predictions += 1
        if accepted:
            config.correct_predictions += 1
        
        config.accuracy_rate = (
            config.correct_predictions / config.total_predictions * 100
        )
        
        db.commit()
        
        # 触发增量训练（可选）
        if config.total_predictions % 100 == 0:
            self._trigger_retraining()
```

## 4. 批量智能记账

```python
@app.post("/api/v1/ai/smart-booking")
def smart_booking(data: SmartBookingRequest):
    """智能记账"""
    
    engine = SmartBookingEngine(data.customer_id)
    results = []
    
    for bill_id in data.bill_ids:
        bill = db.query(Bill).get(bill_id)
        
        # AI分析
        suggestion = engine.analyze_bill(bill)
        
        # 保存建议
        ai_suggestion = AISuggestion(
            source_type="bill",
            source_id=bill.id,
            suggested_subjects=suggestion.subjects,
            suggested_entries=[e.dict() for e in suggestion.entries],
            model_version="v1.0"
        )
        db.add(ai_suggestion)
        
        results.append({
            "bill_id": bill_id,
            "suggestion_id": ai_suggestion.id,
            "confidence": suggestion.confidence,
            "entries": suggestion.entries,
            "reasoning": suggestion.reasoning
        })
    
    db.commit()
    
    return {"code": 200, "data": results}


@app.post("/api/v1/ai/suggestions/{id}/accept")
def accept_suggestion(suggestion_id: str):
    """接受AI建议，生成分录"""
    
    suggestion = db.query(AISuggestion).get(suggestion_id)
    bill = db.query(Bill).get(suggestion.source_id)
    
    # 生成凭证
    voucher = Voucher(
        customer_id=bill.customer_id,
        period=get_current_period(),
        voucher_no=generate_voucher_no(),
        voucher_date=datetime.now().date(),
        summary=f"AI生成 - {bill.seller_name}",
        source_type="ai",
        source_bill_id=bill.id,
        items=[]
    )
    
    for entry_data in suggestion.suggested_entries:
        item = VoucherItem(
            subject_code=entry_data["subject_code"],
            subject_name=entry_data["subject_name"],
            summary=entry_data["summary"],
            debit_amount=entry_data.get("debit"),
            credit_amount=entry_data.get("credit")
        )
        voucher.items.append(item)
    
    db.add(voucher)
    
    # 更新学习记录
    engine = SmartBookingEngine(bill.customer_id)
    engine.learn_from_feedback(
        suggestion_id,
        accepted=True,
        final_data=suggestion.suggested_entries
    )
    
    db.commit()
    
    return {"code": 200, "data": {"voucher_id": voucher.id}}
```

## 5. API 接口

```
POST   /api/v1/ai/analyze-bill          # 分析单张票据
POST   /api/v1/ai/smart-booking         # 批量智能记账
GET    /api/v1/ai/suggestions           # AI建议列表
POST   /api/v1/ai/suggestions/{id}/accept  # 接受建议
POST   /api/v1/ai/suggestions/{id}/reject  # 拒绝建议
GET    /api/v1/ai/model-stats           # AI模型统计
POST   /api/v1/ai/retrain               # 触发重新训练
```

## 6. 前端交互

```
┌─────────────────────────────────────────────────────────────────┐
│  AI智能记账                                                    │
├─────────────────────────────────────────────────────────────────┤
│  待记账票据 (50张)  [全选] [批量AI记账]                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ☑ 发票12345678    XX科技有限公司    ¥10,000.00             ││
│  │ AI建议: 借: 管理费用-办公费 贷: 银行存款                    ││
│  │ 置信度: 95%  [采纳] [修改] [忽略]                          ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ ☑ 发票12345679    YY贸易公司        ¥50,000.00             ││
│  │ AI建议: 借: 原材料 借: 进项税 贷: 应付账款                  ││
│  │ 置信度: 88%  [采纳] [修改] [忽略]                          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

================================================================================
                              验收标准
================================================================================

1. [ ] 票据自动科目匹配准确率>80%
2. [ ] 分录借贷平衡100%
3. [ ] 支持批量处理100+票据
4. [ ] 用户采纳率>70%
5. [ ] 模型持续学习优化
6. [ ] 处理速度<2秒/张

================================================================================
                              开发提示
================================================================================

1. 使用GPT-4/Claude等大模型API
2. 本地缓存常用科目减少API调用
3. 建立人工审核机制
4. 保留AI推理过程便于核对
5. 定期重训练提升准确率
