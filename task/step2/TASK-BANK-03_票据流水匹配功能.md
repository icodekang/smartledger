# 任务编号：TASK-BANK-03
# 任务名称：票据流水匹配功能
# 优先级：P0
# 预估工期：3天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

开发智能匹配算法，自动将银行流水与票据进行匹配，并提供人工干预界面。

================================================================================
                              功能需求
================================================================================

## 1. 自动匹配算法

### 1.1 匹配规则

```python
class FlowBillMatcher:
    """流水-票据匹配器"""
    
    def match(self, flow: BankFlow, bills: List[Bill]) -> List[MatchResult]:
        """
        匹配逻辑：
        1. 金额匹配（优先级最高）
        2. 日期范围匹配（±3天）
        3. 对方户名模糊匹配
        4. 综合计算匹配度分数
        """
        results = []
        
        for bill in bills:
            score = 0.0
            reasons = []
            
            # 1. 金额匹配 (权重 50%)
            amount_match = self._match_amount(flow.amount, bill.total_amount)
            score += amount_match.score * 0.5
            if amount_match.matched:
                reasons.append(f"金额匹配: {flow.amount}")
            
            # 2. 日期匹配 (权重 30%)
            date_match = self._match_date(
                flow.transaction_date, 
                bill.invoice_date,
                tolerance_days=3
            )
            score += date_match.score * 0.3
            if date_match.matched:
                reasons.append(f"日期相近: {date_match.diff_days}天")
            
            # 3. 对方户名匹配 (权重 20%)
            name_match = self._match_name(
                flow.counterparty_name,
                bill.seller_name
            )
            score += name_match.score * 0.2
            if name_match.matched:
                reasons.append(f"名称匹配: {name_match.similarity:.0%}")
            
            results.append(MatchResult(
                bill=bill,
                score=score,
                reasons=reasons,
                is_auto_match=score >= 0.85  # 自动匹配阈值
            ))
        
        return sorted(results, key=lambda x: x.score, reverse=True)
```

### 1.2 金额匹配逻辑

```python
def _match_amount(flow_amount: Decimal, bill_amount: Decimal) -> MatchScore:
    """
    金额匹配规则：
    - 完全一致: score=1.0
    - 误差 < 0.01元: score=0.95
    - 误差 < 1元: score=0.8
    - 误差 < 10元: score=0.6
    - 否则: score=0
    """
    diff = abs(abs(flow_amount) - abs(bill_amount))
    
    if diff == 0:
        return MatchScore(matched=True, score=1.0)
    elif diff < 0.01:
        return MatchScore(matched=True, score=0.95, diff=diff)
    elif diff < 1:
        return MatchScore(matched=True, score=0.8, diff=diff)
    elif diff < 10:
        return MatchScore(matched=True, score=0.6, diff=diff)
    else:
        return MatchScore(matched=False, score=0.0)
```

### 1.3 名称模糊匹配

```python
def _match_name(flow_name: str, bill_name: str) -> MatchScore:
    """
    使用编辑距离和Jaccard相似度综合计算
    """
    if not flow_name or not bill_name:
        return MatchScore(matched=False, score=0.0)
    
    # 清洗名称
    clean_flow = self._clean_company_name(flow_name)
    clean_bill = self._clean_company_name(bill_name)
    
    # 完全匹配
    if clean_flow == clean_bill:
        return MatchScore(matched=True, score=1.0, similarity=1.0)
    
    # 包含匹配
    if clean_flow in clean_bill or clean_bill in clean_flow:
        return MatchScore(matched=True, score=0.8, similarity=0.8)
    
    # 相似度计算
    similarity = self._calculate_similarity(clean_flow, clean_bill)
    
    if similarity >= 0.8:
        return MatchScore(matched=True, score=similarity * 0.7, similarity=similarity)
    else:
        return MatchScore(matched=False, score=similarity * 0.3, similarity=similarity)

def _clean_company_name(self, name: str) -> str:
    """清洗公司名称"""
    # 去除常见后缀
    suffixes = ['有限公司', '有限责任公司', '股份公司', '股份有限公司', '公司']
    for suffix in suffixes:
        name = name.replace(suffix, '')
    # 去除空格和特殊字符
    name = re.sub(r'[\s\(\)（）]', '', name)
    return name.lower()
```

## 2. 后端 API

### 2.1 获取匹配建议
```
GET /api/v1/bank-flows/{flow_id}/match-suggestions

响应:
{
  "code": 200,
  "data": {
    "auto_match": {  // 自动匹配结果（分数>0.85）
      "bill_id": "uuid",
      "bill_no": "发票号码",
      "score": 0.92,
      "reasons": ["金额匹配: 15000.00", "日期相近: 0天"]
    },
    "suggestions": [  // 其他候选
      {
        "bill_id": "uuid",
        "bill_no": "发票号码",
        "seller_name": "销售方名称",
        "amount": 15000.00,
        "invoice_date": "2024-03-01",
        "score": 0.75,
        "reasons": ["金额匹配", "名称相似度: 80%"]
      }
    ]
  }
}
```

### 2.2 确认匹配
```
POST /api/v1/bank-flows/{flow_id}/match

请求体:
{
  "bill_id": "uuid",
  "is_manual": true,  // 是否人工匹配
  "note": "匹配说明（可选）"
}

响应: 标准响应
```

### 2.3 取消匹配
```
POST /api/v1/bank-flows/{flow_id}/unmatch

响应: 标准响应
```

### 2.4 批量自动匹配
```
POST /api/v1/bank-flows/batch-match

请求体:
{
  "customer_id": "uuid",
  "date_range": {"start": "2024-03-01", "end": "2024-03-31"}
}

响应:
{
  "code": 200,
  "data": {
    "total_processed": 50,
    "auto_matched": 35,
    "need_manual": 15,
    "failed": 0
  }
}
```

## 3. 前端匹配界面

### 3.1 匹配对话框设计
```
┌─────────────────────────────────────────────────────────┐
│  匹配票据                                                  │
├─────────────────────────────────────────────────────────┤
│  当前流水:                                                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 日期: 2024-03-01          金额: ¥15,000.00      │   │
│  │ 对方: XX科技有限公司      摘要: 货款            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  系统推荐:                                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🎯 高置信度匹配 (92%)                            │   │
│  │ 发票: 12345678                                   │   │
│  │ 销售方: XX科技有限公司                           │   │
│  │ 金额: ¥15,000.00                                │   │
│  │                          [一键确认匹配]         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  其他候选票据:                                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │ □ 发票12345679 | XX贸易公司 | ¥15,000 | 匹配度75%│   │
│  │ □ 发票12345680 | XX科技公司 | ¥14,800 | 匹配度60%│   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  [手动选择票据]  [忽略此流水]  [取消]                     │
└─────────────────────────────────────────────────────────┘
```

### 3.2 匹配结果展示

在流水列表中，已匹配的行显示匹配信息：
- 绿色对勾图标
- 悬停显示匹配的发票号
- 点击可取消匹配

在票据列表中，已匹配的行显示：
- 关联的流水数量和金额
- 点击展开流水详情

## 4. 匹配工作流

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 导入流水     │────>│ 自动匹配     │────>│ 匹配成功?   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                          ┌────────────────────┼────────────────────┐
                          │ 是                 │ 否                 │
                          ▼                    ▼                    ▼
                   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
                   │ 自动关联     │      │ 多候选      │      │ 无匹配      │
                   │ 标记matched  │      │ 人工选择    │      │ 标记unmatched│
                   └─────────────┘      └─────────────┘      └─────────────┘
```

## 5. 数据模型更新

```python
# 新增匹配记录表（可选，用于审计）
class FlowBillMatch(Base):
    __tablename__ = "flow_bill_matches"
    
    id = Column(UUID, primary_key=True)
    bank_flow_id = Column(UUID, ForeignKey("bank_flows.id"))
    bill_id = Column(UUID, ForeignKey("bills.id"))
    match_score = Column(Numeric(3, 2))  # 匹配分数
    is_auto_match = Column(Boolean, default=False)  # 是否自动匹配
    matched_by = Column(UUID, ForeignKey("users.id"))  # 匹配人
    matched_at = Column(DateTime, default=datetime.utcnow)
    note = Column(String(500))
```

================================================================================
                              验收标准
================================================================================

1. [ ] 自动匹配准确率 > 80%（测试数据集）
2. [ ] 匹配算法响应时间 < 1秒（100条数据）
3. [ ] 匹配界面交互流畅，选择后实时更新状态
4. [ ] 支持一键确认自动匹配结果
5. [ ] 支持手动选择其他候选票据
6. [ ] 取消匹配后状态正确恢复
7. [ ] 批量自动匹配功能正常

================================================================================
                              开发提示
================================================================================

1. 使用 fuzzywuzzy 或 rapidfuzz 进行字符串相似度计算
2. 匹配算法需要单元测试，使用预设数据验证准确率
3. 考虑缓存匹配结果，避免重复计算
4. 前端使用 el-dialog 展示匹配对话框
5. 匹配结果使用 el-badge 在列表中标记
