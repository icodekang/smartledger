from typing import Optional, List
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.models.bill import Bill
from app.repositories.bill import BillRepository
from app.schemas.bill import (
    BillCreate, BillUpdate, BillResponse, 
    BillListResponse, BillUploadResponse
)
from app.services.storage_service import StorageService
from app.agents.bill_agent import BillAgent

router = APIRouter(prefix="/invoices", tags=["票据管理"])
bill_repo = BillRepository()


@router.get("", response_model=BillListResponse)
async def list_invoices(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    bill_type: Optional[str] = Query(None, description="票据类型"),
    process_status: Optional[str] = Query(None, description="处理状态"),
    seller_name: Optional[str] = Query(None, description="销售方名称"),
    current_user=Depends(require_permission("invoices:read")),
    db: Session = Depends(get_db)
):
    """获取票据列表"""
    skip = (page - 1) * page_size
    
    # 查询数据
    query = db.query(Bill)
    if bill_type:
        query = query.filter(Bill.bill_type == bill_type)
    if process_status:
        query = query.filter(Bill.process_status == process_status)
    if seller_name:
        query = query.filter(Bill.seller_name.ilike(f"%{seller_name}%"))
    
    total = query.count()
    bills = query.order_by(Bill.created_at.desc()).offset(skip).limit(page_size).all()
    
    # 转换为响应格式
    items = []
    for bill in bills:
        item = BillResponse(
            id=str(bill.id),
            customer_id=str(bill.customer_id) if bill.customer_id else None,
            bill_type=bill.bill_type,
            invoice_code=bill.invoice_code,
            invoice_number=bill.invoice_number,
            invoice_date=bill.invoice_date.isoformat() if bill.invoice_date else None,
            seller_name=bill.seller_name,
            amount=float(bill.amount) if bill.amount else None,
            tax_amount=float(bill.tax_amount) if bill.tax_amount else None,
            total_amount=float(bill.total_amount) if bill.total_amount else None,
            storage_path=bill.storage_path,
            storage_url=bill.storage_url,
            ocr_result=bill.ocr_result,
            ocr_confidence=float(bill.ocr_confidence) if bill.ocr_confidence else None,
            process_status=bill.process_status or "pending",
            ai_confidence=float(bill.ai_confidence) if bill.ai_confidence else None,
            ai_anomalies=bill.ai_anomalies,
            created_at=bill.created_at.isoformat() if bill.created_at else "",
            updated_at=bill.updated_at.isoformat() if bill.updated_at else ""
        )
        items.append(item)
    
    return success_response(data={
        "items": [item.dict() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    })


@router.get("/{invoice_id}", response_model=BillResponse)
async def get_invoice(
    invoice_id: str,
    current_user=Depends(require_permission("invoices:read")),
    db: Session = Depends(get_db)
):
    """获取票据详情"""
    bill = bill_repo.get(db, invoice_id)
    if not bill:
        return error_response(404, "票据不存在")
    
    # 检查权限
    if str(bill.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权访问此票据")
    
    return success_response(data=BillResponse(
        id=str(bill.id),
        customer_id=str(bill.customer_id) if bill.customer_id else None,
        bill_type=bill.bill_type,
        invoice_code=bill.invoice_code,
        invoice_number=bill.invoice_number,
        invoice_date=bill.invoice_date.isoformat() if bill.invoice_date else None,
        seller_name=bill.seller_name,
        amount=float(bill.amount) if bill.amount else None,
        tax_amount=float(bill.tax_amount) if bill.tax_amount else None,
        total_amount=float(bill.total_amount) if bill.total_amount else None,
        storage_path=bill.storage_path,
        storage_url=bill.storage_url,
        ocr_result=bill.ocr_result,
        ocr_confidence=float(bill.ocr_confidence) if bill.ocr_confidence else None,
        process_status=bill.process_status or "pending",
        ai_confidence=float(bill.ai_confidence) if bill.ai_confidence else None,
        ai_anomalies=bill.ai_anomalies,
        created_at=bill.created_at.isoformat() if bill.created_at else "",
        updated_at=bill.updated_at.isoformat() if bill.updated_at else ""
    ).dict())


@router.post("", response_model=BillResponse)
async def create_invoice(
    request: BillCreate,
    current_user=Depends(require_permission("invoices:create")),
    db: Session = Depends(get_db)
):
    """创建票据"""
    bill_data = request.dict()
    bill_data["customer_id"] = current_user.customer_id
    bill_data["process_status"] = "manual"
    
    bill = bill_repo.create(db, obj_in=bill_data)
    
    return success_response(data=BillResponse(
        id=str(bill.id),
        customer_id=str(bill.customer_id) if bill.customer_id else None,
        bill_type=bill.bill_type,
        invoice_code=bill.invoice_code,
        invoice_number=bill.invoice_number,
        invoice_date=bill.invoice_date.isoformat() if bill.invoice_date else None,
        seller_name=bill.seller_name,
        amount=float(bill.amount) if bill.amount else None,
        tax_amount=float(bill.tax_amount) if bill.tax_amount else None,
        total_amount=float(bill.total_amount) if bill.total_amount else None,
        storage_path=bill.storage_path,
        storage_url=bill.storage_url,
        ocr_result=bill.ocr_result,
        ocr_confidence=float(bill.ocr_confidence) if bill.ocr_confidence else None,
        process_status=bill.process_status,
        ai_confidence=float(bill.ai_confidence) if bill.ai_confidence else None,
        ai_anomalies=bill.ai_anomalies,
        created_at=bill.created_at.isoformat() if bill.created_at else "",
        updated_at=bill.updated_at.isoformat() if bill.updated_at else ""
    ).dict())


@router.put("/{invoice_id}", response_model=BillResponse)
async def update_invoice(
    invoice_id: str,
    request: BillUpdate,
    current_user=Depends(require_permission("invoices:update")),
    db: Session = Depends(get_db)
):
    """更新票据"""
    bill = bill_repo.get(db, invoice_id)
    if not bill:
        return error_response(404, "票据不存在")
    
    # 检查权限
    if str(bill.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权更新此票据")
    
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    bill = bill_repo.update(db, db_obj=bill, obj_in=update_data)
    
    return success_response(data=BillResponse(
        id=str(bill.id),
        customer_id=str(bill.customer_id) if bill.customer_id else None,
        bill_type=bill.bill_type,
        invoice_code=bill.invoice_code,
        invoice_number=bill.invoice_number,
        invoice_date=bill.invoice_date.isoformat() if bill.invoice_date else None,
        seller_name=bill.seller_name,
        amount=float(bill.amount) if bill.amount else None,
        tax_amount=float(bill.tax_amount) if bill.tax_amount else None,
        total_amount=float(bill.total_amount) if bill.total_amount else None,
        storage_path=bill.storage_path,
        storage_url=bill.storage_url,
        ocr_result=bill.ocr_result,
        ocr_confidence=float(bill.ocr_confidence) if bill.ocr_confidence else None,
        process_status=bill.process_status or "pending",
        ai_confidence=float(bill.ai_confidence) if bill.ai_confidence else None,
        ai_anomalies=bill.ai_anomalies,
        created_at=bill.created_at.isoformat() if bill.created_at else "",
        updated_at=bill.updated_at.isoformat() if bill.updated_at else ""
    ).dict())


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    current_user=Depends(require_permission("invoices:delete")),
    db: Session = Depends(get_db)
):
    """删除票据"""
    bill = bill_repo.get(db, invoice_id)
    if not bill:
        return error_response(404, "票据不存在")
    
    # 检查权限
    if str(bill.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权删除此票据")
    
    bill_repo.delete(db, id=invoice_id)
    
    return success_response(data={"message": "票据已删除"})


@router.post("/upload", response_model=BillUploadResponse)
async def upload_invoice(
    file: UploadFile = File(..., description="票据图片文件"),
    bill_type: Optional[str] = Query("invoice", description="票据类型"),
    current_user=Depends(require_permission("invoices:create")),
    db: Session = Depends(get_db)
):
    """上传票据文件"""
    # 检查文件类型
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        return error_response(400, f"不支持的文件类型: {file.content_type}")
    
    # 限制文件大小 (10MB)
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    if file_size > 10 * 1024 * 1024:
        return error_response(400, "文件大小超过10MB限制")
    
    # 上传文件到存储服务
    storage = StorageService()
    try:
        storage_path = await storage.upload_file(
            contents, 
            file.filename, 
            file.content_type,
            folder=f"invoices/{current_user.customer_id}"
        )
        storage_url = await storage.get_file_url(storage_path)
    except Exception as e:
        return error_response(500, f"文件上传失败: {str(e)}")
    
    # 创建票据记录
    bill_data = {
        "customer_id": current_user.customer_id,
        "bill_type": bill_type,
        "storage_path": storage_path,
        "storage_url": storage_url,
        "process_status": "ocr_pending"
    }
    bill = bill_repo.create(db, obj_in=bill_data)
    
    # 启动OCR识别（异步）
    bill_agent = BillAgent()
    try:
        ocr_result = await bill_agent.process_bill_image(contents, file.content_type)
        if ocr_result:
            bill_repo.update(db, db_obj=bill, obj_in={
                "ocr_result": ocr_result,
                "ocr_confidence": ocr_result.get("confidence", 0),
                "invoice_code": ocr_result.get("invoice_code"),
                "invoice_number": ocr_result.get("invoice_number"),
                "invoice_date": ocr_result.get("invoice_date"),
                "seller_name": ocr_result.get("seller_name"),
                "amount": ocr_result.get("amount"),
                "tax_amount": ocr_result.get("tax_amount"),
                "total_amount": ocr_result.get("total_amount"),
                "process_status": "ocr_completed"
            })
    except Exception as e:
        # OCR失败，记录但不影响上传
        bill_repo.update(db, db_obj=bill, obj_in={
            "process_status": "ocr_failed"
        })
    
    return success_response(data={
        "bill_id": str(bill.id),
        "storage_url": storage_url,
        "ocr_status": "completed" if bill.process_status == "ocr_completed" else "pending",
        "message": "上传成功"
    })
