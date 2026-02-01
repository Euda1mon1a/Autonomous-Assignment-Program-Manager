"""Tests for model ↔ schema field alignment."""

from app.schemas.activity import ActivityResponse, ActivityUpdate


def test_activity_response_includes_supervision_and_capacity_flags():
    """ActivityResponse should include supervision and physical-capacity fields."""
    fields = ActivityResponse.model_fields.keys()
    assert "provides_supervision" in fields
    assert "counts_toward_physical_capacity" in fields


def test_activity_update_supports_supervision_and_capacity_flags():
    """ActivityUpdate should accept supervision and physical-capacity fields."""
    fields = ActivityUpdate.model_fields.keys()
    assert "provides_supervision" in fields
    assert "counts_toward_physical_capacity" in fields
