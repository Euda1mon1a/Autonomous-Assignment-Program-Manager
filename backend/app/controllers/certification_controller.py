"""Certification controller for request/response handling."""

from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.certification_service import CertificationService
from app.schemas.certification import (
    CertificationTypeCreate,
    CertificationTypeUpdate,
    CertificationTypeResponse,
    CertificationTypeListResponse,
    PersonCertificationCreate,
    PersonCertificationUpdate,
    PersonCertificationResponse,
    PersonCertificationListResponse,
    PersonCertificationWithTypeListResponse,
    ExpiringCertificationsListResponse,
    ExpiringCertificationResponse,
    ComplianceSummaryResponse,
    PersonComplianceResponse,
    CertificationTypeSummary,
)
from app.schemas.certification import PersonSummary


class CertificationController:
    """Controller for certification endpoints."""

    def __init__(self, db: Session):
        self.service = CertificationService(db)

    # ========================================================================
    # Certification Type Endpoints
    # ========================================================================

    def list_certification_types(
        self,
        active_only: bool = True,
    ) -> CertificationTypeListResponse:
        """List all certification types."""
        result = self.service.list_certification_types(active_only=active_only)
        return CertificationTypeListResponse(items=result["items"], total=result["total"])

    def get_certification_type(self, cert_type_id: UUID) -> CertificationTypeResponse:
        """Get a certification type by ID."""
        cert_type = self.service.get_certification_type(cert_type_id)
        if not cert_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certification type not found",
            )
        return cert_type

    def create_certification_type(
        self,
        cert_type_in: CertificationTypeCreate,
    ) -> CertificationTypeResponse:
        """Create a new certification type."""
        result = self.service.create_certification_type(
            name=cert_type_in.name,
            full_name=cert_type_in.full_name,
            description=cert_type_in.description,
            renewal_period_months=cert_type_in.renewal_period_months,
            required_for_residents=cert_type_in.required_for_residents,
            required_for_faculty=cert_type_in.required_for_faculty,
            required_for_specialties=cert_type_in.required_for_specialties,
            reminder_days_180=cert_type_in.reminder_days_180,
            reminder_days_90=cert_type_in.reminder_days_90,
            reminder_days_30=cert_type_in.reminder_days_30,
            reminder_days_14=cert_type_in.reminder_days_14,
            reminder_days_7=cert_type_in.reminder_days_7,
            is_active=cert_type_in.is_active,
        )
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )
        return result["certification_type"]

    def update_certification_type(
        self,
        cert_type_id: UUID,
        cert_type_in: CertificationTypeUpdate,
    ) -> CertificationTypeResponse:
        """Update a certification type."""
        update_data = cert_type_in.model_dump(exclude_unset=True)
        result = self.service.update_certification_type(cert_type_id, update_data)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
        return result["certification_type"]

    # ========================================================================
    # Person Certification Endpoints
    # ========================================================================

    def list_certifications_for_person(
        self,
        person_id: UUID,
        include_expired: bool = True,
    ) -> PersonCertificationListResponse:
        """List all certifications for a person."""
        result = self.service.list_certifications_for_person(
            person_id=person_id,
            include_expired=include_expired,
        )
        return PersonCertificationListResponse(items=result["items"], total=result["total"])

    def get_person_certification(self, cert_id: UUID) -> PersonCertificationResponse:
        """Get a person certification by ID."""
        cert = self.service.get_person_certification(cert_id)
        if not cert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certification not found",
            )
        return cert

    def create_person_certification(
        self,
        cert_in: PersonCertificationCreate,
    ) -> PersonCertificationResponse:
        """Create a certification for a person."""
        result = self.service.create_person_certification(
            person_id=cert_in.person_id,
            certification_type_id=cert_in.certification_type_id,
            issued_date=cert_in.issued_date,
            expiration_date=cert_in.expiration_date,
            certification_number=cert_in.certification_number,
            verified_by=cert_in.verified_by,
            notes=cert_in.notes,
        )
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )
        return result["certification"]

    def update_person_certification(
        self,
        cert_id: UUID,
        cert_in: PersonCertificationUpdate,
    ) -> PersonCertificationResponse:
        """Update a person's certification."""
        update_data = cert_in.model_dump(exclude_unset=True)
        result = self.service.update_person_certification(cert_id, update_data)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
        return result["certification"]

    def renew_certification(
        self,
        cert_id: UUID,
        new_issued_date: date,
        new_expiration_date: date,
        new_certification_number: Optional[str] = None,
    ) -> PersonCertificationResponse:
        """Renew a certification."""
        result = self.service.renew_certification(
            cert_id=cert_id,
            new_issued_date=new_issued_date,
            new_expiration_date=new_expiration_date,
            new_certification_number=new_certification_number,
        )
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
        return result["certification"]

    def delete_person_certification(self, cert_id: UUID) -> None:
        """Delete a person's certification."""
        result = self.service.delete_person_certification(cert_id)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )

    # ========================================================================
    # Expiration & Compliance Endpoints
    # ========================================================================

    def get_expiring_certifications(
        self,
        days: int = 180,
    ) -> ExpiringCertificationsListResponse:
        """Get certifications expiring within N days."""
        result = self.service.get_expiring_certifications(days=days)

        items = []
        for cert in result["items"]:
            items.append(ExpiringCertificationResponse(
                id=cert.id,
                person=PersonSummary(
                    id=cert.person.id,
                    name=cert.person.name,
                    type=cert.person.type,
                    email=cert.person.email,
                ),
                certification_type=CertificationTypeSummary(
                    id=cert.certification_type.id,
                    name=cert.certification_type.name,
                    full_name=cert.certification_type.full_name,
                ),
                expiration_date=cert.expiration_date,
                days_until_expiration=cert.days_until_expiration,
                status=cert.status,
            ))

        return ExpiringCertificationsListResponse(
            items=items,
            total=result["total"],
            days_threshold=result["days_threshold"],
        )

    def get_compliance_summary(self) -> ComplianceSummaryResponse:
        """Get overall compliance summary."""
        result = self.service.get_compliance_summary()
        return ComplianceSummaryResponse(**result)

    def get_person_compliance(self, person_id: UUID) -> PersonComplianceResponse:
        """Get compliance for a single person."""
        result = self.service.get_person_compliance(person_id)
        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )
        return PersonComplianceResponse(
            person=PersonSummary(
                id=result["person"].id,
                name=result["person"].name,
                type=result["person"].type,
                email=result["person"].email,
            ),
            total_required=result["total_required"],
            total_current=result["total_current"],
            expired=result["expired"],
            expiring_soon=result["expiring_soon"],
            missing=[
                CertificationTypeSummary(id=m.id, name=m.name, full_name=m.full_name)
                for m in result["missing"]
            ],
            is_compliant=result["is_compliant"],
        )
