"""用户管理API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.response import success_response
from app.core.permissions import require_permission
from app.models.user import User

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.get("")
async def list_users(
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(require_permission("users:read")),
    db: Session = Depends(get_db)
):
    """用户列表"""
    skip = (page - 1) * page_size
    users = db.query(User).offset(skip).limit(page_size).all()
    total = db.query(User).count()
    
    items = [{
        "id": str(u.id),
        "username": u.username,
        "name": u.name,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else ""
    } for u in users]
    
    return success_response(data={"items": items, "total": total})

@router.post("")
async def create_user(
    request: dict,
    current_user=Depends(require_permission("users:create")),
    db: Session = Depends(get_db)
):
    """创建用户"""
    import uuid
    from app.core.security import get_password_hash
    
    user = User(
        id=uuid.uuid4(),
        username=request["username"],
        password_hash=get_password_hash(request["password"]),
        name=request.get("name"),
        role=request.get("role", "viewer"),
        is_active=True
    )
    db.add(user)
    db.commit()
    return success_response(data={"id": str(user.id), "message": "用户创建成功"})

@router.put("/{user_id}")
async def update_user(
    user_id: str,
    request: dict,
    current_user=Depends(require_permission("users:update")),
    db: Session = Depends(get_db)
):
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from app.core.response import error_response
        return error_response(404, "用户不存在")
    
    if "name" in request:
        user.name = request["name"]
    if "role" in request:
        user.role = request["role"]
    if "is_active" in request:
        user.is_active = request["is_active"]
    
    db.commit()
    return success_response(data={"message": "用户更新成功"})

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user=Depends(require_permission("users:delete")),
    db: Session = Depends(get_db)
):
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from app.core.response import error_response
        return error_response(404, "用户不存在")
    
    db.delete(user)
    db.commit()
    return success_response(data={"message": "用户删除成功"})
