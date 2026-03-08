# 任务编号：TASK-INT-02
# 任务名称：税局电子税务局对接
# 优先级：P0
# 预估工期：3天
# 负责人：后端/前端

================================================================================
                              任务描述
================================================================================

实现与税务局电子税务局对接，支持发票查验、纳税申报、税费查询等功能。

================================================================================
                              需求详情
================================================================================

## 1. 数据模型

```python
class TaxAuth(Base):
    """税务授权信息"""
    __tablename__ = "tax_auths"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    tax_no = Column(String(20), nullable=False, comment="纳税人识别号")
    tax_area = Column(String(50), comment="税务地区")
    
    # 电子税务局账号
    etax_username = Column(String(50), comment="电子税务局账号")
    etax_password_encrypted = Column(Text, comment="密码(加密)")
    
    # 认证信息
    auth_status = Column(String(20), default="unauthorized")
    auth_token = Column(Text)
    auth_expires_at = Column(DateTime)
    
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaxDeclaration(Base):
    """纳税申报记录"""
    __tablename__ = "tax_declarations"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID, ForeignKey("customers.id"), nullable=False)
    
    period = Column(String(10), nullable=False, comment="申报期间")
    tax_type = Column(String(50), nullable=False, comment="税种")
    # 增值税/企业所得税/个人所得税/印花税等
    
    # 申报数据
    taxable_amount = Column(Numeric(15, 2), comment="应税金额")
    tax_amount = Column(Numeric(15, 2), comment="应纳税额")
    deduction_amount = Column(Numeric(15, 2), comment="抵扣金额")
    payable_amount = Column(Numeric(15, 2), comment="应缴金额")
    
    # 申报状态
    status = Column(String(20), default="draft", comment="draft/submitted/paid")
    declared_at = Column(DateTime, comment="申报时间")
    paid_at = Column(DateTime, comment="缴纳时间")
    
    # 电子税局回执
    receipt_no = Column(String(50), comment="申报回执号")
    receipt_url = Column(String(500), comment="回执文件URL")
```

## 2. 电子税务局接口

```python
class ETaxService:
    """电子税务局服务"""
    
    def __init__(self, tax_area: str):
        self.tax_area = tax_area
        self.base_url = self._get_tax_api_url(tax_area)
    
    def _get_tax_api_url(self, area: str) -> str:
        """获取各地税局API地址"""
        urls = {
            "北京": "https://etax.beijing.chinatax.gov.cn",
            "上海": "https://etax.shanghai.chinatax.gov.cn",
            "广东": "https://etax.guangdong.chinatax.gov.cn",
            # ...
        }
        return urls.get(area, urls["北京"])
    
    def login(self, tax_no: str, username: str, password: str) -> AuthResult:
        """登录电子税务局"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={
                "taxpayer_id": tax_no,
                "username": username,
                "password": password,
                "captcha": "..."  # 验证码处理
            }
        )
        return AuthResult(**response.json())
    
    def query_invoice(self, invoice_code: str, invoice_no: str, issue_date: str) -> InvoiceInfo:
        """发票查验"""
        response = requests.post(
            f"{self.base_url}/api/v1/invoice/query",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "invoice_code": invoice_code,
                "invoice_no": invoice_no,
                "issue_date": issue_date
            }
        )
        return InvoiceInfo(**response.json())
    
    def get_tax_data(self, tax_no: str, period: str, tax_type: str) -> TaxData:
        """获取税局数据（销项、进项）"""
        response = requests.get(
            f"{self.base_url}/api/v1/tax-data",
            headers={"Authorization": f"Bearer {self.token}"},
            params={
                "taxpayer_id": tax_no,
                "period": period,
                "tax_type": tax_type
            }
        )
        return TaxData(**response.json())
    
    def submit_declaration(self, declaration: TaxDeclaration) -> SubmitResult:
        """提交纳税申报"""
        response = requests.post(
            f"{self.base_url}/api/v1/declaration/submit",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "taxpayer_id": declaration.customer.tax_no,
                "period": declaration.period,
                "tax_type": declaration.tax_type,
                "taxable_amount": str(declaration.taxable_amount),
                "tax_amount": str(declaration.tax_amount),
                # ...
            }
        )
        return SubmitResult(**response.json())
```

## 3. 发票查验功能

```python
@app.post("/api/v1/invoices/verify")
def verify_invoice(data: InvoiceVerifyRequest):
    """发票查验"""
    
    # 1. 获取客户税务授权
    tax_auth = db.query(TaxAuth).filter(
        TaxAuth.customer_id == data.customer_id,
        TaxAuth.auth_status == "authorized"
    ).first()
    
    if not tax_auth:
        raise HTTPException(400, "客户未授权税务信息")
    
    # 2. 调用税局接口查验
    service = ETaxService(tax_auth.tax_area)
    service.token = tax_auth.auth_token
    
    try:
        invoice_info = service.query_invoice(
            data.invoice_code,
            data.invoice_no,
            data.issue_date
        )
        
        # 3. 与系统内票据对比
        bill = db.query(Bill).filter(
            Bill.invoice_code == data.invoice_code,
            Bill.invoice_number == data.invoice_no
        ).first()
        
        if bill:
            # 对比金额、税号等信息
            discrepancies = []
            if bill.total_amount != invoice_info.amount:
                discrepancies.append(f"金额不一致: 系统{bill.total_amount} vs 税局{invoice_info.amount}")
            
            return {
                "code": 200,
                "data": {
                    "invoice_status": "valid",  # valid/invalid/not_found
                    "invoice_info": invoice_info,
                    "system_bill": bill,
                    "discrepancies": discrepancies,
                    "is_consistent": len(discrepancies) == 0
                }
            }
        else:
            return {
                "code": 200,
                "data": {
                    "invoice_status": "valid",
                    "invoice_info": invoice_info,
                    "system_bill": None,
                    "message": "税局存在此发票，但系统未录入"
                }
            }
            
    except Exception as e:
        return {
            "code": 500,
            "message": f"查验失败: {str(e)}"
        }
```

## 4. 纳税申报功能

```python
@app.post("/api/v1/tax-declarations/generate")
def generate_tax_declaration(data: DeclarationGenerateRequest):
    """生成纳税申报表"""
    
    customer = db.query(Customer).get(data.customer_id)
    
    # 1. 获取账期内数据
    vouchers = db.query(Voucher).filter(
        Voucher.customer_id == data.customer_id,
        Voucher.period == data.period,
        Voucher.status == "approved"
    ).all()
    
    # 2. 根据税种计算
    if data.tax_type == "增值税":
        declaration = calculate_vat(customer, vouchers, data.period)
    elif data.tax_type == "企业所得税":
        declaration = calculate_income_tax(customer, vouchers, data.period)
    elif data.tax_type == "附加税":
        declaration = calculate_surtax(customer, vouchers, data.period)
    
    # 3. 保存申报表
    db.add(declaration)
    db.commit()
    
    return {"code": 200, "data": declaration}


def calculate_vat(customer, vouchers, period) -> TaxDeclaration:
    """计算增值税"""
    
    # 销项税额（收入相关凭证）
    output_vat = sum(
        item.tax_amount for voucher in vouchers
        for item in voucher.items
        if item.subject_code.startswith("22210101")  # 销项税额
    )
    
    # 进项税额（成本相关凭证）
    input_vat = sum(
        item.tax_amount for voucher in vouchers
        for item in voucher.items
        if item.subject_code.startswith("22210102")  # 进项税额
    )
    
    # 应缴增值税
    payable_vat = output_vat - input_vat
    
    return TaxDeclaration(
        customer_id=customer.id,
        period=period,
        tax_type="增值税",
        taxable_amount=sum(v.total_amount for v in vouchers),  # 简化计算
        tax_amount=payable_vat,
        deduction_amount=input_vat,
        payable_amount=payable_vat
    )
```

## 5. API 接口

```
POST   /api/v1/tax-auths                    # 添加税务授权
DELETE /api/v1/tax-auths/{id}              # 解除授权
POST   /api/v1/tax-auths/{id}/refresh      # 刷新授权

POST   /api/v1/invoices/verify             # 发票查验
POST   /api/v1/invoices/batch-verify       # 批量查验

POST   /api/v1/tax-declarations/generate   # 生成申报表
GET    /api/v1/tax-declarations            # 申报列表
POST   /api/v1/tax-declarations/{id}/submit # 提交申报
GET    /api/v1/tax-declarations/{id}/receipt # 获取回执

GET    /api/v1/tax-data/sales             # 销项数据
GET    /api/v1/tax-data/purchases         # 进项数据
```

## 6. 前端页面

```
┌─────────────────────────────────────────────────────────────────┐
│  税务管理                                                      │
├─────────────────────────────────────────────────────────────────┤
│  [税务授权] [发票查验] [纳税申报] [税费查询]                    │
├─────────────────────────────────────────────────────────────────┤
│  税务授权状态: ✅ 已授权 (北京市税务局)                         │
│  授权到期: 2024-12-31  [刷新授权]                              │
├─────────────────────────────────────────────────────────────────┤
│  发票查验:                                                      │
│  发票代码: [____________]  发票号码: [____________]             │
│  开票日期: [____________]  [查验]                              │
├─────────────────────────────────────────────────────────────────┤
│  纳税申报:                                                      │
│  期间: [2024年3月 ▼]  税种: [增值税 ▼]  [生成申报表]          │
│                                                                  │
│  应税金额: ¥100,000.00   销项税额: ¥13,000.00                  │
│  抵扣金额: ¥8,000.00     应缴税额: ¥5,000.00                   │
│                                                                  │
│  [预览申报表]  [提交申报]                                       │
└─────────────────────────────────────────────────────────────────┘
```

================================================================================
                              验收标准
================================================================================

1. [ ] 支持至少3个地区税局对接
2. [ ] 发票查验功能正常
3. [ ] 增值税申报表生成准确
4. [ ] 可提交申报至电子税务局
5. [ ] 申报回执可下载
6. [ ] 进项/销项数据自动获取
7. [ ] 申报数据与账务一致

================================================================================
                              开发提示
================================================================================

1. 电子税务局接口需要申请开发者资质
2. 使用RPA技术辅助（如官方API不完善）
3. 申报前务必提示用户核对数据
4. 敏感操作需要二次确认
5. 保存申报历史便于追溯
