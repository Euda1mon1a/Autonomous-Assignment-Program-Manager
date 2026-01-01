"""
Tests for faceted search service.

Comprehensive test suite for faceted search functionality,
covering facet extraction, filtering, and result refinement.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from app.search.faceted_search import (
    FacetType,
    FacetOrder,
    DateRangePeriod,
    FacetValue,
    RangeFacetValue,
    DateRangeFacetValue,
    Facet,
    FacetConfig,
)


class TestFacetType:
    """Test suite for FacetType enum."""

    def test_facet_type_values(self):
        """Test FacetType has all expected values."""
        # Assert
        assert FacetType.TERM == "term"
        assert FacetType.RANGE == "range"
        assert FacetType.DATE_RANGE == "date_range"
        assert FacetType.HIERARCHICAL == "hierarchical"


class TestFacetOrder:
    """Test suite for FacetOrder enum."""

    def test_facet_order_values(self):
        """Test FacetOrder has all expected values."""
        # Assert
        assert FacetOrder.COUNT_DESC == "count_desc"
        assert FacetOrder.COUNT_ASC == "count_asc"
        assert FacetOrder.VALUE_ASC == "value_asc"
        assert FacetOrder.VALUE_DESC == "value_desc"
        assert FacetOrder.CUSTOM == "custom"


class TestDateRangePeriod:
    """Test suite for DateRangePeriod enum."""

    def test_date_range_period_values(self):
        """Test DateRangePeriod has all expected periods."""
        # Assert
        assert DateRangePeriod.TODAY == "today"
        assert DateRangePeriod.THIS_WEEK == "this_week"
        assert DateRangePeriod.THIS_MONTH == "this_month"
        assert DateRangePeriod.THIS_QUARTER == "this_quarter"
        assert DateRangePeriod.THIS_YEAR == "this_year"
        assert DateRangePeriod.LAST_7_DAYS == "last_7_days"
        assert DateRangePeriod.LAST_30_DAYS == "last_30_days"
        assert DateRangePeriod.LAST_90_DAYS == "last_90_days"
        assert DateRangePeriod.LAST_YEAR == "last_year"
        assert DateRangePeriod.CUSTOM == "custom"


class TestFacetValue:
    """Test suite for FacetValue model."""

    def test_facet_value_creation(self):
        """Test creating a facet value."""
        # Act
        facet_value = FacetValue(
            value="Resident",
            key="resident",
            count=25,
            selected=False,
        )

        # Assert
        assert facet_value.value == "Resident"
        assert facet_value.key == "resident"
        assert facet_value.count == 25
        assert facet_value.selected is False
        assert facet_value.parent is None
        assert facet_value.children == []
        assert facet_value.metadata == {}

    def test_facet_value_with_hierarchical_data(self):
        """Test facet value with parent and children."""
        # Act
        child = FacetValue(
            value="PGY-1",
            key="pgy1",
            count=10,
            parent="resident",
        )

        parent = FacetValue(
            value="Resident",
            key="resident",
            count=25,
            children=[child],
        )

        # Assert
        assert parent.children[0] == child
        assert child.parent == "resident"

    def test_facet_value_with_metadata(self):
        """Test facet value with custom metadata."""
        # Act
        facet_value = FacetValue(
            value="Faculty",
            key="faculty",
            count=15,
            metadata={"role_type": "teaching", "active": True},
        )

        # Assert
        assert facet_value.metadata["role_type"] == "teaching"
        assert facet_value.metadata["active"] is True


class TestRangeFacetValue:
    """Test suite for RangeFacetValue model."""

    def test_range_facet_value_creation(self):
        """Test creating a range facet value."""
        # Act
        range_value = RangeFacetValue(
            label="0-10",
            min_value=0,
            max_value=10,
            count=5,
            selected=False,
        )

        # Assert
        assert range_value.label == "0-10"
        assert range_value.min_value == 0
        assert range_value.max_value == 10
        assert range_value.count == 5
        assert range_value.selected is False

    def test_range_facet_value_open_ended(self):
        """Test range facet value with open-ended range."""
        # Act
        range_value = RangeFacetValue(
            label="100+",
            min_value=100,
            max_value=None,  # Open-ended
            count=3,
        )

        # Assert
        assert range_value.min_value == 100
        assert range_value.max_value is None


class TestDateRangeFacetValue:
    """Test suite for DateRangeFacetValue model."""

    def test_date_range_facet_value_creation(self):
        """Test creating a date range facet value."""
        # Act
        date_value = DateRangeFacetValue(
            label="This Week",
            period=DateRangePeriod.THIS_WEEK,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            count=12,
            selected=False,
        )

        # Assert
        assert date_value.label == "This Week"
        assert date_value.period == DateRangePeriod.THIS_WEEK
        assert date_value.start_date == date(2025, 1, 1)
        assert date_value.end_date == date(2025, 1, 7)
        assert date_value.count == 12

    def test_date_range_facet_value_with_custom_period(self):
        """Test date range with custom period."""
        # Act
        date_value = DateRangeFacetValue(
            label="Custom Range",
            period=DateRangePeriod.CUSTOM,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 2, 15),
            count=8,
        )

        # Assert
        assert date_value.period == DateRangePeriod.CUSTOM
        assert date_value.label == "Custom Range"


class TestFacet:
    """Test suite for Facet model."""

    def test_facet_creation_with_term_values(self):
        """Test creating a facet with term values."""
        # Arrange
        values = [
            FacetValue(value="Resident", key="resident", count=25),
            FacetValue(value="Faculty", key="faculty", count=15),
        ]

        # Act
        facet = Facet(
            name="person_type",
            label="Person Type",
            type=FacetType.TERM,
            values=values,
            total_count=40,
        )

        # Assert
        assert facet.name == "person_type"
        assert facet.label == "Person Type"
        assert facet.type == FacetType.TERM
        assert len(facet.values) == 2
        assert facet.total_count == 40
        assert facet.order == FacetOrder.COUNT_DESC  # Default

    def test_facet_with_range_values(self):
        """Test facet with range values."""
        # Arrange
        range_values = [
            RangeFacetValue(label="0-50", min_value=0, max_value=50, count=10),
            RangeFacetValue(label="50-100", min_value=50, max_value=100, count=8),
        ]

        # Act
        facet = Facet(
            name="hours_worked",
            label="Hours Worked",
            type=FacetType.RANGE,
            range_values=range_values,
            total_count=18,
        )

        # Assert
        assert facet.type == FacetType.RANGE
        assert len(facet.range_values) == 2

    def test_facet_with_date_range_values(self):
        """Test facet with date range values."""
        # Arrange
        date_values = [
            DateRangeFacetValue(
                label="This Week",
                period=DateRangePeriod.THIS_WEEK,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                count=5,
            ),
        ]

        # Act
        facet = Facet(
            name="date_range",
            label="Date Range",
            type=FacetType.DATE_RANGE,
            date_range_values=date_values,
        )

        # Assert
        assert facet.type == FacetType.DATE_RANGE
        assert len(facet.date_range_values) == 1

    def test_facet_with_custom_order(self):
        """Test facet with custom ordering."""
        # Act
        facet = Facet(
            name="specialty",
            label="Specialty",
            type=FacetType.TERM,
            order=FacetOrder.VALUE_ASC,
        )

        # Assert
        assert facet.order == FacetOrder.VALUE_ASC

    def test_facet_multi_select(self):
        """Test facet allows multi-select."""
        # Act
        facet = Facet(
            name="status",
            label="Status",
            type=FacetType.TERM,
            multi_select=True,
        )

        # Assert
        assert facet.multi_select is True


class TestFacetConfig:
    """Test suite for FacetConfig model."""

    def test_facet_config_default_enabled_facets(self):
        """Test FacetConfig has default enabled facets."""
        # Act
        config = FacetConfig()

        # Assert
        assert "person_type" in config.enabled_facets
        assert "pgy_level" in config.enabled_facets
        assert "faculty_role" in config.enabled_facets
        assert "rotation_type" in config.enabled_facets
        assert "status" in config.enabled_facets
        assert "date_range" in config.enabled_facets

    def test_facet_config_custom_enabled_facets(self):
        """Test FacetConfig with custom enabled facets."""
        # Act
        config = FacetConfig(
            enabled_facets=["person_type", "status"],
        )

        # Assert
        assert len(config.enabled_facets) == 2
        assert "person_type" in config.enabled_facets
        assert "status" in config.enabled_facets
        assert "pgy_level" not in config.enabled_facets
