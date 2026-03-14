"""
移动端专用API
H5、小程序、客户Portal专用接口
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

from app.core.database import get_db
from app.core.response import success_response
from app.core.permissions import require_permission

router = APIRouter(tags=["移动端API"])


# ===== H5专用API =====
h5_router = APIRouter(prefix="/h5", tags=["H5端"])

@h5_router.get("/dashboard")
async def h5_dashboard(
    current_user=Depends(require_permission("reports:read"))
):
    """H5首页仪表盘 - 简化版"""
    return success_response(data={
        "platform": "h5",
        "summary": {
            "bills_count": 0,
            "vouchers_count": 0,
            "pending_audit": 0
        },
        "quick_actions": [
            {"name": "扫码识票", "icon": "scan", "action": "/scan"},
            {"name": "记一笔", "icon": "add", "action": "/voucher/create"},
            {"name": "查余额", "icon": "balance", "action": "/reports/balance"},
            {"name": "看报表", "icon": "report", "action": "/reports"}
        ]
    })


@h5_router.get("/bills/recent")
async def h5_recent_bills(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user=Depends(require_permission("bills:read"))
):
    """H5最近票据"""
    return success_response(data={
        "platform": "h5",
        "items": [],
        "page": page,
        "page_size": page_size
    })


# ===== 小程序专用API =====
miniapp_router = APIRouter(prefix="/miniapp", tags=["小程序"])

@miniapp_router.get("/dashboard")
async def miniapp_dashboard(
    current_user=Depends(require_permission("reports:read"))
):
    """小程序首页"""
    return success_response(data={
        "platform": "miniapp",
        "features": [
            {"name": "拍照识票", "code": "camera"},
            {"name": "语音记账", "code": "voice"},
            {"name": "发票管理", "code": "invoices"},
            {"name": "智能报表", "code": "reports"}
        ]
    })


@miniapp_router.post("/voice/book")
async def miniapp_voice_book(
    audio_data: str,
    current_user=Depends(require_permission("bills:create"))
):
    """小程序语音记账"""
    return success_response(data={
        "platform": "miniapp",
        "result": {
            "success": True,
            "voucher_id": None
        }
    })


# ===== 客户Portal专用API =====
portal_router = APIRouter(prefix="/portal", tags=["客户Portal"])

@portal_router.get("/dashboard")
async def portal_dashboard(
    current_user=Depends(require_permission("reports:read"))
):
    """客户Portal首页"""
    return success_response(data={
        "platform": "portal",
        "modules": [
            {"name": "我的票据", "count": 0},
            {"name": "我的凭证", "count": 0},
            {"name": "纳税申报", "status": "pending"},
            {"name": "财务报表", "periods": []}
        ]
    })


@portal_router.get("/tax/status")
async def portal_tax_status(
    current_user=Depends(require_permission("reports:read"))
):
    """Portal纳税状态"""
    return success_response(data={
        "platform": "portal",
        "tax": {
            "vat": {"status": "pending", "due_date": None},
            "income": {"status": "pending", "due_date": None}
        }
    })


@portal_router.get("/reports/custom")
async def portal_custom_reports(
    report_type: str = Query(..., description="报表类型: balance/income/cash"),
    period: str = Query(..., description="期间: 2024-01"),
    current_user=Depends(require_permission("reports:read"))
):
    """Portal自定义报表"""
    return success_response(data={
        "platform": "portal",
        "report_type": report_type,
        "period": period,
        "data": {}
    })


# ===== H5更多API =====

@h5_router.get("/customers")
async def h5_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    keyword: Optional[str] = None,
    current_user=Depends(require_permission("customers:read"))
):
    """H5客户列表"""
    return success_response(data={
        "platform": "h5",
        "items": [],
        "page": page,
        "page_size": page_size,
        "total": 0
    })


@h5_router.get("/customers/{customer_id}")
async def h5_customer_detail(
    customer_id: str,
    current_user=Depends(require_permission("customers:read"))
):
    """H5客户详情"""
    return success_response(data={
        "platform": "h5",
        "customer": {
            "id": customer_id,
            "name": "客户名称",
            "bills_count": 0,
            "vouchers_count": 0,
            "balance": 0
        }
    })


@h5_router.get("/pending-tasks")
async def h5_pending_tasks(
    current_user=Depends(require_permission("bills:read"))
):
    """H5待办任务"""
    return success_response(data={
        "platform": "h5",
        "items": [
            {"id": "1", "type": "bill_approval", "title": "待审批票据", "count": 3},
            {"id": "2", "type": "voucher_approval", "title": "待审批凭证", "count": 5},
            {"id": "3", "type": "tax_filing", "title": "待纳税申报", "count": 1}
        ]
    })


@h5_router.get("/messages")
async def h5_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user=Depends(require_permission("notifications:read"))
):
    """H5消息列表"""
    return success_response(data={
        "platform": "h5",
        "items": [],
        "unread_count": 0
    })


@h5_router.get("/vouchers")
async def h5_vouchers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user=Depends(require_permission("vouchers:read"))
):
    """H5凭证列表"""
    return success_response(data={
        "platform": "h5",
        "items": [],
        "page": page
    })


@h5_router.get("/bank-flows")
async def h5_bank_flows(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user=Depends(require_permission("bank_flows:read"))
):
    """H5银行流水"""
    return success_response(data={
        "platform": "h5",
        "items": [],
        "page": page
    })


# ===== 小程序更多API =====

@miniapp_router.get("/invoices")
async def miniapp_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user=Depends(require_permission("bills:read"))
):
    """小程序发票列表"""
    return success_response(data={
        "platform": "miniapp",
        "items": [],
        "page": page
    })


@miniapp_router.post("/scan/recognize")
async def miniapp_scan_recognize(
    request: dict,
    current_user=Depends(require_permission("bills:create"))
):
    """小程序扫码识票"""
    return success_response(data={
        "platform": "miniapp",
        "result": {
            "success": True,
            "bill_data": {
                "invoice_code": "1234567890",
                "invoice_number": "12345678",
                "amount": 100.00
            }
        }
    })


@miniapp_router.get("/reports")
async def miniapp_reports(
    report_type: str = Query(..., description="报表类型"),
    period: str = Query(..., description="期间"),
    current_user=Depends(require_permission("reports:read"))
):
    """小程序报表查看"""
    return success_response(data={
        "platform": "miniapp",
        "report_type": report_type,
        "period": period,
        "data": {}
    })


@miniapp_router.get("/customers")
async def miniapp_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user=Depends(require_permission("customers:read"))
):
    """小程序客户列表"""
    return success_response(data={
        "platform": "miniapp",
        "items": [],
        "page": page
    })


@miniapp_router.get("/vouchers")
async def miniapp_vouchers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user=Depends(require_permission("vouchers:read"))
):
    """小程序凭证列表"""
    return success_response(data={
        "platform": "miniapp",
        "items": [],
        "page": page
    })


@miniapp_router.get("/tasks")
async def miniapp_tasks(
    current_user=Depends(require_permission("tasks:read"))
):
    """小程序待办"""
    return success_response(data={
        "platform": "miniapp",
        "items": []
    })


@miniapp_router.get("/settings")
async def miniapp_settings(
    current_user=Depends(require_permission("settings:read"))
):
    """小程序设置"""
    return success_response(data={
        "platform": "miniapp",
        "settings": {}
    })


@miniapp_router.get("/search")
async def miniapp_search(
    keyword: str = Query(..., description="搜索关键词"),
    current_user=Depends(require_permission("search:read"))
):
    """小程序搜索"""
    return success_response(data={
        "platform": "miniapp",
        "results": []
    })


@miniapp_router.get("/notifications")
async def miniapp_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user=Depends(require_permission("notifications:read"))
):
    """小程序通知"""
    return success_response(data={
        "platform": "miniapp",
        "items": [],
        "unread_count": 0
    })


# ===== Portal更多API =====

@portal_router.get("/bills")
async def portal_bills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user=Depends(require_permission("bills:read"))
):
    """Portal票据列表"""
    return success_response(data={
        "platform": "portal",
        "items": [],
        "total": 0
    })


@portal_router.get("/vouchers")
async def portal_vouchers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user=Depends(require_permission("vouchers:read"))
):
    """Portal凭证列表"""
    return success_response(data={
        "platform": "portal",
        "items": [],
        "total": 0
    })


@portal_router.get("/filing/calendar")
async def portal_filing_calendar(
    year: int = Query(2024),
    current_user=Depends(require_permission("tax:read"))
):
    """Portal纳税日历"""
    return success_response(data={
        "platform": "portal",
        "items": [
            {"month": "01", "tax_types": ["增值税", "附加税"], "due_date": "2024-02-15"},
            {"month": "04", "tax_types": ["企业所得税"], "due_date": "2024-05-15"},
            {"month": "07", "tax_types": ["增值税", "附加税"], "due_date": "2024-08-15"}
        ]
    })


@portal_router.get("/tax")
async def portal_tax(
    current_user=Depends(require_permission("tax:read"))
):
    """Portal税务"""
    return success_response(data={
        "platform": "portal",
        "items": []
    })


@portal_router.get("/messages")
async def portal_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user=Depends(require_permission("notifications:read"))
):
    """Portal消息"""
    return success_response(data={
        "platform": "portal",
        "items": [],
        "unread_count": 0
    })


@portal_router.get("/settings")
async def portal_settings(
    current_user=Depends(require_permission("settings:read"))
):
    """Portal设置"""
    return success_response(data={
        "platform": "portal",
        "settings": {}
    })


@portal_router.get("/invoices")
async def portal_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user=Depends(require_permission("bills:read"))
):
    """Portal发票"""
    return success_response(data={
        "platform": "portal",
        "items": [],
        "total": 0
    })


@portal_router.get("/profile")
async def portal_profile(
    current_user=Depends(require_permission("profile:read"))
):
    """Portal企业信息"""
    return success_response(data={
        "platform": "portal",
        "company": {
            "name": "企业名称",
            "tax_no": "税号",
            "tax_type": "一般纳税人",
            "service_period": {"start": "2024-01-01", "end": "2024-12-31"}
        }
    })
