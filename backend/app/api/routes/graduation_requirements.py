import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import get_scheduler_user
from app.schemas.graduation_requirement import (
    GraduationRequirement,
    GraduationRequirementCreate,
    GraduationRequirementUpdate,
)
from app.services.graduation_requirement_service import graduation_requirement_service

router = APIRouter()


@router.get("/pgy/{pgy_level}", response_model=list[GraduationRequirement])
def read_graduation_requirements_by_pgy(
    pgy_level: int,
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve graduation requirements for a specific PGY level.
    """
    return graduation_requirement_service.get_by_pgy(db, pgy_level=pgy_level)


@router.post("/", response_model=GraduationRequirement)
def create_graduation_requirement(
    *,
    db: Session = Depends(deps.get_db),
    req_in: GraduationRequirementCreate,
    current_user: dict = Depends(get_scheduler_user),
) -> Any:
    """
    Create a new graduation requirement. Only available to superusers/coordinators.
    """
    existing = graduation_requirement_service.get_by_pgy_and_template(
        db, pgy_level=req_in.pgy_level, rotation_template_id=req_in.rotation_template_id
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A requirement for this PGY level and template already exists.",
        )
    return graduation_requirement_service.create(db, obj_in=req_in)


@router.put("/{req_id}", response_model=GraduationRequirement)
def update_graduation_requirement(
    *,
    db: Session = Depends(deps.get_db),
    req_id: uuid.UUID,
    req_in: GraduationRequirementUpdate,
    current_user: dict = Depends(get_scheduler_user),
) -> Any:
    """
    Update a graduation requirement. Only available to superusers/coordinators.
    """
    requirement = graduation_requirement_service.get_by_id(db, req_id=req_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Graduation requirement not found")
    return graduation_requirement_service.update(db, db_obj=requirement, obj_in=req_in)


@router.delete("/{req_id}")
def delete_graduation_requirement(
    *,
    db: Session = Depends(deps.get_db),
    req_id: uuid.UUID,
    current_user: dict = Depends(get_scheduler_user),
) -> Any:
    """
    Delete a graduation requirement. Only available to superusers/coordinators.
    """
    requirement = graduation_requirement_service.get_by_id(db, req_id=req_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Graduation requirement not found")
    graduation_requirement_service.delete(db, db_obj=requirement)
    return {"message": "Successfully deleted"}
