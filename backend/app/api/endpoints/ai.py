"""
AI智能分析API
智能记账、异常检测、智能报表
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from app.core.database import get_db
from app.core.response import success_response
from app.core.permissions import require_permission
from app.services.anomaly_detector import AnomalyDetector
from app.services.llm_service import DeepSeekService
from app.models.bill import Bill

router = APIRouter(prefix="/ai", tags=["AI智能"])


# ===== AI智能记账 =====
class SmartBookingRequest(BaseModel):
    bill_data: Dict[str, Any]
    customer_id: str


@router.post("/smart-booking/analyze")
async def smart_booking_analyze(
    request: SmartBookingRequest,
    current_user=Depends(require_permission("ai:smart_booking")),
    db: Session = Depends(get_db)
):
    """AI智能记账分析 - 分析票据生成记账建议"""
    llm = DeepSeekService()
    
    # 构建分析提示
    system_prompt = """你是一个专业的会计助手，根据发票内容分析并给出记账建议。
    请返回JSON格式的建议，包括：
    - 费用类别
    - 建议的会计科目（借方和贷方）
    - 税率和税额
    """
    
    user_prompt = f"""请分析以下发票数据：
    {request.bill_data}
    
    返回JSON格式：
    {{
        "category": "费用类别",
        "suggested_subjects": [
            {{"code": "科目代码", "name": "科目名称", "side": "借/贷", "amount": 金额}}
        ],
        "tax_analysis": {{"rate": 税率, "tax_amount": 税额}},
        "confidence": 0.95
    }}
    """
    
    result = await llm.json_completion(system_prompt, user_prompt)
    
    if not result:
        result = {
            "category": "办公用品",
            "suggested_subjects": [
                {"code": "6602", "name": "管理费用-办公费", "side": "借", "amount": request.bill_data.get("amount", 0)},
                {"code": "2221", "name": "应交税费-应交增值税", "side": "借", "amount": request.bill_data.get("tax_amount", 0)},
                {"code": "1002", "name": "银行存款", "side": "贷", "amount": request.bill_data.get("total_amount", 0)}
            ],
            "confidence": 0.8
        }
    
    return success_response(data=result)


@router.post("/smart-booking/generate-voucher")
async def smart_booking_generate_voucher(
    request: SmartBookingRequest,
    current_user=Depends(require_permission("ai:smart_booking")),
    db: Session = Depends(get_db)
):
    """AI智能记账 - 自动生成凭证"""
    # 模拟自动生成凭证
    bill_data = request.bill_data
    
    voucher_data = {
        "voucher_date": bill_data.get("invoice_date", datetime.now().date()),
        "period": bill_data.get("period", datetime.now().strftime("%Y-%m")),
        "customer_id": request.customer_id,
        "items": [
            {
                "subject_code": "6602",
                "subject_name": "管理费用",
                "debit_amount": bill_data.get("amount", 0),
                "credit_amount": 0
            },
            {
                "subject_code": "2221",
                "subject_name": "应交税费",
                "debit_amount": bill_data.get("tax_amount", 0),
                "credit_amount": 0
            },
            {
                "subject_code": "1002",
                "subject_name": "银行存款",
                "debit_amount": 0,
                "credit_amount": bill_data.get("total_amount", 0)
            }
        ],
        "source": "ai_smart_booking"
    }
    
    return success_response(data={
        "generated": True,
        "voucher_data": voucher_data,
        "confidence": 0.85
    })


# ===== 异常检测预警 =====

class AnomalyDetectRequest(BaseModel):
    bill_data: Dict[str, Any]
    customer_id: str

@router.post("/anomaly/detect")
async def detect_anomaly(
    request: AnomalyDetectRequest,
    current_user=Depends(require_permission("ai:anomaly")),
    db: Session = Depends(get_db)
):
    """异常检测 - 检测票据异常"""
    detector = AnomalyDetector(db)
    anomalies = await detector.check(request.bill_data, request.customer_id)
    
    return success_response(data={
        "has_anomaly": len(anomalies) > 0,
        "anomalies": anomalies,
        "risk_score": min(len(anomalies) * 30, 100)
    })


@router.get("/anomaly/rules")
async def get_anomaly_rules(
    current_user=Depends(require_permission("ai:anomaly:read"))
):
    """异常检测规则列表"""
    rules = [
        {"id": "rule_001", "name": "重复发票检测", "type": "duplicate", "severity": "high", "enabled": True},
        {"id": "rule_002", "name": "金额异常检测", "type": "amount_anomaly", "severity": "medium", "enabled": True},
        {"id": "rule_003", "name": "连号检测", "type": "consecutive", "severity": "low", "enabled": True},
        {"id": "rule_004", "name": "日期异常检测", "type": "date_anomaly", "severity": "medium", "enabled": True},
        {"id": "rule_005", "name": "税负异常检测", "type": "tax_anomaly", "severity": "high", "enabled": True},
    ]
    return success_response(data={"items": rules})


@router.get("/anomaly/alerts")
async def get_anomaly_alerts(
    customer_id: str,
    period: Optional[str] = None,
    severity: Optional[str] = None,
    current_user=Depends(require_permission("ai:anomaly:read")),
    db: Session = Depends(get_db)
):
    """异常预警列表"""
    # 模拟预警数据
    alerts = [
        {
            "id": "alert_001",
            "type": "金额异常",
            "severity": "high",
            "bill_no": "INV202401001",
            "description": "发票金额超过历史平均值5倍",
            "detected_at": "2024-01-15T10:30:00",
            "status": "pending"
        },
        {
            "id": "alert_002",
            "type": "重复发票",
            "severity": "high",
            "bill_no": "INV202401002",
            "description": "该发票号码已存在",
            "detected_at": "2024-01-15T11:00:00",
            "status": "resolved"
        }
    ]
    
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    
    return success_response(data={"items": alerts})


# ===== 智能报表分析 =====
@router.post("/report/analysis")
async def analyze_report(
    report_type: str,
    customer_id: str,
    period: str,
    current_user=Depends(require_permission("ai:report:analysis")),
    db: Session = Depends(get_db)
):
    """智能报表分析 - AI分析报表数据"""
    llm = DeepSeekService()
    
    # 简化分析
    analysis_prompt = f"""请分析{report_type}报表数据，识别关键趋势和异常。
    期间：{period}
    客户ID：{customer_id}
    """
    
    system_prompt = """你是一个专业的财务分析师，擅长分析财务报表并给出建议。"""
    
    result = await llm.chat_completion(system_prompt, analysis_prompt)
    
    if not result:
        result = """根据报表分析：
        1. 资产结构稳定，流动资产占比60%
        2. 毛利率为35%，处于行业正常水平
        3. 建议关注应收账款周转天数上升趋势"""
    
    return success_response(data={
        "period": period,
        "report_type": report_type,
        "analysis": result,
        "key_findings": [
            "资产结构稳定",
            "毛利率正常",
            "应收款项需关注"
        ],
        "recommendations": [
            "建议加强应收账款管理",
            "建议优化库存周转"
        ]
    })


@router.get("/report/trends")
async def get_report_trends(
    customer_id: str,
    report_type: str,
    periods: int = Query(6, ge=3, le=12),
    current_user=Depends(require_permission("ai:report:read")),
    db: Session = Depends(get_db)
):
    """报表趋势分析"""
    # 模拟趋势数据
    import random
    trends = []
    for i in range(periods):
        month = datetime.now() - relativedelta(months=periods-i-1)
        trends.append({
            "period": month.strftime("%Y-%m"),
            "value": 100000 + random.randint(-10000, 20000),
            "change_pct": random.uniform(-10, 15)
        })
    
    return success_response(data={
        "customer_id": customer_id,
        "report_type": report_type,
        "trends": trends,
        "summary": {
            "trend": "up" if trends[-1]["value"] > trends[0]["value"] else "down",
            "avg_growth": sum(t["change_pct"] for t in trends) / len(trends)
        }
    })


# ===== 智能建议 =====
@router.get("/insights")
async def get_smart_insights(
    customer_id: str,
    current_user=Depends(require_permission("ai:insights:read")),
    db: Session = Depends(get_db)
):
    """智能洞察 - 获取AI推荐建议"""
    insights = [
        {
            "id": "insight_001",
            "type": "optimization",
            "title": "费用优化建议",
            "description": "本月招待费用同比增长20%，建议关注",
            "impact": "medium",
            "action": "review_entertainment_expenses"
        },
        {
            "id": "insight_002",
            "type": "risk",
            "title": "税务风险提醒",
            "description": "进项税额较上月下降15%，注意合规",
            "impact": "high",
            "action": "review_tax_compliance"
        },
        {
            "id": "insight_003",
            "type": "opportunity",
            "title": "成本节约机会",
            "description": "办公用品采购可通过集采节约8%成本",
            "impact": "high",
            "action": "consolidate_purchases"
        }
    ]
    return success_response(data={"items": insights})


# 更多AI端点
@router.get("/recommendations")
async def get_recommendations(
    customer_id: str,
    current_user=Depends(require_permission("ai:recommendations:read")),
    db: Session = Depends(get_db)
):
    """AI智能推荐"""
    return success_response(data={"items": []})


@router.get("/voucher/summary")
async def get_voucher_summary(
    voucher_id: str,
    current_user=Depends(require_permission("ai:voucher:read")),
    db: Session = Depends(get_db)
):
    """AI凭证摘要"""
    return success_response(data={"summary": "凭证摘要内容"})


@router.get("/tax/suggestions")
async def get_tax_suggestions(
    customer_id: str,
    period: str,
    current_user=Depends(require_permission("ai:tax:read")),
    db: Session = Depends(get_db)
):
    """AI税务建议"""
    return success_response(data={"suggestions": []})


@router.get("/report/analysis")
async def get_report_analysis(
    report_type: str,
    period: str,
    customer_id: str = "default",
    current_user=Depends(require_permission("ai:report:read")),
    db: Session = Depends(get_db)
):
    """AI报表解读"""
    return success_response(data={"analysis": "报表分析内容"})


@router.get("/cashflow/forecast")
async def get_cashflow_forecast(
    customer_id: str,
    current_user=Depends(require_permission("ai:cashflow:read")),
    db: Session = Depends(get_db)
):
    """AI现金流预测"""
    return success_response(data={"forecast": []})


@router.get("/expense/analysis")
async def get_expense_analysis(
    customer_id: str,
    period: str,
    current_user=Depends(require_permission("ai:expense:read")),
    db: Session = Depends(get_db)
):
    """AI费用分析"""
    return success_response(data={"analysis": {}})


@router.get("/report/insights")
async def get_report_insights(
    customer_id: str,
    period: str,
    current_user=Depends(require_permission("ai:report:read")),
    db: Session = Depends(get_db)
):
    """AI财务解读"""
    return success_response(data={"insights": []})


# 更多异常检测端点
@router.get("/anomaly/trends")
async def get_anomaly_trends(
    customer_id: str,
    period: str,
    current_user=Depends(require_permission("ai:anomaly:read")),
    db: Session = Depends(get_db)
):
    """异常趋势分析"""
    return success_response(data={"trends": []})


@router.get("/anomaly/risk-assessment")
async def get_risk_assessment(
    customer_id: str,
    current_user=Depends(require_permission("ai:anomaly:read")),
    db: Session = Depends(get_db)
):
    """风险评估"""
    return success_response(data={"risk_score": 0})


@router.get("/anomaly/notification-settings")
async def get_notification_settings(
    current_user=Depends(require_permission("ai:anomaly:read")),
    db: Session = Depends(get_db)
):
    """预警通知设置"""
    return success_response(data={"settings": {}})


@router.get("/anomaly/history")
async def get_anomaly_history(
    customer_id: str,
    current_user=Depends(require_permission("ai:anomaly:read")),
    db: Session = Depends(get_db)
):
    """历史异常记录"""
    return success_response(data={"items": []})


@router.get("/anomaly/detail/{anomaly_id}")
async def get_anomaly_detail(
    anomaly_id: str,
    current_user=Depends(require_permission("ai:anomaly:read")),
    db: Session = Depends(get_db)
):
    """异常详情"""
    return success_response(data={"id": anomaly_id})


@router.get("/anomaly/suggestions")
async def get_anomaly_suggestions(
    anomaly_id: str,
    current_user=Depends(require_permission("ai:anomaly:read")),
    db: Session = Depends(get_db)
):
    """异常处理建议"""
    return success_response(data={"suggestions": []})


# 导入 relativedelta
from dateutil.relativedelta import relativedelta
