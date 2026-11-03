from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.reference_data import PropertyCategory


def require_active_category(db: Session, category_slug: str) -> PropertyCategory:
    category = db.get(PropertyCategory, category_slug)
    if category is None or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Property category is unavailable",
        )
    return category
