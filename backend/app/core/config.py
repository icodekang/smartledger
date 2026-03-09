from pydantic import BaseModel
from functools import lru_cache
import os


class Settings(BaseModel):
    """应用配置"""
    APP_NAME: str = "SmartLedger AI"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    # 数据库
    DATABASE_URL: str = "sqlite:///./smartledger.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "bills"
    MINIO_SECURE: bool = False
    
    # DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    
    # 百度OCR
    BAIDU_APP_ID: str = ""
    BAIDU_API_KEY: str = ""
    BAIDU_SECRET_KEY: str = ""
    
    def __init__(self, **kwargs):
        # 从环境变量读取
        env_mapping = {
            'APP_NAME': 'APP_NAME',
            'DEBUG': 'DEBUG',
            'DATABASE_URL': 'DATABASE_URL',
            'REDIS_URL': 'REDIS_URL',
            'SECRET_KEY': 'SECRET_KEY',
            'DEEPSEEK_API_KEY': 'DEEPSEEK_API_KEY',
        }
        for attr, env_var in env_mapping.items():
            if env_var in os.environ:
                kwargs[attr] = os.environ[env_var]
        # 布尔值转换
        if 'DEBUG' in kwargs and isinstance(kwargs['DEBUG'], str):
            kwargs['DEBUG'] = kwargs['DEBUG'].lower() in ('true', '1', 'yes')
        super().__init__(**kwargs)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
