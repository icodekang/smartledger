# 依赖管理

## 安装开发环境

```bash
pip install -r requirements/dev.txt
```

## 安装生产环境

```bash
pip install -r requirements/prod.txt
```

## 依赖说明

| 依赖 | 用途 |
|------|------|
| fastapi | Web框架 |
| uvicorn | ASGI服务器 |
| sqlalchemy | ORM |
| alembic | 数据库迁移 |
| asyncpg | PostgreSQL异步驱动 |
| redis | 缓存 |
| pyjwt | JWT认证 |
| passlib | 密码加密 |
| httpx | HTTP客户端 |
| pydantic | 数据校验 |
| celery | 任务队列 |
| minio | 对象存储 |
| openai/langchain | AI集成 |
