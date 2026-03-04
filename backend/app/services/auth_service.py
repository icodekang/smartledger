from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token
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
