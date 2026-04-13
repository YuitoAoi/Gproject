# 项目上下文 (PROJECT.md)

## 项目信息
- **名称**: 基于 LLaMA-Factory 的轻量级本地化大模型微调工作站
- **版本**: v1.0 (初始版本)
- **描述**: 一款面向本地/私有云环境的“一站式”LLMOps 轻量级工作站，集成数据处理、模型微调、任务监控、模型推理功能。
- **目标用户**: 开发者、研究人员，需要本地微调大模型的用户。
- **部署环境**: 本地或私有云，支持 GPU。

## 技术栈
- 核心框架: LLaMA-Factory
- 后端: Python 3.10+, FastAPI, Celery + Redis, SQLAlchemy, MySQL, pynvml
- 前端: Vue 3, Vite, Element Plus, Pinia, ECharts, WebSocket

## 项目目标
- 提供完整的数据管理流程。
- 支持高效的模型训练编排和监控。
- 实现可靠的模型推理服务。
- 确保全链路可观测性和安全性。

## 关键决策
- 使用 LLaMA-Factory 作为微调核心，确保兼容性。
- 采用 Celery 进行任务调度，支持异步和排队。
- 实时监控通过 WebSocket 实现低延迟。

## 参考文档
- REQUIREMENTS.md
- ROADMAP.md