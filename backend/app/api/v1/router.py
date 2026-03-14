from fastapi import APIRouter

from app.api.endpoints import (
    auth, files, vouchers, bills, bank_flows, audit, 
    customers, users, contracts, bank_accounts, ledger, reports,
    system, advanced, tax, erp_integrations, enterprise_im,
    operations, security, open_platform, ai_smart_booking, voucher_export,
    mobile, ai
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
router.include_router(ledger.router)
router.include_router(reports.router)
router.include_router(system.router)
router.include_router(advanced.router)
router.include_router(tax.router)
router.include_router(erp_integrations.router)
router.include_router(enterprise_im.router)
router.include_router(operations.router)
router.include_router(security.router)
router.include_router(open_platform.router)
router.include_router(ai_smart_booking.router)
router.include_router(voucher_export.router)
router.include_router(ai.router)
router.include_router(mobile.h5_router, prefix="/mobile")
router.include_router(mobile.miniapp_router, prefix="/mobile")
router.include_router(mobile.portal_router, prefix="/mobile")
