"""Service for institutional events."""

from datetime import date
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.institutional_event import InstitutionalEvent
from app.schemas.institutional_event import (
    InstitutionalEventCreate,
    InstitutionalEventUpdate,
)


class InstitutionalEventService:
    """Business logic for institutional events."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_events(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        event_type: str | None = None,
        applies_to: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict:
        query = self.db.query(InstitutionalEvent)

        if start_date:
            query = query.filter(InstitutionalEvent.end_date >= start_date)
        if end_date:
            query = query.filter(InstitutionalEvent.start_date <= end_date)
        if event_type:
            query = query.filter(InstitutionalEvent.event_type == event_type)
        if applies_to:
            query = query.filter(InstitutionalEvent.applies_to == applies_to)
        if is_active is not None:
            query = query.filter(InstitutionalEvent.is_active.is_(is_active))

        total = query.with_entities(func.count(InstitutionalEvent.id)).scalar() or 0

        items = (
            query.order_by(
                InstitutionalEvent.start_date, InstitutionalEvent.time_of_day
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_event(self, event_id: UUID) -> InstitutionalEvent | None:
        return self.db.query(InstitutionalEvent).filter_by(id=event_id).first()

    def create_event(self, event_in: InstitutionalEventCreate) -> InstitutionalEvent:
        event = InstitutionalEvent(**event_in.model_dump())
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def update_event(
        self, event_id: UUID, event_in: InstitutionalEventUpdate
    ) -> InstitutionalEvent | None:
        event = self.get_event(event_id)
        if not event:
            return None

        data = event_in.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(event, key, value)

        self.db.commit()
        self.db.refresh(event)
        return event

    def delete_event(self, event_id: UUID) -> bool:
        event = self.get_event(event_id)
        if not event:
            return False
        event.is_active = False
        self.db.commit()
        return True
