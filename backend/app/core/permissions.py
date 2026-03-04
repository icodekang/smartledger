from enum import Enum
from functools import wraps
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import PermissionDeniedException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class Role(Enum):
    """角色枚举"""
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


# 权限映射
PERMISSIONS = {
    Role.ADMIN: ["*"],
    Role.ACCOUNTANT: [
        "bills:read", "bills:create", "bills:update",
        "vouchers:read", "vouchers:create", "vouchers:audit",
        "dashboard:read"
    ],
    Role.VIEWER: ["bills:read", "vouchers:read", "dashboard:read"]
}


def check_permission(user_role: str, required_permission: str) -> bool:
    """检查权限"""
    try:
        role = Role(user_role)
    except ValueError:
        return False
    
    user_permissions = PERMISSIONS.get(role, [])
    
    if "*" in user_permissions:
        return True
    
    for perm in user_permissions:
        if perm == required_permission:
            return True
        if perm.endswith(":*"):
            resource = perm[:-2]
            if required_permission.startswith(f"{resource}:"):
                return True
    
    return False


def require_permission(permission: str):
    """权限装饰器"""
    from app.core.security import decode_token
    from app.core.database import get_db
    from sqlalchemy.orm import Session
    from app.models.user import User
    from fastapi import Depends
    
    async def permission_checker(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ):
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")
        
        if not check_permission(user.role, permission):
            raise PermissionDeniedException(f"Permission denied: {permission}")
        
        return user
    
    return permission_checker
