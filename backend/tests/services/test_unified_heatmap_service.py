"""Test suite for unified heatmap service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.rotation_template import RotationTemplate
from app.services.unified_heatmap_service import UnifiedHeatmapService


class TestUnifiedHeatmapService:
    """Test suite for unified heatmap service."""

    @pytest.fixture
    def heatmap_service(self, db: Session) -> UnifiedHeatmapService:
        """Create a unified heatmap service instance."""
        return UnifiedHeatmapService(db)

    @pytest.fixture
    def resident(self, db: Session) -> Person:
        """Create a resident."""
        person = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            email="resident@hospital.org",
            pgy_level=1,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    @pytest.fixture
    def rotation_template(self, db: Session) -> RotationTemplate:
        """Create a rotation template."""
        template = RotationTemplate(
            id=uuid4(),
            name="Rotation",
            activity_type="outpatient",
            abbreviation="ROT",
            max_residents=4,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def test_service_initialization(self, db: Session):
        """Test UnifiedHeatmapService initialization."""
        service = UnifiedHeatmapService(db)

        assert service.db is db

    def test_generate_heatmap(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test generating unified heatmap."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        heatmap = heatmap_service.generate(start_date, end_date)

        assert isinstance(heatmap, (dict, list, str))

    def test_get_heatmap_data(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test getting heatmap data."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        data = heatmap_service.get_data(start_date, end_date)

        assert isinstance(data, (dict, list))

    def test_generate_utilization_heatmap(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test generating utilization heatmap."""
        heatmap = heatmap_service.generate_utilization()

        assert isinstance(heatmap, (dict, list, str))

    def test_generate_workload_heatmap(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test generating workload heatmap."""
        heatmap = heatmap_service.generate_workload()

        assert isinstance(heatmap, (dict, list, str))

    def test_generate_coverage_heatmap(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test generating coverage heatmap."""
        heatmap = heatmap_service.generate_coverage()

        assert isinstance(heatmap, (dict, list, str))

    def test_generate_burnout_risk_heatmap(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test generating burnout risk heatmap."""
        heatmap = heatmap_service.generate_burnout_risk()

        assert isinstance(heatmap, (dict, list, str))

    def test_get_person_heatmap(
        self,
        heatmap_service: UnifiedHeatmapService,
        resident: Person,
    ):
        """Test getting heatmap for specific person."""
        heatmap = heatmap_service.get_person_heatmap(resident.id)

        assert isinstance(heatmap, (dict, list, str))

    def test_generate_person_utilization_heatmap(
        self,
        heatmap_service: UnifiedHeatmapService,
        resident: Person,
    ):
        """Test generating utilization heatmap for person."""
        heatmap = heatmap_service.generate_person_utilization(resident.id)

        assert isinstance(heatmap, (dict, list, str))

    def test_get_hotspot_analysis(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test getting hotspot analysis."""
        hotspots = heatmap_service.get_hotspots()

        assert isinstance(hotspots, list)

    def test_identify_high_utilization_periods(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test identifying high utilization periods."""
        periods = heatmap_service.get_high_utilization_periods()

        assert isinstance(periods, list)

    def test_identify_low_coverage_areas(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test identifying low coverage areas."""
        areas = heatmap_service.get_low_coverage_areas()

        assert isinstance(areas, list)

    def test_generate_heatmap_as_json(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test generating heatmap as JSON."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        json_data = heatmap_service.to_json(start_date, end_date)

        assert isinstance(json_data, (str, dict))

    def test_generate_heatmap_as_csv(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test generating heatmap as CSV."""
        csv_data = heatmap_service.to_csv()

        assert isinstance(csv_data, str)

    def test_generate_heatmap_as_html(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test generating heatmap as HTML."""
        html_data = heatmap_service.to_html()

        assert isinstance(html_data, str)

    def test_compare_heatmaps(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test comparing two heatmaps."""
        start_date1 = date.today() - timedelta(days=30)
        end_date1 = date.today()
        start_date2 = date.today()
        end_date2 = start_date2 + timedelta(days=30)

        comparison = heatmap_service.compare(
            start_date1, end_date1, start_date2, end_date2
        )

        assert isinstance(comparison, (dict, str))

    def test_get_heatmap_statistics(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test getting heatmap statistics."""
        stats = heatmap_service.get_statistics()

        assert isinstance(stats, dict)

    def test_identify_trends(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test identifying trends in heatmap."""
        trends = heatmap_service.get_trends()

        assert isinstance(trends, list)

    def test_get_anomalies(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test identifying anomalies in heatmap."""
        anomalies = heatmap_service.get_anomalies()

        assert isinstance(anomalies, list)

    def test_generate_recommendations(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test generating recommendations from heatmap."""
        recommendations = heatmap_service.get_recommendations()

        assert isinstance(recommendations, list)

    def test_export_heatmap_image(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test exporting heatmap as image."""
        result = heatmap_service.export_image(filename="heatmap.png")

        assert isinstance(result, bool)

    def test_heatmap_color_scheme(
        self,
        heatmap_service: UnifiedHeatmapService,
    ):
        """Test customizing heatmap color scheme."""
        result = heatmap_service.set_color_scheme("viridis")

        assert isinstance(result, bool)
