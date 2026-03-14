from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.services.enterprise_im import EnterpriseIMService

router = APIRouter(prefix="/enterprise-im", tags=["企业IM对接"])


class IMConfigRequest(BaseModel):
    platform: str  # wechat/dingtalk
    corp_id: Optional[str] = None
    corp_secret: Optional[str] = None
    app_key: Optional[str] = None
    app_secret: Optional[str] = None


class SendMessageRequest(BaseModel):
    user_ids: List[str]
    message: str


@router.post("/sync")
async def sync_organization(
    request: IMConfigRequest,
    current_user=Depends(require_permission("im:manage")),
    db: Session = Depends(get_db)
):
    """同步组织架构"""
    try:
        config = {}
        if request.platform == "wechat":
            config = {"corp_id": request.corp_id, "corp_secret": request.corp_secret}
        elif request.platform == "dingtalk":
            config = {"app_key": request.app_key, "app_secret": request.app_secret}
        
        result = EnterpriseIMService.sync_organization(request.platform, config, db)
        
        return success_response(data={
            "platform": request.platform,
            "departments": len(result["departments"]),
            "users": result["total_users"],
            "message": f"成功同步 {result['total_users']} 位成员"
        })
    except Exception as e:
        return error_response(500, f"同步失败: {str(e)}")


@router.post("/send")
async def send_message(
    request: SendMessageRequest,
    platform: str,
    config: IMConfigRequest,
    current_user=Depends(require_permission("im:manage"))
):
    """发送消息"""
    try:
        config_dict = {}
        if platform == "wechat":
            config_dict = {"corp_id": config.corp_id, "corp_secret": config.corp_secret}
        elif platform == "dingtalk":
            config_dict = {"app_key": config.app_key, "app_secret": config.app_secret}
        
        success = EnterpriseIMService.send_notification(platform, config_dict, request.user_ids, request.message)
        
        return success_response(data={
            "success": success,
            "message": "消息发送成功" if success else "消息发送失败"
        })
    except Exception as e:
        return error_response(500, f"发送失败: {str(e)}")


# 更多企业IM端点
@router.get("/config")
async def get_im_config(
    current_user=Depends(require_permission("im:read"))
):
    """企微配置"""
    return success_response(data={"config": {}})


@router.get("/messages")
async def get_messages(
    current_user=Depends(require_permission("im:read"))
):
    """企微消息"""
    return success_response(data={"items": []})


@router.get("/notifications")
async def get_notifications(
    current_user=Depends(require_permission("im:read"))
):
    """企微通知"""
    return success_response(data={"items": []})


@router.get("/approval-flows")
async def get_approval_flows(
    current_user=Depends(require_permission("im:read"))
):
    """企微审批流"""
    return success_response(data={"items": []})


@router.get("/contacts")
async def get_contacts(
    current_user=Depends(require_permission("im:read"))
):
    """企微通讯录"""
    return success_response(data={"items": []})
