# SmartLedger AI 🤖💰

AI智能代理记账系统 - 让记账更智能、更高效

## 🎯 项目简介

SmartLedger AI 是一个基于人工智能的代理记账系统，通过 OCR + LLM 技术实现智能票据识别、自动记账核算和人机协作审核。

## 🏗️ 技术栈

- **后端**: Python + FastAPI + SQLAlchemy
- **前端**: Vue3 + Vite + Element Plus
- **AI**: DeepSeek API + 百度OCR
- **数据库**: PostgreSQL + Redis
- **存储**: MinIO (对象存储)

## 🚀 快速开始

```bash
# 克隆仓库
git clone https://github.com/icodekang/smartledger.git
cd smartledger

# 切换到开发分支
git checkout dev

# 启动服务
docker-compose up -d
```

## 📁 分支规范

| 分支 | 说明 |
|------|------|
| `main` | 生产分支，稳定版本 |
| `dev` | 开发分支，日常开发 |
| `feature/*` | 功能分支，具体功能开发 |
| `bugfix/*` | 修复分支，bug修复 |

## 📝 Commit规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试相关
chore: 构建/工具
```

## 👥 团队

- 技术负责人
- 后端开发
- 前端开发
- AI工程师

---
**Made with ❤️ by SmartLedger Team**
