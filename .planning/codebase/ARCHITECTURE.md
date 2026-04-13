# Architecture

**Analysis Date:** 2026-04-13

## Pattern Overview

**Overall:** Monorepo Client-Server with Async Task Queue

**Key Characteristics:**
- Two independent services: Python FastAPI backend + Vue 3 SPA frontend
- REST API communication between frontend and backend via `/api/v1` prefix
- Async task processing via Celery + Redis for long-running LLM training jobs
- Real-time push via WebSocket for training progress, logs, and model status notifications
- SQLAlchemy ORM with MySQL for persistent data
- Vite dev proxy bridges frontend to backend during development

## Layers

**Frontend (Presentation Layer):**
- Purpose: User interface for LLM fine-tuning workstation management
- Location: `1/frontend/src/`
- Contains: Vue 3 SFCs (`.vue`), TypeScript modules, Pinia stores, Vue Router config, API clients
- Depends on: Backend REST API (`/api/v1`), WebSocket server (`/ws`)
- Used by: End users (browser)

**Backend API Layer:**
- Purpose: REST API endpoint definitions and request handling
- Location: `1/backend/app/api/`
- Contains: FastAPI routers, Pydantic request/response schemas (inline)
- Depends on: Services layer, Celery tasks, SQLAlchemy models
- Used by: Frontend HTTP client (`1/frontend/src/api/httpClient.ts`)

**Backend Core Layer:**
- Purpose: Application configuration and shared infrastructure
- Location: `1/backend/app/core/`
- Contains: Settings (pydantic-settings), Celery app instance
- Depends on: Environment variables (`.env`)
- Used by: All backend modules import `app.core.config.settings`

**Backend Data Layer:**
- Purpose: Database models, session management, and initialization
- Location: `1/backend/app/db/`
- Contains: SQLAlchemy declarative models, engine/session factory, `init_db` script
- Depends on: `app.core.config` for `DATABASE_URL`
- Used by: CRUD layer, API endpoints (via `get_db` dependency injection)

**Backend Task Layer:**
- Purpose: Asynchronous background job execution
- Location: `1/backend/app/tasks.py`
- Contains: Celery `@shared_task` definitions
- Depends on: `app.core.celery_app`
- Used by: API endpoints dispatch tasks via `.delay()`

**Backend Service Layer (Scaffolded):**
- Purpose: Business logic orchestration
- Location: `1/backend/app/services/`
- Contains: Empty `__init__.py` only — not yet implemented
- Depends on: Planned to depend on CRUD, Celery, LLaMA-Factory
- Used by: Planned to be used by API endpoints

**Backend CRUD Layer (Scaffolded):**
- Purpose: Database read/write operations
- Location: `1/backend/app/crud/`
- Contains: Empty `__init__.py` only — not yet implemented
- Depends on: Planned to depend on SQLAlchemy session and models
- Used by: Planned to be used by service layer

**Backend Schema Layer (Scaffolded):**
- Purpose: Pydantic models for request/response validation
- Location: `1/backend/app/schemas/`
- Contains: Empty `__init__.py` only — not yet implemented
- Depends on: None
- Used by: Currently API endpoints define inline Pydantic models instead

## Data Flow

**API Request Flow:**

1. Browser sends request to `http://localhost:3000/api/v1/...`
2. Vite dev server proxies `/api/*` → `http://localhost:8000` (see `1/frontend/vite.config.ts`)
3. FastAPI receives request, routes through `api_router` with `/api/v1` prefix (see `1/backend/app/main.py`)
4. `api_router` delegates to endpoint router (`1/backend/app/api/router.py`)
5. Endpoint handler processes request, optionally dispatches Celery task
6. Response serialized via Pydantic model, returned as JSON

**Async Task Flow:**

1. API endpoint calls `task.delay(args)` (e.g., `add.delay(x, y)` in `1/backend/app/api/endpoints/tasks.py`)
2. Celery serializes task and enqueues to Redis broker (`redis://localhost:6379/1`)
3. Celery worker picks up task, executes function
4. Result stored in Redis result backend (`redis://localhost:6379/2`)
5. Frontend polls `GET /api/v1/tasks/{task_id}` to check status via `AsyncResult`

**WebSocket Real-Time Flow:**

1. Frontend `WebSocketManager` connects to `ws://host/ws` (see `1/frontend/src/api/websocket.ts`)
2. Backend pushes events (training progress, model status changes) as JSON
3. `WebSocketManager` dispatches events to registered handlers by `data.type`
4. Built-in handlers show `ElNotification` for `system-notification`, `model-activated`, `model-deactivated`
5. Heartbeat pings every 30s; auto-reconnect on disconnect (5s interval)

**State Management:**
- Pinia stores (Composition API style) manage reactive state
- Currently only `useUIStore` in `1/frontend/src/store/ui.ts` (sidebar collapsed state)
- No auth store or data stores yet — planned for future phases

## Key Abstractions

**Settings (Pydantic BaseSettings):**
- Purpose: Centralized configuration with env var override support
- Examples: `1/backend/app/core/config.py`
- Pattern: Singleton `settings` instance, reads `.env` file, provides typed config values (`DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `BACKEND_CORS_ORIGINS`)

**Celery App:**
- Purpose: Distributed task queue for long-running LLM operations
- Examples: `1/backend/app/core/celery_app.py`
- Pattern: Named Celery instance with Redis broker/backend, JSON serialization, 30min hard timeout, 25min soft timeout, auto-discovered tasks via `include=["app.tasks"]`

**SQLAlchemy Declarative Base:**
- Purpose: ORM model base class for all database tables
- Examples: `1/backend/app/db/session.py` (`Base`), `1/backend/app/db/models/__init__.py` (model definitions)
- Pattern: Single `Base` instance from `declarative_base()`, models inherit from it, `init_db()` calls `Base.metadata.create_all()`

**Database Session Dependency:**
- Purpose: FastAPI dependency injection for DB sessions
- Examples: `1/backend/app/db/session.py` (`get_db` generator)
- Pattern: Generator function yields session, closes on exit; intended for `Depends(get_db)` injection (not yet used in endpoints)

**HTTP Client (Axios):**
- Purpose: Centralized HTTP communication with interceptors
- Examples: `1/frontend/src/api/httpClient.ts`
- Pattern: Singleton Axios instance with `baseURL`, request interceptor (auth token from localStorage), response interceptor (error notification via Element Plus, 401 redirect)

**WebSocket Manager:**
- Purpose: Persistent WebSocket connection with reconnection and event dispatch
- Examples: `1/frontend/src/api/websocket.ts`
- Pattern: Singleton class with pub/sub event system (`on`/`off`), auto-reconnect (5s), heartbeat (30s), wildcard listener support (`*` event)

**Pinia Store (Composition API):**
- Purpose: Reactive state management
- Examples: `1/frontend/src/store/ui.ts`
- Pattern: `defineStore` with setup function, `ref` for reactive state, returned object exposes state and actions

## Entry Points

**FastAPI Application:**
- Location: `1/backend/app/main.py`
- Triggers: `uvicorn app.main:app --reload --port 8000`
- Responsibilities: Creates FastAPI app, configures CORS middleware, includes API router at `/api/v1`

**Celery Worker:**
- Location: `1/backend/app/core/celery_app.py`
- Triggers: `celery -A app.core.celery_app worker --loglevel=info`
- Responsibilities: Consumes tasks from Redis queue, executes `app.tasks` functions

**Database Init:**
- Location: `1/backend/app/db/init_db.py`
- Triggers: `python -m app.db.init_db` (standalone script)
- Responsibilities: Creates all database tables from SQLAlchemy model metadata

**Frontend Dev Server:**
- Location: `1/frontend/vite.config.ts`
- Triggers: `npm run dev` (runs `vite`)
- Responsibilities: Serves SPA on port 3000, proxies `/api/*` to backend

**Frontend Build:**
- Location: `1/frontend/package.json`
- Triggers: `npm run build` (runs `vue-tsc && vite build`)
- Responsibilities: Type-checks then builds production bundle

## Error Handling

**Strategy:** Mixed — some layers have structured error handling, others do not

**Patterns:**
- **Backend API**: FastAPI auto-handles validation errors (422), unhandled exceptions return 500. Custom `HTTPException` used in endpoints (e.g., `1/backend/app/api/endpoints/tasks.py`)
- **Frontend HTTP**: Axios response interceptor in `1/frontend/src/api/httpClient.ts` catches all errors, shows `ElNotification` with error detail, handles 401 by clearing token and redirecting to `/`
- **Frontend WebSocket**: Try/catch in `onmessage` parser, auto-reconnect on close/error (see `1/frontend/src/api/websocket.ts`)
- **Backend Celery**: Tasks have 30min hard limit / 25min soft limit (see `1/backend/app/core/celery_app.py`), but no explicit retry or error handling in current task definitions
- **Database**: No error handling in `get_db` generator or `init_db`; relies on SQLAlchemy/PyMySQL defaults

## Cross-Cutting Concerns

**Logging:** Backend uses Celery's built-in logging (configured via `--loglevel=info`). Frontend uses `console.log`/`console.error` in WebSocket manager. No structured logging framework.

**Validation:** Backend uses Pydantic models for request/response validation (auto-422). Frontend has no form validation library configured — planned for future phases.

**Authentication:** Token-based auth scaffolded in HTTP client interceptor (`1/frontend/src/api/httpClient.ts` reads `auth_token` from localStorage, sends as Bearer header). No backend auth implementation exists yet — no auth middleware, no login endpoint, no user CRUD.

**CORS:** Configured in `1/backend/app/main.py` with `CORSMiddleware`, allowing `http://localhost:3000` and `http://localhost:5173` origins, all methods and headers.

**Configuration:** Centralized in `1/backend/app/core/config.py` via `pydantic-settings` `BaseSettings` with `.env` file support. Frontend uses Vite's `import.meta.env` (e.g., `VITE_API_BASE_URL`, `VITE_WS_URL`).

---

*Architecture analysis: 2026-04-13*
