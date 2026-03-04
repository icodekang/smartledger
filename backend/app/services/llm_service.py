import asyncio
import json
from typing import Optional, Dict, Any
from functools import wraps

from app.core.config import settings
from app.core.logging import logger


def retry_on_error(max_retries=3, delay=1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                    await asyncio.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator


class DeepSeekService:
    """DeepSeek LLM服务"""
    
    def __init__(self):
        self.client = None
        self.model = settings.DEEPSEEK_MODEL
        
        if settings.DEEPSEEK_API_KEY:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(
                    api_key=settings.DEEPSEEK_API_KEY,
                    base_url=settings.DEEPSEEK_BASE_URL
                )
            except ImportError:
                logger.warning("openai not installed, LLM will be mocked")
    
    @retry_on_error(max_retries=3)
    async def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[str] = None
    ) -> Optional[str]:
        """调用DeepSeek对话接口"""
        if not self.client:
            logger.warning("LLM client not initialized, returning mock response")
            return self._mock_response(user_prompt)
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if response_format == "json_object":
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**kwargs)
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return None
    
    async def json_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3
    ) -> Optional[Dict[str, Any]]:
        """获取JSON格式响应"""
        content = await self.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            response_format="json_object"
        )
        
        if not content:
            return None
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, content: {content}")
            return None
    
    def _mock_response(self, user_prompt: str) -> str:
        """模拟响应（测试用）"""
        return json.dumps({
            "analysis": "这是一张增值税普通发票",
            "category": "办公用品",
            "confidence": 0.95,
            "suggested_subjects": [
                {"code": "6602", "name": "管理费用", "debit": True},
                {"code": "2221", "name": "应交税费", "debit": True},
                {"code": "1002", "name": "银行存款", "credit": True}
            ]
        })
