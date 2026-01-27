"""Resident weekly requirement API routes.

Provides endpoints for:
- CRUD operations on resident weekly requirements
- Get requirements by rotation template
- Bulk operations for multiple templates

ACGME Compliance:
- Minimum 2 FM clinic half-days per week on outpatient rotations
- Protected academic time (Wednesday AM conference)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.resident_weekly_requirement import ResidentWeeklyRequirement
from app.models.rotation_template import RotationTemplate
from app.models.user import User
from app.schemas.resident_weekly_requirement import (
    ResidentWeeklyRequirementCreate,
    ResidentWeeklyRequirementListResponse,
    ResidentWeeklyRequirementResponse,
    ResidentWeeklyRequirementUpdate,
    ResidentWeeklyRequirementWithTemplate,
)

router = APIRouter()
logger = get_logger(__name__)


# =============================================================================
# Collection-level endpoints
# =============================================================================


@router.get("", response_model=ResidentWeeklyRequirementListResponse)
async def list_resident_weekly_requirements(
    rotation_type: str | None = Query(
        None, description="Filter by rotation template rotation type"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResidentWeeklyRequirementListResponse:
    """List all resident weekly requirements, optionally filtered by rotation type.

    Args:
        rotation_type: Filter by rotation template rotation type (e.g., 'outpatient')
        db: Database session
        current_user: Current authenticated user

    Returns:
        ResidentWeeklyRequirementListResponse with requirements and count
    """
    query = (
        select(ResidentWeeklyRequirement)
        .options(selectinload(ResidentWeeklyRequirement.rotation_template))
        .join(RotationTemplate)
    )

    if rotation_type:
        query = query.where(RotationTemplate.rotation_type == rotation_type)

    # Exclude requirements for archived templates
    query = query.where(RotationTemplate.is_archived == False)

    result = db.execute(query)
    requirements = list(result.scalars().all())

    items = [
        ResidentWeeklyRequirementResponse.from_orm_with_computed(req)
        for req in requirements
    ]

    return ResidentWeeklyRequirementListResponse(items=items, total=len(items))


@router.post("", response_model=ResidentWeeklyRequirementResponse, status_code=201)
async def create_resident_weekly_requirement(
    requirement_in: ResidentWeeklyRequirementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResidentWeeklyRequirementResponse:
    """Create a new resident weekly requirement for a rotation template.

    Args:
        requirement_in: Requirement data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created ResidentWeeklyRequirementResponse

    Raises:
        404: Template not found
        400: Requirement already exists for template
    """
    # Verify template exists
    template = await db.get(RotationTemplate, requirement_in.rotation_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    # Check if requirement already exists
    existing = db.execute(
        select(ResidentWeeklyRequirement).where(
            ResidentWeeklyRequirement.rotation_template_id
            == requirement_in.rotation_template_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Weekly requirement already exists for this template. Use PUT to update.",
        )

    # Create requirement
    requirement = ResidentWeeklyRequirement(**requirement_in.model_dump())
    db.add(requirement)
    db.commit()
    db.refresh(requirement)

    logger.info(
        f"Created resident weekly requirement for template {template.name}",
        extra={"template_id": str(template.id), "user_id": str(current_user.id)},
    )

    return ResidentWeeklyRequirementResponse.from_orm_with_computed(requirement)


# =============================================================================
# By Template endpoints
# =============================================================================


@router.get(
    "/by-template/{template_id}",
    response_model=ResidentWeeklyRequirementWithTemplate,
)
async def get_requirement_by_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get weekly requirement for a specific rotation template.

    Args:
        template_id: UUID of the rotation template
        db: Database session
        current_user: Current authenticated user

    Returns:
        ResidentWeeklyRequirementWithTemplate

    Raises:
        404: Template not found or no requirement configured
    """
    # Verify template exists and get requirement
    template = await db.get(RotationTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    result = db.execute(
        select(ResidentWeeklyRequirement).where(
            ResidentWeeklyRequirement.rotation_template_id == template_id
        )
    )
    requirement = result.scalar_one_or_none()

    if not requirement:
        raise HTTPException(
            status_code=404,
            detail="No weekly requirement configured for this template",
        )

    # Build response with template info
    base = ResidentWeeklyRequirementResponse.from_orm_with_computed(requirement)
    return ResidentWeeklyRequirementWithTemplate(
        **base.model_dump(),
        template_name=template.name,
        template_rotation_type=template.rotation_type,
    )


@router.put(
    "/by-template/{template_id}",
    response_model=ResidentWeeklyRequirementWithTemplate,
)
async def upsert_requirement_by_template(
    template_id: UUID,
    requirement_in: ResidentWeeklyRequirementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create or update weekly requirement for a rotation template (upsert).

    If no requirement exists, creates one with defaults for fields not provided.
    If requirement exists, updates only the provided fields.

    Args:
        template_id: UUID of the rotation template
        requirement_in: Requirement update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        ResidentWeeklyRequirementWithTemplate

    Raises:
        404: Template not found
    """
    # Verify template exists
    template = await db.get(RotationTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    # Check for existing requirement
    result = db.execute(
        select(ResidentWeeklyRequirement).where(
            ResidentWeeklyRequirement.rotation_template_id == template_id
        )
    )
    requirement = result.scalar_one_or_none()

    if requirement:
        # Update existing
        update_data = requirement_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(requirement, field, value)
        action = "Updated"
    else:
        # Create new with defaults
        create_data = requirement_in.model_dump(exclude_unset=True)
        create_data["rotation_template_id"] = template_id
        requirement = ResidentWeeklyRequirement(**create_data)
        db.add(requirement)
        action = "Created"

    db.commit()
    db.refresh(requirement)

    logger.info(
        f"{action} resident weekly requirement for template {template.name}",
        extra={"template_id": str(template.id), "user_id": str(current_user.id)},
    )

    base = ResidentWeeklyRequirementResponse.from_orm_with_computed(requirement)
    return ResidentWeeklyRequirementWithTemplate(
        **base.model_dump(),
        template_name=template.name,
        template_rotation_type=template.rotation_type,
    )


@router.delete("/by-template/{template_id}", status_code=204)
async def delete_requirement_by_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete weekly requirement for a rotation template.

    Args:
        template_id: UUID of the rotation template
        db: Database session
        current_user: Current authenticated user

    Raises:
        404: Template or requirement not found
    """
    # Verify template exists
    template = await db.get(RotationTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Rotation template not found")

    result = db.execute(
        select(ResidentWeeklyRequirement).where(
            ResidentWeeklyRequirement.rotation_template_id == template_id
        )
    )
    requirement = result.scalar_one_or_none()

    if not requirement:
        raise HTTPException(
            status_code=404,
            detail="No weekly requirement found for this template",
        )

    db.delete(requirement)
    db.commit()

    logger.info(
        f"Deleted resident weekly requirement for template {template.name}",
        extra={"template_id": str(template.id), "user_id": str(current_user.id)},
    )


# =============================================================================
# Single Requirement endpoints (by ID)
# =============================================================================


@router.get("/{requirement_id}", response_model=ResidentWeeklyRequirementResponse)
async def get_resident_weekly_requirement(
    requirement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResidentWeeklyRequirementResponse:
    """Get a resident weekly requirement by ID.

    Args:
        requirement_id: UUID of the requirement
        db: Database session
        current_user: Current authenticated user

    Returns:
        ResidentWeeklyRequirementResponse

    Raises:
        404: Requirement not found
    """
    requirement = await db.get(ResidentWeeklyRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    return ResidentWeeklyRequirementResponse.from_orm_with_computed(requirement)


@router.put("/{requirement_id}", response_model=ResidentWeeklyRequirementResponse)
async def update_resident_weekly_requirement(
    requirement_id: UUID,
    requirement_in: ResidentWeeklyRequirementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResidentWeeklyRequirementResponse:
    """Update an existing resident weekly requirement.

    Args:
        requirement_id: UUID of the requirement
        requirement_in: Update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated ResidentWeeklyRequirementResponse

    Raises:
        404: Requirement not found
    """
    requirement = await db.get(ResidentWeeklyRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    update_data = requirement_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(requirement, field, value)

    db.commit()
    db.refresh(requirement)

    logger.info(
        f"Updated resident weekly requirement {requirement_id}",
        extra={"requirement_id": str(requirement_id), "user_id": str(current_user.id)},
    )

    return ResidentWeeklyRequirementResponse.from_orm_with_computed(requirement)


@router.delete("/{requirement_id}", status_code=204)
async def delete_resident_weekly_requirement(
    requirement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a resident weekly requirement.

    Args:
        requirement_id: UUID of the requirement
        db: Database session
        current_user: Current authenticated user

    Raises:
        404: Requirement not found
    """
    requirement = await db.get(ResidentWeeklyRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    db.delete(requirement)
    db.commit()

    logger.info(
        f"Deleted resident weekly requirement {requirement_id}",
        extra={"requirement_id": str(requirement_id), "user_id": str(current_user.id)},
    )


# =============================================================================
# Bulk Operations
# =============================================================================


@router.post("/bulk/outpatient-defaults", response_model=dict)
async def apply_outpatient_defaults(
    template_ids: list[UUID] | None = None,
    fm_clinic_min: int = Query(2, ge=0, le=10, description="Min FM clinic half-days"),
    fm_clinic_max: int = Query(3, ge=0, le=10, description="Max FM clinic half-days"),
    dry_run: bool = Query(False, description="If true, validate only without changes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Apply ACGME-compliant defaults to outpatient rotation templates.

    If template_ids provided, applies to those templates.
    If not provided, applies to all outpatient templates without requirements.

    Default configuration:
    - fm_clinic_min_per_week = 2 (ACGME requirement)
    - fm_clinic_max_per_week = 3
    - academics_required = True
    - protected_slots = {"wed_am": "conference"}

    Args:
        template_ids: Optional list of template IDs (defaults to all outpatient)
        fm_clinic_min: Minimum FM clinic half-days per week
        fm_clinic_max: Maximum FM clinic half-days per week
        dry_run: If true, don't save changes
        db: Database session
        current_user: Current authenticated user

    Returns:
        Dict with created/updated counts and affected template IDs
    """
    # Query templates
    query = select(RotationTemplate).where(
        RotationTemplate.is_archived == False,
        RotationTemplate.rotation_type == "outpatient",
    )

    if template_ids:
        query = query.where(RotationTemplate.id.in_(template_ids))

    result = db.execute(query)
    templates = list(result.scalars().all())

    created = []
    updated = []
    skipped = []

    for template in templates:
        # Check for existing requirement
        existing_result = db.execute(
            select(ResidentWeeklyRequirement).where(
                ResidentWeeklyRequirement.rotation_template_id == template.id
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Update if explicitly requested
            if template_ids:
                existing.fm_clinic_min_per_week = fm_clinic_min
                existing.fm_clinic_max_per_week = fm_clinic_max
                existing.academics_required = True
                if not existing.protected_slots:
                    existing.protected_slots = {"wed_am": "conference"}
                updated.append(str(template.id))
            else:
                skipped.append(str(template.id))
        else:
            # Create new requirement
            requirement = ResidentWeeklyRequirement(
                rotation_template_id=template.id,
                fm_clinic_min_per_week=fm_clinic_min,
                fm_clinic_max_per_week=fm_clinic_max,
                specialty_min_per_week=0,
                specialty_max_per_week=10,
                academics_required=True,
                protected_slots={"wed_am": "conference"},
                allowed_clinic_days=[],  # All weekdays allowed
            )
            db.add(requirement)
            created.append(str(template.id))

    if not dry_run:
        db.commit()
        logger.info(
            f"Applied outpatient defaults: {len(created)} created, {len(updated)} updated",
            extra={"user_id": str(current_user.id)},
        )

    return {
        "dry_run": dry_run,
        "templates_processed": len(templates),
        "created": len(created),
        "created_ids": created,
        "updated": len(updated),
        "updated_ids": updated,
        "skipped": len(skipped),
        "skipped_ids": skipped,
    }
