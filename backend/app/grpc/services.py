"""
gRPC Service Implementations for Residency Scheduler.

This module implements gRPC services for:
1. Schedule Operations: Generate, validate, and query schedules
2. Assignment Operations: Create, update, delete assignments
3. Person Operations: Query personnel data
4. Streaming Operations: Bulk data transfer for large datasets

Service Definitions:
- ScheduleService: Schedule generation and validation
- AssignmentService: Assignment CRUD operations
- PersonService: Personnel queries
- HealthService: Health checks

Note: In production, these would be generated from .proto files.
For this implementation, we use a simplified approach with manual serialization.
"""

import logging
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from uuid import UUID

import grpc

from app.db.session import SessionLocal
from app.grpc.converters import (
    from_proto_assignment,
    to_proto_assignment,
    to_proto_person,
)
from app.models.person import Person
from app.schemas.assignment import AssignmentResponse
from app.services.assignment_service import AssignmentService

logger = logging.getLogger(__name__)


class ScheduleServicer:
    """
    gRPC servicer for schedule operations.

    Provides RPCs for:
    - GenerateSchedule: Create new schedule for date range
    - ValidateSchedule: Check ACGME compliance
    - GetScheduleStatus: Query generation progress
    - StreamAssignments: Stream all assignments for a schedule (server streaming)
    """

    def GenerateSchedule(self, request: dict, context: grpc.ServicerContext) -> dict:
        """
        Generate a new schedule for specified date range.

        Args:
            request: Dict with:
                - start_date: ISO date string
                - end_date: ISO date string
                - optimization_level: "fast" | "balanced" | "optimal"
                - constraints: Optional constraints JSON
            context: gRPC context

        Returns:
            Dict with:
                - schedule_id: UUID of created schedule
                - status: "pending" | "running" | "completed" | "failed"
                - message: Status message
        """
        db = SessionLocal()
        try:
            # Extract request data
            start_date_str = request.get("start_date", "")
            end_date_str = request.get("end_date", "")
            optimization_level = request.get("optimization_level", "balanced")

            # Parse dates
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)

            # Validate date range
            if start_date > end_date:
                context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "start_date must be before or equal to end_date",
                )

            if (end_date - start_date).days > 365:
                context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "Date range cannot exceed 365 days",
                )

            # Get user from context (set by AuthenticationInterceptor)
            user_id = getattr(context, "user_id", None)
            if not user_id:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "User not authenticated")

            # Import scheduling service
            from app.services.cached_schedule_service import CachedScheduleService

            schedule_service = CachedScheduleService(db)

            # Generate schedule (simplified - in production this would be async)
            logger.info(
                f"Generating schedule: {start_date} to {end_date}, "
                f"level={optimization_level}, user={user_id}"
            )

            # For demonstration, we return a pending status
            # In production, this would trigger a Celery task
            result = {
                "schedule_id": "pending",
                "status": "pending",
                "message": f"Schedule generation queued for {start_date} to {end_date}",
                "created_at": datetime.utcnow().isoformat(),
            }

            return result

        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except Exception as e:
            logger.error(f"Error generating schedule: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Failed to generate schedule")
        finally:
            db.close()

    def ValidateSchedule(self, request: dict, context: grpc.ServicerContext) -> dict:
        """
        Validate ACGME compliance for assignments in date range.

        Args:
            request: Dict with:
                - start_date: ISO date string
                - end_date: ISO date string
            context: gRPC context

        Returns:
            Dict with:
                - is_compliant: Boolean
                - violations: List of violation messages
                - warnings: List of warning messages
        """
        db = SessionLocal()
        try:
            start_date_str = request.get("start_date", "")
            end_date_str = request.get("end_date", "")

            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)

            # Import validator
            from app.scheduling.validator import ACGMEValidator

            validator = ACGMEValidator(db)
            result = validator.validate_all(start_date, end_date)

            # Convert to proto-compatible format
            response = {
                "is_compliant": result.is_compliant,
                "violations": [
                    {
                        "person_id": str(v.person_id) if v.person_id else "",
                        "severity": v.severity,
                        "rule": v.rule,
                        "message": v.message,
                        "date": v.date.isoformat() if v.date else "",
                    }
                    for v in result.violations
                ],
                "warnings": result.warnings,
                "total_violations": len(result.violations),
            }

            return response

        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except Exception as e:
            logger.error(f"Error validating schedule: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Failed to validate schedule")
        finally:
            db.close()

    def StreamAssignments(
        self, request: dict, context: grpc.ServicerContext
    ) -> Iterator[dict]:
        """
        Stream assignments for a date range (server streaming RPC).

        This is more efficient than fetching all assignments at once for large datasets.

        Args:
            request: Dict with:
                - start_date: ISO date string
                - end_date: ISO date string
                - person_id: Optional UUID filter
                - batch_size: Optional batch size (default 100)
            context: gRPC context

        Yields:
            Dict for each assignment
        """
        db = SessionLocal()
        try:
            start_date_str = request.get("start_date", "")
            end_date_str = request.get("end_date", "")
            person_id_str = request.get("person_id", "")
            batch_size = request.get("batch_size", 100)

            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
            person_id = UUID(person_id_str) if person_id_str else None

            # Query assignments in batches
            service = AssignmentService(db)

            # For streaming, we query in batches to avoid loading everything into memory
            current_date = start_date
            total_streamed = 0

            while current_date <= end_date:
                batch_end = min(current_date + timedelta(days=30), end_date)

                # Query batch
                result = service.list_assignments(
                    start_date=current_date, end_date=batch_end, person_id=person_id
                )

                # Stream each assignment
                for assignment in result["items"]:
                    # Convert to AssignmentResponse if needed
                    if not isinstance(assignment, AssignmentResponse):
                        assignment = AssignmentResponse.from_orm(assignment)

                    # Convert to proto format and yield
                    proto_assignment = to_proto_assignment(assignment)
                    yield proto_assignment
                    total_streamed += 1

                    # Check if client cancelled
                    if context.is_active() is False:
                        logger.info(
                            f"Client cancelled streaming after {total_streamed} assignments"
                        )
                        return

                current_date = batch_end + timedelta(days=1)

            logger.info(f"Streamed {total_streamed} assignments")

        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except Exception as e:
            logger.error(f"Error streaming assignments: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Failed to stream assignments")
        finally:
            db.close()


class AssignmentServicer:
    """
    gRPC servicer for assignment operations.

    Provides RPCs for:
    - GetAssignment: Fetch single assignment by ID
    - CreateAssignment: Create new assignment
    - UpdateAssignment: Update existing assignment
    - DeleteAssignment: Delete assignment
    - ListAssignments: Query assignments with filters
    """

    def GetAssignment(self, request: dict, context: grpc.ServicerContext) -> dict:
        """
        Get a single assignment by ID.

        Args:
            request: Dict with:
                - id: Assignment UUID
            context: gRPC context

        Returns:
            Dict with assignment data
        """
        db = SessionLocal()
        try:
            assignment_id_str = request.get("id", "")
            assignment_id = UUID(assignment_id_str)

            service = AssignmentService(db)
            assignment = service.get_assignment(assignment_id)

            if not assignment:
                context.abort(grpc.StatusCode.NOT_FOUND, "Assignment not found")

            # Convert to response schema
            response = AssignmentResponse.from_orm(assignment)
            return to_proto_assignment(response)

        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except Exception as e:
            logger.error(f"Error getting assignment: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Failed to get assignment")
        finally:
            db.close()

    def CreateAssignment(self, request: dict, context: grpc.ServicerContext) -> dict:
        """
        Create a new assignment.

        Args:
            request: Dict with assignment data
            context: gRPC context

        Returns:
            Dict with created assignment
        """
        db = SessionLocal()
        try:
            # Get user from context
            user_id = getattr(context, "user_id", None)
            username = getattr(context, "username", "unknown")

            # Convert from proto format
            assignment_data = from_proto_assignment(request)

            service = AssignmentService(db)
            result = service.create_assignment(
                block_id=assignment_data["block_id"],
                person_id=assignment_data["person_id"],
                role=assignment_data["role"],
                created_by=username,
                rotation_template_id=assignment_data.get("rotation_template_id"),
                notes=assignment_data.get("notes"),
            )

            if result.get("error"):
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, result["error"])

            assignment = result["assignment"]
            response = AssignmentResponse.from_orm(assignment)

            # Return with ACGME warnings
            proto_response = to_proto_assignment(response)
            proto_response["acgme_warnings"] = result.get("acgme_warnings", [])
            proto_response["is_compliant"] = result.get("is_compliant", True)

            return proto_response

        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except Exception as e:
            logger.error(f"Error creating assignment: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Failed to create assignment")
        finally:
            db.close()

    def DeleteAssignment(self, request: dict, context: grpc.ServicerContext) -> dict:
        """
        Delete an assignment.

        Args:
            request: Dict with:
                - id: Assignment UUID
            context: gRPC context

        Returns:
            Dict with:
                - success: Boolean
                - message: Status message
        """
        db = SessionLocal()
        try:
            assignment_id_str = request.get("id", "")
            assignment_id = UUID(assignment_id_str)
            username = getattr(context, "username", "unknown")

            service = AssignmentService(db)
            result = service.delete_assignment(
                assignment_id=assignment_id, deleted_by=username
            )

            if result.get("error"):
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, result["error"])

            return {
                "success": result.get("success", False),
                "message": "Assignment deleted successfully",
            }

        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except Exception as e:
            logger.error(f"Error deleting assignment: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Failed to delete assignment")
        finally:
            db.close()


class PersonServicer:
    """
    gRPC servicer for person operations.

    Provides RPCs for:
    - GetPerson: Fetch single person by ID
    - ListPersons: Query persons with filters
    - StreamPersons: Stream all persons (for bulk export)
    """

    def GetPerson(self, request: dict, context: grpc.ServicerContext) -> dict:
        """
        Get a single person by ID.

        Args:
            request: Dict with:
                - id: Person UUID
            context: gRPC context

        Returns:
            Dict with person data
        """
        db = SessionLocal()
        try:
            person_id_str = request.get("id", "")
            person_id = UUID(person_id_str)

            person = db.query(Person).filter(Person.id == person_id).first()

            if not person:
                context.abort(grpc.StatusCode.NOT_FOUND, "Person not found")

            return to_proto_person(person)

        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except Exception as e:
            logger.error(f"Error getting person: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Failed to get person")
        finally:
            db.close()

    def ListPersons(self, request: dict, context: grpc.ServicerContext) -> dict:
        """
        List persons with optional filters.

        Args:
            request: Dict with:
                - type: Optional person type filter
                - specialty: Optional specialty filter
                - is_active: Optional active status filter
                - limit: Optional result limit
                - offset: Optional result offset
            context: gRPC context

        Returns:
            Dict with:
                - persons: List of person dicts
                - total: Total count
        """
        db = SessionLocal()
        try:
            person_type = request.get("type", "")
            specialty = request.get("specialty", "")
            is_active = request.get("is_active")
            limit = request.get("limit", 100)
            offset = request.get("offset", 0)

            # Build query
            query = db.query(Person)

            if person_type:
                query = query.filter(Person.type == person_type)
            if specialty:
                query = query.filter(Person.specialty == specialty)
            if is_active is not None:
                query = query.filter(Person.is_active == is_active)

            # Get total count
            total = query.count()

            # Apply pagination
            persons = query.offset(offset).limit(limit).all()

            # Convert to proto format
            return {
                "persons": [to_proto_person(p) for p in persons],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(f"Error listing persons: {e}", exc_info=True)
            context.abort(grpc.StatusCode.INTERNAL, "Failed to list persons")
        finally:
            db.close()


class HealthServicer:
    """
    gRPC servicer for health checks.

    Implements the standard gRPC health checking protocol.
    """

    def Check(self, request: dict, context: grpc.ServicerContext) -> dict:
        """
        Perform health check.

        Args:
            request: Dict with:
                - service: Optional service name to check
            context: gRPC context

        Returns:
            Dict with:
                - status: "SERVING" | "NOT_SERVING" | "UNKNOWN"
        """
        # Check database connectivity
        db = SessionLocal()
        try:
            # Simple query to verify DB is accessible
            db.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "unhealthy"
        finally:
            db.close()

        if db_status == "healthy":
            return {"status": "SERVING"}
        else:
            return {"status": "NOT_SERVING"}

    def Watch(self, request: dict, context: grpc.ServicerContext) -> Iterator[dict]:
        """
        Watch health status changes (server streaming RPC).

        Args:
            request: Dict with:
                - service: Optional service name to watch
            context: gRPC context

        Yields:
            Dict with status updates
        """
        # Initial status
        yield {"status": "SERVING"}

        # In production, this would monitor for status changes
        # For now, we just keep the stream open
        while context.is_active():
            import time

            time.sleep(30)  # Check every 30 seconds

            # Send periodic heartbeat
            yield {"status": "SERVING"}
