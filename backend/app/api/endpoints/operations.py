from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.core.response import success_response
from app.core.permissions import require_permission
from app.services.operations import WebhookManager, PluginMarket, MarketingTools, CustomerSuccess, Analytics

router = APIRouter(prefix="/operations", tags=["运营支持"])


# ========== Webhook系统 ==========

class WebhookCreateRequest(BaseModel):
    url: str
    events: List[str]
    secret: Optional[str] = None


@router.get("/webhooks/events")
async def get_webhook_events(
    current_user=Depends(require_permission("webhook:read"))
):
    """获取支持的Webhook事件"""
    return success_response(data={"events": WebhookManager.EVENT_TYPES})


@router.post("/webhooks/test")
async def test_webhook(
    url: str,
    event: str,
    current_user=Depends(require_permission("webhook:manage"))
):
    """测试Webhook"""
    secret = WebhookManager.generate_secret()
    success = WebhookManager.send_webhook(
        url, event, {"test": True, "timestamp": "2024-01-01T00:00:00"}, secret
    )
    return success_response(data={"success": success})


# ========== 插件市场 ==========

@router.get("/plugins")
async def list_plugins(
    category: Optional[str] = None,
    current_user=Depends(require_permission("plugin:read"))
):
    """获取插件列表"""
    plugins = PluginMarket.list_plugins(category)
    return success_response(data={"items": plugins})


@router.get("/plugins/{plugin_id}")
async def get_plugin(
    plugin_id: str,
    current_user=Depends(require_permission("plugin:read"))
):
    """获取插件详情"""
    plugin = PluginMarket.get_plugin(plugin_id)
    return success_response(data=plugin)


# ========== 营销工具 ==========

@router.post("/marketing/promo-code")
async def generate_promo_code(
    current_user=Depends(require_permission("marketing:manage"))
):
    """生成优惠码"""
    code = MarketingTools.generate_promo_code()
    return success_response(data={"promo_code": code})


@router.post("/marketing/calculate-discount")
async def calculate_discount(
    amount: float,
    promo_code: str,
    current_user=Depends(require_permission("marketing:read"))
):
    """计算折扣"""
    discounted = MarketingTools.calculate_discount(amount, promo_code)
    return success_response(data={
        "original_amount": amount,
        "discounted_amount": discounted,
        "discount": amount - discounted
    })


# ========== 客户成功 ==========

@router.post("/customer-success/health-score")
async def calculate_health_score(
    customer_data: dict,
    current_user=Depends(require_permission("customer_success:read"))
):
    """计算客户健康度"""
    score = CustomerSuccess.calculate_health_score(customer_data)
    return success_response(data=score)


@router.post("/customer-success/churn-risk")
async def predict_churn_risk(
    customer_data: dict,
    current_user=Depends(require_permission("customer_success:read"))
):
    """预测流失风险"""
    risk = CustomerSuccess.predict_churn_risk(customer_data)
    return success_response(data=risk)


# ========== 运营分析 ==========

@router.get("/analytics/dashboard")
async def get_dashboard_metrics(
    current_user=Depends(require_permission("analytics:read"))
):
    """获取仪表盘指标"""
    metrics = Analytics.get_dashboard_metrics()
    return success_response(data=metrics)
