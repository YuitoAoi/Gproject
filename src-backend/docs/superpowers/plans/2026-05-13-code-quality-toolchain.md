# Code Quality Toolchain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ruff, mypy, pytest config, and pre-commit to the backend project with medium strictness.

**Architecture:** All tool configuration lives in `pyproject.toml` (single source of truth). Pre-commit handles format/lint on commit. Mypy runs manually or in CI only.

**Tech Stack:** Poetry, ruff >=0.11.0, mypy >=1.15.0, pre-commit >=4.2.0, pytest >=8.0.0

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `pyproject.toml` | Modify | Dev dependencies + all tool configs |
| `.pre-commit-config.yaml` | Create | Pre-commit hook definitions |
| `src/**/*.py` | Modify (auto) | Ruff auto-fix + format pass |
| `tests/**/*.py` | Modify (auto) | Ruff auto-fix + format pass |

---

### Task 1: Add dev dependencies and tool configs to pyproject.toml

**Files:**
- Modify: `pyproject.toml:36-39`

- [ ] **Step 1: Replace the `[dependency-groups]` section and append all tool config**

Replace the entire content of `pyproject.toml` with:

```toml
[project]
name = "gproject-backend"
version = "0.1.0"
description = ""
authors = [
    {name = "Your Name",email = "you@example.com"}
]
requires-python = ">=3.12,<3.13"
dependencies = [
    "celery (>=5.6.3,<6.0.0)",
    "fastapi (>=0.136.1,<0.137.0)",
    "pydantic-settings (>=2.14.0,<3.0.0)",
    "sqlalchemy (>=2.0.0,<3.0.0)",
    "pymysql (>=1.1.0,<2.0.0)",
    "uvicorn (>=0.46.0,<0.47.0)",
    "bcrypt (>=5.0.0,<6.0.0)",
    "pyjwt (>=2.12.1,<3.0.0)",
    "aiomysql (>=0.3.2,<0.4.0)",
    "pytest-asyncio (>=1.3.0,<2.0.0)",
    "python-multipart (>=0.0.27,<0.0.28)",
    "redis (>=7.4.0,<8.0.0)",
    "msgspec (>=0.21.1,<0.22.0)",
    "httpx (>=0.28.1,<0.29.0)",
    "openpyxl (>=3.1.5,<4.0.0)",
    "websockets (>=14.0,<15.0)",
]


[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
package-mode = false

[dependency-groups]
dev = [
    "pytest (>=8.0.0,<9.0.0)",
    "pytest-cov (>=7.1.0,<8.0.0)",
    "ruff (>=0.11.0,<1.0.0)",
    "mypy (>=1.15.0,<2.0.0)",
    "pre-commit (>=4.2.0,<5.0.0)",
]

# ── Ruff ─────────────────────────────────────────────────────

[tool.ruff]
target-version = "py312"
line-length = 120
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "RUF",  # ruff-specific
]
ignore = [
    "E501",   # line-length 交给 formatter
    "B008",   # FastAPI Depends() 在默认参数中是惯用写法
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["B011", "S101"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

# ── Mypy ─────────────────────────────────────────────────────

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false

# ── Pytest ───────────────────────────────────────────────────

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --strict-markers"
```

- [ ] **Step 2: Verify the file is valid TOML**

Run: `poetry run python -c "import tomllib; tomllib.load(open('pyproject.toml','rb')); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "build: add ruff/mypy/pytest/pre-commit dev deps and tool configs"
```

---

### Task 2: Create .pre-commit-config.yaml

**Files:**
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: Create the pre-commit config file**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
```

- [ ] **Step 2: Validate YAML syntax**

Run: `poetry run python -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml')); print('OK')" 2>/dev/null || poetry run python -c "import json,subprocess; print('YAML file created, validate manually')"`
Expected: `OK` or confirmation file exists

- [ ] **Step 3: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "build: add pre-commit config with ruff hooks"
```

---

### Task 3: Install dependencies

**Files:**
- Modify: `poetry.lock` (auto-generated)

- [ ] **Step 1: Install all dev dependencies**

Run: `poetry install --with dev`
Expected: Successfully installs ruff, mypy, pre-commit, pytest without errors

- [ ] **Step 2: Verify tools are available**

Run: `poetry run ruff --version && poetry run mypy --version && poetry run pre-commit --version`
Expected: Version strings for all three tools (e.g. `ruff 0.11.x`, `mypy 1.15.x`, `pre-commit 4.x.x`)

- [ ] **Step 3: Commit lock file**

```bash
git add poetry.lock
git commit -m "build: update poetry.lock with quality toolchain deps"
```

---

### Task 4: Run ruff auto-fix and format on codebase

**Files:**
- Modify: `src/**/*.py` (auto)
- Modify: `tests/**/*.py` (auto)

- [ ] **Step 1: Run ruff check with auto-fix**

Run: `poetry run ruff check --fix src/ tests/`
Expected: Output showing fixed issues (e.g. unused imports removed, import order fixed). Some unfixable warnings may remain.

- [ ] **Step 2: Run ruff format**

Run: `poetry run ruff format src/ tests/`
Expected: Output showing files reformatted (e.g. `12 files reformatted`)

- [ ] **Step 3: Run ruff check again to see remaining warnings**

Run: `poetry run ruff check src/ tests/`
Expected: Either clean (no output) or a small number of warnings that need manual `# noqa` or `per-file-ignores`

- [ ] **Step 4: Fix remaining warnings**

For each remaining warning, either:
- Fix the code if it's a real issue
- Add `# noqa: XXXX` inline comment if it's intentional old code
- Add to `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml` if it's a whole-file pattern

Goal: `poetry run ruff check src/ tests/` exits with code 0.

- [ ] **Step 5: Verify ruff passes clean**

Run: `poetry run ruff check src/ tests/ && poetry run ruff format --check src/ tests/`
Expected: Both commands exit 0 with no output

- [ ] **Step 6: Run existing tests to confirm nothing broke**

Run: `poetry run pytest`
Expected: All existing tests pass (same results as before the format changes)

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "style: apply ruff auto-fix and format to existing codebase"
```

---

### Task 5: Record mypy baseline

**Files:**
- None modified (observation only)

- [ ] **Step 1: Run mypy on src/**

Run: `poetry run mypy src/`
Expected: Errors are expected (old code lacks type annotations). Note the count for future reference.

- [ ] **Step 2: Document baseline in commit message**

No code changes needed. The error count serves as a baseline. Future PRs should not increase it.

---

### Task 6: Install pre-commit hooks and verify

**Files:**
- Modify: `.git/hooks/pre-commit` (auto-generated by pre-commit install)

- [ ] **Step 1: Install pre-commit hooks**

Run: `poetry run pre-commit install`
Expected: `pre-commit installed at .git/hooks/pre-commit`

- [ ] **Step 2: Run pre-commit against all files to verify**

Run: `poetry run pre-commit run --all-files`
Expected: All hooks pass (since we already ran ruff fix+format in Task 4)

- [ ] **Step 3: Verify hook triggers on commit**

Create a test: add a trailing space to any file, attempt `git add` + `git commit`. The hook should auto-fix the trailing space and fail the commit (requiring re-add + re-commit).

After verifying, revert the test change:
```bash
git checkout -- .
```

---

### Task 7: Final verification and cleanup commit

**Files:**
- Possibly: `pyproject.toml` (if per-file-ignores were added in Task 4)

- [ ] **Step 1: Run full quality check suite**

Run:
```bash
poetry run ruff check src/ tests/ && \
poetry run ruff format --check src/ tests/ && \
poetry run pytest
```
Expected: All three commands pass (exit 0)

- [ ] **Step 2: Commit any remaining changes**

If Task 4 Step 4 added `noqa` comments or updated `per-file-ignores`:
```bash
git add -A
git commit -m "build: finalize code quality toolchain setup"
```

If no changes remain, skip this step.
