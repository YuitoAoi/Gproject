"""
GProject FastAPI 入口。

启动方式::

    # Linux / macOS
    cd backend && PYTHONPATH=src uvicorn src.app.main:app --reload

    # Windows PowerShell
    cd backend; $env:PYTHONPATH="src"; uvicorn src.app.main:app --reload

    # 或直接运行
    cd backend && python src/app/main.py
"""

from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI, Request
from src.services import ServiceFactory
from src.core.config import config
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期：启动时组装服务，MySQL 不可达时降级启动。"""
    import logging
    logger = logging.getLogger("uvicorn")

    from src.db_connections.mysql import MysqlDatabaseConnection
    from src.adapters.repositories.mysql_user_repo import MysqlUserRepository
    from src.adapters.repositories.mysql_dataset_repo import MysqlDatasetRepository
    from src.adapters.repositories.windows_file_repo import WindowsFileRepository

    db_conn = MysqlDatabaseConnection(database_url=config.DATABASE_URL)

    try:
        db_conn.start()
        logger.info("MySQL connected successfully")
        MysqlDatasetRepository(db_conn).init_table()
    except RuntimeError as e:
        logger.warning(f"MySQL unavailable, starting in degraded mode: {e}")

    app.state.services = ServiceFactory(
        user_repo=MysqlUserRepository(db_conn),
        dataset_repo=MysqlDatasetRepository(db_conn),
        file_repo=WindowsFileRepository(),
    )
    app.state.db_conn = db_conn
    yield
    app.state.services.dispose()
    db_conn.dispose()


app = FastAPI(
    title="GProject",
    version="1.0.0",
    lifespan=lifespan,
)


# ── 依赖注入 ──────────────────────────────────────────────


def get_services(request: Request) -> ServiceFactory:
    """从 app.state 获取 ServiceFactory，供路由 Depends 使用。"""
    return request.app.state.services


# ── 健康检查 ──────────────────────────────────────────────


@app.get("/health")
def health(request: Request):
    db_conn = getattr(request.app.state, "db_conn", None)
    db_ok = db_conn.is_connected if db_conn else False
    return {
        "app": "GProject",
        "status": "running",
        "mysql": "connected" if db_ok else "unavailable",
    }


# ── 路由注册 ──────────────────────────────────────────────


from src.app.router import router  # noqa: E402
from src.app.v1.dataset import download_router  # noqa: E402

app.include_router(router)
app.include_router(download_router)

# TODO 修改为更安全的用法
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 允许所有来源
    allow_credentials=True,        # 允许携带 cookies（若使用 "*" 需注意例外情况）
    allow_methods=["*"],           # 允许所有请求方法 (GET, POST, PUT, DELETE, OPTIONS等)
    allow_headers=["*"],           # 允许所有请求头
)
# ── 启动入口 ──────────────────────────────────────────────


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 确保 src/ 在 sys.path 中（支持 python src/app/main.py 直接运行）
    _src = Path(__file__).resolve().parents[1]
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

    import uvicorn

    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)

# poetry run uvicorn src.app.main:app --reload