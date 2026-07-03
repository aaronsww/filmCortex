from fastapi import APIRouter

from filmcortex.api.v1 import health, movies

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(movies.router, tags=["movies"])
