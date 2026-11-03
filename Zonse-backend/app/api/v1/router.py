from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    discovery,
    featured,
    health,
    properties,
    reference_data,
    reports,
    users,
)

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, tags=["auth"])
router.include_router(users.router, tags=["users"])
router.include_router(properties.router, tags=["properties"])
router.include_router(reports.router, tags=["reports"])
router.include_router(admin.router, tags=["admin"])
router.include_router(reference_data.router, tags=["reference-data"])
router.include_router(reference_data.admin_router, tags=["admin"])
router.include_router(discovery.router, tags=["discovery"])
router.include_router(discovery.featured_router, tags=["discovery"])
router.include_router(featured.router)
