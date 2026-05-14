# ruff: noqa: E402
from fastapi import APIRouter

api_v1 = APIRouter(prefix="/v1")

from src.app.v1.dataset import datasets_router, logs_router
from src.app.v1.dataset import router as dataset_router

api_v1.include_router(dataset_router)
api_v1.include_router(datasets_router)
api_v1.include_router(logs_router)

from src.app.v1.dataset_tag import router as tag_router
from src.app.v1.dataset_tag import tags_router

api_v1.include_router(tag_router)
api_v1.include_router(tags_router)

from src.app.v1.user import auth_api, user_api

api_v1.include_router(user_api)
api_v1.include_router(auth_api)

from src.app.v1.admin import admin_api

api_v1.include_router(admin_api)

from src.app.v1.task import router as task_router

api_v1.include_router(task_router)

from src.app.v1.llamafactory import router as llamafactory_router

api_v1.include_router(llamafactory_router)

from src.app.v1.dashboard import router as dashboard_router

api_v1.include_router(dashboard_router)


@api_v1.get("/")
def ask_v1_router():
    return {"api_version": "v1", "status": "ok"}
