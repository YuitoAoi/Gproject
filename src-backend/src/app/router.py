from fastapi import APIRouter

router = APIRouter(prefix="/api")

from src.app.v1.apis import api_v1  # noqa: E402

router.include_router(api_v1)
