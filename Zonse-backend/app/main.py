import logging

from fastapi import FastAPI
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import check_database_connection

logger = logging.getLogger(__name__)

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
    try:
        check_database_connection()
    except SQLAlchemyError:
        logger.warning("Database readiness check failed")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from None

    return {"status": "ready", "service": settings.PROJECT_NAME}