from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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
)
:
    """获取JavaScript SDK"""
    code = SDKGenerator.generate_javascript_sdk()
    return success_response(data={
        "language": "javascript",
        "code": code,
        "install_command": "npm install smartledger-sdk"
    })
