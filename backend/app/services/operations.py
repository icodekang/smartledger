"""
Webhook系统
TASK-OPEN-02: Webhook系统
"""
from typing import Dict, List, Optional
from datetime import datetime
import requests
import json
import hmac
import hashlib


class WebhookManager:
    """Webhook管理器"""
    
    # 支持的事件类型
    EVENT_TYPES = [
        "bill.created",      # 票据创建
        "bill.updated",      # 票据更新
        "voucher.created",   # 凭证创建
        "voucher.approved",  # 凭证审核
        "bank_flow.synced",  # 流水同步
        "tax.declaration.submitted",  # 纳税申报
    ]
    
    @staticmethod
    def generate_secret() -> str:
        """生成Webhook密钥"""
        import uuid
        return f"whsec_{uuid.uuid4().hex}"
    
    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """生成Webhook签名"""
        timestamp = str(int(datetime.utcnow().timestamp()))
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"
    
    @staticmethod
    def send_webhook(url: str, event: str, data: dict, secret: str) -> bool:
        """发送Webhook通知"""
        payload = json.dumps({
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })
        
        signature = WebhookManager.generate_signature(payload, secret)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Event-Type": event,
            "User-Agent": "SmartLedger-Webhook/1.0"
        }
        
        try:
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Webhook发送失败: {e}")
            return False


class PluginMarket:
    """插件市场"""
    
    # 内置插件列表
    PLUGINS = [
        {
            "id": "plugin_001",
            "name": "银行直连-工商银行",
            "description": "工商银行银企直连接口",
            "version": "1.0.0",
            "author": "SmartLedger",
            "category": "bank",
            "price": 0,
            "installed": True
        },
        {
            "id": "plugin_002",
            "name": "银行直连-建设银行",
            "description": "建设银行银企直连接口",
            "version": "1.0.0",
            "author": "SmartLedger",
            "category": "bank",
            "price": 0,
            "installed": True
        },
        {
            "id": "plugin_003",
            "name": "智能OCR识别",
            "description": "AI驱动的票据OCR识别",
            "version": "2.0.0",
            "author": "SmartLedger",
            "category": "ai",
            "price": 299,
            "installed": False
        },
        {
            "id": "plugin_004",
            "name": "金蝶K3对接",
            "description": "金蝶K3 ERP系统对接",
            "version": "1.5.0",
            "author": "SmartLedger",
            "category": "erp",
            "price": 499,
            "installed": False
        },
        {
            "id": "plugin_005",
            "name": "企业微信通知",
            "description": "企业微信消息推送",
            "version": "1.0.0",
            "author": "SmartLedger",
            "category": "notification",
            "price": 0,
            "installed": True
        }
    ]
    
    @classmethod
    def list_plugins(cls, category: str = None) -> List[Dict]:
        """获取插件列表"""
        if category:
            return [p for p in cls.PLUGINS if p["category"] == category]
        return cls.PLUGINS
    
    @classmethod
    def get_plugin(cls, plugin_id: str) -> Optional[Dict]:
        """获取插件详情"""
        for plugin in cls.PLUGINS:
            if plugin["id"] == plugin_id:
                return plugin
        return None


class MarketingTools:
    """营销工具系统"""
    
    @staticmethod
    def generate_promo_code() -> str:
        """生成优惠码"""
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return code
    
    @staticmethod
    def calculate_discount(amount: float, promo_code: str) -> float:
        """计算折扣"""
        # 简化的折扣逻辑
        discounts = {
            "WELCOME2024": 0.9,    # 9折
            "VIP50": 0.5,          # 5折
            "FREE30": 1.0,         # 免费30天
        }
        discount_rate = discounts.get(promo_code, 1.0)
        return amount * discount_rate


class CustomerSuccess:
    """客户成功系统"""
    
    @staticmethod
    def calculate_health_score(customer_data: Dict) -> Dict:
        """计算客户健康度评分"""
        # 健康度维度
        dimensions = {
            "usage_frequency": 30,    # 使用频率 (30%)
            "feature_adoption": 25,   # 功能使用 (25%)
            "data_quality": 20,       # 数据质量 (20%)
            "support_tickets": 15,    # 工单情况 (15%)
            "payment_status": 10      # 付费状态 (10%)
        }
        
        # 简化的评分逻辑
        scores = {
            "usage_frequency": min(customer_data.get("login_days_last_month", 0) / 20 * 100, 100),
            "feature_adoption": min(len(customer_data.get("used_features", [])) / 10 * 100, 100),
            "data_quality": 90 if customer_data.get("has_complete_data") else 60,
            "support_tickets": max(0, 100 - customer_data.get("support_tickets", 0) * 10),
            "payment_status": 100 if customer_data.get("payment_status") == "paid" else 50
        }
        
        # 加权总分
        total_score = sum(
            scores[dim] * weight / 100
            for dim, weight in dimensions.items()
        )
        
        return {
            "total_score": round(total_score),
            "dimension_scores": scores,
            "risk_level": "high" if total_score < 50 else "medium" if total_score < 75 else "low"
        }
    
    @staticmethod
    def predict_churn_risk(customer_data: Dict) -> Dict:
        """预测流失风险"""
        health = CustomerSuccess.calculate_health_score(customer_data)
        
        risk_factors = []
        if health["dimension_scores"]["usage_frequency"] < 30:
            risk_factors.append("使用频率低")
        if health["dimension_scores"]["payment_status"] < 80:
            risk_factors.append("付费异常")
        if health["dimension_scores"]["support_tickets"] < 50:
            risk_factors.append("工单问题多")
        
        return {
            "risk_score": 100 - health["total_score"],
            "risk_level": health["risk_level"],
            "risk_factors": risk_factors,
            "recommendations": [
                "安排客户成功经理跟进" if health["risk_level"] == "high" else "定期关怀"
            ]
        }


class Analytics:
    """运营数据分析"""
    
    @staticmethod
    def get_dashboard_metrics() -> Dict:
        """获取仪表盘指标"""
        return {
            "overview": {
                "total_customers": 150,
                "active_customers": 120,
                "new_customers_this_month": 15,
                "churned_customers": 2
            },
            "revenue": {
                "mrr": 45000,  # 月度经常性收入
                "arr": 540000,  # 年度经常性收入
                "this_month": 52000,
                "last_month": 48000,
                "growth_rate": 0.083
            },
            "usage": {
                "total_bills": 15000,
                "total_vouchers": 8500,
                "avg_bills_per_customer": 100,
                "active_users_today": 80
            },
            "health": {
                "avg_health_score": 78,
                "high_risk_customers": 5,
                "medium_risk_customers": 20,
                "low_risk_customers": 125
            }
        }
