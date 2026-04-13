# External Integrations

**Analysis Date:** 2026-04-13

## APIs & External Services

**LLM Training / Inference (Planned):**
- LLaMA-Factory - Local LLM fine-tuning framework (the core purpose of the application)
  - Integration: Not yet implemented; `1/backend/app/services/inference_service.py` is planned
  - The `pynvml` dependency (NVIDIA management library) indicates GPU interaction for model loading/inference

**No external API integrations currently active.** The backend has `httpx` installed (`1/backend/requirements.txt`) but no service modules exist yet in `1/backend/app/services/`.

## Data Storage

**Databases:**
- MySQL (via PyMySQL driver)
  - Connection: `DATABASE_URL` env var (default: `mysql+pymysql://root:password@localhost:3306/llama_factory`)
  - ORM: SQLAlchemy 2.0 with declarative base (`1/backend/app/db/session.py`)
  - Migrations: Alembic 1.12.1 (installed but not yet configured - no `alembic.ini`)
  - Schema init: `1/backend/app/db/init_db.py` uses `Base.metadata.create_all()`

**Database Models** (defined in `1/backend/app/db/models/__init__.py`):
- `User` - Authentication and ownership
- `Dataset` - Dataset metadata and file references
- `TrainingTask` - Training job configuration and status
- `TrainedModel` - Fine-tuned model metadata and status (`UNLOADED` | `LOADING` | `ACTIVE`)

**File Storage:**
- Local filesystem only (referenced via `file_path`, `model_path`, `log_path`, `output_path` columns in models)
- No cloud storage integration (S3, GCS, etc.)

**Caching / Message Queue:**
- Redis (multiple databases)
  - DB 0: General Redis (default)
  - DB 1: Celery broker
  - DB 2: Celery result backend

## Authentication & Identity

**Auth Provider:**
- Custom implementation (planned, not yet built)
  - `1/frontend/src/api/httpClient.ts` includes auth token handling:
    - Reads `auth_token` from `localStorage` on every request
    - Sets `Authorization: Bearer <token>` header
    - On 401 response: removes token and redirects to `/`
  - `User` model in `1/backend/app/db/models/__init__.py` has `hashed_password` and `role` fields
  - No auth endpoints implemented yet (no login/register routes)

## Monitoring & Observability

**Error Tracking:**
- None configured

**Logs:**
- Console logging (Python `print` in `1/backend/app/db/init_db.py`)
- `console.log`/`console.error` in frontend WebSocket manager (`1/frontend/src/api/websocket.ts`)
- Celery worker logging via `--loglevel=info`

**GPU Monitoring:**
- `pynvml` library installed for NVIDIA GPU status queries (not yet used in any service)

## CI/CD & Deployment

**Hosting:**
- Local development only (no deployment config found)
- Vite dev server with proxy for frontend (`1/frontend/vite.config.ts`)
- Uvicorn for backend (`1/backend/app/main.py`)

**CI Pipeline:**
- None configured

**Container:**
- No Dockerfile or docker-compose found

## Environment Configuration

**Required env vars (backend):**
- `DATABASE_URL` - MySQL connection string (default in `1/backend/app/core/config.py`)
- `REDIS_URL` - Redis connection (default: `redis://localhost:6379/0`)
- `CELERY_BROKER_URL` - Celery broker (default: `redis://localhost:6379/1`)
- `CELERY_RESULT_BACKEND` - Celery result backend (default: `redis://localhost:6379/2`)
- `BACKEND_CORS_ORIGINS` - Allowed CORS origins (JSON list)
- `.env` file supported via `python-dotenv` (file not present yet)

**Required env vars (frontend):**
- `VITE_API_BASE_URL` - Backend API base URL (default: `http://localhost:8000/api/v1`)
- `VITE_WS_URL` - WebSocket server URL (default: current `window.location.host`)

**Secrets location:**
- `.env` file expected at `1/backend/` (not yet created)
- Auth tokens stored in browser `localStorage`

## Webhooks & Callbacks

**Incoming:**
- None implemented
- WebSocket endpoint at `/ws` referenced in frontend (`1/frontend/src/api/websocket.ts`) but not implemented on backend

**Outgoing:**
- None implemented

## Real-time Communication

**WebSocket (Frontend client ready, backend not yet):**
- `1/frontend/src/api/websocket.ts` - Full WebSocket manager with:
  - Auto-reconnect (5s interval)
  - Heartbeat (ping every 30s)
  - Event dispatch system (event-based listener pattern)
  - Pre-registered handlers for `system-notification`, `model-activated`, `model-deactivated`
  - URL construction: `ws://<host>/ws` or `wss://<host>/ws`

## API Endpoints (Current)

**Health:**
- `GET /api/v1/health/` - Health check (`1/backend/app/api/endpoints/health.py`)

**Tasks (Celery demo):**
- `POST /api/v1/tasks/add` - Create addition task (`1/backend/app/api/endpoints/tasks.py`)
- `POST /api/v1/tasks/multiply` - Create multiplication task
- `GET /api/v1/tasks/{task_id}` - Get task status

**Planned endpoints** (from `1/frontend/src/api/httpClient.ts`):
- `/datasets` - Dataset management
- `/training/tasks` - Training task management
- `/models` - Model management
- `/inference/models` - Inference model management
- `/inference/chat-stream` - Streaming chat inference

---

*Integration audit: 2026-04-13*