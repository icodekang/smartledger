from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.exceptions import AuthenticationException
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import LoginResponse


class AuthService:
    """认证服务"""
    
    async def authenticate(self, username: str, password: str, db: Session) -> LoginResponse:
        """用户认证"""
        # 查询用户
        user = db.query(User).filter(User.username == username).first()
        
        # 验证用户存在且激活
        if not user or not user.is_active:
            raise AuthenticationException("Invalid username or password")
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            raise AuthenticationException("Invalid username or password")
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.commit()
        
        # 创建访问令牌
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return LoginResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": str(user.id),
                "username": user.username,
                "name": user.name,
                "role": user.role
            }
        )
    
    async def register(self, username: str, password: str, name: str, db: Session) -> User:
        """用户注册"""
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise Exception("用户名已存在")
        
        # 创建新用户，默认管理员角色
        user = User(
            id=uuid4(),
            username=username,
            password_hash=get_password_hash(password),
            name=name,
            role="admin",  # 默认管理员角色
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
