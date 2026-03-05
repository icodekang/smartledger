"""
限流和速率限制模块
无需外部依赖实现登录限流和API限流
"""
import time
from functools import wraps
from fastapi import Request, HTTPException
from typing import Dict, Tuple, Optional


class RateLimiter:
    """内存中的速率限制器"""
    
    def __init__(self):
        # 存储每个key的请求记录: {key: [(timestamp, count), ...]}
        self._records: Dict[str, list] = {}
        # 清理计数器
        self._cleanup_counter = 0
    
    def _cleanup_old_records(self):
        """清理过期的记录（每1000次请求执行一次）"""
        self._cleanup_counter += 1
        if self._cleanup_counter < 1000:
            return
        
        self._cleanup_counter = 0
        current_time = time.time()
        # 清理超过1小时的记录
        for key in list(self._records.keys()):
            self._records[key] = [
                record for record in self._records[key]
                if current_time - record[0] < 3600
            ]
            if not self._records[key]:
                del self._records[key]
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        检查是否允许请求
        
        Args:
            key: 限流的key（如IP地址或用户ID）
            max_requests: 窗口期内最大请求数
            window_seconds: 时间窗口（秒）
        
        Returns:
            (是否允许, 剩余请求数)
        """
        self._cleanup_old_records()
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # 获取该key的记录
        if key not in self._records:
            self._records[key] = []
        
        # 过滤窗口期内的记录
        records_in_window = [
            record for record in self._records[key]
            if record[0] > window_start
        ]
        
        # 计算窗口期内的请求总数
        total_requests = sum(record[1] for record in records_in_window)
        
        if total_requests >= max_requests:
            return False, 0
        
        # 记录当前请求
        records_in_window.append((current_time, 1))
        self._records[key] = records_in_window
        
        return True, max_requests - total_requests - 1


# 全局限流器实例
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 60, window_seconds: int = 60, key_func=None):
    """
    速率限制装饰器
    
    Args:
        max_requests: 时间窗口内最大请求数
        window_seconds: 时间窗口（秒）
        key_func: 自定义key生成函数，接收request参数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中找到request
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request is None:
                request = kwargs.get('request')
            
            # 生成限流key
            if key_func:
                key = key_func(request)
            else:
                # 默认使用客户端IP
                key = request.client.host if request and request.client else "unknown"
            
            allowed, remaining = rate_limiter.is_allowed(key, max_requests, window_seconds)
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"请求过于频繁，请稍后再试。限制：{max_requests}/{window_seconds}秒"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def login_rate_limit(max_attempts: int = 5, window_seconds: int = 300):
    """
    登录限流装饰器
    
    Args:
        max_attempts: 时间窗口内最大尝试次数
        window_seconds: 时间窗口（秒），默认5分钟
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中找到request
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request is None:
                request = kwargs.get('request')
            
            # 使用IP+用户名作为key
            client_ip = request.client.host if request and request.client else "unknown"
            
            # 从表单数据获取用户名
            username = "unknown"
            if request:
                try:
                    form_data = await request.form()
                    username = form_data.get("username", "unknown")
                except:
                    pass
            
            key = f"login:{client_ip}:{username}"
            
            allowed, remaining = rate_limiter.is_allowed(key, max_attempts, window_seconds)
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"登录尝试次数过多，请{window_seconds//60}分钟后再试"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
