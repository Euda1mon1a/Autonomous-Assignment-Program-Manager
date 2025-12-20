"""Workflow service for managing workflow templates and instances.

This service provides high-level operations for:
- Creating and managing workflow templates
- Executing workflows
- Monitoring workflow progress
- Handling workflow errors
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.workflow import WorkflowInstance, WorkflowStatus, WorkflowTemplate
from app.workflow.engine import WorkflowEngine

logger = logging.getLogger(__name__)


class WorkflowService:
    """
    High-level service for workflow management.

    This service wraps the WorkflowEngine and provides business logic
    for common workflow operations in the Residency Scheduler application.
    """

    def __init__(self, db: Session):
        """
        Initialize workflow service.

        Args:
            db: Database session
        """
        self.db = db
        self.engine = WorkflowEngine(db)

    # ========================================================================
    # Template Management
    # ========================================================================

    def create_template(
        self,
        name: str,
        definition: dict[str, Any],
        description: str | None = None,
        tags: list[str] | None = None,
        created_by_id: UUID | None = None,
    ) -> WorkflowTemplate:
        """
        Create a new workflow template.

        Args:
            name: Template name
            definition: Workflow definition
            description: Template description
            tags: Tags for categorization
            created_by_id: ID of user creating template

        Returns:
            Created WorkflowTemplate

        Raises:
            ValueError: If template definition is invalid
        """
        try:
            template = self.engine.create_template(
                name=name,
                definition=definition,
                description=description,
                tags=tags,
                created_by_id=created_by_id,
            )
            self.db.commit()

            logger.info(
                f"Created workflow template '{name}' v{template.version} "
                f"by user {created_by_id}"
            )
            return template

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create workflow template '{name}': {str(e)}")
            raise

    def get_template(
        self,
        template_id: UUID | None = None,
        name: str | None = None,
        version: int | None = None,
    ) -> WorkflowTemplate | None:
        """
        Get workflow template by ID or name/version.

        Args:
            template_id: Template UUID
            name: Template name
            version: Template version (gets latest if not specified)

        Returns:
            WorkflowTemplate or None if not found
        """
        return self.engine.get_template(
            template_id=template_id,
            name=name,
            version=version,
        )

    def list_templates(
        self,
        active_only: bool = True,
        tags: list[str] | None = None,
    ) -> list[WorkflowTemplate]:
        """
        List all workflow templates.

        Args:
            active_only: Only return active templates
            tags: Filter by tags

        Returns:
            List of WorkflowTemplate instances
        """
        query = self.db.query(WorkflowTemplate)

        if active_only:
            query = query.filter(WorkflowTemplate.is_active == True)  # noqa: E712

        if tags:
            # Filter templates that have any of the specified tags
            query = query.filter(WorkflowTemplate.tags.contains(tags))

        return query.order_by(
            WorkflowTemplate.name,
            WorkflowTemplate.version.desc()
        ).all()

    def deactivate_template(self, template_id: UUID) -> WorkflowTemplate:
        """
        Deactivate a workflow template.

        Args:
            template_id: Template ID to deactivate

        Returns:
            Updated WorkflowTemplate

        Raises:
            ValueError: If template not found
        """
        template = self.get_template(template_id=template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        template.is_active = False
        self.db.commit()

        logger.info(f"Deactivated workflow template '{template.name}' v{template.version}")
        return template

    # ========================================================================
    # Workflow Instance Management
    # ========================================================================

    def start_workflow(
        self,
        template_name: str,
        input_data: dict[str, Any] | None = None,
        name: str | None = None,
        description: str | None = None,
        priority: int = 0,
        timeout_seconds: int | None = None,
        created_by_id: UUID | None = None,
        async_execution: bool = True,
    ) -> WorkflowInstance:
        """
        Start a new workflow execution.

        Args:
            template_name: Name of workflow template to execute
            input_data: Input parameters for workflow
            name: Custom instance name
            description: Instance description
            priority: Execution priority (0-100)
            timeout_seconds: Override default timeout
            created_by_id: ID of user starting workflow
            async_execution: Execute asynchronously (default) or wait for completion

        Returns:
            WorkflowInstance (RUNNING if async, terminal state if sync)

        Raises:
            ValueError: If template not found or invalid
        """
        # Get latest version of template
        template = self.engine.get_template(name=template_name)
        if not template:
            raise ValueError(f"Workflow template '{template_name}' not found")

        if not template.is_active:
            raise ValueError(
                f"Workflow template '{template_name}' v{template.version} is inactive"
            )

        try:
            # Create instance
            instance = self.engine.create_instance(
                template_id=template.id,
                input_data=input_data,
                name=name,
                description=description,
                priority=priority,
                timeout_seconds=timeout_seconds,
                created_by_id=created_by_id,
            )
            self.db.commit()

            # Start execution
            import asyncio
            if async_execution:
                # Execute asynchronously
                asyncio.create_task(
                    self.engine.execute_workflow(
                        instance_id=instance.id,
                        async_execution=True,
                    )
                )
                logger.info(
                    f"Started async workflow '{template_name}' "
                    f"instance {instance.id}"
                )
            else:
                # Execute synchronously (blocking)
                loop = asyncio.get_event_loop()
                instance = loop.run_until_complete(
                    self.engine.execute_workflow(
                        instance_id=instance.id,
                        async_execution=False,
                    )
                )
                logger.info(
                    f"Completed sync workflow '{template_name}' "
                    f"instance {instance.id}: {instance.status}"
                )

            return instance

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Failed to start workflow '{template_name}': {str(e)}",
                exc_info=True
            )
            raise

    def get_instance(self, instance_id: UUID) -> WorkflowInstance | None:
        """
        Get workflow instance with step executions.

        Args:
            instance_id: Workflow instance ID

        Returns:
            WorkflowInstance with eager-loaded steps or None
        """
        return self.engine.get_instance(instance_id=instance_id)

    def cancel_workflow(
        self,
        instance_id: UUID,
        reason: str,
        cancelled_by_id: UUID | None = None,
    ) -> WorkflowInstance:
        """
        Cancel a running workflow.

        Args:
            instance_id: Workflow instance ID
            reason: Cancellation reason
            cancelled_by_id: ID of user cancelling workflow

        Returns:
            Cancelled WorkflowInstance

        Raises:
            ValueError: If instance not found or cannot be cancelled
        """
        try:
            instance = self.engine.cancel_instance(
                instance_id=instance_id,
                reason=reason,
                cancelled_by_id=cancelled_by_id,
            )
            self.db.commit()

            logger.info(
                f"Cancelled workflow instance {instance_id} "
                f"by user {cancelled_by_id}: {reason}"
            )
            return instance

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cancel workflow {instance_id}: {str(e)}")
            raise

    # ========================================================================
    # Query and Monitoring
    # ========================================================================

    def list_instances(
        self,
        template_name: str | None = None,
        status: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        priority_min: int | None = None,
        priority_max: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[WorkflowInstance], int]:
        """
        List workflow instances with filters.

        Args:
            template_name: Filter by template name
            status: Filter by status
            created_after: Filter by creation date (after)
            created_before: Filter by creation date (before)
            priority_min: Filter by minimum priority
            priority_max: Filter by maximum priority
            limit: Maximum results to return
            offset: Offset for pagination

        Returns:
            Tuple of (list of instances, total count)
        """
        template_id = None
        if template_name:
            template = self.engine.get_template(name=template_name)
            if template:
                template_id = template.id

        return self.engine.query_instances(
            template_id=template_id,
            status=status,
            created_after=created_after,
            created_before=created_before,
            priority_min=priority_min,
            priority_max=priority_max,
            limit=limit,
            offset=offset,
        )

    def get_running_workflows(self, limit: int = 100) -> list[WorkflowInstance]:
        """
        Get all currently running workflows.

        Args:
            limit: Maximum results to return

        Returns:
            List of running WorkflowInstance objects
        """
        instances, _ = self.engine.query_instances(
            status=WorkflowStatus.RUNNING.value,
            limit=limit,
        )
        return instances

    def get_failed_workflows(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[WorkflowInstance]:
        """
        Get failed workflows for error investigation.

        Args:
            since: Only return failures after this time
            limit: Maximum results to return

        Returns:
            List of failed WorkflowInstance objects
        """
        instances, _ = self.engine.query_instances(
            status=WorkflowStatus.FAILED.value,
            created_after=since,
            limit=limit,
        )
        return instances

    def get_statistics(
        self,
        template_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Get workflow execution statistics.

        Args:
            template_name: Optional template name to filter statistics

        Returns:
            Dictionary of statistics
        """
        template_id = None
        if template_name:
            template = self.engine.get_template(name=template_name)
            if template:
                template_id = template.id

        return self.engine.get_statistics(template_id=template_id)

    # ========================================================================
    # Common Workflow Templates
    # ========================================================================

    def create_schedule_generation_workflow(
        self,
        created_by_id: UUID | None = None,
    ) -> WorkflowTemplate:
        """
        Create a workflow template for schedule generation.

        This workflow includes:
        1. Validate input parameters
        2. Generate schedule
        3. Validate ACGME compliance
        4. Check for conflicts (parallel)
        5. Calculate resilience metrics (parallel)
        6. Send notification

        Args:
            created_by_id: ID of user creating template

        Returns:
            Created WorkflowTemplate
        """
        definition = {
            "steps": [
                {
                    "id": "validate_input",
                    "name": "Validate Input Parameters",
                    "handler": "app.services.workflow_handlers.validate_schedule_input",
                    "execution_mode": "sequential",
                    "depends_on": [],
                    "retry_policy": {"max_attempts": 1},
                    "timeout_seconds": 10,
                },
                {
                    "id": "generate_schedule",
                    "name": "Generate Schedule",
                    "handler": "app.services.workflow_handlers.generate_schedule",
                    "execution_mode": "sequential",
                    "depends_on": ["validate_input"],
                    "retry_policy": {
                        "max_attempts": 3,
                        "backoff_multiplier": 2,
                        "max_backoff_seconds": 300,
                    },
                    "timeout_seconds": 600,
                },
                {
                    "id": "validate_acgme",
                    "name": "Validate ACGME Compliance",
                    "handler": "app.services.workflow_handlers.validate_acgme_compliance",
                    "execution_mode": "sequential",
                    "depends_on": ["generate_schedule"],
                    "retry_policy": {"max_attempts": 1},
                    "timeout_seconds": 60,
                },
                {
                    "id": "check_conflicts",
                    "name": "Check Schedule Conflicts",
                    "handler": "app.services.workflow_handlers.check_conflicts",
                    "execution_mode": "parallel",
                    "depends_on": ["validate_acgme"],
                    "retry_policy": {"max_attempts": 2},
                    "timeout_seconds": 120,
                },
                {
                    "id": "calculate_resilience",
                    "name": "Calculate Resilience Metrics",
                    "handler": "app.services.workflow_handlers.calculate_resilience",
                    "execution_mode": "parallel",
                    "depends_on": ["validate_acgme"],
                    "retry_policy": {"max_attempts": 2},
                    "timeout_seconds": 120,
                },
                {
                    "id": "send_notification",
                    "name": "Send Completion Notification",
                    "handler": "app.services.workflow_handlers.send_notification",
                    "execution_mode": "sequential",
                    "depends_on": ["check_conflicts", "calculate_resilience"],
                    "retry_policy": {
                        "max_attempts": 3,
                        "backoff_multiplier": 1.5,
                        "max_backoff_seconds": 60,
                    },
                    "timeout_seconds": 30,
                },
            ],
            "error_handlers": {
                "generate_schedule": "send_error_notification",
                "validate_acgme": "send_error_notification",
            },
            "default_timeout_seconds": 1800,  # 30 minutes
        }

        return self.create_template(
            name="schedule_generation",
            definition=definition,
            description="Automated schedule generation with validation and notifications",
            tags=["schedule", "acgme", "automated"],
            created_by_id=created_by_id,
        )
