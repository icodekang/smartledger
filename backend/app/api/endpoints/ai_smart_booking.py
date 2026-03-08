from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional

from app.core.database import get_db
from app.core.response import success_response
from app.core.permissions import require_permission
from app.services.smart_booking import SmartBookingEngine, IntelligentClassification, AnomalyDetector

router = APIRouter(prefix="/ai", tags=["AI智能"])


class SubjectMatchRequest(BaseModel):
    description: str


class VoucherGenerateRequest(BaseModel):
    bill_data: dict
    industry: str = "trade"


class AnomalyCheckRequest(BaseModel):
    bill_data: dict
    historical_avg: Optional[float] = None
    current_period: Optional[str] = None


# 科目智能匹配
@router.post("/match-subject")
async def match_subject(
    request: SubjectMatchRequest,
    current_user=Depends(require_permission("ai:use"))
):
    """智能科目匹配"""
    subject_code = SmartBookingEngine.auto_match_subject(request.description)
    
    subject_names = {
        "1001": "库存现金", "1002": "银行存款", "1122": "应收账款",
        "1403": "原材料", "1405": "库存商品", "1601": "固定资产",
        "2001": "短期借款", "2202": "应付账款", "2221": "应交税费",
        "4001": "实收资本", "5001": "生产成本", "6001": "主营业务收入",
        "6401": "主营业务成本", "6601": "销售费用", "6602": "管理费用",
        "6603": "财务费用"
    }
    
    return success_response(data={
        "subject_code": subject_code,
        "subject_name": subject_names.get(subject_code, "未知科目"),
        "confidence": 0.85 if subject_code else 0.0
    })


# 智能生成分录
@router.post("/generate-voucher")
async def generate_voucher(
    request: VoucherGenerateRequest,
    current_user=Depends(require_permission("ai:use"))
):
    """智能生成凭证分录"""
    entries = SmartBookingEngine.generate_voucher_entries(
        request.bill_data,
        request.industry
    )
    
    return success_response(data={
        "entries": entries,
        "industry": request.industry,
        "confidence": 0.8
    })


# 智能分类
@router.post("/classify")
async def classify_bill(
    bill_data: dict,
    current_user=Depends(require_permission("ai:use"))
):
    """智能分类票据"""
    result = IntelligentClassification.classify_bill(bill_data)
    
    return success_response(data=result)


# 异常检测
@router.post("/detect-anomaly")
async def detect_anomaly(
    request: AnomalyCheckRequest,
    current_user=Depends(require_permission("ai:use"))
):
    """异常检测"""
    anomalies = []
    
    # 金额异常
    if request.historical_avg:
        from decimal import Decimal
        amount = Decimal(str(request.bill_data.get("total_amount", 0)))
        avg = Decimal(str(request.historical_avg))
        result = AnomalyDetector.detect_amount_anomaly(amount, avg)
        if result:
            anomalies.append(result)
    
    # 跨期检测
    if request.current_period and request.bill_data.get("invoice_date"):
        result = AnomalyDetector.detect_period_anomaly(
            request.bill_data["invoice_date"],
            request.current_period
        )
        if result:
            anomalies.append(result)
    
    return success_response(data={
        "has_anomaly": len(anomalies) > 0,
        "anomalies": anomalies
    })


# 业务类型分析
@router.post("/analyze-business")
async def analyze_business(
    bill_list: List[dict],
    current_user=Depends(require_permission("ai:use"))
):
    """分析业务类型"""
    industry = SmartBookingEngine.analyze_business_type(bill_list)
    
    industries = {
        "trade": "贸易公司",
        "service": "服务公司",
        "manufacturing": "制造业"
    }
    
    return success_response(data={
        "industry_code": industry,
        "industry_name": industries.get(industry, "未知"),
        "confidence": 0.75
    })
