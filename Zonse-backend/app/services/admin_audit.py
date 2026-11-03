from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.models.admin_audit import AdminActionLog


def record_admin_action(
    db: Session,
    *,
    actor_id: int,
    action: str,
    entity_type: str,
    entity_id: int | str,
    before_data: dict[str, Any] | None,
    after_data: dict[str, Any] | None,
) -> None:
    db.add(
        AdminActionLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            before_data=jsonable_encoder(before_data),
            after_data=jsonable_encoder(after_data),
        )
    )
