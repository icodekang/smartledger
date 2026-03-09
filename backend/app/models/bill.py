from sqlalchemy import Column, String, Date, Numeric, ForeignKey, JSON, Text, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class BillItem(BaseModel):
    """票据明细项"""
    __tablename__ = "bill_items"
    
    bill_id = Column(ForeignKey("bills.id"), nullable=False)
    name = Column(String(200), nullable=False, comment="商品名称")
    spec = Column(String(100), comment="规格型号")
    unit = Column(String(20), comment="单位")
    quantity = Column(Numeric(12, 4), comment="数量")
    unit_price = Column(Numeric(12, 4), comment="单价")
    amount = Column(Numeric(12, 2), comment="金额")
    tax_rate = Column(String(10), comment="税率")
    tax_amount = Column(Numeric(12, 2), comment="税额")
    
    # 关系
    bill = relationship("Bill", back_populates="items")


class Bill(BaseModel):
    """票据表"""
    __tablename__ = "bills"
    
    customer_id = Column(ForeignKey("customers.id"))
    bill_type = Column(String(20))
    storage_path = Column(String(500))
    storage_url = Column(String(500))
    
    ocr_result = Column(JSON)
    ocr_confidence = Column(Numeric(3, 2))
    
    # 发票基本信息
    invoice_code = Column(String(20), comment="发票代码")
    invoice_number = Column(String(20), comment="发票号码")
    invoice_date = Column(Date, comment="开票日期")
    invoice_type = Column(String(20), comment="发票类型")
    
    # 金额信息
    amount = Column(Numeric(12, 2), comment="金额")
    tax_amount = Column(Numeric(12, 2), comment="税额")
    total_amount = Column(Numeric(12, 2), comment="价税合计")
    
    # 销售方信息
    seller_name = Column(String(200), comment="销售方名称")
    seller_tax_no = Column(String(20), comment="销售方税号")
    seller_address = Column(String(200), comment="销售方地址电话")
    seller_bank = Column(String(100), comment="销售方开户行及账号")
    
    # 购买方信息
    buyer_name = Column(String(200), comment="购买方名称")
    buyer_tax_no = Column(String(20), comment="购买方税号")
    buyer_address = Column(String(200), comment="购买方地址电话")
    buyer_bank = Column(String(100), comment="购买方开户行及账号")
    
    process_status = Column(String(20), default="pending")
    ai_confidence = Column(Numeric(3, 2))
    ai_anomalies = Column(JSON)
    
    # 关联生成的凭证
    voucher_id = Column(ForeignKey("vouchers.id"), nullable=True)
    
    # 关系
    customer = relationship("Customer", back_populates="bills")
    items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")
    bank_flow_matches = relationship("BankFlow", back_populates="matched_bill")
