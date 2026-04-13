<!-- GSD:project-start source:PROJECT.md -->
## Project

**LLaMA-Factory Workstation**

一款面向本地/私有云环境的"一站式"LLMOps 轻量级工作站，集成数据处理、模型微调、任务监控、模型推理功能。使用 LLaMA-Factory 作为核心 LLM 框架，Vue 3 + FastAPI 架构，Celery + Redis 异步任务队列，MySQL 持久化存储。目标用户为开发者和研究人员，需要本地微调大模型的用户。

**Core Value:** 用户可以通过统一的 Web 界面完成从数据准备到模型微调再到推理部署的完整 LLMOps 闭环，无需切换工具或编写命令行脚本。

### Constraints

- **Tech Stack**: Vue 3 + Element Plus + FastAPI + SQLAlchemy + Celery + Redis + MySQL — 已确定的技术选型
- **Deployment**: 本地或私有云，需 GPU 支持 — 决定了轻量级架构方向
- **LLaMA-Factory**: 必须以库方式导入调用，不能 subprocess — 影响训练服务设计
- **Windows 兼容**: 使用 pymysql 替代 mysqlclient — 构建兼容性约束
- **File Size**: 数据集上传最大 100MB — 影响上传机制设计
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.12 - Backend API, models, services, Celery tasks (`1/backend/`)
- TypeScript - Frontend Vue SPA (`1/frontend/`)
- Vue SFC (Single File Components) - UI templates and styles (`1/frontend/src/**/*.vue`)
- SQL - Database schema via SQLAlchemy ORM (`1/backend/app/db/models/`)
## Runtime
- Python 3.12 (backend)
- Node.js v24.14.1 (frontend dev/build)
- pip + `requirements.txt` (backend) - Lockfile: not present (no `requirements.lock`)
- npm + `package-lock.json` (frontend) - Lockfile: present
## Frameworks
- FastAPI 0.104.1 - Backend REST API framework (`1/backend/app/main.py`)
- Vue 3.3.8 - Frontend SPA framework (`1/frontend/src/main.ts`)
- Vue Router 4.2.5 - Client-side routing (`1/frontend/src/router/index.ts`)
- Pinia 2.1.7 - State management (`1/frontend/src/store/`)
- Celery 5.3.4 - Distributed task queue (`1/backend/app/core/celery_app.py`)
- Redis 5.0.1 - Celery broker and result backend
- SQLAlchemy 2.0.23 - ORM for MySQL (`1/backend/app/db/session.py`)
- Alembic 1.12.1 - Database migrations (installed, no `alembic.ini` yet)
- PyMySQL 1.1.0 - MySQL driver
- Element Plus 2.4.2 - Vue 3 UI component library (`1/frontend/src/main.ts`)
- @element-plus/icons-vue 2.1.0 - Icon set
- Vite 4.5.0 - Frontend build tool and dev server (`1/frontend/vite.config.ts`)
- TypeScript 5.2.2 - Type checking (`1/frontend/tsconfig.json`)
- vue-tsc 1.8.22 - Vue TypeScript type checking
- @vitejs/plugin-vue 4.5.0 - Vue SFC support for Vite
- httpx 0.25.2 - Async HTTP client (backend)
- axios 1.6.0 - Frontend HTTP client (`1/frontend/src/api/httpClient.ts`)
## Key Dependencies
- Pydantic 2.5.0 + pydantic-settings 2.1.0 - Data validation and settings management (`1/backend/app/core/config.py`)
- websockets 12.0 - WebSocket protocol support (backend)
- pynvml 11.5.0 - NVIDIA GPU monitoring library (backend, for future GPU management features)
- cryptography 41.0.7 - Cryptographic primitives (backend)
- python-multipart 0.0.6 - File upload handling (backend)
- python-dotenv 1.0.0 - `.env` file loading (`1/backend/app/core/config.py`)
- uvicorn 0.24.0 (with `[standard]` extras) - ASGI server (`1/backend/app/main.py`)
## Configuration
- Backend uses `pydantic-settings` with `.env` file support (`1/backend/app/core/config.py`)
- Frontend uses `import.meta.env` for Vite env vars (e.g., `VITE_API_BASE_URL`, `VITE_WS_URL`)
- Default CORS origins: `http://localhost:3000`, `http://localhost:5173`
- Default database URL: `mysql+pymysql://root:password@localhost:3306/llama_factory`
- Default Redis URL: `redis://localhost:6379/0`
- Celery broker: `redis://localhost:6379/1`, result backend: `redis://localhost:6379/2`
- `1/frontend/vite.config.ts` - Vite config with dev proxy (`/api` → `http://localhost:8000`)
- `1/frontend/tsconfig.json` - TypeScript config (ES2020 target, strict mode, `@/*` path alias)
- `1/frontend/tsconfig.node.json` - Node-specific TS config for Vite
- No `alembic.ini` yet (Alembic dependency present but not configured)
- Frontend: `@/*` → `src/*` (defined in `1/frontend/tsconfig.json`)
## Platform Requirements
- Python 3.12+ runtime
- Node.js 18+ (v24 confirmed)
- MySQL server (local or remote)
- Redis server (local or remote)
- Vite dev server runs on port 3000
- FastAPI/Uvicorn runs on port 8000
- ASGI server (uvicorn) for FastAPI
- Static file serving for Vue SPA build output
- MySQL database
- Redis for Celery broker/result backend
- Celery worker process
- NVIDIA GPU with drivers (for LLM inference, pynvml dependency)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Module directories use `snake_case`: `api/`, `db/`, `core/`, `crud/`, `services/`, `schemas/`
- Python modules use `snake_case`: `celery_app.py`, `init_db.py`, `session.py`
- Endpoint files use `snake_case` singular nouns: `health.py`, `tasks.py`
- Vue components use `PascalCase`: `MainLayout.vue`, `TheHeader.vue`, `TheSidebar.vue`, `HomeView.vue`
- Layout components prefixed with `The`: `TheHeader.vue`, `TheSidebar.vue`
- View components suffixed with `View`: `HomeView.vue`, `DashboardView.vue`, `DataManagementView.vue`
- TypeScript modules use `camelCase`: `httpClient.ts`, `websocket.ts`, `ui.ts`
- Directories use `kebab-case` or `camelCase`: `training/`, `layout/`
- Use `snake_case` for all Python functions: `get_db()`, `init_db()`, `health_check()`, `create_add_task()`
- Route handler functions are `async def` with descriptive `snake_case` names
- Celery tasks use `snake_case`: `add()`, `multiply()`
- Use `camelCase` for all TypeScript functions: `toggleSidebar()`, `setSidebarCollapsed()`
- WebSocket class methods use `camelCase`: `connect()`, `disconnect()`, `scheduleReconnect()`
- Exported convenience functions use `camelCase`: `connectWebSocket()`, `onWebSocketMessage()`
- Backend: `snake_case` for module-level variables: `api_router`, `celery_app`, `settings`
- Frontend: `camelCase` for variables and refs: `isCollapsed`, `httpClient`, `reconnectInterval`
- Constants: `UPPER_SNAKE_CASE` in Settings class: `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`
- Backend Python Enums use `PascalCase` with `PascalCase` values: `UserRole.ADMIN`, `TaskStatus.PENDING`, `ModelStatus.UNLOADED`
- SQLAlchemy model classes use `PascalCase`: `User`, `Dataset`, `TrainingTask`, `TrainedModel`
- Pydantic models use `PascalCase`: `HealthResponse`, `TaskRequest`, `TaskResponse`
- Frontend: `PascalCase` for Vue component names and TypeScript types
- TypeScript type aliases use `PascalCase`: `MessageHandler`
## Code Style
- No linter or formatter config detected in the project root (no `.eslintrc`, `.prettierrc`, `biome.json`, `ruff.toml`, `black` config, or similar)
- Frontend: relies on Vue/Vite defaults; TypeScript strict mode enabled in `tsconfig.json`
- Backend: no Black/isort/flake8/pylint config detected
- Backend Python: 4 spaces (standard PEP 8)
- Frontend TypeScript/Vue: 2 spaces (standard Vue/Vite convention)
- Backend Python: single quotes for imports and simple strings, double quotes for f-strings and docstrings
- Frontend TypeScript: single quotes for imports and string literals
- `"strict": true` — strict type checking
- `"noUnusedLocals": false` — allows unused locals
- `"noUnusedParameters": false` — allows unused params
- `"target": "ES2020"`, `"module": "ESNext"`
- Path alias: `@/*` → `src/*`
## Import Organization
- `@/*` maps to `src/*` in `tsconfig.json` — available but not currently used in source files
- Current imports use relative paths: `'../../store/ui'`, `'../views/HomeView.vue'`
- Prefer using `@/` alias for consistency going forward
## Error Handling
- HTTP errors raised via `HTTPException` from FastAPI: `from fastapi import HTTPException` (imported in `1/backend/app/api/endpoints/tasks.py`)
- No custom exception handlers or middleware registered in `1/backend/app/main.py`
- Database session cleanup uses `try/finally`: `get_db()` in `1/backend/app/db/session.py`
- No global exception handler middleware configured
- Axios response interceptor handles errors globally in `1/frontend/src/api/httpClient.ts`
- Error messages extracted from `error.response?.data?.detail || error.message || '请求失败'`
- `ElNotification` used for user-facing error display
- 401 responses trigger `localStorage.removeItem('auth_token')` and redirect to `/`
- All errors are re-rejected via `Promise.reject(error)` for local handling
- Connection errors logged via `console.error` and trigger auto-reconnect with 5s interval
- JSON parse errors in `onmessage` fall back to dispatching raw data: `dispatch('message', event.data)`
- Use `HTTPException` for API error responses
- Use `try/finally` for resource cleanup (DB sessions)
- Use Axios interceptors for centralized HTTP error handling
- Use `ElNotification` for user-facing error display in the frontend
- Use console logging (`console.log`, `console.error`) for WebSocket debugging
## Logging
- No logging framework configured (no `logging` module usage found)
- `print()` used in `1/backend/app/db/init_db.py` for startup messages
- Celery uses its own logging (`--loglevel=info` in worker command)
- `console.log()` and `console.error()` used in `1/frontend/src/api/websocket.ts`
- Prefixed with `[WebSocket]` for categorization: `console.log('[WebSocket] Connected to', this.url)`
- Backend: Add `import logging; logger = logging.getLogger(__name__)` for new modules
- Frontend: Use `console.log('[ComponentName]')` prefix pattern for debugging
- Prefer structured logging over raw `print()` statements
## Comments
- Chinese language docstrings on endpoint handlers: `"""健康检查端点"""`, `"""创建加法任务"""`, `"""获取任务状态"""`
- Chinese inline comments for section labels: `# 配置CORS`, `# 注册路由`, `# 关系`, `# 外键`
- Comments in Chinese are the project standard
- Not used in the frontend codebase
- Celery task docstrings use Chinese: `"""示例任务：加法运算"""`
- Use Chinese for all comments and docstrings
- Use docstrings (`"""..."""`) for Python functions and classes
- Use section-separator comments (`# 配置CORS`) for logical groupings in configuration files
- No JSDoc/TSDoc convention established yet — add for complex functions
## Function Design
- Backend endpoint handlers are short (3-10 lines)
- Frontend component `<script setup>` blocks are concise (2-23 lines)
- Keep functions focused and under 50 lines; extract helpers when longer
- Backend: Use Pydantic `BaseModel` classes for request bodies: `TaskRequest`, `TaskRequest(BaseModel)`
- Backend: Use FastAPI dependency injection for DB sessions: `Depends(get_db)` (pattern established, not yet used)
- Frontend: Use typed parameters in class methods and functions
- Backend: Use Pydantic `BaseModel` for response serialization: `TaskResponse`, `HealthResponse`
- Backend: Use `response_model=TaskResponse` parameter in route decorators
- Frontend: Store composables return reactive refs and methods
## Module Design
- Backend: Each endpoint module exports a `router = APIRouter()` instance
- Backend: Config exports a singleton `settings = Settings()`
- Frontend: Pinia stores export `useXxxStore` composables: `useUIStore`
- Frontend: API modules export both default and named exports: `export default httpClient`, `export const apiEndpoints`
- Frontend: WebSocket exports named functions: `export const connectWebSocket`, `export const onWebSocketMessage`
- Backend: `__init__.py` files exist but are empty for `schemas/`, `crud/`, `services/`, `api/`, `api/endpoints/`
- Backend: Only `1/backend/app/db/models/__init__.py` has substantive content (all model definitions)
- Frontend: No barrel `index.ts` files for component directories
- Pattern: Use `__init__.py` to re-export public API when modules grow
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Two independent services: Python FastAPI backend + Vue 3 SPA frontend
- REST API communication between frontend and backend via `/api/v1` prefix
- Async task processing via Celery + Redis for long-running LLM training jobs
- Real-time push via WebSocket for training progress, logs, and model status notifications
- SQLAlchemy ORM with MySQL for persistent data
- Vite dev proxy bridges frontend to backend during development
## Layers
- Purpose: User interface for LLM fine-tuning workstation management
- Location: `1/frontend/src/`
- Contains: Vue 3 SFCs (`.vue`), TypeScript modules, Pinia stores, Vue Router config, API clients
- Depends on: Backend REST API (`/api/v1`), WebSocket server (`/ws`)
- Used by: End users (browser)
- Purpose: REST API endpoint definitions and request handling
- Location: `1/backend/app/api/`
- Contains: FastAPI routers, Pydantic request/response schemas (inline)
- Depends on: Services layer, Celery tasks, SQLAlchemy models
- Used by: Frontend HTTP client (`1/frontend/src/api/httpClient.ts`)
- Purpose: Application configuration and shared infrastructure
- Location: `1/backend/app/core/`
- Contains: Settings (pydantic-settings), Celery app instance
- Depends on: Environment variables (`.env`)
- Used by: All backend modules import `app.core.config.settings`
- Purpose: Database models, session management, and initialization
- Location: `1/backend/app/db/`
- Contains: SQLAlchemy declarative models, engine/session factory, `init_db` script
- Depends on: `app.core.config` for `DATABASE_URL`
- Used by: CRUD layer, API endpoints (via `get_db` dependency injection)
- Purpose: Asynchronous background job execution
- Location: `1/backend/app/tasks.py`
- Contains: Celery `@shared_task` definitions
- Depends on: `app.core.celery_app`
- Used by: API endpoints dispatch tasks via `.delay()`
- Purpose: Business logic orchestration
- Location: `1/backend/app/services/`
- Contains: Empty `__init__.py` only — not yet implemented
- Depends on: Planned to depend on CRUD, Celery, LLaMA-Factory
- Used by: Planned to be used by API endpoints
- Purpose: Database read/write operations
- Location: `1/backend/app/crud/`
- Contains: Empty `__init__.py` only — not yet implemented
- Depends on: Planned to depend on SQLAlchemy session and models
- Used by: Planned to be used by service layer
- Purpose: Pydantic models for request/response validation
- Location: `1/backend/app/schemas/`
- Contains: Empty `__init__.py` only — not yet implemented
- Depends on: None
- Used by: Currently API endpoints define inline Pydantic models instead
## Data Flow
- Pinia stores (Composition API style) manage reactive state
- Currently only `useUIStore` in `1/frontend/src/store/ui.ts` (sidebar collapsed state)
- No auth store or data stores yet — planned for future phases
## Key Abstractions
- Purpose: Centralized configuration with env var override support
- Examples: `1/backend/app/core/config.py`
- Pattern: Singleton `settings` instance, reads `.env` file, provides typed config values (`DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `BACKEND_CORS_ORIGINS`)
- Purpose: Distributed task queue for long-running LLM operations
- Examples: `1/backend/app/core/celery_app.py`
- Pattern: Named Celery instance with Redis broker/backend, JSON serialization, 30min hard timeout, 25min soft timeout, auto-discovered tasks via `include=["app.tasks"]`
- Purpose: ORM model base class for all database tables
- Examples: `1/backend/app/db/session.py` (`Base`), `1/backend/app/db/models/__init__.py` (model definitions)
- Pattern: Single `Base` instance from `declarative_base()`, models inherit from it, `init_db()` calls `Base.metadata.create_all()`
- Purpose: FastAPI dependency injection for DB sessions
- Examples: `1/backend/app/db/session.py` (`get_db` generator)
- Pattern: Generator function yields session, closes on exit; intended for `Depends(get_db)` injection (not yet used in endpoints)
- Purpose: Centralized HTTP communication with interceptors
- Examples: `1/frontend/src/api/httpClient.ts`
- Pattern: Singleton Axios instance with `baseURL`, request interceptor (auth token from localStorage), response interceptor (error notification via Element Plus, 401 redirect)
- Purpose: Persistent WebSocket connection with reconnection and event dispatch
- Examples: `1/frontend/src/api/websocket.ts`
- Pattern: Singleton class with pub/sub event system (`on`/`off`), auto-reconnect (5s), heartbeat (30s), wildcard listener support (`*` event)
- Purpose: Reactive state management
- Examples: `1/frontend/src/store/ui.ts`
- Pattern: `defineStore` with setup function, `ref` for reactive state, returned object exposes state and actions
## Entry Points
- Location: `1/backend/app/main.py`
- Triggers: `uvicorn app.main:app --reload --port 8000`
- Responsibilities: Creates FastAPI app, configures CORS middleware, includes API router at `/api/v1`
- Location: `1/backend/app/core/celery_app.py`
- Triggers: `celery -A app.core.celery_app worker --loglevel=info`
- Responsibilities: Consumes tasks from Redis queue, executes `app.tasks` functions
- Location: `1/backend/app/db/init_db.py`
- Triggers: `python -m app.db.init_db` (standalone script)
- Responsibilities: Creates all database tables from SQLAlchemy model metadata
- Location: `1/frontend/vite.config.ts`
- Triggers: `npm run dev` (runs `vite`)
- Responsibilities: Serves SPA on port 3000, proxies `/api/*` to backend
- Location: `1/frontend/package.json`
- Triggers: `npm run build` (runs `vue-tsc && vite build`)
- Responsibilities: Type-checks then builds production bundle
## Error Handling
- **Backend API**: FastAPI auto-handles validation errors (422), unhandled exceptions return 500. Custom `HTTPException` used in endpoints (e.g., `1/backend/app/api/endpoints/tasks.py`)
- **Frontend HTTP**: Axios response interceptor in `1/frontend/src/api/httpClient.ts` catches all errors, shows `ElNotification` with error detail, handles 401 by clearing token and redirecting to `/`
- **Frontend WebSocket**: Try/catch in `onmessage` parser, auto-reconnect on close/error (see `1/frontend/src/api/websocket.ts`)
- **Backend Celery**: Tasks have 30min hard limit / 25min soft limit (see `1/backend/app/core/celery_app.py`), but no explicit retry or error handling in current task definitions
- **Database**: No error handling in `get_db` generator or `init_db`; relies on SQLAlchemy/PyMySQL defaults
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
