# 任务编号：TASK-AI-TAX-01
# 任务名称：自动税务筹划
# 优先级：P0
# 预估工期：12天
# 负责人：后端/AI工程师/税务专家

================================================================================
                              任务描述
================================================================================

开发AI税务筹划系统，自动匹配适用的税收优惠政策，提供税负优化方案，辅助申报决策，帮助企业合规节税。

================================================================================
                              需求详情
================================================================================

## 1. 核心能力

### 1.1 优惠政策智能匹配
- 企业画像自动分析（行业、规模、资质、研发投入等）
- 政策库智能检索（国家/地方/行业政策）
- 适用性判断（AI判断是否满足政策条件）
- 节税金额测算（量化优惠政策价值）

### 1.2 税务筹划方案生成
- 业务场景筹划（采购、销售、投资等场景）
- 税负优化路径（不同方案税负对比）
- 最优方案推荐（综合考虑节税与风险）
- 实施步骤指导（具体操作指引）

### 1.3 申报智能辅助
- 申报数据智能复核（规则+AI检测异常）
- 优惠政策自动填报（符合条件的自动填写）
- 风险提示预警（申报前风险扫描）
- 历史申报分析（发现潜在问题）

### 1.4 税务知识服务
- 政策解读问答（自然语言询问政策）
- 实务操作指导（申报流程、材料准备）
- 新政推送（自动推送相关政策）

## 2. 数据模型

```python
class TaxPolicy(Base):
    """税收政策"""
    __tablename__ = "tax_policies"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # 基本信息
    policy_code = Column(String(50), unique=True, nullable=False)
    policy_name = Column(String(200), nullable=False)
    policy_type = Column(String(50))  # incentive/exemption/reduction/refund
    tax_category = Column(String(50))  # vat/income_tax/stamp_duty/etc
    
    # 政策来源
    issuing_authority = Column(String(100))  # 发文机关
    document_number = Column(String(100))     # 文号
    issue_date = Column(Date)
    effective_date = Column(Date)
    expiry_date = Column(Date, nullable=True)
    
    # 适用条件（结构化）
    applicable_conditions = Column(JSON)  # {
        # "industries": ["软件", "集成电路"],
        # "company_sizes": ["small", "micro"],
        # "qualifications": ["高新技术企业"],
        # "r_and_d_ratio": {"min": 0.03},
        # "employee_count": {"min": 100, "max": 500}
    # }
    
    # 优惠内容
    benefit_type = Column(String(50))  # rate_reduction/additional_deduction/exemption
    benefit_details = Column(JSON)  # {
        # "reduction_rate": 0.15,  # 减按15%
        # "additional_deduction_rate": 1.0,  # 加计扣除100%
        # "max_amount": 1000000
    # }
    
    # 政策原文
    original_text = Column(Text)
    summary = Column(Text)
    
    # 状态
    status = Column(String(20), default="active")  # active/expired/repealed
    
    # 向量嵌入（用于语义检索）
    embedding = Column(Vector(768))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TaxIncentiveMatch(Base):
    """税收优惠匹配结果"""
    __tablename__ = "tax_incentive_matches"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    policy_id = Column(UUID, ForeignKey("tax_policies.id"), nullable=False)
    
    # 匹配结果
    is_eligible = Column(Boolean, nullable=False)
    confidence = Column(Numeric(3, 2))  # AI判断置信度
    
    # 匹配详情
    matched_conditions = Column(JSON)  # 满足的条件
    unmet_conditions = Column(JSON)    # 未满足的条件
    missing_info = Column(JSON)        # 缺失的信息
    
    # 节税测算
    estimated_annual_savings = Column(Numeric(15, 2))
    calculation_basis = Column(Text)   # 计算依据说明
    
    # 状态
    status = Column(String(20), default="identified")  # identified/under_review/applied/enjoyed/rejected
    
    # 申请信息
    application_date = Column(DateTime)
    application_result = Column(String(50))
    actual_savings = Column(Numeric(15, 2))
    
    identified_at = Column(DateTime, default=datetime.utcnow)


class TaxPlan(Base):
    """税务筹划方案"""
    __tablename__ = "tax_plans"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    # 方案基本信息
    plan_name = Column(String(200), nullable=False)
    plan_type = Column(String(50))  # procurement/sales/investment/restructure
    scenario_description = Column(Text)  # 筹划场景描述
    
    # 方案详情
    options = Column(JSON)  # [{
        # "option_name": "方案A：分期采购",
        # "description": "...",
        # "tax_savings": 50000,
        # "implementation_cost": 2000,
        # "net_benefit": 48000,
        # "risk_level": "low",
        # "steps": [...]
    # }]
    
    recommended_option = Column(String(50))  # 推荐方案
    
    # 方案对比
    comparison_table = Column(JSON)
    
    # 风险提示
    risk_analysis = Column(Text)
    compliance_notes = Column(Text)
    
    # 状态
    status = Column(String(20), default="draft")  # draft/proposed/approved/implemented
    
    # 实施跟踪
    implemented_at = Column(DateTime)
    actual_savings = Column(Numeric(15, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)


class FilingReviewResult(Base):
    """申报复核结果"""
    __tablename__ = "tax_filing_reviews"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    # 申报信息
    tax_type = Column(String(50), nullable=False)  # vat/income_tax/etc
    period = Column(String(20), nullable=False)    # 2024-01
    
    # 复核结果
    overall_risk_level = Column(String(20))  # low/medium/high/critical
    
    # 发现的问题
    issues = Column(JSON)  # [{
        # "type": "amount_mismatch",
        # "severity": "high",
        # "description": "申报收入与账面收入差异5%",
        # "suggestion": "请核实..."
    # }]
    
    # 优惠政策检查
    incentives_check = Column(JSON)  # {
        # "applied_incentives": [...],
        # "missed_incentives": [...],
        # "potential_savings": 10000
    # }
    
    # 历史对比异常
    historical_anomalies = Column(JSON)
    
    # 处理状态
    review_status = Column(String(20), default="pending")  # pending/reviewed/confirmed/filing
    reviewer_notes = Column(Text)
    
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 3. 知识库设计

### 3.1 知识库架构

```yaml
税收政策知识库:
  结构化数据:
    - 政策基本信息（编码、名称、有效期等）
    - 适用条件（可计算的条件）
    - 优惠内容（可量化的优惠）
    - 申报要求
  
  非结构化数据:
    - 政策原文（存储在向量库）
    - 官方解读
    - 实务案例
    - FAQ
  
  知识图谱:
    - 实体: 政策、行业、税种、企业资质、地区
    - 关系: APPLIES_TO, REQUIRES, SUPERSEDES, RELATED_TO

企业画像维度:
  基础信息:
    - 行业分类（国标）
    - 企业规模（员工数、营收）
    - 注册地区
    - 成立时间
  
  资质认证:
    - 高新技术企业
    - 专精特新
    - 软件企业
    - 其他资质
  
  经营数据:
    - 研发投入占比
    - 研发费用金额
    - 软件收入占比
    - 进出口额
  
  历史税务:
    - 往年享受优惠
    - 税负率水平
    - 稽查记录
```

### 3.2 RAG检索设计

```python
class TaxPolicyRAG:
    """税收政策RAG系统"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.embedding_model = EmbeddingModel()
        self.reranker = Reranker()
    
    def search(self, query: str, filters: dict = None, top_k: int = 5) -> List[TaxPolicy]:
        """
        检索相关政策
        """
        # 1. 向量检索
        query_vector = self.embedding_model.encode(query)
        candidates = self.vector_store.similarity_search(
            vector=query_vector,
            filters=filters,  # 如：effective_date > now, status = active
            top_k=top_k * 2
        )
        
        # 2. 重排序
        reranked = self.reranker.rerank(query, candidates)
        
        return reranked[:top_k]
    
    def match_policies_for_company(self, company_profile: dict) -> List[TaxIncentiveMatch]:
        """
        为企业匹配适用政策
        """
        matches = []
        
        # 1. 基于规则快速筛选
        candidate_policies = self._rule_based_filter(company_profile)
        
        # 2. AI深度匹配
        for policy in candidate_policies:
            match = self._ai_assess_eligibility(company_profile, policy)
            matches.append(match)
        
        # 3. 按节税金额排序
        matches.sort(key=lambda x: x.estimated_annual_savings or 0, reverse=True)
        
        return matches
```

## 4. 核心实现

### 4.1 优惠政策匹配引擎

```python
class TaxIncentiveMatcher:
    """税收优惠匹配引擎"""
    
    def __init__(self):
        self.policy_kb = TaxPolicyKnowledgeBase()
        self.llm = LargeLanguageModel()
    
    async def match_incentives(self, customer_id: str) -> List[TaxIncentiveMatch]:
        """
        匹配适用的税收优惠政策
        """
        # 1. 获取企业画像
        company_profile = await self._get_company_profile(customer_id)
        
        # 2. 基于规则的快速筛选
        candidates = await self._rule_based_filter(company_profile)
        
        # 3. AI深度匹配
        matches = []
        for policy in candidates:
            match = await self._assess_eligibility(company_profile, policy)
            if match.is_eligible or match.confidence > 0.5:
                matches.append(match)
        
        # 4. 节税金额测算
        for match in matches:
            if match.is_eligible:
                match.estimated_annual_savings = await self._calculate_savings(
                    customer_id, match.policy_id
                )
        
        # 5. 按节税金额排序
        matches.sort(key=lambda x: x.estimated_annual_savings or 0, reverse=True)
        
        return matches
    
    async def _assess_eligibility(
        self, 
        company_profile: dict, 
        policy: TaxPolicy
    ) -> TaxIncentiveMatch:
        """
        AI判断政策适用性
        """
        conditions = policy.applicable_conditions
        
        matched = []
        unmet = []
        missing = []
        
        # 逐项检查条件
        for condition_key, condition_value in conditions.items():
            company_value = company_profile.get(condition_key)
            
            if company_value is None:
                missing.append({
                    "condition": condition_key,
                    "required": condition_value,
                    "note": "企业信息缺失"
                })
            elif self._check_condition(company_value, condition_value):
                matched.append({
                    "condition": condition_key,
                    "actual": company_value,
                    "required": condition_value
                })
            else:
                unmet.append({
                    "condition": condition_key,
                    "actual": company_value,
                    "required": condition_value
                })
        
        # 判断是否满足
        is_eligible = len(unmet) == 0 and len(missing) == 0
        
        # 计算置信度
        confidence = self._calc_confidence(matched, unmet, missing)
        
        return TaxIncentiveMatch(
            policy_id=policy.id,
            is_eligible=is_eligible,
            confidence=confidence,
            matched_conditions=matched,
            unmet_conditions=unmet,
            missing_info=missing
        )
    
    async def _calculate_savings(
        self, 
        customer_id: str, 
        policy_id: str
    ) -> Decimal:
        """
        测算节税金额
        """
        policy = await self.policy_kb.get_policy(policy_id)
        financial_data = await self._get_financial_data(customer_id)
        
        # 根据优惠类型计算
        if policy.benefit_type == "additional_deduction":
            # 加计扣除
            base_amount = financial_data.get("r_and_d_expenses", 0)
            deduction_rate = policy.benefit_details.get("additional_deduction_rate", 0)
            tax_rate = Decimal("0.25")  # 假设企业所得税率25%
            
            savings = base_amount * deduction_rate * tax_rate
            
        elif policy.benefit_type == "rate_reduction":
            # 税率减免
            taxable_income = financial_data.get("taxable_income", 0)
            normal_rate = Decimal("0.25")
            reduced_rate = policy.benefit_details.get("reduction_rate", Decimal("0.15"))
            
            savings = taxable_income * (normal_rate - reduced_rate)
            
        elif policy.benefit_type == "exemption":
            # 免征
            exempt_amount = financial_data.get("exemptable_revenue", 0)
            tax_rate = Decimal("0.06")  # 增值税率
            
            savings = exempt_amount * tax_rate
        
        return max(savings, 0)
```

### 4.2 税务筹划方案生成

```python
class TaxPlanningEngine:
    """税务筹划引擎"""
    
    def __init__(self):
        self.llm = LargeLanguageModel()
        self.calculator = TaxCalculator()
    
    async def generate_plan(
        self, 
        customer_id: str, 
        scenario: str,
        constraints: dict = None
    ) -> TaxPlan:
        """
        生成税务筹划方案
        """
        # 1. 收集信息
        context = await self._collect_context(customer_id, scenario)
        
        # 2. 生成备选方案（使用LLM）
        prompt = f"""
        作为资深税务筹划专家，请针对以下业务场景提供税务筹划方案：
        
        场景：{scenario}
        
        企业背景：
        {context}
        
        约束条件：
        {constraints}
        
        请提供2-3个不同的筹划方案，每个方案包括：
        1. 方案名称和描述
        2. 具体操作步骤
        3. 节税金额测算
        4. 实施成本
        5. 风险提示
        6. 合规性分析
        
        返回JSON格式。
        """
        
        llm_result = self.llm.generate(prompt, response_format="json")
        raw_options = json.loads(llm_result)
        
        # 3. 精确计算各方案节税金额
        options = []
        for opt in raw_options:
            precise_calc = await self.calculator.calculate(
                customer_id=customer_id,
                plan_description=opt["description"],
                steps=opt["steps"]
            )
            opt["tax_savings"] = precise_calc["tax_savings"]
            opt["implementation_cost"] = precise_calc["costs"]
            opt["net_benefit"] = opt["tax_savings"] - opt["implementation_cost"]
            options.append(opt)
        
        # 4. 推荐最优方案
        recommended = self._select_optimal(options)
        
        # 5. 生成对比表
        comparison = self._generate_comparison(options)
        
        # 6. 风险评估
        risk_analysis = self._assess_risks(options, context)
        
        return TaxPlan(
            customer_id=customer_id,
            plan_name=f"{scenario}税务筹划方案",
            plan_type=self._classify_scenario(scenario),
            scenario_description=scenario,
            options=options,
            recommended_option=recommended["option_name"],
            comparison_table=comparison,
            risk_analysis=risk_analysis,
            compliance_notes="本方案基于现行税法设计，建议在实施前咨询专业税务师"
        )
    
    async def _collect_context(self, customer_id: str, scenario: str) -> dict:
        """收集筹划所需信息"""
        return {
            "company_profile": await self._get_company_profile(customer_id),
            "financial_data": await self._get_recent_financial_data(customer_id, months=12),
            "tax_history": await self._get_tax_history(customer_id, years=2),
            "current_incentives": await self._get_current_incentives(customer_id),
            "business_plan": scenario
        }
```

### 4.3 申报智能复核

```python
class FilingReviewEngine:
    """申报复核引擎"""
    
    def __init__(self):
        self.rule_checker = RuleBasedChecker()
        self.ai_checker = AIChecker()
    
    async def review_filing(
        self, 
        customer_id: str, 
        tax_type: str, 
        period: str
    ) -> FilingReviewResult:
        """
        申报前智能复核
        """
        # 1. 获取申报数据
        filing_data = await self._get_filing_data(customer_id, tax_type, period)
        
        issues = []
        
        # 2. 规则检查
        rule_issues = self.rule_checker.check(filing_data, tax_type)
        issues.extend(rule_issues)
        
        # 3. AI异常检测
        ai_issues = await self.ai_checker.detect_anomalies(
            customer_id, tax_type, period, filing_data
        )
        issues.extend(ai_issues)
        
        # 4. 历史对比
        historical_issues = await self._compare_with_history(
            customer_id, tax_type, period, filing_data
        )
        issues.extend(historical_issues)
        
        # 5. 优惠政策检查
        incentives_check = await self._check_incentives(
            customer_id, tax_type, period, filing_data
        )
        
        # 6. 计算风险等级
        risk_level = self._calculate_risk_level(issues)
        
        return FilingReviewResult(
            customer_id=customer_id,
            tax_type=tax_type,
            period=period,
            overall_risk_level=risk_level,
            issues=issues,
            incentives_check=incentives_check
        )
    
    async def _check_incentives(
        self, 
        customer_id: str, 
        tax_type: str, 
        period: str,
        filing_data: dict
    ) -> dict:
        """检查优惠政策适用情况"""
        result = {
            "applied_incentives": [],
            "missed_incentives": [],
            "potential_savings": 0
        }
        
        # 获取已享受的优惠
        applied = filing_data.get("incentives_applied", [])
        result["applied_incentives"] = applied
        
        # 检查是否有遗漏的优惠
        matcher = TaxIncentiveMatcher()
        all_matches = await matcher.match_incentives(customer_id)
        
        for match in all_matches:
            if match.is_eligible:
                # 检查该优惠是否已申报
                if not any(a["policy_id"] == str(match.policy_id) for a in applied):
                    result["missed_incentives"].append({
                        "policy_id": str(match.policy_id),
                        "policy_name": match.policy_name,
                        "potential_savings": match.estimated_annual_savings
                    })
                    result["potential_savings"] += match.estimated_annual_savings or 0
        
        return result
```

## 5. 接口设计

### 5.1 匹配优惠政策

```http
GET /api/v1/ai/tax/incentives/match
Response:
{
    "matches": [
        {
            "policy_id": "pol_xxx",
            "policy_name": "研发费用加计扣除",
            "is_eligible": true,
            "confidence": 0.95,
            "estimated_annual_savings": 125000,
            "matched_conditions": [
                {"condition": "行业", "actual": "软件", "required": "非限制行业"},
                {"condition": "研发占比", "actual": "0.08", "required": ">=0.03"}
            ],
            "status": "identified"
        }
    ],
    "total_potential_savings": 245000
}
```

### 5.2 生成税务筹划方案

```http
POST /api/v1/ai/tax/planning
Request:
{
    "scenario": "计划采购一台价值50万元的生产设备",
    "constraints": {
        "budget": 500000,
        "timeline": "本季度内"
    }
}

Response:
{
    "plan_id": "plan_xxx",
    "plan_name": "设备采购税务筹划方案",
    "options": [
        {
            "option_name": "方案A：一次性扣除",
            "description": "选择一次性计入当期成本费用",
            "tax_savings": 125000,
            "implementation_cost": 0,
            "net_benefit": 125000,
            "risk_level": "low",
            "steps": [...]
        },
        {
            "option_name": "方案B：分期折旧",
            "description": "按5年折旧，每年扣除10万",
            ...
        }
    ],
    "recommended_option": "方案A",
    "comparison_table": {...},
    "risk_analysis": "..."
}
```

### 5.3 申报复核

```http
POST /api/v1/ai/tax/filing-review
Request:
{
    "tax_type": "vat",
    "period": "2024-01"
}

Response:
{
    "review_id": "rev_xxx",
    "overall_risk_level": "medium",
    "issues": [
        {
            "type": "amount_mismatch",
            "severity": "high",
            "description": "申报销售额与账面收入差异3.2%",
            "suggestion": "请核实是否有未开票收入未申报"
        }
    ],
    "incentives_check": {
        "applied": [...],
        "missed": [
            {
                "policy_name": "加计抵减",
                "potential_savings": 5000
            }
        ]
    }
}
```

## 6. 验收标准

- [ ] 政策匹配准确率 ≥ 90%
- [ ] 节税金额测算误差 ≤ 10%
- [ ] 支持100+条优惠政策
- [ ] 申报复核覆盖20+项检查点
- [ ] 筹划方案生成时间 ≤ 10秒
- [ ] 用户采纳建议率 ≥ 50%

================================================================================
                              任务依赖
================================================================================

- 依赖：TASK-AI-CHAT-01（问答能力）
- 依赖：税收政策知识库建设
- 依赖：税务专家参与知识整理

================================================================================
                              风险与应对
================================================================================

| 风险 | 影响 | 应对 |
|------|------|------|
| 政策更新不及时 | 高 | 建立政策更新机制，定期同步 |
| 节税测算不准确 | 高 | 财务专家校验，用户确认机制 |
| 政策适用争议 | 中 | 明确免责条款，建议专业咨询 |
