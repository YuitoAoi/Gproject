# Roadmap: LLaMA-Factory Workstation

**Milestone:** v1.0 — Core LLMOps Platform
**Defined:** 2026-04-13

## Progress

| Phase | Name | Status | Plans | Progress |
|-------|------|--------|-------|----------|
| 1 | Frontend & Backend Infrastructure | ✓ Complete | 1/1 | 100% |
| 2 | Data Management Module | ○ Pending | 3/3 | 0% |
| 3 | Training Task Orchestration | ○ Pending | 0/1 | 0% |
| 4 | Real-time Monitoring | ○ Pending | 0/1 | 0% |
| 5 | Inference Service & Observability | ○ Pending | 0/1 | 0% |

---

## Phase 1: Frontend & Backend Infrastructure

**Goal:** 搭建前后端基础架构，实现完整的应用布局和通信基础设施

**Dependencies:** None (foundation phase)

**Requirements:** Phase 1 validated (see PROJECT.md Validated section)

**Success Criteria:**
1. Backend service starts and connects to MySQL database
2. Frontend application displays full layout with navigable routes
3. Health check endpoint responds correctly
4. Celery worker processes demo tasks
5. HTTP Client and WebSocket Manager modules importable in frontend

---

## Phase 2: Data Management Module

**Goal:** 实现数据集的完整生命周期管理：分块上传、清洗、格式转换、CRUD 操作

**Dependencies:** Phase 1 (infrastructure)

**Requirements:** DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06

**UI hint:** yes

**Success Criteria:**
1. User can upload a dataset file up to 100MB with visible progress
2. User can trigger data cleaning and preview results before applying
3. User can convert dataset to LLaMA-Factory format (Alpaca/ShareGPT JSON)
4. dataset_info.json is auto-generated after conversion
5. Dataset list displays all datasets with correct status
6. Delete operation removes both database record and files

**Plans:**
- [ ] 02-01-PLAN.md — Backend: Dataset API + Celery Tasks
- [ ] 02-02-PLAN.md — Frontend: Data Management UI
- [ ] 02-03-PLAN.md — Integration: End-to-end verification

---

## Phase 3: Training Task Orchestration

**Goal:** 实现模型训练任务的全流程编排：配置、调度、执行、中止、模型注册

**Dependencies:** Phase 2 (datasets for training), Phase 1 (Celery infrastructure)

**Requirements:** TRNG-01 through TRNG-09

**UI hint:** yes

**Success Criteria:**
1. User can configure training parameters via curated web form
2. System estimates GPU VRAM and warns when insufficient
3. Multiple training tasks queue and execute sequentially
4. User can cancel running task and GPU resources are properly cleaned
5. Successful training produces model weights file and database record
6. Task status transitions correctly through all states

---

## Phase 4: Real-time Monitoring

**Goal:** 实现训练过程的实时监控：日志流、指标图表、硬件状态

**Dependencies:** Phase 3 (training execution), Phase 1 (WebSocket infrastructure)

**Requirements:** MON-01 through MON-05, OBSV-01, OBSV-02, OBSV-03

**UI hint:** yes

**Success Criteria:**
1. Training logs stream in real-time via WebSocket terminal display
2. Loss metrics display as real-time ECharts line chart
3. GPU stats (VRAM, temp, utilization) update in real-time
4. Training progress bar shows current Epoch/Step
5. Data flows through Redis Pub/Sub with low latency, no data loss

---

## Phase 5: Inference Service & Observability

**Goal:** 实现模型推理服务和全链路可观测性：模型生命周期管理、流式对话、系统监控

**Dependencies:** Phase 3 (trained models), Phase 4 (monitoring infrastructure)

**Requirements:** INFR-01 through INFR-07

**UI hint:** yes

**Success Criteria:**
1. User can activate/deactivate a trained model with async loading and notification
2. Chat interface supports multi-turn conversation with streaming output
3. Model status persists correctly (UNLOADED/LOADING/ACTIVE)
4. Deactivating model releases GPU memory
5. Full observability covers all modules with no blind spots

---

## Future Milestones

- **v1.1**: Testing, optimization, deployment scripts, documentation
- **v2.0**: Multi-GPU support, distributed training
- **v2.1**: Additional LLM frameworks, extended data format support
