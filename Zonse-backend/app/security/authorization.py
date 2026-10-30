from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.identity import UserRole
from app.models.property import Property
from app.models.user import User
from app.security.sessions import get_current_user

_ALLOWED_ROLES = frozenset({"seeker", "owner", "agent", "property_manager", "admin"})


def require_roles(*roles: str):
    required_roles = frozenset(roles)
    if not required_roles or not required_roles.issubset(_ALLOWED_ROLES):
        raise ValueError("At least one valid assigned role is required")

    def role_dependency(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        statement = select(UserRole.role).where(UserRole.user_id == user.id)
        assigned_roles = set(db.execute(statement).scalars())
        if not required_roles.intersection(assigned_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return user

    return role_dependency


def require_listing_manager(
    user: User = Depends(require_roles("owner", "agent", "property_manager", "admin")),
) -> User:
    return user


def require_property_owner(
    property_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Property:
    statement = select(Property).where(
        Property.id == property_id,
        Property.owner_id == user.id,
    )
    property_record = db.execute(statement).scalar_one_or_none()
    if property_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    return property_record
