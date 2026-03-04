from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import logger
from app.core.response import APIResponse, success_response, error_response
from app.core.exception_handler import register_exception_handlers
from app.core.middleware import log_requests
from app.core.exceptions import BusinessException
from app.api.v1.router import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    default_response_class=APIResponse
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册请求日志中间件
app.middleware("http")(log_requests)

# 注册异常处理器
register_exception_handlers(app)

# 注册API路由
app.include_router(api_router)


@app.get("/health")
async def health_check():
    return success_response(data={"status": "healthy", "version": settings.VERSION})


@app.get("/test/success")
async def test_success():
    """测试成功响应"""
    return success_response(data={"message": "Hello"})


@app.get("/test/error")
async def test_error():
    """测试错误响应"""
    raise BusinessException(4001, "Test error")
