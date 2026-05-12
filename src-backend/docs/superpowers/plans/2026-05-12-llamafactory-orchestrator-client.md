# LlamaFactory Orchestrator Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在后端中落地一套可扩展的 LlamaFactory 集成：推理走 LlamaFactory 已公开的 OpenAI 兼容 `/v1` API，训练与数据集能力由后端通过本地工作区、CLI 与 Celery 自主管理。

**Architecture:** 适配器层拆成 `inference / dataset / training` 三个子客户端，并由 `LlamafactoryClient` 门面统一暴露。推理客户端只做同步 HTTP 调用；数据集同步负责把现有项目数据集复制进 LlamaFactory 工作区并维护 `dataset_info.json`；训练与批量推理通过服务层创建本地 `tasks` 记录，再由 Celery 任务执行 CLI / 批处理逻辑并持续回写状态。

**Tech Stack:** FastAPI、Pydantic、httpx、Celery、SQLAlchemy、subprocess、现有 `TaskRepository` / `DatasetRepositoryAdapter` / `WindowsFileRepository`

---

## Critical review before coding

1. 当前公开文档里稳定可见的 LlamaFactory HTTP API 主要是推理用的 OpenAI 兼容 `/v1` 接口；训练与数据集管理没有稳定公开的 HTTP 面，因此本计划按用户确认后的“后端自管编排”路线执行。
2. 当前 `tests/conftest.py` 仍引用已删除的 `src.db_connections.sqlite`，会导致任何新的 `pytest` 执行在收集阶段失败；第一项任务必须先修复测试基座，否则无法按 TDD 推进。
3. 当前仓库里存在命名漂移：`src/adapters/llmamafactory_client.py` 拼写错误，且有一个待删除路径 `src/adapters/llamafactory/__init__.py`。第一阶段必须先统一命名。

## File structure map

### New files

- `src/adapters/llamafactory_client.py` — 门面客户端，持有 `training / datasets / inference` 三个子客户端。
- `src/adapters/llamafactory_inference_client.py` — 对接 LlamaFactory OpenAI 兼容 `/v1/models` 与 `/v1/chat/completions`。
- `src/adapters/llamafactory_dataset_client.py` — 将项目内数据集复制到 LlamaFactory 数据目录，并维护 `dataset_info.json`。
- `src/adapters/llamafactory_training_client.py` — 生成训练 YAML 配置、启动 `llamafactory-cli train`、处理跨平台取消。
- `src/services/llamafactory_service.py` — Pydantic 请求/响应模型 + 业务编排（同步推理、数据集同步、训练/批推理任务创建、取消）。
- `src/tasks/llamafactory_tasks.py` — Celery 任务函数；训练执行器、批量推理执行器、任务状态回写辅助函数。
- `src/app/v1/llamafactory.py` — FastAPI 路由，暴露推理、数据集同步、训练创建/取消、批量推理创建接口。
- `tests/test_llamafactory_inference_client.py` — 推理客户端单测。
- `tests/test_llamafactory_dataset_client.py` — 数据集同步客户端单测。
- `tests/test_llamafactory_training_client.py` — 训练客户端单测。
- `tests/test_llamafactory_service.py` — 服务编排单测。
- `tests/test_llamafactory_tasks.py` — Celery 核心逻辑单测。
- `tests/test_llamafactory_router.py` — 路由单测（只验证路由层参数与状态码，不依赖真实数据库）。

### Modified files

- `tests/conftest.py` — 去掉对已删除 SQLite 模块的依赖，恢复 pytest 可运行状态。
- `src/core/config.py` — 增加 LlamaFactory 专用配置项。
- `src/adapters/celery_client.py` — 显式包含新的 Celery 任务模块。
- `src/services/__init__.py` — 暴露并装配新的 `LlamafactoryService`。
- `src/app/v1/apis.py` — 注册新的 `llamafactory` 路由。
- `.gitignore` — 加入 `.worktrees/`，避免后续 worktree 内容被追踪。

### Removed files

- `src/adapters/llmamafactory_client.py` — 错拼旧文件，替换为正确拼写的新门面客户端。
- `src/adapters/llamafactory/__init__.py` — 若确认无引用则彻底删除，避免双路径并存。

---

### Task 1: Repair pytest baseline and repository hygiene

**Files:**
- Modify: `tests/conftest.py`
- Modify: `.gitignore`
- Delete: `src/adapters/llmamafactory_client.py`
- Delete: `src/adapters/llamafactory/__init__.py`
- Test: `tests/test_http_client.py`

- [ ] **Step 1: Write the failing baseline check**

Create this smoke test file first so the failure mode is explicit:

```python
# tests/test_pytest_baseline.py
from src.services.interfaces.http_client import HTTPClientConfig


def test_pytest_collection_baseline():
    config = HTTPClientConfig(name="baseline", url="http://localhost:9999")
    assert config.name == "baseline"
```

- [ ] **Step 2: Run test collection to verify it fails for the known reason**

Run: `pytest tests/test_pytest_baseline.py -q`
Expected: FAIL during collection with `ModuleNotFoundError: No module named 'src.db_connections.sqlite'`

- [ ] **Step 3: Replace the broken SQLite fixture with a local SQLAlchemy test connection**

Rewrite `tests/conftest.py` to stop importing the deleted module:

```python
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.adapters.repositories.user_repo import UserRepositoryAdapter

_SERVICES_DIR = Path(__file__).resolve().parent.parent / "src" / "services"
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

TRUNCATE_USERS = text("DELETE FROM users")


class _TestSqliteConnection:
    def __init__(self, url: str = "sqlite+pysqlite:///:memory:", echo: bool = False):
        self._url = url
        self._echo = echo
        self._engine = None
        self._session_factory = None

    @property
    def engine(self):
        assert self._engine is not None
        return self._engine

    @property
    def is_connected(self) -> bool:
        return self._engine is not None

    def start(self, **_kwargs):
        if self._engine is None:
            self._engine = create_engine(self._url, echo=self._echo, future=True)
            self._session_factory = sessionmaker(bind=self._engine, autoflush=False, autocommit=False)

    def new_session(self) -> Session:
        assert self._session_factory is not None
        return self._session_factory()

    def dispose(self):
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._session_factory = None

    def create_tables(self, base):
        self.start()
        base.metadata.create_all(self.engine)

    def drop_tables(self, base):
        if self._engine is not None:
            base.metadata.drop_all(self.engine)


@pytest.fixture(scope="session")
def db_connection():
    conn = _TestSqliteConnection()
    conn.start()
    UserRepositoryAdapter(conn).init_table()
    yield conn
    conn.dispose()


@pytest.fixture
def repo(db_connection):
    with db_connection.new_session() as session:
        session.execute(TRUNCATE_USERS)
        session.commit()
    return UserRepositoryAdapter(db_connection)
```

Also add `.worktrees/` to `.gitignore`:

```gitignore
.worktrees/
```

- [ ] **Step 4: Remove the stale LlamaFactory placeholders**

Delete the wrong-spelling adapter and the stale package stub:

```bash
rm -f src/adapters/llmamafactory_client.py
rm -f src/adapters/llamafactory/__init__.py
```

- [ ] **Step 5: Run the baseline tests again**

Run: `pytest tests/test_pytest_baseline.py tests/test_http_client.py -q`
Expected: PASS with `2 passed` or more, and no import/collection errors.

- [ ] **Step 6: Prepare the change for review**

Run: `git add .gitignore tests/conftest.py tests/test_pytest_baseline.py src/adapters/llmamafactory_client.py src/adapters/llamafactory/__init__.py`
Expected: staged baseline-fix changes only.

---

### Task 2: Add configuration and facade scaffolding

**Files:**
- Create: `src/adapters/llamafactory_client.py`
- Modify: `src/core/config.py`
- Test: `tests/test_llamafactory_inference_client.py`

- [ ] **Step 1: Write the failing facade/config tests**

Create the test file with the first two tests:

```python
from src.core.config import Config


def test_llamafactory_config_defaults():
    cfg = Config()
    assert cfg.LLAMAFACTORY_API_PREFIX == "/v1"
    assert cfg.LLAMAFACTORY_TIMEOUT_MS == 30000
    assert cfg.LLAMAFACTORY_RETRIES == 2
    assert cfg.LLAMAFACTORY_DATA_DIR.endswith("data/llamafactory/data")
    assert cfg.LLAMAFACTORY_JOB_DIR.endswith("data/llamafactory/jobs")


def test_facade_exposes_named_slots():
    from src.adapters.llamafactory_client import LlamafactoryClient

    client = object.__new__(LlamafactoryClient)
    client.training = "training-client"
    client.datasets = "dataset-client"
    client.inference = "inference-client"

    assert client.training == "training-client"
    assert client.datasets == "dataset-client"
    assert client.inference == "inference-client"
```

- [ ] **Step 2: Run the tests to verify the missing config and module errors**

Run: `pytest tests/test_llamafactory_inference_client.py -q`
Expected: FAIL with missing `LLAMAFACTORY_API_PREFIX` and/or missing `src.adapters.llamafactory_client`.

- [ ] **Step 3: Extend `Config` with LlamaFactory orchestration settings**

Add these fields to `src/core/config.py` under the existing `LLAMAFACTORY_URL` setting:

```python
    LLAMAFACTORY_API_PREFIX: str = "/v1"
    LLAMAFACTORY_TIMEOUT_MS: int = 30000
    LLAMAFACTORY_RETRIES: int = 2
    LLAMAFACTORY_DATA_DIR: str = "data/llamafactory/data"
    LLAMAFACTORY_DATASET_INFO_PATH: str = "data/llamafactory/data/dataset_info.json"
    LLAMAFACTORY_JOB_DIR: str = "data/llamafactory/jobs"
    LLAMAFACTORY_TRAIN_COMMAND: str = "llamafactory-cli"
    LLAMAFACTORY_POLL_INTERVAL_SECONDS: int = 5
```

- [ ] **Step 4: Create the facade module with explicit constructor injection**

Create `src/adapters/llamafactory_client.py`:

```python
from src.adapters.llamafactory_dataset_client import LlamafactoryDatasetClient
from src.adapters.llamafactory_inference_client import LlamafactoryInferenceClient
from src.adapters.llamafactory_training_client import LlamafactoryTrainingClient
from src.services.interfaces.file_repository import FileRepository


class LlamafactoryClient:
    def __init__(
        self,
        *,
        file_repo: FileRepository,
        inference: LlamafactoryInferenceClient | None = None,
        datasets: LlamafactoryDatasetClient | None = None,
        training: LlamafactoryTrainingClient | None = None,
    ) -> None:
        self.inference = inference or LlamafactoryInferenceClient()
        self.datasets = datasets or LlamafactoryDatasetClient(file_repo=file_repo)
        self.training = training or LlamafactoryTrainingClient(file_repo=file_repo)
```

- [ ] **Step 5: Run the facade/config tests**

Run: `pytest tests/test_llamafactory_inference_client.py -q`
Expected: PASS with the two new tests green.

- [ ] **Step 6: Prepare the scaffold change for review**

Run: `git add src/core/config.py src/adapters/llamafactory_client.py tests/test_llamafactory_inference_client.py`
Expected: only config + facade scaffold changes staged.

---

### Task 3: Implement the synchronous inference client

**Files:**
- Create: `src/adapters/llamafactory_inference_client.py`
- Modify: `tests/test_llamafactory_inference_client.py`
- Test: `tests/test_llamafactory_inference_client.py`

- [ ] **Step 1: Extend the test file with failing client-behavior tests**

Append these tests to `tests/test_llamafactory_inference_client.py`:

```python
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def inference_client():
    with patch("src.services.interfaces.http_client.httpx.Client") as mock_client_cls:
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_http.get.return_value = mock_resp
        mock_http.request.return_value = MagicMock(is_server_error=False)
        mock_client_cls.return_value = mock_http

        from src.adapters.llamafactory_inference_client import LlamafactoryInferenceClient

        yield LlamafactoryInferenceClient(), mock_http


def test_inference_health_check_uses_models_endpoint(inference_client):
    client, mock_http = inference_client
    assert client._API_PREFIX == "/v1"
    mock_http.get.assert_called_with("/v1/models")


def test_list_models_uses_bearer_zero(inference_client):
    client, mock_http = inference_client
    client.list_models()
    mock_http.request.assert_called_with(
        method="GET",
        url="/v1/models",
        params=None,
        json=None,
        data=None,
        headers={"Authorization": "Bearer 0"},
        files=None,
    )


def test_chat_completion_posts_openai_payload(inference_client):
    client, mock_http = inference_client
    client.chat(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.2,
        max_tokens=64,
    )
    mock_http.request.assert_called_with(
        method="POST",
        url="/v1/chat/completions",
        params=None,
        json={
            "model": "meta-llama/Meta-Llama-3-8B-Instruct",
            "messages": [{"role": "user", "content": "hello"}],
            "temperature": 0.2,
            "max_tokens": 64,
        },
        data=None,
        headers={"Authorization": "Bearer 0"},
        files=None,
    )
```

- [ ] **Step 2: Run the inference-client tests to verify the missing module failure**

Run: `pytest tests/test_llamafactory_inference_client.py -q`
Expected: FAIL because `src.adapters.llamafactory_inference_client` does not exist yet.

- [ ] **Step 3: Implement `LlamafactoryInferenceClient`**

Create `src/adapters/llamafactory_inference_client.py`:

```python
from typing import Any, Mapping, Sequence

from httpx import Response

from src.core.config import config as proj_config
from src.services.interfaces.http_client import HTTPClient, HTTPClientConfig


class LlamafactoryInferenceClient(HTTPClient):
    _API_PREFIX = proj_config.LLAMAFACTORY_API_PREFIX

    def __init__(self, client_config: HTTPClientConfig | None = None) -> None:
        cfg = client_config or HTTPClientConfig(
            name="LlamaFactory Inference",
            url=proj_config.LLAMAFACTORY_URL,
            retries=proj_config.LLAMAFACTORY_RETRIES,
            timeout=proj_config.LLAMAFACTORY_TIMEOUT_MS,
        )
        super().__init__(cfg)

    def _check(self) -> bool:
        try:
            status = self._client.get(f"{self._API_PREFIX}/models")
            return not status.is_error
        except Exception:
            return False

    @staticmethod
    def _auth_headers(api_key: str = "0") -> Mapping[str, str]:
        return {"Authorization": f"Bearer {api_key}"}

    def list_models(self, api_key: str = "0") -> Response:
        return self.get(f"{self._API_PREFIX}/models", headers=self._auth_headers(api_key))

    def chat(
        self,
        *,
        model: str,
        messages: Sequence[dict[str, Any]],
        api_key: str = "0",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Response:
        payload: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        return self.post(
            f"{self._API_PREFIX}/chat/completions",
            json=payload,
            headers=self._auth_headers(api_key),
        )
```

- [ ] **Step 4: Run the inference unit tests**

Run: `pytest tests/test_llamafactory_inference_client.py -q`
Expected: PASS with all inference client tests green.

- [ ] **Step 5: Run the shared HTTP client regression test**

Run: `pytest tests/test_http_client.py tests/test_llamafactory_inference_client.py -q`
Expected: PASS; shared `HTTPClient` behavior still green.

- [ ] **Step 6: Prepare the inference adapter change for review**

Run: `git add src/adapters/llamafactory_inference_client.py tests/test_llamafactory_inference_client.py`
Expected: only inference adapter changes staged.

---

### Task 4: Implement dataset sync client and service orchestration

**Files:**
- Create: `src/adapters/llamafactory_dataset_client.py`
- Create: `src/services/llamafactory_service.py`
- Modify: `src/services/__init__.py`
- Create: `tests/test_llamafactory_dataset_client.py`
- Create: `tests/test_llamafactory_service.py`

- [ ] **Step 1: Write the failing dataset-sync tests**

Create `tests/test_llamafactory_dataset_client.py`:

```python
import json
from datetime import datetime
from pathlib import Path

from src.core.dataset import Dataset, DatasetMeta
from src.adapters.repositories.windows_file_repo import WindowsFileRepository


def test_sync_dataset_copies_file_and_updates_dataset_info(tmp_path):
    source = tmp_path / "source.jsonl"
    source.write_text('{"instruction":"hi","output":"there"}\n', encoding="utf-8")
    dataset = Dataset.new(
        owner_id=1,
        name="demo",
        meta=DatasetMeta(format="jsonl", file_path=str(source), file_size=source.stat().st_size),
        status=0,
    )
    file_repo = WindowsFileRepository()

    from src.adapters.llamafactory_dataset_client import LlamafactoryDatasetClient

    client = LlamafactoryDatasetClient(
        file_repo=file_repo,
        data_dir=str(tmp_path / "lf_data"),
        dataset_info_path=str(tmp_path / "lf_data" / "dataset_info.json"),
    )
    result = client.sync_dataset(dataset=dataset, dataset_name="demo_train")

    copied = tmp_path / "lf_data" / "demo_train.jsonl"
    assert copied.exists()
    info = json.loads((tmp_path / "lf_data" / "dataset_info.json").read_text(encoding="utf-8"))
    assert result["dataset_name"] == "demo_train"
    assert info["demo_train"]["file_name"] == "demo_train.jsonl"
```

Create `tests/test_llamafactory_service.py` with the first service test:

```python
from datetime import datetime
from unittest.mock import MagicMock

from src.core.dataset import Dataset, DatasetMeta


def test_sync_dataset_returns_not_found_when_dataset_missing():
    from src.services.llamafactory_service import LlamafactoryService, LlamafactoryDatasetSyncRequest

    dataset_repo = MagicMock()
    dataset_repo.find_by_id.return_value = None
    service = LlamafactoryService(
        dataset_repo=dataset_repo,
        task_repo=MagicMock(),
        file_repo=MagicMock(),
        llama_client=MagicMock(),
    )

    result = service.sync_dataset(LlamafactoryDatasetSyncRequest(dataset_id=99), owner_id=1)
    assert not result.success
    assert result.error == "Dataset not found: 99"
```

- [ ] **Step 2: Run the new tests to verify the missing-module failures**

Run: `pytest tests/test_llamafactory_dataset_client.py tests/test_llamafactory_service.py -q`
Expected: FAIL because the new adapter/service modules do not exist yet.

- [ ] **Step 3: Implement the dataset sync adapter**

Create `src/adapters/llamafactory_dataset_client.py`:

```python
import json
from pathlib import Path

from src.core.config import config
from src.core.dataset import Dataset
from src.services.interfaces.file_repository import FileRepository


class LlamafactoryDatasetClient:
    def __init__(
        self,
        *,
        file_repo: FileRepository,
        data_dir: str | None = None,
        dataset_info_path: str | None = None,
    ) -> None:
        self._file_repo = file_repo
        self._data_dir = Path(data_dir or config.LLAMAFACTORY_DATA_DIR)
        self._dataset_info_path = Path(dataset_info_path or config.LLAMAFACTORY_DATASET_INFO_PATH)

    def sync_dataset(self, *, dataset: Dataset, dataset_name: str | None = None) -> dict[str, str]:
        alias = dataset_name or f"dataset_{dataset.id}"
        ext = Path(dataset.meta.file_path).suffix or ".jsonl"
        target_name = f"{alias}{ext}"
        target_path = self._data_dir / target_name

        self._file_repo.makedirs(str(self._data_dir))
        self._file_repo.copy(dataset.meta.file_path, str(target_path))

        dataset_info = self._read_dataset_info()
        dataset_info[alias] = {"file_name": target_name}
        self._write_dataset_info(dataset_info)
        return {
            "dataset_name": alias,
            "file_name": target_name,
            "target_path": str(target_path),
        }

    def _read_dataset_info(self) -> dict:
        if not self._dataset_info_path.exists():
            return {}
        return json.loads(self._dataset_info_path.read_text(encoding="utf-8"))

    def _write_dataset_info(self, dataset_info: dict) -> None:
        self._dataset_info_path.parent.mkdir(parents=True, exist_ok=True)
        self._dataset_info_path.write_text(
            json.dumps(dataset_info, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
```

- [ ] **Step 4: Implement the service request/response models and sync method**

Create `src/services/llamafactory_service.py` with the sync path first:

```python
import json
from datetime import datetime
from typing import Any, Optional, Sequence

from pydantic import BaseModel, Field

from src.core.task_record import TaskRecord
from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.file_repository import FileRepository


class LlamafactoryDatasetSyncRequest(BaseModel):
    dataset_id: int
    dataset_name: str | None = Field(default=None, min_length=1, max_length=120)


class LlamafactoryDatasetSyncResponse(BaseModel):
    success: bool = False
    dataset_id: int | None = None
    dataset_name: str | None = None
    file_name: str | None = None
    target_path: str | None = None
    error: str | None = None


class LlamafactoryChatRequest(BaseModel):
    model: str
    messages: list[dict[str, Any]]
    temperature: float | None = Field(default=None, ge=0.0)
    max_tokens: int | None = Field(default=None, ge=1)


class LlamafactoryChatResponse(BaseModel):
    success: bool = False
    content: str | None = None
    raw_response: dict[str, Any] | None = None
    error: str | None = None


class LlamafactoryTrainingCreateRequest(BaseModel):
    dataset_id: int
    dataset_name: str
    model_name_or_path: str
    template: str
    stage: str = "sft"
    finetuning_type: str = "lora"
    output_name: str
    learning_rate: float = 1.0e-4
    num_train_epochs: float = 3.0
    per_device_train_batch_size: int = 1


class LlamafactoryBatchInferenceRequest(BaseModel):
    model: str
    inputs: list[str]
    temperature: float | None = Field(default=None, ge=0.0)
    max_tokens: int | None = Field(default=None, ge=1)
    output_name: str


class LlamafactoryTaskCreateResponse(BaseModel):
    success: bool = False
    task_id: int | None = None
    task_type: str | None = None
    status: str | None = None
    error: str | None = None


class LlamafactoryCancelResponse(BaseModel):
    success: bool = False
    task_id: int | None = None
    status: str | None = None
    error: str | None = None


class LlamafactoryService:
    def __init__(self, *, dataset_repo, task_repo, file_repo: FileRepository, llama_client, celery_client=None) -> None:
        self._dataset_repo = dataset_repo
        self._task_repo = task_repo
        self._file_repo = file_repo
        self._llama = llama_client
        self._celery = celery_client

    def sync_dataset(self, request: LlamafactoryDatasetSyncRequest, owner_id: int) -> LlamafactoryDatasetSyncResponse:
        dataset = self._dataset_repo.find_by_id(request.dataset_id)
        if dataset is None or dataset.owner_id != owner_id:
            return LlamafactoryDatasetSyncResponse(error=f"Dataset not found: {request.dataset_id}")

        result = self._llama.datasets.sync_dataset(dataset=dataset, dataset_name=request.dataset_name)
        return LlamafactoryDatasetSyncResponse(
            success=True,
            dataset_id=request.dataset_id,
            dataset_name=result["dataset_name"],
            file_name=result["file_name"],
            target_path=result["target_path"],
        )
```

- [ ] **Step 5: Wire the new service into `ServiceFactory`**

In `src/services/__init__.py`, add the imports and factory method:

```python
from src.services.llamafactory_service import (
    LlamafactoryService,
    LlamafactoryDatasetSyncRequest,
    LlamafactoryDatasetSyncResponse,
    LlamafactoryChatRequest,
    LlamafactoryChatResponse,
    LlamafactoryTrainingCreateRequest,
    LlamafactoryBatchInferenceRequest,
    LlamafactoryTaskCreateResponse,
    LlamafactoryCancelResponse,
)
```

Inside `ServiceFactory.__init__`:

```python
        self._llamafactory: Optional[LlamafactoryService] = None
```

Add the factory method near the other services:

```python
    def llamafactory(self) -> LlamafactoryService:
        if self._llamafactory is None:
            from src.adapters.celery_client import celery_client
            from src.adapters.llamafactory_client import LlamafactoryClient

            self._llamafactory = LlamafactoryService(
                dataset_repo=self.dataset_repo,
                task_repo=self.task_repo,
                file_repo=self.file_repo,
                llama_client=LlamafactoryClient(file_repo=self.file_repo),
                celery_client=celery_client,
            )
        return self._llamafactory
```

And in `dispose()`:

```python
        self._llamafactory = None
```

- [ ] **Step 6: Run dataset + service tests**

Run: `pytest tests/test_llamafactory_dataset_client.py tests/test_llamafactory_service.py -q`
Expected: PASS for dataset sync and not-found service behavior.

- [ ] **Step 7: Add a success-path service test and rerun**

Append this to `tests/test_llamafactory_service.py`:

```python
from src.core.dataset import Dataset, DatasetMeta


def test_sync_dataset_success_returns_alias():
    from src.services.llamafactory_service import LlamafactoryService, LlamafactoryDatasetSyncRequest

    dataset = Dataset.new(
        owner_id=7,
        name="demo",
        meta=DatasetMeta(format="jsonl", file_path="data/demo.jsonl", file_size=10),
        status=0,
    )
    dataset.id = 5

    dataset_repo = MagicMock()
    dataset_repo.find_by_id.return_value = dataset
    llama_client = MagicMock()
    llama_client.datasets.sync_dataset.return_value = {
        "dataset_name": "demo_train",
        "file_name": "demo_train.jsonl",
        "target_path": "data/llamafactory/data/demo_train.jsonl",
    }

    service = LlamafactoryService(
        dataset_repo=dataset_repo,
        task_repo=MagicMock(),
        file_repo=MagicMock(),
        llama_client=llama_client,
    )

    result = service.sync_dataset(LlamafactoryDatasetSyncRequest(dataset_id=5, dataset_name="demo_train"), owner_id=7)
    assert result.success is True
    assert result.dataset_name == "demo_train"
```

Run: `pytest tests/test_llamafactory_dataset_client.py tests/test_llamafactory_service.py -q`
Expected: PASS with the success path green.

- [ ] **Step 8: Prepare the dataset/service change for review**

Run: `git add src/adapters/llamafactory_dataset_client.py src/services/llamafactory_service.py src/services/__init__.py tests/test_llamafactory_dataset_client.py tests/test_llamafactory_service.py`
Expected: only dataset sync + service wiring staged.

---

### Task 5: Implement training and batch-inference Celery orchestration

**Files:**
- Create: `src/adapters/llamafactory_training_client.py`
- Create: `src/tasks/llamafactory_tasks.py`
- Modify: `src/adapters/celery_client.py`
- Modify: `src/services/llamafactory_service.py`
- Create: `tests/test_llamafactory_training_client.py`
- Create: `tests/test_llamafactory_tasks.py`

- [ ] **Step 1: Write the failing training-client tests**

Create `tests/test_llamafactory_training_client.py`:

```python
from pathlib import Path
from unittest.mock import MagicMock, patch


@patch("src.adapters.llamafactory_training_client.subprocess.Popen")
def test_launch_training_returns_pid(mock_popen, tmp_path):
    process = MagicMock()
    process.pid = 4321
    mock_popen.return_value = process

    from src.adapters.llamafactory_training_client import LlamafactoryTrainingClient
    from src.adapters.repositories.windows_file_repo import WindowsFileRepository

    client = LlamafactoryTrainingClient(file_repo=WindowsFileRepository(), job_dir=str(tmp_path))
    config_path = tmp_path / "train.yaml"
    config_path.write_text("stage: sft\n", encoding="utf-8")

    pid = client.launch_training(str(config_path))
    assert pid == 4321


def test_write_training_config_persists_yaml(tmp_path):
    from src.adapters.llamafactory_training_client import LlamafactoryTrainingClient
    from src.adapters.repositories.windows_file_repo import WindowsFileRepository

    client = LlamafactoryTrainingClient(file_repo=WindowsFileRepository(), job_dir=str(tmp_path))
    path = client.write_training_config(
        task_id=9,
        payload={
            "model_name_or_path": "meta-llama/Meta-Llama-3-8B-Instruct",
            "stage": "sft",
            "do_train": True,
            "dataset": "demo_train",
            "template": "llama3",
            "output_dir": "saves/demo",
        },
    )
    text = Path(path).read_text(encoding="utf-8")
    assert "model_name_or_path: meta-llama/Meta-Llama-3-8B-Instruct" in text
    assert "dataset: demo_train" in text
```

Create `tests/test_llamafactory_tasks.py` with the first pure-function test:

```python
from src.core.task_record import TaskRecord


def test_update_task_status_mutates_task_fields():
    from src.tasks.llamafactory_tasks import _update_task_status

    class Repo:
        def __init__(self):
            self.saved = None
        def find_by_id(self, task_id):
            return TaskRecord(id=task_id, owner_id=1, task_name="x", task_type="training")
        def update(self, task_id, task):
            self.saved = task
            return None

    repo = Repo()
    _update_task_status(repo, task_id=1, status="running", progress=0.5, phase="训练中")
    assert repo.saved.status == "running"
    assert repo.saved.progress == 0.5
    assert repo.saved.phase == "训练中"
```

- [ ] **Step 2: Run the new tests to verify missing-module failures**

Run: `pytest tests/test_llamafactory_training_client.py tests/test_llamafactory_tasks.py -q`
Expected: FAIL because the training client and task module do not exist yet.

- [ ] **Step 3: Implement the training adapter**

Create `src/adapters/llamafactory_training_client.py`:

```python
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.core.config import config
from src.services.interfaces.file_repository import FileRepository


class LlamafactoryTrainingClient:
    def __init__(self, *, file_repo: FileRepository, job_dir: str | None = None) -> None:
        self._file_repo = file_repo
        self._job_dir = Path(job_dir or config.LLAMAFACTORY_JOB_DIR)

    def write_training_config(self, *, task_id: int, payload: dict[str, Any]) -> str:
        self._job_dir.mkdir(parents=True, exist_ok=True)
        config_path = self._job_dir / f"train_{task_id}.yaml"
        lines: list[str] = []
        for key, value in payload.items():
            if isinstance(value, bool):
                lines.append(f"{key}: {'true' if value else 'false'}")
            else:
                lines.append(f"{key}: {value}")
        config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(config_path)

    def launch_training(self, config_path: str) -> int:
        process = subprocess.Popen(
            [config.LLAMAFACTORY_TRAIN_COMMAND, "train", config_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        return process.pid

    def cancel_process(self, pid: int) -> None:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
        else:
            os.kill(pid, 15)
```

- [ ] **Step 4: Add task creation methods to the service**

Append these methods to `src/services/llamafactory_service.py` inside `LlamafactoryService`:

```python
    def create_training_task(self, request: LlamafactoryTrainingCreateRequest, owner_id: int) -> LlamafactoryTaskCreateResponse:
        dataset = self._dataset_repo.find_by_id(request.dataset_id)
        if dataset is None or dataset.owner_id != owner_id:
            return LlamafactoryTaskCreateResponse(error=f"Dataset not found: {request.dataset_id}")

        sync_result = self._llama.datasets.sync_dataset(dataset=dataset, dataset_name=request.dataset_name)
        task = TaskRecord(
            owner_id=owner_id,
            task_name=request.output_name,
            task_type="training",
            status="pending",
            config=TaskRecord.config_to_json({
                "kind": "training",
                "dataset_id": request.dataset_id,
                "dataset_name": sync_result["dataset_name"],
                "model_name_or_path": request.model_name_or_path,
                "template": request.template,
                "stage": request.stage,
                "finetuning_type": request.finetuning_type,
                "output_name": request.output_name,
                "learning_rate": request.learning_rate,
                "num_train_epochs": request.num_train_epochs,
                "per_device_train_batch_size": request.per_device_train_batch_size,
            }),
        )
        error = self._task_repo.insert(task)
        if error:
            return LlamafactoryTaskCreateResponse(error=str(error))

        if self._celery is not None:
            async_result = self._celery.send_task("llamafactory.training.run", kwargs={"task_id": task.id})
            task.config = TaskRecord.config_to_json({**task.config_dict, "celery_task_id": async_result.id})
            self._task_repo.update(task.id, task)

        return LlamafactoryTaskCreateResponse(success=True, task_id=task.id, task_type="training", status="pending")

    def create_batch_inference_task(self, request: LlamafactoryBatchInferenceRequest, owner_id: int) -> LlamafactoryTaskCreateResponse:
        task = TaskRecord(
            owner_id=owner_id,
            task_name=request.output_name,
            task_type="inference",
            status="pending",
            config=TaskRecord.config_to_json({
                "kind": "batch_inference",
                "model": request.model,
                "inputs": request.inputs,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "output_name": request.output_name,
            }),
        )
        error = self._task_repo.insert(task)
        if error:
            return LlamafactoryTaskCreateResponse(error=str(error))

        if self._celery is not None:
            async_result = self._celery.send_task("llamafactory.inference.batch.run", kwargs={"task_id": task.id})
            task.config = TaskRecord.config_to_json({**task.config_dict, "celery_task_id": async_result.id})
            self._task_repo.update(task.id, task)

        return LlamafactoryTaskCreateResponse(success=True, task_id=task.id, task_type="inference", status="pending")

    def cancel_task(self, task_id: int, owner_id: int) -> LlamafactoryCancelResponse:
        task = self._task_repo.find_by_id(task_id)
        if task is None or task.owner_id != owner_id:
            return LlamafactoryCancelResponse(error=f"Task not found: {task_id}")

        cfg = task.config_dict
        pid = cfg.get("pid")
        if task.task_type == "training" and pid:
            self._llama.training.cancel_process(pid)
        task.status = "cancelled"
        task.phase = "已取消"
        task.updated_at = datetime.now()
        self._task_repo.update(task.id, task)
        return LlamafactoryCancelResponse(success=True, task_id=task.id, status="cancelled")
```

- [ ] **Step 5: Implement pure Celery task helpers and task entrypoints**

Create `src/tasks/llamafactory_tasks.py`:

```python
import json
from datetime import datetime
from pathlib import Path

from src.adapters.llamafactory_client import LlamafactoryClient
from src.adapters.repositories.dataset_repo import DatasetRepositoryAdapter
from src.adapters.repositories.task_repo import TaskRepository
from src.adapters.repositories.windows_file_repo import WindowsFileRepository
from src.adapters.celery_client import celery_client
from src.core.config import config
from src.db_connections import create_db_connection


def _build_dependencies():
    conn = create_db_connection(config.DATABASE_URL)
    conn.start()
    task_repo = TaskRepository(conn)
    task_repo.init_table()
    dataset_repo = DatasetRepositoryAdapter(conn)
    dataset_repo.init_table()
    file_repo = WindowsFileRepository()
    llama_client = LlamafactoryClient(file_repo=file_repo)
    return conn, task_repo, dataset_repo, file_repo, llama_client


def _update_task_status(task_repo, *, task_id: int, status: str, progress: float, phase: str, config_patch: dict | None = None):
    task = task_repo.find_by_id(task_id)
    if task is None:
        return
    task.status = status
    task.progress = progress
    task.phase = phase
    if config_patch:
        merged = {**task.config_dict, **config_patch}
        task.config = task.config_to_json(merged)
    task.updated_at = datetime.now()
    task_repo.update(task_id, task)


@celery_client.task(name="llamafactory.training.run")
def run_training_task(task_id: int):
    conn, task_repo, _dataset_repo, _file_repo, llama_client = _build_dependencies()
    try:
        task = task_repo.find_by_id(task_id)
        if task is None or task.status == "cancelled":
            return
        cfg = task.config_dict
        payload = {
            "model_name_or_path": cfg["model_name_or_path"],
            "stage": cfg["stage"],
            "do_train": True,
            "finetuning_type": cfg["finetuning_type"],
            "dataset": cfg["dataset_name"],
            "template": cfg["template"],
            "output_dir": f"saves/{cfg['output_name']}",
            "learning_rate": cfg["learning_rate"],
            "num_train_epochs": cfg["num_train_epochs"],
            "per_device_train_batch_size": cfg["per_device_train_batch_size"],
        }
        config_path = llama_client.training.write_training_config(task_id=task_id, payload=payload)
        pid = llama_client.training.launch_training(config_path)
        _update_task_status(task_repo, task_id=task_id, status="running", progress=0.1, phase="训练启动", config_patch={"pid": pid, "config_path": config_path})
        _update_task_status(task_repo, task_id=task_id, status="done", progress=1.0, phase="训练完成")
    except Exception as exc:
        _update_task_status(task_repo, task_id=task_id, status="failed", progress=1.0, phase=str(exc))
        raise
    finally:
        conn.dispose()


@celery_client.task(name="llamafactory.inference.batch.run")
def run_batch_inference_task(task_id: int):
    conn, task_repo, _dataset_repo, file_repo, llama_client = _build_dependencies()
    try:
        task = task_repo.find_by_id(task_id)
        if task is None or task.status == "cancelled":
            return
        cfg = task.config_dict
        inputs = cfg["inputs"]
        output_dir = Path(config.LOG_DIR) / "llamafactory_inference"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"task_{task_id}.jsonl"

        _update_task_status(task_repo, task_id=task_id, status="running", progress=0.0, phase="批量推理开始", config_patch={"output_path": str(output_path)})

        rows: list[str] = []
        for idx, text in enumerate(inputs, start=1):
            latest = task_repo.find_by_id(task_id)
            if latest is None or latest.status == "cancelled":
                return
            resp = llama_client.inference.chat(model=cfg["model"], messages=[{"role": "user", "content": text}], temperature=cfg.get("temperature"), max_tokens=cfg.get("max_tokens"))
            data = resp.json()
            rows.append(json.dumps({"input": text, "response": data}, ensure_ascii=False))
            output_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            _update_task_status(task_repo, task_id=task_id, status="running", progress=idx / len(inputs), phase=f"已完成 {idx}/{len(inputs)}")

        _update_task_status(task_repo, task_id=task_id, status="done", progress=1.0, phase="批量推理完成")
    except Exception as exc:
        _update_task_status(task_repo, task_id=task_id, status="failed", progress=1.0, phase=str(exc))
        raise
    finally:
        conn.dispose()
```

- [ ] **Step 6: Make Celery import the new task module**

Modify `src/adapters/celery_client.py` so the task module is loaded by the worker:

```python
celery_client.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_soft_time_limit=25 * 60,
    task_time_limit=30 * 60,
    task_track_started=True,
    include=["src.tasks.llamafactory_tasks"],
)
```

- [ ] **Step 7: Add service tests for async task creation and cancel**

Append to `tests/test_llamafactory_service.py`:

```python
from unittest.mock import MagicMock


def test_create_training_task_dispatches_celery():
    from src.services.llamafactory_service import LlamafactoryService, LlamafactoryTrainingCreateRequest
    from src.core.dataset import Dataset, DatasetMeta

    dataset = Dataset.new(
        owner_id=3,
        name="demo",
        meta=DatasetMeta(format="jsonl", file_path="data/demo.jsonl", file_size=10),
        status=0,
    )
    dataset.id = 11

    task_repo = MagicMock()
    task_repo.insert.return_value = None
    task_repo.update.return_value = None
    task_repo.find_by_id.side_effect = []

    celery_result = MagicMock(id="celery-123")
    celery_client = MagicMock()
    celery_client.send_task.return_value = celery_result

    llama_client = MagicMock()
    llama_client.datasets.sync_dataset.return_value = {
        "dataset_name": "demo_train",
        "file_name": "demo_train.jsonl",
        "target_path": "data/llamafactory/data/demo_train.jsonl",
    }

    service = LlamafactoryService(
        dataset_repo=MagicMock(find_by_id=MagicMock(return_value=dataset)),
        task_repo=task_repo,
        file_repo=MagicMock(),
        llama_client=llama_client,
        celery_client=celery_client,
    )

    result = service.create_training_task(
        LlamafactoryTrainingCreateRequest(
            dataset_id=11,
            dataset_name="demo_train",
            model_name_or_path="meta-llama/Meta-Llama-3-8B-Instruct",
            template="llama3",
            output_name="demo-sft",
        ),
        owner_id=3,
    )
    assert result.success is True
    celery_client.send_task.assert_called_once_with("llamafactory.training.run", kwargs={"task_id": task_repo.insert.call_args[0][0].id})
```

Append to `tests/test_llamafactory_tasks.py`:

```python
from unittest.mock import MagicMock, patch


@patch("src.tasks.llamafactory_tasks._build_dependencies")
def test_run_training_task_marks_done(mock_build):
    from src.core.task_record import TaskRecord
    from src.tasks.llamafactory_tasks import run_training_task

    task_repo = MagicMock()
    task_repo.find_by_id.side_effect = [
        TaskRecord(id=5, owner_id=1, task_name="train", task_type="training", config=TaskRecord.config_to_json({
            "model_name_or_path": "meta-llama/Meta-Llama-3-8B-Instruct",
            "stage": "sft",
            "finetuning_type": "lora",
            "dataset_name": "demo_train",
            "template": "llama3",
            "output_name": "demo-sft",
            "learning_rate": 1.0e-4,
            "num_train_epochs": 3.0,
            "per_device_train_batch_size": 1,
        })),
        TaskRecord(id=5, owner_id=1, task_name="train", task_type="training", config=TaskRecord.config_to_json({})),
    ]
    llama_client = MagicMock()
    llama_client.training.write_training_config.return_value = "data/llamafactory/jobs/train_5.yaml"
    llama_client.training.launch_training.return_value = 999
    conn = MagicMock()

    mock_build.return_value = (conn, task_repo, MagicMock(), MagicMock(), llama_client)

    run_training_task(task_id=5)
    assert task_repo.update.call_count >= 2
    conn.dispose.assert_called_once()
```

- [ ] **Step 8: Run the orchestration tests**

Run: `pytest tests/test_llamafactory_training_client.py tests/test_llamafactory_tasks.py tests/test_llamafactory_service.py -q`
Expected: PASS with training client, task helper, and async-service tests green.

- [ ] **Step 9: Prepare the orchestration change for review**

Run: `git add src/adapters/llamafactory_training_client.py src/tasks/llamafactory_tasks.py src/adapters/celery_client.py src/services/llamafactory_service.py tests/test_llamafactory_training_client.py tests/test_llamafactory_tasks.py tests/test_llamafactory_service.py`
Expected: only training / batch orchestration changes staged.

---

### Task 6: Add API routes and final end-to-end verifications

**Files:**
- Create: `src/app/v1/llamafactory.py`
- Modify: `src/app/v1/apis.py`
- Modify: `tests/test_llamafactory_service.py`
- Create: `tests/test_llamafactory_router.py`

- [ ] **Step 1: Write the failing router tests**

Create `tests/test_llamafactory_router.py`:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.app.v1.llamafactory import router


def _build_app(service_mock):
    app = FastAPI()
    app.include_router(router)
    app.state.services = MagicMock(llamafactory=MagicMock(return_value=service_mock))
    return app


def test_chat_endpoint_returns_400_when_service_fails():
    from src.services.llamafactory_service import LlamafactoryChatResponse

    service = MagicMock()
    service.chat.return_value = LlamafactoryChatResponse(error="upstream error")
    app = _build_app(service)
    client = TestClient(app)

    response = client.post(
        "/llamafactory/inference/chat",
        json={"model": "demo", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 400
```

- [ ] **Step 2: Run the router test to verify the route module is missing**

Run: `pytest tests/test_llamafactory_router.py -q`
Expected: FAIL because `src.app.v1.llamafactory` does not exist yet.

- [ ] **Step 3: Finish the service chat path and create the router**

Append the synchronous chat method to `src/services/llamafactory_service.py`:

```python
    def chat(self, request: LlamafactoryChatRequest) -> LlamafactoryChatResponse:
        try:
            response = self._llama.inference.chat(
                model=request.model,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return LlamafactoryChatResponse(success=True, content=content, raw_response=data)
        except Exception as exc:
            return LlamafactoryChatResponse(error=str(exc))
```

Create `src/app/v1/llamafactory.py`:

```python
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.app.dependencies import get_current_user, get_services
from src.services import ServiceFactory
from src.services.jwt_service import TokenPayload
from src.services.llamafactory_service import (
    LlamafactoryBatchInferenceRequest,
    LlamafactoryChatRequest,
    LlamafactoryDatasetSyncRequest,
    LlamafactoryTrainingCreateRequest,
)

router = APIRouter(prefix="/llamafactory", tags=["llamafactory"])


@router.post("/datasets/sync")
def sync_dataset(
    request: LlamafactoryDatasetSyncRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    result = svc.llamafactory().sync_dataset(request, owner_id=int(current_user.user_id))
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=404)
    return result


@router.post("/training/jobs")
def create_training_job(
    request: LlamafactoryTrainingCreateRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    result = svc.llamafactory().create_training_task(request, owner_id=int(current_user.user_id))
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=400)
    return result


@router.post("/inference/chat")
def chat(
    request: LlamafactoryChatRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    result = svc.llamafactory().chat(request)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=400)
    return result


@router.post("/inference/batch")
def create_batch_inference_job(
    request: LlamafactoryBatchInferenceRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    result = svc.llamafactory().create_batch_inference_task(request, owner_id=int(current_user.user_id))
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=400)
    return result


@router.post("/tasks/{task_id}/cancel")
def cancel_task(
    task_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    result = svc.llamafactory().cancel_task(task_id, owner_id=int(current_user.user_id))
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=404)
    return result
```

- [ ] **Step 4: Register the new router in API v1**

Modify `src/app/v1/apis.py`:

```python
from src.app.v1.llamafactory import router as llamafactory_router
api_v1.include_router(llamafactory_router)
```

Place the import and `include_router` alongside the existing `task_router` include.

- [ ] **Step 5: Add router dependency overrides and rerun tests**

Update `tests/test_llamafactory_router.py` to override auth and services before creating `TestClient`:

```python
from src.app.dependencies import get_current_user, get_services
from src.services.jwt_service import TokenPayload


def _build_app(service_mock):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: TokenPayload(user_id="1", email="demo@test.com", exp=0)
    app.dependency_overrides[get_services] = lambda: MagicMock(llamafactory=MagicMock(return_value=service_mock))
    return app
```

Run: `pytest tests/test_llamafactory_router.py -q`
Expected: PASS with the route layer returning the expected status codes.

- [ ] **Step 6: Run the complete targeted verification suite**

Run: `pytest tests/test_pytest_baseline.py tests/test_http_client.py tests/test_llamafactory_inference_client.py tests/test_llamafactory_dataset_client.py tests/test_llamafactory_training_client.py tests/test_llamafactory_service.py tests/test_llamafactory_tasks.py tests/test_llamafactory_router.py -q`
Expected: PASS with all new targeted tests green.

- [ ] **Step 7: Run one import/typing sanity check**

Run: `python -m compileall src`
Expected: all files under `src/` compile without syntax errors.

- [ ] **Step 8: Prepare the final feature set for review**

Run: `git add src/app/v1/llamafactory.py src/app/v1/apis.py src/services/llamafactory_service.py tests/test_llamafactory_router.py`
Expected: route integration changes staged on top of the already-validated feature files.

---

## Self-review checklist

### Spec coverage

- 训练：Task 5 覆盖训练任务创建、CLI 配置写入、Celery 执行与取消。
- 数据集：Task 4 覆盖项目数据集同步到 LlamaFactory 工作区与 `dataset_info.json` 维护。
- 推理：Task 3 覆盖同步 chat 调用；Task 5 覆盖批量推理异步任务。
- Celery：Task 5 覆盖纯函数状态回写、训练执行器、批量推理执行器。
- API：Task 6 暴露同步推理、数据集同步、训练创建、批量推理创建、任务取消。

### Placeholder scan

- 没有 `TODO` / `TBD` / “类似前一任务” 之类占位。
- 每个需要改代码的步骤都给出了要写入的具体代码。
- 每个验证步骤都给了具体命令和预期结果。

### Type consistency

- 服务层统一使用 `Llamafactory*Request/Response` 命名。
- 门面客户端统一暴露 `training / datasets / inference`。
- Celery 任务名统一为 `llamafactory.training.run` 与 `llamafactory.inference.batch.run`。
- 训练任务使用 `task_type="training"`，批量推理使用 `task_type="inference"`，与现有 `TASK_TYPE` 保持一致。
