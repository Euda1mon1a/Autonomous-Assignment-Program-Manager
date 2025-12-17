"""Event type definitions for resilience simulations.

This module defines the event types and data structures used to track
events during resilience simulations, including faculty events, zone
events, cascading failures, and cross-zone borrowing events.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class EventSeverity(str, Enum):
    """Severity levels for simulation events."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    CATASTROPHIC = "CATASTROPHIC"


class EventType(str, Enum):
    """Types of events that can occur during simulation."""

    ***REMOVED*** events
    FACULTY_SICK_CALL = "FACULTY_SICK_CALL"
    FACULTY_RETURN = "FACULTY_RETURN"
    FACULTY_RESIGNATION = "FACULTY_RESIGNATION"
    FACULTY_PCS = "FACULTY_PCS"

    # Zone events
    ZONE_DEGRADED = "ZONE_DEGRADED"
    ZONE_FAILED = "ZONE_FAILED"
    ZONE_RECOVERED = "ZONE_RECOVERED"

    # Cascade events
    CASCADE_STARTED = "CASCADE_STARTED"
    CASCADE_CONTAINED = "CASCADE_CONTAINED"
    CASCADE_SPREAD = "CASCADE_SPREAD"

    # Borrowing events
    BORROWING_REQUESTED = "BORROWING_REQUESTED"
    BORROWING_APPROVED = "BORROWING_APPROVED"
    BORROWING_DENIED = "BORROWING_DENIED"
    BORROWING_COMPLETED = "BORROWING_COMPLETED"

    # Simulation control events
    SIMULATION_START = "SIMULATION_START"
    SIMULATION_END = "SIMULATION_END"
    CHECKPOINT = "CHECKPOINT"


@dataclass
class SimulationEvent:
    """Base class for all simulation events.

    Attributes:
        id: Unique identifier for this event
        timestamp: Simulation time when event occurred
        event_type: Type of event
        severity: Severity level of the event
        description: Human-readable description of the event
        metadata: Additional event-specific data
    """

    id: UUID = field(default_factory=uuid4)
    timestamp: float = 0.0
    event_type: EventType = EventType.SIMULATION_START
    severity: EventSeverity = EventSeverity.INFO
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FacultyEvent(SimulationEvent):
    """Event related to faculty status changes.

    Attributes:
        faculty_id: ID of the affected faculty member
        faculty_name: Name of the faculty member
        zone_id: Zone the faculty belongs to (if applicable)
        duration_days: Duration of the event in days (for sick calls, etc.)
        is_permanent: Whether the change is permanent (resignation, PCS)
    """

    faculty_id: UUID = field(default_factory=uuid4)
    faculty_name: str = ""
    zone_id: UUID | None = None
    duration_days: float | None = None
    is_permanent: bool = False


@dataclass
class ZoneEvent(SimulationEvent):
    """Event related to zone status changes.

    Attributes:
        zone_id: ID of the affected zone
        zone_name: Name of the zone
        previous_status: Status before the event
        new_status: Status after the event
        faculty_affected: List of faculty IDs affected by this event
        services_affected: List of service names affected by this event
    """

    zone_id: UUID = field(default_factory=uuid4)
    zone_name: str = ""
    previous_status: str = ""
    new_status: str = ""
    faculty_affected: list[UUID] = field(default_factory=list)
    services_affected: list[str] = field(default_factory=list)


@dataclass
class CascadeEvent(SimulationEvent):
    """Event representing cascading failures across zones.

    Attributes:
        trigger_zone_id: ID of the zone that triggered the cascade
        trigger_event_id: ID of the event that triggered the cascade
        affected_zones: List of zone IDs affected by the cascade
        depth: Number of hops from the trigger zone
        was_contained: Whether the cascade was successfully contained
        containment_time: Time when cascade was contained (if applicable)
    """

    trigger_zone_id: UUID = field(default_factory=uuid4)
    trigger_event_id: UUID = field(default_factory=uuid4)
    affected_zones: list[UUID] = field(default_factory=list)
    depth: int = 1
    was_contained: bool = False
    containment_time: float | None = None


@dataclass
class BorrowingEvent(SimulationEvent):
    """Event related to cross-zone faculty borrowing.

    Attributes:
        requesting_zone_id: ID of the zone requesting faculty
        lending_zone_id: ID of the zone lending faculty
        faculty_id: ID of the faculty member being borrowed
        was_approved: Whether the borrowing request was approved
        denial_reason: Reason for denial (if not approved)
    """

    requesting_zone_id: UUID = field(default_factory=uuid4)
    lending_zone_id: UUID = field(default_factory=uuid4)
    faculty_id: UUID = field(default_factory=uuid4)
    was_approved: bool = False
    denial_reason: str | None = None


def create_event(event_type: EventType, **kwargs: Any) -> SimulationEvent:
    """Create a simulation event of the appropriate type.

    This helper function creates the appropriate event subclass based on
    the event type. It automatically selects the correct event class and
    passes through all provided keyword arguments.

    Args:
        event_type: The type of event to create
        **kwargs: Additional arguments to pass to the event constructor

    Returns:
        A SimulationEvent instance of the appropriate subclass

    Examples:
        >>> event = create_event(
        ...     EventType.FACULTY_SICK_CALL,
        ...     timestamp=10.0,
        ...     faculty_id=some_uuid,
        ...     faculty_name="John Doe",
        ...     duration_days=3.0
        ... )
        >>> isinstance(event, FacultyEvent)
        True
    """
    # Map event types to their corresponding event classes
    event_class_map: dict[EventType, type[SimulationEvent]] = {
        ***REMOVED*** events
        EventType.FACULTY_SICK_CALL: FacultyEvent,
        EventType.FACULTY_RETURN: FacultyEvent,
        EventType.FACULTY_RESIGNATION: FacultyEvent,
        EventType.FACULTY_PCS: FacultyEvent,
        # Zone events
        EventType.ZONE_DEGRADED: ZoneEvent,
        EventType.ZONE_FAILED: ZoneEvent,
        EventType.ZONE_RECOVERED: ZoneEvent,
        # Cascade events
        EventType.CASCADE_STARTED: CascadeEvent,
        EventType.CASCADE_CONTAINED: CascadeEvent,
        EventType.CASCADE_SPREAD: CascadeEvent,
        # Borrowing events
        EventType.BORROWING_REQUESTED: BorrowingEvent,
        EventType.BORROWING_APPROVED: BorrowingEvent,
        EventType.BORROWING_DENIED: BorrowingEvent,
        EventType.BORROWING_COMPLETED: BorrowingEvent,
    }

    # Get the appropriate event class, defaulting to base SimulationEvent
    event_class = event_class_map.get(event_type, SimulationEvent)

    # Ensure event_type is set
    kwargs["event_type"] = event_type

    # Set default severity if not provided
    if "severity" not in kwargs:
        kwargs["severity"] = _get_default_severity(event_type)

    # Create and return the event
    return event_class(**kwargs)


def _get_default_severity(event_type: EventType) -> EventSeverity:
    """Get the default severity for an event type.

    Args:
        event_type: The type of event

    Returns:
        The default severity level for this event type
    """
    severity_map: dict[EventType, EventSeverity] = {
        ***REMOVED*** events
        EventType.FACULTY_SICK_CALL: EventSeverity.WARNING,
        EventType.FACULTY_RETURN: EventSeverity.INFO,
        EventType.FACULTY_RESIGNATION: EventSeverity.CRITICAL,
        EventType.FACULTY_PCS: EventSeverity.CRITICAL,
        # Zone events
        EventType.ZONE_DEGRADED: EventSeverity.WARNING,
        EventType.ZONE_FAILED: EventSeverity.CRITICAL,
        EventType.ZONE_RECOVERED: EventSeverity.INFO,
        # Cascade events
        EventType.CASCADE_STARTED: EventSeverity.CRITICAL,
        EventType.CASCADE_CONTAINED: EventSeverity.WARNING,
        EventType.CASCADE_SPREAD: EventSeverity.CATASTROPHIC,
        # Borrowing events
        EventType.BORROWING_REQUESTED: EventSeverity.INFO,
        EventType.BORROWING_APPROVED: EventSeverity.INFO,
        EventType.BORROWING_DENIED: EventSeverity.WARNING,
        EventType.BORROWING_COMPLETED: EventSeverity.INFO,
        # Simulation control events
        EventType.SIMULATION_START: EventSeverity.INFO,
        EventType.SIMULATION_END: EventSeverity.INFO,
        EventType.CHECKPOINT: EventSeverity.INFO,
    }

    return severity_map.get(event_type, EventSeverity.INFO)
