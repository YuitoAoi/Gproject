# LLaMA-Factory Workstation

Vue 3 + FastAPI monorepo for LLM fine-tuning. Plan phases are in `.planning/`.

## Commands

```bash
# Frontend (port 3000, proxies /api to backend)
cd frontend && npm run dev
cd frontend && npm run build

# Backend
cd backend && python -m uvicorn app.main:app --reload --port 8000

# Celery worker
cd backend && celery -A app.core.celery_app worker --loglevel=info
```

## Architecture

- **API prefix**: All routes under `/api/v1`
- **Vite proxy**: `/api/*` → `http://localhost:8000`
- **Database**: MySQL (config in `backend/app/core/config.py`)
- **Task queue**: Celery + Redis
- **Models base**: `backend/app/db/models/__init__.py` uses SQLAlchemy declarative

## Key Files

| Path | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app entry |
| `backend/app/core/celery_app.py` | Celery config |
| `backend/app/tasks.py` | Shared tasks |
| `backend/app/api/router.py` | API route aggregation |
| `frontend/src/router/index.ts` | Vue Router config |
| `frontend/src/layouts/MainLayout.vue` | App shell (header/sidebar) |

## Database Models

- `User`, `Dataset`, `TrainingTask`, `TrainedModel`
- `TrainedModel.status`: `UNLOADED` | `LOADING` | `ACTIVE`

## Planned But Missing

- `backend/app/services/inference_service.py` (Phase 5)
- `frontend/src/views/DataManagementView.vue` (Phase 2)
- `frontend/src/views/training/TasksView.vue` (Phase 3)
- `frontend/src/views/training/ModelsView.vue` (Phase 3)
- `frontend/src/api/` (empty - needs HTTP client module)
