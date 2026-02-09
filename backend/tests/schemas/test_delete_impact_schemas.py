"""Tests for delete impact schemas (enum values, model instantiation)."""

from uuid import uuid4

from app.schemas.delete_impact import (
    DeleteImpactResource,
    DeleteImpactDependency,
    DeleteImpactResponse,
)


class TestDeleteImpactResource:
    def test_values(self):
        assert DeleteImpactResource.person.value == "person"
        assert DeleteImpactResource.rotation_template.value == "rotation_template"
        assert DeleteImpactResource.block.value == "block"
        assert DeleteImpactResource.activity.value == "activity"
        assert DeleteImpactResource.academic_block.value == "academic_block"

    def test_count(self):
        assert len(DeleteImpactResource) == 5

    def test_is_str(self):
        assert isinstance(DeleteImpactResource.person, str)


class TestDeleteImpactDependency:
    def test_valid(self):
        r = DeleteImpactDependency(
            table="block_assignments", count=3, columns=["person_id"]
        )
        assert r.table == "block_assignments"
        assert r.count == 3
        assert r.columns == ["person_id"]

    def test_empty_columns(self):
        r = DeleteImpactDependency(table="t", count=0, columns=[])
        assert r.columns == []


class TestDeleteImpactResponse:
    def test_valid(self):
        rid = uuid4()
        r = DeleteImpactResponse(
            resource_type=DeleteImpactResource.person,
            resource_id=rid,
            dependencies=[],
            total_dependents=0,
        )
        assert r.resource_type == DeleteImpactResource.person
        assert r.resource_id == rid
        assert r.dependencies == []
        assert r.total_dependents == 0

    def test_with_dependencies(self):
        dep = DeleteImpactDependency(table="absences", count=2, columns=["person_id"])
        r = DeleteImpactResponse(
            resource_type=DeleteImpactResource.activity,
            resource_id=uuid4(),
            dependencies=[dep],
            total_dependents=2,
        )
        assert len(r.dependencies) == 1
        assert r.total_dependents == 2
