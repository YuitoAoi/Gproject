# Technology Stack

**Analysis Date:** 2026-05-01

## Languages

**Primary:**
- Python 3.12 - Backend API, Celery workers, data processing tasks (`1/backend/`)
- TypeScript ~5.6.3 - Frontend Vue SPA with strict mode (`1/frontend/`)
- Vue SFC (Single File Components) with `<script setup lang="ts">` - UI templates (`1/frontend/src/**/*.vue`)
- SCSS/SASS 1.81.0 - Component styling with shared variables and mixins (`1/frontend/src/assets/styles/`)

**Secondary:**
- JavaScript (ESNext) - Vite config, build scripts (`1/frontend/vite.config.ts`)
- JSON - Locale files, mock data (`1/frontend/src/locales/langs/`, `1/frontend/src/mock/`)
- SQL - Database schema via SQLAlchemy ORM (`1/backend/app/db/models/__init__.py`)

## Runtime

**Backend Environment:**
- Python 3.12+ runtime
- ASGI server: Uvicorn 0.24.0 (with `[standard]` extras, includes websockets & watchfiles)
- Entry: `python -m uvicorn app.main:app --reload --port 8000`

**Frontend Environment:**
- Node.js >=20.19.0 (v24 confirmed in dev)
- Entry: `npm run dev` → Vite dev server on port 3000 (default) / 3006 (.env override)

**Package Managers:**
- pip + `requirements.txt` (backend) — Lockfile: not present (no `requirements.lock`)
- npm/pnpm >=8.8.0 (frontend) — Lockfile: `package-lock.json` present

## Frameworks

**Core:**
- FastAPI 0.104.1 - Backend REST API framework (`1/backend/app/main.py`)
- Vue 3.5.21 - Frontend SPA framework with Composition API (`1/frontend/src/main.ts`)
- Vue Router 4.5.1 - Client-side routing, hash history mode (`1/frontend/src/router/index.ts`)
- Pinia 3.0.3 - State management with Composition API (`1/frontend/src/store/`)
- Celery 5.3.4 - Distributed task queue (`1/backend/app/core/celery_app.py`)
- Element Plus 2.11.2 - Vue 3 UI component library (`1/frontend/src/main.ts`)
- TailwindCSS 4.1.14 - Utility-first CSS framework (`1/frontend/src/assets/styles/core/tailwind.css`)

**Build/Dev:**
- Vite 7.1.5 - Frontend build tool, dev server, HMR (`1/frontend/vite.config.ts`)
- Uvicorn 0.24.0 - ASGI server (backend dev)
- vue-tsc ~2.1.6 - Vue TypeScript type checking (build step: `vue-tsc --noEmit`)
- terser 5.36.0 - JavaScript minification (production build)
- vite-plugin-compression 0.5.1 - Gzip compression of build assets
- vue-devtools 7.7.6 - Browser DevTools integration (`vite-plugin-vue-devtools`)
- unplugin-auto-import 20.2.0 - Auto-import Vue/Pinia/Router/Element Plus APIs
- unplugin-vue-components 29.1.0 - Auto-import Element Plus components

**Testing:**
- No test framework configured for either backend or frontend
- No test files detected (no `*.test.*`, `*.spec.*`, `tests/`, `__tests__/`)

## Key Dependencies

### Backend Critical

| Package | Version | Purpose |
|---------|---------|---------|
| pydantic | 2.5.0 | Request/response data validation |
| pydantic-settings | 2.1.0 | Settings management with `.env` file support |
| sqlalchemy | 2.0.23 | ORM for MySQL |
| alembic | 1.12.1 | Database migrations (installed, not configured) |
| pymysql | 1.1.0 | MySQL driver (Windows-compatible, replaces mysqlclient) |
| redis | 5.0.1 | Python Redis client (Celery broker + PubSub) |
| celery | 5.3.4 | Async distributed task queue |
| websockets | 12.0 | WebSocket protocol support |
| python-multipart | 0.0.6 | File upload handling (multipart/form-data) |
| cryptography | 41.0.7 | Cryptographic primitives |
| python-dotenv | 1.0.0 | `.env` file loading |
| pynvml | 11.5.0 | NVIDIA GPU monitoring (planned for GPU management) |
| httpx | 0.25.2 | Async HTTP client |

### Frontend Critical

| Package | Version | Purpose |
|---------|---------|---------|
| axios | 1.12.2 | HTTP client with interceptors |
| pinia | 3.0.3 | State management |
| pinia-plugin-persistedstate | 4.3.0 | localStorage persistence for Pinia stores |
| vue-i18n | 9.14.0 | Internationalization (zh/en) |
| @element-plus/icons-vue | 2.3.2 | Icon set for Element Plus |
| @iconify/vue | 5.0.0 | Additional icon library |
| echarts | 6.0.0 | Data visualization charts |
| @vueuse/core | 13.9.0 | Vue Composition API utilities |
| tailwindcss | 4.1.14 | Utility-first CSS (with @tailwindcss/vite plugin) |
| sass | 1.81.0 | SCSS preprocessor |
| nprogress | 0.2.0 | Page loading progress bar |
| mitt | 3.0.1 | Event emitter/bus |
| crypto-js | 4.2.0 | Client-side cryptographic (lock screen) |
| xlsx | 0.18.5 | Excel file read/write |
| file-saver | 2.0.5 | Client-side file download |

### Frontend Dev Tools

| Package | Version | Purpose |
|---------|---------|---------|
| eslint | 9.9.1 | JavaScript/TypeScript linter |
| prettier | 3.5.3 | Code formatter |
| stylelint | 16.20.0 | SCSS/CSS linter |
| husky | 9.1.5 | Git hooks manager |
| lint-staged | 15.5.2 | Pre-commit linting of staged files |
| commitizen + cz-git | 4.3.0 / 1.11.1 | Conventional commit messages |
| @commitlint | 19.4.1 | Commit message linting |
| typescript-eslint | 8.9.0 | TypeScript ESLint integration |

## Configuration

**Backend Environment:**
- Configured via `pydantic-settings` with `.env` file support (`1/backend/app/core/config.py`)
- Settings class provides typed defaults for all config values
- `.env.example` at `1/backend/.env.example` documents required variables
- `.env` file at `1/backend/.env` (present, contains actual credentials)

**Backend Config Variables:**
| Variable | Default | Purpose |
|----------|---------|---------|
| `PROJECT_NAME` | `LLaMA-Factory Workstation` | API title |
| `VERSION` | `1.0.0` | API version |
| `API_V1_STR` | `/api/v1` | API URL prefix |
| `DATABASE_URL` | `mysql+pymysql://root:password@localhost:3306/llama_factory` | MySQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | General Redis connection |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Celery result backend |
| `BACKEND_CORS_ORIGINS` | `['http://localhost:3000', 'http://localhost:5173']` | Allowed CORS origins |

**Frontend Environment:**
- Vite env vars via `import.meta.env` and `loadEnv()` in Vite config
- `.env` — Common settings (version, port, access mode)
- `.env.development` — Dev-specific (API URLs, port 3000)
- `.env.production` — Production (mock API endpoint for dev/demo)

**Frontend Config Variables:**
| Variable | Dev Value | Prod Value | Purpose |
|----------|-----------|------------|---------|
| `VITE_VERSION` | `3.0.2` | (same) | App version |
| `VITE_PORT` | `3000` | `3006` | Dev server port |
| `VITE_BASE_URL` | `/` | `/` | Base path for deployment |
| `VITE_API_URL` | `http://localhost:8000/api/v1` | `https://m1.apifoxmock.com/...` | Backend API base URL |
| `VITE_API_PROXY_URL` | `http://localhost:8000` | (not set) | Vite dev proxy target |
| `VITE_WS_URL` | `ws://localhost:8000` | (not set) | WebSocket endpoint |
| `VITE_ACCESS_MODE` | `frontend` | — | Auth mode (frontend/backend) |
| `VITE_LOCK_ENCRYPT_KEY` | `s3cur3k3y4adpro` | — | Lock screen encryption key |

**Build Configuration:**
- `1/frontend/vite.config.ts` — Vite 7 config with plugins, aliases, proxy, build options
- `1/frontend/tsconfig.json` — TypeScript config: `target: "esnext"`, `module: "esnext"`, strict mode, path aliases
- `1/frontend/tsconfig.node.json` — Node-specific TS config (for Vite config itself)
- `1/frontend/eslint.config.js` — Flat ESLint config (ESLint 9)
- `1/frontend/.prettierrc` — Prettier config (detected via scripts)
- No `alembic.ini` — Alembic dependency present but not yet configured
- No `docker-compose.yml`, `Dockerfile`, or CI config detected

**Path Aliases (frontend):**
| Alias | Path |
|-------|------|
| `@/*` | `src/*` |
| `@views/*` | `src/views/*` |
| `@imgs/*` | `src/assets/images/*` |
| `@icons/*` | `src/assets/icons/*` |
| `@utils/*` | `src/utils/*` |
| `@stores/*` | `src/store/*` |
| `@plugins/*` | `src/plugins/*` |
| `@styles/*` | `src/assets/styles/*` |

## Platform Requirements

**Development:**
- Python 3.12+ with pip
- Node.js >=20.19.0 with pnpm >=8.8.0 (or npm)
- MySQL server (local or remote, database `llama_factory`)
- Redis server (local or remote, databases 0/1/2)
- NVIDIA GPU with drivers (for LLM inference/training via pynvml)

**Production:**
- Same runtime requirements
- Python environment with all `requirements.txt` dependencies
- Vite build output: `1/frontend/dist/` (static files)
- ASGI server (uvicorn) for FastAPI
- Celery worker process: `celery -A app.core.celery_app worker --loglevel=info --pool=solo`
- Static file serving for Vue SPA build output (or Vite preview)
- MySQL database with tables created via `python -m app.db.init_db`
- Redis for Celery broker/result backend

---

*Stack analysis: 2026-05-01*
