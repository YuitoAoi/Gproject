# Testing Patterns

**Analysis Date:** 2026-04-13

## Test Framework

**Runner:**
- **No test framework is currently installed or configured**
- Backend: No `pytest`, `unittest`, or any test runner in `1/backend/requirements.txt`
- Frontend: No `vitest`, `jest`, or any test runner in `1/frontend/package.json` devDependencies
- No test config files found: no `pytest.ini`, `conftest.py`, `jest.config.*`, `vitest.config.*`

**Assertion Library:**
- Not configured — would use `pytest` assertions (Python) and `vitest` assertions (TypeScript) when added

**Run Commands:**
```bash
# No test commands currently exist
# Backend (when added):
cd 1/backend && pytest                          # Run all tests
cd 1/backend && pytest -x                        # Stop on first failure
cd 1/backend && pytest --cov=app                 # Coverage

# Frontend (when added):
cd 1/frontend && npm run test                    # Run all tests (needs to be added to scripts)
cd 1/frontend && npx vitest                      # Run vitest
cd 1/frontend && npx vitest --coverage           # Coverage
```

## Test File Organization

**Location:**
- **No test files exist anywhere in the project source**
- No `tests/` directory in `1/backend/`
- No `__tests__/` or `*.test.ts` / `*.spec.ts` files in `1/frontend/src/`
- No test files adjacent to source files (co-located pattern)

**Recommended Structure (when adding tests):**

Backend:
```
1/backend/
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       ├── health.py
│   │       └── tests/
│   │           └── test_health.py      # Co-located tests
│   └── ...
├── tests/                              # Or top-level tests directory
│   ├── conftest.py                     # Shared fixtures
│   ├── api/
│   │   └── test_health.py
│   └── test_tasks.py
└── requirements.txt
```

Frontend:
```
1/frontend/
├── src/
│   ├── api/
│   │   ├── httpClient.ts
│   │   └── httpClient.spec.ts          # Co-located test files
│   ├── store/
│   │   ├── ui.ts
│   │   └── ui.spec.ts
│   └── views/
│       └── HomeView.spec.ts
└── vitest.config.ts                   # Vitest config file
```

**Naming Convention (to adopt):**
- Backend Python: `test_*.py` files with `test_*` function names
- Frontend TypeScript: `*.spec.ts` for unit tests, `*.spec.vue` for component tests (or `*.test.ts` / `*.test.vue`)

## Test Structure

**Suite Organization (to adopt):**

Backend (pytest):
```python
# test_health.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_returns_ok():
    """健康检查端点应返回200和正确状态"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
```

Frontend (vitest):
```typescript
// ui.spec.ts
import { describe, it, expect } from 'vitest'
import { useUIStore } from '../ui'

describe('useUIStore', () => {
  it('should toggle sidebar state', () => {
    const store = useUIStore()
    expect(store.isCollapsed).toBe(false)
    store.toggleSidebar()
    expect(store.isCollapsed).toBe(true)
  })
})
```

**Patterns:**
- Use `describe`/`it` blocks for grouping and naming test cases
- Use descriptive test names in Chinese or English that explain expected behavior
- Use `pytest` fixtures for reusable test setup (DB sessions, test client)
- Use `beforeEach`/`afterEach` for Vue/Pinia store state reset

## Mocking

**Framework:** Not yet configured

**Backend Mocking (when added):**
```python
# Use unittest.mock for Celery tasks
from unittest.mock import patch, MagicMock

def test_create_add_task_dispatches_celery():
    with patch('app.api.endpoints.tasks.add.delay') as mock_delay:
        mock_delay.return_value.id = 'test-task-id'
        # ... test API endpoint
```

```python
# Use TestClient for FastAPI endpoint testing (no mock needed for DB if using test DB)
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
```

**Frontend Mocking (when added):**
```typescript
// Mock axios for API tests
import { vi } from 'vitest'
import httpClient from '../httpClient'

vi.mock('axios', () => ({
  default: { create: () => ({ /* mock instance */ }) }
}))

// Mock Element Plus notification
vi.mock('element-plus', () => ({
  ElNotification: vi.fn()
}))
```

**What to Mock:**
- External HTTP calls (use `httpx` `AsyncClient` or `TestClient` for FastAPI)
- Celery task execution (mock `.delay()` to avoid actual task dispatch)
- Database calls in unit tests (use test DB for integration tests)
- WebSocket connections in frontend tests
- `localStorage` in frontend tests
- `ElNotification` calls in frontend tests

**What NOT to Mock:**
- Pydantic model validation — test these directly
- Pinia store logic — test store actions directly
- Vue component rendering — use `@vue/test-utils` for real rendering
- SQLAlchemy model definitions

## Fixtures and Factories

**Test Data:** No fixtures or factories exist yet.

**Backend Fixtures (to create):**

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal, Base
from app.core.config import settings

@pytest.fixture(scope="session")
def test_client():
    """Create a TestClient for the FastAPI app"""
    return TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
```

**Frontend Fixtures (to create):**

```typescript
// test/setup.ts
import { setActivePinia, createPinia } from 'pinia'

// Auto-setup Pinia for all tests
beforeEach(() => {
  setActivePinia(createPinia())
})
```

**Location:**
- Backend: `1/backend/tests/conftest.py` for shared fixtures
- Frontend: `1/frontend/src/test/setup.ts` for test environment setup

## Coverage

**Requirements:** No coverage target enforced. Not configured.

**Recommended Targets:**
- Backend API endpoints: >80% coverage
- Frontend store logic: >90% coverage
- Critical paths (task submission, WebSocket): 100% coverage

**View Coverage (when configured):**
```bash
# Backend
cd 1/backend && pytest --cov=app --cov-report=html

# Frontend
cd 1/frontend && npx vitest --coverage
```

**Configuration to add in `1/frontend/package.json`:**
```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

**Configuration to add in `1/backend/requirements.txt`:**
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
pytest-cov>=4.1.0
```

## Test Types

**Unit Tests:**
- Not yet implemented
- Should cover: Pydantic models, Pinia stores, utility functions, Celery tasks
- Target: `1/backend/tests/unit/` and `1/frontend/src/**/*.spec.ts`

**Integration Tests:**
- Not yet implemented
- Should cover: FastAPI endpoints with TestClient, database operations with test DB
- Target: `1/backend/tests/integration/`
- Use `TestClient` from FastAPI for endpoint testing

**E2E Tests:**
- Not used
- Consider: Playwright or Cypress for browser-based E2E testing
- Target: `1/frontend/e2e/`

## Common Patterns

**Async Testing (Backend - when added):**
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health/")
    assert response.status_code == 200
```

**Async Testing (Frontend - when added):**
```typescript
import { describe, it, expect } from 'vitest'

describe('WebSocketManager', () => {
  it('should connect and dispatch messages', async () => {
    // Test WebSocket reconnection logic
    // Use fake timers for reconnect interval testing
  })
})
```

**Error Testing:**
```python
# Backend: Test error responses
def test_get_nonexistent_task_returns_404():
    response = client.get("/api/v1/tasks/nonexistent-id")
    # Currently returns Celery result, not 404
    # This test documents expected behavior
```

```typescript
// Frontend: Test error handling in httpClient
describe('httpClient error interceptor', () => {
  it('should show notification on 401 and redirect', () => {
    // Test that 401 responses clear auth_token and redirect
  })
})
```

## Test Dependencies to Add

**Backend (`1/backend/requirements.txt`):**
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
pytest-cov>=4.1.0
```

**Frontend (`1/frontend/package.json` devDependencies):**
```json
{
  "vitest": "^1.0.0",
  "@vue/test-utils": "^2.4.0",
  "jsdom": "^23.0.0",
  "@vitest/coverage-v8": "^1.0.0"
}
```

**Frontend config (`1/frontend/vitest.config.ts`):**
```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
  }
})
```

---

*Testing analysis: 2026-04-13*