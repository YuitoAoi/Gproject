# 阶段 3 计划：模型训练任务编排

本计划概述了实现模型训练任务编排模块的可执行步骤。计划基于 `3-CONTEXT.md` 中定义的架构决策。

## 第 1 部分：后端实现

### 任务 1.1：数据库模型扩展
- **动作**: 在 `backend/app/db/models/` 目录下，创建一个新的模型文件用于 `trained_models` 表。该表应至少包含 `id`, `model_name`, `base_model_id` (外键), `training_task_id` (外键), `model_path`, 和 `created_at` 字段。
- **动作**: 更新数据库迁移脚本（或手动执行DDL）以在数据库中创建此新表。
- **验证**: `trained_models` 表已成功在数据库中创建，其列结构符合设计。

### 任务 1.2：LLaMA-Factory 训练服务封装
- **动作**: 在 `backend/app/services/` 中创建一个 `training_service.py` 文件。
- **动作**: 在该文件中，创建一个核心函数 `run_llama_factory_training(training_task_id: int, training_args: dict)`。
- **动作**: 在此函数内部，以编程方式导入并调用 LLaMA-Factory 的主训练函数。将 `training_args` 字典转换为其所需的参数格式。
- **动作**: **（关键）** 在 LLaMA-Factory 的训练循环中注入一个回调函数或修改其循环逻辑，以定期检查 Redis 中是否存在 `cancel-task:{training_task_id}` 标志。如果存在，训练应优雅地停止，执行必要的 GPU 显存清理（如 `torch.cuda.empty_cache()`），并返回一个表示“已取消”的状态。
- **验证**: 单元测试可以表明，使用有效的参数调用此服务函数会启动训练流程，而设置取消标志会导致其正常退出。

### 任务 1.3：Celery 训练任务实现
- **动作**: 创建一个新的 Celery 任务 `execute_training_task(training_task_id: int)`。
- **动作**: 此任务的逻辑应为：
  1.  从数据库中根据 `training_task_id` 获取任务详情。
  2.  将数据库中该任务的状态更新为 `Running`。
  3.  调用 `training_service.run_llama_factory_training` 函数，并传入所需参数。
  4.  根据训练函数的返回值，调用下面的模型保存与注册服务。
  5.  在 `try...except...finally` 块中执行上述操作，确保无论成功、失败还是取消，最终都能将数据库中的任务状态更新为 `Success`, `Failed`, 或 `Cancelled`。
- **验证**: 通过手动或 API 触发此 Celery 任务，数据库中的任务状态会按预期进行 `Pending` -> `Running` -> `Success`/`Failed` 的流转。

### 任务 1.4：模型保存与注册服务
- **动作**: 在 `training_service.py` 中，创建一个函数 `save_and_register_model(...)`。
- **动作**: 此函数负责将训练成功后产出的模型权重文件保存到指定的持久化存储路径，并在 `trained_models` 数据库表中创建一条新的记录。
- **验证**: 在一次模拟的成功训练后，模型文件被保存在正确的位置，并且 `trained_models` 表中出现了一条与之对应的新记录。

### 任务 1.5：训练 API 端点
- **动作**: 实现 `POST /api/v1/training-tasks` 端点。它接收前端传来的配置，在 `training_tasks` 表中创建记录，并分派 `execute_training_task` Celery 任务。
- **动作**: 实现 `GET /api/v1/training-tasks` 端点，用于获取任务列表。
- **动作**: 实现 `POST /api/v1/training-tasks/{task_id}/cancel` 端点，该端点只负责在 Redis 中设置取消标志。
- **验证**: 使用 API 测试工具可以成功调用所有端点，并且行为符合预期（如创建任务、获取列表、设置取消标志）。

## 第 2 部分：前端实现

### 任务 2.1：训练页面与路由
- **动作**: 在 `frontend/src/features/` 下创建一个 `model-training` 目录。
- **动作**: 在路由中添加 `/training` 路径，并将其链接到侧边栏菜单。
- **验证**: 点击侧边栏的“模型训练”菜单项，可以导航到空白的训练页面。

### 任务 2.2：训练参数配置表单
- **动作**: 创建 `TrainingConfigurationForm.vue` 组件。
- **动作**: 使用 Element Plus 的 `el-form` 和 `el-collapse` 实现“精选与分层”的表单布局。默认视图展示核心参数，高级参数放在折叠面板中。
- **动作**: “基础模型”和“数据集”的下拉选择器应通过调用后端 API (`/api/v1/models` 和 `/api/v1/datasets`) 动态填充。
- **验证**: 表单渲染正确，下拉框数据加载正常，高级设置可以展开和折叠。

### 任务 2.3：训练任务列表
- **动作**: 创建 `TrainingTaskList.vue` 组件，使用 `el-table` 展示从 `GET /api/v1/training-tasks` 获取的任务列表。
- **动作**: 表格应包含任务状态，并根据状态（`Pending`, `Running`）显示一个“中止”按钮。
- **动作**: 点击“中止”按钮应调用 `POST /api/v1/training-tasks/{task_id}/cancel` API。
- **验证**: 任务列表能正确显示所有任务及其状态。对于正在进行中的任务，点击“中止”按钮可以成功发送请求。

## 第 3 部分：最终验证 (UAT)

### 任务 3.1：端到端训练与中止流程测试
- **动作**: 执行一个完整的用户流程：
  1.  在训练页面填写参数，启动一个新训练。
  2.  在任务列表中观察到任务状态变为 `Pending`，然后变为 `Running`。
  3.  点击“中止”按钮。
  4.  观察并确认任务状态最终变为 `Cancelled`。
  5.  启动另一个任务（使用小数据集以快速完成），并让其自然结束。
  6.  观察并确认任务状态最终变为 `Success`。
  7.  验证 `trained_models` 数据库表中出现了一条与成功任务对应的新记录。
- **验证**: 整个流程可以无差错地完成。所有状态变更都按预期在 UI 和数据库中正确反映。
