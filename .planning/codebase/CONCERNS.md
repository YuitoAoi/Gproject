# Codebase Concerns

**Generated:** 2026-04-13
**Codebase:** LLaMA-Factory Workstation (Vue 3 + FastAPI)

## Technical Debt

### TD-01: No Authentication Implementation
- **Severity:** High
- **Location:** `1/backend/app/core/config.py`, `1/frontend/src/api/httpClient.ts`
- **Description:** The httpClient has auth token handling (Bearer token in interceptor, 401 redirect), but the backend has no auth endpoints, no JWT issuance, no password hashing service, and no auth middleware. The `User` model has `hashed_password` and `role` fields, but nothing creates or verifies credentials.
- **Impact:** All API endpoints are completely unprotected. Anyone with network access can call any endpoint.
- **Remediation:** Implement full auth flow: signup, login, JWT middleware, token refresh.

### TD-02: Placeholder Celery Tasks
- **Severity:** Medium
- **Location:** `1/backend/app/tasks.py`
- **Description:** Only `add` and `multiply` demo tasks exist. No actual training tasks, data processing tasks, or model management tasks are implemented. The entire task processing pipeline is a stub.
- **Impact:** Core business logic (training orchestration, data processing) cannot function.
- **Remediation:** Implement real Celery tasks for training, data processing, and model operations.

### TD-03: Minimal API Surface
- **Severity:** Medium
- **Location:** `1/backend/app/api/router.py`, `1/backend/app/api/endpoints/`
- **Description:** Only 2 endpoint modules exist: `health.py` (1 GET) and `tasks.py` (2 POST + 1 GET for demo tasks). No endpoints for datasets, training config, model management, inference, or monitoring — all critical for the product.
- **Impact:** Frontend has no real backend to communicate with.
- **Remediation:** Build out full API endpoint coverage per REQUIREMENTS.md.

### TD-04: Schemas and CRUD Modules Are Empty
- **Severity:** Medium
- **Location:** `1/backend/app/schemas/__init__.py`, `1/backend/app/crud/__init__.py`, `1/backend/app/services/__init__.py`
- **Description:** All three critical module directories contain only empty `__init__.py` files. No Pydantic schemas for request/response validation, no CRUD operations for database models, no service layer.
- **Impact:** No data validation, no database operations, no business logic layer.
- **Remediation:** Implement schemas, CRUD, and services for each domain entity.

### TD-05: Frontend Views Are Placeholder Shells
- **Severity:** Medium
- **Location:** `1/frontend/src/views/`
- **Description:** All views (DashboardView, DataManagementView, TasksView, ModelsView) are empty placeholder components with just a heading. No forms, tables, or interactive elements.
- **Impact:** The UI is non-functional beyond basic navigation.
- **Remediation:** Build out each view with actual functionality.

## Security Issues

### SEC-01: Hardcoded Database Credentials
- **Severity:** High
- **Location:** `1/backend/app/core/config.py:10`
- **Description:** Default `DATABASE_URL` contains `root:password` hardcoded. While `.env` override exists, the fallback is insecure and will be used if `.env` is missing.
- **Impact:** Database exposure if deployed without `.env` file.
- **Remediation:** Remove default value or use a non-privileged default that fails safely.

### SEC-02: Permissive CORS Configuration
- **Severity:** Medium
- **Location:** `1/backend/app/main.py:16`
- **Description:** CORS allows `allow_methods=["*"]` and `allow_headers=["*"]`. While origins are restricted, methods and headers are fully open.
- **Impact:** Potential for cross-origin attacks if origin list is expanded carelessly.
- **Remediation:** Restrict to specific methods and headers needed.

### SEC-03: No Input Sanitization on File Paths
- **Severity:** High
- **Location:** `1/backend/app/db/models/__init__.py` — `Dataset.file_path`, `TrainingTask.log_path`, `TrainingTask.output_path`, `TrainedModel.model_path`
- **Description:** Database models store file paths as plain strings with no validation. When file operations are implemented, path traversal attacks are likely possible.
- **Impact:** Path traversal could allow reading/writing arbitrary files on the server.
- **Remediation:** Validate and sanitize all file paths. Use allowlist-based directory restrictions.

### SEC-04: No Rate Limiting
- **Severity:** Low
- **Location:** `1/backend/app/main.py`
- **Description:** No rate limiting middleware configured on the FastAPI app.
- **Impact:** API abuse, denial of service possible.
- **Remediation:** Add rate limiting middleware (e.g., `slowapi`).

## Performance Concerns

### PERF-01: No Database Connection Pooling Config
- **Severity:** Low
- **Location:** `1/backend/app/db/session.py:6`
- **Description:** `create_engine(settings.DATABASE_URL)` uses default pool settings. For a multi-user workstation, this may not be sufficient.
- **Impact:** Connection exhaustion under concurrent load.
- **Remediation:** Configure `pool_size`, `max_overflow`, and `pool_pre_ping` explicitly.

### PERF-02: WebSocket Heartbeat Memory Leak
- **Severity:** Medium
- **Location:** `1/frontend/src/api/websocket.ts:97-102`
- **Description:** `startHeartbeat()` uses `setInterval` but never stores or clears the interval reference. If `disconnect()` is called, the interval keeps running.
- **Impact:** Memory leak and unnecessary CPU usage after disconnect.
- **Remediation:** Store interval reference and clear it in `disconnect()`.

### PERF-03: No Lazy Loading for Large Dataset Lists
- **Severity:** Low
- **Location:** Frontend views (not yet implemented)
- **Description:** When data management views are implemented, there's no infrastructure for pagination or virtual scrolling for large dataset lists.
- **Impact:** Performance degradation with large datasets.
- **Remediation:** Plan pagination/virtual scrolling from the start.

## Fragile Areas

### FRAG-01: Circular Import Risk Between Models and Session
- **Severity:** Low
- **Location:** `1/backend/app/db/models/__init__.py` imports from `app.db.session`, while session module creates engine that may need models.
- **Description:** Models import `Base` from session, but `init_db.py` likely imports models to create tables. This works now but could break with refactoring.
- **Impact:** Import errors during restructuring.
- **Remediation:** Consider using a separate `base.py` for the declarative base.

### FRAG-02: No Database Migration Strategy
- **Severity:** Medium
- **Location:** `1/backend/` — `alembic` is in requirements.txt but no `alembic.ini` or `migrations/` directory exists
- **Description:** Alembic is listed as a dependency but never configured. Schema changes will require manual SQL or recreating tables.
- **Impact:** Schema evolution will be painful and error-prone.
- **Remediation:** Initialize Alembic with `alembic init migrations` and create initial migration.

### FRAG-03: WebSocket URL Derivation May Fail in Production
- **Severity:** Low
- **Location:** `1/frontend/src/api/websocket.ts:104-108`
- **Description:** WebSocket URL is derived from `window.location` with `VITE_WS_URL` as override. In production behind reverse proxies, this may not resolve correctly.
- **Impact:** WebSocket connections fail silently in certain deployment configurations.
- **Remediation:** Document expected proxy configuration and test with nginx/caddy.

## Missing Infrastructure

### MISS-01: No `.gitignore`
- **Severity:** High
- **Location:** Project root
- **Description:** No `.gitignore` file exists. The `venv/`, `node_modules/`, `__pycache__/`, and `.env` directories could be committed accidentally.
- **Impact:** Repository bloat, potential secret leaks.
- **Remediation:** Create comprehensive `.gitignore` for Python + Node.js project.

### MISS-02: No Environment Configuration
- **Severity:** Medium
- **Location:** `1/backend/`
- **Description:** No `.env.example` file to document required environment variables. New developers won't know what to configure.
- **Impact:** Difficult onboarding, misconfiguration.
- **Remediation:** Create `.env.example` with all required variables documented.

### MISS-03: No Linter/Formatter Configuration
- **Severity:** Low
- **Location:** Both `1/backend/` and `1/frontend/`
- **Description:** No ESLint, Prettier, Ruff, or Black configuration files found. No pre-commit hooks.
- **Impact:** Inconsistent code style, no automated quality checks.
- **Remediation:** Add linter/formatter configs for both backend and frontend.

### MISS-04: No Test Infrastructure
- **Severity:** High
- **Location:** Entire project
- **Description:** No test files, test directories, or test configuration exist anywhere in the project. No pytest, no vitest, no test scripts.
- **Impact:** No way to verify correctness of any implementation.
- **Remediation:** Set up pytest for backend and vitest for frontend with initial test structure.

### MISS-05: No Docker/Container Configuration
- **Severity:** Low
- **Location:** Project root
- **Description:** No Dockerfile, docker-compose.yml, or container configuration for the multi-service architecture (FastAPI, Celery, Redis, MySQL).
- **Impact:** Manual, error-prone deployment; no reproducible environments.
- **Remediation:** Create docker-compose.yml for local development and deployment.

## Summary

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Technical Debt | 0 | 1 | 4 | 0 |
| Security | 0 | 2 | 1 | 1 |
| Performance | 0 | 0 | 1 | 2 |
| Fragile | 0 | 0 | 1 | 2 |
| Missing Infra | 0 | 2 | 1 | 2 |

**Total: 20 concerns** — The codebase is in early scaffolding stage. Most business logic is not yet implemented, and the existing code has placeholder/demo functionality only. Priority should be: auth implementation (SEC-01, TD-01), real API endpoints (TD-03), and test infrastructure (MISS-04).
