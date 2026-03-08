from typing import Optional, List
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.bank_account import BankAccount
from app.models.bank_flow import BankFlow
from app.services.bank_api import BankAPIFactory

router = APIRouter(prefix="/bank-accounts", tags=["银行账户"])


class BankAccountCreateRequest(BaseModel):
    bank_code: str
    account_no: str
    account_name: Optional[str] = None
    account_type: str = "basic"


class BankAccountSyncConfigRequest(BaseModel):
    auto_sync: bool = True
    sync_range_days: int = 30


class BankAccountResponse(BaseModel):
    id: str
    bank_code: str
    bank_name: str
    account_no: str
    account_name: Optional[str]
    account_type: str
    auth_status: str
    balance: Optional[float]
    last_sync_at: Optional[str]
    auto_sync: bool


# 支持的银行列表
@router.get("/banks")
async def get_supported_banks(
    current_user=Depends(require_permission("bank_accounts:read"))
):
    """获取支持的银行列表"""
    banks = BankAPIFactory.get_supported_banks()
    return success_response(data={"items": banks})


# 添加银行账户
@router.post("")
async def create_bank_account(
    request: BankAccountCreateRequest,
    current_user=Depends(require_permission("bank_accounts:create")),
    db: Session = Depends(get_db)
):
    """添加银行账户"""
    # 检查账号是否已存在
    exists = db.query(BankAccount).filter(
        BankAccount.customer_id == current_user.customer_id,
        BankAccount.account_no == request.account_no
    ).first()
    
    if exists:
        return error_response(400, "该银行账户已存在")
    
    # 创建银行账户记录
    account = BankAccount(
        id=uuid.uuid4(),
        customer_id=current_user.customer_id,
        bank_code=request.bank_code,
        bank_name=BankAPIFactory.get_bank_name(request.bank_code),
        account_no=request.account_no,
        account_name=request.account_name,
        account_type=request.account_type,
        auth_status="unauthorized",
        auto_sync=True,
        sync_range_days=30,
        is_enabled=True
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    # 生成授权URL
    api = BankAPIFactory.get_api(request.bank_code)
    auth_url = api.get_auth_url(
        redirect_uri=f"/api/v1/bank-accounts/{account.id}/auth-callback",
        state=str(account.id)
    )
    
    return success_response(data={
        "id": str(account.id),
        "auth_url": auth_url,
        "message": "请前往授权页面完成银行授权"
    })


# 银行授权回调
@router.get("/{account_id}/auth-callback")
async def auth_callback(
    account_id: str,
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """银行授权回调"""
    account = db.query(BankAccount).filter(BankAccount.id == account_id).first()
    if not account:
        return error_response(404, "银行账户不存在")
    
    # 模拟获取token
    api = BankAPIFactory.get_api(account.bank_code)
    try:
        auth_result = api.authenticate({"auth_code": code})
        
        account.auth_status = "authorized"
        account.auth_token = auth_result.access_token
        account.refresh_token = auth_result.refresh_token
        account.token_expires_at = datetime.utcnow() + timedelta(seconds=auth_result.expires_in)
        
        db.commit()
        
        return success_response(data={
            "message": "银行授权成功",
            "account_id": str(account.id)
        })
    except Exception as e:
        return error_response(500, f"授权失败: {str(e)}")


# 查询银行账户列表
@router.get("")
async def list_bank_accounts(
    current_user=Depends(require_permission("bank_accounts:read")),
    db: Session = Depends(get_db)
):
    """查询银行账户列表"""
    accounts = db.query(BankAccount).filter(
        BankAccount.customer_id == current_user.customer_id,
        BankAccount.is_enabled == True
    ).order_by(BankAccount.created_at.desc()).all()
    
    items = []
    for account in accounts:
        items.append({
            "id": str(account.id),
            "bank_code": account.bank_code,
            "bank_name": account.bank_name,
            "account_no": mask_account_no(account.account_no),
            "account_name": account.account_name,
            "account_type": account.account_type,
            "auth_status": account.auth_status,
            "balance": float(account.balance) if account.balance else None,
            "balance_updated_at": account.balance_updated_at.isoformat() if account.balance_updated_at else None,
            "last_sync_at": account.last_sync_at.isoformat() if account.last_sync_at else None,
            "auto_sync": account.auto_sync,
            "sync_range_days": account.sync_range_days
        })
    
    return success_response(data={"items": items})


# 同步银行流水
@router.post("/{account_id}/sync")
async def sync_bank_flows(
    account_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    background_tasks: BackgroundTasks = None,
    current_user=Depends(require_permission("bank_accounts:update")),
    db: Session = Depends(get_db)
):
    """同步银行流水"""
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.customer_id == current_user.customer_id
    ).first()
    
    if not account:
        return error_response(404, "银行账户不存在")
    
    if account.auth_status != "authorized":
        return error_response(400, "银行账户未授权")
    
    # 检查token是否过期
    if account.token_expires_at and account.token_expires_at < datetime.utcnow():
        try:
            api = BankAPIFactory.get_api(account.bank_code)
            auth_result = api.refresh_token(account.refresh_token)
            account.auth_token = auth_result.access_token
            account.refresh_token = auth_result.refresh_token
            account.token_expires_at = datetime.utcnow() + timedelta(seconds=auth_result.expires_in)
        except Exception as e:
            return error_response(500, f"Token刷新失败: {str(e)}")
    
    # 同步流水
    try:
        api = BankAPIFactory.get_api(account.bank_code)
        
        if not start_date:
            start_date = datetime.now().date() - timedelta(days=account.sync_range_days)
        if not end_date:
            end_date = datetime.now().date()
        
        transactions = api.query_transactions(
            account.account_no,
            start_date,
            end_date
        )
        
        synced_count = 0
        new_count = 0
        duplicate_count = 0
        
        for trans in transactions:
            synced_count += 1
            
            # 检查是否已存在
            exists = db.query(BankFlow).filter(
                BankFlow.bank_account_id == account_id,
                BankFlow.reference_no == trans.reference_no
            ).first()
            
            if exists:
                duplicate_count += 1
                continue
            
            # 创建流水记录
            flow = BankFlow(
                id=uuid.uuid4(),
                customer_id=account.customer_id,
                bank_account_id=account_id,
                transaction_date=trans.transaction_date,
                transaction_time=trans.transaction_time,
                amount=trans.amount,
                balance=trans.balance,
                counterparty_name=trans.counterparty_name,
                counterparty_account=trans.counterparty_account,
                summary=trans.summary,
                reference_no=trans.reference_no,
                match_status="unmatched"
            )
            db.add(flow)
            new_count += 1
        
        # 更新账户余额
        balance_result = api.query_balance(account.account_no)
        account.balance = balance_result.balance
        account.balance_updated_at = datetime.utcnow()
        account.last_sync_at = datetime.utcnow()
        
        db.commit()
        
        return success_response(data={
            "synced_count": synced_count,
            "new_count": new_count,
            "duplicate_count": duplicate_count,
            "message": f"成功同步 {new_count} 条新流水"
        })
        
    except Exception as e:
        return error_response(500, f"同步失败: {str(e)}")


# 更新同步配置
@router.put("/{account_id}/sync-config")
async def update_sync_config(
    account_id: str,
    request: BankAccountSyncConfigRequest,
    current_user=Depends(require_permission("bank_accounts:update")),
    db: Session = Depends(get_db)
):
    """更新自动同步配置"""
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.customer_id == current_user.customer_id
    ).first()
    
    if not account:
        return error_response(404, "银行账户不存在")
    
    account.auto_sync = request.auto_sync
    account.sync_range_days = request.sync_range_days
    
    db.commit()
    
    return success_response(data={"message": "配置更新成功"})


# 删除银行账户
@router.delete("/{account_id}")
async def delete_bank_account(
    account_id: str,
    current_user=Depends(require_permission("bank_accounts:delete")),
    db: Session = Depends(get_db)
):
    """删除银行账户"""
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.customer_id == current_user.customer_id
    ).first()
    
    if not account:
        return error_response(404, "银行账户不存在")
    
    account.is_enabled = False
    db.commit()
    
    return success_response(data={"message": "银行账户已删除"})


def mask_account_no(account_no: str) -> str:
    """脱敏银行账号"""
    if len(account_no) <= 8:
        return "****" + account_no[-4:]
    return account_no[:4] + "****" + account_no[-4:]
