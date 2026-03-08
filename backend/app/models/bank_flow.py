from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Text, Date, Time, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class BankFlow(BaseModel):
    """银行流水表"""
    __tablename__ = "bank_flows"
    
    customer_id = Column(ForeignKey("customers.id"), nullable=False)
    bank_account_id = Column(ForeignKey("bank_accounts.id"), nullable=True)
    
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
    reference_no = Column(String(100), nullable=True, comment="银行流水号")
    
    # 匹配状态
    match_status = Column(String(20), default="unmatched", comment="匹配状态: unmatched/matched/ignored")
    matched_bill_id = Column(ForeignKey("bills.id"), nullable=True)
    
    # 原始数据
    raw_data = Column(JSON, nullable=True, comment="原始行数据")
    source_file = Column(String(255), nullable=True, comment="源文件名")
    
    # 状态
    status = Column(String(20), default="active", comment="状态: active/deleted")
    
    # 关系
    customer = relationship("Customer", back_populates="bank_flows")
    bank_account = relationship("BankAccount", back_populates="bank_flows")
    matched_bill = relationship("Bill", back_populates="bank_flow_matches")
