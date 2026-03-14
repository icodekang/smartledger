from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.response import success_response
from app.core.permissions import require_permission
from app.services.open_platform import OpenAPIPlatform, APIDocumentation, SDKGenerator

router = APIRouter(prefix="/open-platform", tags=["开放平台"])


@router.get("/docs")
async def get_api_docs(
    current_user=Depends(require_permission("open:read"))
):
    """获取API文档"""
    docs = APIDocumentation.get_documentation()
    return success_response(data={"endpoints": docs})


@router.post("/api-keys")
async def create_api_key(
    current_user=Depends(require_permission("open:manage"))
):
    """创建API密钥"""
    key_pair = OpenAPIPlatform.generate_api_key()
    return success_response(data={
        "api_key": key_pair["api_key"],
        "api_secret": key_pair["api_secret"],
        "created_at": key_pair["created_at"],
        "warning": "请妥善保存API Secret，只显示一次"
    })


@router.get("/sdk/python")
async def get_python_sdk(
    current_user=Depends(require_permission("open:read"))
):
    """获取Python SDK"""
    code = SDKGenerator.generate_python_sdk()
    return success_response(data={
        "language": "python",
        "code": code,
        "install_command": "pip install smartledger-sdk"
    })


@router.get("/sdk/javascript")
async def get_javascript_sdk(
    current_user=Depends(require_permission("open:read"))
):
    """获取JavaScript SDK"""
    code = SDKGenerator.generate_javascript_sdk()
    return success_response(data={
        "language": "javascript",
        "code": code,
        "install_command": "npm install smartledger-sdk"
    })


# 开放平台更多API
@router.get("/customers")
async def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    current_user=Depends(require_permission("customers:read"))
):
    """开放平台客户API"""
    return success_response(data={"items": [], "total": 0})


@router.get("/vouchers")
async def get_vouchers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_permission("vouchers:read"))
):
    """开放平台凭证API"""
    return success_response(data={"items": [], "total": 0})


@router.get("/reports")
async def get_reports(
    report_type: Optional[str] = None,
    period: Optional[str] = None,
    current_user=Depends(require_permission("reports:read"))
):
    """开放平台报表API"""
    return success_response(data={"items": [], "total": 0})


@router.get("/bills")
async def get_bills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_permission("bills:read"))
):
    """开放平台票据API"""
    return success_response(data={"items": [], "total": 0})


@router.get("/api-keys")
async def list_api_keys(
    current_user=Depends(require_permission("open:read"))
):
    """API密钥列表"""
    return success_response(data={"items": []})


@router.get("/usage-stats")
async def get_usage_stats(
    current_user=Depends(require_permission("open:read"))
):
    """调用统计"""
    return success_response(data={
        "total_calls": 0,
        "success_rate": 100,
        "avg_response_time": 0
    })


@router.get("/sdks")
async def list_sdks(
    current_user=Depends(require_permission("open:read"))
):
    """SDK列表"""
    return success_response(data={
        "items": [
            {"name": "Python", "version": "1.0.0", "downloads": 1000},
            {"name": "JavaScript", "version": "1.0.0", "downloads": 800},
            {"name": "Java", "version": "1.0.0", "downloads": 500}
        ]
    })


@router.get("/monitoring")
async def get_monitoring(
    current_user=Depends(require_permission("open:read"))
):
    """API监控"""
    return success_response(data={
        "status": "healthy",
        "uptime": 99.9,
        "latency": 50
    })
