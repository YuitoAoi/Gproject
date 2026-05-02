---
phase: codebase
reviewed: 2026-05-01T00:00:00Z
depth: deep
files_reviewed: 27
files_reviewed_list:
  - 1/backend/app/__init__.py
  - 1/backend/app/api/__init__.py
  - 1/backend/app/api/endpoints/__init__.py
  - 1/backend/app/api/endpoints/auth.py
  - 1/backend/app/api/endpoints/datasets.py
  - 1/backend/app/api/endpoints/health.py
  - 1/backend/app/api/endpoints/tasks.py
  - 1/backend/app/api/endpoints/users.py
  - 1/backend/app/api/endpoints/websocket.py
  - 1/backend/app/api/router.py
  - 1/backend/app/core/__init__.py
  - 1/backend/app/core/celery_app.py
  - 1/backend/app/core/config.py
  - 1/backend/app/core/redis_pubsub.py
  - 1/backend/app/core/websocket_manager.py
  - 1/backend/app/crud/__init__.py
  - 1/backend/app/crud/dataset.py
  - 1/backend/app/db/__init__.py
  - 1/backend/app/db/init_db.py
  - 1/backend/app/db/models/__init__.py
  - 1/backend/app/db/session.py
  - 1/backend/app/main.py
  - 1/backend/app/schemas/__init__.py
  - 1/backend/app/schemas/dataset.py
  - 1/backend/app/services/__init__.py
  - 1/backend/app/tasks/__init__.py
  - 1/backend/app/tasks/dataset_tasks.py
findings:
  critical: 4
  warning: 13
  info: 14
  total: 31
status: issues_found
---

# Phase codebase: Code Review Report

**Reviewed:** 2026-05-01T00:00:00Z
**Depth:** deep（跨文件导入链路追踪 + 调用链分析）
**Files Reviewed:** 27
**Status:** issues_found（发现 4 个严重问题 + 13 个警告 + 14 个信息项）

## Summary

对 `1/backend/app/` 下全部 27 个 Python 源文件进行了深度审查，包括跨文件导入图分析、Celery 任务注册链路追踪、以及三层架构（API → Services → CRUD）的完整性评估。

**核心发现：**

1. **Celery 任务注册断裂**：`tasks/__init__.py` 中定义的 `add`/`multiply` 示例任务在 Worker 进程中无法被发现和执行，因为 `celery_app.py` 的 `include` 列表仅包含 `app.tasks.dataset_tasks`，遗漏了 `app.tasks`。这会导致调用 `.delay()` 成功入队但 Worker 永远无法消费。

2. **硬编码凭证散布多处**：数据库密码、Redis 连接信息硬编码在 `config.py`、`celery_app.py`、`redis_pubsub.py`、`dataset_tasks.py` 中，且 `celery_app.py` 完全忽略了 `config.py` 中已定义的 `CELERY_BROKER_URL` 和 `CELERY_RESULT_BACKEND` 配置项。

3. **Services 层完全空白**：架构设计中的 Service 层（业务编排）尚未实现，所有端点直接调用 CRUD 或 Tasks，缺少中间抽象层。

4. **数据集处功能缺失**：XLSX 格式在 Schema 中定义但数据清洗和格式转换任务完全不支持处理。

---

## Critical Issues

### CR-01: Celery Worker 无法发现 add/multiply 任务（任务注册断裂）

**File:** `1/backend/app/core/celery_app.py:7` + `1/backend/app/tasks/__init__.py:3-11`
**Issue:** `celery_app.py` 的 `include` 参数仅设置为 `['app.tasks.dataset_tasks']`，而 `add` 和 `multiply` 任务定义在 `app/tasks/__init__.py` 中。当 Celery Worker 启动时（`celery -A app.core.celery_app worker`），Worker 进程仅加载 `app.tasks.dataset_tasks` 模块，不会加载 `app.tasks`（即 `tasks/__init__.py`）。因此 `app.tasks.add` 和 `app.tasks.multiply` 在 Worker 中完全不可见。

**调用链分析：**
- `tasks.py` endpoint → `from app.tasks import add, multiply` → 导入 `tasks/__init__.py` → `@celery_app.task` 在 **API 进程** 中注册任务
- Worker 进程：`celery -A app.core.celery_app` → `include=['app.tasks.dataset_tasks']` → **不加载** `app.tasks` → `add`/`multiply` **未注册**
- 结果：`.delay()` 成功将消息发送到 Redis，但 Worker 收到后报 `Received unregistered task of type 'app.tasks.add'`

**Fix:**
```python
# celery_app.py —— 修改 include 列表，同时包含两个任务模块
celery_app = Celery(
    'llama_factory',
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/2',
    include=['app.tasks', 'app.tasks.dataset_tasks'],  # 增加 'app.tasks'
)
```

**关联修复建议：** `datasets.py:17-19` 的手动任务注册 workaround（`celery_app.tasks[task.name] = task`）在修复 include 后可以移除，避免双重注册。

---

### CR-02: 认证端点硬编码凭证 + mock 无安全防护

**File:** `1/backend/app/api/endpoints/auth.py:17`
**Issue:** 登录逻辑直接将用户名/密码与硬编码字符串 `'admin'` 和 `'admin123'` 比较，返回 mock token `'mock-token-for-dev'`。该端点没有：
- 密码哈希存储/比对
- JWT 令牌签发/验证
- 任何形式的速率限制
- 防暴力破解机制
- 数据库用户表验证（User 模型已定义但未使用）

虽然当前标记为"开发模式 mock"，但端点在路由中注册后即可被外部访问，且没有环境检测（如 `if settings.DEBUG`）来限制 mock 模式的使用范围。

**Fix:**
```python
# 至少添加开发模式门控，防止误部署到生产环境
from app.core.config import settings

@router.post('/login')
async def login(request: LoginRequest):
    """用户登录接口"""
    if not settings.DEBUG:  # 非开发模式下禁用 mock 登录
        raise HTTPException(status_code=503, detail='认证服务未就绪')
    # ... 现有 mock 逻辑
```

**长期方案：** 实现基于 `User` 模型 + JWT 的真实认证流程。

---

### CR-03: 多处硬编码 Redis/DB 连接信息，配置体系断裂

**File:** 多个文件
**Issue:** 项目存在三套独立的 Redis 连接配置，互不同步：

| 位置 | 硬编码值 | 是否可被 .env 覆盖 |
|------|----------|-------------------|
| `config.py:10` | `mysql://root:password@localhost:3306/llama_factory` | ✅ 可覆盖 |
| `config.py:12-13` | `redis://localhost:6379/0` (未使用) | ✅ 可覆盖 |
| `config.py:16-17` | `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | ✅ 可覆盖 |
| `celery_app.py:5-6` | `redis://localhost:6379/1` / `redis://localhost:6379/2` | ❌ 硬编码 |
| `redis_pubsub.py:21` | `host='localhost', port=6379, db=0` | ❌ 硬编码 |
| `dataset_tasks.py:18-20` | `REDIS_HOST='localhost', REDIS_PORT=6379, REDIS_DB=0` | ❌ 硬编码 |

`config.py` 中定义的 `CELERY_BROKER_URL` 和 `CELERY_RESULT_BACKEND` 在 `celery_app.py` 中完全未被引用，是死代码。`redis_pubsub.py` 和 `dataset_tasks.py` 各自独立创建 Redis 连接，无法通过 `.env` 统一管理。

**Fix:**
```python
# celery_app.py —— 使用 settings 中的配置
from app.core.config import settings

celery_app = Celery(
    'llama_factory',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks', 'app.tasks.dataset_tasks'],
)
```

```python
# redis_pubsub.py —— 解析 settings.REDIS_URL
from app.core.config import settings
import re

def _parse_redis_url(url: str):
    """从 redis://host:port/db 解析连接参数"""
    m = re.match(r'redis://([^:]+):(\d+)(?:/(\d+))?', url)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3) or 0)
    return 'localhost', 6379, 0

class RedisPubSub:
    def __init__(self):
        host, port, db = _parse_redis_url(settings.REDIS_URL)
        self._host = host
        self._port = port
        self._db = db
        # ...
```

```python
# dataset_tasks.py —— 统一使用 settings
from app.core.config import settings
# 同样使用 _parse_redis_url 或直接传入 settings.REDIS_URL
```

---

### CR-04: 配置文件使用已废弃的 Pydantic v1 风格

**File:** `1/backend/app/core/config.py:19-20`
**Issue:** 项目使用 `pydantic-settings 2.1.0`（Pydantic v2 时代），但配置类使用了 v1 风格的 `class Config` 内部类：
```python
class Config:
    env_file = '.env'
```

在 Pydantic v2 中，正确的写法是使用 `model_config`：
```python
model_config = SettingsConfigDict(env_file='.env')
```

虽然 v1 风格目前仍被兼容，但未来版本可能移除，且类型检查工具会发出警告。

**Fix:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    PROJECT_NAME: str = 'LLaMA-Factory Workstation'
    # ... 其余字段不变
```

---

## Warnings

### WR-01: `AsyncResult` 未指定 Celery app 实例

**File:** `1/backend/app/api/endpoints/tasks.py:37`
**Issue:** `AsyncResult(task_id)` 未传递 `app=celery_app` 参数，Celery 将使用默认 app 实例查询结果。如果默认 app 的 broker/backend 配置与项目不一致（例如 Redis DB 不同），将查询不到任务状态。对比 `datasets.py:143` 正确地传递了 `app=celery_app`。
```python
# tasks.py:37 —— 缺少 app 参数
task_result = AsyncResult(task_id)

# datasets.py:143 —— 正确传参
task_result = AsyncResult(task_id, app=celery_app)
```

**Fix:**
```python
from app.core.celery_app import celery_app

@router.get('/tasks/{task_id}', response_model=TaskResponse)
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)  # 添加 app 参数
```

---

### WR-02: `TaskResponse.result` 类型标注错误

**File:** `1/backend/app/api/endpoints/tasks.py:17`
**Issue:** `result: int = None` 的类型标注自相矛盾——声明为 `int` 但默认值为 `None`。应使用 `Optional[int]`。
```python
class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: int = None  # ❌ 类型标注与默认值冲突
```

**Fix:**
```python
from typing import Optional

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[int] = None  # ✅ 正确的 Optional 标注
```

---

### WR-03: 文件删除存在 TOCTOU 竞态条件

**File:** `1/backend/app/api/endpoints/datasets.py:102-103`
**Issue:** `os.path.exists(dataset.file_path)` 和 `os.remove(dataset.file_path)` 之间存在检查时间与使用时间（TOCTOU）竞态窗口。在并发场景下，文件可能在检查后被其他进程删除，导致 `os.remove` 抛出 `FileNotFoundError`。
```python
if os.path.exists(dataset.file_path):
    os.remove(dataset.file_path)  # 竞态：文件可能在此刻已被删除
```

**Fix:**
```python
try:
    os.remove(dataset.file_path)
except FileNotFoundError:
    pass  # 文件已不存在，无需处理
```

---

### WR-04: 分块上传完成时 dataset_id 硬编码为 0

**File:** `1/backend/app/api/endpoints/datasets.py:73`
**Issue:** `complete_upload` 响应中 `dataset_id=0` 是一个占位符/魔术数字。在前端收到此响应时，真实 dataset_id 尚未创建（由 Celery 任务异步生成），0 可能被前端误解为有效 ID。
```python
return UploadCompleteResponse(
    upload_id=upload_id,
    task_id=task.id,
    dataset_id=0,  # ❌ 魔术数字占位符
    ...
)
```

**Fix:**
```python
# 方案1：dataset_id 设为 Optional[int] 并在此时返回 None
class UploadCompleteResponse(BaseModel):
    upload_id: str
    task_id: str
    dataset_id: Optional[int] = None  # 异步创建，稍后通过 WebSocket 通知
    status: str
    message: str

# 方案2：增加 pending 状态说明
return UploadCompleteResponse(
    ...
    dataset_id=0,  # 0 表示待创建
    status="processing",
    message="File assembly task started, dataset will be created asynchronously"
)
```

---

### WR-05: `tag_id=0` 触发 falsy 短路逻辑错误

**File:** `1/backend/app/crud/dataset.py:27`
**Issue:** `tag_id or dataset_in.tag_id` 使用 `or` 短路运算符。当 `tag_id=0`（有效的整数主键值，例如数据库中第一个 Tag 的 ID 为 0）时，`0` 是 falsy 值，会回退到 `dataset_in.tag_id`，即使调用方明确传入了 `0`。
```python
tag_id=tag_id or dataset_in.tag_id  # ❌ 如果 tag_id=0，会被覆盖
```

**Fix:**
```python
tag_id=tag_id if tag_id is not None else dataset_in.tag_id  # ✅ 严格 None 检查
```

---

### WR-06: `broadcast()` 断开连接时未清理 `_task_connections`

**File:** `1/backend/app/core/websocket_manager.py:61-71`
**Issue:** `broadcast()` 方法在清理断开连接时调用 `self.disconnect(conn)` 但**未传递 `task_id`**：
```python
# broadcast() 调用 disconnect 时缺少 task_id（line 71）
for conn in dead_connections:
    await self.disconnect(conn)  # task_id=None，仅在 _active_connections 中移除
```
这导致断开连接从 `_active_connections` 中移除，但在 `_task_connections` 中仍保留失效的 WebSocket 引用。后续 `send_to_task()` 尝试向这些已失效连接推送消息时会出错（虽有 try/except 捕获但资源泄漏）。

**Fix:**
```python
async def broadcast(self, message: dict):
    dead_connections = []
    for connection in self._active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            dead_connections.append(connection)

    for conn in dead_connections:
        # 需要找到 conn 对应的 task_id 并从 _task_connections 中清理
        for tid, conns in list(self._task_connections.items()):
            if conn in conns:
                await self.disconnect(conn, tid)
                break
        else:
            await self.disconnect(conn)  # 未找到 task_id 的回退
```

---

### WR-07: XLSX 格式在任务处理中缺失支持

**File:** `1/backend/app/tasks/dataset_tasks.py:135-376`
**Issue:** `schemas/dataset.py` 中 `DatasetCreate.format` 定义为 `Literal["csv", "xlsx", "json"]`，但 `process_dataset_clean` 和 `convert_dataset_format` 仅处理 `csv` 和 `json` 格式。当用户上传 XLSX 文件并触发清洗/转换时，代码会落入 `else` 分支抛出 `Exception(f"不支持的数据格式: {dataset.format}")`（仅在 `convert_dataset_format` 的 line 377，清洗任务完全没有 else 分支处理 xlsx，会静默跳过）。

**Fix:** 两个任务函数都需要添加 xlsx 格式处理分支，使用 `openpyxl` 或 `pandas` 库读取 Excel 文件。

---

### WR-08: `all(item.values())` 将 0/False 误判为缺失值

**File:** `1/backend/app/tasks/dataset_tasks.py:164` + `:204`
**Issue:** 缺失值填充的 `drop` 策略使用 `all(row.values())` / `all(item.values())` 判断数据完整性。这会将值为 `0`、`False`、空字符串 `""` 的行视为"有缺失"，从而错误地丢弃这些行。例如：`{"age": 0, "name": "test"}` 会被判定为缺失并删除。

**Fix:**
```python
# 正确判断缺失值——仅将 None 和空字符串视为缺失
def has_missing(row: dict) -> bool:
    return any(v is None or v == '' for v in row.values())

if missing_strategy == "drop":
    reader = [row for row in reader if not has_missing(row)]
```

---

### WR-09: `reader[0]` 可能 IndexError

**File:** `1/backend/app/tasks/dataset_tasks.py:174-178`
**Issue:** 当去重或缺失值处理后的 `reader` 为空列表时，`reader[0]` 会抛出 `IndexError`：
```python
if cleaned_rows > 0:
    with open(cleaned_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=reader[0].keys() if reader else [])
        #                                           ^^^^^^^^^^
        # 外层的 `if cleaned_rows > 0` 已保证 reader 非空，但 cleaned_rows 变量值
        # 可能与 len(reader) 不同步（因代码路径分支），仍有风险
```
虽然在大多数路径中 `cleaned_rows = len(reader)`，但代码耦合使得这不可靠。CSV 和 JSON 两条路径中，CSV 路径有保护（line 174），JSON 路径 line 209 也有保护，但 JSON 路径下的 SQL 更新在 line 213 时仍依赖 `cleaned_rows`，逻辑分叉处较多。

**Fix:** 使用显式的 `if reader:` 检查替代对 `cleaned_rows` 的依赖。

---

### WR-10: `format` 参数名遮蔽 Python 内置函数

**File:** `1/backend/app/api/endpoints/datasets.py:35` + `:66`
**Issue:** 函数参数 `format: str` 和 `format: str = Query(...)` 覆盖了 Python 内置的 `format()` 函数。虽然在此处不直接调用内置 `format()`，但 IDE 会发出警告，且如果在函数体内需要使用 `format()` 时将无法使用。

**Fix:**
```python
# 重命名为 file_format 避免与内置函数冲突
async def initiate_upload(filename: str = Query(...), file_size: int = Query(...), file_format: str = Query(...)):
```

---

### WR-11: Celery Worker Pool 硬编码为 `solo` 无说明

**File:** `1/backend/app/core/celery_app.py:20`
**Issue:** `worker_pool='solo'` 硬编码在配置中。`solo` pool 是单进程执行模式，主要用于 Windows 兼容（Windows 不支持 `prefork`）。但缺少注释说明此选择的原因，后续维护者可能不理解为何使用 solo 而非默认的 prefork。

**Fix:**
```python
celery_app.conf.update(
    # ...
    worker_pool='solo',  # Windows 兼容：Windows 不支持 prefork pool，必须使用 solo
)
```

---

### WR-12: 裸 `Exception` 抛出

**File:** `1/backend/app/tasks/dataset_tasks.py:82` + `:127` + `:238` + `:377`
**Issue:** 多处使用 `raise Exception(...)` 抛出裸异常，缺少细化的异常类型（如 `ValueError`、`FileNotFoundError`）。Celery 会将所有异常统一捕获，但细化异常类型有助于日志分类和重试策略配置。

**Fix:**
```python
# 使用具体的异常类型
raise FileNotFoundError(f"未找到分块文件: upload_id={upload_id}")
raise ValueError(f"不支持的数据格式: {dataset.format}")
```

---

### WR-13: WebSocket 端点导入了未使用的 `ConnectionManager` 类

**File:** `1/backend/app/api/endpoints/websocket.py:11`
**Issue:** `from app.core.websocket_manager import manager, ConnectionManager` 导入了 `ConnectionManager` 类，但文件中只使用了 `manager` 实例。多余的导入不会导致运行时错误但增加代码噪音。

**Fix:**
```python
from app.core.websocket_manager import manager
```

---

## Info

### IN-01: Services 层完全空白——架构断层

**File:** `1/backend/app/services/__init__.py`
**Issue:** 架构设计文档规定 API → Services → CRUD 三层分离，但 `services/` 目录仅包含空的 `__init__.py`。当前所有端点直接调用 CRUD 和 Celery Tasks，缺少业务编排层。随着功能增长（训练任务编排、模型管理、推理服务），直接在端点中处理复杂业务逻辑会导致端点膨胀。

**建议:** 按功能域创建 Service 类（如 `DatasetService`、`TrainingService`），将业务逻辑从端点中提取出来。

---

### IN-02: `auth.py` 中 `import json` 仅用于调试打印

**File:** `1/backend/app/api/endpoints/auth.py:3`
**Issue:** `json.dumps()` 仅在 `print()` 语句中使用（line 28），而 `print()` 本身是调试代码。两者都应替换为正式的日志记录。

```python
# 当前
import json
print(f"[Auth] 返回数据: {json.dumps(response_data, ensure_ascii=False)}")

# 建议
import logging
logger = logging.getLogger(__name__)
logger.debug(f"返回数据: {response_data}")
```

---

### IN-03: `dataset_tasks.py` 中 `import time` 未使用

**File:** `1/backend/app/tasks/dataset_tasks.py:4`
**Issue:** `import time` 在文件中未被任何代码引用，属于死导入。

**Fix:** 删除第 4 行的 `import time`。

---

### IN-04: 多处使用 `print()` 而非结构化日志

**File:** `1/backend/app/api/endpoints/auth.py:16,28,30`、`1/backend/app/db/init_db.py:8`、`1/backend/app/tasks/dataset_tasks.py:56`

**Issue:** 项目约定要求使用 `logging` 模块，但多处仍在使用 `print()` 进行输出。`print()` 的输出无法被日志系统过滤、格式化或路由。

**Fix:** 统一替换为 `logging.getLogger(__name__)` 模式。

---

### IN-05: 不必要的 `async def`（同步函数标记为异步）

**File:** `1/backend/app/api/endpoints/auth.py:14`、`1/backend/app/api/endpoints/users.py:7`

**Issue:** `login()` 和 `get_user_info()` 两个端点函数声明为 `async def`，但函数体内没有任何 `await` 调用。虽然 FastAPI 同时支持同步和异步端点，但将纯同步函数声明为 `async` 误导了调用者，且可能在事件循环中造成不必要的调度开销。

**Fix:** 改为 `def login(request: LoginRequest):` 和 `def get_user_info():`，或在函数体内添加实际的异步操作。

---

### IN-06: `datetime.utcnow()` 在 Python 3.12 中已废弃

**File:** `1/backend/app/db/models/__init__.py:37,38,57,58,77,99,100,123,124`

**Issue:** SQLAlchemy 模型中使用 `default=datetime.utcnow` 作为时间戳默认值。`datetime.utcnow()` 在 Python 3.12 中已标记为废弃（deprecated），推荐使用 `datetime.now(datetime.UTC)` 替代。

**Fix:**
```python
from datetime import datetime, UTC  # Python 3.11+

created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
```

---

### IN-07: SQLAlchemy 使用遗留的 `declarative_base` 导入路径

**File:** `1/backend/app/db/session.py:2`
**Issue:** `from sqlalchemy.ext.declarative import declarative_base` 是 SQLAlchemy 1.x 的遗留导入路径。在 SQLAlchemy 2.0+ 中，推荐使用 `from sqlalchemy.orm import declarative_base`。当前导入仍然有效（向后兼容），但应迁移到新路径。

**Fix:**
```python
from sqlalchemy.orm import declarative_base  # SQLAlchemy 2.0 推荐路径
```

---

### IN-08: `dataset_tasks.py` 中存在大量代码重复

**File:** `1/backend/app/tasks/dataset_tasks.py:135-376`
**Issue:** `process_dataset_clean` 和 `convert_dataset_format` 两个函数中：
- CSV 和 JSON 格式的处理逻辑高度相似但分别独立实现
- Alpaca 和 ShareGPT 转换逻辑在 CSV/JSON 两个代码路径中各实现了一遍（共 4 次）
- 文件写入、进度发布模式完全重复

当前 `dataset_tasks.py` 长达 392 行（远超 50 行指导上限），且扩展新格式时需要修改多处。建议抽象出 `read_dataset(file_path, format)` 和 `write_dataset(data, format, output_path)` 通用函数。

---

### IN-09: `PROJECT_ROOT` 计算脆弱（多层 `dirname` 链）

**File:** `1/backend/app/api/endpoints/datasets.py:26` + `1/backend/app/tasks/dataset_tasks.py:13`

**Issue:** 两个文件中使用不同数量的 `os.path.dirname()` 链式调用来计算项目根目录：
- `datasets.py`: 6 层 `dirname`（从 `endpoints/datasets.py` 向上到项目根）
- `dataset_tasks.py`: 5 层 `dirname`（从 `tasks/dataset_tasks.py` 向上到项目根）

这种计算方式极其脆弱，任何目录结构调整都会导致路径错误。

**Fix:**
```python
# 在 config.py 中添加
class Settings(BaseSettings):
    # ...
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.dirname(__file__)))), "datafile")

# 或使用 pathlib
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[5]  # 明确表达层级
```

---

### IN-10: `datasets` 路由前缀与其他路由不一致

**File:** `1/backend/app/api/router.py:10`
**Issue:** 其他路由都有明确前缀（`/health`、`/auth`、`/tasks`、`/user`），但 datasets 路由使用空前缀 `''`：
```python
api_router.include_router(datasets.router, prefix='', tags=['datasets'])
```
这导致 datasets 端点的 URL 直接挂载在 `/api/v1/datasets/...` 下，而其他路由为 `/api/v1/health/`、`/api/v1/auth/login` 等。不一致性增加了理解成本。

**Fix:**
```python
api_router.include_router(datasets.router, prefix='/datasets', tags=['datasets'])
# 同时调整 datasets.py 中各路由的 path 去掉 /datasets 前缀
```

---

### IN-11: WebSocket 路由注册方式不一致

**File:** `1/backend/app/main.py:8,46`
**Issue:** REST API 路由通过 `api_router` 统一聚合在 `router.py` 中，但 WebSocket 路由单独在 `main.py` 中注册：
```python
from app.api.endpoints.websocket import router as websocket_router
# ...
app.include_router(websocket_router)
```
应统一在 `router.py` 中管理所有路由注册。

---

### IN-12: `init_db.py` 导入未使用的模型引用

**File:** `1/backend/app/db/init_db.py:2`
**Issue:** 导入了 `User, Dataset, TrainingTask, TrainedModel, Tag` 但未在代码中直接使用。这些导入是为了触发 SQLAlchemy 模型注册（使 `Base.metadata` 包含这些表），但这种隐式依赖模式不够直观。建议添加注释说明或用 `# noqa: F401` 标记。

**Fix:**
```python
from app.db.models import User, Dataset, TrainingTask, TrainedModel, Tag  # noqa: F401  # 触发模型注册
```

---

### IN-13: 分块上传缺少服务端校验

**File:** `1/backend/app/api/endpoints/datasets.py:48-62` + `:66-76`
**Issue:** 
- `upload_chunk`（line 48）不验证单个分块大小是否 ≤ CHUNK_SIZE（5MB）
- `complete_upload`（line 66）不校验是否所有分块（`total_chunks` 个）都已上传完毕
- 没有分块完整性校验（如 checksum/MD5）

**建议:** 添加 chunk 索引范围校验、完整性检查，并在 complete_upload 时验证所有分块文件存在。

---

### IN-14: `auth.py` 中 `import json` 应提升到模块级别（已实现）但仅用于打印

**File:** `1/backend/app/api/endpoints/auth.py:3,28`
**Issue:** `json` 模块在模块级导入是常规做法，但它仅用于 `print()` 调试输出（line 28），而项目已明确推荐使用 `logging` 替代 `print()`。应一并替换为结构化日志。

---

_Reviewed: 2026-05-01T00:00:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
