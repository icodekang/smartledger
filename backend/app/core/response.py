from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import time

T = TypeVar('T')


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


def error_response(code: int, message: str, data: Any = None) -> ResponseModel:
    """错误响应"""
    return ResponseModel(code=code, message=message, data=data)


class APIResponse(JSONResponse):
    """自定义JSON响应"""
    def render(self, content) -> bytes:
        if isinstance(content, ResponseModel):
            return super().render(content.dict())
        return super().render(content)
