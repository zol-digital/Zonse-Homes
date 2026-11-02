from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import router as api_router
from app.config import settings
from app.exception_handlers import register_exception_handlers

settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

register_exception_handlers(app)
app.include_router(api_router)
app.mount(
    "/uploads",
    StaticFiles(directory=str(settings.UPLOAD_DIR), follow_symlink=False),
    name="uploads",
)