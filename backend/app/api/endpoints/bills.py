from typing import Optional, List
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.response import success_response, error_response, ResponseModel, ListData
from app.core.permissions import require_permission
from app.models.bill import Bill, BillItem
from app.repositories.bill import BillRepository
from app.schemas.bill import (
    BillCreate, BillUpdate, BillResponse, BillUploadResponse
)
from app.services.storage_service import StorageService
from app.agents.bill_agent import BillAgent

router = APIRouter(prefix="/invoices", tags=["票据管理"])
bill_repo = BillRepository()


class BillItemData(BaseModel):
    """票据明细项数据"""
    id: Optional[str] = None
    name: str
    spec: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None
    tax_rate: Optional[str] = None
    tax_amount: Optional[float] = None


class BillDetailData(BaseModel):
    """票据详情数据"""
    invoice_code: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    invoice_type: Optional[str] = None
    amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    seller_name: Optional[str] = None
    seller_tax_no: Optional[str] = None
    seller_address: Optional[str] = None
    seller_bank: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_tax_no: Optional[str] = None
    buyer_address: Optional[str] = None
    buyer_bank: Optional[str] = None


class BillListData(BaseModel):
    """票据列表数据"""
    items: List[BillResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    """消息响应"""
    message: str


class BillUploadData(BaseModel):
    """票据上传响应数据"""
    bill_id: str
    storage_url: str
    ocr_status: str
    message: str


@router.get("")
async def list_invoices(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    bill_type: Optional[str] = Query(None, description="票据类型"),
    process_status: Optional[str] = Query(None, description="处理状态"),
    seller_name: Optional[str] = Query(None, description="销售方名称"),
    current_user=Depends(require_permission("bills:read")),
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
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    })


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    current_user=Depends(require_permission("bills:read")),
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
    ))


@router.post("")
async def create_invoice(
    request: BillCreate,
    current_user=Depends(require_permission("bills:create")),
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
    ))


@router.put("/{invoice_id}")
async def update_invoice(
    invoice_id: str,
    request: BillUpdate,
    current_user=Depends(require_permission("bills:update")),
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
    ))


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    current_user=Depends(require_permission("bills:delete")),
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


@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(..., description="票据图片文件"),
    bill_type: Optional[str] = Query("invoice", description="票据类型"),
    current_user=Depends(require_permission("bills:create")),
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
    from io import BytesIO
    storage = StorageService()
    try:
        # 如果customer_id为None，使用user_id作为替代
        customer_id_for_path = str(current_user.customer_id) if current_user.customer_id else str(current_user.id)
        object_name = f"invoices/{customer_id_for_path}/{uuid.uuid4()}_{file.filename}"
        file_stream = BytesIO(contents)
        storage_path = await storage.upload_file(
            file_data=file_stream,
            object_name=object_name,
            content_type=file.content_type,
            file_size=file_size
        )
        storage_url = storage.get_file_url(storage_path)
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


@router.get("/{invoice_id}/detail")
async def get_invoice_detail(
    invoice_id: str,
    current_user=Depends(require_permission("bills:read")),
    db: Session = Depends(get_db)
):
    """获取票据详情（含明细项和OCR结果）"""
    bill = bill_repo.get(db, invoice_id)
    if not bill:
        return error_response(404, "票据不存在")
    
    if str(bill.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权访问此票据")
    
    # 构建明细项
    items = []
    for item in bill.items:
        items.append({
            "id": str(item.id),
            "name": item.name,
            "spec": item.spec,
            "unit": item.unit,
            "quantity": float(item.quantity) if item.quantity else None,
            "unit_price": float(item.unit_price) if item.unit_price else None,
            "amount": float(item.amount) if item.amount else None,
            "tax_rate": item.tax_rate,
            "tax_amount": float(item.tax_amount) if item.tax_amount else None
        })
    
    return success_response(data={
        "id": str(bill.id),
        "invoice_code": bill.invoice_code,
        "invoice_number": bill.invoice_number,
        "invoice_date": bill.invoice_date.isoformat() if bill.invoice_date else None,
        "invoice_type": bill.bill_type,
        "amount": float(bill.amount) if bill.amount else None,
        "tax_amount": float(bill.tax_amount) if bill.tax_amount else None,
        "total_amount": float(bill.total_amount) if bill.total_amount else None,
        "seller_name": bill.seller_name,
        "seller_tax_no": bill.seller_tax_no,
        "seller_address": bill.seller_address,
        "seller_bank": bill.seller_bank,
        "buyer_name": bill.buyer_name,
        "buyer_tax_no": bill.buyer_tax_no,
        "buyer_address": bill.buyer_address,
        "buyer_bank": bill.buyer_bank,
        "items": items,
        "image_url": bill.storage_url,
        "ocr_result": bill.ocr_result,
        "process_status": bill.process_status,
        "created_at": bill.created_at.isoformat() if bill.created_at else ""
    })


@router.put("/{invoice_id}")
async def update_invoice(
    invoice_id: str,
    request: BillDetailData,
    current_user=Depends(require_permission("bills:update")),
    db: Session = Depends(get_db)
):
    """更新票据基本信息"""
    bill = bill_repo.get(db, invoice_id)
    if not bill:
        return error_response(404, "票据不存在")
    
    if str(bill.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权更新此票据")
    
    # 构建更新数据
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    
    # 转换日期字符串为date对象
    if "invoice_date" in update_data and update_data["invoice_date"]:
        from datetime import datetime as dt
        update_data["invoice_date"] = dt.strptime(update_data["invoice_date"], "%Y-%m-%d").date()
    
    # 转换金额为Decimal
    for field in ["amount", "tax_amount", "total_amount"]:
        if field in update_data and update_data[field] is not None:
            update_data[field] = Decimal(str(update_data[field]))
    
    bill_repo.update(db, db_obj=bill, obj_in=update_data)
    
    return success_response(data={"message": "票据更新成功"})


@router.put("/{invoice_id}/items")
async def update_invoice_items(
    invoice_id: str,
    request: dict,
    current_user=Depends(require_permission("bills:update")),
    db: Session = Depends(get_db)
):
    """更新票据明细项"""
    bill = bill_repo.get(db, invoice_id)
    if not bill:
        return error_response(404, "票据不存在")
    
    if str(bill.customer_id) != str(current_user.customer_id) and current_user.role != "admin":
        return error_response(403, "无权更新此票据")
    
    items_data = request.get("items", [])
    
    # 删除现有明细
    db.query(BillItem).filter(BillItem.bill_id == invoice_id).delete()
    
    # 创建新明细
    for item_data in items_data:
        item = BillItem(
            bill_id=invoice_id,
            name=item_data.get("name", ""),
            spec=item_data.get("spec"),
            unit=item_data.get("unit"),
            quantity=Decimal(str(item_data.get("quantity", 0))) if item_data.get("quantity") else None,
            unit_price=Decimal(str(item_data.get("unit_price", 0))) if item_data.get("unit_price") else None,
            amount=Decimal(str(item_data.get("amount", 0))) if item_data.get("amount") else None,
            tax_rate=item_data.get("tax_rate"),
            tax_amount=Decimal(str(item_data.get("tax_amount", 0))) if item_data.get("tax_amount") else None
        )
        db.add(item)
    
    db.commit()
    
    return success_response(data={"message": "明细项更新成功"})
