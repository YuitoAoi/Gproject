# Coding Conventions

**Analysis Date:** 2026-05-01

## Naming Patterns

### Files

**Backend Python:**
- Module files use `snake_case`: `celery_app.py`, `init_db.py`, `session.py`
- Endpoint files use `snake_case` singular nouns: `health.py`, `tasks.py`, `auth.py`, `users.py`, `datasets.py`, `websocket.py`
- Task files use `snake_case`: `dataset_tasks.py`

**Frontend TypeScript/Vue:**
- Vue components use `PascalCase`: `App.vue`, `MainLayout.vue`, `TheHeader.vue`, `HomeView.vue`
- Layout components prefixed with `The`: `TheHeader.vue`, `TheSidebar.vue`
- View components suffixed with `View`: `HomeView.vue`, `DashboardView.vue`, `DataManagementView.vue`
- TypeScript modules use `camelCase` or `kebab-case`: `httpClient.ts`, `websocket.ts`, `beforeEach.ts`
- API module files use `camelCase`: `auth.ts`, `dataset.ts`, `data-manage.ts`, `system-manage.ts`
- Store module files use `camelCase`: `user.ts`, `task.ts`, `setting.ts`, `menu.ts`, `worktab.ts`, `table.ts`

### Functions/Methods

**Backend Python:**
- Use `snake_case` for all functions: `get_db()`, `init_db()`, `health_check()`, `create_add_task()`, `get_task_status()`, `publish_progress()`, `ensure_dirs()`
- Route handler functions are `async def` with descriptive `snake_case` names
- Celery tasks use `snake_case`: `add()`, `multiply()`, `assemble_and_save_dataset()`, `process_dataset_clean()`, `convert_dataset_format()`
- CRUD functions use `snake_case` with `crud_entity` pattern: `get_datasets()`, `get_dataset()`, `create_dataset()`, `delete_dataset()`, `update_dataset_status()`

**Frontend TypeScript:**
- Use `camelCase` for all functions: `toggleSidebar()`, `fetchLogin()`, `handleMessage()`, `initStore()`, `initRouter()`
- Store action functions use `camelCase`: `setUserInfo()`, `updateTask()`, `switchMenuLayouts()`, `reload()`
- Vue composables/hooks use `use` prefix + `PascalCase`/`camelCase`: `useWebSocketTask()`, `useUserStore()`, `useSettingStore()`
- API functions use `fetch` prefix: `fetchLogin()`, `fetchGetUserInfo()`, `fetchGetDatasetList()`, `fetchDeleteDataset()`

### Variables

**Backend Python:**
- `snake_case` for module-level variables: `api_router`, `celery_app`, `settings`, `manager`, `redis_pubsub`
- `UPPER_SNAKE_CASE` for module-level constants: `CHUNK_SIZE`, `PROJECT_ROOT`, `UPLOAD_DIR`, `DATASET_DIR`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
- `UPPER_SNAKE_CASE` in Settings class fields: `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `BACKEND_CORS_ORIGINS`

**Frontend TypeScript:**
- `camelCase` for variables and refs: `isCollapsed`, `httpClient`, `reconnectInterval`, `connected`, `retryCount`
- `UPPER_SNAKE_CASE` for module-level constants in HTTP client: `REQUEST_TIMEOUT`, `LOGOUT_DELAY`, `MAX_RETRIES`, `RETRY_DELAY`, `UNAUTHORIZED_DEBOUNCE_TIME`

### Types/Classes/Enums

**Backend Python:**
- SQLAlchemy model classes use `PascalCase`: `User`, `Dataset`, `TrainingTask`, `TrainedModel`, `Tag`
- Pydantic models use `PascalCase`: `HealthResponse`, `TaskRequest`, `TaskResponse`, `DatasetCreate`, `DatasetResponse`, `ProcessRequest`, `LoginRequest`
- Enums use `PascalCase` names with `PascalCase` values: `UserRole.ADMIN`, `TaskStatus.PENDING`, `ModelStatus.UNLOADED`
- Settings class: `Settings` (singleton: `settings`)

**Frontend TypeScript:**
- `PascalCase` for Vue component names
- `PascalCase` for TypeScript interfaces: `TaskProgress`, `Dataset`, `UploadInitiateResponse`, `ProcessRequest`
- `PascalCase` for TypeScript enums: `LanguageEnum`, `SystemThemeEnum`, `MenuThemeEnum`, `MenuTypeEnum`, `ContainerWidthEnum`
- `PascalCase` for classes: `RouteRegistry`, `MenuProcessor`, `IframeRouteManager`, `RoutePermissionValidator`, `StorageKeyManager`

## Code Style

### Formatting

**Frontend (configured):**
- **Formatter:** Prettier 3.5.3
  - Config: `1/frontend/.prettierrc`
  - `printWidth`: 100
  - `tabWidth`: 2 spaces
  - `semi`: false (no semicolons)
  - `singleQuote`: true
  - `trailingComma`: "none"
  - `arrowParens`: "always"
- **Linter:** ESLint 9.9.1
  - Config: `1/frontend/eslint.config.mjs`
  - Key rules: single quotes, no semicolons, no `var`, no-multiple-empty-lines (max 1), no-unexpected-multiline
  - `@typescript-eslint/no-explicit-any`: off
  - `vue/multi-word-component-names`: off
- **Style Linter:** Stylelint 16.20.0
  - Config: `1/frontend/.stylelintrc.cjs`
  - Extends: standard, recommended-scss, recommended-vue, recess-order
- **Pre-commit hooks:** Husky 9.1.5
  - `1/frontend/.husky/pre-commit` - lint-staged
  - `1/frontend/.husky/commit-msg` - commitlint

**Backend (NOT configured):**
- No linter or formatter config detected in the backend
- No Black, isort, flake8, pylint, or ruff configuration
- Follows PEP 8 conventions loosely (4 spaces indentation, snake_case functions)
- Some files use 4-space indentation; consistent across all files

### Quoting

**Backend Python:**
- Single quotes for imports and simple strings: `'mysql+pymysql://root:password@localhost:3306/llama_factory'`
- Double quotes for f-strings and docstrings: `"""健康检查端点"""`
- Mixed usage in some files (e.g., `auth.py` line 28 uses double quotes for `json.dumps`)

**Frontend TypeScript:**
- Single quotes enforced by ESLint/Prettier: `'vue'`, `'@/store'`
- Template literals with backticks for dynamic strings

### TypeScript Strictness

- Config: `1/frontend/tsconfig.json`
- `"strict": true` — strict type checking enabled
- `"target": "esnext"`, `"module": "esnext"`, `"moduleResolution": "node"`
- `"noUnusedLocals"` and `"noUnusedParameters"` — not specified (default: false)
- `"skipLibCheck": true`

## Import Organization

### Path Aliases

**Frontend (`1/frontend/tsconfig.json`):**
- `@/*` → `src/*`
- `@views/*` → `src/views/*`
- `@imgs/*` → `src/assets/images/*`
- `@icons/*` → `src/assets/icons/*`
- `@utils/*` → `src/utils/*`
- `@stores/*` → `src/store/*`
- `@plugins/*` → `src/plugins/*`
- `@styles/*` → `src/assets/styles/*`

Alias usage is widespread in core modules (store, router, hooks, utils). Some relative imports persist:
- `1/frontend/src/router/guards/beforeEach.ts`: `from '../routesAlias'`, `from '../routes/staticRoutes'`, `from '../core'`
- `1/frontend/src/router/routes/asyncRoutes.ts`: `from '../modules'`
- `1/frontend/src/router/core/MenuProcessor.ts`: `from '../routes/asyncRoutes'`, `from '../routesAlias'`
- `1/frontend/src/router/core/RouteValidator.ts`: `from '../routesAlias'`
- `1/frontend/src/hooks/core/useTable.ts`: `from '../../utils/table/tableConfig'`
- `1/frontend/src/components/core/layouts/*`: relative imports within component hierarchy
- `1/frontend/src/views/data-management/data-processing/modules/step1-datasource.vue`: `from '../../dataset-hub/modules/dataset-upload.vue'`

**Recommended:** Prefer `@/` alias for all `src/` imports to improve readability and refactoring safety.

### Import Order (implicit, not enforced)

**Backend Python:**
1. Standard library imports (`os`, `uuid`, `asyncio`, `json`, `logging`)
2. Third-party imports (`fastapi`, `sqlalchemy`, `celery`, `redis`, `pydantic`)
3. Application imports (`from app.core.config import settings`, `from app.db.session import get_db`)

**Frontend TypeScript:**
1. Vue/core framework imports (`vue`, `vue-router`, `pinia`)
2. Third-party libraries (`axios`, `element-plus`, `echarts`)
3. Application imports (`@/store`, `@/utils`, `@/hooks`)
4. Relative imports (`./modules`, `../components`)

## Error Handling

### Backend

**API Error Responses:**
- FastAPI `HTTPException` used in `1/backend/app/api/endpoints/datasets.py` and `1/backend/app/api/endpoints/auth.py`
- Status codes: 401 (auth), 400 (bad request), 404 (not found)
- No custom exception handlers registered in `1/backend/app/main.py`
- No global exception handler middleware

**Database Session Cleanup:**
- `1/backend/app/db/session.py`: `get_db()` uses `try/finally` with `db.close()`
- `1/backend/app/tasks/dataset_tasks.py`: Each Celery task uses `try/except/finally` with `db.close()` in finally block

**Celery Task Error Handling:**
- Tasks in `1/backend/app/tasks/dataset_tasks.py` use `try/except` blocks
- On error: publishes failure progress via `publish_progress(task_id, ..., 'failure', str(e))` then re-raises
- No retry mechanism configured in task definitions
- Celery has global limits: `task_time_limit=30*60` (30min hard), `task_soft_time_limit=25*60` (25min soft)

**WebSocket Error Handling:**
- `1/backend/app/api/endpoints/websocket.py`: try/except for `WebSocketDisconnect` and general `Exception`
- `1/backend/app/core/websocket_manager.py`: `send_to_task()` catches exceptions per-connection, marks dead connections for cleanup

### Frontend

**HTTP Error Handling:**
- `1/frontend/src/utils/http/index.ts`: Axios response interceptor handles all errors
- 401 responses trigger `handleUnauthorizedError()` with debounce (3s) then `logOut()`
- `HttpError` class in `1/frontend/src/utils/http/error.ts` for structured error representation
- `ElMessage.error()` for user-facing error display
- Request retry logic for 5xx status codes (configurable, currently `MAX_RETRIES=0`)

**Route Guard Error Handling:**
- `1/frontend/src/router/guards/beforeEach.ts`: top-level try/catch handles guard failures
- Catches errors and redirects to `Exception500` page
- Tracks `routeInitFailed` flag to prevent infinite retry loops
- Tracks `routeInitInProgress` flag to prevent concurrent initialization

**Component Error Handling:**
- `1/frontend/src/utils/sys/error-handle.ts`: setup via `setupErrorHandle(app)` in `main.ts`
- Vue `onErrorCaptured` lifecycle hook for component-level errors

**WebSocket Error Handling:**
- `1/frontend/src/hooks/core/useWebSocketTask.ts`: try/catch in `handleMessage` for JSON parse errors
- `handleError` callback logs errors to console
- Auto-reconnect on close (up to 5 retries with exponential backoff: `retryDelay * retryCount`)

### Prescriptive Patterns

- **Backend API**: Use `HTTPException` for expected error responses
- **Backend DB**: Use `try/finally` for session cleanup; use `Depends(get_db)` dependency injection
- **Frontend HTTP**: Use the centralized Axios instance from `@/utils/http` (never raw `axios`)
- **Frontend WebSocket**: Use `useWebSocketTask()` composable for task progress connections

## Logging

### Backend (inconsistent)

**Using `logging` module:**
- `1/backend/app/main.py`: `logging.basicConfig(level=logging.INFO)`, uses logger
- `1/backend/app/api/endpoints/websocket.py`: `logger = logging.getLogger(__name__)`
- `1/backend/app/core/websocket_manager.py`: `logger = logging.getLogger(__name__)`
- `1/backend/app/core/redis_pubsub.py`: `logger = logging.getLogger(__name__)`

**Using `print()` statements (no structured logging):**
- `1/backend/app/db/init_db.py`: `print('数据库表创建完成')`
- `1/backend/app/api/endpoints/auth.py`: `print(f"[Auth] 收到登录请求: userName={request.userName}")`
- `1/backend/app/tasks/dataset_tasks.py`: `print(f"[WARN] Redis进度发布失败: {e}")` (fallback when Redis unavailable)

**Celery logging:** Uses built-in Celery logging (`--loglevel=info` in worker command)

**Prescriptive:** Use `logging.getLogger(__name__)` for all new backend modules. Migrate existing `print()` calls to structured logging.

### Frontend

- `console.log()` and `console.error()` used throughout
- Prefixed with component/module name: `console.log('[WS] 已连接:', data.message)`, `console.log('[RouteGuard] 开始注册动态路由...')`
- Build config strips `console.log` in production: `terserOptions.compress.drop_console: true`

## Comments

### Language

- **Chinese is the project standard** for all comments and docstrings
- Backend docstrings: `"""健康检查端点"""`, `"""创建加法任务"""`, `"""获取任务状态"""`
- Frontend JSDoc blocks: `/** 用户状态管理模块 */`, `/** 处理路由守卫逻辑 */`
- Inline section comments: `# 配置CORS`, `# 注册路由`, `# 关系`, `# 外键`

### Documentation Patterns

**Backend (docstrings):**
- Used on all endpoint handlers, Celery tasks, and public functions
- Chinese language, single-line for simple functions, multi-line for complex ones
- `1/backend/app/tasks/dataset_tasks.py` has detailed docstrings with Args documentation

**Frontend (JSDoc/TSDoc):**
- Used on stores (`1/frontend/src/store/modules/user.ts`, `1/frontend/src/store/modules/setting.ts`)
- Used on router guards (`1/frontend/src/router/guards/beforeEach.ts`)
- Used on utility modules (`1/frontend/src/utils/http/index.ts`, `1/frontend/src/store/index.ts`)
- `@module`, `@author` tags used in store/utility documentation
- Store actions/functions have `@param` annotations
- Not consistently used across all files — Vue component `<script setup>` blocks often lack JSDoc

## Function Design

### Size Guidelines
- Backend endpoint handlers: 3-15 lines (short and focused)
- Backend Celery tasks: up to ~150 lines (longer due to business logic in `dataset_tasks.py`)
- Frontend store actions: 3-15 lines
- Frontend `<script setup>` blocks: 2-30 lines for simple components, up to ~200 lines for complex views
- Vue SFC templates: 30-200+ lines

### Parameters
- **Backend**: Pydantic `BaseModel` for request bodies, query parameters for GET, FastAPI `Depends(get_db)` for DB sessions
- **Frontend**: Typed parameters in function signatures, TypeScript interfaces for API params/responses
- Store actions accept typed parameters with `@param` annotations

### Return Values
- **Backend**: Pydantic models as response (`response_model=TaskResponse`), or raw dict for mock endpoints (`auth.py`, `users.py`)
- **Frontend**: API functions return typed Promises (`Promise<Dataset>`, `Promise<UploadInitiateResponse>`)
- Store actions typically return `void`, expose reactive `ref`/`computed` for state

### Prescriptive
- Keep functions focused and under 50 lines; extract helpers when longer
- Use Pydantic models for all API request/response schemas (avoid inline dict returns as in `auth.py`)
- Use TypeScript interfaces for all API data shapes (already followed)

## Module Design

### Backend

- Each endpoint module exports a `router = APIRouter()` instance
- Config exports a singleton: `settings = Settings()` in `1/backend/app/core/config.py`
- Celery app exports a singleton: `celery_app` in `1/backend/app/core/celery_app.py`
- WebSocket manager exports a singleton: `manager = ConnectionManager()` in `1/backend/app/core/websocket_manager.py`
- Redis pubsub exports a singleton: `redis_pubsub = RedisPubSub()` in `1/backend/app/core/redis_pubsub.py`
- DB session exports factory: `get_db()` generator in `1/backend/app/db/session.py`
- `__init__.py` files: mostly empty except `1/backend/app/db/models/__init__.py` (all model definitions) and `1/backend/app/tasks/__init__.py` (add/multiply tasks)
- No re-exports from `__init__.py` for `crud/`, `schemas/`, `services/`

### Frontend

- Pinia stores export `useXxxStore` composables: `useUserStore`, `useSettingStore`, `useTaskStore`
- API modules export named functions: `export function fetchLogin()`, `export async function getDatasets()`
- HTTP utility exports default `api` object with method shortcuts: `api.get()`, `api.post()`, `api.del()`
- Router modules export route arrays and core classes
- Utils organized by domain: `utils/http/`, `utils/ui/`, `utils/sys/`, `utils/storage/`
- No barrel `index.ts` files for component directories — components are imported directly

### Prescriptive
- Use `__init__.py` to re-export public API from packages when they grow
- Consider barrel `index.ts` files for component directories to simplify imports

---

*Convention analysis: 2026-05-01*
