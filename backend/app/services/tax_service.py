"""
电子税务局服务
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import random
import uuid


@dataclass
class InvoiceVerifyResult:
    """发票查验结果"""
    invoice_code: str
    invoice_number: str
    issue_date: str
    seller_name: str
    seller_tax_no: str
    buyer_name: str
    buyer_tax_no: str
    amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str  # valid/invalid


@dataclass
class TaxData:
    """税务数据"""
    period: str
    tax_type: str
    sales_amount: Decimal  # 销项金额
    sales_tax: Decimal     # 销项税额
    purchase_amount: Decimal  # 进项金额
    purchase_tax: Decimal     # 进项税额
    payable_tax: Decimal      # 应缴税额


class ETaxService:
    """电子税务局服务"""
    
    # 各地税局API地址（模拟）
    API_URLS = {
        "北京": "https://etax.beijing.chinatax.gov.cn",
        "上海": "https://etax.shanghai.chinatax.gov.cn",
        "广东": "https://etax.guangdong.chinatax.gov.cn",
        "深圳": "https://etax.shenzhen.chinatax.gov.cn",
        "浙江": "https://etax.zhejiang.chinatax.gov.cn",
        "江苏": "https://etax.jiangsu.chinatax.gov.cn",
    }
    
    def __init__(self, tax_area: str = "北京"):
        self.tax_area = tax_area
        self.base_url = self.API_URLS.get(tax_area, self.API_URLS["北京"])
        self.token = None
    
    def login(self, tax_no: str, username: str, password: str) -> Dict:
        """登录电子税务局"""
        # 模拟登录
        return {
            "access_token": f"etax_token_{uuid.uuid4().hex[:16]}",
            "refresh_token": f"etax_refresh_{uuid.uuid4().hex[:16]}",
            "expires_in": 7200,
            "taxpayer_name": f"{tax_no}公司",
            "taxpayer_type": "一般纳税人"
        }
    
    def verify_invoice(self, invoice_code: str, invoice_no: str, issue_date: str) -> InvoiceVerifyResult:
        """发票查验"""
        # 模拟查验结果
        amount = Decimal(str(random.randint(1000, 100000)))
        tax_rate = Decimal("0.13")
        tax_amount = (amount * tax_rate).quantize(Decimal("0.01"))
        total_amount = amount + tax_amount
        
        return InvoiceVerifyResult(
            invoice_code=invoice_code,
            invoice_number=invoice_no,
            issue_date=issue_date,
            seller_name=f"销售方{random.randint(1000, 9999)}公司",
            seller_tax_no=f"91{random.randint(100000000000, 999999999999)}",
            buyer_name="购买方公司",
            buyer_tax_no=f"92{random.randint(100000000000, 999999999999)}",
            amount=amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            status="valid"
        )
    
    def get_tax_data(self, tax_no: str, period: str, tax_type: str) -> TaxData:
        """获取税局数据"""
        # 模拟税局数据
        sales_amount = Decimal(str(random.randint(100000, 1000000)))
        sales_tax = (sales_amount * Decimal("0.13")).quantize(Decimal("0.01"))
        
        purchase_amount = Decimal(str(random.randint(50000, 500000)))
        purchase_tax = (purchase_amount * Decimal("0.13")).quantize(Decimal("0.01"))
        
        payable_tax = sales_tax - purchase_tax
        
        return TaxData(
            period=period,
            tax_type=tax_type,
            sales_amount=sales_amount,
            sales_tax=sales_tax,
            purchase_amount=purchase_amount,
            purchase_tax=purchase_tax,
            payable_tax=payable_tax
        )
    
    def submit_declaration(self, declaration_data: Dict) -> Dict:
        """提交纳税申报"""
        # 模拟提交
        return {
            "success": True,
            "receipt_no": f"RECEIPT{uuid.uuid4().hex[:12].upper()}",
            "submit_time": datetime.now().isoformat(),
            "message": "申报提交成功"
        }


class TaxCalculator:
    """税费计算器"""
    
    @staticmethod
    def calculate_vat(vouchers: List, period: str) -> Dict:
        """计算增值税"""
        output_vat = Decimal("0")  # 销项税额
        input_vat = Decimal("0")   # 进项税额
        
        for voucher in vouchers:
            for item in voucher.items:
                # 销项税额
                if item.subject_code and "22210101" in item.subject_code:
                    output_vat += item.credit_amount or Decimal("0")
                # 进项税额
                elif item.subject_code and "22210102" in item.subject_code:
                    input_vat += item.debit_amount or Decimal("0")
        
        payable_vat = output_vat - input_vat
        
        return {
            "period": period,
            "tax_type": "增值税",
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "payable_vat": float(payable_vat),
            "taxable_amount": float((output_vat / Decimal("0.13")).quantize(Decimal("0.01")))
        }
    
    @staticmethod
    def calculate_surtax(vat_payable: Decimal, period: str) -> Dict:
        """计算附加税"""
        # 城建税 7%
        city_tax = (vat_payable * Decimal("0.07")).quantize(Decimal("0.01"))
        # 教育费附加 3%
        edu_tax = (vat_payable * Decimal("0.03")).quantize(Decimal("0.01"))
        # 地方教育费附加 2%
        local_edu_tax = (vat_payable * Decimal("0.02")).quantize(Decimal("0.01"))
        
        total_surtax = city_tax + edu_tax + local_edu_tax
        
        return {
            "period": period,
            "tax_type": "附加税",
            "city_tax": float(city_tax),
            "edu_tax": float(edu_tax),
            "local_edu_tax": float(local_edu_tax),
            "total_surtax": float(total_surtax),
            "payable_amount": float(total_surtax)
        }
    
    @staticmethod
    def calculate_income_tax(profit: Decimal, period: str) -> Dict:
        """计算企业所得税"""
        # 简化计算，实际需考虑各项调整
        rate = Decimal("0.25")  # 25%税率
        tax_amount = (profit * rate).quantize(Decimal("0.01"))
        
        return {
            "period": period,
            "tax_type": "企业所得税",
            "taxable_income": float(profit),
            "tax_rate": "25%",
            "tax_amount": float(tax_amount),
            "payable_amount": float(tax_amount)
        }


# 支持的税务地区
SUPPORTED_TAX_AREAS = [
    {"code": "北京", "name": "北京市税务局"},
    {"code": "上海", "name": "上海市税务局"},
    {"code": "广东", "name": "广东省税务局"},
    {"code": "深圳", "name": "深圳市税务局"},
    {"code": "浙江", "name": "浙江省税务局"},
    {"code": "江苏", "name": "江苏省税务局"},
]

from datetime import datetime
