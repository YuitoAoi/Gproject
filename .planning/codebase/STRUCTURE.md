# Codebase Structure

**Analysis Date:** 2026-04-13

## Directory Layout

```
1/
├── backend/                    # Python FastAPI backend
│   ├── app/                    # Application source code
│   │   ├── __init__.py         # Package init (empty)
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── tasks.py            # Celery shared task definitions
│   │   ├── api/                # API layer
│   │   │   ├── __init__.py     # Package init (empty)
│   │   │   ├── router.py       # Top-level API router aggregation
│   │   │   └── endpoints/      # Individual endpoint modules
│   │   │       ├── __init__.py # Package init (empty)
│   │   │       ├── health.py   # Health check endpoint
│   │   │       └── tasks.py    # Task creation/status endpoints
│   │   ├── core/               # Core infrastructure
│   │   │   ├── __init__.py     # Package init (empty)
│   │   │   ├── config.py       # Settings (pydantic-settings)
│   │   │   └── celery_app.py   # Celery app instance
│   │   ├── crud/               # CRUD operations (scaffolded, empty)
│   │   │   └── __init__.py     # Package init (empty)
│   │   ├── db/                 # Database layer
│   │   │   ├── __init__.py     # Package init (empty)
│   │   │   ├── session.py      # Engine, SessionLocal, Base, get_db
│   │   │   ├── init_db.py      # Table creation script
│   │   │   └── models/         # SQLAlchemy ORM models
│   │   │       └── __init__.py # All model classes defined here
│   │   ├── schemas/            # Pydantic schemas (scaffolded, empty)
│   │   │   └── __init__.py     # Package init (empty)
│   │   └── services/           # Business logic (scaffolded, empty)
│   │       └── __init__.py     # Package init (empty)
│   ├── requirements.txt        # Python dependencies
│   └── venv/                   # Python virtual environment (git-ignored)
├── frontend/                   # Vue 3 SPA frontend
│   ├── index.html              # HTML entry point
│   ├── package.json            # npm dependencies and scripts
│   ├── package-lock.json       # npm lockfile
│   ├── tsconfig.json           # TypeScript config (app code)
│   ├── tsconfig.node.json      # TypeScript config (Vite config)
│   ├── vite.config.ts          # Vite dev server and build config
│   └── src/                    # Application source code
│       ├── main.ts             # Vue app bootstrap
│       ├── App.vue             # Root component
│       ├── env.d.ts            # Vite/Vue type declarations
│       ├── api/                 # API communication modules
│       │   ├── httpClient.ts   # Axios instance with interceptors
│       │   └── websocket.ts    # WebSocket manager class
│       ├── assets/             # Static assets (empty)
│       ├── components/         # Reusable components
│       │   └── layout/         # Layout-specific components
│       │       ├── TheHeader.vue   # App header bar
│       │       └── TheSidebar.vue  # Navigation sidebar
│       ├── features/           # Feature modules (empty, planned)
│       ├── layouts/            # Page layout wrappers
│       │   └── MainLayout.vue  # App shell (header + sidebar + content)
│       ├── router/             # Vue Router config
│       │   └── index.ts        # Route definitions
│       ├── store/              # Pinia stores
│       │   └── ui.ts           # UI state (sidebar collapse)
│       └── views/              # Page-level components
│           ├── HomeView.vue            # Landing page
│           ├── DashboardView.vue       # Dashboard (placeholder)
│           ├── DataManagementView.vue  # Data management (placeholder)
│           └── training/               # Training-related views
│               ├── TasksView.vue       # Training tasks (placeholder)
│               └── ModelsView.vue      # Model management (placeholder)
└── .planning/                  # Project planning documents
    ├── PROJECT.md              # Project context
    ├── REQUIREMENTS.md         # Requirements spec
    ├── ROADMAP.md              # Phase roadmap
    ├── STATE.md                # Current project state
    ├── config.json             # Planning config
    ├── 1-PLAN.md ... 5-PLAN.md # Phase plans
    └── 1-CONTEXT.md ... 5-CONTEXT.md # Phase contexts
```

## Directory Purposes

**`1/backend/app/api/`:**
- Purpose: REST API endpoint definitions
- Contains: FastAPI `APIRouter` modules, Pydantic models (inline)
- Key files: `1/backend/app/api/router.py` (route aggregation), `1/backend/app/api/endpoints/health.py`, `1/backend/app/api/endpoints/tasks.py`

**`1/backend/app/core/`:**
- Purpose: Application infrastructure and configuration
- Contains: Settings class, Celery app factory
- Key files: `1/backend/app/core/config.py`, `1/backend/app/core/celery_app.py`

**`1/backend/app/db/`:**
- Purpose: Database access layer
- Contains: SQLAlchemy engine/session, ORM models, table init script
- Key files: `1/backend/app/db/session.py`, `1/backend/app/db/models/__init__.py`, `1/backend/app/db/init_db.py`

**`1/backend/app/crud/`:**
- Purpose: Database CRUD operations (planned)
- Contains: Empty `__init__.py` only
- Key files: Not yet created

**`1/backend/app/services/`:**
- Purpose: Business logic layer (planned)
- Contains: Empty `__init__.py` only
- Key files: Not yet created — planned: `inference_service.py` (Phase 5)

**`1/backend/app/schemas/`:**
- Purpose: Pydantic request/response schemas (planned)
- Contains: Empty `__init__.py` only
- Key files: Not yet created

**`1/frontend/src/api/`:**
- Purpose: Backend communication (HTTP + WebSocket)
- Contains: Axios client instance, WebSocket manager singleton
- Key files: `1/frontend/src/api/httpClient.ts`, `1/frontend/src/api/websocket.ts`

**`1/frontend/src/views/`:**
- Purpose: Page-level Vue components (one per route)
- Contains: Route target components, organized by feature area
- Key files: `1/frontend/src/views/HomeView.vue`, `1/frontend/src/views/DashboardView.vue`, `1/frontend/src/views/DataManagementView.vue`, `1/frontend/src/views/training/TasksView.vue`, `1/frontend/src/views/training/ModelsView.vue`

**`1/frontend/src/components/`:**
- Purpose: Reusable Vue components
- Contains: Layout components (header, sidebar)
- Key files: `1/frontend/src/components/layout/TheHeader.vue`, `1/frontend/src/components/layout/TheSidebar.vue`

**`1/frontend/src/layouts/`:**
- Purpose: Page layout wrapper components
- Contains: Main app shell layout
- Key files: `1/frontend/src/layouts/MainLayout.vue`

**`1/frontend/src/store/`:**
- Purpose: Pinia state management stores
- Contains: One store file per domain
- Key files: `1/frontend/src/store/ui.ts`

**`1/frontend/src/router/`:**
- Purpose: Vue Router configuration
- Contains: Route definitions and router instance
- Key files: `1/frontend/src/router/index.ts`

**`1/frontend/src/features/`:**
- Purpose: Feature-module organization (planned)
- Contains: Empty directory — intended for feature-scoped components/composables
- Key files: Not yet created

## Key File Locations

**Entry Points:**
- `1/backend/app/main.py`: FastAPI application creation, CORS middleware, router registration
- `1/frontend/src/main.ts`: Vue app creation, Pinia/Router/ElementPlus registration, mount to `#app`
- `1/frontend/index.html`: HTML shell that loads `src/main.ts`

**Configuration:**
- `1/backend/app/core/config.py`: `Settings` class with all backend config (DB URL, Redis, CORS, Celery)
- `1/frontend/vite.config.ts`: Vite dev server port (3000), API proxy to backend (8000)
- `1/frontend/tsconfig.json`: TypeScript config, `@/*` path alias to `src/*`
- `1/backend/requirements.txt`: Python package dependencies

**Core Logic:**
- `1/backend/app/db/models/__init__.py`: All SQLAlchemy ORM models (`User`, `Dataset`, `TrainingTask`, `TrainedModel`) and enums (`UserRole`, `TaskStatus`, `ModelStatus`)
- `1/backend/app/api/router.py`: Route aggregation — includes `health` and `tasks` routers
- `1/backend/app/tasks.py`: Celery task definitions (`add`, `multiply` — demo/placeholder tasks)
- `1/frontend/src/api/httpClient.ts`: Axios instance, interceptors, `apiEndpoints` path constants
- `1/frontend/src/api/websocket.ts`: `WebSocketManager` class with connect/reconnect/event dispatch

**Routing:**
- `1/frontend/src/router/index.ts`: Vue Router with 5 routes (`/`, `/dashboard`, `/data-management`, `/training/tasks`, `/training/models`)

**Testing:**
- No test files exist in the codebase currently

## Naming Conventions

**Files:**
- Backend Python modules: `snake_case.py` (e.g., `celery_app.py`, `init_db.py`, `health.py`)
- Backend `__init__.py`: Used as package markers; model file `1/backend/app/db/models/__init__.py` also contains all model class definitions
- Frontend Vue SFCs: `PascalCase.vue` (e.g., `MainLayout.vue`, `TheHeader.vue`, `HomeView.vue`)
- Frontend TypeScript: `camelCase.ts` (e.g., `httpClient.ts`, `websocket.ts`)
- Frontend type declarations: `.d.ts` suffix (e.g., `env.d.ts`)

**Directories:**
- Backend: `snake_case/` (e.g., `api/`, `endpoints/`, `core/`, `db/`, `models/`, `crud/`, `schemas/`, `services/`)
- Frontend: `camelCase/` for feature dirs (`training/`), `kebab-case` acceptable, `PascalCase` not used for directories
- Layout-specific: `components/layout/`, `views/training/` — subdirectories group by feature or purpose

**Vue Component Naming:**
- Layout components: `The` prefix (e.g., `TheHeader.vue`, `TheSidebar.vue`)
- View components: `*View` suffix (e.g., `HomeView.vue`, `DashboardView.vue`, `TasksView.vue`, `ModelsView.vue`)
- Layout wrappers: `*Layout` suffix (e.g., `MainLayout.vue`)

## Where to Add New Code

**New Backend API Endpoint:**
1. Create new file: `1/backend/app/api/endpoints/{feature}.py`
2. Define `router = APIRouter()` with route handlers
3. Register in `1/backend/app/api/router.py`: `api_router.include_router({feature}.router, prefix="/{feature}", tags=["{feature}"])`
4. Add Pydantic schemas to `1/backend/app/schemas/` (create `{feature}.py`) or define inline for simple cases
5. Add CRUD operations to `1/backend/app/crud/` (create `{feature}.py`) if database interaction needed

**New Backend Service:**
1. Create new file: `1/backend/app/services/{feature}_service.py`
2. Import from CRUD layer and Celery tasks
3. Import service in API endpoint via `from app.services.{feature}_service import ...`

**New Backend Celery Task:**
1. Add task function to `1/backend/app/tasks.py` with `@shared_task` decorator
2. Task is auto-discovered (Celery `include=["app.tasks"]`)
3. For feature-specific tasks, create `1/backend/app/{feature}_tasks.py` and add to `celery_app.conf.include`

**New Frontend View/Page:**
1. Create Vue SFC: `1/frontend/src/views/{Feature}View.vue` or `1/frontend/src/views/{category}/{Feature}View.vue`
2. Add lazy-loaded route in `1/frontend/src/router/index.ts`:
   ```typescript
   {
     path: '/{feature}',
     name: '{Feature}',
     component: () => import('../views/{Feature}View.vue')
   }
   ```
3. Add navigation item in `1/frontend/src/components/layout/TheSidebar.vue` as `<el-menu-item>` or `<el-sub-menu>`

**New Frontend Component:**
1. Reusable UI component: `1/frontend/src/components/{category}/{ComponentName}.vue`
2. Layout component: `1/frontend/src/components/layout/{ComponentName}.vue`
3. Feature-scoped component: `1/frontend/src/features/{feature}/components/{ComponentName}.vue` (planned pattern, directory empty)

**New Frontend Pinia Store:**
1. Create store file: `1/frontend/src/store/{domain}.ts`
2. Use Composition API pattern (setup function with `ref`/`computed`):
   ```typescript
   import { defineStore } from 'pinia'
   import { ref } from 'vue'
   export const use{Domain}Store = defineStore('{domain}', () => { ... })
   ```

**New Frontend API Module:**
1. Add endpoint path to `apiEndpoints` object in `1/frontend/src/api/httpClient.ts`
2. Create feature-specific API module in `1/frontend/src/api/{feature}.ts` if logic is complex
3. Import `httpClient` from `./httpClient` and call `httpClient.get/post/put/delete`

**New Database Model:**
1. Add model class to `1/backend/app/db/models/__init__.py`
2. Import `Base` from `app.db.session` and inherit from it
3. Define `__tablename__`, columns, relationships
4. Run `python -m app.db.init_db` to create table (or use Alembic migration — `alembic` in requirements but not yet configured)

## Special Directories

**`1/backend/venv/`:**
- Purpose: Python virtual environment
- Generated: Yes (by `python -m venv`)
- Committed: Should not be — should be in `.gitignore`

**`1/frontend/node_modules/`:**
- Purpose: npm package dependencies
- Generated: Yes (by `npm install`)
- Committed: Should not be — should be in `.gitignore`

**`1/.planning/`:**
- Purpose: Project planning documents (roadmap, phase plans, context)
- Generated: No (manually maintained)
- Committed: Yes

**`1/frontend/src/features/`:**
- Purpose: Feature-module organization (planned pattern per ROADMAP)
- Generated: No
- Committed: Yes (currently empty)

**`1/frontend/src/assets/`:**
- Purpose: Static assets (images, fonts, global CSS)
- Generated: No
- Committed: Yes (currently empty)

**`1/backend/app/__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (auto-generated by Python)
- Committed: Should not be — should be in `.gitignore`

---

*Structure analysis: 2026-04-13*
