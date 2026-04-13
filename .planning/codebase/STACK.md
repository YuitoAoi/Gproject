# Technology Stack

**Analysis Date:** 2026-04-13

## Languages

**Primary:**
- Python 3.12 - Backend API, models, services, Celery tasks (`1/backend/`)
- TypeScript - Frontend Vue SPA (`1/frontend/`)

**Secondary:**
- Vue SFC (Single File Components) - UI templates and styles (`1/frontend/src/**/*.vue`)
- SQL - Database schema via SQLAlchemy ORM (`1/backend/app/db/models/`)

## Runtime

**Environment:**
- Python 3.12 (backend)
- Node.js v24.14.1 (frontend dev/build)

**Package Manager:**
- pip + `requirements.txt` (backend) - Lockfile: not present (no `requirements.lock`)
- npm + `package-lock.json` (frontend) - Lockfile: present

## Frameworks

**Core:**
- FastAPI 0.104.1 - Backend REST API framework (`1/backend/app/main.py`)
- Vue 3.3.8 - Frontend SPA framework (`1/frontend/src/main.ts`)
- Vue Router 4.2.5 - Client-side routing (`1/frontend/src/router/index.ts`)
- Pinia 2.1.7 - State management (`1/frontend/src/store/`)

**Task Queue:**
- Celery 5.3.4 - Distributed task queue (`1/backend/app/core/celery_app.py`)
- Redis 5.0.1 - Celery broker and result backend

**ORM / Database:**
- SQLAlchemy 2.0.23 - ORM for MySQL (`1/backend/app/db/session.py`)
- Alembic 1.12.1 - Database migrations (installed, no `alembic.ini` yet)
- PyMySQL 1.1.0 - MySQL driver

**UI Library:**
- Element Plus 2.4.2 - Vue 3 UI component library (`1/frontend/src/main.ts`)
- @element-plus/icons-vue 2.1.0 - Icon set

**Build/Dev:**
- Vite 4.5.0 - Frontend build tool and dev server (`1/frontend/vite.config.ts`)
- TypeScript 5.2.2 - Type checking (`1/frontend/tsconfig.json`)
- vue-tsc 1.8.22 - Vue TypeScript type checking
- @vitejs/plugin-vue 4.5.0 - Vue SFC support for Vite

**HTTP Client:**
- httpx 0.25.2 - Async HTTP client (backend)
- axios 1.6.0 - Frontend HTTP client (`1/frontend/src/api/httpClient.ts`)

## Key Dependencies

**Critical:**
- Pydantic 2.5.0 + pydantic-settings 2.1.0 - Data validation and settings management (`1/backend/app/core/config.py`)
- websockets 12.0 - WebSocket protocol support (backend)
- pynvml 11.5.0 - NVIDIA GPU monitoring library (backend, for future GPU management features)
- cryptography 41.0.7 - Cryptographic primitives (backend)
- python-multipart 0.0.6 - File upload handling (backend)
- python-dotenv 1.0.0 - `.env` file loading (`1/backend/app/core/config.py`)

**Infrastructure:**
- uvicorn 0.24.0 (with `[standard]` extras) - ASGI server (`1/backend/app/main.py`)

## Configuration

**Environment:**
- Backend uses `pydantic-settings` with `.env` file support (`1/backend/app/core/config.py`)
- Frontend uses `import.meta.env` for Vite env vars (e.g., `VITE_API_BASE_URL`, `VITE_WS_URL`)
- Default CORS origins: `http://localhost:3000`, `http://localhost:5173`
- Default database URL: `mysql+pymysql://root:password@localhost:3306/llama_factory`
- Default Redis URL: `redis://localhost:6379/0`
- Celery broker: `redis://localhost:6379/1`, result backend: `redis://localhost:6379/2`

**Build:**
- `1/frontend/vite.config.ts` - Vite config with dev proxy (`/api` → `http://localhost:8000`)
- `1/frontend/tsconfig.json` - TypeScript config (ES2020 target, strict mode, `@/*` path alias)
- `1/frontend/tsconfig.node.json` - Node-specific TS config for Vite
- No `alembic.ini` yet (Alembic dependency present but not configured)

**Path Aliases:**
- Frontend: `@/*` → `src/*` (defined in `1/frontend/tsconfig.json`)

## Platform Requirements

**Development:**
- Python 3.12+ runtime
- Node.js 18+ (v24 confirmed)
- MySQL server (local or remote)
- Redis server (local or remote)
- Vite dev server runs on port 3000
- FastAPI/Uvicorn runs on port 8000

**Production:**
- ASGI server (uvicorn) for FastAPI
- Static file serving for Vue SPA build output
- MySQL database
- Redis for Celery broker/result backend
- Celery worker process
- NVIDIA GPU with drivers (for LLM inference, pynvml dependency)

---

*Stack analysis: 2026-04-13*