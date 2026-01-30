"""Service for faculty schedule preferences (clinic/call)."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.faculty_schedule_preference import (
    FacultyPreferenceType,
    FacultySchedulePreference,
)
from app.schemas.faculty_schedule_preference import (
    FacultySchedulePreferenceCreate,
    FacultySchedulePreferenceUpdate,
)


class FacultySchedulePreferenceService:
    """Business logic for faculty schedule preferences."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_preferences(
        self,
        person_id: UUID | None = None,
        preference_type: FacultyPreferenceType | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict:
        query = self.db.query(FacultySchedulePreference)

        if person_id:
            query = query.filter(FacultySchedulePreference.person_id == person_id)
        if preference_type:
            query = query.filter(
                FacultySchedulePreference.preference_type == preference_type
            )
        if is_active is not None:
            query = query.filter(FacultySchedulePreference.is_active.is_(is_active))

        total = (
            query.with_entities(func.count(FacultySchedulePreference.id)).scalar() or 0
        )

        items = (
            query.order_by(
                FacultySchedulePreference.person_id,
                FacultySchedulePreference.rank,
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_preference(self, preference_id: UUID) -> FacultySchedulePreference | None:
        return (
            self.db.query(FacultySchedulePreference).filter_by(id=preference_id).first()
        )

    def create_preference(
        self, pref_in: FacultySchedulePreferenceCreate
    ) -> FacultySchedulePreference:
        existing_rank = (
            self.db.query(FacultySchedulePreference)
            .filter(
                FacultySchedulePreference.person_id == pref_in.person_id,
                FacultySchedulePreference.rank == pref_in.rank,
            )
            .first()
        )
        if existing_rank:
            raise HTTPException(
                status_code=409,
                detail="Preference rank already exists for this faculty",
            )

        if pref_in.is_active:
            active_count = (
                self.db.query(func.count(FacultySchedulePreference.id))
                .filter(
                    FacultySchedulePreference.person_id == pref_in.person_id,
                    FacultySchedulePreference.is_active.is_(True),
                )
                .scalar()
                or 0
            )
            if active_count >= 2:
                raise HTTPException(
                    status_code=400,
                    detail="Faculty already has two active preferences",
                )

        pref = FacultySchedulePreference(**pref_in.model_dump())
        self.db.add(pref)
        self.db.commit()
        self.db.refresh(pref)
        return pref

    def update_preference(
        self,
        preference_id: UUID,
        pref_in: FacultySchedulePreferenceUpdate,
    ) -> FacultySchedulePreference | None:
        pref = self.get_preference(preference_id)
        if not pref:
            return None

        data = pref_in.model_dump(exclude_unset=True)

        if "rank" in data and data["rank"] != pref.rank:
            existing_rank = (
                self.db.query(FacultySchedulePreference)
                .filter(
                    FacultySchedulePreference.person_id == pref.person_id,
                    FacultySchedulePreference.rank == data["rank"],
                )
                .first()
            )
            if existing_rank:
                raise HTTPException(
                    status_code=409,
                    detail="Preference rank already exists for this faculty",
                )

        if data.get("is_active") is True:
            active_count = (
                self.db.query(func.count(FacultySchedulePreference.id))
                .filter(
                    FacultySchedulePreference.person_id == pref.person_id,
                    FacultySchedulePreference.is_active.is_(True),
                    FacultySchedulePreference.id != pref.id,
                )
                .scalar()
                or 0
            )
            if active_count >= 2:
                raise HTTPException(
                    status_code=400,
                    detail="Faculty already has two active preferences",
                )

        for key, value in data.items():
            setattr(pref, key, value)

        self.db.commit()
        self.db.refresh(pref)
        return pref

    def delete_preference(self, preference_id: UUID) -> bool:
        pref = self.get_preference(preference_id)
        if not pref:
            return False
        pref.is_active = False
        self.db.commit()
        return True
