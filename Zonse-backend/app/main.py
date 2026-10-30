from fastapi import FastAPI

from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


@app.get(f"{settings.API_V1_STR}/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}


@app.get(f"{settings.API_V1_STR}/ready", tags=["health"])
def readiness_check():
    return {"status": "ready", "service": settings.PROJECT_NAME}