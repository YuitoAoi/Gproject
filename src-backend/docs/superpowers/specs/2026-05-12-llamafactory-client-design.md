# 2026-05-12 LlamaFactory Client 适配器设计

## 背景

当前后端已经具备以下基础能力：

- 通用同步 HTTP 客户端基座：`src/services/interfaces/http_client.py`
- Celery 实例与 Redis broker/result backend：`src/adapters/celery_client.py`、`src/core/config.py`
- 本地任务查询接口与任务记录体系：`src/app/v1/task.py`、`src/adapters/repositories/task_repo.py`
- 已有外部服务适配样例：`src/adapters/graphgen_client.py`

项目目标不是一次性完成 LlamaFactory 全量 API 的 1:1 封装，而是先建立一套可扩展骨架。第一阶段覆盖训练、数据集、推理三类核心能力，并将长耗时操作纳入 Celery 异步编排，支撑多任务并发。

## 目标

构建位于 `src/adapters` 的 LlamaFactory client 适配体系，满足以下目标：

1. 提供面向领域的稳定调用接口，而不是让上层直接拼接 HTTP 路径。
2. 第一阶段支持训练、数据集、推理三类核心能力。
3. 长耗时操作通过 Celery 异步执行，轻量查询与单次轻量推理保留同步直连。
4. 复用现有本地任务系统统一追踪状态、进度、错误与上游任务 ID。
5. 为后续补齐更多 LlamaFactory API 保留清晰扩展点，而不推翻第一阶段结构。

## 非目标

第一阶段明确不包含以下范围：

- 全量 API 1:1 覆盖
- WebSocket 或流式推理
- 自动补偿与高级重试工作流
- 多 LlamaFactory 实例负载均衡
- 高级优先级调度与复杂任务编排
- 大规模结果持久化优化

## 总体架构

采用“门面客户端 + 领域子客户端 + 服务层编排 + Celery 长任务处理”的分层结构。

### 1. 适配器层

建议在 `src/adapters` 中形成以下结构：

- `llamafactory_client.py`：门面入口，统一持有共享配置与底层 HTTP 能力
- `llamafactory_training_client.py`：训练相关 API
- `llamafactory_dataset_client.py`：数据集相关 API
- `llamafactory_inference_client.py`：推理相关 API

门面客户端对上层暴露以下访问方式：

- `client.training.*`
- `client.datasets.*`
- `client.inference.*`

适配器层职责：

- 组装请求路径、方法、参数、表单与 JSON 负载
- 处理上游鉴权 header 或 token 注入
- 解析上游响应
- 统一进行错误映射
- 复用现有 `HTTPClient` 基座

适配器层不负责：

- 本地任务表写入
- 业务权限判断
- Celery 调度与轮询生命周期
- 前端响应模型拼装

### 2. 服务层

服务层位于 `src/services`，负责本地业务编排：

- 调用 LlamaFactory adapter
- 写入和更新本地任务记录
- 决定同步调用还是异步投递 Celery
- 向 API 层返回项目自己的响应模型

服务层是上游能力与本地持久化之间的协调者。上层 API 不直接依赖子客户端细节。

### 3. Celery 层

复用现有 Celery 基础设施，仅承接长耗时操作：

- 训练状态轮询
- 数据集导入、上传后处理、预处理状态跟踪
- 批量推理任务提交后的异步跟踪与结果回写

不进入 Celery 的操作包括：

- 只读查询
- 健康检查
- 单次轻量推理或聊天调用

### 4. 配置层

在 `src/core/config.py` 现有配置基础上扩展 LlamaFactory 专用配置。建议包含：

- `LLAMAFACTORY_URL`
- `LLAMAFACTORY_API_KEY` 或其他鉴权字段（如果上游需要）
- `LLAMAFACTORY_TIMEOUT_MS`
- `LLAMAFACTORY_RETRIES`
- `LLAMAFACTORY_POLL_INTERVAL_SECONDS`
- `LLAMAFACTORY_MAX_CONCURRENT_POLLS`（如需要限流）

配置层为适配器和异步任务提供统一来源，避免把魔法数字散落在业务逻辑里。

## 第一阶段能力范围

### 训练能力

第一阶段训练域至少支持：

- 创建训练任务
- 查询训练任务状态
- 取消或停止训练任务
- 获取训练结果或产物摘要
- 将上游状态同步回本地任务记录

建议调用形态示例：

- `client.training.create_job(...)`
- `client.training.get_job(...)`
- `client.training.cancel_job(...)`
- `client.training.get_artifacts(...)`

训练请求的数据流：

1. API 或 service 接收训练请求。
2. service 调用 `client.training.create_job(...)` 向 LlamaFactory 提交任务。
3. 成功后写入本地 `task_repo`，保存本地 task_id 与上游 job_id 的关联。
4. service 投递 Celery 监控任务。
5. Celery 周期性查询训练状态。
6. 到达终态后，回写本地任务状态、进度、错误信息及产物摘要。

### 数据集能力

第一阶段数据集域至少支持：

- 上传或注册数据集
- 查询数据集列表与详情
- 触发数据集导入、预处理或转换任务
- 查询长任务状态
- 必要的删除或解绑能力

建议调用形态示例：

- `client.datasets.upload(...)`
- `client.datasets.list(...)`
- `client.datasets.get(...)`
- `client.datasets.prepare(...)`
- `client.datasets.delete(...)`

数据集调用的数据流分两类：

- 轻量查询接口同步直连上游并立即返回。
- 上传、导入、预处理等长耗时操作先创建本地 task，再投递 Celery 进行异步跟踪与结果回写。

如果上游数据集导入接口是同步实现但实际耗时明显，服务层仍应在本地封装成异步任务，以保证前端和调用方体验一致。

### 推理能力

第一阶段推理域至少支持：

- 同步单次推理或聊天调用
- 异步批量推理提交
- 批量推理状态查询
- 批量推理取消

建议调用形态示例：

- `client.inference.chat(...)`
- `client.inference.batch_submit(...)`
- `client.inference.get_batch_job(...)`
- `client.inference.cancel_batch_job(...)`

推理调用的数据流：

- 单次推理或聊天：service 同步调用 adapter，并将结果直接返回。
- 批量推理：service 创建本地 task，调用上游创建批任务，随后投递 Celery 轮询状态。
- 结果较大时，只在本地保存结果文件路径、对象引用或摘要信息，不把大型结果直接写进任务表。

## 本地任务系统集成

第一阶段继续复用现有本地任务系统，不另起一套状态体系。

本地任务系统承担以下职责：

- 向前端提供稳定的 `task_id`
- 统一展示状态、进度、阶段和错误
- 存储上游 `job_id` 及关键上下文
- 支撑多任务并发观察

建议做法：

- 上游 `job_id` 写入现有 `config` 字段，或在后续迭代中升级为结构化字段
- 对长任务统一维护 `phase`、`progress`、`status`
- 保留 `raw_status` 或原始上游状态，便于排查状态映射问题

## 错误处理设计

适配器层不应把裸 `httpx` 异常直接泄漏给服务层，应统一映射为稳定错误类型或结构。

建议按三类处理：

### 1. 连接类错误

包括：

- 超时
- 连接失败
- 网络不可达
- DNS 解析失败

这类错误统一表示为“上游不可达”或“请求超时”类型，供服务层决定是直接返回失败还是把本地任务标记为失败。

### 2. 协议类错误

包括：

- 4xx
- 5xx
- 返回体缺字段
- 返回结构与预期不符

应保留以下信息：

- HTTP 状态码
- 上游错误消息
- 当前领域与动作，例如训练创建、数据集上传、批量推理取消

### 3. 业务类错误

包括：

- 参数不合法
- 数据集不存在
- 模型不可用
- 当前状态不允许取消或重复提交

这类错误尽量转化为明确、可读的消息，避免只向上层抛出模糊文本。

## 状态映射设计

为了让前端与本地任务接口不依赖 LlamaFactory 的原始状态命名，第一阶段应统一定义本地状态集合：

- `pending`
- `running`
- `done`
- `failed`
- `cancelled`

映射原则：

- `queued`、`created` 等初始状态映射为 `pending`
- `running`、`processing` 等执行中状态映射为 `running`
- `finished`、`succeeded` 映射为 `done`
- `failed`、`error` 映射为 `failed`
- `canceled`、`cancelled`、`stopped` 映射为 `cancelled`

同时保留 `raw_status` 字段或等价信息，以便排查上游兼容性问题。

## Celery 并发与幂等策略

### 并发策略

遵循“只有长耗时操作走 Celery”的原则。Celery 承担三类任务：

1. 训练轮询任务
2. 数据集长任务跟踪任务
3. 批量推理跟踪任务

并发原则如下：

- 一个上游长任务对应一个本地 Celery 监控任务
- worker 并发度由部署配置控制，不在业务代码中硬编码
- 轮询间隔可配置，避免高频请求冲击 LlamaFactory
- 避免为同一个本地 task 重复投递多个监控任务

### 幂等策略

第一阶段必须显式考虑幂等：

- 提交上游任务成功后，先写本地 task，再投递 Celery
- Celery 启动时先检查本地 task 是否已进入终态
- 若本地任务已完成、失败或取消，则直接退出，不重复回写
- 取消动作先检查本地状态，避免重复 cancel
- 重试执行时尽量基于本地 task_id 与上游 job_id 判断是否是重复监控

## 结果存储策略

大结果不直接塞入任务表。

建议存储原则：

- task 表保存状态、进度、阶段、错误信息、上游 ID、关键摘要
- 大日志保存路径、引用或外部存储标识
- 批量推理结果保存输出路径、引用或摘要信息
- 训练产物保存模型名、版本、输出目录等结构化摘要

这样既避免任务表膨胀，也有利于后续扩展下载或浏览接口。

## 测试策略

第一阶段最小测试覆盖建议分三层：

### 1. adapter 单元测试

覆盖：

- 路径拼接
- 请求方法选择
- payload / params / headers 组装
- 错误映射
- 状态解析

### 2. service 编排测试

覆盖：

- 创建上游任务后是否正确落本地 task
- 长任务是否正确投递 Celery
- 查询与取消是否正确走 repo + adapter
- 上游失败时本地状态是否正确更新

### 3. Celery 核心逻辑测试

覆盖：

- 轮询逻辑
- 终态写回
- 失败停止
- 幂等保护

如果当前项目尚未形成完整的 Celery 测试基建，第一阶段至少应将轮询与状态回写逻辑抽成可直接调用函数，避免只能依赖端到端测试。

## 第一阶段完成标准

完成第一阶段时，应满足以下标准：

1. `src/adapters` 中形成 LlamaFactory 门面客户端与三个领域子客户端。
2. 服务层可以稳定编排训练、数据集、推理三类核心流程。
3. 长耗时操作通过 Celery 异步处理，轻量查询保持同步。
4. 本地 task 系统可以统一观察状态、进度、阶段与错误。
5. 至少具备 adapter、service、Celery 核心逻辑的最小可用测试覆盖。
6. 后续新增 API 时，只需扩展对应领域客户端与服务编排，而不需要推翻整体结构。

## 命名与兼容性说明

当前仓库中存在以下与本设计相关的命名问题：

- 用户最初需求中写作 `src.adpaters`，实际目录应为 `src/adapters`
- 当前存在占位文件 `src/adapters/llmamafactory_client.py`，其中 `llmama` 拼写不正确，应统一为 `llamafactory`
- 当前存在删除状态路径 `src/adapters/llamafactory/__init__.py`，需要在实现阶段确认是否保留包结构还是统一收敛到单文件 / 多文件客户端结构

实现阶段应先统一命名，再进入具体编码，避免在适配器、导入路径、测试中留下双拼写并存问题。
