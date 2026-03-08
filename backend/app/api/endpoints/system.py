"""
Step3 系统管理模块快速开发
TASK-SYS-01 用户管理 + TASK-SYS-02 角色权限 + TASK-SYS-03 操作日志 + TASK-SYS-04 系统配置
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.user import User

router = APIRouter(prefix="/sys", tags=["系统管理"])

# ===== TASK-SYS-01: 用户管理 =====

class UserCreateRequest(BaseModel):
    username: str
    password: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str = "viewer"
    is_active: bool = True

@router.get("/users")
async def list_users(
    keyword: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_permission("sys:users:read")),
    db: Session = Depends(get_db)
):
    """用户列表"""
    query = db.query(User)
    
    if keyword:
        query = query.filter(
            User.name.ilike(f"%{keyword}%") | 
            User.username.ilike(f"%{keyword}%")
        )
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for u in users:
        items.append({
            "id": str(u.id),
            "username": u.username,
            "name": u.name,
            "phone": u.phone,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })
    
    return success_response(data={"items": items, "total": total})


@router.post("/users")
async def create_user(
    request: UserCreateRequest,
    current_user=Depends(require_permission("sys:users:create")),
    db: Session = Depends(get_db)
):
    """创建用户"""
    from app.core.security import get_password_hash
    
    exists = db.query(User).filter(User.username == request.username).first()
    if exists:
        return error_response(400, "用户名已存在")
    
    user = User(
        id=uuid.uuid4(),
        username=request.username,
        password_hash=get_password_hash(request.password),
        name=request.name,
        phone=request.phone,
        role=request.role,
        is_active=request.is_active
    )
    db.add(user)
    db.commit()
    
    return success_response(data={"id": str(user.id), "message": "用户创建成功"})


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    request: dict,
    current_user=Depends(require_permission("sys:users:update")),
    db: Session = Depends(get_db)
):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error_response(404, "用户不存在")
    
    for key, value in request.items():
        if hasattr(user, key) and key != "id":
            setattr(user, key, value)
    
    db.commit()
    return success_response(data={"message": "用户更新成功"})


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user=Depends(require_permission("sys:users:delete")),
    db: Session = Depends(get_db)
):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return error_response(404, "用户不存在")
    
    if user.id == current_user.id:
        return error_response(400, "不能删除自己")
    
    db.delete(user)
    db.commit()
    return success_response(data={"message": "用户删除成功"})


# ===== TASK-SYS-02: 角色权限 =====

ROLES_CONFIG = {
    "admin": {
        "name": "管理员",
        "permissions": ["*"]
    },
    "accountant": {
        "name": "会计",
        "permissions": [
            "bills:read", "bills:create", "bills:update",
            "vouchers:read", "vouchers:create", "vouchers:audit",
            "customers:read"
        ]
    },
    "viewer": {
        "name": "查看者",
        "permissions": ["bills:read", "vouchers:read", "customers:read"]
    },
    "customer": {
        "name": "客户",
        "permissions": ["bills:read", "bills:create", "vouchers:read"]
    }
}

@router.get("/roles")
async def list_roles(
    current_user=Depends(require_permission("sys:roles:read"))
):
    """角色列表"""
    items = []
    for key, config in ROLES_CONFIG.items():
        items.append({
            "code": key,
            "name": config["name"],
            "permissions": config["permissions"]
        })
    return success_response(data={"items": items})


# ===== TASK-SYS-03: 操作日志 =====

from sqlalchemy import Column, String, Text, JSON
from app.models.base import BaseModel

class OperationLog(BaseModel):
    __tablename__ = "operation_logs"
    
    user_id = Column(String(50))
    username = Column(String(50))
    action = Column(String(50))  # CREATE/UPDATE/DELETE/LOGIN/LOGOUT
    resource_type = Column(String(50))
    resource_id = Column(String(50))
    description = Column(Text)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    request_data = Column(JSON)
    created_at = Column(datetime, default=datetime.utcnow)

@router.get("/logs")
async def list_logs(
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_permission("sys:logs:read")),
    db: Session = Depends(get_db)
):
    """操作日志列表"""
    query = db.query(OperationLog)
    
    if action:
        query = query.filter(OperationLog.action == action)
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    if start_date:
        query = query.filter(OperationLog.created_at >= start_date)
    if end_date:
        query = query.filter(OperationLog.created_at <= end_date)
    
    total = query.count()
    logs = query.order_by(OperationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for log in logs:
        items.append({
            "id": str(log.id),
            "username": log.username,
            "action": log.action,
            "resource_type": log.resource_type,
            "description": log.description,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    return success_response(data={"items": items, "total": total})


# ===== TASK-SYS-04: 系统配置 =====

SYSTEM_CONFIG = {
    "company_name": "SmartLedger",
    "system_name": "智能记账系统",
    "logo_url": "/logo.png",
    "favicon_url": "/favicon.ico",
    "login_bg": "/login-bg.jpg",
    "theme_color": "#409EFF",
    "default_page_size": 20,
    "max_upload_size": 10485760,
    "session_timeout": 30,
    "enable_register": True,
    "enable_oauth": False
}

@router.get("/config")
async def get_config(
    current_user=Depends(require_permission("sys:config:read"))
):
    """获取系统配置"""
    return success_response(data=SYSTEM_CONFIG)


@router.put("/config")
async def update_config(
    config: dict,
    current_user=Depends(require_permission("sys:config:update"))
):
    """更新系统配置"""
    global SYSTEM_CONFIG
    SYSTEM_CONFIG.update(config)
    return success_response(data={"message": "配置更新成功"})
