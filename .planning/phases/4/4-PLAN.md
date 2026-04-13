# 阶段 4 计划：实时监控

本计划概述了实现实时监控模块的可执行步骤。计划基于 `4-CONTEXT.md` 中定义的、包含弹性设计的架构决策。

## 第 1 部分：后端实现

### 任务 1.1：常量与配置
- **动作**: 在 `backend/app/core/` 目录下创建 `constants.py` 文件。
- **动作**: 在此文件中，定义 Redis Pub/Sub 频道的常量前缀，例如 `LOG_CHANNEL_PREFIX = "log-channel:"`，以及全局系统通知频道 `SYSTEM_NOTIFICATIONS_CHANNEL = "system-notifications"`。
- **验证**: 代码中所有使用频道名称的地方都必须引用这些常量。

### 任务 1.2：弹性 Redis 连接服务
- **动作**: 在 `backend/app/db/` 目录下创建一个 `redis_client.py` 文件。
- **动作**: 在此文件中，实现一个函数 `get_redis_connection()`，该函数应包含一个带有指数退避算法的重连循环，以应对 Redis 服务临时不可用的情况。
- **验证**: 单元测试表明，在 Redis 服务中断时，调用此函数会进行多次重连尝试，而不是立即失败。

### 任务 1.3：数据捕获与发布（在 Celery Worker 中）
- **动作**: 修改 `backend/app/services/training_service.py`。
- **动作**: 实现一个自定义的日志处理器 `RedisLogHandler(logging.Handler)`。在其 `emit` 方法中，它将日志记录发布到 `constants.LOG_CHANNEL_PREFIX + task_id` 频道。
- **动作**: 实现一个自定义的回调类 `MetricsPushCallback(TrainerCallback)`。在其 `on_log` 方法中，它将指标字典发布到 `constants.METRICS_CHANNEL_PREFIX + task_id` 频道。
- **动作**: 实现一个守护线程函数 `gpu_monitor_thread(task_id)`。该线程在一个循环中定期查询 `pynvml` 并将结果发布到 `constants.GPU_STATS_CHANNEL_PREFIX + task_id` 频道。
- **动作**: 修改核心训练函数 `run_llama_factory_training`，在任务开始时，配置并添加 `RedisLogHandler`，将 `MetricsPushCallback` 传递给 Trainer，并启动 `gpu_monitor_thread` 守护线程。
- **验证**: 启动一个训练任务后，使用 `redis-cli` 的 `MONITOR` 命令可以观察到日志、指标和 GPU 状态数据被持续发布到正确的 Redis 频道中。

### 任务 1.4：WebSocket 数据推送服务
- **动作**: 在 `backend/app/api/` 目录下创建一个新的路由文件，用于 WebSocket 通信。
- **动作**: 实现一个 WebSocket 端点 `/ws/tasks/{task_id}`。
- **动作**: 在此端点的连接逻辑中，为每个客户端启动一个异步任务（或线程），该任务负责：
  1.  使用 `redis_client` 连接到 Redis。
  2.  订阅与该 `task_id` 相关的所有数据频道（日志、指标、GPU）。
  3.  在一个循环中监听消息，一旦收到，就立即将其通过 WebSocket 发送给客户端。
  4.  在客户端断开连接时，确保能优雅地终止监听循环并清理 Redis 订阅。
- **验证**: 使用一个简单的 WebSocket 客户端连接到此端点。当一个训练任务正在进行时，客户端能够实时接收到来自后端的 JSON 格式的日志、指标和 GPU 数据。

## 第 2 部分：前端实现

### 任务 2.1：任务监控页面与路由
- **动作**: 在 `frontend/src/features/` 下创建一个 `task-monitoring` 目录。
- **动作**: 在路由中添加一条动态路由 `/tasks/{task_id}/monitor`，并创建 `TaskMonitorView.vue` 作为其组件。
- **动作**: 在训练任务列表页面（阶段3创建），将“查看日志”按钮的链接指向此新路由。
- **验证**: 点击任务列表中的“查看日志”按钮，可以成功导航到对应任务的监控页面。

### 任务 2.2：WebSocket 服务与状态管理
- **动作**: 扩展 `frontend/src/api/websocket.js`，添加连接到 `/ws/tasks/{task_id}` 端点的逻辑，并实现消息处理和断线重连机制。
- **动作**: 在 `frontend/src/features/task-monitoring/` 中创建 `taskMonitoringStore.js` (Pinia store)。该 store 负责管理 WebSocket 连接状态，并存储接收到的实时日志、指标和 GPU 数据。
- **验证**: 当进入监控页面时，Pinia store 的状态显示 WebSocket 已连接。在浏览器的开发者工具中可以看到 WebSocket 消息流。

### 任务 2.3：实时 UI 组件
- **动作**: 创建 `LogViewer.vue` 组件。它从 Pinia store 中获取日志数组，并将其渲染到一个可自动滚动的、类似终端的文本区域中。
- **动作**: 创建 `MetricsChart.vue` 组件。它使用 ECharts，并 watch Pinia store 中的指标数据，以动态地向图表中追加新的数据点，从而实现实时折线图。
- **动作**: 创建 `GpuStatusDisplay.vue` 组件。它展示从 Pinia store 获取的最新 GPU 状态，使用 Element Plus 的 `el-progress` 组件来显示百分比使用率。
- **验证**: 三个组件都能正确地从 Pinia store 中获取数据并实时更新其视图。

## 第 3 部分：最终验证 (UAT)

### 任务 3.1：端到端实时监控流程测试
- **动作**: 执行一个完整的用户流程：
  1.  启动一个新的训练任务。
  2.  点击该任务的“查看日志”按钮，进入监控页面。
  3.  观察并确认：日志区域在实时滚动显示新日志；Loss 图表在平滑地绘制新数据点；GPU 显存使用率在动态变化。
- **验证**: 整个监控页面数据流畅、无卡顿，与后端训练过程保持同步。刷新页面后，WebSocket 会自动重连并继续接收数据。
