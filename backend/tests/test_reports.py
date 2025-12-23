"""Tests for PDF report generation service."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.schemas.reports import (
    AnalyticsReportRequest,
    ComplianceReportRequest,
    ScheduleReportRequest,
)
from app.services.reports.pdf_generator import PDFReportGenerator
from app.services.reports.templates.analytics_report import AnalyticsReportTemplate
from app.services.reports.templates.compliance_report import ComplianceReportTemplate
from app.services.reports.templates.schedule_report import ScheduleReportTemplate


@pytest.fixture
def sample_residents(db: Session) -> list[Person]:
    """Create sample residents for testing."""
    residents = []
    for i in range(3):
        resident = Person(
            id=uuid4(),
            name=f"Resident {i + 1}",
            type="resident",
            pgy_level=i + 1,
            email=f"resident{i + 1}@test.org",
        )
        db.add(resident)
        residents.append(resident)
    db.commit()
    return residents


@pytest.fixture
def sample_faculty(db: Session) -> list[Person]:
    """Create sample faculty for testing."""
    faculty = []
    for i in range(2):
        fac = Person(
            id=uuid4(),
            name=f"Faculty {i + 1}",
            type="faculty",
            email=f"faculty{i + 1}@test.org",
            performs_procedures=True,
        )
        db.add(fac)
        faculty.append(fac)
    db.commit()
    return faculty


@pytest.fixture
def sample_rotation(db: Session) -> RotationTemplate:
    """Create sample rotation template."""
    rotation = RotationTemplate(
        id=uuid4(),
        name="Clinic",
        description="Outpatient clinic rotation",
        category="clinical",
    )
    db.add(rotation)
    db.commit()
    return rotation


@pytest.fixture
def sample_assignments(
    db: Session,
    sample_residents: list[Person],
    sample_faculty: list[Person],
    sample_rotation: RotationTemplate,
) -> list[Assignment]:
    """Create sample assignments for testing."""
    assignments = []
    start_date = date.today()

    # Create blocks and assignments for a week
    for day in range(7):
        current_date = start_date + timedelta(days=day)

        for session in ["am", "pm"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                session=session,
            )
            db.add(block)
            db.flush()

            # Assign residents
            for resident in sample_residents:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=resident.id,
                    rotation_template_id=sample_rotation.id,
                    role="primary",
                )
                db.add(assignment)
                assignments.append(assignment)

            # Assign faculty
            if sample_faculty:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=sample_faculty[0].id,
                    rotation_template_id=sample_rotation.id,
                    role="supervising",
                )
                db.add(assignment)
                assignments.append(assignment)

    db.commit()
    return assignments


class TestPDFReportGenerator:
    """Test suite for PDF report generator."""

    def test_generator_initialization(self, db: Session):
        """Test PDF generator initializes correctly."""
        generator = PDFReportGenerator(db)
        assert generator.db == db
        assert generator.styles is not None

    def test_create_table(self, db: Session):
        """Test table creation."""
        generator = PDFReportGenerator(db)

        data = [
            ["Header 1", "Header 2"],
            ["Row 1 Col 1", "Row 1 Col 2"],
            ["Row 2 Col 1", "Row 2 Col 2"],
        ]

        table = generator._create_table(data, header_row=True)
        assert table is not None

    def test_generate_pdf(self, db: Session):
        """Test basic PDF generation."""
        from reportlab.platypus import Paragraph

        generator = PDFReportGenerator(db)

        elements = [
            Paragraph("Test Report", generator.styles["ReportTitle"]),
            Paragraph("This is a test.", generator.styles["ReportBody"]),
        ]

        pdf_bytes = generator.generate_pdf(
            elements=elements,
            title="Test Report",
            include_logo=True,
            include_page_numbers=True,
        )

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        # PDF files start with %PDF
        assert pdf_bytes[:4] == b"%PDF"

    def test_create_metadata(self, db: Session):
        """Test report metadata creation."""
        generator = PDFReportGenerator(db)

        request = ScheduleReportRequest(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )

        pdf_bytes = b"test pdf content"
        metadata = generator.create_metadata(
            request=request,
            pdf_bytes=pdf_bytes,
            generated_by="test@example.com",
            page_count=5,
        )

        assert metadata.report_type == "schedule"
        assert metadata.start_date == date(2025, 1, 1)
        assert metadata.end_date == date(2025, 1, 31)
        assert metadata.generated_by == "test@example.com"
        assert metadata.page_count == 5
        assert metadata.file_size_bytes == len(pdf_bytes)


class TestScheduleReportTemplate:
    """Test suite for schedule report template."""

    def test_template_initialization(self, db: Session):
        """Test schedule template initializes correctly."""
        template = ScheduleReportTemplate(db)
        assert template.db == db
        assert template.generator is not None

    def test_generate_schedule_report(
        self, db: Session, sample_assignments: list[Assignment]
    ):
        """Test schedule report generation."""
        template = ScheduleReportTemplate(db)

        request = ScheduleReportRequest(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
            include_details=True,
        )

        pdf_bytes = template.generate(request)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_schedule_report_with_filters(
        self,
        db: Session,
        sample_assignments: list[Assignment],
        sample_residents: list[Person],
    ):
        """Test schedule report with person filters."""
        template = ScheduleReportTemplate(db)

        request = ScheduleReportRequest(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
            person_ids=[sample_residents[0].id],
            include_details=False,
        )

        pdf_bytes = template.generate(request)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0


class TestComplianceReportTemplate:
    """Test suite for compliance report template."""

    def test_template_initialization(self, db: Session):
        """Test compliance template initializes correctly."""
        template = ComplianceReportTemplate(db)
        assert template.db == db
        assert template.generator is not None
        assert template.validator is not None

    def test_generate_compliance_report(
        self, db: Session, sample_assignments: list[Assignment]
    ):
        """Test compliance report generation."""
        template = ComplianceReportTemplate(db)

        request = ComplianceReportRequest(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
        )

        pdf_bytes = template.generate(request)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_compliance_report_with_filters(
        self,
        db: Session,
        sample_assignments: list[Assignment],
        sample_residents: list[Person],
    ):
        """Test compliance report with resident filters."""
        template = ComplianceReportTemplate(db)

        request = ComplianceReportRequest(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
            pgy_levels=[1, 2],
            include_violations_only=False,
        )

        pdf_bytes = template.generate(request)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0


class TestAnalyticsReportTemplate:
    """Test suite for analytics report template."""

    def test_template_initialization(self, db: Session):
        """Test analytics template initializes correctly."""
        template = AnalyticsReportTemplate(db)
        assert template.db == db
        assert template.generator is not None

    def test_generate_analytics_report(
        self, db: Session, sample_assignments: list[Assignment]
    ):
        """Test analytics report generation."""
        template = AnalyticsReportTemplate(db)

        request = AnalyticsReportRequest(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
            include_charts=False,
            include_fairness_metrics=True,
            include_trends=False,
        )

        pdf_bytes = template.generate(request)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_calculate_fairness_metrics(self, db: Session):
        """Test fairness metrics calculation."""
        template = AnalyticsReportTemplate(db)

        workload_data = {
            "person1": {"assignments": 10, "name": "Person 1", "type": "resident"},
            "person2": {"assignments": 12, "name": "Person 2", "type": "resident"},
            "person3": {"assignments": 11, "name": "Person 3", "type": "resident"},
        }

        metrics = template._calculate_fairness_metrics(workload_data)

        assert "gini_coefficient" in metrics
        assert "std_deviation" in metrics
        assert "mean" in metrics
        assert "median" in metrics
        assert metrics["mean"] == pytest.approx(11.0)
        assert metrics["median"] == 11.0

    def test_gini_coefficient_perfect_equality(self, db: Session):
        """Test Gini coefficient for perfect equality."""
        template = AnalyticsReportTemplate(db)

        # Perfect equality - all same values
        values = [10, 10, 10, 10]
        gini = template._calculate_gini(values)

        assert gini == pytest.approx(0.0, abs=0.01)

    def test_gini_coefficient_inequality(self, db: Session):
        """Test Gini coefficient for unequal distribution."""
        template = AnalyticsReportTemplate(db)

        # Unequal distribution
        values = [1, 5, 10, 20]
        gini = template._calculate_gini(values)

        assert 0.0 < gini < 1.0


class TestReportAPIRoutes:
    """Test suite for report API routes."""

    def test_generate_schedule_report_endpoint(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignments: list[Assignment],
    ):
        """Test schedule report generation endpoint."""
        response = client.post(
            "/api/reports/schedule",
            json={
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=6)),
                "include_details": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0

    def test_generate_compliance_report_endpoint(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignments: list[Assignment],
    ):
        """Test compliance report generation endpoint."""
        response = client.post(
            "/api/reports/compliance",
            json={
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=6)),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0

    def test_generate_analytics_report_endpoint(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignments: list[Assignment],
    ):
        """Test analytics report generation endpoint."""
        response = client.post(
            "/api/reports/analytics",
            json={
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=6)),
                "include_charts": False,
                "include_fairness_metrics": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0

    def test_report_requires_authentication(self, client: TestClient):
        """Test that report endpoints require authentication."""
        response = client.post(
            "/api/reports/schedule",
            json={
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=6)),
            },
        )

        assert response.status_code == 401

    def test_faculty_summary_report_endpoint(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignments: list[Assignment],
    ):
        """Test faculty summary report generation endpoint."""
        response = client.post(
            "/api/reports/faculty-summary",
            json={
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=6)),
                "include_workload": True,
                "include_supervision": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
