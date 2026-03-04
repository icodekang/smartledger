from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
import traceback

from app.core.exceptions import BusinessException
from app.core.response import error_response, ResponseModel
from app.core.logging import logger


def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""
    
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        logger.warning(f"Business error: {exc.message}")
        return JSONResponse(
            status_code=200,
            content=error_response(exc.code, exc.message).dict()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unexpected error: {str(exc)}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content=error_response(500, "Internal server error").dict()
        )
