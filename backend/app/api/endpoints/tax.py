from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.tax import TaxAuth, TaxDeclaration
from app.models.voucher import Voucher
from app.models.customer import Customer
from app.services.tax_service import ETaxService, TaxCalculator, SUPPORTED_TAX_AREAS

router = APIRouter(prefix="/tax", tags=["税务管理"])


class TaxAuthCreateRequest(BaseModel):
    tax_no: str
    tax_area: str
    etax_username: str
    etax_password: str


class InvoiceVerifyRequest(BaseModel):
    invoice_code: str
    invoice_number: str
    issue_date: str


class DeclarationGenerateRequest(BaseModel):
    period: str
    tax_type: str


class DeclarationSubmitRequest(BaseModel):
    declaration_id: str


# 获取支持的税务地区
@router.get("/areas")
async def get_tax_areas(
    current_user=Depends(require_permission("tax:read"))
):
    """获取支持的税务地区"""
    return success_response(data={"items": SUPPORTED_TAX_AREAS})


# 添加税务授权
@router.post("/auths")
async def create_tax_auth(
    request: TaxAuthCreateRequest,
    current_user=Depends(require_permission("tax:manage")),
    db: Session = Depends(get_db)
):
    """添加税务授权"""
    # 检查是否已存在
    exists = db.query(TaxAuth).filter(
        TaxAuth.customer_id == current_user.customer_id,
        TaxAuth.tax_no == request.tax_no
    ).first()
    
    if exists:
        return error_response(400, "该税号已存在")
    
    # 尝试登录电子税务局
    service = ETaxService(request.tax_area)
    try:
        login_result = service.login(
            request.tax_no,
            request.etax_username,
            request.etax_password
        )
        
        # 创建授权记录
        auth = TaxAuth(
            id=uuid.uuid4(),
            customer_id=current_user.customer_id,
            tax_no=request.tax_no,
            tax_area=request.tax_area,
            etax_username=request.etax_username,
            etax_password_encrypted=request.etax_password,  # 实际应加密
            auth_status="authorized",
            auth_token=login_result["access_token"],
            auth_expires_at=datetime.utcnow() + datetime.timedelta(seconds=login_result["expires_in"])
        )
        
        db.add(auth)
        db.commit()
        
        return success_response(data={
            "id": str(auth.id),
            "tax_no": auth.tax_no,
            "taxpayer_name": login_result["taxpayer_name"],
            "message": "税务授权成功"
        })
    except Exception as e:
        return error_response(400, f"授权失败: {str(e)}")


# 获取税务授权列表
@router.get("/auths")
async def list_tax_auths(
    current_user=Depends(require_permission("tax:read")),
    db: Session = Depends(get_db)
):
    """获取税务授权列表"""
    auths = db.query(TaxAuth).filter(
        TaxAuth.customer_id == current_user.customer_id,
        TaxAuth.is_enabled == True
    ).all()
    
    items = []
    for auth in auths:
        items.append({
            "id": str(auth.id),
            "tax_no": auth.tax_no,
            "tax_area": auth.tax_area,
            "auth_status": auth.auth_status,
            "auth_expires_at": auth.auth_expires_at.isoformat() if auth.auth_expires_at else None,
            "created_at": auth.created_at.isoformat() if auth.created_at else None
        })
    
    return success_response(data={"items": items})


# 发票查验
@router.post("/invoices/verify")
async def verify_invoice(
    request: InvoiceVerifyRequest,
    current_user=Depends(require_permission("tax:read")),
    db: Session = Depends(get_db)
):
    """发票查验"""
    # 获取客户税务授权
    tax_auth = db.query(TaxAuth).filter(
        TaxAuth.customer_id == current_user.customer_id,
        TaxAuth.auth_status == "authorized"
    ).first()
    
    if not tax_auth:
        return error_response(400, "客户未授权税务信息")
    
    try:
        # 调用税局接口查验
        service = ETaxService(tax_auth.tax_area)
        result = service.verify_invoice(
            request.invoice_code,
            request.invoice_number,
            request.issue_date
        )
        
        return success_response(data={
            "status": result.status,
            "invoice_info": {
                "invoice_code": result.invoice_code,
                "invoice_number": result.invoice_number,
                "issue_date": result.issue_date,
                "seller_name": result.seller_name,
                "seller_tax_no": result.seller_tax_no,
                "buyer_name": result.buyer_name,
                "buyer_tax_no": result.buyer_tax_no,
                "amount": float(result.amount),
                "tax_amount": float(result.tax_amount),
                "total_amount": float(result.total_amount)
            }
        })
    except Exception as e:
        return error_response(500, f"查验失败: {str(e)}")


# 生成纳税申报表
@router.post("/declarations/generate")
async def generate_declaration(
    request: DeclarationGenerateRequest,
    current_user=Depends(require_permission("tax:manage")),
    db: Session = Depends(get_db)
):
    """生成纳税申报表"""
    # 获取账期内凭证
    vouchers = db.query(Voucher).filter(
        Voucher.customer_id == current_user.customer_id,
        Voucher.period == request.period,
        Voucher.status == "approved"
    ).all()
    
    # 根据税种计算
    if request.tax_type == "增值税":
        calc_result = TaxCalculator.calculate_vat(vouchers, request.period)
        
        declaration = TaxDeclaration(
            id=uuid.uuid4(),
            customer_id=current_user.customer_id,
            period=request.period,
            tax_type=request.tax_type,
            taxable_amount=Decimal(str(calc_result["taxable_amount"])),
            tax_amount=Decimal(str(calc_result["payable_vat"])),
            deduction_amount=Decimal(str(calc_result["input_vat"])),
            payable_amount=Decimal(str(calc_result["payable_vat"])),
            status="draft"
        )
    elif request.tax_type == "附加税":
        # 先计算增值税
        vat_result = TaxCalculator.calculate_vat(vouchers, request.period)
        surtax_result = TaxCalculator.calculate_surtax(
            Decimal(str(vat_result["payable_vat"])),
            request.period
        )
        
        declaration = TaxDeclaration(
            id=uuid.uuid4(),
            customer_id=current_user.customer_id,
            period=request.period,
            tax_type=request.tax_type,
            payable_amount=Decimal(str(surtax_result["payable_amount"])),
            status="draft"
        )
    else:
        return error_response(400, f"不支持的税种: {request.tax_type}")
    
    db.add(declaration)
    db.commit()
    db.refresh(declaration)
    
    return success_response(data={
        "id": str(declaration.id),
        "period": declaration.period,
        "tax_type": declaration.tax_type,
        "taxable_amount": float(declaration.taxable_amount) if declaration.taxable_amount else 0,
        "tax_amount": float(declaration.tax_amount) if declaration.tax_amount else 0,
        "deduction_amount": float(declaration.deduction_amount) if declaration.deduction_amount else 0,
        "payable_amount": float(declaration.payable_amount) if declaration.payable_amount else 0,
        "status": declaration.status
    })


# 获取申报列表
@router.get("/declarations")
async def list_declarations(
    period: Optional[str] = None,
    tax_type: Optional[str] = None,
    current_user=Depends(require_permission("tax:read")),
    db: Session = Depends(get_db)
):
    """获取申报列表"""
    query = db.query(TaxDeclaration).filter(
        TaxDeclaration.customer_id == current_user.customer_id
    )
    
    if period:
        query = query.filter(TaxDeclaration.period == period)
    if tax_type:
        query = query.filter(TaxDeclaration.tax_type == tax_type)
    
    declarations = query.order_by(TaxDeclaration.created_at.desc()).all()
    
    items = []
    for d in declarations:
        items.append({
            "id": str(d.id),
            "period": d.period,
            "tax_type": d.tax_type,
            "taxable_amount": float(d.taxable_amount) if d.taxable_amount else 0,
            "tax_amount": float(d.tax_amount) if d.tax_amount else 0,
            "payable_amount": float(d.payable_amount) if d.payable_amount else 0,
            "status": d.status,
            "declared_at": d.declared_at.isoformat() if d.declared_at else None,
            "receipt_no": d.receipt_no
        })
    
    return success_response(data={"items": items})


# 提交申报
@router.post("/declarations/{declaration_id}/submit")
async def submit_declaration(
    declaration_id: str,
    current_user=Depends(require_permission("tax:manage")),
    db: Session = Depends(get_db)
):
    """提交纳税申报"""
    declaration = db.query(TaxDeclaration).filter(
        TaxDeclaration.id == declaration_id,
        TaxDeclaration.customer_id == current_user.customer_id
    ).first()
    
    if not declaration:
        return error_response(404, "申报记录不存在")
    
    if declaration.status != "draft":
        return error_response(400, "只能提交草稿状态的申报")
    
    # 获取税务授权
    tax_auth = db.query(TaxAuth).filter(
        TaxAuth.customer_id == current_user.customer_id,
        TaxAuth.auth_status == "authorized"
    ).first()
    
    if not tax_auth:
        return error_response(400, "未授权税务信息")
    
    try:
        # 调用税局接口提交
        service = ETaxService(tax_auth.tax_area)
        result = service.submit_declaration({
            "tax_no": tax_auth.tax_no,
            "period": declaration.period,
            "tax_type": declaration.tax_type,
            "payable_amount": declaration.payable_amount
        })
        
        if result["success"]:
            declaration.status = "submitted"
            declaration.declared_at = datetime.utcnow()
            declaration.receipt_no = result["receipt_no"]
            db.commit()
            
            return success_response(data={
                "message": "申报提交成功",
                "receipt_no": result["receipt_no"]
            })
        else:
            return error_response(500, result.get("message", "提交失败"))
    except Exception as e:
        return error_response(500, f"提交失败: {str(e)}")


# 获取税局数据
@router.get("/data")
async def get_tax_data(
    period: str,
    tax_type: str = "增值税",
    current_user=Depends(require_permission("tax:read")),
    db: Session = Depends(get_db)
):
    """获取税局数据（销项/进项）"""
    tax_auth = db.query(TaxAuth).filter(
        TaxAuth.customer_id == current_user.customer_id,
        TaxAuth.auth_status == "authorized"
    ).first()
    
    if not tax_auth:
        return error_response(400, "未授权税务信息")
    
    try:
        service = ETaxService(tax_auth.tax_area)
        data = service.get_tax_data(
            tax_auth.tax_no,
            period,
            tax_type
        )
        
        return success_response(data={
            "period": data.period,
            "tax_type": data.tax_type,
            "sales_amount": float(data.sales_amount),
            "sales_tax": float(data.sales_tax),
            "purchase_amount": float(data.purchase_amount),
            "purchase_tax": float(data.purchase_tax),
            "payable_tax": float(data.payable_tax)
        })
    except Exception as e:
        return error_response(500, f"获取数据失败: {str(e)}")


# 删除税务授权
@router.delete("/auths/{auth_id}")
async def delete_tax_auth(
    auth_id: str,
    current_user=Depends(require_permission("tax:manage")),
    db: Session = Depends(get_db)
):
    """删除税务授权"""
    auth = db.query(TaxAuth).filter(
        TaxAuth.id == auth_id,
        TaxAuth.customer_id == current_user.customer_id
    ).first()
    
    if not auth:
        return error_response(404, "税务授权不存在")
    
    auth.is_enabled = False
    db.commit()
    
    return success_response(data={"message": "税务授权已删除"})


from datetime import timedelta
