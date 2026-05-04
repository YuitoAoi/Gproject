from fastapi import APIRouter

api_v1 = APIRouter(prefix="/v1")

from src.app.v1.dataset import router as dataset_router, datasets_router  # noqa: E402

api_v1.include_router(dataset_router)
api_v1.include_router(datasets_router)

from src.app.v1.dataset_tag import router as tag_router, tags_router
api_v1.include_router(tag_router)
api_v1.include_router(tags_router)

from src.app.v1.user import user_api,auth_api
api_v1.include_router(user_api)
api_v1.include_router(auth_api)


@api_v1.get("/")
def ask_v1_router():
    return {"api_version": "v1", "status": "ok"}
