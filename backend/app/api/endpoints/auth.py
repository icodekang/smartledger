from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
import re

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.exceptions import AuthenticationException
from app.core.security import decode_token
from app.core.rate_limit import login_rate_limit
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class RegisterRequest(BaseModel):
    """注册请求体"""
    username: str
    password: str
    name: str


def validate_password_strength(password: str) -> tuple[bool, str]:
    """验证密码强度
    
    要求：
    - 至少8个字符
    - 包含至少一个大写字母
    - 包含至少一个小写字母
    - 包含至少一个数字
    """
    if len(password) < 8:
        return False, "密码长度至少8个字符"
    
    if not re.search(r"[A-Z]", password):
        return False, "密码必须包含至少一个大写字母"
    
    if not re.search(r"[a-z]", password):
        return False, "密码必须包含至少一个小写字母"
    
    if not re.search(r"\d", password):
        return False, "密码必须包含至少一个数字"
    
    return True, ""


@router.post("/login")
@login_rate_limit(max_attempts=5, window_seconds=300)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录 - 限制5分钟内最多5次尝试"""
    from datetime import datetime, timedelta
    
    # 查找用户
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 检查账户是否被锁定
    if user and user.locked_until and user.locked_until > datetime.utcnow():
        remaining = (user.locked_until - datetime.utcnow()).seconds // 60
        return error_response(403, f"账户已被锁定，请{remaining}分钟后重试")
    
    try:
        auth_service = AuthService()
        result = await auth_service.authenticate(form_data.username, form_data.password, db)
        
        # 登录成功，重置失败次数
        if user:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()
        
        return success_response(data=result.dict())
    except AuthenticationException as e:
        # 登录失败，增加失败次数
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            user.last_failed_login = datetime.utcnow()
            
            # 连续5次失败，锁定账户30分钟
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                db.commit()
                return error_response(403, "连续5次登录失败，账户已锁定30分钟")
            
            db.commit()
        
        return error_response(401, e.message)
    except Exception as e:
        import traceback
        print(f"Login error: {str(e)}")
        print(traceback.format_exc())
        return error_response(500, f"Internal server error: {str(e)}")


@router.post("/register")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """用户注册 - 带密码强度检查"""
    # 验证密码强度
    is_valid, error_msg = validate_password_strength(request.password)
    if not is_valid:
        return error_response(400, error_msg)
    
    try:
        auth_service = AuthService()
        user = await auth_service.register(request.username, request.password, request.name, db)
        # 手动构建响应数据，User 是 SQLAlchemy 模型，没有 dict() 方法
        return success_response(data={
            "id": str(user.id),
            "username": user.username,
            "name": user.name,
            "role": user.role
        })
    except Exception as e:
        return error_response(400, str(e))


@router.get("/me")
async def get_me(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    payload = decode_token(token)
    if not payload:
        return error_response(401, "Invalid token")
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return error_response(401, "User not found")
    
    return success_response(data={
        "id": str(user.id),
        "username": user.username,
        "name": user.name,
        "role": user.role
    })
