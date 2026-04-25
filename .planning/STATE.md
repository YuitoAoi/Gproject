# Project State

## Current Milestone
**v1.0 — Core LLMOps Platform**

## Current Phase
**Phase 1: Frontend & Backend Infrastructure** — COMPLETE

## Phase Status
| Phase | Name | Status |
|-------|------|--------|
| 1 | Frontend & Backend Infrastructure | COMPLETE |
| 2 | Data Management Module | NOT STARTED |
| 3 | Training Task Orchestration | NOT STARTED |
| 4 | Real-time Monitoring | NOT STARTED |
| 5 | Inference Service & Observability | NOT STARTED |

## Key Decisions
- 使用 pymysql 替代 mysqlclient 解决 Windows 构建兼容性
- 统一 SQLAlchemy Base 实例（从 db/session.py 导出）
- 前端手动搭建而非 Vite 脚手架（因权限问题）
- 分块上传机制处理大文件（100MB）
- Celery 异步处理数据清洗和转换
- LLaMA-Factory 作为库导入（白盒控制训练循环）
- Redis 中止标志位机制实现安全中止
- WebSocket + Redis Pub/Sub 推送实时数据
- 异步模型预加载 + 主动通知模式
- Fetch API + StreamingResponse 实现流式推理

## Blockers
- MySQL 服务需要启动才能验证数据库表创建
- Redis 服务需要启动才能验证 Celery worker

## Project Rules
- **权限暂停规则**: 遇到文件/目录权限问题（EPERM、EACCES 等）时，必须暂停执行并通知用户，待用户确认解决后再继续

## Infrastructure Notes
- 后端启动: `cd 1/backend && python -m uvicorn app.main:app --reload --port 8000`
- 前端启动: `cd 1/frontend && npm run dev` (端口 3000)
- Celery worker: `cd 1/backend && celery -A app.core.celery_app worker --loglevel=info`
- Vite proxy: `/api/*` → `http://localhost:8000`

## Project Reference
See: .planning/PROJECT.md (updated 2026-04-13)

**Core value:** 用户可以通过统一的 Web 界面完成从数据准备到模型微调再到推理部署的完整 LLMOps 闭环
**Current focus:** Phase 2: Data Management Module
