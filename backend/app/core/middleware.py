from fastapi import Request, HTTPException
import time
from app.core.logging import logger
from app.core.rate_limit import rate_limiter


async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


class RateLimitMiddleware:
    """API限流中间件 - 全局限流控制"""
    
    def __init__(self, app, default_limit: int = 100, window: int = 60):
        """
        Args:
            app: FastAPI应用
            default_limit: 默认每分钟请求数限制
            window: 时间窗口（秒）
        """
        self.app = app
        self.default_limit = default_limit
        self.window = window
        
        # 不同路径的特殊限流配置
        self.path_limits = {
            # 认证接口更严格
            "/api/v1/auth/login": (10, 60),
            "/api/v1/auth/register": (5, 60),
            # 上传接口限制
            "/api/v1/invoices/upload": (20, 60),
            "/api/v1/bank-flows/upload": (10, 60),
            # 批量操作限制
            "/api/v1/vouchers/generate": (30, 60),
            "/api/v1/audit/batch-audit": (50, 60),
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # 获取限流配置
        path = request.url.path
        limit, window = self.path_limits.get(path, (self.default_limit, self.window))
        
        # 生成限流key（已登录用户使用用户ID，未登录使用IP）
        client_ip = request.client.host if request.client else "unknown"
        
        # 尝试从header获取token
        auth_header = request.headers.get("authorization", "")
        key = client_ip
        if auth_header.startswith("Bearer "):
            # 使用IP+token前缀作为key，更精确
            token_prefix = auth_header[7:15]  # token前8个字符
            key = f"{client_ip}:{token_prefix}"
        
        # 检查限流
        allowed, remaining = rate_limiter.is_allowed(f"api:{key}", limit, window)
        
        if not allowed:
            # 触发限流
            response = HTTPException(
                status_code=429,
                detail=f"请求过于频繁，请稍后再试。限制：{limit}/{window}秒"
            )
            
            # 发送429响应
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"X-RateLimit-Limit", str(limit).encode()],
                    [b"X-RateLimit-Window", str(window).encode()],
                ],
            })
            await send({
                "type": "http.response.body",
                "body": '{"code":429,"message":"Rate limited"}'.encode(),
            })
            return
        
        # 添加限流响应头
        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                headers.append([b"X-RateLimit-Limit", str(limit).encode()])
                headers.append([b"X-RateLimit-Remaining", str(remaining).encode()])
                headers.append([b"X-RateLimit-Window", str(window).encode()])
                message["headers"] = headers
            await send(message)
        
        await self.app(scope, receive, wrapped_send)
