# Coding Conventions

**Analysis Date:** 2026-04-13

## Naming Patterns

**Files - Backend (Python):**
- Module directories use `snake_case`: `api/`, `db/`, `core/`, `crud/`, `services/`, `schemas/`
- Python modules use `snake_case`: `celery_app.py`, `init_db.py`, `session.py`
- Endpoint files use `snake_case` singular nouns: `health.py`, `tasks.py`

**Files - Frontend (TypeScript/Vue):**
- Vue components use `PascalCase`: `MainLayout.vue`, `TheHeader.vue`, `TheSidebar.vue`, `HomeView.vue`
- Layout components prefixed with `The`: `TheHeader.vue`, `TheSidebar.vue`
- View components suffixed with `View`: `HomeView.vue`, `DashboardView.vue`, `DataManagementView.vue`
- TypeScript modules use `camelCase`: `httpClient.ts`, `websocket.ts`, `ui.ts`
- Directories use `kebab-case` or `camelCase`: `training/`, `layout/`

**Functions (Backend):**
- Use `snake_case` for all Python functions: `get_db()`, `init_db()`, `health_check()`, `create_add_task()`
- Route handler functions are `async def` with descriptive `snake_case` names
- Celery tasks use `snake_case`: `add()`, `multiply()`

**Functions (Frontend):**
- Use `camelCase` for all TypeScript functions: `toggleSidebar()`, `setSidebarCollapsed()`
- WebSocket class methods use `camelCase`: `connect()`, `disconnect()`, `scheduleReconnect()`
- Exported convenience functions use `camelCase`: `connectWebSocket()`, `onWebSocketMessage()`

**Variables:**
- Backend: `snake_case` for module-level variables: `api_router`, `celery_app`, `settings`
- Frontend: `camelCase` for variables and refs: `isCollapsed`, `httpClient`, `reconnectInterval`
- Constants: `UPPER_SNAKE_CASE` in Settings class: `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`

**Types:**
- Backend Python Enums use `PascalCase` with `PascalCase` values: `UserRole.ADMIN`, `TaskStatus.PENDING`, `ModelStatus.UNLOADED`
- SQLAlchemy model classes use `PascalCase`: `User`, `Dataset`, `TrainingTask`, `TrainedModel`
- Pydantic models use `PascalCase`: `HealthResponse`, `TaskRequest`, `TaskResponse`
- Frontend: `PascalCase` for Vue component names and TypeScript types
- TypeScript type aliases use `PascalCase`: `MessageHandler`

## Code Style

**Formatting:**
- No linter or formatter config detected in the project root (no `.eslintrc`, `.prettierrc`, `biome.json`, `ruff.toml`, `black` config, or similar)
- Frontend: relies on Vue/Vite defaults; TypeScript strict mode enabled in `tsconfig.json`
- Backend: no Black/isort/flake8/pylint config detected

**Indentation:**
- Backend Python: 4 spaces (standard PEP 8)
- Frontend TypeScript/Vue: 2 spaces (standard Vue/Vite convention)

**String Quotes:**
- Backend Python: single quotes for imports and simple strings, double quotes for f-strings and docstrings
- Frontend TypeScript: single quotes for imports and string literals

**TypeScript Configuration** (`1/frontend/tsconfig.json`):
- `"strict": true` — strict type checking
- `"noUnusedLocals": false` — allows unused locals
- `"noUnusedParameters": false` — allows unused params
- `"target": "ES2020"`, `"module": "ESNext"`
- Path alias: `@/*` → `src/*`

## Import Organization

**Backend (Python):**
1. Standard library imports: `from datetime import datetime`, `import enum`
2. Third-party imports: `from fastapi import APIRouter`, `from sqlalchemy import Column, ...`
3. Local application imports: `from app.core.config import settings`, `from app.db.session import Base`

**Frontend (TypeScript):**
1. Vue ecosystem: `import { createApp } from 'vue'`
2. Third-party libraries: `import ElementPlus from 'element-plus'`, `import axios from 'axios'`
3. Local modules: `import { useUIStore } from '../../store/ui'`

**Path Aliases (Frontend):**
- `@/*` maps to `src/*` in `tsconfig.json` — available but not currently used in source files
- Current imports use relative paths: `'../../store/ui'`, `'../views/HomeView.vue'`
- Prefer using `@/` alias for consistency going forward

## Error Handling

**Backend (FastAPI):**
- HTTP errors raised via `HTTPException` from FastAPI: `from fastapi import HTTPException` (imported in `1/backend/app/api/endpoints/tasks.py`)
- No custom exception handlers or middleware registered in `1/backend/app/main.py`
- Database session cleanup uses `try/finally`: `get_db()` in `1/backend/app/db/session.py`
- No global exception handler middleware configured

**Frontend (HTTP Client):**
- Axios response interceptor handles errors globally in `1/frontend/src/api/httpClient.ts`
- Error messages extracted from `error.response?.data?.detail || error.message || '请求失败'`
- `ElNotification` used for user-facing error display
- 401 responses trigger `localStorage.removeItem('auth_token')` and redirect to `/`
- All errors are re-rejected via `Promise.reject(error)` for local handling

**Frontend (WebSocket):**
- Connection errors logged via `console.error` and trigger auto-reconnect with 5s interval
- JSON parse errors in `onmessage` fall back to dispatching raw data: `dispatch('message', event.data)`

**Patterns:**
- Use `HTTPException` for API error responses
- Use `try/finally` for resource cleanup (DB sessions)
- Use Axios interceptors for centralized HTTP error handling
- Use `ElNotification` for user-facing error display in the frontend
- Use console logging (`console.log`, `console.error`) for WebSocket debugging

## Logging

**Framework:** Console-based (no structured logging framework)

**Backend:**
- No logging framework configured (no `logging` module usage found)
- `print()` used in `1/backend/app/db/init_db.py` for startup messages
- Celery uses its own logging (`--loglevel=info` in worker command)

**Frontend:**
- `console.log()` and `console.error()` used in `1/frontend/src/api/websocket.ts`
- Prefixed with `[WebSocket]` for categorization: `console.log('[WebSocket] Connected to', this.url)`

**Patterns:**
- Backend: Add `import logging; logger = logging.getLogger(__name__)` for new modules
- Frontend: Use `console.log('[ComponentName]')` prefix pattern for debugging
- Prefer structured logging over raw `print()` statements

## Comments

**When to Comment:**
- Chinese language docstrings on endpoint handlers: `"""健康检查端点"""`, `"""创建加法任务"""`, `"""获取任务状态"""`
- Chinese inline comments for section labels: `# 配置CORS`, `# 注册路由`, `# 关系`, `# 外键`
- Comments in Chinese are the project standard

**JSDoc/TSDoc:**
- Not used in the frontend codebase
- Celery task docstrings use Chinese: `"""示例任务：加法运算"""`

**Patterns:**
- Use Chinese for all comments and docstrings
- Use docstrings (`"""..."""`) for Python functions and classes
- Use section-separator comments (`# 配置CORS`) for logical groupings in configuration files
- No JSDoc/TSDoc convention established yet — add for complex functions

## Function Design

**Size:**
- Backend endpoint handlers are short (3-10 lines)
- Frontend component `<script setup>` blocks are concise (2-23 lines)
- Keep functions focused and under 50 lines; extract helpers when longer

**Parameters:**
- Backend: Use Pydantic `BaseModel` classes for request bodies: `TaskRequest`, `TaskRequest(BaseModel)`
- Backend: Use FastAPI dependency injection for DB sessions: `Depends(get_db)` (pattern established, not yet used)
- Frontend: Use typed parameters in class methods and functions

**Return Values:**
- Backend: Use Pydantic `BaseModel` for response serialization: `TaskResponse`, `HealthResponse`
- Backend: Use `response_model=TaskResponse` parameter in route decorators
- Frontend: Store composables return reactive refs and methods

## Module Design

**Exports:**
- Backend: Each endpoint module exports a `router = APIRouter()` instance
- Backend: Config exports a singleton `settings = Settings()`
- Frontend: Pinia stores export `useXxxStore` composables: `useUIStore`
- Frontend: API modules export both default and named exports: `export default httpClient`, `export const apiEndpoints`
- Frontend: WebSocket exports named functions: `export const connectWebSocket`, `export const onWebSocketMessage`

**Barrel Files:**
- Backend: `__init__.py` files exist but are empty for `schemas/`, `crud/`, `services/`, `api/`, `api/endpoints/`
- Backend: Only `1/backend/app/db/models/__init__.py` has substantive content (all model definitions)
- Frontend: No barrel `index.ts` files for component directories
- Pattern: Use `__init__.py` to re-export public API when modules grow

**Vue Component Pattern:**
```vue
<template>
  <!-- Element Plus components and layout -->
</template>

<script setup lang="ts">
// Imports
// Store/state usage
// Local functions
</script>

<style scoped>
/* Component-scoped styles */
</style>
```

---

*Convention analysis: 2026-04-13*