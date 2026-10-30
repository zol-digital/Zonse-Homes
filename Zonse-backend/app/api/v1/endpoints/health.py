import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import check_database_connection

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}


@router.get("/ready")
def readiness_check():
    try:
        check_database_connection()
    except SQLAlchemyError:
        logger.warning("Database readiness check failed")
        raise HTTPException(status_code=503, detail="Database unavailable") from None

    return {"status": "ready", "service": settings.PROJECT_NAME}
