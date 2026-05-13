# 2026-05-13 代码质量工具链脚手架设计

## 背景

当前 `pyproject.toml` 仅包含 `pytest-cov` 一个 dev 依赖，没有任何静态检查、格式化或 pre-commit 配置。代码风格不一致、类型缺失等问题完全没有自动护栏。

## 目标

为后端项目搭建最小可用的代码质量工具链：

1. 引入 ruff（lint + format）、mypy（类型检查）、pre-commit（提交门禁）
2. 中等严格度：新代码必须通过全部规则，老代码允许逐步清理
3. pre-commit 只拦格式和 lint，mypy 留给手动/CI 执行
4. 所有配置集中在 `pyproject.toml`（除 `.pre-commit-config.yaml`）
5. 完全基于 Poetry 工作流

## 非目标

- 不引入 nox/tox 任务编排
- 不在 pre-commit 中跑 mypy 或 pytest
- 不一次性修复全仓历史代码问题
- 不搭建 CI pipeline（留给后续）

## 方案

### 新增 dev 依赖

| 包 | 版本约束 | 用途 |
|---|---|---|
| ruff | >=0.11.0 | lint + format |
| mypy | >=1.15.0 | 类型检查 |
| pre-commit | >=4.2.0 | 提交钩子管理 |
| pytest | >=8.0.0 | 显式声明测试框架 |

全部进入 `[dependency-groups] dev`，不影响生产镜像。

### Ruff 配置

位置：`pyproject.toml` 的 `[tool.ruff]` 段。

```toml
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
```

策略：
- 首次接入时跑 `ruff check --fix` + `ruff format` 对全仓做一次自动修复（仅机器可安全修复的部分）
- 自动修复后仍存在的 warning：如果是老代码且不影响正确性，加 `# noqa` 或 `per-file-ignores` 豁免
- 新增/修改的代码必须零 warning 通过

### Mypy 配置

位置：`pyproject.toml` 的 `[tool.mypy]` 段。

```toml
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
```

执行方式：`poetry run mypy src/`，不进 pre-commit。

### Pytest 配置

位置：`pyproject.toml` 的 `[tool.pytest.ini_options]` 段。

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --strict-markers"
```

### Pre-commit 配置

位置：项目根目录 `.pre-commit-config.yaml`。

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

### 常用命令

| 场景 | 命令 |
|---|---|
| 安装 dev 依赖 | `poetry install --with dev` |
| 安装 pre-commit hooks | `poetry run pre-commit install` |
| 手动跑 lint | `poetry run ruff check src/ tests/` |
| 自动修复 | `poetry run ruff check --fix src/ tests/` |
| 格式化 | `poetry run ruff format src/ tests/` |
| 类型检查 | `poetry run mypy src/` |
| 跑测试 | `poetry run pytest` |
| 跑测试+覆盖率 | `poetry run pytest --cov=src` |

## 落地策略

1. 先修改 `pyproject.toml`，添加 dev 依赖和工具配置
2. 创建 `.pre-commit-config.yaml`
3. 执行 `poetry install --with dev`
4. 跑一次 `ruff check --fix` + `ruff format` 清理现有代码
5. 跑一次 `mypy src/` 记录当前 baseline（不要求零错误）
6. 执行 `pre-commit install` 激活钩子
7. 提交全部变更
