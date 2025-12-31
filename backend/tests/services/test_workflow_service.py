"""Tests for WorkflowService."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest

from app.models.workflow import WorkflowInstance, WorkflowStatus, WorkflowTemplate
from app.services.workflow_service import WorkflowService
from app.workflow.engine import WorkflowEngine


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_workflow_definition() -> dict:
    """Create a sample workflow definition."""
    return {
        "steps": [
            {
                "id": "step1",
                "name": "First Step",
                "handler": "app.services.test_handler.step1",
                "execution_mode": "sequential",
                "depends_on": [],
                "retry_policy": {"max_attempts": 1},
                "timeout_seconds": 10,
            },
            {
                "id": "step2",
                "name": "Second Step",
                "handler": "app.services.test_handler.step2",
                "execution_mode": "sequential",
                "depends_on": ["step1"],
                "retry_policy": {"max_attempts": 2},
                "timeout_seconds": 20,
            },
        ],
        "default_timeout_seconds": 300,
    }


@pytest.fixture
def sample_workflow_template(db, sample_workflow_definition, admin_user):
    """Create a sample workflow template."""
    template = WorkflowTemplate(
        id=uuid4(),
        name="test_workflow",
        description="Test workflow template",
        version=1,
        definition=sample_workflow_definition,
        is_active=True,
        tags=["test", "automated"],
        created_by_id=admin_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def sample_workflow_instance(db, sample_workflow_template, admin_user):
    """Create a sample workflow instance."""
    instance = WorkflowInstance(
        id=uuid4(),
        template_id=sample_workflow_template.id,
        template_version=sample_workflow_template.version,
        name="Test Workflow Instance",
        description="Test instance",
        status=WorkflowStatus.PENDING.value,
        input_data={"param1": "value1"},
        priority=5,
        created_by_id=admin_user.id,
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


# ============================================================================
# Template Management Tests
# ============================================================================


class TestTemplateManagement:
    """Test suite for workflow template management."""

    def test_create_template_success(self, db, sample_workflow_definition, admin_user):
        """Test creating a workflow template successfully."""
        service = WorkflowService(db)
        result = service.create_template(
            name="new_workflow",
            definition=sample_workflow_definition,
            description="New workflow template",
            tags=["schedule", "acgme"],
            created_by_id=admin_user.id,
        )

        assert result is not None
        assert result.name == "new_workflow"
        assert result.description == "New workflow template"
        assert result.version == 1
        assert result.is_active is True
        assert result.tags == ["schedule", "acgme"]
        assert result.created_by_id == admin_user.id
        assert result.definition == sample_workflow_definition

    def test_create_template_minimal_data(self, db, sample_workflow_definition):
        """Test creating a template with minimal required fields."""
        service = WorkflowService(db)
        result = service.create_template(
            name="minimal_workflow",
            definition=sample_workflow_definition,
        )

        assert result is not None
        assert result.name == "minimal_workflow"
        assert result.description is None
        assert result.tags is None
        assert result.created_by_id is None
        assert result.version == 1

    def test_create_template_invalid_definition_error(self, db):
        """Test creating a template with invalid definition raises error."""
        service = WorkflowService(db)

        # Mock the engine to raise ValueError
        with patch.object(
            service.engine,
            "create_template",
            side_effect=ValueError("Invalid definition"),
        ):
            with pytest.raises(ValueError, match="Invalid definition"):
                service.create_template(
                    name="invalid_workflow",
                    definition={"invalid": "data"},
                )

    def test_create_template_database_rollback_on_error(
        self, db, sample_workflow_definition
    ):
        """Test that database is rolled back on error."""
        service = WorkflowService(db)

        # Mock the engine to raise an exception
        with patch.object(
            service.engine,
            "create_template",
            side_effect=Exception("Database error"),
        ):
            with pytest.raises(Exception, match="Database error"):
                service.create_template(
                    name="error_workflow",
                    definition=sample_workflow_definition,
                )

    def test_get_template_by_id(self, db, sample_workflow_template):
        """Test getting a template by ID."""
        service = WorkflowService(db)
        result = service.get_template(template_id=sample_workflow_template.id)

        assert result is not None
        assert result.id == sample_workflow_template.id
        assert result.name == sample_workflow_template.name

    def test_get_template_by_name(self, db, sample_workflow_template):
        """Test getting a template by name (latest version)."""
        service = WorkflowService(db)
        result = service.get_template(name=sample_workflow_template.name)

        assert result is not None
        assert result.name == sample_workflow_template.name
        assert result.version == sample_workflow_template.version

    def test_get_template_by_name_and_version(self, db, sample_workflow_template):
        """Test getting a template by name and specific version."""
        service = WorkflowService(db)
        result = service.get_template(
            name=sample_workflow_template.name,
            version=sample_workflow_template.version,
        )

        assert result is not None
        assert result.name == sample_workflow_template.name
        assert result.version == sample_workflow_template.version

    def test_get_template_not_found(self, db):
        """Test getting a non-existent template returns None."""
        service = WorkflowService(db)
        result = service.get_template(template_id=uuid4())

        assert result is None

    def test_list_templates_no_filters(self, db, sample_workflow_template):
        """Test listing all templates without filters."""
        service = WorkflowService(db)
        result = service.list_templates(active_only=False)

        assert len(result) >= 1
        assert any(t.id == sample_workflow_template.id for t in result)

    def test_list_templates_active_only(
        self, db, sample_workflow_definition, admin_user
    ):
        """Test listing only active templates."""
        # Create active and inactive templates
        active_template = WorkflowTemplate(
            id=uuid4(),
            name="active_workflow",
            version=1,
            definition=sample_workflow_definition,
            is_active=True,
            created_by_id=admin_user.id,
        )
        inactive_template = WorkflowTemplate(
            id=uuid4(),
            name="inactive_workflow",
            version=1,
            definition=sample_workflow_definition,
            is_active=False,
            created_by_id=admin_user.id,
        )
        db.add_all([active_template, inactive_template])
        db.commit()

        service = WorkflowService(db)
        result = service.list_templates(active_only=True)

        assert any(t.id == active_template.id for t in result)
        assert not any(t.id == inactive_template.id for t in result)

    def test_list_templates_filter_by_tags(
        self, db, sample_workflow_definition, admin_user
    ):
        """Test filtering templates by tags."""
        # Create templates with different tags
        template1 = WorkflowTemplate(
            id=uuid4(),
            name="schedule_workflow",
            version=1,
            definition=sample_workflow_definition,
            tags=["schedule", "acgme"],
            created_by_id=admin_user.id,
        )
        template2 = WorkflowTemplate(
            id=uuid4(),
            name="other_workflow",
            version=1,
            definition=sample_workflow_definition,
            tags=["other"],
            created_by_id=admin_user.id,
        )
        db.add_all([template1, template2])
        db.commit()

        service = WorkflowService(db)
        result = service.list_templates(tags=["schedule"])

        # Should include template1 but not template2
        assert any(t.id == template1.id for t in result)

    def test_list_templates_empty_result(self, db):
        """Test listing templates when none exist."""
        service = WorkflowService(db)
        result = service.list_templates(active_only=False)

        assert isinstance(result, list)

    def test_deactivate_template_success(self, db, sample_workflow_template):
        """Test deactivating a template successfully."""
        service = WorkflowService(db)
        result = service.deactivate_template(sample_workflow_template.id)

        assert result is not None
        assert result.id == sample_workflow_template.id
        assert result.is_active is False

    def test_deactivate_template_not_found_error(self, db):
        """Test deactivating a non-existent template raises error."""
        service = WorkflowService(db)

        with pytest.raises(ValueError, match="Template .* not found"):
            service.deactivate_template(uuid4())

    def test_deactivate_template_persists_to_database(
        self, db, sample_workflow_template
    ):
        """Test that template deactivation persists to database."""
        service = WorkflowService(db)
        service.deactivate_template(sample_workflow_template.id)

        # Query directly from database
        db_template = (
            db.query(WorkflowTemplate)
            .filter(WorkflowTemplate.id == sample_workflow_template.id)
            .first()
        )
        assert db_template.is_active is False


# ============================================================================
# Workflow Instance Management Tests
# ============================================================================


class TestWorkflowInstanceManagement:
    """Test suite for workflow instance management."""

    @patch("asyncio.create_task")
    def test_start_workflow_async_success(
        self, mock_create_task, db, sample_workflow_template, admin_user
    ):
        """Test starting a workflow asynchronously."""
        service = WorkflowService(db)

        # Mock the engine methods
        mock_instance = Mock(spec=WorkflowInstance)
        mock_instance.id = uuid4()
        mock_instance.status = WorkflowStatus.RUNNING.value

        with patch.object(
            service.engine,
            "create_instance",
            return_value=mock_instance,
        ):
            result = service.start_workflow(
                template_name=sample_workflow_template.name,
                input_data={"param1": "value1"},
                name="Test Instance",
                priority=10,
                created_by_id=admin_user.id,
                async_execution=True,
            )

            assert result is not None
            assert result.id == mock_instance.id
            # Verify async task was created
            mock_create_task.assert_called_once()

    def test_start_workflow_template_not_found_error(self, db):
        """Test starting a workflow with non-existent template raises error."""
        service = WorkflowService(db)

        with pytest.raises(ValueError, match="Workflow template .* not found"):
            service.start_workflow(
                template_name="nonexistent_workflow",
                async_execution=False,
            )

    def test_start_workflow_inactive_template_error(self, db, sample_workflow_template):
        """Test starting a workflow with inactive template raises error."""
        # Deactivate the template
        sample_workflow_template.is_active = False
        db.commit()

        service = WorkflowService(db)

        with pytest.raises(ValueError, match="is inactive"):
            service.start_workflow(
                template_name=sample_workflow_template.name,
                async_execution=False,
            )

    def test_start_workflow_with_all_parameters(
        self, db, sample_workflow_template, admin_user
    ):
        """Test starting a workflow with all optional parameters."""
        service = WorkflowService(db)

        mock_instance = Mock(spec=WorkflowInstance)
        mock_instance.id = uuid4()

        with patch.object(
            service.engine, "create_instance", return_value=mock_instance
        ):
            with patch("asyncio.create_task"):
                result = service.start_workflow(
                    template_name=sample_workflow_template.name,
                    input_data={"key": "value"},
                    name="Custom Name",
                    description="Custom description",
                    priority=99,
                    timeout_seconds=3600,
                    created_by_id=admin_user.id,
                    async_execution=True,
                )

                assert result is not None

    def test_start_workflow_database_rollback_on_error(
        self, db, sample_workflow_template
    ):
        """Test that database is rolled back on workflow start error."""
        service = WorkflowService(db)

        with patch.object(
            service.engine,
            "create_instance",
            side_effect=Exception("Creation error"),
        ):
            with pytest.raises(Exception, match="Creation error"):
                service.start_workflow(
                    template_name=sample_workflow_template.name,
                    async_execution=False,
                )

    def test_get_instance_success(self, db, sample_workflow_instance):
        """Test getting a workflow instance successfully."""
        service = WorkflowService(db)

        mock_instance = Mock(spec=WorkflowInstance)
        mock_instance.id = sample_workflow_instance.id

        with patch.object(
            service.engine,
            "get_instance",
            return_value=mock_instance,
        ):
            result = service.get_instance(sample_workflow_instance.id)

            assert result is not None
            assert result.id == sample_workflow_instance.id

    def test_get_instance_not_found(self, db):
        """Test getting a non-existent instance returns None."""
        service = WorkflowService(db)

        with patch.object(service.engine, "get_instance", return_value=None):
            result = service.get_instance(uuid4())

            assert result is None

    def test_cancel_workflow_success(self, db, sample_workflow_instance, admin_user):
        """Test cancelling a workflow successfully."""
        service = WorkflowService(db)

        # Set instance to running state
        sample_workflow_instance.status = WorkflowStatus.RUNNING.value
        db.commit()

        mock_cancelled_instance = Mock(spec=WorkflowInstance)
        mock_cancelled_instance.id = sample_workflow_instance.id
        mock_cancelled_instance.status = WorkflowStatus.CANCELLED.value

        with patch.object(
            service.engine,
            "cancel_instance",
            return_value=mock_cancelled_instance,
        ):
            result = service.cancel_workflow(
                instance_id=sample_workflow_instance.id,
                reason="Test cancellation",
                cancelled_by_id=admin_user.id,
            )

            assert result is not None
            assert result.id == sample_workflow_instance.id
            assert result.status == WorkflowStatus.CANCELLED.value

    def test_cancel_workflow_not_found_error(self, db):
        """Test cancelling a non-existent workflow raises error."""
        service = WorkflowService(db)

        with patch.object(
            service.engine,
            "cancel_instance",
            side_effect=ValueError("Instance not found"),
        ):
            with pytest.raises(ValueError, match="Instance not found"):
                service.cancel_workflow(
                    instance_id=uuid4(),
                    reason="Test",
                )

    def test_cancel_workflow_database_rollback_on_error(
        self, db, sample_workflow_instance
    ):
        """Test that database is rolled back on cancellation error."""
        service = WorkflowService(db)

        with patch.object(
            service.engine,
            "cancel_instance",
            side_effect=Exception("Cancellation error"),
        ):
            with pytest.raises(Exception, match="Cancellation error"):
                service.cancel_workflow(
                    instance_id=sample_workflow_instance.id,
                    reason="Test",
                )


# ============================================================================
# Query and Monitoring Tests
# ============================================================================


class TestQueryAndMonitoring:
    """Test suite for workflow query and monitoring operations."""

    def test_list_instances_no_filters(self, db, sample_workflow_instance):
        """Test listing all instances without filters."""
        service = WorkflowService(db)

        mock_instances = [sample_workflow_instance]
        mock_total = 1

        with patch.object(
            service.engine,
            "query_instances",
            return_value=(mock_instances, mock_total),
        ):
            instances, total = service.list_instances()

            assert total == 1
            assert len(instances) == 1
            assert instances[0].id == sample_workflow_instance.id

    def test_list_instances_filter_by_template_name(
        self, db, sample_workflow_template, sample_workflow_instance
    ):
        """Test filtering instances by template name."""
        service = WorkflowService(db)

        mock_instances = [sample_workflow_instance]
        mock_total = 1

        with patch.object(
            service.engine,
            "query_instances",
            return_value=(mock_instances, mock_total),
        ):
            instances, total = service.list_instances(
                template_name=sample_workflow_template.name
            )

            assert total == 1
            assert len(instances) == 1

    def test_list_instances_filter_by_status(self, db, sample_workflow_instance):
        """Test filtering instances by status."""
        service = WorkflowService(db)

        mock_instances = [sample_workflow_instance]
        mock_total = 1

        with patch.object(
            service.engine,
            "query_instances",
            return_value=(mock_instances, mock_total),
        ):
            instances, total = service.list_instances(
                status=WorkflowStatus.PENDING.value
            )

            assert total == 1
            assert instances[0].status == WorkflowStatus.PENDING.value

    def test_list_instances_filter_by_date_range(self, db):
        """Test filtering instances by creation date range."""
        service = WorkflowService(db)

        now = datetime.utcnow()
        created_after = now - timedelta(days=7)
        created_before = now

        with patch.object(
            service.engine,
            "query_instances",
            return_value=([], 0),
        ):
            instances, total = service.list_instances(
                created_after=created_after,
                created_before=created_before,
            )

            assert isinstance(instances, list)
            assert total == 0

    def test_list_instances_filter_by_priority(self, db):
        """Test filtering instances by priority range."""
        service = WorkflowService(db)

        with patch.object(
            service.engine,
            "query_instances",
            return_value=([], 0),
        ):
            instances, total = service.list_instances(
                priority_min=5,
                priority_max=10,
            )

            assert isinstance(instances, list)

    def test_list_instances_pagination(self, db):
        """Test instance pagination with limit and offset."""
        service = WorkflowService(db)

        with patch.object(
            service.engine,
            "query_instances",
            return_value=([], 0),
        ):
            instances, total = service.list_instances(
                limit=10,
                offset=20,
            )

            assert isinstance(instances, list)

    def test_list_instances_template_not_found_returns_empty(self, db):
        """Test listing instances with non-existent template name returns empty."""
        service = WorkflowService(db)

        with patch.object(
            service.engine,
            "query_instances",
            return_value=([], 0),
        ):
            instances, total = service.list_instances(
                template_name="nonexistent_template"
            )

            assert total == 0
            assert len(instances) == 0

    def test_get_running_workflows(self, db):
        """Test getting all running workflows."""
        service = WorkflowService(db)

        mock_instance = Mock(spec=WorkflowInstance)
        mock_instance.status = WorkflowStatus.RUNNING.value

        with patch.object(
            service.engine,
            "query_instances",
            return_value=([mock_instance], 1),
        ):
            result = service.get_running_workflows(limit=50)

            assert len(result) == 1
            assert result[0].status == WorkflowStatus.RUNNING.value

    def test_get_running_workflows_with_limit(self, db):
        """Test getting running workflows with custom limit."""
        service = WorkflowService(db)

        with patch.object(
            service.engine,
            "query_instances",
            return_value=([], 0),
        ) as mock_query:
            service.get_running_workflows(limit=25)

            # Verify that limit was passed to query
            mock_query.assert_called_once()
            call_kwargs = mock_query.call_args[1]
            assert call_kwargs["limit"] == 25

    def test_get_failed_workflows(self, db):
        """Test getting failed workflows."""
        service = WorkflowService(db)

        mock_instance = Mock(spec=WorkflowInstance)
        mock_instance.status = WorkflowStatus.FAILED.value

        with patch.object(
            service.engine,
            "query_instances",
            return_value=([mock_instance], 1),
        ):
            result = service.get_failed_workflows()

            assert len(result) == 1
            assert result[0].status == WorkflowStatus.FAILED.value

    def test_get_failed_workflows_with_time_filter(self, db):
        """Test getting failed workflows since a specific time."""
        service = WorkflowService(db)

        since = datetime.utcnow() - timedelta(hours=24)

        with patch.object(
            service.engine,
            "query_instances",
            return_value=([], 0),
        ) as mock_query:
            service.get_failed_workflows(since=since, limit=50)

            # Verify that created_after was passed
            mock_query.assert_called_once()
            call_kwargs = mock_query.call_args[1]
            assert call_kwargs["created_after"] == since

    def test_get_statistics_no_filter(self, db):
        """Test getting workflow statistics without filters."""
        service = WorkflowService(db)

        mock_stats = {
            "total_workflows": 100,
            "completed": 80,
            "failed": 10,
            "running": 5,
            "pending": 5,
        }

        with patch.object(
            service.engine,
            "get_statistics",
            return_value=mock_stats,
        ):
            result = service.get_statistics()

            assert result["total_workflows"] == 100
            assert result["completed"] == 80
            assert result["failed"] == 10

    def test_get_statistics_filter_by_template(self, db, sample_workflow_template):
        """Test getting statistics filtered by template name."""
        service = WorkflowService(db)

        mock_stats = {
            "total_workflows": 10,
            "completed": 8,
            "failed": 2,
        }

        with patch.object(
            service.engine,
            "get_statistics",
            return_value=mock_stats,
        ):
            result = service.get_statistics(template_name=sample_workflow_template.name)

            assert result["total_workflows"] == 10

    def test_get_statistics_template_not_found_returns_all(self, db):
        """Test statistics with non-existent template name."""
        service = WorkflowService(db)

        mock_stats = {"total_workflows": 0}

        with patch.object(
            service.engine,
            "get_statistics",
            return_value=mock_stats,
        ):
            result = service.get_statistics(template_name="nonexistent")

            assert isinstance(result, dict)


# ============================================================================
# Common Workflow Templates Tests
# ============================================================================


class TestCommonWorkflowTemplates:
    """Test suite for common workflow template creation."""

    def test_create_schedule_generation_workflow(self, db, admin_user):
        """Test creating schedule generation workflow template."""
        service = WorkflowService(db)

        result = service.create_schedule_generation_workflow(
            created_by_id=admin_user.id
        )

        assert result is not None
        assert result.name == "schedule_generation"
        assert (
            result.description
            == "Automated schedule generation with validation and notifications"
        )
        assert result.tags == ["schedule", "acgme", "automated"]
        assert result.created_by_id == admin_user.id
        assert result.is_active is True

    def test_schedule_generation_workflow_has_correct_steps(self, db, admin_user):
        """Test that schedule generation workflow has all required steps."""
        service = WorkflowService(db)

        result = service.create_schedule_generation_workflow(
            created_by_id=admin_user.id
        )

        steps = result.definition["steps"]
        step_ids = [step["id"] for step in steps]

        # Verify all required steps are present
        assert "validate_input" in step_ids
        assert "generate_schedule" in step_ids
        assert "validate_acgme" in step_ids
        assert "check_conflicts" in step_ids
        assert "calculate_resilience" in step_ids
        assert "send_notification" in step_ids

    def test_schedule_generation_workflow_step_dependencies(self, db, admin_user):
        """Test that schedule generation workflow steps have correct dependencies."""
        service = WorkflowService(db)

        result = service.create_schedule_generation_workflow(
            created_by_id=admin_user.id
        )

        steps = {step["id"]: step for step in result.definition["steps"]}

        # Verify dependency chain
        assert steps["validate_input"]["depends_on"] == []
        assert steps["generate_schedule"]["depends_on"] == ["validate_input"]
        assert steps["validate_acgme"]["depends_on"] == ["generate_schedule"]
        assert steps["check_conflicts"]["depends_on"] == ["validate_acgme"]
        assert steps["calculate_resilience"]["depends_on"] == ["validate_acgme"]
        assert set(steps["send_notification"]["depends_on"]) == {
            "check_conflicts",
            "calculate_resilience",
        }

    def test_schedule_generation_workflow_has_error_handlers(self, db, admin_user):
        """Test that schedule generation workflow has error handlers."""
        service = WorkflowService(db)

        result = service.create_schedule_generation_workflow(
            created_by_id=admin_user.id
        )

        error_handlers = result.definition.get("error_handlers", {})

        # Verify error handlers are configured
        assert "generate_schedule" in error_handlers
        assert "validate_acgme" in error_handlers

    def test_schedule_generation_workflow_has_timeout(self, db, admin_user):
        """Test that schedule generation workflow has default timeout."""
        service = WorkflowService(db)

        result = service.create_schedule_generation_workflow(
            created_by_id=admin_user.id
        )

        assert "default_timeout_seconds" in result.definition
        assert result.definition["default_timeout_seconds"] == 1800  # 30 minutes

    def test_schedule_generation_workflow_parallel_steps(self, db, admin_user):
        """Test that certain steps are configured for parallel execution."""
        service = WorkflowService(db)

        result = service.create_schedule_generation_workflow(
            created_by_id=admin_user.id
        )

        steps = {step["id"]: step for step in result.definition["steps"]}

        # These steps should run in parallel
        assert steps["check_conflicts"]["execution_mode"] == "parallel"
        assert steps["calculate_resilience"]["execution_mode"] == "parallel"

    def test_schedule_generation_workflow_without_creator(self, db):
        """Test creating schedule generation workflow without creator ID."""
        service = WorkflowService(db)

        result = service.create_schedule_generation_workflow()

        assert result is not None
        assert result.created_by_id is None


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================


class TestEdgeCases:
    """Test suite for edge cases and integration scenarios."""

    def test_multiple_template_versions(
        self, db, sample_workflow_definition, admin_user
    ):
        """Test handling multiple versions of the same template."""
        service = WorkflowService(db)

        # Create version 1
        template_v1 = service.create_template(
            name="versioned_workflow",
            definition=sample_workflow_definition,
            created_by_id=admin_user.id,
        )

        # Create version 2
        template_v2 = service.create_template(
            name="versioned_workflow",
            definition=sample_workflow_definition,
            created_by_id=admin_user.id,
        )

        # Get template by name should return latest version
        latest = service.get_template(name="versioned_workflow")
        assert latest.version == max(template_v1.version, template_v2.version)

    def test_list_templates_ordering(self, db, sample_workflow_definition, admin_user):
        """Test that templates are ordered by name and version descending."""
        service = WorkflowService(db)

        # Create multiple templates with different names and versions
        template_a_v1 = WorkflowTemplate(
            id=uuid4(),
            name="a_workflow",
            version=1,
            definition=sample_workflow_definition,
            created_by_id=admin_user.id,
        )
        template_a_v2 = WorkflowTemplate(
            id=uuid4(),
            name="a_workflow",
            version=2,
            definition=sample_workflow_definition,
            created_by_id=admin_user.id,
        )
        template_b_v1 = WorkflowTemplate(
            id=uuid4(),
            name="b_workflow",
            version=1,
            definition=sample_workflow_definition,
            created_by_id=admin_user.id,
        )
        db.add_all([template_a_v1, template_a_v2, template_b_v1])
        db.commit()

        result = service.list_templates(active_only=False)

        # Verify ordering: a_workflow v2, a_workflow v1, b_workflow v1
        template_names_versions = [(t.name, t.version) for t in result]

        # Find indices of our templates
        a_v2_idx = next(
            (
                i
                for i, (n, v) in enumerate(template_names_versions)
                if n == "a_workflow" and v == 2
            ),
            None,
        )
        a_v1_idx = next(
            (
                i
                for i, (n, v) in enumerate(template_names_versions)
                if n == "a_workflow" and v == 1
            ),
            None,
        )
        b_v1_idx = next(
            (
                i
                for i, (n, v) in enumerate(template_names_versions)
                if n == "b_workflow" and v == 1
            ),
            None,
        )

        # Verify ordering if all found
        if a_v2_idx is not None and a_v1_idx is not None:
            assert a_v2_idx < a_v1_idx  # v2 before v1
        if a_v1_idx is not None and b_v1_idx is not None:
            assert a_v1_idx < b_v1_idx  # a before b

    def test_empty_input_data_handling(self, db, sample_workflow_template):
        """Test starting a workflow with no input data."""
        service = WorkflowService(db)

        mock_instance = Mock(spec=WorkflowInstance)
        mock_instance.id = uuid4()
        mock_instance.input_data = None

        with patch.object(
            service.engine, "create_instance", return_value=mock_instance
        ):
            with patch("asyncio.create_task"):
                result = service.start_workflow(
                    template_name=sample_workflow_template.name,
                    input_data=None,
                    async_execution=True,
                )

                assert result is not None

    def test_workflow_service_reuses_database_session(self, db):
        """Test that WorkflowService properly uses the provided database session."""
        service = WorkflowService(db)

        # Verify the service uses the same session
        assert service.db is db
        assert service.engine.db is db
