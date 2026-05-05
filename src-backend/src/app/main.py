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
from fastapi.responses import JSONResponse
from src.services import ServiceFactory
from src.core.config import config
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期：启动时组装服务，数据库不可达则退出。"""
    import logging
    logger = logging.getLogger("uvicorn")

    from src.db_connections import create_db_connection
    from src.adapters.repositories.user_repo import UserRepositoryAdapter
    from src.adapters.repositories.dataset_repo import DatasetRepositoryAdapter
    from src.adapters.repositories.dataset_tag_repo import DatasetTagRepositoryAdapter
    from src.adapters.repositories.windows_file_repo import WindowsFileRepository

    db_conn = create_db_connection(config.DATABASE_URL)

    db_conn.start()
    logger.info("Database connected successfully")
    DatasetRepositoryAdapter(db_conn).init_table()
    DatasetTagRepositoryAdapter(db_conn).init_table()

    # ── 超级用户初始化：id=0 表首位 ──────────────────────────
    from datetime import datetime
    from src.core.password_encryptor import hash_password
    from sqlalchemy import text

    user_repo = UserRepositoryAdapter(db_conn)
    user_repo.init_table()
    existing = user_repo.find_by_id(0)

    if existing is None:
        now = datetime.now()
        s = db_conn.new_session()
        try:
            s.execute(text(
                "INSERT INTO users (id, name, email, password, is_admin, is_active, created_at, last_login, last_login_ip) "
                "VALUES (0, :name, :email, :password, 1, 1, :now, :now, :ip)"
            ), {
                "name": "super",
                "email": config.SUPER_USER_EMAIL,
                "password": hash_password(config.SUPER_USER_PASSWORD),
                "now": now,
                "ip": "",
            })
            s.commit()
        finally:
            s.close()
        logger.info(f"Super user created at id=0: {config.SUPER_USER_EMAIL}")
    else:
        existing.email = config.SUPER_USER_EMAIL
        existing.password = hash_password(config.SUPER_USER_PASSWORD)
        user_repo.update(0, existing)
        logger.info(f"Super user updated at id=0: {config.SUPER_USER_EMAIL}")

    app.state.services = ServiceFactory(
        user_repo=UserRepositoryAdapter(db_conn),
        dataset_repo=DatasetRepositoryAdapter(db_conn),
        file_repo=WindowsFileRepository(),
        conn=db_conn,
        dataset_tag_repo=DatasetTagRepositoryAdapter(db_conn),
    )
    app.state.db_conn = db_conn
    yield
    app.state.services.dispose()
    db_conn.dispose()


from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(
    title="GProject",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(_request: Request, exc: StarletteHTTPException):
    """HTTPException → 统一 Response 格式。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def _pydantic_422_to_400(_request: Request, exc: RequestValidationError):
    """Pydantic 校验错 → 400，统一 Response 格式。"""
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": str(exc.errors())},
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

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
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