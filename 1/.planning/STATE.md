# Project State

## Current Milestone
**里程碑 1: 项目初始化与基础架构搭建 (v1.0)**

## Current Phase
**阶段 1: 前后端基础架构搭建** — COMPLETE

## Phase Status
| Phase | Name | Status |
|-------|------|--------|
| 1 | 前后端基础架构搭建 | COMPLETE |
| 2 | 数据管理模块 | NOT STARTED |
| 3 | 模型训练任务编排 | NOT STARTED |
| 4 | 实时监控 | NOT STARTED |
| 5 | 模型推理与服务 | NOT STARTED |

## Key Decisions
- 使用 `pymysql` 替代 `mysqlclient` 解决 Windows 构建兼容性
- 统一 SQLAlchemy Base 实例（从 `db/session.py` 导出，`db/models/__init__.py` 引用）
- 前端手动搭建而非 Vite 脚手架（因权限问题无法执行 `npm create`）

## Blockers
- MySQL 服务需要启动才能验证数据库表创建
- Redis 服务需要启动才能验证 Celery worker
- npm cache 目录有权限问题（EPERM），需使用临时缓存目录绕过

## Infrastructure Notes
- 后端启动命令: `cd backend && python -m uvicorn app.main:app --reload --port 8000`
- 前端启动命令: `cd frontend && npm run dev` (端口 3000)
- Celery worker: `cd backend && celery -A app.core.celery_app worker --loglevel=info`
