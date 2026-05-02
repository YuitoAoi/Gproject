# Codebase Structure

**Analysis Date:** 2026-05-01

## Directory Layout

```
Gproject/
├── .planning/                         # GSD planning artifacts
├── 1/                                 # Main project monorepo
│   ├── AGENTS.md                      # Project-level agent instructions
│   ├── backend/                       # Python FastAPI backend
│   │   ├── .env                       # Environment variables (secrets)
│   │   ├── .env.example               # Environment template
│   │   ├── requirements.txt           # Python dependencies
│   │   ├── app/                       # Application source
│   │   │   ├── __init__.py            # Empty
│   │   │   ├── main.py                # FastAPI app entry point
│   │   │   ├── api/                   # API layer
│   │   │   │   ├── __init__.py        # Empty
│   │   │   │   ├── router.py          # V1 API route aggregator
│   │   │   │   └── endpoints/         # Route handler modules
│   │   │   │       ├── __init__.py    # Empty
│   │   │   │       ├── health.py      # Health check endpoint
│   │   │   │       ├── auth.py        # Auth endpoints (mock)
│   │   │   │       ├── users.py       # User info endpoint (mock)
│   │   │   │       ├── tasks.py       # Celery task endpoints (legacy demo)
│   │   │   │       ├── datasets.py    # Dataset CRUD + upload + processing API
│   │   │   │       └── websocket.py   # WebSocket progress endpoints
│   │   │   ├── core/                  # Core infrastructure
│   │   │   │   ├── __init__.py        # Empty
│   │   │   │   ├── config.py          # Pydantic settings singleton
│   │   │   │   ├── celery_app.py      # Celery instance configuration
│   │   │   │   ├── websocket_manager.py # ConnectionManager singleton
│   │   │   │   └── redis_pubsub.py    # Redis Pub/Sub ↔ WebSocket bridge
│   │   │   ├── db/                    # Database layer
│   │   │   │   ├── __init__.py        # Empty
│   │   │   │   ├── session.py         # Engine, SessionLocal, Base, get_db
│   │   │   │   ├── init_db.py         # Table creation script
│   │   │   │   └── models/            # ORM model definitions
│   │   │   │       └── __init__.py    # All models in single file (132 lines)
│   │   │   ├── crud/                  # Data access layer
│   │   │   │   ├── __init__.py        # Empty
│   │   │   │   └── dataset.py         # Dataset CRUD operations (54 lines)
│   │   │   ├── schemas/               # Pydantic schemas
│   │   │   │   ├── __init__.py        # Empty
│   │   │   │   └── dataset.py         # Dataset request/response schemas (77 lines)
│   │   │   ├── services/              # Business logic layer
│   │   │   │   └── __init__.py        # Empty — NOT IMPLEMENTED
│   │   │   ├── tasks/                 # Celery task definitions
│   │   │   │   ├── __init__.py        # Legacy add/multiply demo tasks
│   │   │   │   └── dataset_tasks.py   # Assembly, clean, convert tasks (392 lines)
│   │   │   └── uploads/               # Upload directory
│   │   │       └── chunks/            # Empty — chunk storage dir
│   │   ├── test_celery.py             # Celery test script
│   │   ├── test_celery_direct.py      # Celery direct test script
│   │   ├── test_celery_tasks.py       # Celery tasks test script
│   │   ├── test_mysql.py              # MySQL connection test script
│   │   └── venv/                      # Python virtual environment
│   └── frontend/                      # Vue 3 SPA frontend
│       ├── .env                       # Environment variables (secrets)
│       ├── .env.development           # Dev env: VITE_PORT, VITE_API_URL, etc.
│       ├── .env.production            # Prod env (secrets)
│       ├── .prettierrc                # Prettier config
│       ├── .stylelintrc.cjs           # Stylelint config
│       ├── eslint.config.mjs          # ESLint flat config
│       ├── commitlint.config.cjs      # Commitlint config
│       ├── index.html                 # SPA entry HTML
│       ├── package.json               # Node dependencies & scripts
│       ├── package-lock.json          # npm lockfile
│       ├── pnpm-lock.yaml             # pnpm lockfile
│       ├── tsconfig.json              # TypeScript config
│       ├── vite.config.ts             # Vite build config with plugins
│       ├── src/                       # Application source
│       │   ├── main.ts                # Vue app entry point
│       │   ├── App.vue                # Root component (ElConfigProvider wrapper)
│       │   ├── api/                   # API client modules
│       │   │   ├── auth.ts            # Login & user info API calls
│       │   │   ├── dataset.ts         # Dataset upload + CRUD API calls
│       │   │   ├── data-manage.ts     # Data management API + mock functions
│       │   │   └── system-manage.ts   # System management API calls
│       │   ├── assets/                # Static assets (images, icons, styles)
│       │   ├── components/            # Reusable Vue components
│       │   │   ├── business/          # Business-specific components
│       │   │   │   └── comment-widget/ # Comment widget
│       │   │   └── core/              # Core infrastructure components
│       │   │       ├── banners/       # Banner components
│       │   │       ├── base/          # Base utility components
│       │   │       ├── cards/         # Card components
│       │   │       ├── charts/        # Chart components (echarts)
│       │   │       ├── forms/         # Form components (schema-based)
│       │   │       ├── layouts/       # Layout system components
│       │   │       │   ├── art-breadcrumb/    # Breadcrumb
│       │   │       │   ├── art-fast-enter/    # Quick access
│       │   │       │   ├── art-global-component/ # Global modals
│       │   │       │   ├── art-global-search/ # Global search
│       │   │       │   ├── art-header-bar/    # Top header bar
│       │   │       │   ├── art-menus/         # Menu bar (horizontal/mixed/sidebar)
│       │   │       │   ├── art-page-content/  # Main content area
│       │   │       │   ├── art-settings-panel/ # Settings panel
│       │   │       │   ├── art-screen-lock/   # Screen lock
│       │   │       │   ├── art-work-tab/      # Work tab bar
│       │   │       │   └── ...                # Other layout widgets
│       │   │       ├── media/         # Media components
│       │   │       ├── others/        # Miscellaneous components
│       │   │       ├── tables/        # Table components
│       │   │       ├── theme/         # Theme components
│       │   │       └── views/         # Generic view wrappers
│       │   ├── config/                # App configuration constants
│       │   ├── directives/            # Vue custom directives
│       │   ├── enums/                 # TypeScript enums
│       │   ├── hooks/                 # Vue composables (hooks)
│       │   │   ├── index.ts           # Barrel export
│       │   │   └── core/              # Core composables
│       │   │       ├── useTheme.ts    # Theme composable
│       │   │       ├── useAuth.ts     # Auth composable
│       │   │       ├── useTable.ts    # Table composable
│       │   │       ├── useCommon.ts   # Common utilities
│       │   │       ├── useWebSocketTask.ts # WebSocket task composable
│       │   │       └── ...            # Other composables
│       │   ├── locales/               # Internationalization
│       │   │   ├── index.ts           # i18n setup
│       │   │   └── langs/             # Language packs
│       │   │       ├── zh.json        # Chinese translations
│       │   │       └── en.json        # English translations
│       │   ├── mock/                  # Mock data
│       │   ├── plugins/               # Vue plugins
│       │   ├── router/                # Vue Router configuration
│       │   │   ├── index.ts           # Router setup & init function
│       │   │   ├── routesAlias.ts     # Route path aliases
│       │   │   ├── core/              # Route infrastructure classes
│       │   │   │   ├── index.ts              # Barrel export
│       │   │   │   ├── RouteRegistry.ts      # Dynamic route registration
│       │   │   │   ├── RouteTransformer.ts   # Menu → Route transformation
│       │   │   │   ├── MenuProcessor.ts      # Menu data processing
│       │   │   │   ├── RouteValidator.ts     # Route validation
│       │   │   │   ├── RoutePermissionValidator.ts # Permission checking
│       │   │   │   ├── ComponentLoader.ts    # Dynamic component loading
│       │   │   │   └── IframeRouteManager.ts # Iframe route management
│       │   │   ├── modules/           # Route module definitions
│       │   │   │   ├── index.ts             # Module aggregator
│       │   │   │   ├── workbench.ts         # Workbench + Data + Model routes
│       │   │   │   ├── dashboard.ts         # Dashboard routes
│       │   │   │   ├── system.ts            # System management routes
│       │   │   │   ├── safeguard.ts         # Safeguard routes
│       │   │   │   ├── template.ts          # Template routes
│       │   │   │   ├── widgets.ts           # Widget routes
│       │   │   │   ├── examples.ts          # Example routes
│       │   │   │   ├── exception.ts         # Exception page routes
│       │   │   │   ├── help.ts              # Help routes
│       │   │   │   ├── article.ts           # Article routes
│       │   │   │   ├── result.ts            # Result routes
│       │   │   │   └── workbench.ts         # App-specific routes
│       │   │   ├── routes/            # Route config arrays
│       │   │   │   ├── staticRoutes.ts      # Public routes (no auth needed)
│       │   │   │   └── asyncRoutes.ts       # Dynamic routes (auth required)
│       │   │   └── guards/            # Navigation guards
│       │   │       ├── beforeEach.ts  # Global before-each guard (436 lines)
│       │   │       └── afterEach.ts   # Global after-each guard
│       │   ├── store/                 # Pinia state management
│       │   │   ├── index.ts           # Pinia setup (persistedstate plugin)
│       │   │   └── modules/           # Store modules
│       │   │       ├── user.ts        # User auth & identity store (242 lines)
│       │   │       ├── menu.ts        # Menu navigation store
│       │   │       ├── setting.ts     # UI settings store
│       │   │       ├── table.ts       # Table state store
│       │   │       ├── task.ts        # Celery task progress store (112 lines)
│       │   │       └── worktab.ts     # Work tab management store
│       │   ├── types/                 # TypeScript type definitions
│       │   │   ├── index.ts           # Type barrel
│       │   │   ├── api/               # API type declarations
│       │   │   ├── common/            # Common type declarations
│       │   │   ├── component/         # Component type declarations
│       │   │   ├── config/            # Config type declarations
│       │   │   ├── directive/         # Directive type declarations
│       │   │   ├── import/            # Auto-import type declarations
│       │   │   ├── router/            # Router type declarations
│       │   │   └── store/             # Store type declarations
│       │   ├── utils/                 # Utility modules
│       │   │   ├── index.ts           # Utility barrel
│       │   │   ├── http/              # HTTP client
│       │   │   │   ├── index.ts       # Axios wrapper (214 lines)
│       │   │   │   ├── status.ts      # HTTP status codes
│       │   │   │   └── error.ts       # HTTP error classes & handlers
│       │   │   ├── socket/            # WebSocket client
│       │   │   │   └── index.ts       # WebSocketClient class (423 lines)
│       │   │   ├── router.ts          # Router utilities (NProgress, title)
│       │   │   ├── navigation.ts      # Navigation utilities (worktab)
│       │   │   ├── storage/           # Storage key management
│       │   │   ├── sys/               # System utilities (error handle, console)
│       │   │   ├── form/              # Form utilities
│       │   │   ├── table/             # Table utilities
│       │   │   ├── ui/                # UI utilities (loading service)
│       │   │   └── constants/         # Constant definitions
│       │   └── views/                 # Page-level Vue components
│       │       ├── index/             # Main layout shell
│       │       │   └── index.vue      # AppLayout (sidebar + header + content)
│       │       ├── auth/              # Auth pages (login, register, forgot)
│       │       ├── dashboard/         # Dashboard pages (analysis, console, ecommerce)
│       │       ├── data-management/   # Data management pages
│       │       │   ├── index.vue      # Redirect/layout stub
│       │       │   ├── dataset-hub/   # Dataset CRUD view (1094 lines - fully built)
│       │       │   └── data-processing/ # Data cleaning/convert view
│       │       ├── model-factory/     # Model training pages
│       │       │   ├── new-training/  # New training page (placeholder)
│       │       │   └── model-registry/ # Model registry page (placeholder)
│       │       ├── model-training/    # Model training page (placeholder)
│       │       ├── model-inference/   # Model inference page (placeholder)
│       │       ├── task-monitoring/   # Task monitoring page (placeholder)
│       │       ├── system-management/ # System management pages
│       │       │   ├── users-roles/   # User & role management (placeholder)
│       │       │   └── advanced-settings/ # Advanced settings (placeholder)
│       │       ├── workbench/         # Workbench pages
│       │       ├── exception/         # Error pages (403, 404, 500)
│       │       ├── outside/           # Iframe container pages
│       │       ├── safeguard/         # Safeguard pages
│       │       ├── result/            # Result pages
│       │       ├── template/          # Template pages
│       │       ├── widgets/           # Widget pages
│       │       ├── article/           # Article pages
│       │       ├── change/            # Change pages
│       │       ├── examples/          # Example pages
│       │       └── system/            # System pages
│       ├── public/                    # Static public files
│       ├── scripts/                   # Build/tooling scripts
│       ├── dist/                      # Production build output (generated)
│       └── node_modules/              # Node dependencies (generated)
├── 111.txt                            # Reference file
├── AGENTS.md                          # Root agent instructions
├── art-design-pro-3.0.2/              # Art Design Pro template reference
├── datafile/                          # Dataset file storage root (shared)
└── front需求.md                       # Frontend requirements document
```

## Directory Purposes

**`1/backend/app/api/`** — API Layer:
- Purpose: REST API endpoint definitions and route aggregation
- Contains: `router.py` (aggregates all endpoint routers into one `api_router`), `endpoints/` with individual route handler modules
- Key files: `1/backend/app/api/router.py`, `1/backend/app/api/endpoints/datasets.py` (153 lines, most complex endpoint), `1/backend/app/api/endpoints/websocket.py` (132 lines)

**`1/backend/app/core/`** — Core Infrastructure:
- Purpose: Application configuration, Celery setup, WebSocket management, Redis bridge
- Contains: Singleton instances consumed by all other layers
- Key files: `1/backend/app/core/config.py` (23 lines, pydantic-settings), `1/backend/app/core/celery_app.py` (21 lines, solo worker pool), `1/backend/app/core/redis_pubsub.py` (126 lines, Pub/Sub bridge)

**`1/backend/app/db/`** — Database Layer:
- Purpose: SQLAlchemy ORM setup, session management, model definitions, table creation
- Contains: `session.py` (24 lines, engine/session/Base/get_db), `init_db.py` (12 lines, table creation), `models/__init__.py` (132 lines, all 5 models in one file)
- Key files: `1/backend/app/db/models/__init__.py` — all model classes (`User`, `Dataset`, `Tag`, `TrainingTask`, `TrainedModel`) defined in a single module

**`1/backend/app/crud/`** — Data Access Layer:
- Purpose: Database read/write operation functions
- Contains: `dataset.py` (54 lines, 5 CRUD functions), empty `__init__.py`
- Key files: `1/backend/app/crud/dataset.py` — only implemented CRUD module
- Missing: CRUD for `User`, `TrainingTask`, `TrainedModel`, `Tag` tables

**`1/backend/app/schemas/`** — Schema Layer:
- Purpose: Pydantic models for request/response serialization
- Contains: `dataset.py` (77 lines, 7 schema classes), empty `__init__.py`
- Key files: `1/backend/app/schemas/dataset.py` — only implemented schema module
- Note: Some schemas (e.g., `HealthResponse`, `TaskRequest`, `LoginRequest`) are still inline in endpoint files

**`1/backend/app/services/`** — Service Layer:
- Purpose: Intended for business logic orchestration
- Contains: Only empty `__init__.py` — **entirely unimplemented**
- Impact: Business logic currently embedded directly in endpoint handlers and Celery tasks

**`1/backend/app/tasks/`** — Task Layer:
- Purpose: Celery background task definitions
- Contains: `__init__.py` (legacy `add`/`multiply` demo tasks), `dataset_tasks.py` (392 lines, 3 tasks: assembly, cleaning, format conversion)
- Key files: `1/backend/app/tasks/dataset_tasks.py` — full chunked upload assembly, CSV/JSON data cleaning, Alpaca/ShareGPT format conversion with granular progress reporting

**`1/backend/app/uploads/`** — Upload Storage:
- Purpose: Temporary chunk file storage during dataset upload
- Contains: `chunks/` directory (empty in source, populated at runtime)
- Note: Actual runtime chunks stored in `datafile/chunks/` at project root (see `datasets.py` line 27: `PROJECT_ROOT = ...`)

**`1/frontend/src/api/`** — API Client Modules:
- Purpose: Typed API call functions for each backend domain
- Contains: `auth.ts` (login + user info), `dataset.ts` (198 lines, full chunked upload + CRUD + processing), `data-manage.ts` (130 lines, mostly mock functions), `system-manage.ts` (user/role/menu list)
- Key files: `1/frontend/src/api/dataset.ts` — complete client-side chunked upload workflow

**`1/frontend/src/components/core/layouts/`** — Layout System:
- Purpose: Application shell components (sidebar, header, content area, tabs, breadcrumb)
- Contains: 13 layout component subdirectories, each with `index.vue` and sometimes `widget/` sub-components
- Key files: `art-sidebar-menu/`, `art-header-bar/`, `art-page-content/index.vue`, `art-work-tab/`
- Pattern: Components follow `<script setup>` Composition API, use Element Plus + Tailwind

**`1/frontend/src/router/core/`** — Router Infrastructure:
- Purpose: Dynamic route registration, menu processing, permission validation
- Contains: 7 TypeScript classes for route management
- Key files: `RouteRegistry.ts`, `MenuProcessor.ts`, `RoutePermissionValidator.ts`, `IframeRouteManager.ts`
- Pattern: Class-based with barrel exports via `index.ts`

**`1/frontend/src/router/guards/`** — Navigation Guards:
- Purpose: Route lifecycle hooks for auth, dynamic registration, permission checking
- Contains: `beforeEach.ts` (436 lines, complex guard logic), `afterEach.ts`
- Key files: `beforeEach.ts` — handles login check, dynamic route registration, path validation, root redirect

**`1/frontend/src/store/modules/`** — State Stores:
- Purpose: Domain-specific reactive state management with persistence
- Contains: `user.ts` (242 lines, auth/identity/language/lock), `task.ts` (112 lines, Celery task progress), `setting.ts`, `menu.ts`, `table.ts`, `worktab.ts`
- Key files: `user.ts` — handles login, logout, token persistence, user info, search history, lock screen

**`1/frontend/src/views/data-management/`** — Data Management Views:
- Purpose: Dataset management and data processing UI
- Contains: `dataset-hub/` (1094-line index.vue + modules/), `data-processing/` (index.vue + modules/)
- Key files: `dataset-hub/index.vue` — fully built dataset management with upload dialog, table, stats cards, tags, search

**`1/frontend/src/views/model-factory/`** — Model Factory Views:
- Purpose: Model training and registry UI
- Contains: `new-training/index.vue`, `model-registry/index.vue`
- Status: Both are **placeholders** — display "即将上线" (coming soon) messages

**`1/frontend/src/views/model-training/`, `views/task-monitoring/`, `views/model-inference/`** — Placeholder Views:
- Status: All contain only placeholder templates with SVG icons and "即将上线" text
- Implementation: Minimal `<script setup>` (only `defineOptions({ name })`), no real functionality

**`1/frontend/src/utils/http/`** — HTTP Client:
- Purpose: Axios wrapper with interceptors, auth, error handling, retry
- Contains: `index.ts` (214 lines, core client), `status.ts` (status codes), `error.ts` (error classes)
- Key files: `index.ts` — exports `default api` object with `get`, `post`, `put`, `del`, `request` methods

**`1/frontend/src/utils/socket/`** — WebSocket Client:
- Purpose: Persistent WebSocket connection with resilience
- Contains: `index.ts` (423 lines, `WebSocketClient` singleton class)
- Pattern: Singleton with `getInstance()`, message queue, heartbeat, exponential backoff reconnection, connection timeout

**`1/frontend/src/hooks/core/`** — Composables:
- Purpose: Vue 3 composables for reusable component logic
- Contains: 13 composable files including `useTheme.ts`, `useAuth.ts`, `useTable.ts`, `useWebSocketTask.ts`, `useCommon.ts`
- Pattern: Single-file composables with `use` prefix, export functions that return reactive refs/methods

## Key File Locations

**Entry Points:**
- `1/backend/app/main.py` — FastAPI application creation, CORS, route registration, lifespan
- `1/backend/app/core/celery_app.py` — Celery worker configuration
- `1/backend/app/db/init_db.py` — Database table creation
- `1/frontend/src/main.ts` — Vue app creation, Pinia/Router/i18n initialization
- `1/frontend/vite.config.ts` — Vite build config, dev proxy, path aliases (161 lines)
- `1/frontend/index.html` — SPA HTML shell

**Configuration:**
- `1/backend/app/core/config.py` — Pydantic settings with `.env` loading
- `1/backend/.env.example` — Backend environment template
- `1/frontend/.env.development` — Frontend dev env: `VITE_PORT=3000`, `VITE_API_URL`, `VITE_API_PROXY_URL`, `VITE_WS_URL`
- `1/frontend/.env.production` — Frontend prod env
- `1/frontend/vite.config.ts` — Vite config with auto-import, compression, SCSS globals, path aliases
- `1/frontend/tsconfig.json` — TypeScript config (strict mode, ES2020 target, `@/*` path alias)
- `1/frontend/eslint.config.mjs` — ESLint flat config
- `1/frontend/.prettierrc` — Prettier formatting config
- `1/frontend/.stylelintrc.cjs` — Stylelint config
- `1/frontend/commitlint.config.cjs` — Commit message linting

**Core Logic:**
- `1/backend/app/db/models/__init__.py` — All ORM models (`User`, `Dataset`, `Tag`, `TrainingTask`, `TrainedModel`)
- `1/backend/app/crud/dataset.py` — Dataset CRUD operations
- `1/backend/app/schemas/dataset.py` — Dataset Pydantic schemas
- `1/backend/app/tasks/dataset_tasks.py` — Celery tasks (assembly, cleaning, format conversion)
- `1/backend/app/core/websocket_manager.py` — WebSocket connection manager
- `1/backend/app/core/redis_pubsub.py` — Redis Pub/Sub → WebSocket bridge
- `1/frontend/src/utils/http/index.ts` — Axios HTTP client
- `1/frontend/src/utils/socket/index.ts` — WebSocket client
- `1/frontend/src/store/modules/user.ts` — User authentication store
- `1/frontend/src/store/modules/task.ts` — Task progress store
- `1/frontend/src/api/dataset.ts` — Dataset API client
- `1/frontend/src/router/guards/beforeEach.ts` — Route guard logic
- `1/frontend/src/router/core/RouteRegistry.ts` — Dynamic route management

**Placeholder / Stub Files:**
- `1/backend/app/services/__init__.py` — Empty, **entire service layer not implemented**
- `1/backend/app/crud/__init__.py` — Empty, only `dataset.py` implemented
- `1/backend/app/schemas/__init__.py` — Empty, only `dataset.py` implemented
- `1/backend/app/api/__init__.py` — Empty
- `1/backend/app/api/endpoints/__init__.py` — Empty
- `1/backend/app/core/__init__.py` — Empty
- `1/backend/app/db/__init__.py` — Empty
- `1/backend/app/__init__.py` — Empty
- `1/frontend/src/views/model-training/index.vue` — Placeholder page
- `1/frontend/src/views/model-inference/index.vue` — Placeholder page
- `1/frontend/src/views/task-monitoring/index.vue` — Placeholder page
- `1/frontend/src/views/model-factory/new-training/index.vue` — Placeholder page
- `1/frontend/src/views/model-factory/model-registry/index.vue` — Placeholder page

**Testing:**
- `1/backend/test_celery.py` — Celery connection test
- `1/backend/test_celery_direct.py` — Celery direct invocation test
- `1/backend/test_celery_tasks.py` — Celery tasks test
- `1/backend/test_mysql.py` — MySQL connection test
- Frontend: No test files detected (no `*.test.ts`, `*.spec.ts`, or test directory)

## Naming Conventions

**Files:**
- Backend Python: `snake_case` (e.g., `celery_app.py`, `init_db.py`, `session.py`, `redis_pubsub.py`, `dataset_tasks.py`)
- Backend endpoint files: `snake_case` singular nouns (e.g., `health.py`, `tasks.py`, `datasets.py`)
- Frontend TypeScript: `camelCase` (e.g., `httpClient.ts` not used; actual: `index.ts` for modules)
- Frontend Vue components: `PascalCase` (e.g., `App.vue`), but all component files are `index.vue` within named directories
- Frontend composables: `use` prefix camelCase (e.g., `useTheme.ts`, `useWebSocketTask.ts`)

**Directories:**
- Backend: `snake_case` (e.g., `api/`, `endpoints/`, `crud/`, `services/`)
- Frontend view directories: `kebab-case` (e.g., `data-management/`, `model-factory/`, `task-monitoring/`)
- Frontend component directories: `kebab-case` with `art-` prefix for core components (e.g., `art-header-bar/`, `art-sidebar-menu/`)
- Frontend sub-view modules: `camelCase` or `kebab-case` (e.g., `dataset-hub/`, `data-processing/`)

**Functions:**
- Backend: `snake_case` (e.g., `get_db()`, `health_check()`, `assemble_and_save_dataset()`, `publish_progress()`)
- Frontend: `camelCase` (e.g., `useUserStore()`, `setupBeforeEachGuard()`, `initRouter()`)
- Pinia stores: `useXxxStore` composable pattern

**Types/Classes:**
- Backend: `PascalCase` for models (e.g., `User`, `Dataset`, `TrainingTask`), enums (e.g., `TaskStatus`, `ModelStatus`)
- Frontend: `PascalCase` for types, interfaces, classes (e.g., `TaskProgress`, `WebSocketClient`, `RouteRegistry`)

**Constants:**
- Backend: `UPPER_SNAKE_CASE` in Settings class (e.g., `DATABASE_URL`, `REDIS_URL`)
- Frontend: `UPPER_SNAKE_CASE` for config constants (e.g., `SETTING_DEFAULT_CONFIG`)

## Where to Add New Code

**New Backend API Endpoint:**
- Primary code: `1/backend/app/api/endpoints/{new_feature}.py` — create a new APIRouter module
- Registration: Add to `1/backend/app/api/router.py` with `.include_router()`
- Schemas: `1/backend/app/schemas/{new_feature}.py` — Pydantic request/response models
- CRUD: `1/backend/app/crud/{new_feature}.py` — database operations
- Tasks: `1/backend/app/tasks/{new_feature}_tasks.py` — Celery background tasks
- Tests: Add test scripts to `1/backend/` root (following `test_*.py` pattern)

**New Frontend Page:**
- Primary code: `1/frontend/src/views/{domain}/{page-name}/index.vue` — page component
- Sub-components: `1/frontend/src/views/{domain}/{page-name}/modules/` — page-specific sub-components
- Route definition: `1/frontend/src/router/modules/{domain}.ts` — add route in existing or new module file
- Route aggregation: Update `1/frontend/src/router/modules/index.ts` if new module file
- API calls: `1/frontend/src/api/{domain}.ts` — new API module file
- Store: `1/frontend/src/store/modules/{feature}.ts` — if new state needed
- Types: `1/frontend/src/types/api/api.d.ts` or new `.d.ts` in `types/api/`

**New Layout Component:**
- Implementation: `1/frontend/src/components/core/layouts/{component-name}/index.vue`
- Sub-widgets: `1/frontend/src/components/core/layouts/{component-name}/widget/`

**New Composable (Hook):**
- Implementation: `1/frontend/src/hooks/core/use{Feature}.ts`
- Barrel export: Update `1/frontend/src/hooks/index.ts` if new file

**Utilities:**
- Shared helpers: `1/frontend/src/utils/{category}/` — add module file + update barrel if needed
- HTTP client: Modify `1/frontend/src/utils/http/index.ts` for interceptors, auth
- WebSocket: Modify `1/frontend/src/utils/socket/index.ts` for connection behavior

## Special Directories

**`1/backend/app/uploads/chunks/`** — Chunk upload storage:
- Purpose: Temporary storage for file chunks during upload
- Generated: No (empty in source, populated at runtime)
- Committed: Yes (empty directory tracked)
- Note: Actual runtime chunks go to `datafile/chunks/` at project root per `datasets.py` configuration

**`1/backend/venv/`** — Python virtual environment:
- Purpose: Isolated Python dependencies
- Generated: Yes (created by `python -m venv`)
- Committed: No (gitignored)

**`1/frontend/node_modules/`** — Node dependencies:
- Purpose: Installed npm packages
- Generated: Yes (created by `npm install`)
- Committed: No (gitignored)

**`1/frontend/dist/`** — Production build output:
- Purpose: Built Vue SPA assets
- Generated: Yes (created by `npm run build`)
- Committed: No (gitignored)

**`1/frontend/.husky/`** — Git hooks:
- Purpose: Pre-commit hooks (lint-staged, commitlint)
- Generated: Yes (configured by `npm run prepare`)
- Committed: Yes

**`1/frontend/src/types/import/`** — Auto-generated type declarations:
- Purpose: Auto-import type definitions (Vue, Vue Router, Pinia, Element Plus)
- Generated: Yes (by `unplugin-auto-import` and `unplugin-vue-components`)
- Committed: No (gitignored, generated at build/dev time)

**`datafile/`** — Shared data storage root:
- Purpose: Runtime storage for dataset files and chunks, shared between backend worker and FastAPI
- Generated: No (manually created or at runtime)
- Committed: Not tracked (check `.gitignore`)
- Used by: `1/backend/app/api/endpoints/datasets.py`, `1/backend/app/tasks/dataset_tasks.py`

---

*Structure analysis: 2026-05-01*
