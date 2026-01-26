"""
Integration tests for compliance service with rules engine.

Tests ACGME compliance checking with real data and rules.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.utils.academic_blocks import get_block_number_for_date


class TestComplianceIntegration:
    """Test compliance service integration."""

    def test_80_hour_rule_enforcement_integration(
        self,
        db: Session,
        sample_resident: Person,
        sample_rotation_template: RotationTemplate,
    ):
        """Test 80-hour rule with real assignments."""
        start_date = date.today()

        # Create blocks for one week
        blocks = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)
                blocks.append(block)
        db.commit()

        # Create assignments (all blocks = violation)
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # Check compliance
        # compliance_service = ComplianceService(db)
        # result = compliance_service.check_80_hour_rule(
        #     person_id=sample_resident.id,
        #     start_date=start_date,
        # )
        # assert result.is_compliant == False

    def test_1_in_7_rule_enforcement_integration(
        self,
        db: Session,
        sample_resident: Person,
        sample_rotation_template: RotationTemplate,
    ):
        """Test 1-in-7 rule with real assignments."""
        start_date = date.today()

        # Create continuous assignments (violation)
        for i in range(14):
            current_date = start_date + timedelta(days=i)
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)
                db.commit()

                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=sample_resident.id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        # Check compliance
        # Should detect violation of 1-in-7 rule

    def test_supervision_ratio_integration(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
    ):
        """Test supervision ratio compliance."""
        # Create supervised rotation
        template = RotationTemplate(
            id=uuid4(),
            name="Supervised Clinic",
            rotation_type="outpatient",
            abbreviation="SUP",
            max_residents=4,
            supervision_required=True,
            max_supervision_ratio=2,
        )
        db.add(template)
        db.commit()

        # Create block
        block = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)
        db.commit()

        # Assign residents without adequate supervision
        for resident in sample_residents[:3]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                rotation_template_id=template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # Check supervision compliance
        # Should detect inadequate supervision

    def test_rolling_average_calculation_integration(
        self,
        db: Session,
        sample_resident: Person,
        sample_rotation_template: RotationTemplate,
    ):
        """Test rolling 4-week average calculation."""
        start_date = date.today()

        # Create 4 weeks of assignments with varying load
        for i in range(28):
            current_date = start_date + timedelta(days=i)
            # Use Thursday-Wednesday aligned block number calculation
            block_number, _ = get_block_number_for_date(current_date)
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=tod,
                    block_number=block_number,
                )
                db.add(block)
                db.commit()

                # Vary assignment pattern
                if i % 3 != 0:  # Work 2 out of 3
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=block.id,
                        person_id=sample_resident.id,
                        rotation_template_id=sample_rotation_template.id,
                        role="primary",
                    )
                    db.add(assignment)
        db.commit()

        # Calculate rolling average
        # Should compute 4-week rolling average correctly
