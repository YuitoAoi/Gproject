# LLaMA-Factory Workstation

## What This Is

一款面向本地/私有云环境的"一站式"LLMOps 轻量级工作站，集成数据处理、模型微调、任务监控、模型推理功能。使用 LLaMA-Factory 作为核心 LLM 框架，Vue 3 + FastAPI 架构，Celery + Redis 异步任务队列，MySQL 持久化存储。目标用户为开发者和研究人员，需要本地微调大模型的用户。

## Core Value

用户可以通过统一的 Web 界面完成从数据准备到模型微调再到推理部署的完整 LLMOps 闭环，无需切换工具或编写命令行脚本。

## Requirements

### Validated

- ✓ 前端应用布局（顶部导航 + 可折叠侧边菜单 + 内容区）— Phase 1
- ✓ Vue 3 + Vite 项目初始化，Vue Router/Pinia 集成 — Phase 1
- ✓ HTTP Client（Axios）与 WebSocket Manager 通信模块 — Phase 1
- ✓ FastAPI 后端基础架构，CORS 配置 — Phase 1
- ✓ SQLAlchemy ORM 模型（User, Dataset, TrainingTask, TrainedModel）— Phase 1
- ✓ Celery + Redis 异步任务队列集成 — Phase 1
- ✓ 健康检查端点 — Phase 1

### Active

- [ ] 数据集分块上传（100MB 限制、类型校验、进度显示）
- [ ] 数据清洗工具（去重、缺失值处理、预览效果）
- [ ] 格式转换到 LLaMA-Factory 格式（Alpaca/ShareGPT JSON、dataset_info.json）
- [ ] 数据集 CRUD 管理（列表、查询、删除、版本化）
- [ ] 训练任务配置 Web 界面（精选与分层参数模式）
- [ ] 资源预估与校验（GPU 显存估算、警告、强制启动）
- [ ] 任务调度与排队（Celery 多任务管理）
- [ ] 安全中止训练（Redis 标志位、优雅退出、GPU 资源清理）
- [ ] 模型保存与注册（权重持久化、trained_models 数据库记录）
- [ ] 检查点支持（按 Epoch 保存、断点续训）
- [ ] 实时日志流（WebSocket + Redis Pub/Sub 推送）
- [ ] 实时训练指标图表（Loss 等 ECharts 动态折线图）
- [ ] 硬件监控（GPU 显存/温度/利用率 pynvml）
- [ ] 模型生命周期管理（异步预加载、激活/停用、显存管理）
- [ ] 交互式聊天界面（多轮对话、流式输出）
- [ ] 全链路可观测性（任务生命周期、硬件状态、日志指标覆盖）

### Out of Scope

- 多 GPU 支持 / 分布式训练 — v2.0 范围
- 集成更多 LLM 框架（Beyond LLaMA-Factory） — v2.1 范围
- OAuth/第三方登录 — v1 仅需本地私有环境
- 移动端适配 — 桌面端优先
- 实时聊天（用户间通讯） — 非 LLMOps 核心需求
- 视频内容支持 — 存储/带宽成本过高

## Context

- 现有代码位于 `1/backend/`（Python/FastAPI）和 `1/frontend/`（Vue 3），处于脚手架阶段
- Phase 1（前后端基础架构）已完成，包含布局、路由、数据库模型、Celery 集成
- 后端 schemas/crud/services 层为空，API 仅有健康检查和示例任务端点
- 前端视图均为占位符组件，无实际业务 UI
- WebSocket Manager 已实现连接/重连/事件分发，但后端无 WebSocket 端点
- 已有 5 个阶段的完整 CONTEXT.md 和 PLAN.md 规划文档
- LLaMA-Factory 作为 Python 库导入调用（非 subprocess），以实现对训练循环的白盒控制
- Redis Pub/Sub 作为实时数据总线，连接 Celery worker（生产者）和 WebSocket 服务（消费者）

## Constraints

- **Tech Stack**: Vue 3 + Element Plus + FastAPI + SQLAlchemy + Celery + Redis + MySQL — 已确定的技术选型
- **Deployment**: 本地或私有云，需 GPU 支持 — 决定了轻量级架构方向
- **LLaMA-Factory**: 必须以库方式导入调用，不能 subprocess — 影响训练服务设计
- **Windows 兼容**: 使用 pymysql 替代 mysqlclient — 构建兼容性约束
- **File Size**: 数据集上传最大 100MB — 影响上传机制设计
- **Permission**: 遇到文件/目录权限问题（EPERM、EACCES 等）时必须暂停执行，通知用户手动解决，待用户确认后再继续

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 分块（多部分）上传机制 | 大文件可靠上传、网络中断恢复、精确进度跟踪 | — Pending |
| Celery 异步处理数据清洗和转换 | 防止 FastAPI 超时、解耦用户请求与重负载执行 | — Pending |
| LLaMA-Factory 作为库导入 | 白盒控制训练循环、精确中止、可靠 GPU 资源释放 | — Pending |
| Redis 中止标志位机制 | 数据库为状态唯一真实来源、Redis 做信令通道 | — Pending |
| 精选与分层参数展示 | 平衡易用性和功能完整性 | — Pending |
| WebSocket + Redis Pub/Sub 推送模式 | 低延迟实时更新、降低轮询开销 | — Pending |
| 异步模型预加载 + 主动通知 | 兼顾用户体验和 GPU 资源效率 | — Pending |
| Fetch API + StreamingResponse 流式推理 | 逐字生成效果、低延迟交互 | — Pending |
| pymysql 替代 mysqlclient | Windows 构建兼容性 | ✓ Good |
| 前端手动搭建非 Vite 脚手架 | npm create 权限问题 | ⚠ Revisit |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-13 after initialization (merged from 1/.planning/)*
