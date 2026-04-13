# Requirements: LLaMA-Factory Workstation

**Defined:** 2026-04-13
**Core Value:** 用户可以通过统一的 Web 界面完成从数据准备到模型微调再到推理部署的完整 LLMOps 闭环

## v1 Requirements

### Data Management

- [ ] **DATA-01**: User can upload dataset files (.csv, .xlsx) with chunked multipart upload (max 100MB)
- [ ] **DATA-02**: User sees upload progress bar and status (success/failure/in-progress) with error details
- [ ] **DATA-03**: User can trigger data cleaning (deduplication, missing value handling) and preview results before applying
- [ ] **DATA-04**: User can convert dataset to LLaMA-Factory format (Alpaca/ShareGPT JSON) with automatic dataset_info.json generation
- [ ] **DATA-05**: User can list, search, and delete datasets with status indicators (Ready, Processing, Error)
- [ ] **DATA-06**: User can manage dataset versions

### Training Orchestration

- [ ] **TRNG-01**: User can configure training parameters via "curated & layered" web form (core params visible, advanced params in collapsible panel)
- [ ] **TRNG-02**: User can select base model and dataset from dynamic dropdown lists
- [ ] **TRNG-03**: System estimates GPU VRAM requirement and warns user when insufficient (with force-start option)
- [ ] **TRNG-04**: System queues multiple training tasks and executes them sequentially via Celery
- [ ] **TRNG-05**: User can safely cancel a running training task (Redis flag, graceful exit, GPU resource cleanup)
- [ ] **TRNG-06**: System saves final model weights to persistent storage after successful training
- [ ] **TRNG-07**: System registers trained model metadata in database (name, base model, training params, file path)
- [ ] **TRNG-08**: System supports checkpoint saving at configurable epoch intervals for resumable training
- [ ] **TRNG-09**: Training task status transitions correctly: Pending → Running → Success/Failed/Cancelled

### Real-time Monitoring

- [ ] **MON-01**: User can view real-time training logs in terminal-like display via WebSocket
- [ ] **MON-02**: User can see real-time training metrics (Loss) as dynamic ECharts line charts
- [ ] **MON-03**: User can monitor GPU status (VRAM usage, temperature, utilization, power) in real-time via pynvml
- [ ] **MON-04**: System shows training progress bar with current Epoch/Step
- [ ] **MON-05**: Real-time data flows through Redis Pub/Sub channels with low latency and no data loss

### Inference Service

- [ ] **INFR-01**: User can activate a trained model (async load to GPU) and see loading progress
- [ ] **INFR-02**: User receives global notification when model activation completes
- [ ] **INFR-03**: User can deactivate a model to release GPU memory
- [ ] **INFR-04**: User can chat with an activated model in interactive interface with multi-turn conversation
- [ ] **INFR-05**: Model responses display with streaming output (token-by-token generation effect)
- [ ] **INFR-06**: User can clear conversation and start new dialogue
- [ ] **INFR-07**: Model status persists in database (UNLOADED/LOADING/ACTIVE)

### Observability

- [ ] **OBSV-01**: System provides continuous GPU hardware status display across all modules
- [ ] **OBSV-02**: System provides task lifecycle view showing full status history
- [ ] **OBSV-03**: System ensures complete logging and metrics coverage across all modules with real-time transmission

## v2 Requirements

### Multi-GPU & Distributed

- **MGPU-01**: System supports multi-GPU training
- **MGPU-02**: System supports distributed training across nodes

### Extended Framework Support

- **FRMW-01**: System integrates additional LLM frameworks beyond LLaMA-Factory
- **FRMW-02**: System supports additional data format conversion

## Out of Scope

| Feature | Reason |
|---------|--------|
| OAuth/SSO login | Local/private cloud only, basic auth sufficient for v1 |
| Mobile app / responsive | Desktop-first design, tablet consideration only |
| Real-time user chat | Not LLMOps core, no user-to-user messaging |
| Video content support | Storage/bandwidth costs prohibitive |
| Auto-scaling inference | Single-node deployment target for v1 |
| Model evaluation benchmarks | Complex feature, defer to v2 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 2 | Pending |
| DATA-02 | Phase 2 | Pending |
| DATA-03 | Phase 2 | Pending |
| DATA-04 | Phase 2 | Pending |
| DATA-05 | Phase 2 | Pending |
| DATA-06 | Phase 2 | Pending |
| TRNG-01 | Phase 3 | Pending |
| TRNG-02 | Phase 3 | Pending |
| TRNG-03 | Phase 3 | Pending |
| TRNG-04 | Phase 3 | Pending |
| TRNG-05 | Phase 3 | Pending |
| TRNG-06 | Phase 3 | Pending |
| TRNG-07 | Phase 3 | Pending |
| TRNG-08 | Phase 3 | Pending |
| TRNG-09 | Phase 3 | Pending |
| MON-01 | Phase 4 | Pending |
| MON-02 | Phase 4 | Pending |
| MON-03 | Phase 4 | Pending |
| MON-04 | Phase 4 | Pending |
| MON-05 | Phase 4 | Pending |
| INFR-01 | Phase 5 | Pending |
| INFR-02 | Phase 5 | Pending |
| INFR-03 | Phase 5 | Pending |
| INFR-04 | Phase 5 | Pending |
| INFR-05 | Phase 5 | Pending |
| INFR-06 | Phase 5 | Pending |
| INFR-07 | Phase 5 | Pending |
| OBSV-01 | Phase 4 | Pending |
| OBSV-02 | Phase 4 | Pending |
| OBSV-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-13*
*Last updated: 2026-04-13 after initialization (merged from 1/.planning/)*
