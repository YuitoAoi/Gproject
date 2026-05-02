# Codebase Concerns

**Analysis Date:** 2026-05-01

---

## Security Considerations

### Hardcoded Credentials

**Database password hardcoded:**
- Files: `1/backend/app/core/config.py` (line 10), `1/backend/.env.example` (line 1)
- Risk: Default database password `root:password` is committed to source code. Anyone with repo access can connect to the database using these credentials.
- Current mitigation: `.env` file exists (not read per policy) which can override the default, but the default remains in code.
- Recommendations: Remove hardcoded defaults and require explicit configuration. Use only `.env` without fallback credentials in source.

**Admin login hardcoded:**
- Files: `1/backend/app/api/endpoints/auth.py` (line 17)
- Risk: Login endpoint contains hardcoded credentials `admin/admin123`. This is a complete bypass of any authentication system.
- Current mitigation: None. The `isLogin` defaults to `true` in `1/frontend/src/store/modules/user.ts` (line 56), so the login endpoint may not even be called in normal flow.
- Recommendations: Replace with database-backed authentication using hashed passwords. Remove hardcoded credentials immediately.

**Dev token hardcoded in frontend:**
- Files: `1/frontend/src/store/modules/user.ts` (lines 73–75)
- Risk: `accessToken: 'dev-token'` and `refreshToken: 'dev-refresh-token'` are hardcoded defaults. The `isLogin` ref defaults to `true`, meaning the entire auth guard is bypassed in development mode.
- Recommendations: Default `isLogin` to `false`; tokens should start empty until a real login occurs.

### Missing Authentication Enforcement

**Auth bypass via default login state:**
- Files: `1/frontend/src/store/modules/user.ts` (line 56)
- Risk: `isLogin = ref(true)` means all pages are accessible without any authentication check.
- Recommendations: Set to `false` and implement real login flow.

**Backend endpoints unprotected:**
- Files: `1/backend/app/api/endpoints/datasets.py`, `1/backend/app/api/endpoints/users.py`, `1/backend/app/api/endpoints/tasks.py`
- Risk: No authentication middleware or dependency injection on any API endpoint. Any unauthenticated request can access, modify, or delete data.
- Recommendations: Implement JWT-based auth middleware. Use FastAPI `Depends(get_current_user)` on all protected routes.

### Exposed Configuration

**`.env.example` exposes infrastructure layout:**
- Files: `1/backend/.env.example`
- Risk: Lists all required environment variables (database, Redis, Celery broker URLs) with default values. While not secrets per se, it reveals the internal infrastructure topology.
- Recommendations: Remove default values from `.env.example`, document only the variable names needed.

---

## Tech Debt

### Architectural Violations: Celery App Ignores Central Config

- Issue: `1/backend/app/core/celery_app.py` (lines 4–6) hardcodes Redis broker/backend URLs directly instead of using `settings` from `config.py`. The `config.py` defines `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` but they are never consumed by the Celery app.
- Files: `1/backend/app/core/celery_app.py`
- Impact: Changing Redis configuration requires editing two files. The config system is half-implemented.
- Fix approach: Replace hardcoded strings with `settings.CELERY_BROKER_URL` and `settings.CELERY_RESULT_BACKEND`.

### Architectural Violations: Celery Tasks Hardcode Redis

- Issue: `dataset_tasks.py` bypasses the central Redis config and hardcodes `REDIS_HOST = 'localhost'`, `REDIS_PORT = 6379`, `REDIS_DB = 0`.
- Files: `1/backend/app/tasks/dataset_tasks.py` (lines 18–20)
- Impact: Task progress publishing will fail in any non-local deployment. This is completely invisible to the config system.
- Fix approach: Import `settings` from `config.py` and use `REDIS_URL` to connect.

### Frontend HTTP Client Inconsistency

- Issue: `1/frontend/src/api/dataset.ts` mixes two different HTTP clients. Lines 67, 79, 101, 163 use raw `axios` directly, while lines 176, 182, 188, 195 use the wrapped `request` from `@/utils/http`.
- Files: `1/frontend/src/api/dataset.ts`
- Impact: Raw `axios` calls bypass auth token injection (interceptor in `@/utils/http`), bypass error handling, bypass response unwrapping. The `initiateUpload`, `uploadChunk`, `completeUpload`, and `getDatasets` functions will not include auth headers and will not handle 401 errors.
- Fix approach: Replace all raw `axios` calls with the wrapped `request` client. Ensure all API modules consistently use `@/utils/http`.

### Mock API Path Mismatch

- Issue: `1/frontend/src/api/data-manage.ts` defines mock endpoints at `/api/dataset/list`, `/api/dataset/detail/{id}`, `/api/dataset/delete/{id}`. The actual backend routes are at `/api/v1/datasets`, `/api/v1/datasets/{id}`. The mock data functions (`fetchGetDatasetListMock`, etc.) are completely disconnected from the real API.
- Files: `1/frontend/src/api/data-manage.ts`
- Impact: Components using these mock functions will not work when switched to the real backend without URL changes.
- Fix approach: Align mock endpoint URLs with real backend routes (`/api/v1/datasets*`). Add a clear `// TODO: switch to real API` marker.

### Login API Sends Params as Query String Instead of Body

- Issue: `1/frontend/src/api/auth.ts` (line 6) calls `request.post({ url: '/auth/login', params })`. The wrapped HTTP client treats `params` as POST body for POST/PUT methods (see `1/frontend/src/utils/http/index.ts` lines 168–174), but the backend `auth.py` expects a JSON body via Pydantic `LoginRequest` model (`userName`, `password` as body fields).
- Files: `1/frontend/src/api/auth.ts` (line 6), `1/backend/app/api/endpoints/auth.py` (lines 8–10)
- Impact: Login may fail because the backend expects `{ "userName": "...", "password": "..." }` in the body. The frontend `auth.ts` also lacks a catch for network errors and has a fallback that returns mock data (lines 13–21), masking the failure.
- Fix approach: Change `params` to `data` in the frontend POST call. Remove the error-silencing fallback or make it development-mode only.

### Fragile Path Resolution

- Issue: `1/backend/app/api/endpoints/datasets.py` (line 26) uses 6 levels of `os.path.dirname()` to compute `PROJECT_ROOT`. `1/backend/app/tasks/dataset_tasks.py` (line 13) uses 5 levels similarly.
- Files: `1/backend/app/api/endpoints/datasets.py`, `1/backend/app/tasks/dataset_tasks.py`
- Impact: If any intermediate directory structure changes, both path calculations silently break. This is extremely fragile and non-portable.
- Fix approach: Use a configuration-based root path (e.g., `settings.DATA_DIR`) or compute from a known anchor like `__package__`.

---

## Incomplete Code

### Empty Service Layer

- Issue: `1/backend/app/services/__init__.py` is completely empty (0 bytes). The services layer is expected to contain business logic orchestration, but no code exists.
- Files: `1/backend/app/services/__init__.py`
- Impact: Business logic gets pushed into API endpoint handlers and Celery tasks, violating separation of concerns.
- Fix approach: Extract business logic from `dataset_tasks.py` (like data cleaning, format conversion) into service classes. Create `dataset_service.py`, `training_service.py`, etc.

### Missing CRUD Operations for Core Models

- Issue: `1/backend/app/crud/` only has `dataset.py` implemented. Models `User`, `TrainingTask`, `TrainedModel`, and `Tag` have no CRUD operations.
- Files: `1/backend/app/crud/__init__.py` (empty), `1/backend/app/crud/dataset.py`
- Impact: API endpoints for users, training, and models cannot be built without CRUD functions.
- Fix approach: Create `user.py`, `training_task.py`, `trained_model.py`, `tag.py` in the CRUD directory.

### Missing Schemas for Non-Dataset Models

- Issue: `1/backend/app/schemas/` only has `dataset.py` implemented. No Pydantic schemas exist for `User`, `TrainingTask`, `TrainedModel`, `Tag`, or auth-related models.
- Files: `1/backend/app/schemas/__init__.py` (empty), `1/backend/app/schemas/dataset.py`
- Impact: API endpoints define inline Pydantic models (e.g., `HealthResponse` in `health.py`, `LoginRequest` in `auth.py`), violating the schema layer convention.
- Fix approach: Move all request/response models from endpoint files into `schemas/`. Create `user.py`, `training.py`, `auth.py` schemas.

### Half-Implemented Data Management Frontend

- Issue: `1/frontend/src/views/data-management/index.vue` is a placeholder page ("数据集上传、清洗、格式转换等功能即将上线"). The actual dataset-hub and data-processing sub-views exist with full mock UI, but the parent placeholder is still active.
- Files: `1/frontend/src/views/data-management/index.vue`
- Impact: Users navigating to `/data-management` see a placeholder. Real content is only visible via direct sub-routes.
- Fix approach: Replace the placeholder with a redirect to `dataset-hub` or integrate the welcome content into the routing system.

### Router Modules Reference Non-Existent Views

- Issue: Several router module files define routes to view paths that may not exist or are from the art-design-pro template:
  - `1/frontend/src/router/modules/dashboard.ts` routes to `/dashboard/console`, `/dashboard/analysis`, `/dashboard/ecommerce` — these views are not part of the LLMOps workspace and may not exist
  - `1/frontend/src/router/modules/article.ts`, `examples.ts`, `help.ts`, `safeguard.ts`, `template.ts`, `widgets.ts` — all from the template, unused in the workbench
- Files: `1/frontend/src/router/modules/dashboard.ts`
- Impact: These modules are imported via the index barrel and will cause 404 component resolution errors if the views don't exist.
- Fix approach: Remove unused router modules from `1/frontend/src/router/modules/index.ts`. Keep only `workbench.ts`.

---

## Redundant Code

### Leftover Test Files in Backend Root

- Issue: Four ad-hoc test scripts with hardcoded absolute paths live in the backend root:
  - `1/backend/test_mysql.py` — uses `sys.path.insert(0, 'D:/files/Gproject/1/backend')`
  - `1/backend/test_celery.py` — starts Celery worker via subprocess, hardcoded path
  - `1/backend/test_celery_direct.py` — hardcoded path
  - `1/backend/test_celery_tasks.py` — hardcoded path
- Files: `1/backend/test_mysql.py`, `1/backend/test_celery.py`, `1/backend/test_celery_direct.py`, `1/backend/test_celery_tasks.py`
- Impact: These are development-only scripts not meant for production. The hardcoded paths make them non-portable. They clutter the backend root.
- Fix approach: Move to a `tests/` directory with proper test framework (pytest). Remove hardcoded paths.

### Scratch File in Project Root

- Issue: `111.txt` contains terminal commands for starting dev servers. This is a personal scratch file.
- Files: `111.txt`
- Impact: Not a code concern per se, but indicates informal development practices. Should not be committed.
- Fix approach: Delete and add to `.gitignore` if necessary.

### Reference Project Copy

- Issue: `art-design-pro-3.0.2/` is a complete copy of the Art Design Pro reference project (108+ files including `.env`, `.env.development`, `.env.production`, `.prettierrc`, etc.). This is a duplicate template living alongside the actual project.
- Files: `art-design-pro-3.0.2/` (entire directory)
- Impact: Doubles the repo size. Contains its own `.env` files, package.json, and dependencies that may conflict or confuse. The `front需求.md` explicitly references it as a prototype source.
- Fix approach: Remove from the repo if it's only for reference. If it must stay, move to a `reference/` or `templates/` directory and add a clear README explaining its purpose.

### Test Data File

- Issue: `datafile/datasets/test1.json` is a leftover test file.
- Files: `datafile/datasets/test1.json`
- Impact: May interfere with dataset listing or be mistaken for real data.
- Fix approach: Remove or move to a `tests/fixtures/` directory.

---

## Fragile Areas

### Database Session Not Used with Dependency Injection

- Issue: `1/backend/app/db/session.py` defines a `get_db()` generator for FastAPI `Depends` injection, but some endpoints bypass it. Celery tasks create their own sessions via `SessionLocal()` directly.
- Files: `1/backend/app/db/session.py`, `1/backend/app/tasks/dataset_tasks.py` (lines 69, 123, 234)
- Impact: Consistent error handling and session lifecycle management are not guaranteed. If a session is not properly closed (though tasks do close them in `finally`), connection pool exhaustion can occur.
- Fix approach: Consider a context manager for Celery tasks. Ensure `db.close()` is always in a `finally` block (currently done correctly but fragile).

### Response Model Inconsistency

- Issue: `1/backend/app/api/endpoints/datasets.py` line 79 uses `response_model=list[DatasetResponse]` but individual item endpoints (lines 86, 109) also use `response_model=DatasetResponse`. The list endpoint serializes correctly, but nested relationships (like `owner_name`, `tag_name`) are not included in `DatasetResponse` — these would trigger lazy loading and potential N+1 queries.
- Files: `1/backend/app/api/endpoints/datasets.py`
- Impact: If the frontend displays dataset owner or tag names, every row in the list triggers a separate database query.
- Fix approach: Add `joinedload` or `selectinload` to CRUD queries. Include relationship fields in response schemas.

### No Database Indexes on Foreign Keys

- Issue: Foreign key columns (`owner_id`, `dataset_id`, `tag_id`, `training_task_id`) in models have `ForeignKey()` but not `index=True`.
- Files: `1/backend/app/db/models/__init__.py` (lines 61–62, 103–104, 127–128)
- Impact: JOIN queries on foreign keys will perform full table scans as datasets grow.
- Fix approach: Add `index=True` to all foreign key columns.

### Incomplete Error Handling on File Operations

- Issue: `1/backend/app/api/endpoints/datasets.py` (lines 102–103) deletes a file with `os.remove()` without try/except. If the file is missing or locked, the endpoint returns 500.
- Files: `1/backend/app/api/endpoints/datasets.py`
- Impact: File deletion failures crash the API response instead of returning a graceful error.
- Fix approach: Wrap `os.remove()` in try/except and log a warning if the file doesn't exist.

### taskStore Full Map Re-creation on Every Update

- Issue: `1/frontend/src/store/modules/task.ts` (lines 59, 73, 85, 97) uses `tasks.value = new Map(tasks.value)` to trigger Vue reactivity on every update. This is O(n) per update and creates garbage collection pressure.
- Files: `1/frontend/src/store/modules/task.ts`
- Impact: Under high task load (frequent WebSocket progress updates), this causes unnecessary CPU churn.
- Fix approach: Use a `reactive` Map or a flat `ref<Record<string, TaskProgress>>` object that Vue can track natively.

---

## Known Bugs

### Dataset List Pagination Fabrication

- Bug: `1/frontend/src/api/dataset.ts` (lines 161–173) `getDatasets()` receives a raw array from the backend but fabricates pagination metadata: `current: 1`, `size: limit`, `total: records.length`. The backend returns all records matching skip/limit, but the frontend always reports `current: 1`.
- Files: `1/frontend/src/api/dataset.ts`
- Symptoms: Pagination controls show incorrect page numbers. If the user is on page 3 and the API returns 100 records, the UI still shows "page 1 of 1."
- Trigger: Calling `getDatasets({ skip: 100, limit: 100 })`.
- Workaround: The backend needs to return total count in the response. Add a `total` field to the list response or a `Content-Range` header.

### Dataset Complete Upload Returns dataset_id=0

- Bug: `1/backend/app/api/endpoints/datasets.py` (line 73) hardcodes `dataset_id=0` in the `UploadCompleteResponse`. The real dataset ID is only known after the Celery task completes.
- Files: `1/backend/app/api/endpoints/datasets.py`
- Symptoms: Frontend receives `dataset_id: 0` and cannot track the newly created dataset.
- Trigger: Calling the complete-upload endpoint.
- Workaround: Poll the task result to get the real `dataset_id` after the task finishes.

### Empty `ensure_upload_dir` No-Op

- Bug: `1/backend/app/api/endpoints/datasets.py` (line 30–31) defines `ensure_upload_dir()` using `UPLOAD_DIR`. But `UPLOAD_DIR` points to `datafile/chunks/` while `dataset_tasks.py` creates `datafile/datasets/`. The upload directory is created correctly, but if the `datafile/` parent doesn't exist, the API endpoints will fail silently because `os.makedirs(exist_ok=True)` does create it — but the task also calls `ensure_dirs()` redundantly.
- Files: `1/backend/app/api/endpoints/datasets.py`, `1/backend/app/tasks/dataset_tasks.py`
- Impact: Duplicate directory creation logic. Not a functional bug but adds confusion.
- Fix approach: Centralize directory initialization in a single module (e.g., a startup event handler).

---

## Performance Bottlenecks

### Full File Read into Memory

- Problem: `1/backend/app/tasks/dataset_tasks.py` reads entire CSV/JSON files into memory for cleaning and conversion. Lines 138 (`list(csv.DictReader(f))`), 182 (`json.load(f)`), 250, 313.
- Files: `1/backend/app/tasks/dataset_tasks.py`
- Cause: No streaming/chunked processing. A 100MB JSON file consumes 100MB+ of worker memory.
- Improvement path: Implement streaming/chunked processing for large files. Use `ijson` for JSON streaming. Process CSV in chunks using pandas with `chunksize`.

### Inefficient Deduplication

- Problem: CSV dedup (lines 146–159) creates a `tuple(sorted(row.items()))` for every row, then checks against a growing `set()`. Hash computation is O(k log k) per row where k = number of columns.
- Files: `1/backend/app/tasks/dataset_tasks.py` (lines 147–151)
- Cause: Sorting row items for every row just to create a hashable key.
- Improvement path: Use `json.dumps(row, sort_keys=True)` which is more efficient, or hash only the values that matter.

### No Database Connection Pooling in Celery Tasks

- Problem: Each Celery task creates a new `SessionLocal()` directly (lines 69, 123, 234). While `SessionLocal` does use connection pooling (configured with `pool_size=5` in `session.py`), the tasks bypass the `get_db` generator pattern.
- Files: `1/backend/app/tasks/dataset_tasks.py`
- Cause: Celery tasks are not FastAPI endpoints, so dependency injection doesn't apply.
- Improvement path: Create a context manager for Celery task database sessions that ensures proper cleanup.

---

## Dependencies at Risk

### sqlalchemy `declarative_base` Deprecation

- Risk: `1/backend/app/db/session.py` (line 16) uses `sqlalchemy.ext.declarative.declarative_base` which was the legacy API. For SQLAlchemy 2.0+, the recommended approach is `sqlalchemy.orm.DeclarativeBase`.
- Impact: Current code works but future SQLAlchemy versions may deprecate or remove this API.
- Migration plan: Switch to `from sqlalchemy.orm import DeclarativeBase` and update models to use the new-style declarative mapping.

### pynvml Not Used

- Risk: `pynvml==11.5.0` is in `1/backend/requirements.txt` but has no import anywhere in the codebase.
- Impact: Unnecessary dependency that increases install time and potential security surface.
- Migration plan: Remove from requirements until GPU monitoring is implemented. Re-add when needed with a proper wrapper.

---

## Test Coverage Gaps

### No Automated Tests

- What's not tested: Entire codebase has zero automated tests. No pytest configuration, no vitest configuration, no test directories.
- Files: All source files
- Risk: Any change can break existing functionality without detection. The four ad-hoc test scripts in `1/backend/` are manual and use hardcoded paths.
- Priority: High — implement pytest for backend (crud, endpoints, tasks) and vitest + vue-test-utils for frontend.

### Data Cleaning Logic Untested

- What's not tested: `process_dataset_clean` and `convert_dataset_format` in `1/backend/app/tasks/dataset_tasks.py` are 392 lines of business logic with zero test coverage.
- Files: `1/backend/app/tasks/dataset_tasks.py`
- Risk: Data corruption during cleaning/conversion would go undetected until end users notice.
- Priority: High — add unit tests for cleaning operators (dedup, missing value fill, format conversion).

---

## Scaling Limits

### Single Celery Worker with Solo Pool

- Current capacity: `1/backend/app/core/celery_app.py` (line 20) uses `worker_pool='solo'`. This means only ONE task at a time can be processed.
- Limit: Any concurrent upload/cleaning/conversion request will queue behind the active task.
- Scaling path: Change to `prefork` for multi-CPU concurrent task processing. For GPU-intensive training tasks, consider a separate `gpu` queue with dedicated workers.

### No File Size Limit Enforcement on Upload

- Current capacity: The 100MB limit from `PROJECT.md` constraints is not enforced in code. `datasets.py` only declares `CHUNK_SIZE = 5 * 1024 * 1024` but doesn't validate total file size.
- Limit: A user could upload arbitrarily large files, exhausting disk space and memory.
- Scaling path: Add file size validation at both the initiate-upload stage (reject if >100MB) and the chunk accumulation stage (track total received bytes).

---

## AGENTS.md Documentation Drift

### Stale File References

- Issue: `1/AGENTS.md` (line 33) references `backend/app/tasks.py` which no longer exists. The tasks are now in `backend/app/tasks/__init__.py` and `backend/app/tasks/dataset_tasks.py`.
- Impact: Developers following the documentation will look for a non-existent file.
- Fix approach: Update to `backend/app/tasks/` (package).

- Issue: `1/AGENTS.md` (line 49) claims `frontend/src/api/ (empty - needs HTTP client module)`. The directory actually contains 4 files: `auth.ts`, `data-manage.ts`, `dataset.ts`, `system-manage.ts`.
- Impact: Misleading status report. Developers may create duplicate HTTP client code.
- Fix approach: Update status or remove the "empty" claim.

- Issue: `1/AGENTS.md` lists `frontend/src/views/DataManagementView.vue` as "planned but missing" (Phase 2). The actual file is at `frontend/src/views/data-management/index.vue` — it exists but is a placeholder.
- Impact: Phase planning may be based on incorrect completion status.
- Fix approach: Update to reflect current state: "placeholder exists, needs full implementation."

---

*Concerns audit: 2026-05-01*
