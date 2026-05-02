# Architecture

**Analysis Date:** 2026-05-01

## Pattern Overview

**Overall:** Layered Monolith (API + Worker), paired with independent Vue SPA frontend. Two-service architecture: Python FastAPI backend + Vue 3 frontend, communicating via REST API and WebSocket.

**Key Characteristics:**
- REST API with `/api/v1` prefix between frontend and backend
- Async task processing via Celery + Redis for long-running LLM dataset operations
- Real-time progress push via WebSocket + Redis Pub/Sub bridge (supports multi-worker)
- SQLAlchemy ORM with MySQL for persistent storage
- Vite dev proxy bridges frontend to backend during development
- Vue 3 Composition API with `<script setup>` throughout frontend
- Pinia stores with localStorage persistence for state management

## Layers

**Presentation Layer (Frontend):**
- Purpose: User interface for LLM fine-tuning workstation management
- Location: `1/frontend/src/`
- Contains: Vue 3 SFCs (`.vue`), TypeScript modules, Pinia stores, Vue Router config, API client modules, WebSocket client, i18n, hooks (composables), type definitions
- Depends on: Backend REST API (`/api/v1`), WebSocket server (`/ws`)
- Used by: End users (browser)

**API Layer (Backend):**
- Purpose: REST API endpoint definitions, request handling, WebSocket endpoints
- Location: `1/backend/app/api/`
- Contains: FastAPI routers (`router.py` aggregates all endpoint routers), endpoint modules (`health.py`, `auth.py`, `tasks.py`, `users.py`, `datasets.py`, `websocket.py`), inline Pydantic request/response schemas (some moved to `app/schemas/`)
- Depends on: CRUD layer, Celery tasks, Pydantic schemas, `get_db` dependency injection
- Used by: Frontend HTTP client (`1/frontend/src/utils/http/index.ts`) and WebSocket client (`1/frontend/src/utils/socket/index.ts`)

**Core Layer (Backend):**
- Purpose: Application configuration, shared infrastructure, cross-cutting concerns
- Location: `1/backend/app/core/`
- Contains: `config.py` (pydantic-settings singleton), `celery_app.py` (Celery instance), `websocket_manager.py` (ConnectionManager singleton), `redis_pubsub.py` (Redis Pub/Sub subscriber that bridges Celery progress to WebSocket)
- Depends on: Environment variables (`.env`)
- Used by: All backend modules

**CRUD / Data Access Layer (Backend):**
- Purpose: Database read/write operations
- Location: `1/backend/app/crud/`
- Contains: `dataset.py` (fully implemented CRUD for datasets), empty `__init__.py`
- Depends on: SQLAlchemy session (`Session`), `app.db.models`
- Used by: API endpoints (`datasets.py`), Celery tasks (`dataset_tasks.py`)
- Status: Only `dataset.py` implemented; no CRUD for `User`, `TrainingTask`, `TrainedModel`, `Tag`

**Schema Layer (Backend):**
- Purpose: Pydantic models for request/response validation and serialization
- Location: `1/backend/app/schemas/`
- Contains: `dataset.py` (DatasetCreate, DatasetResponse, Upload*, Process*, TaskStatusResponse), empty `__init__.py`
- Depends on: None (pure data models)
- Used by: API endpoints (`datasets.py`), CRUD (`dataset.py`)
- Status: Only dataset schemas defined; auth/tasks/users schemas are inline in endpoint files

**Service Layer (Backend):**
- Purpose: Business logic orchestration
- Location: `1/backend/app/services/`
- Contains: Empty `__init__.py` only — **not implemented**
- Depends on: Planned to depend on CRUD, Celery, LLaMA-Factory
- Used by: Not yet used; business logic currently embedded in API endpoints and Celery tasks directly

**Task Layer (Backend):**
- Purpose: Asynchronous background job execution via Celery
- Location: `1/backend/app/tasks/`
- Contains: `__init__.py` (legacy `add`/`multiply` example tasks), `dataset_tasks.py` (assembly, cleaning, format conversion with real-time Redis Pub/Sub progress)
- Depends on: `app.core.celery_app`, `app.crud.dataset`, `app.schemas.dataset`, Redis
- Used by: API endpoints dispatch tasks via `.delay()`

**Database Layer (Backend):**
- Purpose: Database models, session management, and initialization
- Location: `1/backend/app/db/`
- Contains: `session.py` (engine, SessionLocal, declarative `Base`, `get_db` generator), `init_db.py` (table creation script), `models/__init__.py` (all model classes: `User`, `Dataset`, `Tag`, `TrainingTask`, `TrainedModel`)
- Depends on: `app.core.config` for `DATABASE_URL`
- Used by: CRUD layer, API endpoints (via `get_db` dependency injection), Celery tasks

**Presentation State Layer (Frontend):**
- Purpose: Reactive state management with persistence
- Location: `1/frontend/src/store/`
- Contains: `index.ts` (Pinia setup with persistedstate plugin), `modules/` (domain stores: `user.ts`, `menu.ts`, `setting.ts`, `table.ts`, `task.ts`, `worktab.ts`)
- Depends on: Pinia, localStorage, Vue Router (for navigation in `logOut()`)
- Used by: All Vue components, composables, router guards

**HTTP Client Layer (Frontend):**
- Purpose: Centralized HTTP communication with interceptors, retry, auth
- Location: `1/frontend/src/utils/http/index.ts`
- Contains: Axios instance, request/response interceptors (token injection, error handling, 401 redirect), retry logic, status codes (`status.ts`), error types (`error.ts`)
- Depends on: Axios, user store, i18n
- Used by: All API modules in `1/frontend/src/api/`

**WebSocket Client Layer (Frontend):**
- Purpose: Persistent WebSocket connection with singleton pattern, reconnection, message queue, heartbeats
- Location: `1/frontend/src/utils/socket/index.ts`
- Contains: `WebSocketClient` class (singleton), connect/reconnect/send, heartbeat/ping timers, message queue for offline buffering, exponential backoff reconnection
- Depends on: Browser WebSocket API
- Used by: Task progress monitoring, real-time notifications

## Data Flow

**Dataset Upload Flow (Chunked):**
1. Frontend chunkifies file client-side → calls `initiateUpload()` (`GET /api/v1/datasets/initiate-upload`)
2. Backend returns `upload_id`, `chunk_size`, `total_chunks`
3. Frontend uploads chunks in batches of 3 → `POST /api/v1/datasets/upload-chunk` per chunk
4. Backend writes each chunk to `datafile/chunks/` on disk
5. Frontend calls `completeUpload()` → `POST /api/v1/datasets/complete-upload`
6. Backend endpoint dispatches `assemble_and_save_dataset.delay()` Celery task
7. Worker merges chunks → creates DB record via `crud.create_dataset()` → publishes progress to Redis `progress:{task_id}` channel
8. Redis Pub/Sub subscriber (`app.core.redis_pubsub`) picks up progress → pushes to WebSocket via `ConnectionManager`
9. Frontend WebSocket receives progress updates → updates `useTaskStore`

**Dataset Processing Flow (Clean/Convert):**
1. Frontend calls `POST /api/v1/datasets/{id}/process` with `ProcessRequest`
2. Backend dispatches `process_dataset_clean.delay()` or `convert_dataset_format.delay()`
3. Worker reads dataset file, processes in stages (reading → deduping → cleaning → saving / format conversion), publishes granular progress per stage
4. Progress flows: Redis Pub/Sub → WebSocket → frontend `useTaskStore`

**Auth Flow (Mock):**
1. Frontend calls `POST /api/v1/auth/login` with `{userName, password}`
2. Backend checks hardcoded `admin/admin123` → returns mock token
3. Frontend stores token in Pinia `userStore` (persisted to localStorage)
4. Axios request interceptor attaches token as `Authorization` header
5. No real JWT or session management; no database-backed auth

**Route Initialization Flow:**
1. App boot → `beforeEach` guard checks login state
2. First navigation triggers dynamic route registration: fetches user info (mock), gets menu list, registers routes via `RouteRegistry`, validates path permissions
3. Subsequent navigations use cached routes; guard checks permission against menu list

**State Management:**
- Pinia stores with Composition API (`defineStore` + `setup()` function)
- `pinia-plugin-persistedstate` with versioned localStorage keys (`sys-v{version}-{storeId}`)
- Stores: `user` (auth/identity), `menu` (navigation), `setting` (UI preferences), `table`, `task` (Celery task progress), `worktab` (tab management)
- Cross-store communication: stores directly import other stores (e.g., `useUserStore` imports `useSettingStore`, `useWorktabStore`)

## Key Abstractions

**Settings Singleton:**
- Purpose: Centralized configuration with `.env` file override support
- Examples: `1/backend/app/core/config.py`
- Pattern: Singleton `settings = Settings()` instance, reads `.env`, provides typed config values (`PROJECT_NAME`, `VERSION`, `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `BACKEND_CORS_ORIGINS`, `API_V1_STR`)

**Celery App Instance:**
- Purpose: Distributed task queue for long-running LLM operations
- Examples: `1/backend/app/core/celery_app.py`
- Pattern: Named Celery instance (`'llama_factory'`) with Redis broker (DB 1) and result backend (DB 2), JSON serialization, 30min hard / 25min soft timeout, solo worker pool, auto-discovered tasks via `include=["app.tasks.dataset_tasks"]`

**ConnectionManager (WebSocket Manager):**
- Purpose: Manage active WebSocket connections grouped by `task_id`, enable targeted push
- Examples: `1/backend/app/core/websocket_manager.py`
- Pattern: Singleton `manager` instance, maintains `{task_id: [WebSocket]}` dict and global active connections set, supports `send_to_task()` and `broadcast()`, dead connection cleanup

**RedisPubSub (Pub/Sub Bridge):**
- Purpose: Bridge Celery task progress (Redis Pub/Sub) to WebSocket real-time push, enabling multi-worker environments
- Examples: `1/backend/app/core/redis_pubsub.py`
- Pattern: Singleton `redis_pubsub`, pattern-subscribes `progress:*` channels, runs subscriber in daemon thread, dispatches messages to WebSocket via `asyncio.ensure_future()` from `call_soon_threadsafe()`

**SQLAlchemy Base:**
- Purpose: ORM model base class for all database tables
- Examples: `1/backend/app/db/session.py` (line 16: `Base = declarative_base()`), `1/backend/app/db/models/__init__.py` (all model definitions inherit from `Base`)
- Pattern: Single `Base` instance, models inherit from it, `init_db()` calls `Base.metadata.create_all()`. All models defined in a single `models/__init__.py` file (132 lines)
- Models: `User` (users table), `Dataset` (datasets table), `Tag` (tags table), `TrainingTask` (training_tasks table), `TrainedModel` (trained_models table)
- Enums: `UserRole` (ADMIN/USER), `TaskStatus` (PENDING/RUNNING/COMPLETED/FAILED/CANCELLED), `ModelStatus` (UNLOADED/LOADING/ACTIVE)

**get_db Generator:**
- Purpose: FastAPI dependency injection for database sessions
- Examples: `1/backend/app/db/session.py` (lines 19-24)
- Pattern: Generator function yields `SessionLocal()`, closes on exit via `try/finally`; injected via `Depends(get_db)`

**Axios Request Client:**
- Purpose: Centralized HTTP communication with interceptors, auth, retry
- Examples: `1/frontend/src/utils/http/index.ts`
- Pattern: Named export `default api` with typed methods (`get<T>`, `post<T>`, `put<T>`, `del<T>`, `request<T>`). Configurable retry (currently 0). 401 handling with debounce/redirect. Request interceptor injects `Authorization` token; response interceptor handles success/error codes

**WebSocketClient Singleton:**
- Purpose: Persistent WebSocket connection with resilience features
- Examples: `1/frontend/src/utils/socket/index.ts`
- Pattern: `WebSocketClient` class with `static getInstance()` singleton, exponential backoff reconnection (up to 10 attempts), message queue for offline buffering, heartbeat/ping timers, connection timeout detection

**Pinia Store Composition:**
- Purpose: Reactive state management
- Examples: `1/frontend/src/store/modules/user.ts`, `task.ts`, `setting.ts`, `menu.ts`, `table.ts`, `worktab.ts`
- Pattern: `defineStore(id, setupFunction, persistOptions)`. Setup function returns reactive refs and computed/methods directly. `persist: { key, storage: localStorage }` configures pinia-plugin-persistedstate

**RouteRegistry:**
- Purpose: Dynamic route registration with permission validation
- Examples: `1/frontend/src/router/core/RouteRegistry.ts`, `RouteTransformer.ts`, `RoutePermissionValidator.ts`, `MenuProcessor.ts`
- Pattern: Class-based registry that transforms backend menu list into Vue Router routes, registers them dynamically, tracks removal functions for cleanup

## Entry Points

**Backend FastAPI App:**
- Location: `1/backend/app/main.py`
- Triggers: `uvicorn app.main:app --reload --port 8000` (or `python -m uvicorn app.main:app`)
- Responsibilities: Creates FastAPI app with lifespan context (starts/stops Redis PubSub subscriber), configures CORS middleware, includes REST API router at `/api/v1`, includes WebSocket router

**Backend V1 API Router:**
- Location: `1/backend/app/api/router.py`
- Triggers: Included by `main.py` at `/api/v1`
- Responsibilities: Aggregates endpoint routers:
  - `/api/v1/health` → `health.router`
  - `/api/v1/auth` → `auth.router`
  - `/api/v1/tasks` → `tasks.router`
  - `/api/v1/user` → `users.router`
  - `/api/v1/datasets/*` → `datasets.router` (prefix `''`, endpoints define their own paths)

**Celery Worker:**
- Location: `1/backend/app/core/celery_app.py`
- Triggers: `celery -A app.core.celery_app worker --loglevel=info`
- Responsibilities: Consumes tasks from Redis queue (DB 1), executes `app.tasks.dataset_tasks` functions, publishes progress to Redis Pub/Sub `progress:*` channels

**Database Initializer:**
- Location: `1/backend/app/db/init_db.py`
- Triggers: `python -m app.db.init_db` (standalone script)
- Responsibilities: Creates all database tables from SQLAlchemy model metadata

**Frontend Vite Dev Server:**
- Location: `1/frontend/vite.config.ts`
- Triggers: `npm run dev` (runs `vite --open`)
- Responsibilities: Serves SPA on port 3000, proxies `/api/*` → backend, `/ws/*` → WebSocket backend, configures path aliases (`@`, `@views`, `@imgs`, `@icons`, `@utils`, `@stores`, `@styles`)

**Frontend Vue App Entry:**
- Location: `1/frontend/src/main.ts`
- Triggers: Browser loads `index.html`
- Responsibilities: Creates Vue app, initializes Pinia store, Vue Router, global directives, error handling, i18n, mounts `App.vue` to `#app`

**Frontend Build Entry:**
- Location: `1/frontend/package.json` scripts
- Triggers: `npm run build` (runs `vue-tsc --noEmit && vite build`)
- Responsibilities: Type-checks then builds production bundle to `dist/`

## Routing Structure

**Backend API Routes (FastAPI):**
```
/api/v1/health/                        GET  - Health check
/api/v1/auth/login                     POST - Login (mock)
/api/v1/tasks/add                      POST - Create add task (legacy demo)
/api/v1/tasks/multiply                 POST - Create multiply task (legacy demo)
/api/v1/tasks/{task_id}                GET  - Get task status
/api/v1/user/info                      GET  - Get current user info (mock)
/api/v1/datasets/initiate-upload       GET  - Initiate chunked upload
/api/v1/datasets/upload-chunk          POST - Upload individual chunk
/api/v1/datasets/complete-upload       POST - Complete upload, trigger assembly
/api/v1/datasets                       GET  - List datasets
/api/v1/datasets/{dataset_id}          GET  - Get dataset
/api/v1/datasets/{dataset_id}          DELETE - Delete dataset
/api/v1/datasets/{dataset_id}/process  POST - Trigger cleaning/convert task
/api/v1/datasets/tasks/{task_id}       GET  - Get async task status
/ws/progress?task_id={task_id}         WS   - Task-specific progress WebSocket
/ws/broadcast                          WS   - Global broadcast WebSocket
```

**Frontend Routes (Vue Router, hash history):**

Static routes (always available, no auth required):
- `/auth/login` → `src/views/auth/login/index.vue`
- `/auth/register` → `src/views/auth/register/index.vue`
- `/auth/forget-password` → `src/views/auth/forget-password/index.vue`
- `/403`, `/500`, `/:pathMatch(.*)*` → exception pages
- `/outside` → iframe container

Async routes (require auth, registered dynamically):
- `/workbench/dashboard` → Monitoring dashboard (placeholder)
- `/workbench/compute-storage` → Compute & storage (placeholder)
- `/workbench/task-dispatch` → Task dispatch (placeholder)
- `/data-management/dataset-hub` → Dataset management (fully implemented)
- `/data-management/data-processing` → Data processing tools (fully implemented)
- `/model-factory/new-training` → New training configuration (placeholder)
- `/model-factory/model-registry` → Trained model registry (placeholder)
- `/task-monitoring` → Task monitoring (placeholder)
- `/model-inference` → Model inference chat (placeholder)
- `/system-management/users-roles` → User/role management (placeholder)
- `/system-management/advanced-settings` → Advanced settings (placeholder)

**Route Guards (`1/frontend/src/router/guards/beforeEach.ts`):**
1. Check login status → redirect to login if unauthenticated
2. If routes not yet registered → fetch user info + menu list → register dynamic routes → validate path permissions
3. Root `/` → redirect to home path from menu
4. Unmatched → redirect to 404

## Error Handling

**Backend API:**
- FastAPI auto-handles validation errors (422), unhandled exceptions (500)
- Custom `HTTPException` raised in endpoints (`datasets.py` lines 91, 99, 114, 124, 131)
- `try/finally` for database session cleanup (`dataset_tasks.py` lines 69-115, 125-225, etc.)
- No global exception handler middleware registered in `main.py`

**Frontend HTTP (`1/frontend/src/utils/http/index.ts`):**
- Axios response interceptor checks `response.data.code` against `ApiStatus.success`
- 401 errors trigger debounced logout (3s debounce window) via `handleUnauthorizedError()`
- Configurable retry on server errors (currently `MAX_RETRIES = 0` means no retries)
- `ExtendedAxiosRequestConfig.showErrorMessage` to suppress error notifications
- All errors typed as `HttpError` with code/message

**Frontend WebSocket (`1/frontend/src/utils/socket/index.ts`):**
- Try/catch in message parsing, auto-reconnect on close/error
- Exponential backoff reconnection with jitter, max 10 attempts
- Connection timeout detection (10s default)
- Message queue buffers sends when disconnected

**Backend Celery Tasks:**
- Tasks have 30min hard limit / 25min soft limit (`celery_app.py` lines 17-18)
- Each task wraps logic in `try/except/finally` with `db.close()` in finally
- Progress publishing failures logged but don't fail the main task (`dataset_tasks.py` line 56)
- No explicit Celery retry or error handling callbacks configured

**Frontend Router Guards:**
- Full try/catch in `handleRouteGuard()` → catches and shows error messages
- Route init failure tracking prevents infinite loops (`routeInitFailed` flag)
- Concurrent init prevention (`routeInitInProgress` flag)

## Cross-Cutting Concerns

**Logging:**
- Backend: Python `logging` module configured in `main.py` with `logging.basicConfig(level=logging.INFO)`; `logger = logging.getLogger(__name__)` used in `main.py`, `websocket.py`, `websocket_manager.py`, `redis_pubsub.py`
- Backend: `print()` still used in `init_db.py` for startup messages
- Celery: Uses own logging (`--loglevel=info`)
- Frontend: `console.log`/`console.error` with prefixed categories (e.g., `'[WebSocket]'`, `'[RouteGuard]'`)

**Validation:**
- Backend: Pydantic `BaseModel` for request body validation (inline in endpoint files + schemas in `app/schemas/dataset.py`); FastAPI route `response_model` parameter for response serialization
- Frontend: TypeScript strict mode enabled in `tsconfig.json`, `vue-tsc` for type checking at build time

**Authentication:**
- Backend: Mock auth — hardcoded `admin/admin123` check in `auth.py`; no JWT, no session, no database-backed users
- Frontend: Token stored in Pinia `userStore.accessToken` (persisted to localStorage); Axios interceptor attaches as `Authorization` header; `isLogin` set to `true` by default in dev mode; `logOut()` clears state and redirects to login

**Internationalization:**
- `vue-i18n` with locale files at `1/frontend/src/locales/langs/{en,zh}.json`
- `$t()` function for translation keys (e.g., `menus.dataManagement.title`)
- Language stored in `userStore.language` (defaults to `LanguageEnum.ZH`)

**Theme:**
- Tailwind CSS v4 with `@tailwindcss/vite` plugin
- SCSS variables and mixins injected globally via `vite.config.ts` `css.preprocessorOptions.scss.additionalData`
- Element Plus theme customization via `unplugin-element-plus`

**Build & Optimization:**
- Vite build with `terser` minification (production drops console/debugger)
- `vite-plugin-compression` for gzip output
- `rollup-plugin-visualizer` available (commented out)
- Auto-import for Vue/VueRouter/Pinia/VueUse composables and Element Plus components

---

*Architecture analysis: 2026-05-01*
