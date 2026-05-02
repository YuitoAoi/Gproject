# Phase 2: Data Management Module — 后端实现计划

**版本:** v1.0  
**日期:** 2026-05-02  
**规范:** Clean Architecture  
**需求:** DATA-01 ~ DATA-06

---

## 1. 架构上下文

### 当前 src-backend 的 Clean Architecture 分层

```
src/
├── core/           # 领域层 — 实体、值对象
├── services/       # 用例层 — 业务逻辑、接口定义
│   └── interfaces/ # 仓储接口（依赖倒置的边界）
├── adapters/       # 适配器层 — 接口的具体实现
│   └── repositories/
├── db_connections/  # 基础设施 — 数据库连接
└── app/            # 交付层 — FastAPI 路由、依赖注入
```

### 已实现 vs 待实现

| 模块 | 状态 | 说明 |
|------|------|------|
| `core/user.py` | ✓ 已实现 | User 实体 |
| `core/dataset.py` | ✓ 已实现 | Dataset + DatasetMeta 实体 |
| `services/interfaces/user_repository.py` | ✓ 已实现 | User 仓储接口 |
| `services/interfaces/dataset_repository.py` | ✓ 已实现 | Dataset 仓储接口 |
| `services/interfaces/file_repository.py` | ✓ 已实现 | 文件存储接口 |
| `adapters/repositories/mysql_user_repo.py` | ✓ 已实现 | User MySQL 仓储 |
| `adapters/repositories/mysql_dataset_repo.py` | ○ 存根 | Dataset MySQL 仓储（TODO 标记） |
| `adapters/repositories/memory_dataset_repo.py` | ○ 存根 | Dataset 内存仓储 |
| `adapters/repositories/windows_file_repo.py` | ○ 存根 | Windows 文件存储 |
| `services/dataset_*_service.py` | ○ 存根 | 数据集用例（TODO 标记） |
| `services/jwt_service.py` | ✓ 已实现 | JWT 服务 |
| `services/user_login_service.py` | ✓ 已实现 | 用户登录用例 |
| `services/user_register_service.py` | ✓ 已实现 | 用户注册用例 |
| `app/v1/dataset.py` | ○ 存根 | 数据集路由 |

---

## 2. 需求 → 后端任务映射

| 需求 ID | 需求 | 后端任务 |
|---------|------|---------|
| DATA-01 | 分块上传（100MB，类型校验，进度） | 分块上传 API + 文件仓储实现 |
| DATA-02 | 上传进度展示 + 错误详情 | Celery 任务 + WebSocket 推送 |
| DATA-03 | 数据清洗（去重、缺失值） | 清洗服务 + Celery 异步任务 |
| DATA-04 | 格式转换（Alpaca/ShareGPT + dataset_info.json） | 格式转换服务 + Celery 异步任务 |
| DATA-05 | 数据集 CRUD（列表、查询、删除） | 完整 CRUD API + MySQL 仓储 |
| DATA-06 | 数据集版本管理 | 版本化存储 + 版本查询 API |

---

## 3. 分步实现计划

### Step 1: 完善领域实体 `Dataset`

**文件:** `src/core/dataset.py`

当前状态：已有 `Dataset` 和 `DatasetMeta` 基本定义。  
需要补充：

- `Dataset` 增加 `status` 字段（`"ready" | "processing" | "error"`）
- `Dataset` 增加 `total_records`、`owner_id` 字段
- `Dataset.version` 保留现有 int 版本号
- `DatasetMeta` 已有 `format`、`file_path`、`file_size`

**依赖:** 无  
**产出:** 完整的 Dataset 领域模型

---

### Step 2: 实现 `MysqlDatasetRepoAdapter`

**文件:** `src/adapters/repositories/mysql_dataset_repo.py`

当前状态：存根，所有方法为 `TODO`/`pass`。  
需要实现 `DatabaseRepository[Dataset, int]` 的全部方法：

| 方法 | SQL |
|------|-----|
| `create(entity)` | `INSERT INTO datasets (...) VALUES (...)` + `LAST_INSERT_ID()` |
| `find(id)` | `SELECT ... FROM datasets WHERE id = :id` |
| `find_all()` | `SELECT ... FROM datasets` 支持分页 `skip/limit` |
| `exists(id)` | `SELECT 1 FROM datasets WHERE id = :id` |
| `update(id, entity)` | `UPDATE datasets SET ... WHERE id = :id` |
| `remove(id)` | `DELETE FROM datasets WHERE id = :id` |

**依赖:**
- Step 1 的 `Dataset` 实体
- `DatabaseConnection`（已有 `MysqlDatabaseConnection`）
- 参考 `mysql_user_repo.py` 的实现模式

**参考模式** (`mysql_user_repo.py`):
- 构造器接收 `DatabaseConnection`
- `_session()` 用 `cast(Session, ...)` 获取 session
- `create()` 用 `text()` + `SELECT LAST_INSERT_ID()` 获取自增 ID
- `update()` 用 `cast(CursorResult, ...)` 获取 `rowcount`
- `_row_to_entity()` 静态方法做 SQL Row → 领域实体映射

---

### Step 3: 实现文件存储适配器

**文件:** `src/adapters/repositories/windows_file_repo.py`

当前状态：存根。  
需要实现 `FileRepository` 接口：

| 方法 | 功能 |
|------|------|
| `save_chunk(upload_id, chunk_number, data)` | 写入分块文件 |
| `assemble_chunks(upload_id, target_path)` | 合并分块到最终文件 |
| `delete(path)` | 删除文件/分块目录 |
| `exists(path)` | 文件是否存在 |

**存储路径规范:**
- 分块临时目录: `PROJECT_ROOT/datafile/chunks/{upload_id}/`
- 数据集最终目录: `PROJECT_ROOT/datafile/datasets/{dataset_id}/`

**依赖:** `config.py` 的 `DATA_DIR`（需新增配置项）

---

### Step 4: 实现数据集用例服务

#### 4a. `CreateDatasetService` 完善

**文件:** `src/services/dataset_create_service.py`

当前状态：存根，有 `CreateDatasetRequest`/`CreateDatasetResponse` 模型。  
需要实现：

- 校验 `file_path` 文件存在性
- 校验文件格式（csv/xlsx/json）
- 调用 `dataset_repo.create()` 创建记录
- 返回 `CreateDatasetResponse(success=True/False, error=...)`

#### 4b. `GetDatasetsService` 完善

**文件:** `src/services/datasets_get_service.py`

当前状态：存根，有 `GetDatasetsResponse` 模型。  
需要实现：

- `get_all(skip, limit)` 分页查询
- `get_by_id(dataset_id)` 单条查询
- 返回 `GetDatasetsResponse(items=[...], total=N)`

#### 4c. 新增 `DeleteDatasetService`

**文件:** `src/services/dataset_delete_service.py`（新建）

- `execute(dataset_id)` → 先查后删，同时删文件（调用 `file_repo.delete`）
- 返回 `DeleteDatasetResponse(success, error)`

#### 4d. 新增分块上传用例 `ChunkedUploadService`

**文件:** `src/services/chunked_upload_service.py`（新建）

请求/响应模型：

```python
class InitiateUploadRequest(BaseModel):
    filename: str
    file_size: int
    format: str  # csv | xlsx | json

class InitiateUploadResponse(BaseModel):
    upload_id: str       # uuid
    chunk_size: int      # 5MB
    total_chunks: int

class UploadChunkRequest(BaseModel):
    upload_id: str
    chunk_number: int

class UploadChunkResponse(BaseModel):
    upload_id: str
    chunk_number: int
    received: bool

class CompleteUploadRequest(BaseModel):
    upload_id: str
    name: str          # 数据集名称
    desc: Optional[str]

class CompleteUploadResponse(BaseModel):
    dataset_id: int
    status: str
    message: str
```

用例方法：

| 方法 | 逻辑 |
|------|------|
| `initiate(filename, file_size, format)` | 生成 upload_id，计算 total_chunks |
| `upload_chunk(upload_id, chunk_number, data)` | 写入分块到 file_repo |
| `complete(request)` | 合并分块 → 创建 Dataset 记录 → 清理临时分块 |

**依赖:** `file_repo` + `dataset_repo`

#### 4e. 新增数据清洗/转换用例

**文件:** `src/services/dataset_process_service.py`（需完善）

当前状态：存根，有 `ProcessDatasetRequest`/`ProcessDatasetResponse`。  
需要实现：

- 触发 Celery 异步清洗任务
- 触发 Celery 异步格式转换任务
- 返回 `task_id` 用于进度追踪

**关键决策:** 清洗和转换是 CPU/IO 密集型操作，必须异步执行（Celery），FastAPI 端点仅负责触发并返回 task_id。

---

### Step 5: 新增 Celery 异步任务

**文件:** `src/services/dataset_tasks.py`（新建）

| 任务 | 功能 | 进度阶段 |
|------|------|---------|
| `assemble_and_save_dataset` | 合并分块 + 创建 DB 记录 | merging → saving → done |
| `process_dataset_clean` | pandas 去重/缺失值处理 | reading → deduping → cleaning → saving |
| `convert_dataset_format` | 转换 Alpaca/ShareGPT + dataset_info.json | reading → converting → saving → done |

每个任务阶段通过 Redis Pub/Sub 发布进度：
```python
redis_client.publish(f"progress:{task_id}", json.dumps({
    "stage": "cleaning",
    "progress": 0.65,
    "message": "Removing duplicates..."
}))
```

---

### Step 6: 新增 API 端点

**文件:** `src/app/v1/dataset.py`（需完善）

| 方法 | 路径 | 用例 |
|------|------|------|
| `POST` | `/dataset/upload/initiate` | ChunkedUploadService.initiate |
| `POST` | `/dataset/upload/chunk` | ChunkedUploadService.upload_chunk |
| `POST` | `/dataset/upload/complete` | ChunkedUploadService.complete |
| `GET` | `/dataset/` | GetDatasetsService.get_all |
| `GET` | `/dataset/{id}` | GetDatasetsService.get_by_id |
| `DELETE` | `/dataset/{id}` | DeleteDatasetService.execute |
| `POST` | `/dataset/{id}/process` | ProcessDatasetService.execute |
| `GET` | `/tasks/{task_id}` | Celery AsyncResult 查询 |

---

### Step 7: ServiceFactory 更新 & 依赖注册

**文件:** `src/services/__init__.py`

新增属性/方法：

```python
def chunked_upload(self) -> ChunkedUploadService:
    if self._chunked_upload is None:
        self._chunked_upload = ChunkedUploadService(
            self.file_repo, self.dataset_repo
        )
    return self._chunked_upload

def delete_dataset(self) -> DeleteDatasetService:
    ...
```

新增 `DATA_DIR` 配置到 `config.py`:
```python
DATA_DIR: str = str(Path(__file__).resolve().parents[2].parent / "datafile")
```

---

## 4. 依赖关系图

```
config.py (DATA_DIR)
    └── windows_file_repo.py  ──────────────────────┐
                                                     ├── ChunkedUploadService
dataset.py (实体完善)                                 │
    └── mysql_dataset_repo.py ──────────────────────┤
                                                     │
dataset_create_service.py ──────────────────────────┤
datasets_get_service.py ────────────────────────────┤── ServiceFactory ── 路由
dataset_delete_service.py (新增) ───────────────────┤
dataset_process_service.py ─────────────────────────┤
    └── dataset_tasks.py (Celery) ──────────────────┘
```

---

## 5. 测试策略

| 层 | 测试类型 | 文件 |
|-----|---------|------|
| 实体 | 单元测试 | `tests/test_dataset.py` |
| 用例 | 单元测试 + mock 仓储 | `tests/test_dataset_create_service.py` 等 |
| 仓储 | 集成测试（需 MySQL） | `tests/test_mysql_dataset_repo.py` |
| 文件仓储 | 集成测试（本地文件系统） | `tests/test_windows_file_repo.py` |
| API 端点 | 集成测试（TestClient） | `tests/test_dataset_api.py` |

---

## 6. 实现顺序建议

按依赖链自底向上：

1. **Step 1** — 完善 Dataset 实体（无依赖）
2. **Step 2** — 实现 MysqlDatasetRepoAdapter（依赖 Step 1）
3. **Step 3** — 实现 WindowsFileRepo（依赖 config.DATA_DIR）
4. **Step 4abcd** — 实现用例服务（依赖 Step 2 + 3）
5. **Step 4e** — 完善 ProcessDatasetService（触发 Celery）
6. **Step 5** — 实现 Celery 任务（依赖 Step 2）
7. **Step 6** — 实现 API 端点（依赖 Step 4）
8. **Step 7** — 更新 ServiceFactory + config（贯穿）

---

## 7. 关键技术点

- **分块阈值:** 5MB/chunk，100MB 上限
- **文件存储隔离:** 每个 upload_id 独立目录，合并后清理
- **Celery 超时:** 30min hard / 25min soft（已在 celery_app 中配置）
- **进度推送:** Redis Pub/Sub `progress:{task_id}` → WebSocket manager → 前端
- **格式转换:** pandas 读取源文件 → 按行映射到 Alpaca/ShareGPT schema → JSON 输出 + 自动生成 `dataset_info.json`
- **错误处理:** 所有 Celery task 使用 `try/except/finally`，DB session 在 finally 中关闭，进度推送失败不影响主任务
