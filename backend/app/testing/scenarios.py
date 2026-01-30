"""
Pre-built test scenarios for common workflows.

Provides ready-to-use test scenarios for:
- Schedule generation workflows
- Swap request workflows
- ACGME compliance testing
- Emergency coverage scenarios
- Resilience testing
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from uuid import uuid4

from app.testing.factories import (
    create_acgme_validation_response,
    create_assignment_response,
    create_resilience_health_response,
    create_schedule_generation_response,
    create_swap_request_response,
)
from app.testing.mock_server import MockAPIServer, MockResponse


@dataclass
class TestScenario(ABC):
    """
    Base class for test scenarios.

    Scenarios encapsulate common test setups and workflows.
    """

    name: str
    description: str
    mock_server: MockAPIServer | None = None

    @abstractmethod
    def setup(self, server: MockAPIServer) -> None:
        """
        Set up mock endpoints for this scenario.

        Args:
            server: Mock server to configure
        """
        pass

    @abstractmethod
    def get_expected_data(self) -> dict[str, Any]:
        """
        Get expected test data for this scenario.

        Returns:
            Dictionary of expected values
        """
        pass


class ScheduleGenerationScenario(TestScenario):
    """
    Scenario for testing schedule generation workflow.

    Simulates:
    1. Requesting schedule generation
    2. Polling job status
    3. Retrieving completed schedule
    4. Validating ACGME compliance
    """

    def __init__(self) -> None:
        """Initialize schedule generation scenario."""
        super().__init__(
            name="Schedule Generation",
            description="Complete workflow for generating and validating schedules",
        )
        self.job_id = str(uuid4())
        self.schedule_id = str(uuid4())

    def setup(self, server: MockAPIServer) -> None:
        """Set up schedule generation endpoints."""
        # Step 1: Start generation (returns job ID)
        server.register_endpoint(
            method="POST",
            path="/api/v1/schedule/generate",
            status_code=202,
            response=create_schedule_generation_response(
                job_id=self.job_id,
                status="pending",
            ),
        )

        # Step 2: Poll job status (stateful - goes from pending -> running -> completed)
        server.register_endpoint(
            method="GET",
            path=f"/api/v1/jobs/{self.job_id}",
            stateful=True,
            responses=[
                MockResponse(
                    status_code=200,
                    body={"job_id": self.job_id, "status": "pending"},
                ),
                MockResponse(
                    status_code=200,
                    body={"job_id": self.job_id, "status": "running", "progress": 50},
                ),
                MockResponse(
                    status_code=200,
                    body={
                        "job_id": self.job_id,
                        "status": "completed",
                        "result": {"schedule_id": self.schedule_id},
                    },
                ),
            ],
        )

        # Step 3: Get generated schedule
        server.register_endpoint(
            method="GET",
            path=f"/api/v1/schedules/{self.schedule_id}",
            response={
                "id": self.schedule_id,
                "assignments": self._generate_sample_assignments(),
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "acgme_compliant": True,
                },
            },
        )

        # Step 4: Validate ACGME compliance
        server.register_endpoint(
            method="POST",
            path="/api/v1/schedule/validate-acgme",
            response=create_acgme_validation_response(is_compliant=True),
        )

    def get_expected_data(self) -> dict[str, Any]:
        """Get expected data for this scenario."""
        return {
            "job_id": self.job_id,
            "schedule_id": self.schedule_id,
            "expected_status_sequence": ["pending", "running", "completed"],
        }

    def _generate_sample_assignments(self) -> list[dict[str, Any]]:
        """Generate sample assignments for testing."""
        assignments = []
        start_date = date.today()

        # Create 7 days of assignments
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            for time_of_day in ["AM", "PM"]:
                assignments.append(
                    {
                        "id": str(uuid4()),
                        "person_id": str(uuid4()),
                        "block_id": str(uuid4()),
                        "rotation_template_id": str(uuid4()),
                        "role": "primary",
                        "date": current_date.isoformat(),
                        "time_of_day": time_of_day,
                    }
                )

        return assignments


class SwapWorkflowScenario(TestScenario):
    """
    Scenario for testing swap request workflow.

    Simulates:
    1. Creating swap request
    2. Finding swap matches
    3. Approving swap
    4. Executing swap
    5. Verifying updated assignments
    """

    def __init__(self) -> None:
        """Initialize swap workflow scenario."""
        super().__init__(
            name="Swap Workflow",
            description="Complete workflow for requesting and executing swaps",
        )
        self.swap_id = str(uuid4())
        self.requester_id = str(uuid4())
        self.target_id = str(uuid4())

    def setup(self, server: MockAPIServer) -> None:
        """Set up swap workflow endpoints."""
        # Step 1: Create swap request
        server.register_endpoint(
            method="POST",
            path="/api/v1/swaps/requests",
            status_code=201,
            response=create_swap_request_response(
                swap_id=self.swap_id,
                status="pending",
                swap_type="one_to_one",
            ),
        )

        # Step 2: Find matches
        server.register_endpoint(
            method="GET",
            path=f"/api/v1/swaps/requests/{self.swap_id}/matches",
            response={
                "matches": [
                    {
                        "person_id": self.target_id,
                        "assignment_id": str(uuid4()),
                        "compatibility_score": 0.95,
                        "acgme_compliant": True,
                    }
                ]
            },
        )

        # Step 3: Approve swap
        server.register_endpoint(
            method="POST",
            path=f"/api/v1/swaps/requests/{self.swap_id}/approve",
            response={
                "id": self.swap_id,
                "status": "approved",
                "approved_at": datetime.utcnow().isoformat(),
            },
        )

        # Step 4: Execute swap (stateful - pending -> executing -> completed)
        server.register_endpoint(
            method="POST",
            path=f"/api/v1/swaps/requests/{self.swap_id}/execute",
            stateful=True,
            responses=[
                MockResponse(
                    status_code=202,
                    body={"id": self.swap_id, "status": "executing"},
                ),
                MockResponse(
                    status_code=200,
                    body={
                        "id": self.swap_id,
                        "status": "completed",
                        "executed_at": datetime.utcnow().isoformat(),
                    },
                ),
            ],
        )

        # Step 5: Verify assignments updated
        server.register_endpoint(
            method="GET",
            path="/api/v1/assignments",
            response={
                "assignments": [
                    create_assignment_response(person_id=self.target_id),
                    create_assignment_response(person_id=self.requester_id),
                ],
                "total": 2,
            },
        )

    def get_expected_data(self) -> dict[str, Any]:
        """Get expected data for this scenario."""
        return {
            "swap_id": self.swap_id,
            "requester_id": self.requester_id,
            "target_id": self.target_id,
            "expected_status_sequence": [
                "pending",
                "approved",
                "executing",
                "completed",
            ],
        }


class ACGMEComplianceScenario(TestScenario):
    """
    Scenario for testing ACGME compliance validation.

    Tests:
    1. Valid compliant schedule
    2. 80-hour rule violation
    3. 1-in-7 rule violation
    4. Supervision ratio violation
    """

    def __init__(self, violation_type: str | None = None) -> None:
        """
        Initialize ACGME compliance scenario.

        Args:
            violation_type: Type of violation to simulate (None for compliant)
        """
        super().__init__(
            name="ACGME Compliance",
            description=f"Test ACGME compliance validation ({violation_type or 'compliant'})",
        )
        self.violation_type = violation_type

    def setup(self, server: MockAPIServer) -> None:
        """Set up ACGME validation endpoints."""
        if self.violation_type == "80_hour":
            response = create_acgme_validation_response(
                is_compliant=False,
                violations=[
                    {
                        "rule": "80_hour_week",
                        "person_id": str(uuid4()),
                        "week_start": date.today().isoformat(),
                        "hours": 85,
                        "message": "Resident worked 85 hours in week, exceeds 80-hour limit",
                    }
                ],
            )
        elif self.violation_type == "one_in_seven":
            response = create_acgme_validation_response(
                is_compliant=False,
                violations=[
                    {
                        "rule": "one_in_seven",
                        "person_id": str(uuid4()),
                        "period_start": date.today().isoformat(),
                        "days_without_off": 8,
                        "message": "Resident worked 8 consecutive days without 24-hour off period",
                    }
                ],
            )
        elif self.violation_type == "supervision":
            response = create_acgme_validation_response(
                is_compliant=False,
                violations=[
                    {
                        "rule": "supervision_ratio",
                        "block_id": str(uuid4()),
                        "ratio": "1:6",
                        "required": "1:4",
                        "message": "Supervision ratio of 1:6 exceeds required 1:4 for PGY-2/3",
                    }
                ],
            )
        else:
            # Compliant
            response = create_acgme_validation_response(is_compliant=True)

        server.register_endpoint(
            method="POST",
            path="/api/v1/schedule/validate-acgme",
            response=response,
        )

    def get_expected_data(self) -> dict[str, Any]:
        """Get expected data for this scenario."""
        return {
            "violation_type": self.violation_type,
            "is_compliant": self.violation_type is None,
        }


class EmergencyCoverageScenario(TestScenario):
    """
    Scenario for testing emergency coverage workflows.

    Simulates:
    1. Emergency absence reported
    2. Coverage gap detected
    3. Auto-coverage attempted
    4. Manual coverage assignment
    5. Resilience check
    """

    def __init__(self) -> None:
        """Initialize emergency coverage scenario."""
        super().__init__(
            name="Emergency Coverage",
            description="Test emergency absence and coverage workflows",
        )
        self.absence_id = str(uuid4())
        self.affected_person_id = str(uuid4())
        self.coverage_person_id = str(uuid4())

    def setup(self, server: MockAPIServer) -> None:
        """Set up emergency coverage endpoints."""
        # Step 1: Report emergency absence
        server.register_endpoint(
            method="POST",
            path="/api/v1/absences",
            status_code=201,
            response={
                "id": self.absence_id,
                "person_id": self.affected_person_id,
                "absence_type": "emergency_leave",
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=10)).isoformat(),
                "is_blocking": True,
                "return_date_tentative": True,
            },
        )

        # Step 2: Check for coverage gaps
        server.register_endpoint(
            method="GET",
            path="/api/v1/coverage/gaps",
            response={
                "gaps": [
                    {
                        "block_id": str(uuid4()),
                        "date": date.today().isoformat(),
                        "time_of_day": "AM",
                        "rotation": "FMIT",
                        "affected_by": self.absence_id,
                    }
                ]
            },
        )

        # Step 3: Attempt auto-coverage
        server.register_endpoint(
            method="POST",
            path="/api/v1/coverage/auto-assign",
            response={
                "coverage_assigned": True,
                "assignments": [
                    {
                        "block_id": str(uuid4()),
                        "person_id": self.coverage_person_id,
                        "rotation_template_id": str(uuid4()),
                        "is_coverage": True,
                    }
                ],
            },
        )

        # Step 4: Check resilience
        server.register_endpoint(
            method="GET",
            path="/health/resilience",
            response=create_resilience_health_response(
                status="operational",
                utilization=0.75,  # Elevated from normal 0.65 due to coverage
                defense_level="YELLOW",  # Elevated from GREEN
            ),
        )

    def get_expected_data(self) -> dict[str, Any]:
        """Get expected data for this scenario."""
        return {
            "absence_id": self.absence_id,
            "affected_person_id": self.affected_person_id,
            "coverage_person_id": self.coverage_person_id,
            "expected_defense_level": "YELLOW",
        }


class ResilienceLoadScenario(TestScenario):
    """
    Scenario for testing resilience under load.

    Simulates progressive load increases and defense level changes.
    """

    def __init__(self) -> None:
        """Initialize resilience load scenario."""
        super().__init__(
            name="Resilience Load",
            description="Test resilience system under increasing load",
        )

    def setup(self, server: MockAPIServer) -> None:
        """Set up resilience endpoints with stateful responses."""
        # Stateful resilience check - shows progression through defense levels
        server.register_endpoint(
            method="GET",
            path="/health/resilience",
            stateful=True,
            responses=[
                MockResponse(
                    status_code=200,
                    body=create_resilience_health_response(
                        status="operational",
                        utilization=0.65,
                        defense_level="GREEN",
                    ),
                ),
                MockResponse(
                    status_code=200,
                    body=create_resilience_health_response(
                        status="operational",
                        utilization=0.80,
                        defense_level="YELLOW",
                    ),
                ),
                MockResponse(
                    status_code=200,
                    body=create_resilience_health_response(
                        status="degraded",
                        utilization=0.90,
                        defense_level="ORANGE",
                    ),
                ),
                MockResponse(
                    status_code=200,
                    body=create_resilience_health_response(
                        status="degraded",
                        utilization=0.95,
                        defense_level="RED",
                    ),
                ),
            ],
        )

    def get_expected_data(self) -> dict[str, Any]:
        """Get expected data for this scenario."""
        return {
            "defense_level_sequence": ["GREEN", "YELLOW", "ORANGE", "RED"],
            "utilization_sequence": [0.65, 0.80, 0.90, 0.95],
        }


def create_scenario(
    scenario_type: str,
    **kwargs,
) -> TestScenario:
    """
    Create a test scenario by type.

    Args:
        scenario_type: Type of scenario to create
        **kwargs: Additional arguments for scenario

    Returns:
        TestScenario instance

    Raises:
        ValueError: If scenario type is unknown

    Example:
        ```python
        scenario = create_scenario("schedule_generation")
        server = MockAPIServer()
        scenario.setup(server)
        ```
    """
    scenarios = {
        "schedule_generation": ScheduleGenerationScenario,
        "swap_workflow": SwapWorkflowScenario,
        "acgme_compliance": ACGMEComplianceScenario,
        "emergency_coverage": EmergencyCoverageScenario,
        "resilience_load": ResilienceLoadScenario,
    }

    if scenario_type not in scenarios:
        raise ValueError(
            f"Unknown scenario type: {scenario_type}. "
            f"Available: {', '.join(scenarios.keys())}"
        )

    return scenarios[scenario_type](**kwargs)


def load_scenario(
    scenario: TestScenario,
    server: MockAPIServer,
) -> dict[str, Any]:
    """
    Load a scenario into a mock server.

    Args:
        scenario: Scenario to load
        server: Mock server to configure

    Returns:
        Expected data for the scenario

    Example:
        ```python
        server = MockAPIServer()
        scenario = ScheduleGenerationScenario()
        expected_data = load_scenario(scenario, server)
        ```
    """
    scenario.setup(server)
    return scenario.get_expected_data()
