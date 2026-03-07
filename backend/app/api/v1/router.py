from fastapi import APIRouter

from app.api.endpoints import auth, files, vouchers, bills, bank_flows, audit

router = APIRouter(prefix="/api/v1")

# 注册路由
router.include_router(auth.router)
router.include_router(files.router)
router.include_router(vouchers.router)
router.include_router(bills.router)
router.include_router(bank_flows.router)
router.include_router(audit.router)
