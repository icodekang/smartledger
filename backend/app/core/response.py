from typing import Any, Optional, Generic, TypeVar, List
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import HTTPException
import time

T = TypeVar('T')


class ListData(BaseModel, Generic[T]):
    """列表数据通用模型"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    timestamp: int = 0
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = int(time.time())
        super().__init__(**data)


def success_response(data: Any = None, message: str = "success") -> ResponseModel:
    """成功响应"""
    return ResponseModel(code=200, message=message, data=data)


def error_response(code: int, message: str, data: Any = None):
    """错误响应 - 返回HTTPException以正确设置状态码"""
    raise HTTPException(
        status_code=code if code >= 400 else 400,
        detail={
            "code": code,
            "message": message,
            "data": data,
            "timestamp": int(time.time())
        }
    )
