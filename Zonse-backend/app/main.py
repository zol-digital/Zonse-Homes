from fastapi import FastAPI

from app.api.router import router as api_router
from app.config import settings
from app.exception_handlers import register_exception_handlers

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

register_exception_handlers(app)
app.include_router(api_router)