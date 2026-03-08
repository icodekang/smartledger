"""
Step3 财务报表模块快速开发
TASK-REPORT-01 资产负债表 + TASK-REPORT-02 利润表 + TASK-REPORT-03 现金流量表 + TASK-REPORT-04 科目余额表
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import date
from decimal import Decimal

from app.core.database import get_db
from app.core.response import success_response
from app.core.permissions import require_permission
from app.models.voucher import Voucher, VoucherItem

router = APIRouter(prefix="/reports", tags=["财务报表"])

# ===== TASK-REPORT-01: 资产负债表 =====

@router.get("/balance-sheet")
async def get_balance_sheet(
    customer_id: str,
    period: str,  # 2024-03
    current_user=Depends(require_permission("reports:read")),
    db: Session = Depends(get_db)
):
    """资产负债表"""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    period_date = datetime.strptime(period, "%Y-%m").date()
    period_end = period_date + relativedelta(months=1, days=-1)
    
    # 查询期末余额
    vouchers = db.query(Voucher).filter(
        Voucher.customer_id == customer_id,
        Voucher.period == period,
        Voucher.status == "approved"
    ).all()
    
    voucher_ids = [v.id for v in vouchers]
    
    # 统计各科目余额
    items = db.query(
        VoucherItem.subject_code,
        VoucherItem.subject_name,
        func.sum(VoucherItem.debit_amount).label("total_debit"),
        func.sum(VoucherItem.credit_amount).label("total_credit")
    ).filter(
        VoucherItem.voucher_id.in_(voucher_ids)
    ).group_by(VoucherItem.subject_code, VoucherItem.subject_name).all()
    
    # 资产、负债、权益分类
    assets = []
    liabilities = []
    equity = []
    
    total_assets = Decimal("0")
    total_liabilities = Decimal("0")
    total_equity = Decimal("0")
    
    for item in items:
        code = item.subject_code
        balance = (item.total_debit or Decimal("0")) - (item.total_credit or Decimal("0"))
        
        item_data = {
            "subject_code": code,
            "subject_name": item.subject_name,
            "debit": float(item.total_debit or 0),
            "credit": float(item.total_credit or 0),
            "balance": float(balance)
        }
        
        if code.startswith("1"):  # 资产类
            assets.append(item_data)
            total_assets += balance
        elif code.startswith("2"):  # 负债类
            liabilities.append(item_data)
            total_liabilities += balance
        elif code.startswith("4"):  # 权益类
            equity.append(item_data)
            total_equity += balance
    
    return success_response(data={
        "period": period,
        "assets": {
            "items": assets,
            "total": float(total_assets)
        },
        "liabilities": {
            "items": liabilities,
            "total": float(total_liabilities)
        },
        "equity": {
            "items": equity,
            "total": float(total_equity)
        },
        "balance_check": abs(total_assets - total_liabilities - total_equity) < 0.01
    })


# ===== TASK-REPORT-02: 利润表 =====

@router.get("/income-statement")
async def get_income_statement(
    customer_id: str,
    period: str,
    current_user=Depends(require_permission("reports:read")),
    db: Session = Depends(get_db)
):
    """利润表"""
    vouchers = db.query(Voucher).filter(
        Voucher.customer_id == customer_id,
        Voucher.period == period,
        Voucher.status == "approved"
    ).all()
    
    voucher_ids = [v.id for v in vouchers]
    
    items = db.query(
        VoucherItem.subject_code,
        VoucherItem.subject_name,
        func.sum(VoucherItem.debit_amount).label("total_debit"),
        func.sum(VoucherItem.credit_amount).label("total_credit")
    ).filter(
        VoucherItem.voucher_id.in_(voucher_ids)
    ).group_by(VoucherItem.subject_code, VoucherItem.subject_name).all()
    
    revenue = Decimal("0")      # 收入
    cost = Decimal("0")         # 成本
    expenses = Decimal("0")     # 费用
    
    for item in items:
        code = item.subject_code
        balance = (item.total_credit or Decimal("0")) - (item.total_debit or Decimal("0"))
        
        if code.startswith("6") and code[1] in ["0", "1"]:  # 收入类
            revenue += balance
        elif code.startswith("6") and code[1] == "4":  # 成本类
            cost += -balance
        elif code.startswith("6") and code[1] in ["2", "3"]:  # 费用类
            expenses += -balance
    
    gross_profit = revenue - cost
    net_profit = gross_profit - expenses
    
    return success_response(data={
        "period": period,
        "revenue": float(revenue),
        "cost": float(cost),
        "gross_profit": float(gross_profit),
        "expenses": float(expenses),
        "net_profit": float(net_profit)
    })


# ===== TASK-REPORT-03: 现金流量表 =====

@router.get("/cash-flow")
async def get_cash_flow(
    customer_id: str,
    period: str,
    current_user=Depends(require_permission("reports:read")),
    db: Session = Depends(get_db)
):
    """现金流量表"""
    vouchers = db.query(Voucher).filter(
        Voucher.customer_id == customer_id,
        Voucher.period == period,
        Voucher.status == "approved"
    ).all()
    
    voucher_ids = [v.id for v in vouchers]
    
    items = db.query(
        VoucherItem.subject_code,
        VoucherItem.subject_name,
        func.sum(VoucherItem.debit_amount).label("total_debit"),
        func.sum(VoucherItem.credit_amount).label("total_credit")
    ).filter(
        VoucherItem.voucher_id.in_(voucher_ids)
    ).group_by(VoucherItem.subject_code, VoucherItem.subject_name).all()
    
    operating_in = Decimal("0")
    operating_out = Decimal("0")
    investing_in = Decimal("0")
    investing_out = Decimal("0")
    financing_in = Decimal("0")
    financing_out = Decimal("0")
    
    for item in items:
        code = item.subject_code
        
        # 现金类科目
        if code.startswith("1001") or code.startswith("1002"):
            debit = item.total_debit or Decimal("0")
            credit = item.total_credit or Decimal("0")
            
            # 简化分类
            if debit > 0:
                operating_in += debit
            if credit > 0:
                operating_out += credit
    
    operating_net = operating_in - operating_out
    investing_net = investing_in - investing_out
    financing_net = financing_in - financing_out
    
    return success_response(data={
        "period": period,
        "operating": {
            "inflow": float(operating_in),
            "outflow": float(operating_out),
            "net": float(operating_net)
        },
        "investing": {
            "inflow": float(investing_in),
            "outflow": float(investing_out),
            "net": float(investing_net)
        },
        "financing": {
            "inflow": float(financing_in),
            "outflow": float(financing_out),
            "net": float(financing_net)
        },
        "net_increase": float(operating_net + investing_net + financing_net)
    })


# ===== TASK-REPORT-04: 科目余额表 =====

@router.get("/subject-balance")
async def get_subject_balance(
    customer_id: str,
    period: str,
    subject_code: Optional[str] = None,
    current_user=Depends(require_permission("reports:read")),
    db: Session = Depends(get_db)
):
    """科目余额表"""
    vouchers = db.query(Voucher).filter(
        Voucher.customer_id == customer_id,
        Voucher.period == period,
        Voucher.status == "approved"
    ).all()
    
    voucher_ids = [v.id for v in vouchers]
    
    query = db.query(
        VoucherItem.subject_code,
        VoucherItem.subject_name,
        func.sum(VoucherItem.debit_amount).label("total_debit"),
        func.sum(VoucherItem.credit_amount).label("total_credit")
    ).filter(
        VoucherItem.voucher_id.in_(voucher_ids)
    )
    
    if subject_code:
        query = query.filter(VoucherItem.subject_code.like(f"{subject_code}%"))
    
    items = query.group_by(VoucherItem.subject_code, VoucherItem.subject_name).all()
    
    result = []
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    
    for item in items:
        debit = item.total_debit or Decimal("0")
        credit = item.total_credit or Decimal("0")
        balance = debit - credit
        
        result.append({
            "subject_code": item.subject_code,
            "subject_name": item.subject_name,
            "debit": float(debit),
            "credit": float(credit),
            "balance": float(balance),
            "direction": "借" if balance >= 0 else "贷"
        })
        
        total_debit += debit
        total_credit += credit
    
    return success_response(data={
        "period": period,
        "items": result,
        "total": {
            "debit": float(total_debit),
            "credit": float(total_credit),
            "balance": float(total_debit - total_credit)
        },
        "is_balanced": abs(total_debit - total_credit) < 0.01
    })
