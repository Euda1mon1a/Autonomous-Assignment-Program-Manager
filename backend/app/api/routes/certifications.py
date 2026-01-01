"""Certifications API routes.

Provides endpoints for managing personnel certifications (BLS, ACLS, PALS, etc.)
with expiration tracking and compliance monitoring.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.dependencies.role_filter import require_admin
from app.controllers.certification_controller import CertificationController
from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.certification import (
    CertificationTypeCreate,
    CertificationTypeListResponse,
    CertificationTypeResponse,
    CertificationTypeUpdate,
    ComplianceSummaryResponse,
    ExpiringCertificationsListResponse,
    PersonCertificationCreate,
    PersonCertificationListResponse,
    PersonCertificationResponse,
    PersonCertificationUpdate,
    PersonComplianceResponse,
)

router = APIRouter()


# ============================================================================
# Certification Type Endpoints
# ============================================================================


@router.get("/types", response_model=CertificationTypeListResponse)
async def list_certification_types(
    active_only: bool = Query(True, description="Only show active certification types"),
    db=Depends(get_async_db),
):
    """List all certification types (BLS, ACLS, PALS, etc.)."""
    controller = CertificationController(db)
    return controller.list_certification_types(active_only=active_only)


@router.get("/types/{cert_type_id}", response_model=CertificationTypeResponse)
async def get_certification_type(
    cert_type_id: UUID,
    db=Depends(get_async_db),
):
    """Get a certification type by ID."""
    controller = CertificationController(db)
    return controller.get_certification_type(cert_type_id)


@router.post("/types", response_model=CertificationTypeResponse, status_code=201)
async def create_certification_type(
    cert_type_in: CertificationTypeCreate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new certification type. Requires authentication."""
    controller = CertificationController(db)
    return controller.create_certification_type(cert_type_in)


@router.put("/types/{cert_type_id}", response_model=CertificationTypeResponse)
async def update_certification_type(
    cert_type_id: UUID,
    cert_type_in: CertificationTypeUpdate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a certification type. Requires authentication."""
    controller = CertificationController(db)
    return controller.update_certification_type(cert_type_id, cert_type_in)


# ============================================================================
# Expiration & Compliance Endpoints
# ============================================================================


@router.get("/expiring", response_model=ExpiringCertificationsListResponse)
async def get_expiring_certifications(
    days: int = Query(180, description="Days to look ahead (default 6 months)"),
    db=Depends(get_async_db),
):
    """Get all certifications expiring within N days."""
    controller = CertificationController(db)
    return controller.get_expiring_certifications(days=days)


@router.get("/compliance", response_model=ComplianceSummaryResponse)
async def get_compliance_summary(
    db=Depends(get_async_db),
):
    """Get overall certification compliance summary."""
    controller = CertificationController(db)
    return controller.get_compliance_summary()


@router.get("/compliance/{person_id}", response_model=PersonComplianceResponse)
async def get_person_compliance(
    person_id: UUID,
    db=Depends(get_async_db),
):
    """Get certification compliance for a specific person."""
    controller = CertificationController(db)
    return controller.get_person_compliance(person_id)


# ============================================================================
# Person Certification Endpoints
# ============================================================================


@router.get("/by-person/{person_id}", response_model=PersonCertificationListResponse)
async def list_certifications_for_person(
    person_id: UUID,
    include_expired: bool = Query(True, description="Include expired certifications"),
    db=Depends(get_async_db),
):
    """List all certifications for a specific person."""
    controller = CertificationController(db)
    return controller.list_certifications_for_person(
        person_id=person_id,
        include_expired=include_expired,
    )


@router.get("/{cert_id}", response_model=PersonCertificationResponse)
async def get_person_certification(
    cert_id: UUID,
    db=Depends(get_async_db),
):
    """Get a person certification by ID."""
    controller = CertificationController(db)
    return controller.get_person_certification(cert_id)


@router.post("", response_model=PersonCertificationResponse, status_code=201)
async def create_person_certification(
    cert_in: PersonCertificationCreate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a certification for a person. Requires authentication."""
    controller = CertificationController(db)
    return controller.create_person_certification(cert_in)


@router.put("/{cert_id}", response_model=PersonCertificationResponse)
async def update_person_certification(
    cert_id: UUID,
    cert_in: PersonCertificationUpdate,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a person's certification. Requires authentication."""
    controller = CertificationController(db)
    return controller.update_person_certification(cert_id, cert_in)


class RenewalRequest(BaseModel):
    """Request body for renewing a certification."""

    new_issued_date: date
    new_expiration_date: date
    new_certification_number: str | None = None


@router.post("/{cert_id}/renew", response_model=PersonCertificationResponse)
async def renew_certification(
    cert_id: UUID,
    renewal: RenewalRequest,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Renew a certification with new dates. Requires authentication."""
    controller = CertificationController(db)
    return controller.renew_certification(
        cert_id=cert_id,
        new_issued_date=renewal.new_issued_date,
        new_expiration_date=renewal.new_expiration_date,
        new_certification_number=renewal.new_certification_number,
    )


@router.delete("/{cert_id}", status_code=204)
async def delete_person_certification(
    cert_id: UUID,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a person's certification. Requires authentication."""
    controller = CertificationController(db)
    controller.delete_person_certification(cert_id)


# ============================================================================
# Admin Endpoints
# ============================================================================


@router.post("/admin/send-reminders")
async def trigger_certification_reminders(
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Manually trigger certification expiration check and send reminders.

    This runs the same job that normally runs daily at 6 AM.
    Requires admin role.
    """
    from app.services.certification_service import CertificationService

    service = CertificationService(db)

    # Update all statuses
    updated = service.update_all_statuses()

    # Get counts
    expiring = service.get_expiring_certifications(days=180)
    expired = service.get_expired_certifications()

    return {
        "status": "success",
        "statuses_updated": updated,
        "expiring_count": expiring["total"],
        "expired_count": expired["total"],
        "message": "Certification check completed. Email reminders require SMTP configuration.",
    }
