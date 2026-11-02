from fastapi import APIRouter

from app.api.v1.endpoints import auth, discovery, health, properties, users

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, tags=["auth"])
router.include_router(users.router, tags=["users"])
router.include_router(properties.router, tags=["properties"])
router.include_router(discovery.router, tags=["discovery"])
