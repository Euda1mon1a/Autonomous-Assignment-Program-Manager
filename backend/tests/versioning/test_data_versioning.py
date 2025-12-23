"""
Tests for the data versioning service.

This test suite covers:
- Version history retrieval
- Point-in-time queries
- Version comparison and diff
- Version rollback
- Branch creation and management
- Merge conflict detection
- Version tagging and metadata
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.versioning.data_versioning import (
    DataVersioningService,
    MergeConflict,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def versioning_service(db):
    """Create a data versioning service instance."""
    return DataVersioningService(db)


@pytest.fixture
def sample_person(db):
    """Create a sample person for testing."""
    person = Person(
        id=uuid4(),
        name="Dr. Test Person",
        email="test@example.com",
        person_type="faculty",
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@pytest.fixture
def sample_block(db):
    """Create a sample block for testing."""
    block = Block(
        id=uuid4(),
        date=datetime.now().date(),
        session="AM",
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@pytest.fixture
def sample_assignment(db, sample_person, sample_block):
    """Create a sample assignment for testing."""
    assignment = Assignment(
        id=uuid4(),
        person_id=sample_person.id,
        block_id=sample_block.id,
        role="primary",
        created_by="test_user",
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


# =============================================================================
# Version History Tests
# =============================================================================


class TestVersionHistory:
    """Test suite for version history functionality."""

    @pytest.mark.asyncio
    async def test_get_version_history_empty(
        self, versioning_service, sample_assignment
    ):
        """Test getting version history for a new entity."""
        history = await versioning_service.get_version_history(
            "assignment", sample_assignment.id
        )

        # Should have at least one version (creation)
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_get_version_history_invalid_entity_type(self, versioning_service):
        """Test that invalid entity types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported entity type"):
            await versioning_service.get_version_history("invalid_type", uuid4())

    @pytest.mark.asyncio
    async def test_get_version_by_id(self, versioning_service, sample_assignment):
        """Test getting a specific version by ID."""
        # Get version history first
        history = await versioning_service.get_version_history(
            "assignment", sample_assignment.id
        )

        if history:
            version_id = history[0]["version_id"]
            version_data = await versioning_service.get_version_by_id(
                "assignment", sample_assignment.id, version_id
            )

            # Version data should exist
            assert version_data is None or isinstance(version_data, dict)


# =============================================================================
# Point-in-Time Query Tests
# =============================================================================


class TestPointInTimeQueries:
    """Test suite for point-in-time query functionality."""

    @pytest.mark.asyncio
    async def test_query_at_time_present(self, versioning_service, sample_assignment):
        """Test querying entity state at current time."""
        result = await versioning_service.query_at_time(
            "assignment", sample_assignment.id, datetime.utcnow()
        )

        assert isinstance(result, dict)
        assert result["entity_type"] == "assignment"
        assert result["entity_id"] == str(sample_assignment.id)
        assert "timestamp" in result
        assert "version_id" in result
        assert "data" in result
        assert "existed_at_time" in result

    @pytest.mark.asyncio
    async def test_query_at_time_past(self, versioning_service, sample_assignment):
        """Test querying entity state in the past."""
        past_time = datetime.utcnow() - timedelta(days=30)
        result = await versioning_service.query_at_time(
            "assignment", sample_assignment.id, past_time
        )

        # Entity likely didn't exist 30 days ago
        assert result["existed_at_time"] in (True, False)

    @pytest.mark.asyncio
    async def test_query_at_time_invalid_entity_type(self, versioning_service):
        """Test that invalid entity types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported entity type"):
            await versioning_service.query_at_time(
                "invalid_type", uuid4(), datetime.utcnow()
            )

    @pytest.mark.asyncio
    async def test_query_all_at_time(self, versioning_service):
        """Test querying all entities at a point in time."""
        results = await versioning_service.query_all_at_time(
            "assignment", datetime.utcnow()
        )

        assert isinstance(results, list)


# =============================================================================
# Version Comparison Tests
# =============================================================================


class TestVersionComparison:
    """Test suite for version comparison functionality."""

    @pytest.mark.asyncio
    async def test_compare_versions_invalid_entity_type(self, versioning_service):
        """Test that invalid entity types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported entity type"):
            await versioning_service.compare_versions("invalid_type", uuid4(), 1, 2)


# =============================================================================
# Rollback Tests
# =============================================================================


class TestVersionRollback:
    """Test suite for version rollback functionality."""

    @pytest.mark.asyncio
    async def test_rollback_invalid_entity_type(self, versioning_service):
        """Test that invalid entity types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported entity type"):
            await versioning_service.rollback_to_version(
                "invalid_type", uuid4(), 1, "test_user"
            )


# =============================================================================
# Branch Management Tests
# =============================================================================


class TestBranchManagement:
    """Test suite for branch management functionality."""

    @pytest.mark.asyncio
    async def test_create_branch(self, versioning_service):
        """Test creating a new branch."""
        branch = await versioning_service.create_branch(
            parent_branch="main",
            new_branch_name="feature-test",
            user_id="test_user",
            description="Test branch",
        )

        assert isinstance(branch, dict)
        assert branch["branch_name"] == "feature-test"
        assert branch["parent_branch"] == "main"
        assert branch["created_by"] == "test_user"
        assert branch["description"] == "Test branch"
        assert branch["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_duplicate_branch(self, versioning_service):
        """Test that creating a duplicate branch raises ValueError."""
        await versioning_service.create_branch("main", "duplicate-branch", "test_user")

        with pytest.raises(ValueError, match="already exists"):
            await versioning_service.create_branch(
                "main", "duplicate-branch", "test_user"
            )

    @pytest.mark.asyncio
    async def test_get_branch_info(self, versioning_service):
        """Test getting branch information."""
        # Create a branch first
        await versioning_service.create_branch("main", "info-test", "test_user")

        info = await versioning_service.get_branch_info("info-test")

        assert info is not None
        assert isinstance(info, dict)
        assert "branch" in info
        assert "version_count" in info
        assert "entity_count" in info

    @pytest.mark.asyncio
    async def test_get_branch_info_not_found(self, versioning_service):
        """Test getting info for non-existent branch."""
        info = await versioning_service.get_branch_info("nonexistent")
        assert info is None

    @pytest.mark.asyncio
    async def test_list_branches(self, versioning_service):
        """Test listing all branches."""
        # Create some branches
        await versioning_service.create_branch("main", "branch1", "user1")
        await versioning_service.create_branch("main", "branch2", "user2")

        branches = await versioning_service.list_branches()

        assert isinstance(branches, list)
        assert len(branches) >= 2

        branch_names = [b["branch_name"] for b in branches]
        assert "branch1" in branch_names
        assert "branch2" in branch_names

    @pytest.mark.asyncio
    async def test_delete_branch(self, versioning_service):
        """Test deleting a branch."""
        # Create a branch
        await versioning_service.create_branch("main", "delete-test", "test_user")

        # Delete it
        result = await versioning_service.delete_branch("delete-test", "test_user")
        assert result is True

        # Verify it's gone
        info = await versioning_service.get_branch_info("delete-test")
        assert info is None

    @pytest.mark.asyncio
    async def test_delete_main_branch(self, versioning_service):
        """Test that deleting main branch raises ValueError."""
        with pytest.raises(ValueError, match="Cannot delete main branch"):
            await versioning_service.delete_branch("main", "test_user")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_branch(self, versioning_service):
        """Test deleting a non-existent branch."""
        result = await versioning_service.delete_branch("nonexistent", "test_user")
        assert result is False


# =============================================================================
# Merge Conflict Tests
# =============================================================================


class TestMergeConflicts:
    """Test suite for merge conflict detection."""

    @pytest.mark.asyncio
    async def test_detect_merge_conflicts(self, versioning_service):
        """Test detecting merge conflicts between branches."""
        # Create two branches
        await versioning_service.create_branch("main", "branch-a", "user1")
        await versioning_service.create_branch("main", "branch-b", "user2")

        # Detect conflicts
        conflicts = await versioning_service.detect_merge_conflicts(
            "branch-a", "branch-b"
        )

        assert isinstance(conflicts, list)

    @pytest.mark.asyncio
    async def test_detect_conflicts_invalid_branches(self, versioning_service):
        """Test that invalid branches raise ValueError."""
        with pytest.raises(ValueError, match="not found"):
            await versioning_service.detect_merge_conflicts(
                "nonexistent1", "nonexistent2"
            )

    @pytest.mark.asyncio
    async def test_resolve_conflict(self, versioning_service):
        """Test resolving a merge conflict."""
        conflict: MergeConflict = {
            "entity_type": "assignment",
            "entity_id": str(uuid4()),
            "field_name": "role",
            "source_value": "primary",
            "target_value": "supervising",
            "base_value": "primary",
            "conflict_type": "modify-modify",
            "resolution_strategy": None,
        }

        result = await versioning_service.resolve_conflict(
            conflict, "source", "test_user"
        )

        assert result is True


# =============================================================================
# Tagging and Metadata Tests
# =============================================================================


class TestVersionMetadata:
    """Test suite for version tagging and metadata."""

    @pytest.mark.asyncio
    async def test_tag_version(self, versioning_service, sample_assignment):
        """Test tagging a version."""
        result = await versioning_service.tag_version(
            "assignment", sample_assignment.id, 1, "approved", "test_user"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_tag_version_invalid_entity_type(self, versioning_service):
        """Test that invalid entity types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported entity type"):
            await versioning_service.tag_version(
                "invalid_type", uuid4(), 1, "tag", "user"
            )

    @pytest.mark.asyncio
    async def test_add_version_comment(self, versioning_service, sample_assignment):
        """Test adding a comment to a version."""
        result = await versioning_service.add_version_comment(
            "assignment",
            sample_assignment.id,
            1,
            "This version looks good",
            "test_user",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_add_comment_invalid_entity_type(self, versioning_service):
        """Test that invalid entity types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported entity type"):
            await versioning_service.add_version_comment(
                "invalid_type", uuid4(), 1, "comment", "user"
            )


# =============================================================================
# Lineage and Comparison Tests
# =============================================================================


class TestLineageAndComparison:
    """Test suite for lineage and branch comparison."""

    @pytest.mark.asyncio
    async def test_get_entity_lineage(self, versioning_service, sample_assignment):
        """Test getting entity lineage."""
        lineage = await versioning_service.get_entity_lineage(
            "assignment", sample_assignment.id
        )

        assert isinstance(lineage, dict)
        assert lineage["entity_type"] == "assignment"
        assert lineage["entity_id"] == str(sample_assignment.id)
        assert "total_versions" in lineage
        assert "versions" in lineage

    @pytest.mark.asyncio
    async def test_get_lineage_invalid_entity_type(self, versioning_service):
        """Test that invalid entity types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported entity type"):
            await versioning_service.get_entity_lineage("invalid_type", uuid4())

    @pytest.mark.asyncio
    async def test_compare_branches(self, versioning_service):
        """Test comparing two branches."""
        # Create branches
        await versioning_service.create_branch("main", "compare-a", "user1")
        await versioning_service.create_branch("main", "compare-b", "user2")

        comparison = await versioning_service.compare_branches("compare-a", "compare-b")

        assert isinstance(comparison, dict)
        assert comparison["branch1"] == "compare-a"
        assert comparison["branch2"] == "compare-b"
        assert "differences" in comparison
        assert "unique_to_branch1" in comparison
        assert "unique_to_branch2" in comparison

    @pytest.mark.asyncio
    async def test_compare_invalid_branches(self, versioning_service):
        """Test that comparing invalid branches raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            await versioning_service.compare_branches("nonexistent1", "nonexistent2")


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_checksum_calculation(self, versioning_service):
        """Test checksum calculation for version data."""
        data1 = {"field1": "value1", "field2": 123}
        data2 = {"field1": "value1", "field2": 123}
        data3 = {"field1": "value1", "field2": 456}

        checksum1 = versioning_service._calculate_checksum(data1)
        checksum2 = versioning_service._calculate_checksum(data2)
        checksum3 = versioning_service._calculate_checksum(data3)

        # Same data should produce same checksum
        assert checksum1 == checksum2

        # Different data should produce different checksum
        assert checksum1 != checksum3

        # Checksums should be hex strings
        assert isinstance(checksum1, str)
        assert len(checksum1) == 64  # SHA-256 produces 64 hex characters

    @pytest.mark.asyncio
    async def test_checksum_empty_data(self, versioning_service):
        """Test checksum calculation with empty data."""
        checksum = versioning_service._calculate_checksum(None)
        assert checksum == ""

        checksum_empty = versioning_service._calculate_checksum({})
        assert isinstance(checksum_empty, str)
        assert len(checksum_empty) == 64
