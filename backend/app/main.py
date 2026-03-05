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

# 注册API限流中间件（所有请求）
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    from app.core.rate_limit import rate_limiter
    
    # 获取客户端IP
    client_ip = request.client.host if request.client else "unknown"
    
    # 根据路径设置不同的限流策略
    path = request.url.path
    
    # 认证接口限流：5次/分钟
    if path.startswith("/api/v1/auth"):
        limit, window = 5, 60
    # 上传接口限流：20次/分钟
    elif "/upload" in path:
        limit, window = 20, 60
    # 其他API接口：100次/分钟
    else:
        limit, window = 100, 60
    
    # 生成限流key
    key = f"api:{client_ip}:{path}"
    allowed, remaining = rate_limiter.is_allowed(key, limit, window)
    
    if not allowed:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={"code": 429, "message": "请求过于频繁，请稍后再试"},
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Window": str(window)
            }
        )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Window"] = str(window)
    
    return response

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
