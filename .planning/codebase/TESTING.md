# Testing Patterns

**Analysis Date:** 2026-05-01

## Test Framework

**No formal test framework is configured for either backend or frontend.**

### Backend
- **Runner:** Not configured. No `pytest`, `unittest`, or other test runner setup found.
- **Config:** No `pytest.ini`, `pyproject.toml` (with pytest section), or `tox.ini` detected.
- **Test files found:** Ad-hoc Python scripts only (see "Ad-hoc Test Scripts" below).

### Frontend
- **Runner:** Not configured. No `vitest`, `jest`, or other test runner.
- **Config:** No `vitest.config.*` or `jest.config.*` detected.
- **Test files found:** None. Zero `*.test.ts`, `*.spec.ts`, `*.test.tsx`, or `*.spec.vue` files exist.

## Run Commands

**None configured.** The `1/frontend/package.json` scripts do not include any test-related commands:

```json
{
  "scripts": {
    "dev": "vite --open",
    "build": "vue-tsc --noEmit && vite build",
    "serve": "vite preview",
    "lint": "eslint",
    "fix": "eslint --fix",
    "lint:prettier": "prettier --write \"**/*.{js,cjs,ts,json,tsx,css,less,scss,vue,html,md}\"",
    "lint:stylelint": "stylelint  \"**/*.{css,scss,vue}\" --fix",
    "lint:lint-staged": "lint-staged",
    "prepare": "husky",
    "commit": "git-cz",
    "clean:dev": "tsx scripts/clean-dev.ts"
  }
}
```

**No `test` or `coverage` scripts.**

## Code Quality Tools (Linting Only)

These are available but are **linting/formatter tools, not test tools**:

| Tool | Scope | Config File |
|------|-------|-------------|
| ESLint 9.9.1 | JS/TS/Vue | `1/frontend/eslint.config.mjs` |
| Prettier 3.5.3 | All frontend | `1/frontend/.prettierrc` |
| Stylelint 16.20.0 | CSS/SCSS/Vue | `1/frontend/.stylelintrc.cjs` |
| TypeScript (`vue-tsc`) | Type checking | `1/frontend/tsconfig.json` |

**Backend has no linter or formatter configured at all.**

## Ad-hoc Test Scripts

Four Python scripts exist in `1/backend/` that serve as manual integration/verification helpers. They are not part of any test framework and must be run manually:

| File | Purpose | Notes |
|------|---------|-------|
| `1/backend/test_mysql.py` | Verify MySQL connection, create database, initialize tables | Hardcoded path: `'D:/files/Gproject/1/backend'` |
| `1/backend/test_celery.py` | Start Celery worker as subprocess, test `add`/`multiply` tasks | Hardcoded path, uses `subprocess.Popen` |
| `1/backend/test_celery_tasks.py` | Test `add`/`multiply` tasks (requires already-running worker) | Near-duplicate of `test_celery.py` |
| `1/backend/test_celery_direct.py` | Test task dispatch via `celery_app.send_task()` | Hardcoded path |

**Issues with these scripts:**
1. All use hardcoded absolute paths: `sys.path.insert(0, 'D:/files/Gproject/1/backend')`
2. `test_celery.py` and `test_celery_tasks.py` are nearly duplicate and should be consolidated
3. No assertions — just `print()` statements; require human inspection to verify
4. Not discoverable by any test runner
5. No database test helpers, no fixture data, no test isolation

## Test File Organization

**No test file organization pattern exists.**

If tests were to be added, follow these conventions:

**Backend (Python):**
```
1/backend/tests/
├── __init__.py
├── conftest.py           # Shared fixtures (DB session, test client, mock celery)
├── test_api/             # API endpoint tests
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_tasks.py
│   ├── test_datasets.py
│   └── test_users.py
├── test_crud/            # CRUD operation tests
│   └── test_dataset.py
├── test_tasks/           # Celery task tests
│   └── test_dataset_tasks.py
└── test_core/            # Core infrastructure tests
    ├── test_websocket_manager.py
    └── test_redis_pubsub.py
```

**Frontend (TypeScript/Vue):**
```
1/frontend/src/
├── __tests__/            # Co-located with source (if using Vitest)
│   ├── api/
│   │   ├── auth.test.ts
│   │   └── dataset.test.ts
│   ├── store/
│   │   ├── user.test.ts
│   │   └── task.test.ts
│   ├── hooks/
│   │   └── useWebSocketTask.test.ts
│   └── components/
│       └── ...
```

## Mocking

**No mocking framework or library is set up for either backend or frontend.**

### Recommended Setup

**Backend:**
- Use `pytest` + `unittest.mock` (stdlib) or `pytest-mock`
- Mock external dependencies: Redis, MySQL, Celery
- Use FastAPI `TestClient` for endpoint testing
- Use in-memory SQLite for database tests

**Frontend:**
- Use Vitest with `vi.fn()`, `vi.mock()`, `vi.spyOn()`
- Mock Axios for API call testing
- Mock WebSocket for real-time connection testing
- Use `@vue/test-utils` for component testing

## Coverage

**No coverage tooling or requirements exist.**

No coverage configuration found. Neither `pytest-cov` (Python) nor `vitest coverage` / `c8` / `istanbul` (JavaScript) are set up.

## Test Types — Current State

### Unit Tests
**None exist.** No unit tests for:
- Backend CRUD functions (`1/backend/app/crud/dataset.py`)
- Backend Pydantic schemas (`1/backend/app/schemas/dataset.py`)
- Frontend Pinia stores (`1/frontend/src/store/modules/*.ts`)
- Frontend utility functions (`1/frontend/src/utils/**/*.ts`)
- Frontend composables (`1/frontend/src/hooks/core/*.ts`)

### Integration Tests
**None exist.** No integration tests for:
- API endpoint request/response cycles
- Database operations
- Celery task execution
- WebSocket handshake and message passing
- Frontend-backend API contract

### E2E Tests
**None exist.** No end-to-end testing framework (Playwright, Cypress, Selenium) detected.

## Critical Untested Areas

Given the project's core functionality, these areas have zero test coverage and represent significant risk:

| Area | Files | Risk |
|------|-------|------|
| Chunked file upload/assembly | `1/backend/app/api/endpoints/datasets.py`, `1/backend/app/tasks/dataset_tasks.py` | Data corruption, silent failures |
| Dataset CRUD operations | `1/backend/app/crud/dataset.py` | Data loss from incorrect queries |
| Celery task registration | `1/backend/app/core/celery_app.py`, `1/backend/app/tasks/` | Tasks silently not registered (already an issue — see CONCERNS) |
| WebSocket reconnection | `1/frontend/src/hooks/core/useWebSocketTask.ts` | Connection failures unreported |
| Auth flow (mock) | `1/backend/app/api/endpoints/auth.py` | Hardcoded credentials — no real auth tested |
| User store logout/cleanup | `1/frontend/src/store/modules/user.ts` | Token/session leakage |
| HTTP interceptor error handling | `1/frontend/src/utils/http/index.ts` | 401 loops, missing error messages |
| Redis Pub/Sub bridge | `1/backend/app/core/redis_pubsub.py` | Message loss in multi-worker scenarios |

## Prescriptive Guidance

When adding tests to this project:

1. **Use Vitest for frontend** (already in the Vite ecosystem, matches the project's tech choices)
2. **Use pytest for backend** (Python standard, integrates with FastAPI TestClient)
3. **Co-locate frontend tests** with source files (`*.test.ts` next to the implementation)
4. **Separate backend tests** in a `tests/` directory at backend root
5. **Add test scripts to `package.json`**: `"test": "vitest"`, `"test:coverage": "vitest --coverage"`
6. **Start with the critical paths**: dataset upload, Celery task dispatch/result, auth flow

---

*Testing analysis: 2026-05-01*
