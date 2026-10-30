from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserProfileUpdate, UserResponse
from app.security.credentials import normalize_full_name, normalize_phone_number
from app.security.csrf import validate_csrf_origin
from app.security.sessions import get_current_user

router = APIRouter(dependencies=[Depends(validate_csrf_origin)])


@router.get("/users/me", response_model=UserResponse)
def get_my_profile(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/users/me", response_model=UserResponse)
def update_my_profile(
    payload: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    changes = payload.model_dump(exclude_unset=True)

    if "full_name" in changes:
        user.full_name = normalize_full_name(changes["full_name"])

    if "phone_number" in changes:
        phone_number = normalize_phone_number(changes["phone_number"])
        if phone_number != user.phone_number:
            user.phone_verified_at = None
        user.phone_number = phone_number

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except SQLAlchemyError:
        db.rollback()
        raise

    return user
