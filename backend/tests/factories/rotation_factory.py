"""Factory for creating test RotationTemplate instances."""

from typing import Optional
from uuid import uuid4

from faker import Faker
from sqlalchemy.orm import Session

from app.models.rotation_template import RotationTemplate

fake = Faker()


class RotationFactory:
    """Factory for creating RotationTemplate instances with random data."""

    @staticmethod
    def create_rotation_template(
        db: Session,
        name: str | None = None,
        activity_type: str = "clinic",
        abbreviation: str | None = None,
        max_residents: int | None = None,
        supervision_required: bool = True,
        max_supervision_ratio: int = 4,
        leave_eligible: bool = True,
        requires_specialty: str | None = None,
        requires_procedure_credential: bool = False,
    ) -> RotationTemplate:
        """
        Create a single rotation template.

        Args:
            db: Database session
            name: Template name (random if not provided)
            activity_type: "clinic", "inpatient", "procedure", "conference", "outpatient"
            abbreviation: Short abbreviation for Excel export
            max_residents: Maximum residents allowed (capacity constraint)
            supervision_required: Whether supervision is required
            max_supervision_ratio: Maximum residents per faculty (1:N)
            leave_eligible: Whether scheduled leave is allowed on this rotation
            requires_specialty: Specialty requirement (e.g., "Sports Medicine")
            requires_procedure_credential: Whether procedure credential required

        Returns:
            RotationTemplate: Created template instance
        """
        if name is None:
            activity_types_names = {
                "clinic": f"{fake.random_element(['PGY-1', 'PGY-2', 'General'])} Clinic",
                "inpatient": "FMIT Inpatient",
                "procedure": f"{fake.random_element(['Minor', 'Major'])} Procedures",
                "conference": f"{fake.random_element(['Grand Rounds', 'Case Conference', 'Didactics'])}",
                "outpatient": "Outpatient Services",
            }
            name = activity_types_names.get(
                activity_type, f"{activity_type.title()} Rotation"
            )

        if abbreviation is None:
            abbreviation = "".join(word[0].upper() for word in name.split()[:3])
            abbreviation = abbreviation[:10]  # Max 10 chars

        template = RotationTemplate(
            id=uuid4(),
            name=name,
            activity_type=activity_type,
            abbreviation=abbreviation,
            max_residents=max_residents,
            supervision_required=supervision_required,
            max_supervision_ratio=max_supervision_ratio,
            leave_eligible=leave_eligible,
            requires_specialty=requires_specialty,
            requires_procedure_credential=requires_procedure_credential,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def create_clinic_template(
        db: Session,
        pgy_level: int | None = None,
        max_residents: int = 4,
    ) -> RotationTemplate:
        """
        Create a clinic rotation template.

        Args:
            db: Database session
            pgy_level: PGY level for clinic (None for general clinic)
            max_residents: Maximum residents (default 4)

        Returns:
            RotationTemplate: Created clinic template
        """
        if pgy_level:
            name = f"PGY-{pgy_level} Clinic"
            abbreviation = f"C{pgy_level}"
        else:
            name = "General Clinic"
            abbreviation = "CL"

        return RotationFactory.create_rotation_template(
            db,
            name=name,
            activity_type="outpatient",  # Engine default filter
            abbreviation=abbreviation,
            max_residents=max_residents,
            supervision_required=True,
            max_supervision_ratio=4 if pgy_level == 1 else 4,
            leave_eligible=True,
        )

    @staticmethod
    def create_fmit_template(db: Session) -> RotationTemplate:
        """
        Create FMIT (Family Medicine Inpatient Training) template.

        FMIT has special requirements:
        - 24/7 coverage required
        - Leave NOT eligible (requires coverage)
        - Strict supervision ratios

        Returns:
            RotationTemplate: FMIT template
        """
        return RotationFactory.create_rotation_template(
            db,
            name="FMIT Inpatient",
            activity_type="inpatient",
            abbreviation="FMIT",
            max_residents=None,  # No hard cap, staffing driven
            supervision_required=True,
            max_supervision_ratio=4,
            leave_eligible=False,  # Coverage-critical, not leave-eligible
        )

    @staticmethod
    def create_sports_medicine_template(db: Session) -> RotationTemplate:
        """
        Create Sports Medicine clinic template.

        Requires:
        - Sports Medicine specialty
        - Procedure credentials

        Returns:
            RotationTemplate: Sports Medicine template
        """
        return RotationFactory.create_rotation_template(
            db,
            name="Sports Medicine Clinic",
            activity_type="outpatient",
            abbreviation="SM",
            max_residents=3,
            supervision_required=True,
            max_supervision_ratio=4,
            leave_eligible=True,
            requires_specialty="Sports Medicine",
            requires_procedure_credential=True,
        )

    @staticmethod
    def create_procedure_template(db: Session) -> RotationTemplate:
        """
        Create procedure rotation template.

        Returns:
            RotationTemplate: Procedure template
        """
        return RotationFactory.create_rotation_template(
            db,
            name="Procedure Clinic",
            activity_type="procedure",
            abbreviation="PROC",
            max_residents=2,  # Limited by procedure room capacity
            supervision_required=True,
            max_supervision_ratio=2,  # Closer supervision for procedures
            leave_eligible=True,
            requires_procedure_credential=True,
        )

    @staticmethod
    def create_conference_template(db: Session) -> RotationTemplate:
        """
        Create conference/didactics template.

        Returns:
            RotationTemplate: Conference template
        """
        return RotationFactory.create_rotation_template(
            db,
            name="Grand Rounds",
            activity_type="conference",
            abbreviation="CONF",
            max_residents=None,  # No capacity limit
            supervision_required=False,  # Group learning
            leave_eligible=False,  # Mandatory attendance
        )

    @staticmethod
    def create_admin_template(db: Session) -> RotationTemplate:
        """
        Create administrative rotation template (for chiefs).

        Returns:
            RotationTemplate: Admin template
        """
        return RotationFactory.create_rotation_template(
            db,
            name="Administrative",
            activity_type="outpatient",
            abbreviation="ADMIN",
            max_residents=1,  # Usually one chief at a time
            supervision_required=False,
            leave_eligible=True,
        )

    @staticmethod
    def create_standard_template_set(db: Session) -> dict[str, RotationTemplate]:
        """
        Create a standard set of rotation templates for testing.

        Returns:
            dict[str, RotationTemplate]: Dictionary of template name -> template
        """
        templates = {
            "pgy1_clinic": RotationFactory.create_clinic_template(db, pgy_level=1),
            "pgy2_clinic": RotationFactory.create_clinic_template(db, pgy_level=2),
            "pgy3_clinic": RotationFactory.create_clinic_template(db, pgy_level=3),
            "fmit": RotationFactory.create_fmit_template(db),
            "sports_medicine": RotationFactory.create_sports_medicine_template(db),
            "procedures": RotationFactory.create_procedure_template(db),
            "conference": RotationFactory.create_conference_template(db),
            "admin": RotationFactory.create_admin_template(db),
        }
        return templates

    @staticmethod
    def create_batch_templates(
        db: Session,
        count: int = 5,
        activity_types: list[str] | None = None,
    ) -> list[RotationTemplate]:
        """
        Create multiple rotation templates.

        Args:
            db: Database session
            count: Number of templates to create
            activity_types: List of activity types to use (cycles through if count > len)

        Returns:
            list[RotationTemplate]: List of created templates
        """
        if activity_types is None:
            activity_types = ["clinic", "inpatient", "procedure", "conference"]

        templates = []
        for i in range(count):
            activity_type = activity_types[i % len(activity_types)]
            template = RotationFactory.create_rotation_template(
                db, activity_type=activity_type
            )
            templates.append(template)

        return templates
