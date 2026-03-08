from fastapi import APIRouter

from app.api.endpoints import (
    auth, files, vouchers, bills, bank_flows, audit, 
    customers, users, contracts, bank_accounts
)

router = APIRouter(prefix="/api/v1")

# 注册路由
router.include_router(auth.router)
router.include_router(files.router)
router.include_router(vouchers.router)
router.include_router(bills.router)
router.include_router(bank_flows.router)
router.include_router(audit.router)
router.include_router(customers.router)
router.include_router(users.router)
router.include_router(contracts.router)
router.include_router(bank_accounts.router)
