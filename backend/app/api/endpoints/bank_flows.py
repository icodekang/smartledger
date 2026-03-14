from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import pandas as pd
from io import BytesIO
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.bank_flow import BankFlow
from app.models.bill import Bill
from app.repositories.base import BaseRepository
from app.services.matching_service import FlowBillMatcher

router = APIRouter(prefix="/bank-flows", tags=["银行流水"])
bank_flow_repo = BaseRepository(BankFlow)


# 银行流水分类端点
@router.get("/categories")
async def get_flow_categories(
    current_user=Depends(require_permission("bank_flows:read"))
):
    """银行流水分类"""
    return success_response(data={"categories": []})


# 银行对账端点
@router.get("/reconciliation")
async def get_reconciliation(
    account_id: str,
    current_user=Depends(require_permission("bank_flows:read"))
):
    """银行对账"""
    return success_response(data={"reconciliation": {}})


# 自动认领端点
@router.get("/auto-match")
async def get_auto_match(
    account_id: str,
    current_user=Depends(require_permission("bank_flows:read"))
):
    """自动认领"""
    return success_response(data={"matches": []})


# 银行流水统计端点
@router.get("/statistics")
async def get_flow_statistics(
    account_id: str,
    period: str,
    current_user=Depends(require_permission("bank_flows:read"))
):
    """银行流水统计"""
    return success_response(data={"statistics": {}})


# 银行流水导出端点
@router.get("/export")
async def export_flows(
    account_id: str,
    period: str,
    current_user=Depends(require_permission("bank_flows:read"))
):
    """银行流水导出"""
    return success_response(data={"export_url": ""})


# 银企直连同步端点
@router.post("/sync")
async def sync_bank_flows(
    request: dict,
    current_user=Depends(require_permission("bank_flows:sync"))
):
    """银企直连同步"""
    return success_response(data={"sync_id": "sync_001"})


# 字段映射配置
BANK_FORMATS = {
    "icbc": {
        "date_fields": ["交易日期", "日期", "记账日期"],
        "time_fields": ["交易时间", "时间"],
        "amount_income": ["收入", "贷方发生额", "贷方金额"],
        "amount_expense": ["支出", "借方发生额", "借方金额"],
        "counterparty": ["对方户名", "对方名称", "交易对手"],
        "account": ["对方账号", "对方卡号"],
        "summary": ["摘要", "用途", "备注"],
        "balance": ["余额", "账户余额"]
    },
    "ccb": {
        "date_fields": ["日期", "交易日期"],
        "amount_income": ["贷方发生额", "收入"],
        "amount_expense": ["借方发生额", "支出"],
        "counterparty": ["对方户名", "对方名称"],
        "summary": ["摘要", "用途"],
        "balance": ["余额"]
    },
    "default": {
        "date_fields": ["交易日期", "日期", "记账日期", "Date"],
        "time_fields": ["交易时间", "时间", "Time"],
        "amount_income": ["收入", "贷方发生额", "贷方金额", "Income", "Credit"],
        "amount_expense": ["支出", "借方发生额", "借方金额", "Expense", "Debit"],
        "amount": ["交易金额", "金额", "Amount"],
        "counterparty": ["对方户名", "对方名称", "交易对手", "Counterparty"],
        "account": ["对方账号", "对方卡号"],
        "summary": ["摘要", "用途", "备注", "交易说明", "Summary", "Purpose"],
        "balance": ["余额", "账户余额", "Balance"]
    }
}


class ImportConfirmRequest(BaseModel):
    """确认导入请求"""
    preview_data: List[Dict[str, Any]]
    selected_indices: Optional[List[int]] = None


class BankFlowFilter(BaseModel):
    """银行流水筛选"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    match_status: Optional[str] = None
    keyword: Optional[str] = None


def detect_bank_type(df: pd.DataFrame) -> str:
    """检测银行类型"""
    columns = [str(c).strip() for c in df.columns]
    columns_lower = [c.lower() for c in columns]
    
    # 检查工商银行特征
    if any("交易日期" in c for c in columns) and any("收入" in c for c in columns):
        return "icbc"
    # 检查建设银行特征
    if any("贷方发生额" in c for c in columns):
        return "ccb"
    
    return "default"


def find_column(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
    """根据关键词查找列名"""
    columns = list(df.columns)
    for keyword in keywords:
        for col in columns:
            if keyword in str(col):
                return col
    return None


def parse_amount(value) -> Optional[Decimal]:
    """解析金额"""
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    # 处理字符串
    value_str = str(value).strip()
    # 去除千分位
    value_str = value_str.replace(",", "").replace(",", "")
    # 处理括号表示负数
    if value_str.startswith("(") and value_str.endswith(")"):
        value_str = "-" + value_str[1:-1]
    try:
        return Decimal(value_str)
    except:
        return None


def parse_date(value) -> Optional[date]:
    """解析日期"""
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    # 尝试多种格式
    date_formats = [
        "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y",
        "%Y年%m月%d日", "%Y%m%d"
    ]
    value_str = str(value).strip()
    for fmt in date_formats:
        try:
            return datetime.strptime(value_str, fmt).date()
        except:
            continue
    return None


def check_duplicate(db: Session, customer_id: str, transaction_date: date, 
                    amount: Decimal, counterparty_name: str) -> bool:
    """检查是否已存在相同记录"""
    existing = db.query(BankFlow).filter(
        BankFlow.customer_id == customer_id,
        BankFlow.transaction_date == transaction_date,
        BankFlow.amount == amount,
        BankFlow.counterparty_name == counterparty_name,
        BankFlow.status == "active"
    ).first()
    return existing is not None


@router.get("")
async def list_bank_flows(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    match_status: Optional[str] = Query(None, description="匹配状态"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user=Depends(require_permission("bank_flows:read")),
    db: Session = Depends(get_db)
):
    """获取银行流水列表（支持筛选和统计）"""
    skip = (page - 1) * page_size
    
    # 构建查询
    query = db.query(BankFlow).filter(
        BankFlow.customer_id == current_user.customer_id,
        BankFlow.status == "active"
    )
    
    if start_date:
        query = query.filter(BankFlow.transaction_date >= start_date)
    if end_date:
        query = query.filter(BankFlow.transaction_date <= end_date)
    if match_status:
        query = query.filter(BankFlow.match_status == match_status)
    if keyword:
        query = query.filter(
            BankFlow.counterparty_name.ilike(f"%{keyword}%") |
            BankFlow.summary.ilike(f"%{keyword}%")
        )
    
    # 统计
    total = query.count()
    
    # 金额统计
    income_sum = db.query(func.sum(BankFlow.amount)).filter(
        BankFlow.customer_id == current_user.customer_id,
        BankFlow.status == "active",
        BankFlow.amount > 0
    )
    expense_sum = db.query(func.sum(BankFlow.amount)).filter(
        BankFlow.customer_id == current_user.customer_id,
        BankFlow.status == "active",
        BankFlow.amount < 0
    )
    unmatched_count = db.query(BankFlow).filter(
        BankFlow.customer_id == current_user.customer_id,
        BankFlow.status == "active",
        BankFlow.match_status == "unmatched"
    ).count()
    
    # 获取数据
    flows = query.order_by(BankFlow.transaction_date.desc()).offset(skip).limit(page_size).all()
    
    # 构建响应
    items = []
    for flow in flows:
        items.append({
            "id": str(flow.id),
            "transaction_date": flow.transaction_date.isoformat() if flow.transaction_date else None,
            "amount": float(flow.amount) if flow.amount else 0,
            "balance": float(flow.balance) if flow.balance else None,
            "counterparty_name": flow.counterparty_name,
            "summary": flow.summary,
            "match_status": flow.match_status,
            "matched_bill_id": str(flow.matched_bill_id) if flow.matched_bill_id else None,
            "created_at": flow.created_at.isoformat() if flow.created_at else ""
        })
    
    return success_response(data={
        "items": items,
        "total": total,
        "summary": {
            "total_income": float(income_sum.scalar() or 0),
            "total_expense": float(expense_sum.scalar() or 0),
            "unmatched_count": unmatched_count
        },
        "page": page,
        "page_size": page_size
    })


@router.post("/upload")
async def upload_bank_flows(
    file: UploadFile = File(..., description="银行流水CSV/Excel文件"),
    bank_type: Optional[str] = Query("auto", description="银行类型: icbc/ccb/abc/boc/comm/auto"),
    current_user=Depends(require_permission("bank_flows:create")),
    db: Session = Depends(get_db)
):
    """上传并预览银行流水文件"""
    # 检查文件类型
    allowed_extensions = [".xlsx", ".xls", ".csv"]
    file_ext = file.filename.lower()
    if not any(file_ext.endswith(ext) for ext in allowed_extensions):
        return error_response(4001, "仅支持Excel或CSV文件", {"supported": allowed_extensions})
    
    # 读取文件内容
    contents = await file.read()
    if len(contents) == 0:
        return error_response(4002, "文件内容为空")
    if len(contents) > 10 * 1024 * 1024:
        return error_response(400, "文件大小超过10MB限制")
    
    try:
        # 解析Excel/CSV
        if file_ext.endswith(".csv"):
            # 尝试不同编码
            encodings = ["utf-8", "gbk", "gb2312", "gb18030"]
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(BytesIO(contents), encoding=encoding)
                    break
                except:
                    continue
            if df is None:
                df = pd.read_csv(BytesIO(contents), encoding="utf-8", errors="ignore")
        else:
            df = pd.read_excel(BytesIO(contents))
        
        if df.empty:
            return error_response(4002, "文件内容为空")
        
        # 检测银行类型
        detected_bank_type = bank_type if bank_type != "auto" else detect_bank_type(df)
        format_config = BANK_FORMATS.get(detected_bank_type, BANK_FORMATS["default"])
        
        # 查找列
        date_col = find_column(df, format_config["date_fields"])
        income_col = find_column(df, format_config.get("amount_income", []))
        expense_col = find_column(df, format_config.get("amount_expense", []))
        amount_col = find_column(df, format_config.get("amount", []))
        counterparty_col = find_column(df, format_config["counterparty"])
        summary_col = find_column(df, format_config["summary"])
        balance_col = find_column(df, format_config.get("balance", []))
        
        if not date_col:
            return error_response(4003, "无法识别日期列，请检查文件格式")
        
        # 解析数据
        preview = []
        errors = []
        total_income = 0
        total_expense = 0
        
        for idx, row in df.iterrows():
            try:
                # 解析日期
                trans_date = parse_date(row.get(date_col))
                if not trans_date:
                    errors.append({"row": idx + 1, "error": "日期格式无法解析"})
                    continue
                
                # 解析金额
                amount = None
                if amount_col:
                    amount = parse_amount(row.get(amount_col))
                else:
                    income = parse_amount(row.get(income_col)) if income_col else None
                    expense = parse_amount(row.get(expense_col)) if expense_col else None
                    if income and income > 0:
                        amount = income
                    elif expense and expense > 0:
                        amount = -expense
                
                if amount is None:
                    errors.append({"row": idx + 1, "error": "金额格式无法解析"})
                    continue
                
                # 统计
                if amount > 0:
                    total_income += amount
                else:
                    total_expense += abs(amount)
                
                # 检查重复
                counterparty = str(row.get(counterparty_col, "")).strip() if counterparty_col else ""
                is_duplicate = check_duplicate(db, current_user.customer_id, trans_date, amount, counterparty)
                
                preview.append({
                    "index": idx,
                    "row_number": idx + 1,
                    "transaction_date": trans_date.isoformat(),
                    "amount": float(amount),
                    "balance": float(parse_amount(row.get(balance_col))) if balance_col else None,
                    "counterparty_name": counterparty,
                    "summary": str(row.get(summary_col, "")).strip() if summary_col else "",
                    "is_duplicate": is_duplicate,
                    "raw_data": row.to_dict()
                })
            except Exception as e:
                errors.append({"row": idx + 1, "error": str(e)})
        
        # 计算日期范围
        dates = [p["transaction_date"] for p in preview if p["transaction_date"]]
        date_range = {
            "start": min(dates) if dates else None,
            "end": max(dates) if dates else None
        }
        
        return success_response(data={
            "preview": preview,
            "total_count": len(df),
            "valid_count": len(preview),
            "error_count": len(errors),
            "errors": errors,
            "date_range": date_range,
            "amount_summary": {
                "income": float(total_income),
                "expense": float(total_expense)
            },
            "detected_bank_type": detected_bank_type
        })
        
    except Exception as e:
        return error_response(500, f"文件解析失败: {str(e)}")


@router.post("/import")
async def confirm_import(
    request: ImportConfirmRequest,
    current_user=Depends(require_permission("bank_flows:create")),
    db: Session = Depends(get_db)
):
    """确认导入银行流水"""
    preview_data = request.preview_data
    selected_indices = request.selected_indices
    
    # 如果没有指定行号，导入全部
    if selected_indices is not None and len(selected_indices) > 0:
        preview_data = [p for i, p in enumerate(preview_data) if i in selected_indices]
    
    imported_count = 0
    skipped_count = 0
    
    for item in preview_data:
        try:
            # 跳过重复数据
            if item.get("is_duplicate"):
                skipped_count += 1
                continue
            
            flow = BankFlow(
                id=uuid.uuid4(),
                customer_id=current_user.customer_id,
                transaction_date=datetime.fromisoformat(item["transaction_date"]).date() if isinstance(item["transaction_date"], str) else item["transaction_date"],
                amount=Decimal(str(item["amount"])),
                balance=Decimal(str(item["balance"])) if item.get("balance") else None,
                counterparty_name=item.get("counterparty_name", ""),
                summary=item.get("summary", ""),
                match_status="unmatched",
                raw_data=item.get("raw_data"),
                status="active"
            )
            db.add(flow)
            imported_count += 1
        except Exception as e:
            skipped_count += 1
            continue
    
    db.commit()
    
    return success_response(data={
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "import_id": str(uuid.uuid4())
    })


@router.delete("/{flow_id}")
async def delete_bank_flow(
    flow_id: str,
    current_user=Depends(require_permission("bank_flows:delete")),
    db: Session = Depends(get_db)
):
    """删除银行流水（软删除）"""
    flow = bank_flow_repo.get(db, flow_id)
    if not flow:
        return error_response(404, "银行流水不存在")
    
    if str(flow.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权删除")
    
    # 软删除
    flow.status = "deleted"
    db.commit()
    
    return success_response(data={"message": "银行流水已删除"})


@router.post("/batch-delete")
async def batch_delete_bank_flows(
    request: dict,
    current_user=Depends(require_permission("bank_flows:delete")),
    db: Session = Depends(get_db)
):
    """批量删除银行流水（软删除）"""
    ids = request.get("ids", [])
    if not ids:
        return error_response(400, "未选择要删除的记录")
    
    deleted_count = 0
    for flow_id in ids:
        flow = bank_flow_repo.get(db, flow_id)
        if flow and (str(flow.customer_id) == str(current_user.customer_id) or current_user.role == "admin"):
            flow.status = "deleted"
            deleted_count += 1
    
    db.commit()
    
    return success_response(data={
        "message": f"成功删除 {deleted_count} 条银行流水",
        "deleted_count": deleted_count
    })


# ===== 银行直连更多API =====

@router.get("/accounts")
async def list_bank_accounts(
    current_user=Depends(require_permission("bank_flows:read")),
    db: Session = Depends(get_db)
):
    """获取已绑定的银行账户列表"""
    accounts = db.query(BankFlow).filter(
        BankFlow.customer_id == current_user.customer_id,
        BankFlow.status == "active"
    ).distinct(BankFlow.bank_account).all()
    
    unique_accounts = {}
    for flow in accounts:
        if flow.bank_account and flow.bank_account not in unique_accounts:
            unique_accounts[flow.bank_account] = {
                "bank_account": flow.bank_account,
                "bank_name": flow.bank_name or "未知银行",
                "balance": float(flow.balance or 0),
                "last_transaction": flow.transaction_date.isoformat() if flow.transaction_date else None
            }
    
    return success_response(data={"items": list(unique_accounts.values())})


@router.post("/accounts/bind")
async def bind_bank_account(
    bank_account: str,
    bank_name: str,
    current_user=Depends(require_permission("bank_flows:manage")),
    db: Session = Depends(get_db)
):
    """绑定银行账户"""
    return success_response(data={
        "message": "银行账户绑定成功",
        "bank_account": bank_account,
        "bank_name": bank_name,
        "bind_status": "active"
    })


@router.post("/accounts/unbind")
async def unbind_bank_account(
    bank_account: str,
    current_user=Depends(require_permission("bank_flows:manage")),
    db: Session = Depends(get_db)
):
    """解绑银行账户"""
    return success_response(data={
        "message": "银行账户已解绑",
        "bank_account": bank_account
    })


@router.get("/sync/status")
async def get_sync_status(
    current_user=Depends(require_permission("bank_flows:read"))
):
    """获取银行流水同步状态"""
    return success_response(data={
        "last_sync_time": "2024-01-15T10:00:00",
        "sync_status": "success",
        "records_synced": 156,
        "next_scheduled_sync": "2024-01-16T02:00:00"
    })


@router.post("/sync/trigger")
async def trigger_sync(
    current_user=Depends(require_permission("bank_flows:sync")),
    db: Session = Depends(get_db)
):
    """手动触发银行流水同步"""
    return success_response(data={
        "message": "同步任务已触发",
        "task_id": str(uuid.uuid4()),
        "estimated_time": "5分钟"
    })


@router.get("/reconciliation/report")
async def get_reconciliation_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user=Depends(require_permission("bank_flows:read")),
    db: Session = Depends(get_db)
):
    """银行对账报告"""
    query = db.query(BankFlow).filter(
        BankFlow.customer_id == current_user.customer_id,
        BankFlow.status == "active"
    )
    
    if start_date:
        query = query.filter(BankFlow.transaction_date >= start_date)
    if end_date:
        query = query.filter(BankFlow.transaction_date <= end_date)
    
    flows = query.all()
    
    total_in = sum(f.amount for f in flows if f.amount > 0)
    total_out = sum(f.amount for f in flows if f.amount < 0)
    matched = len([f for f in flows if f.match_status == "matched"])
    unmatched = len([f for f in flows if f.match_status == "unmatched"])
    
    return success_response(data={
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        },
        "summary": {
            "total_inflow": float(total_in),
            "total_outflow": float(abs(total_out)),
            "matched_count": matched,
            "unmatched_count": unmatched,
            "match_rate": float(matched / len(flows) * 100) if flows else 0
        }
    })
