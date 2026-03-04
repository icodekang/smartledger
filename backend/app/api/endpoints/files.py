from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.permissions import require_permission
from app.services.storage_service import StorageService
from app.utils.storage import generate_object_name
from app.models.bill import Bill

router = APIRouter(prefix="/files", tags=["文件"])

ALLOWED_TYPES = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/tiff': '.tiff',
    'application/pdf': '.pdf'
}

MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    customer_id: str = None,
    current_user=Depends(require_permission("bills:create")),
    db: Session = Depends(get_db)
):
    """文件上传接口"""
    
    if not file.filename:
        return error_response(400, "No file provided")
    
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE:
        return error_response(400, f"File too large, max {MAX_FILE_SIZE // 1024 // 1024}MB")
    
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_TYPES:
        return error_response(400, f"File type not allowed: {content_type}")
    
    file_obj = BytesIO(content)
    
    storage_path = generate_object_name(
        file_type="bills",
        customer_id=customer_id or "temp",
        original_filename=file.filename
    )
    
    storage = StorageService()
    try:
        await storage.upload_file(
            file_data=file_obj,
            object_name=storage_path,
            content_type=content_type,
            file_size=len(content)
        )
    except Exception as e:
        return error_response(500, f"Upload failed: {str(e)}")
    
    bill = Bill(
        customer_id=customer_id,
        bill_type="image" if content_type.startswith("image") else "pdf",
        storage_path=storage_path,
        storage_url=f"/files/{storage_path}",
        process_status="pending"
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    
    return success_response(data={
        "bill_id": str(bill.id),
        "storage_path": storage_path,
        "storage_url": f"/files/{storage_path}",
        "file_name": file.filename,
        "file_size": len(content),
        "content_type": content_type
    })


@router.get("/{path:path}")
async def get_file(path: str):
    """获取文件"""
    storage = StorageService()
    try:
        response = storage.get_file_stream(path)
        return StreamingResponse(response, media_type="application/octet-stream")
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
