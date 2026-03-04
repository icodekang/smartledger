from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    bill_id: str
    storage_path: str
    storage_url: str
    file_name: str
    file_size: int
    content_type: str
