# External Integrations

**Analysis Date:** 2026-05-01

## Data Storage

### MySQL (Primary Database)

- **Provider:** MySQL (local/private cloud, self-managed)
- **Driver:** PyMySQL 1.1.0 (Windows-compatible, `1/backend/requirements.txt`)
- **ORM:** SQLAlchemy 2.0.23 with `declarative_base()`
- **Connection String:** `mysql+pymysql://root:password@localhost:3306/llama_factory`
  - Config location: `1/backend/app/core/config.py` → `settings.DATABASE_URL`
  - Default in `.env.example`: `1/backend/.env.example`
- **Session Management:** `1/backend/app/db/session.py`
  - Engine: pool_size=5, max_overflow=10, pool_pre_ping=True
  - Dependency injection: `get_db()` generator function for FastAPI `Depends()`
  - Used in endpoints: `1/backend/app/api/endpoints/datasets.py`
  - Used in Celery tasks: `1/backend/app/tasks/dataset_tasks.py`
- **Models:** `1/backend/app/db/models/__init__.py`
  - Tables: `users`, `datasets`, `training_tasks`, `trained_models`, `tags`
  - Enums: `UserRole`, `TaskStatus`, `ModelStatus`
- **Migrations:** Alembic 1.12.1 installed, but `alembic.ini` not yet configured (init_db.py creates tables directly)
- **Initialization:** `1/backend/app/db/init_db.py` — `python -m app.db.init_db` creates all tables

### File Storage (Local Filesystem)

- **Type:** Local filesystem directories (no external object storage)
- **Upload Chunks:** `datafile/chunks/` (project root level, outside backend/frontend)
  - Created by: `1/backend/app/api/endpoints/datasets.py` → `ensure_upload_dir()`
  - Used by: `1/backend/app/tasks/dataset_tasks.py` → `assemble_and_save_dataset()`
- **Final Datasets:** `datafile/datasets/`
  - Created by Celery tasks after chunk merging
  - Output formats: `.csv`, `.json`, `_alpaca.json`, `_sharegpt.json`, `_cleaned.csv`
  - Dataset info files: `*_dataset_info.json`

### Redis (Cache / Message Broker / PubSub)

- **Provider:** Redis (local/private cloud, self-managed)
- **Client:** redis-py 5.0.1 (`1/backend/requirements.txt`)
- **Database Allocation:**
  | Redis DB | Purpose | Config Key |
  |----------|---------|-------------|
  | `0` | General Redis / WebSocket PubSub subscriptions | `REDIS_URL` in `1/backend/app/core/config.py` |
  | `1` | Celery broker (task queue) | `CELERY_BROKER_URL` in `1/backend/app/core/config.py` |
  | `2` | Celery result backend (task results) | `CELERY_RESULT_BACKEND` in `1/backend/app/core/config.py` |
- **PubSub Channels:** Pattern `progress:{task_id}`
  - Publisher: Celery tasks in `1/backend/app/tasks/dataset_tasks.py` (via `client.publish()`)
  - Subscriber: `1/backend/app/core/redis_pubsub.py` (RedisPubSub class, `psubscribe('progress:*')`)
  - Bridge: Subscriber pushes messages to WebSocket via `manager.send_to_task()`
- **Connection Management:** Each Celery worker and the FastAPI lifespan manager create independent Redis connections

## Task Queue (Celery + Redis)

### Celery Configuration

- **Config Location:** `1/backend/app/core/celery_app.py`
- **Instance Name:** `llama_factory`
- **Broker:** `redis://localhost:6379/1`
- **Result Backend:** `redis://localhost:6379/2`
- **Serialization:** JSON (task_serializer, accept_content, result_serializer)
- **Task Limits:**
  - Hard time limit: 30 minutes (`task_time_limit`)
  - Soft time limit: 25 minutes (`task_soft_time_limit`)
- **Worker Pool:** `solo` (single-threaded, for Windows compatibility)
- **Included Modules:** `['app.tasks.dataset_tasks']`
- **Worker Start:** `celery -A app.core.celery_app worker --loglevel=info --pool=solo`

### Celery Tasks

| Task Name | Location | Purpose |
|-----------|----------|---------|
| `app.tasks.add` | `1/backend/app/tasks/__init__.py` | Demo: add two integers |
| `app.tasks.multiply` | `1/backend/app/tasks/__init__.py` | Demo: multiply two integers |
| `app.tasks.dataset_tasks.assemble_and_save_dataset` | `1/backend/app/tasks/dataset_tasks.py` | Merge uploaded chunks, create dataset record |
| `app.tasks.dataset_tasks.process_dataset_clean` | `1/backend/app/tasks/dataset_tasks.py` | Clean CSV/JSON datasets (dedup, fill missing) |
| `app.tasks.dataset_tasks.convert_dataset_format` | `1/backend/app/tasks/dataset_tasks.py` | Convert CSV/JSON to Alpaca or ShareGPT format |

### Task Dispatch Pattern

1. Frontend calls REST endpoint (e.g., `POST /api/v1/datasets/{id}/process`)
2. Endpoint invokes `task.delay(...)` in `1/backend/app/api/endpoints/datasets.py`
3. Celery worker picks up task from Redis broker
4. Task publishes progress via `redis_pubsub.publish()` to channel `progress:{task_id}`
5. FastAPI lifespan-managed subscriber receives progress and bridges to WebSocket
6. Client polls `GET /api/v1/datasets/tasks/{task_id}` for final result

## WebSocket (Real-time Communication)

### Backend WebSocket Server

- **Framework:** FastAPI native WebSocket + `websockets` 12.0
- **Endpoint Definitions:** `1/backend/app/api/endpoints/websocket.py`
- **Connection Manager:** `1/backend/app/core/websocket_manager.py` (`ConnectionManager` class)
- **PubSub Bridge:** `1/backend/app/core/redis_pubsub.py` (`RedisPubSub` class)

**WebSocket Endpoints:**

| Path | Purpose | Query Param |
|------|---------|-------------|
| `/ws/progress` | Task-specific progress streaming | `task_id` (required) |
| `/ws/broadcast` | Global broadcast for notifications | (none) |

**Connection Lifecycle:**
1. Frontend establishes WebSocket connection to `ws://host:port/ws/progress?task_id=xxx`
2. Server sends `{"type": "connected", "task_id": "..."}` confirmation
3. Server listens for client messages (`ping`, `get_status`) with 1-second timeout
4. Server sends `heartbeat` on timeout to keep connection alive
5. Celery tasks publish progress → Redis PubSub → `RedisPubSub._dispatch_to_websocket()` → `manager.send_to_task()` pushes to all clients listening to that task_id
6. On disconnect, connection is cleaned up from manager

**Message Protocol (Progress):**
```json
{
    "task_id": "abc-123",
    "current": 5,
    "total": 10,
    "percentage": 50,
    "phase": "merging",
    "status": "running",
    "message": "已合并 5/10 个分块",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### Frontend WebSocket Client

- **Implementation:** `1/frontend/src/utils/socket/index.ts` (`WebSocketClient` class)
- **Pattern:** Singleton with lazy initialization
- **Features:**
  - Auto-reconnect with exponential backoff (default: 20s base, max 10 attempts)
  - Heartbeat detection (5s interval)
  - Ping keepalive (10s interval)
  - Connection timeout (10s)
  - Message queue (buffers messages when disconnected)
  - Supports both per-task and broadcast connections

**WebSocket Usage in Frontend:**
- `1/frontend/src/store/modules/task.ts` (`useTaskStore`) manages task progress state
- Currently used in dataset upload and processing flows
- Progress displayed in `1/frontend/src/views/data-management/data-processing/modules/step3-execution.vue`

## REST API (Frontend ↔ Backend)

### API Architecture

- **Prefix:** `/api/v1` (defined in `1/backend/app/core/config.py` → `API_V1_STR`)
- **Router Aggregation:** `1/backend/app/api/router.py`
- **Endpoints:** `1/backend/app/api/endpoints/` directory

### Route Table

| Method | Path | Handler File | Purpose |
|--------|------|-------------|---------|
| GET | `/api/v1/health/` | `health.py` | Health check |
| POST | `/api/v1/auth/login` | `auth.py` | User login (dev mock) |
| GET | `/api/v1/user/info` | `users.py` | Current user info (dev mock) |
| POST | `/api/v1/tasks/add` | `tasks.py` | Demo: create add task |
| POST | `/api/v1/tasks/multiply` | `tasks.py` | Demo: create multiply task |
| GET | `/api/v1/tasks/{task_id}` | `tasks.py` | Demo: get task status |
| GET | `/api/v1/datasets/initiate-upload` | `datasets.py` | Start chunked upload |
| POST | `/api/v1/datasets/upload-chunk` | `datasets.py` | Upload one file chunk |
| POST | `/api/v1/datasets/complete-upload` | `datasets.py` | Finalize upload, trigger merge |
| GET | `/api/v1/datasets` | `datasets.py` | List all datasets |
| GET | `/api/v1/datasets/{dataset_id}` | `datasets.py` | Get dataset detail |
| DELETE | `/api/v1/datasets/{dataset_id}` | `datasets.py` | Delete dataset |
| POST | `/api/v1/datasets/{dataset_id}/process` | `datasets.py` | Trigger clean/convert task |
| GET | `/api/v1/datasets/tasks/{task_id}` | `datasets.py` | Get async task status |

### Frontend HTTP Client

- **Core Client:** `1/frontend/src/utils/http/index.ts`
  - Based on Axios 1.12.2
  - Singleton Axios instance with 15s timeout
  - Base URL from `VITE_API_URL` env var
  - Request interceptor: auto-attaches `Authorization` header from user store
  - Response interceptor: success code check (200), 401 auto-logout with debounce
  - Error handling: `1/frontend/src/utils/http/error.ts` (HttpError class, ElMessage notifications)
  - Status codes: `1/frontend/src/utils/http/status.ts` (ApiStatus enum)

**API Module Files:**
| File | Purpose |
|------|---------|
| `1/frontend/src/api/auth.ts` | Login (`POST /auth/login`), user info (`GET /user/info`) |
| `1/frontend/src/api/dataset.ts` | Full dataset CRUD, chunked upload, process/convert task dispatch |
| `1/frontend/src/api/data-manage.ts` | Mock data management (static dev fallbacks for dataset list, cleaning, processing) |
| `1/frontend/src/api/system-manage.ts` | User/role/menu list endpoints (partially mock) |

**API Communication Patterns:**
1. **Direct axios calls:** Chunked upload functions (`initiateUpload`, `uploadChunk`, `completeUpload`) use raw axios for FormData handling
2. **Wrapper requests:** CRUD operations use the custom `request` utility which provides auth header injection and error handling
3. **Mock fallbacks:** `data-manage.ts` provides mock implementations (`*Mock` functions) with simulated delays for development without backend

### CORS Configuration

- **Config Location:** `1/backend/app/main.py`
- **Allowed Origins:** `http://localhost:3000`, `http://localhost:5173` (from `settings.BACKEND_CORS_ORIGINS`)
- **Methods:** All (`*`)
- **Headers:** All (`*`)
- **Credentials:** Allowed (`allow_credentials=True`)

### Dev Proxy

- **Config Location:** `1/frontend/vite.config.ts`
- **Proxy Rules:**
  | Source | Target | Notes |
  |--------|--------|-------|
  | `/api` | `VITE_API_PROXY_URL` (dev: `http://localhost:8000`) | REST API proxy |
  | `/ws` | `VITE_API_PROXY_URL` with `ws` protocol replacement | WebSocket proxy with `ws: true` |
- Frontend dev on port 3000, backend on port 8000, proxy eliminates CORS issues in dev

## Authentication & Identity

**Auth Provider:** Custom (development mock mode)

- **Implementation:** `1/backend/app/api/endpoints/auth.py`
  - Hardcoded credentials: username `admin`, password `admin123`
  - Returns mock token: `mock-token-for-dev`
  - Returns mock refresh token: `mock-refresh-token-for-dev`
  - No JWT, no session, no database verification
- **Frontend Auth:** `1/frontend/src/store/modules/user.ts` (`useUserStore`)
  - Dev mode: `isLogin` defaults to `true`, `accessToken` defaults to `dev-token`
  - Token sent as `Authorization` header in Axios request interceptor
  - 401 responses trigger auto-logout with 3s debounce
  - Auth mode configurable via `VITE_ACCESS_MODE` (currently `frontend`)
- **No external auth provider** (no OAuth, OIDC, Keycloak, etc.)

## Inter-Service Communication Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Browser (Frontend)                        │
│  Vue 3 SPA on port 3000 (dev) / served as static files (prod)    │
│                                                                    │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────────────┐ │
│  │ HTTP Client  │  │ WebSocket     │  │ Pinia Stores           │ │
│  │ (Axios)      │  │ Client        │  │ (user, task, setting)  │ │
│  │ utils/http/  │  │ utils/socket/ │  │ store/modules/         │ │
│  └──────┬───────┘  └──────┬────────┘  └────────────────────────┘ │
└─────────┼─────────────────┼──────────────────────────────────────┘
          │ REST /api/v1    │ WS /ws/progress
          ▼                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Server (port 8000)                      │
│                    `1/backend/app/main.py`                        │
│                                                                    │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────────────┐ │
│  │ API Router   │  │ WebSocket     │  │ Redis PubSub Subscriber│ │
│  │ api/router   │  │ Endpoints     │  │ core/redis_pubsub.py   │ │
│  └──────┬───────┘  └──────┬────────┘  └───────────┬────────────┘ │
│         │                 │                        │              │
│         │    ┌────────────▼────────────────────────▼──┐           │
│         │    │         ConnectionManager               │           │
│         │    │    core/websocket_manager.py            │           │
│         │    └─────────────────────────────────────────┘           │
│         │                                                          │
│  ┌──────▼───────┐                                                  │
│  │ CRUD Layer   │  `1/backend/app/crud/`                          │
│  └──────┬───────┘                                                  │
│         │                                                          │
│  ┌──────▼───────┐  ┌──────────────────────────────────────────┐   │
│  │ SQLAlchemy   │  │ Celery App Instance                       │   │
│  │ Session      │  │ `1/backend/app/core/celery_app.py`        │   │
│  └──────┬───────┘  └────────────────┬─────────────────────────┘   │
└─────────┼───────────────────────────┼─────────────────────────────┘
          │ MySQL                     │ .delay() / .apply_async()
          ▼                           ▼
┌─────────────────┐    ┌─────────────────────────────────────────┐
│   MySQL Server  │    │           Redis Server                   │
│   port 3306     │    │           port 6379                      │
│                 │    │                                          │
│ DB: llama_factory│   │ DB 0: PubSub (progress:{task_id})       │
│ Tables:         │    │ DB 1: Celery Broker (task queue)        │
│  - users        │    │ DB 2: Celery Result Backend             │
│  - datasets     │    └────────────────┬────────────────────────┘
│  - tags         │                     │
│  - training_    │                     │ consume tasks
│    tasks        │                     ▼
│  - trained_     │    ┌─────────────────────────────────────────┐
│    models       │    │       Celery Worker (separate process)   │
└─────────────────┘    │       `celery -A app.core.celery_app`    │
                       │                                          │
                       │  Tasks:                                   │
                       │  - assemble_and_save_dataset              │
                       │  - process_dataset_clean                  │
                       │  - convert_dataset_format                 │
                       │                                          │
                       │  Publishes progress → Redis PubSub        │
                       │  Reads/Writes → MySQL (own session)       │
                       │  Reads/Writes → datafile/ (filesystem)    │
                       └──────────────────────────────────────────┘
```

**Key Communication Paths:**

1. **REST Request Flow:** Frontend → Vite proxy (dev) or direct → FastAPI → CRUD → MySQL → Response
2. **Async Task Flow:** Frontend → FastAPI → `task.delay()` → Redis(Broker) → Celery Worker → Task execution → Redis(Result) → Frontend polls `GET /tasks/{id}`
3. **Real-time Progress Flow:** Celery Worker → `redis.Publish(channel)` → Redis PubSub → FastAPI `RedisPubSub._listen_loop` → `manager.send_to_task()` → WebSocket → Frontend WebSocket Client → `useTaskStore`
4. **Chunked Upload Flow:** Frontend → `POST /datasets/initiate-upload` → `POST /datasets/upload-chunk` (multiple) → `POST /datasets/complete-upload` → `assemble_and_save_dataset.delay()` → Celery performs merge + DB write

## Monitoring & Observability

**Error Tracking:** None (no Sentry, Datadog, or equivalent)

**Logging:**
- Backend: Python `logging` module (`logging.basicConfig(level=logging.INFO)` in `1/backend/app/main.py`)
  - Logger instances created per module: `logger = logging.getLogger(__name__)`
  - Celery: self-managed via `--loglevel=info`
  - Some `print()` statements remain (e.g., `1/backend/app/db/init_db.py`, `1/backend/app/api/endpoints/auth.py`)
- Frontend: `console.log()` / `console.error()` with prefixed patterns (`[HTTP Error]`, `[WebSocket]`, `[RedisPubSub]`)

**Metrics:** None configured

## Environment Configuration

**Required Environment Variables (Backend):**
```
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/llama_factory
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

**Required Environment Variables (Frontend):**
```
VITE_API_URL=http://localhost:8000/api/v1
VITE_API_PROXY_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_PORT=3000
```

**Secrets Location:**
- `.env` file at `1/backend/.env` (contains actual credentials, not committed)
- `.env.example` at `1/backend/.env.example` (template)
- `.env` / `.env.development` / `.env.production` at `1/frontend/` (non-sensitive config, committed)

## CI/CD & Deployment

**Hosting:** Local/private cloud (self-hosted, no cloud platform)

**CI Pipeline:** None detected (no `docker-compose.yml`, `Dockerfile`, GitHub Actions, GitLab CI, etc.)

**Build Commands:**
```bash
# Frontend
cd 1/frontend && npm run build     # Production build → dist/
cd 1/frontend && npm run serve     # Preview production build

# Backend
cd 1/backend && python -m uvicorn app.main:app --reload --port 8000     # Dev
cd 1/backend && celery -A app.core.celery_app worker --loglevel=info --pool=solo  # Worker
cd 1/backend && python -m app.db.init_db                                  # Init DB
```

## Webhooks & Callbacks

**Incoming:** None

**Outgoing:** None

## External Services / APIs

**Current State:** No external SaaS or third-party API integrations

**Planned Integration (LLaMA-Factory):**
- LLaMA-Factory must be imported as a Python library (not subprocess), per project constraints
- No LLaMA-Factory imports detected in current codebase
- `pip freeze` not available to confirm package presence
- `pynvml` (NVIDIA GPU monitoring) suggests GPU integration is planned

**Mock/Development APIs:**
- Production env points to Apifox mock: `https://m1.apifoxmock.com/m1/6400575-6097373-default`
- Frontend mock data at `1/frontend/src/mock/temp/formData.ts`

---

*Integration audit: 2026-05-01*
