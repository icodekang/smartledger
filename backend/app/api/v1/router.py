from fastapi import APIRouter

from app.api.endpoints import auth, users, files

router = APIRouter(prefix="/api/v1")

# 注册路由
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(files.router)
