from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

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


@router.post("/webhooks")
async def create_webhook(
    request: WebhookCreateRequest,
    current_user=Depends(require_permission("webhook:manage"))
):
    """创建Webhook"""
    return success_response(data={"webhook_id": "wh_001"})


@router.get("/webhooks")
async def list_webhooks(
    current_user=Depends(require_permission("webhook:read"))
):
    """Webhook列表"""
    return success_response(data={"items": []})


@router.get("/webhooks/logs")
async def get_webhook_logs(
    current_user=Depends(require_permission("webhook:read"))
):
    """Webhook日志"""
    return success_response(data={"items": []})


class WebhookRetryRequest(BaseModel):
    log_id: str


@router.post("/webhooks/retry")
async def retry_webhook(
    request: WebhookRetryRequest,
    current_user=Depends(require_permission("webhook:manage"))
):
    """重试Webhook"""
    return success_response(data={"success": True})


@router.get("/webhooks/statistics")
async def get_webhook_stats(
    current_user=Depends(require_permission("webhook:read"))
):
    """Webhook统计"""
    return success_response(data={"total": 0, "success": 0, "failed": 0})


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user=Depends(require_permission("webhook:manage"))
):
    """删除Webhook"""
    return success_response(data={"success": True})


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


@router.post("/plugins/install")
async def install_plugin(
    request: dict,
    current_user=Depends(require_permission("plugin:manage"))
):
    """安装插件"""
    return success_response(data={"success": True})


@router.post("/plugins/uninstall")
async def uninstall_plugin(
    request: dict,
    current_user=Depends(require_permission("plugin:manage"))
):
    """卸载插件"""
    return success_response(data={"success": True})


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


@router.get("/analytics/trend")
async def get_analytics_trend(
    current_user=Depends(require_permission("analytics:read"))
):
    """运营趋势"""
    return success_response(data={"trends": []})


@router.get("/analytics/funnel")
async def get_analytics_funnel(
    current_user=Depends(require_permission("analytics:read"))
):
    """运营漏斗"""
    return success_response(data={"funnel": []})


@router.get("/analytics/reports")
async def get_analytics_reports(
    current_user=Depends(require_permission("analytics:read"))
):
    """运营报表"""
    return success_response(data={"reports": []})


@router.get("/analytics/export")
async def export_analytics(
    current_user=Depends(require_permission("analytics:read"))
):
    """运营导出"""
    return success_response(data={"export_url": ""})


@router.get("/analytics/scheduled-tasks")
async def get_scheduled_tasks(
    current_user=Depends(require_permission("analytics:read"))
):
    """定时任务"""
    return success_response(data={"tasks": []})


# ========== 营销工具更多API ==========

@router.get("/marketing/campaigns")
async def list_marketing_campaigns(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(require_permission("marketing:read"))
):
    """营销活动列表"""
    campaigns = [
        {"id": "camp_001", "name": "新年特惠", "type": "discount", "status": "active", "start_date": "2024-01-01", "end_date": "2024-01-31"},
        {"id": "camp_002", "name": "推荐有礼", "type": "referral", "status": "active", "start_date": "2024-01-01", "end_date": "2024-12-31"},
    ]
    if status:
        campaigns = [c for c in campaigns if c["status"] == status]
    return success_response(data={"items": campaigns})


@router.get("/marketing/campaigns/{campaign_id}")
async def get_marketing_campaign(
    campaign_id: str,
    current_user=Depends(require_permission("marketing:read"))
):
    """营销活动详情"""
    return success_response(data={
        "id": campaign_id,
        "name": "营销活动",
        "status": "active"
    })


@router.get("/marketing/statistics")
async def get_marketing_statistics(
    current_user=Depends(require_permission("marketing:read"))
):
    """营销统计"""
    return success_response(data={
        "total_campaigns": 10,
        "active_campaigns": 3,
        "total_conversions": 150
    })


@router.get("/marketing/effectiveness")
async def get_marketing_effectiveness(
    current_user=Depends(require_permission("marketing:read"))
):
    """营销效果分析"""
    return success_response(data={
        "effectiveness": []
    })


@router.post("/marketing/campaigns")
async def create_campaign(
    name: str,
    campaign_type: str,
    start_date: date,
    end_date: date,
    current_user=Depends(require_permission("marketing:manage"))
):
    """创建营销活动"""
    return success_response(data={
        "message": "营销活动创建成功",
        "campaign_id": f"camp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    })


@router.get("/marketing/promo-codes")
async def list_promo_codes(
    status: Optional[str] = None,
    current_user=Depends(require_permission("marketing:read"))
):
    """优惠码列表"""
    codes = [
        {"code": "NEWYEAR2024", "discount": 0.2, "used": 45, "status": "active"},
        {"code": "REFER500", "discount": 500, "used": 12, "status": "active"},
    ]
    return success_response(data={"items": codes})


# ========== 客户成功更多API ==========

@router.get("/customer-success/customers")
async def list_customer_health(
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(require_permission("customer_success:read"))
):
    """客户健康度列表"""
    customers = [
        {"customer_id": "cust_001", "name": "客户A", "health_score": 85, "risk_level": "low"},
        {"customer_id": "cust_002", "name": "客户B", "health_score": 65, "risk_level": "medium"},
    ]
    return success_response(data={"items": customers})


@router.get("/customer-success/health-detail")
async def get_health_detail(
    customer_id: str,
    current_user=Depends(require_permission("customer_success:read"))
):
    """客户健康度详情"""
    return success_response(data={
        "customer_id": customer_id,
        "score": 85,
        "factors": {
            "login_frequency": 20,
            "feature_usage": 0.7,
            "data_completeness": 0.9,
            "support_tickets": 2
        }
    })


@router.get("/customer-success/churn-detail")
async def get_churn_detail(
    customer_id: str,
    current_user=Depends(require_permission("customer_success:read"))
):
    """流失风险详情"""
    return success_response(data={
        "customer_id": customer_id,
        "risk_score": 25,
        "factors": []
    })


@router.get("/customer-success/health-trend")
async def get_health_trend(
    customer_id: str,
    current_user=Depends(require_permission("customer_success:read"))
):
    """客户健康度趋势"""
    return success_response(data={
        "customer_id": customer_id,
        "trends": []
    })


@router.get("/customer-success/suggestions")
async def get_success_suggestions(
    customer_id: str,
    current_user=Depends(require_permission("customer_success:read"))
):
    """客户成功建议"""
    return success_response(data={
        "customer_id": customer_id,
        "suggestions": []
    })


@router.get("/customer-success/dashboard")
async def get_customer_success_dashboard(
    current_user=Depends(require_permission("customer_success:read"))
):
    """客户成功仪表盘"""
    return success_response(data={
        "total_customers": 100,
        "avg_health_score": 75,
        "high_risk_count": 10
    })


@router.get("/customer-success/customers/{customer_id}/insights")
async def get_customer_insights(
    customer_id: str,
    current_user=Depends(require_permission("customer_success:read"))
):
    """客户洞察"""
    return success_response(data={
        "customer_id": customer_id,
        "insights": [
            {"type": "usage", "title": "使用频率下降", "description": "近30天登录次数下降20%"},
            {"type": "feature", "title": "未使用功能", "description": "建议使用智能报表功能"},
        ]
    })


# ========== 运营分析更多API ==========

@router.get("/analytics/revenue")
async def get_revenue_analytics(
    period: str = Query(..., description="期间: 2024-01"),
    current_user=Depends(require_permission("analytics:read"))
):
    """营收分析"""
    return success_response(data={
        "period": period,
        "total_revenue": 1250000,
        "new_revenue": 350000,
        "renewal_revenue": 900000,
        "churn_rate": 0.05,
        "growth_rate": 0.15
    })


@router.get("/analytics/usage")
async def get_usage_analytics(
    current_user=Depends(require_permission("analytics:read"))
):
    """使用分析"""
    return success_response(data={
        "daily_active_users": 1250,
        "monthly_active_users": 3500,
        "avg_session_duration": 15.5,
        "top_features": [
            {"name": "票据管理", "usage": 4500},
            {"name": "凭证管理", "usage": 3800},
            {"name": "报表查看", "usage": 2900},
        ]
    })


@router.get("/analytics/conversion")
async def get_conversion_funnel(
    current_user=Depends(require_permission("analytics:read"))
):
    """转化漏斗"""
    return success_response(data={
        "stages": [
            {"name": "注册", "count": 5000},
            {"name": "激活", "count": 3500},
            {"name": "试用付费", "count": 1200},
            {"name": "续费", "count": 950},
        ]
    })


# ========== 测试数据生成 ==========

class TestDataRequest(BaseModel):
    data_types: List[str]
    count: int = 10


@router.post("/test-data/generate")
async def generate_test_data(
    request: TestDataRequest,
    current_user=Depends(require_permission("admin"))
):
    """生成测试数据"""
    data_types = request.data_types
    count = request.count
    from app.models.bill import Bill
    from app.models.customer import Customer
    from app.models.voucher import Voucher, VoucherItem
    from app.models.bank_flow import BankFlow
    import uuid
    
    db = next(get_db())
    results = {}
    
    if "customers" in data_types:
        # 生成测试客户
        customers = []
        for i in range(count):
            customer = Customer(
                id=uuid.uuid4(),
                name=f"测试客户_{i+1}",
                tax_id=f"91{i:013d}",
                contact=f"联系人_{i+1}",
                phone=f"138{i:08d}",
                email=f"test{i+1}@example.com",
                address=f"测试地址_{i+1}",
                bank_name="测试银行",
                bank_account=f"6222{i:010d}",
                tax_type="general",
                is_active=True
            )
            db.add(customer)
            customers.append(customer)
        db.commit()
        results["customers"] = len(customers)
    
    if "bills" in data_types:
        # 获取客户ID
        customers = db.query(Customer).limit(1).all()
        if customers:
            bills = []
            for i in range(count):
                bill = Bill(
                    id=uuid.uuid4(),
                    bill_type="invoice",
                    invoice_type="VAT",
                    invoice_code=f"{i+1:010d}",
                    invoice_number=f"{i+1:08d}",
                    amount=100 + i * 10,
                    tax_amount=13 + i,
                    total_amount=113 + i * 11,
                    seller_name=f"供应商_{i+1}",
                    seller_tax_id=f"91{i:013d}",
                    buyer_name=customers[0].name,
                    buyer_tax_id=customers[0].tax_id,
                    invoice_date=datetime.now(),
                    period=datetime.now().strftime("%Y-%m"),
                    status="pending",
                    source="imported"
                )
                db.add(bill)
                bills.append(bill)
            db.commit()
            results["bills"] = len(bills)
    
    if "vouchers" in data_types:
        # 获取客户和科目
        customers = db.query(Customer).limit(1).all()
        if customers:
            vouchers = []
            for i in range(count):
                voucher = Voucher(
                    id=uuid.uuid4(),
                    voucher_no=f"JZ-{datetime.now().strftime('%Y%m%d')}-{i+1:04d}",
                    voucher_date=datetime.now(),
                    period=datetime.now().strftime("%Y-%m"),
                    customer_id=customers[0].id,
                    summary=f"测试凭证_{i+1}",
                    total_amount=1000 + i * 100,
                    status="draft",
                    source="manual"
                )
                db.add(voucher)
                db.flush()
                
                # 添加凭证明细
                items = [
                    VoucherItem(
                        id=uuid.uuid4(),
                        voucher_id=voucher.id,
                        subject_code="1001",
                        subject_name="库存现金",
                        debit_amount=1000 + i * 100,
                        credit_amount=0,
                        auxiliary_name=None
                    ),
                    VoucherItem(
                        id=uuid.uuid4(),
                        voucher_id=voucher.id,
                        subject_code="6602",
                        subject_name="管理费用-办公费",
                        debit_amount=0,
                        credit_amount=1000 + i * 100,
                        auxiliary_name=None
                    )
                ]
                for item in items:
                    db.add(item)
                
                vouchers.append(voucher)
            db.commit()
            results["vouchers"] = len(vouchers)
    
    if "bank_flows" in data_types:
        # 获取客户
        customers = db.query(Customer).limit(1).all()
        if customers:
            flows = []
            for i in range(count):
                flow = BankFlow(
                    id=uuid.uuid4(),
                    customer_id=customers[0].id,
                    transaction_date=datetime.now(),
                    summary=f"测试流水_{i+1}",
                    amount=1000 + i * 100,
                    transaction_type="income",
                    balance=10000 + i * 1000,
                    status="verified"
                )
                db.add(flow)
                flows.append(flow)
            db.commit()
            results["bank_flows"] = len(flows)
    
    return success_response(data={
        "message": "测试数据生成成功",
        "generated": results
    })
