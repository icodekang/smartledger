from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.exceptions import AuthenticationException
from app.core.security import decode_token
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        auth_service = AuthService()
        result = await auth_service.authenticate(form_data.username, form_data.password, db)
        return success_response(data=result.dict())
    except AuthenticationException as e:
        return error_response(401, e.message)


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
