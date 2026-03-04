# Lecture Scheduling & Academic Tracking Feature Plan

> **Created:** 2025-12-22
> **Status:** Planning - Awaiting Approval
> **Priority:** Medium-High
> **Estimated Phases:** 5

This document outlines the comprehensive planning for academic scheduling features including faculty lectures, resident lectures, simulation labs, and a user feature request system.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Feature Overview](#feature-overview)
3. [Data Model Design](#data-model-design)
4. [Phase 1: Core Faculty Lectures](#phase-1-core-faculty-lectures)
5. [Phase 2: Resident Lectures](#phase-2-resident-lectures)
6. [Phase 3: Simulation Labs](#phase-3-simulation-labs)
7. [Phase 4: Automated Reminders](#phase-4-automated-reminders)
8. [Phase 5: User Feature Requests](#phase-5-user-feature-requests)
9. [API Endpoints](#api-endpoints)
10. [UI Components](#ui-components)
11. [Testing Strategy](#testing-strategy)
12. [Migration Strategy](#migration-strategy)
13. [Open Questions](#open-questions)

---

## Executive Summary

### Problem Statement

The residency program needs to:
1. **Track faculty lecture delivery** against expectations with automated follow-up
2. **Manage 18-month rotating lecture schedules** to ensure comprehensive topic coverage
3. **Track resident lecture requirements** with automated reminders
4. **Manage simulation lab rotations** (18-month cycle) to avoid repetition
5. **Capture user feedback** through a feature request system

### Proposed Solution

A comprehensive academic tracking system that:
- Maintains lecture topic catalogs with 18-month rotation schedules
- Tracks delivered vs. expected lectures for faculty and residents
- Sends automated email reminders when lectures are not scheduled
- Manages simulation lab rotation to ensure variety
- Provides a user-facing feature request submission system

---

## Feature Overview

### Feature 1: Core Faculty Lectures

| Aspect | Details |
|--------|---------|
| **Purpose** | Track faculty lecture commitments and ensure topics are covered |
| **Rotation Period** | 18 months |
| **Tracking** | Lectures given vs. expected per faculty member |
| **Automation** | Email reminders when lectures are not scheduled |
| **Users** | Program Directors, Coordinators, Core Faculty |

### Feature 2: Resident Lectures

| Aspect | Details |
|--------|---------|
| **Purpose** | Track resident lecture requirements for graduation |
| **Tracking** | Lectures given vs. required per resident |
| **Automation** | Email reminders for overdue requirements |
| **Users** | Program Directors, Residents, Coordinators |

### Feature 3: Simulation Labs

| Aspect | Details |
|--------|---------|
| **Purpose** | Rotate simulation lab topics to ensure variety |
| **Rotation Period** | 18 months |
| **Goal** | Prevent repetition, ensure comprehensive procedural training |
| **Users** | Simulation Coordinators, Faculty, Residents |

### Feature 4: User Feature Requests

| Aspect | Details |
|--------|---------|
| **Purpose** | Allow users to submit and track feature requests |
| **Users** | All authenticated users |
| **Management** | Admin review, prioritization, status tracking |

---

## Data Model Design

### New Models Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LECTURE MANAGEMENT                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐      ┌─────────────────────┐                   │
│  │  LectureTopic   │──────│ LectureAssignment   │                   │
│  │                 │      │                     │                   │
│  │ - name          │      │ - topic_id (FK)     │                   │
│  │ - category      │      │ - presenter_id (FK) │                   │
│  │ - target_month  │      │ - scheduled_date    │                   │
│  │ - cycle_position│      │ - status            │                   │
│  │ - presenter_type│      │ - delivered_date    │                   │
│  │ - required_pgy  │      │ - attendee_count    │                   │
│  └─────────────────┘      └─────────────────────┘                   │
│                                                                      │
│  ┌─────────────────┐      ┌─────────────────────┐                   │
│  │ SimulationTopic │──────│ SimulationSession   │                   │
│  │                 │      │                     │                   │
│  │ - name          │      │ - topic_id (FK)     │                   │
│  │ - category      │      │ - scheduled_date    │                   │
│  │ - cycle_position│      │ - status            │                   │
│  │ - equipment_req │      │ - instructor_id     │                   │
│  │ - duration_hours│      │ - participants      │                   │
│  └─────────────────┘      └─────────────────────┘                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     REQUIREMENT TRACKING                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              PersonLectureRequirement                        │    │
│  │                                                              │    │
│  │  - person_id (FK)                                           │    │
│  │  - academic_year                                            │    │
│  │  - lectures_required (int)                                  │    │
│  │  - lectures_delivered (int, computed)                       │    │
│  │  - last_reminder_sent                                       │    │
│  │  - reminder_count                                           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      FEATURE REQUESTS                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    FeatureRequest                            │    │
│  │                                                              │    │
│  │  - id (UUID)                                                │    │
│  │  - submitter_id (FK to Person)                              │    │
│  │  - title                                                    │    │
│  │  - description                                              │    │
│  │  - category (enum)                                          │    │
│  │  - status (enum)                                            │    │
│  │  - priority (enum)                                          │    │
│  │  - vote_count                                               │    │
│  │  - admin_notes                                              │    │
│  │  - created_at, updated_at                                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   FeatureRequestVote                         │    │
│  │                                                              │    │
│  │  - feature_request_id (FK)                                  │    │
│  │  - voter_id (FK to Person)                                  │    │
│  │  - created_at                                               │    │
│  │  (unique constraint: one vote per user per request)         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Core Faculty Lectures

### 1.1 Lecture Topic Catalog Model

**File to create:** `backend/app/models/lecture_topic.py`

```python
"""
Lecture topic catalog with 18-month rotation scheduling.

Tracks all potential lecture topics that should be covered within
an 18-month academic cycle.
"""

class LectureCategory(str, Enum):
    """Categories for organizing lecture topics."""
    CORE_CURRICULUM = "core_curriculum"       # Required medical knowledge
    SPECIALTY = "specialty"                    # Specialty-specific topics
    PROCEDURES = "procedures"                  # Procedural training
    RESEARCH = "research"                      # Research methodology
    QUALITY_IMPROVEMENT = "quality_improvement"
    PROFESSIONALISM = "professionalism"
    COMMUNICATION = "communication"
    PRACTICE_MANAGEMENT = "practice_management"

class PresenterType(str, Enum):
    """Who is expected to present this lecture type."""
    FACULTY = "faculty"
    RESIDENT = "resident"
    GUEST = "guest"
    ANY = "any"

class LectureTopic(Base):
    """
    Master catalog of lecture topics for the 18-month rotation.

    Each topic has a target month within the 18-month cycle for
    when it should be scheduled.
    """
    __tablename__ = "lecture_topics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Topic details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)  # LectureCategory

    # 18-month rotation scheduling
    cycle_position = Column(Integer, nullable=False)  # 1-18 (month within cycle)
    target_week = Column(Integer)  # Optional: specific week within month (1-4)

    # Presenter requirements
    presenter_type = Column(String(20), default="faculty")  # PresenterType
    required_specialty = Column(String(100))  # If specialty-specific
    required_pgy_level = Column(Integer)  # For resident presenters

    # Duration and format
    duration_minutes = Column(Integer, default=60)
    is_recurring = Column(Boolean, default=True)  # Repeats each 18-month cycle

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    created_by = Column(GUID(), ForeignKey("persons.id"))

    # Relationships
    assignments = relationship("LectureAssignment", back_populates="topic")
```

### 1.2 Lecture Assignment Model

**File to create:** `backend/app/models/lecture_assignment.py`

```python
"""
Tracks individual lecture assignments (scheduled and delivered).
"""

class LectureStatus(str, Enum):
    """Status of a lecture assignment."""
    SCHEDULED = "scheduled"       # Assigned and scheduled
    PENDING = "pending"           # Needs to be scheduled
    DELIVERED = "delivered"       # Successfully presented
    CANCELLED = "cancelled"       # Was cancelled
    RESCHEDULED = "rescheduled"   # Moved to different date
    NO_SHOW = "no_show"           # Presenter didn't show

class LectureAssignment(Base):
    """
    Individual lecture assignment tracking.

    Links a topic to a presenter with scheduling and delivery tracking.
    """
    __tablename__ = "lecture_assignments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    topic_id = Column(GUID(), ForeignKey("lecture_topics.id"), nullable=False)
    presenter_id = Column(GUID(), ForeignKey("persons.id"), nullable=False)

    # Scheduling
    academic_year = Column(String(9), nullable=False)  # "2024-2025"
    cycle_number = Column(Integer, default=1)  # Which 18-month cycle
    scheduled_date = Column(Date)
    scheduled_time = Column(Time)
    location = Column(String(100))

    # Status tracking
    status = Column(String(20), default="pending")  # LectureStatus

    # Delivery tracking
    delivered_date = Column(Date)
    attendee_count = Column(Integer)
    evaluation_score = Column(Float)  # Optional feedback score

    # Reminder tracking
    reminder_sent_at = Column(DateTime)
    reminder_count = Column(Integer, default=0)

    # Notes
    notes = Column(Text)
    cancellation_reason = Column(String(200))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    assigned_by = Column(GUID(), ForeignKey("persons.id"))

    # Relationships
    topic = relationship("LectureTopic", back_populates="assignments")
    presenter = relationship("Person", foreign_keys=[presenter_id])
```

### 1.3 Faculty Lecture Requirement Tracking

**File to create:** `backend/app/models/lecture_requirement.py`

```python
"""
Tracks lecture requirements per person per academic year.
"""

class PersonLectureRequirement(Base):
    """
    Tracks lecture delivery requirements for faculty and residents.

    Computed fields track progress toward requirements.
    """
    __tablename__ = "person_lecture_requirements"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    person_id = Column(GUID(), ForeignKey("persons.id"), nullable=False)
    academic_year = Column(String(9), nullable=False)  # "2024-2025"

    # Requirements
    lectures_required = Column(Integer, nullable=False)

    # Tracking (computed via query, cached here)
    lectures_scheduled = Column(Integer, default=0)
    lectures_delivered = Column(Integer, default=0)

    # Reminder state
    last_reminder_sent = Column(DateTime)
    reminder_count = Column(Integer, default=0)
    next_reminder_date = Column(Date)

    # Notes
    notes = Column(Text)
    exemption_reason = Column(String(200))  # If exempted from requirements
    is_exempt = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('person_id', 'academic_year', name='uq_person_year_req'),
    )

    # Relationships
    person = relationship("Person", back_populates="lecture_requirements")

    @property
    def is_on_track(self) -> bool:
        """Check if person is on track for requirements."""
        if self.is_exempt:
            return True
        return self.lectures_delivered >= self._expected_by_now()

    @property
    def lectures_remaining(self) -> int:
        """Calculate remaining lectures needed."""
        return max(0, self.lectures_required - self.lectures_delivered)
```

### 1.4 18-Month Rotation Schedule Service

**File to create:** `backend/app/services/lecture_rotation_service.py`

```python
"""
Service for managing the 18-month lecture rotation schedule.

Responsibilities:
- Generate rotation schedules for each 18-month cycle
- Auto-assign lectures to faculty based on specialty/availability
- Identify gaps in coverage
- Generate reminder schedules
"""

class LectureRotationService:
    """Manages 18-month lecture topic rotation."""

    CYCLE_MONTHS = 18

    def __init__(self, db: Session):
        self.db = db

    async def generate_cycle_schedule(
        self,
        start_date: date,
        faculty_ids: list[UUID] | None = None
    ) -> list[LectureAssignment]:
        """
        Generate lecture assignments for an 18-month cycle.

        Algorithm:
        1. Get all active topics ordered by cycle_position
        2. For each topic:
           - Calculate target date based on cycle_position
           - Find eligible presenters (by specialty, availability)
           - Create pending assignment
        3. Return assignments for review/approval
        """
        pass

    async def get_unscheduled_topics(
        self,
        academic_year: str,
        months_ahead: int = 3
    ) -> list[LectureTopic]:
        """
        Find topics that should be scheduled soon but aren't.

        Returns topics whose target month is within months_ahead
        that don't have an assignment.
        """
        pass

    async def get_faculty_lecture_status(
        self,
        faculty_id: UUID,
        academic_year: str
    ) -> dict:
        """
        Get lecture delivery status for a faculty member.

        Returns:
            {
                "required": int,
                "delivered": int,
                "scheduled": int,
                "remaining": int,
                "on_track": bool,
                "next_scheduled": date | None,
                "upcoming_topics": list[dict]
            }
        """
        pass

    async def get_cycle_coverage_report(
        self,
        cycle_start: date
    ) -> dict:
        """
        Generate coverage report for an 18-month cycle.

        Shows which topics are:
        - Delivered
        - Scheduled
        - Unassigned
        - Past due
        """
        pass
```

---

## Phase 2: Resident Lectures

### 2.1 Resident Lecture Requirements

Resident lecture requirements differ from faculty:
- Requirements vary by PGY level
- Typically fewer lectures but still tracked
- Often tied to graduation requirements

**Configuration approach:**

```python
# Default resident lecture requirements (configurable)
RESIDENT_LECTURE_REQUIREMENTS = {
    1: {"required": 1, "description": "Grand rounds presentation"},
    2: {"required": 2, "description": "Topic presentations"},
    3: {"required": 2, "description": "Senior presentations + QI"},
}
```

### 2.2 Resident Lecture Tracking Service

**File to create:** `backend/app/services/resident_lecture_service.py`

```python
"""
Service for tracking resident lecture requirements.

Differs from faculty tracking:
- Graduation requirement tracking
- PGY-level specific requirements
- Milestone integration (ACGME milestones)
"""

class ResidentLectureService:
    """Manages resident lecture requirement tracking."""

    def __init__(self, db: Session):
        self.db = db

    async def get_resident_progress(
        self,
        resident_id: UUID
    ) -> ResidentLectureProgress:
        """
        Get resident's lecture progress across their training.

        Returns cumulative progress, not just current year.
        """
        pass

    async def get_graduation_readiness(
        self,
        resident_id: UUID
    ) -> dict:
        """
        Check if resident has met lecture requirements for graduation.
        """
        pass

    async def get_residents_needing_reminders(self) -> list[Person]:
        """
        Find residents who are behind on lecture requirements.
        """
        pass
```

---

## Phase 3: Simulation Labs

### 3.1 Simulation Topic Model

**File to create:** `backend/app/models/simulation_topic.py`

```python
"""
Simulation lab topic catalog with 18-month rotation.

Ensures variety in simulation training - prevents repeating
the same scenarios within the 18-month window.
"""

class SimulationCategory(str, Enum):
    """Categories for simulation topics."""
    ACLS = "acls"                    # Advanced Cardiac Life Support
    PALS = "pals"                    # Pediatric Advanced Life Support
    TRAUMA = "trauma"                # Trauma scenarios
    OB_EMERGENCIES = "ob_emergencies"
    PROCEDURES = "procedures"        # Procedural skills
    COMMUNICATION = "communication"  # Difficult conversations
    TEAM_TRAINING = "team_training"  # CRM, handoffs

class SimulationTopic(Base):
    """
    Master catalog of simulation lab topics.
    """
    __tablename__ = "simulation_topics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Topic details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)  # SimulationCategory

    # 18-month rotation
    cycle_position = Column(Integer, nullable=False)  # 1-18

    # Requirements
    equipment_required = Column(ARRAY(String))  # ["manikin", "ultrasound", etc.]
    room_type = Column(String(50))  # "sim_lab", "procedure_room", etc.
    duration_hours = Column(Float, default=2.0)
    min_participants = Column(Integer, default=2)
    max_participants = Column(Integer, default=8)

    # Instructor requirements
    requires_faculty = Column(Boolean, default=True)
    required_specialty = Column(String(100))

    # Prerequisites
    prerequisite_topic_id = Column(GUID(), ForeignKey("simulation_topics.id"))

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    sessions = relationship("SimulationSession", back_populates="topic")
    prerequisite = relationship("SimulationTopic", remote_side=[id])
```

### 3.2 Simulation Session Model

**File to create:** `backend/app/models/simulation_session.py`

```python
"""
Individual simulation lab session tracking.
"""

class SimulationStatus(str, Enum):
    """Status of a simulation session."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class SimulationSession(Base):
    """
    Individual simulation session instance.
    """
    __tablename__ = "simulation_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    topic_id = Column(GUID(), ForeignKey("simulation_topics.id"), nullable=False)
    instructor_id = Column(GUID(), ForeignKey("persons.id"))

    # Scheduling
    scheduled_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time)
    location = Column(String(100))

    # Status
    status = Column(String(20), default="scheduled")

    # Participation tracking
    participants = Column(ARRAY(GUID()))  # Array of person IDs
    participant_count = Column(Integer)

    # Cycle tracking
    cycle_number = Column(Integer, default=1)
    academic_year = Column(String(9))

    # Feedback
    feedback_score = Column(Float)
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    topic = relationship("SimulationTopic", back_populates="sessions")
    instructor = relationship("Person")
```

### 3.3 Simulation Rotation Service

**File to create:** `backend/app/services/simulation_rotation_service.py`

```python
"""
Service for managing simulation lab 18-month rotation.

Key responsibilities:
- Ensure no topic repeats within 18 months
- Track equipment/room availability
- Manage participant tracking
- Generate rotation schedule
"""

class SimulationRotationService:
    """Manages 18-month simulation lab rotation."""

    CYCLE_MONTHS = 18

    def __init__(self, db: Session):
        self.db = db

    async def generate_cycle_schedule(
        self,
        start_date: date
    ) -> list[SimulationSession]:
        """
        Generate simulation schedule for 18-month cycle.

        Ensures:
        - Topics don't repeat within cycle
        - Equipment availability
        - Faculty coverage
        """
        pass

    async def check_topic_repetition(
        self,
        topic_id: UUID,
        proposed_date: date
    ) -> bool:
        """
        Check if scheduling this topic would violate 18-month rule.

        Returns True if topic was already done within last 18 months.
        """
        pass

    async def get_upcoming_schedule(
        self,
        months: int = 3
    ) -> list[SimulationSession]:
        """Get scheduled simulations for next N months."""
        pass

    async def get_coverage_gaps(self) -> list[SimulationTopic]:
        """Find topics that haven't been covered in current cycle."""
        pass
```

---

## Phase 4: Automated Reminders

### 4.1 Lecture Reminder Task

**File to create:** `backend/app/tasks/lecture_reminder_tasks.py`

```python
"""
Celery tasks for automated lecture reminders.

Schedule:
- Daily check for faculty with unscheduled lectures
- Weekly reminder for upcoming lectures (7 days)
- Monthly summary to Program Director
"""
from celery import shared_task
from app.core.celery_app import celery_app

@shared_task(
    bind=True,
    name="app.tasks.lecture_reminder_tasks.check_unscheduled_lectures",
    max_retries=3,
)
def check_unscheduled_lectures(self):
    """
    Daily task: Find faculty who should have scheduled lectures.

    Logic:
    1. Get all faculty with lecture requirements
    2. For each, check if they have lectures scheduled in next 30 days
    3. If not, and they're behind on requirements, send reminder
    4. Respect reminder cooldown (don't spam - max 1 per week)
    """
    pass

@shared_task(
    bind=True,
    name="app.tasks.lecture_reminder_tasks.send_upcoming_reminders",
)
def send_upcoming_reminders(self):
    """
    Daily task: Remind presenters of upcoming lectures.

    Sends reminders:
    - 7 days before: Initial reminder with preparation time
    - 1 day before: Final reminder with logistics
    """
    pass

@shared_task(
    bind=True,
    name="app.tasks.lecture_reminder_tasks.send_monthly_pd_summary",
)
def send_monthly_pd_summary(self):
    """
    Monthly task: Send lecture coverage summary to PD.

    Includes:
    - Faculty lecture delivery rates
    - Topics covered vs. scheduled
    - Residents behind on requirements
    - Coverage gaps in rotation
    """
    pass
```

### 4.2 Celery Beat Schedule Addition

**Addition to:** `backend/app/core/celery_app.py`

```python
# Add to beat_schedule dict:

"lecture-unscheduled-check": {
    "task": "app.tasks.lecture_reminder_tasks.check_unscheduled_lectures",
    "schedule": crontab(hour=8, minute=0, day_of_week="1-5"),  # Weekdays 8 AM
    "options": {"queue": "notifications"},
},

"lecture-upcoming-reminders": {
    "task": "app.tasks.lecture_reminder_tasks.send_upcoming_reminders",
    "schedule": crontab(hour=7, minute=0),  # Daily 7 AM
    "options": {"queue": "notifications"},
},

"lecture-monthly-pd-summary": {
    "task": "app.tasks.lecture_reminder_tasks.send_monthly_pd_summary",
    "schedule": crontab(day_of_month=1, hour=9, minute=0),  # 1st of month
    "options": {"queue": "notifications"},
},

"simulation-rotation-check": {
    "task": "app.tasks.simulation_tasks.check_rotation_coverage",
    "schedule": crontab(hour=8, minute=30, day_of_week="1"),  # Monday 8:30 AM
    "options": {"queue": "notifications"},
},
```

### 4.3 Notification Templates

**Addition to:** `backend/app/notifications/notification_types.py`

```python
# New notification types for lecture system

class NotificationType(str, Enum):
    # ... existing types ...

    # Lecture reminders
    LECTURE_UPCOMING_7DAY = "lecture_upcoming_7day"
    LECTURE_UPCOMING_1DAY = "lecture_upcoming_1day"
    LECTURE_UNSCHEDULED = "lecture_unscheduled"
    LECTURE_OVERDUE = "lecture_overdue"
    LECTURE_PD_SUMMARY = "lecture_pd_summary"

    # Resident lecture reminders
    RESIDENT_LECTURE_REQUIRED = "resident_lecture_required"
    RESIDENT_LECTURE_OVERDUE = "resident_lecture_overdue"

    # Simulation reminders
    SIMULATION_UPCOMING = "simulation_upcoming"
    SIMULATION_ROTATION_GAP = "simulation_rotation_gap"

# Template definitions
NOTIFICATION_TEMPLATES.update({
    NotificationType.LECTURE_UPCOMING_7DAY: NotificationTemplate(
        type=NotificationType.LECTURE_UPCOMING_7DAY,
        subject_template="Reminder: Lecture scheduled in 7 days - $topic_name",
        body_template="""
Hello $presenter_name,

This is a reminder that you have a lecture scheduled:

Topic: $topic_name
Date: $scheduled_date
Time: $scheduled_time
Location: $location

Please ensure your presentation materials are ready.

If you need to reschedule, please contact the program coordinator.
        """,
        channels=["email"],
        priority="normal"
    ),

    NotificationType.LECTURE_UNSCHEDULED: NotificationTemplate(
        type=NotificationType.LECTURE_UNSCHEDULED,
        subject_template="Action Required: Schedule your lecture",
        body_template="""
Hello $faculty_name,

Our records show you have not yet scheduled your required lecture(s) for this academic year.

Current status:
- Lectures required: $lectures_required
- Lectures delivered: $lectures_delivered
- Lectures scheduled: $lectures_scheduled
- Remaining: $lectures_remaining

Please contact the program coordinator to schedule your lecture.

Topics available for the upcoming rotation:
$available_topics

Thank you for your commitment to resident education.
        """,
        channels=["email"],
        priority="high"
    ),

    # ... additional templates ...
})
```

### 4.4 Reminder Configuration

**File to create:** `backend/app/core/lecture_config.py`

```python
"""
Configuration for lecture reminder system.

All timing/frequency settings should be configurable.
"""

class LectureReminderConfig:
    """Configuration for lecture reminder system."""

    # Upcoming lecture reminders
    UPCOMING_REMINDER_DAYS = [7, 1]  # Days before lecture

    # Unscheduled lecture reminders
    UNSCHEDULED_CHECK_FREQUENCY = "daily"  # daily, weekly
    UNSCHEDULED_REMINDER_COOLDOWN_DAYS = 7  # Min days between reminders
    MAX_REMINDERS_PER_MONTH = 4

    # Monthly summary
    MONTHLY_SUMMARY_DAY = 1  # Day of month
    MONTHLY_SUMMARY_RECIPIENTS = ["pd", "apd", "coordinator"]

    # Escalation
    ESCALATE_AFTER_REMINDERS = 3  # Escalate to PD after N reminders
    ESCALATE_TO_ROLES = ["pd", "apd"]

    @classmethod
    def from_env(cls):
        """Load config from environment variables."""
        # Override defaults from environment
        pass
```

---

## Phase 5: User Feature Requests

### 5.1 Feature Request Model

**File to create:** `backend/app/models/feature_request.py`

```python
"""
User feature request system.

Allows users to submit feature requests which can be voted on,
prioritized, and tracked through implementation.
"""

class FeatureCategory(str, Enum):
    """Categories for feature requests."""
    SCHEDULING = "scheduling"
    REPORTING = "reporting"
    NOTIFICATIONS = "notifications"
    UI_UX = "ui_ux"
    MOBILE = "mobile"
    INTEGRATION = "integration"
    COMPLIANCE = "compliance"
    OTHER = "other"

class FeatureStatus(str, Enum):
    """Status of a feature request."""
    SUBMITTED = "submitted"           # Initial submission
    UNDER_REVIEW = "under_review"     # Admin reviewing
    PLANNED = "planned"               # Accepted, in backlog
    IN_PROGRESS = "in_progress"       # Being implemented
    COMPLETED = "completed"           # Done and deployed
    DECLINED = "declined"             # Not implementing
    DUPLICATE = "duplicate"           # Merged with another request

class FeaturePriority(str, Enum):
    """Priority levels for feature requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FeatureRequest(Base):
    """
    User-submitted feature request.
    """
    __tablename__ = "feature_requests"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Submitter info
    submitter_id = Column(GUID(), ForeignKey("persons.id"), nullable=False)

    # Request details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), default="other")  # FeatureCategory
    use_case = Column(Text)  # Why they need this

    # Status tracking
    status = Column(String(20), default="submitted")  # FeatureStatus
    priority = Column(String(20))  # FeaturePriority (set by admin)

    # Voting
    vote_count = Column(Integer, default=0)  # Cached count

    # Admin fields
    admin_notes = Column(Text)  # Internal notes
    assigned_to = Column(String(100))  # Developer/team
    target_release = Column(String(50))  # Version or date
    duplicate_of_id = Column(GUID(), ForeignKey("feature_requests.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    reviewed_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    submitter = relationship("Person", foreign_keys=[submitter_id])
    votes = relationship("FeatureRequestVote", back_populates="feature_request")
    duplicate_of = relationship("FeatureRequest", remote_side=[id])


class FeatureRequestVote(Base):
    """
    User vote on a feature request.
    """
    __tablename__ = "feature_request_votes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    feature_request_id = Column(
        GUID(),
        ForeignKey("feature_requests.id"),
        nullable=False
    )
    voter_id = Column(GUID(), ForeignKey("persons.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint: one vote per user per request
    __table_args__ = (
        UniqueConstraint(
            'feature_request_id',
            'voter_id',
            name='uq_feature_vote'
        ),
    )

    # Relationships
    feature_request = relationship("FeatureRequest", back_populates="votes")
    voter = relationship("Person")
```

### 5.2 Feature Request Service

**File to create:** `backend/app/services/feature_request_service.py`

```python
"""
Service for managing user feature requests.
"""

class FeatureRequestService:
    """Manages feature request submissions and tracking."""

    def __init__(self, db: Session):
        self.db = db

    async def submit_request(
        self,
        submitter_id: UUID,
        title: str,
        description: str,
        category: str,
        use_case: str | None = None
    ) -> FeatureRequest:
        """
        Submit a new feature request.

        Auto-detects potential duplicates and suggests merging.
        """
        pass

    async def vote(
        self,
        request_id: UUID,
        voter_id: UUID
    ) -> bool:
        """
        Vote for a feature request.

        Returns True if vote added, False if already voted.
        """
        pass

    async def unvote(
        self,
        request_id: UUID,
        voter_id: UUID
    ) -> bool:
        """Remove vote from a feature request."""
        pass

    async def list_requests(
        self,
        status: FeatureStatus | None = None,
        category: FeatureCategory | None = None,
        sort_by: str = "votes",  # votes, created, updated
        limit: int = 50,
        offset: int = 0
    ) -> list[FeatureRequest]:
        """List feature requests with filtering and sorting."""
        pass

    async def update_status(
        self,
        request_id: UUID,
        status: FeatureStatus,
        admin_notes: str | None = None,
        priority: FeaturePriority | None = None
    ) -> FeatureRequest:
        """Update feature request status (admin only)."""
        pass

    async def find_duplicates(
        self,
        title: str,
        description: str
    ) -> list[FeatureRequest]:
        """
        Find potential duplicate requests.

        Uses simple text matching - could be enhanced with embeddings.
        """
        pass

    async def get_user_requests(
        self,
        user_id: UUID
    ) -> list[FeatureRequest]:
        """Get all requests submitted by a user."""
        pass

    async def get_user_votes(
        self,
        user_id: UUID
    ) -> list[FeatureRequest]:
        """Get all requests a user has voted for."""
        pass
```

---

## API Endpoints

### Lecture Management Endpoints

**File to create:** `backend/app/api/routes/lectures.py`

```python
router = APIRouter(prefix="/lectures", tags=["Lectures"])

# Topic management (admin)
@router.get("/topics")  # List all lecture topics
@router.post("/topics")  # Create new topic
@router.get("/topics/{topic_id}")  # Get topic details
@router.put("/topics/{topic_id}")  # Update topic
@router.delete("/topics/{topic_id}")  # Deactivate topic

# Assignments
@router.get("/assignments")  # List assignments (filtered)
@router.post("/assignments")  # Create/schedule lecture
@router.get("/assignments/{assignment_id}")
@router.put("/assignments/{assignment_id}")  # Update assignment
@router.post("/assignments/{assignment_id}/deliver")  # Mark as delivered
@router.post("/assignments/{assignment_id}/cancel")  # Cancel

# Rotation schedule
@router.get("/rotation/current")  # Get current 18-month rotation
@router.post("/rotation/generate")  # Generate rotation schedule
@router.get("/rotation/coverage")  # Coverage report

# Faculty status
@router.get("/faculty/{person_id}/status")  # Faculty lecture status
@router.get("/faculty/behind")  # Faculty behind on requirements

# Resident status
@router.get("/residents/{person_id}/status")  # Resident lecture status
@router.get("/residents/requirements")  # All resident requirements
```

### Simulation Endpoints

**File to create:** `backend/app/api/routes/simulations.py`

```python
router = APIRouter(prefix="/simulations", tags=["Simulations"])

# Topic management
@router.get("/topics")
@router.post("/topics")
@router.get("/topics/{topic_id}")
@router.put("/topics/{topic_id}")

# Sessions
@router.get("/sessions")
@router.post("/sessions")  # Schedule session
@router.get("/sessions/{session_id}")
@router.put("/sessions/{session_id}")
@router.post("/sessions/{session_id}/complete")

# Rotation
@router.get("/rotation/current")
@router.get("/rotation/gaps")  # Topics not covered
@router.post("/rotation/generate")
```

### Feature Request Endpoints

**File to create:** `backend/app/api/routes/feature_requests.py`

```python
router = APIRouter(prefix="/feature-requests", tags=["Feature Requests"])

# Public endpoints (authenticated users)
@router.get("/")  # List all requests
@router.post("/")  # Submit new request
@router.get("/{request_id}")  # Get request details
@router.post("/{request_id}/vote")  # Vote for request
@router.delete("/{request_id}/vote")  # Remove vote
@router.get("/my/submitted")  # User's submitted requests
@router.get("/my/voted")  # User's voted requests

# Admin endpoints
@router.put("/{request_id}/status")  # Update status
@router.put("/{request_id}/priority")  # Set priority
@router.post("/{request_id}/duplicate")  # Mark as duplicate
@router.get("/admin/summary")  # Admin dashboard data
```

---

## UI Components

### React Components Overview

```
frontend/src/components/
├── lectures/
│   ├── LectureTopicList.tsx       # Topic catalog view
│   ├── LectureCalendar.tsx        # Calendar view of scheduled lectures
│   ├── LectureAssignmentForm.tsx  # Schedule/edit lecture form
│   ├── FacultyLectureStatus.tsx   # Faculty progress dashboard
│   ├── ResidentLectureStatus.tsx  # Resident requirements tracker
│   ├── RotationScheduleView.tsx   # 18-month rotation overview
│   └── CoverageReport.tsx         # Topic coverage visualization
│
├── simulations/
│   ├── SimulationTopicList.tsx
│   ├── SimulationCalendar.tsx
│   ├── SimulationSessionForm.tsx
│   └── RotationGapAnalysis.tsx
│
└── feature-requests/
    ├── FeatureRequestList.tsx     # Browsable list with voting
    ├── FeatureRequestForm.tsx     # Submission form
    ├── FeatureRequestDetail.tsx   # Detail view with comments
    ├── VoteButton.tsx             # Reusable vote component
    └── AdminDashboard.tsx         # Admin management view
```

### Key UI Features

1. **Lecture Calendar**: Visual calendar showing scheduled lectures with color-coding by category
2. **Progress Dashboards**: Visual progress bars for faculty/resident requirements
3. **Rotation Timeline**: 18-month timeline view showing topic coverage
4. **Feature Request Board**: Kanban-style board for feature requests with voting

---

## Testing Strategy

### Unit Tests

```
backend/tests/
├── test_lecture_topic_model.py
├── test_lecture_assignment_model.py
├── test_lecture_rotation_service.py
├── test_resident_lecture_service.py
├── test_simulation_rotation_service.py
├── test_lecture_reminder_tasks.py
├── test_feature_request_service.py
└── test_feature_request_voting.py
```

### Integration Tests

```python
# Test cases for lecture system
class TestLectureRotation:
    async def test_18_month_cycle_generation(self):
        """Verify all topics are scheduled within cycle."""

    async def test_no_duplicate_topics_in_cycle(self):
        """Verify no topic appears twice in 18 months."""

    async def test_faculty_requirement_tracking(self):
        """Verify lecture counts update correctly."""

    async def test_reminder_cooldown(self):
        """Verify reminders respect cooldown period."""

# Test cases for feature requests
class TestFeatureRequests:
    async def test_submit_request(self):
        """Test basic request submission."""

    async def test_voting_uniqueness(self):
        """Verify one vote per user per request."""

    async def test_duplicate_detection(self):
        """Test duplicate request detection."""

    async def test_vote_count_caching(self):
        """Verify vote_count field updates correctly."""
```

---

## Migration Strategy

### Database Migrations

```bash
# Phase 1: Lecture models
alembic revision --autogenerate -m "Add lecture_topics table"
alembic revision --autogenerate -m "Add lecture_assignments table"
alembic revision --autogenerate -m "Add person_lecture_requirements table"

# Phase 3: Simulation models
alembic revision --autogenerate -m "Add simulation_topics table"
alembic revision --autogenerate -m "Add simulation_sessions table"

# Phase 5: Feature requests
alembic revision --autogenerate -m "Add feature_requests and votes tables"

# Apply all
alembic upgrade head
```

### Data Seeding

```python
# scripts/seed_lecture_topics.py
"""
Seed initial lecture topic catalog.

Should be customized for specific residency program curriculum.
"""

INITIAL_TOPICS = [
    {
        "name": "Hypertension Management",
        "category": "core_curriculum",
        "cycle_position": 1,
        "presenter_type": "faculty",
        "duration_minutes": 60,
    },
    # ... 50+ topics for 18-month rotation
]
```

---

## Implementation Order

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Core Faculty Lectures (FOUNDATION)                  │
│  - LectureTopic model + migration                           │
│  - LectureAssignment model + migration                      │
│  - PersonLectureRequirement model + migration               │
│  - LectureRotationService                                   │
│  - Basic API endpoints                                      │
│  Duration: ~2-3 days                                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Resident Lectures                                   │
│  - ResidentLectureService                                   │
│  - PGY-level requirement configuration                      │
│  - Graduation tracking                                      │
│  Duration: ~1 day                                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Simulation Labs                                     │
│  - SimulationTopic model + migration                        │
│  - SimulationSession model + migration                      │
│  - SimulationRotationService                                │
│  - API endpoints                                            │
│  Duration: ~2 days                                          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 4: Automated Reminders                                 │
│  - Celery tasks for all reminder types                      │
│  - Notification templates                                   │
│  - Configuration system                                     │
│  - Celery beat schedule                                     │
│  Duration: ~2 days                                          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 5: User Feature Requests                               │
│  - FeatureRequest model + migration                         │
│  - FeatureRequestVote model + migration                     │
│  - FeatureRequestService                                    │
│  - API endpoints (public + admin)                           │
│  Duration: ~2 days                                          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 6: Frontend Implementation                             │
│  - Lecture management UI                                    │
│  - Simulation management UI                                 │
│  - Feature request submission/voting UI                     │
│  Duration: ~3-4 days                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Open Questions

### Lecture System

1. **Topic catalog source**: Where does the initial 18-month topic list come from?
   - Option A: Import from existing spreadsheet
   - Option B: Manual entry
   - Option C: ACGME curriculum template

2. **Multiple presenters**: Can a lecture have co-presenters?
   - If yes, how to track credit?

3. **Guest lecturers**: How to handle external presenters (not in Person table)?
   - Option A: Add guest presenter fields
   - Option B: Create minimal Person records

4. **Make-up lectures**: How to handle missed/cancelled lectures?
   - Reschedule within same cycle?
   - Push to next cycle?

### Simulation System

5. **Equipment tracking**: Do we need inventory integration for simulation equipment?

6. **Participant tracking**: Track which residents attended each simulation?
   - Needed for competency tracking?

7. **Room booking**: Integrate with room scheduling system?

### Feature Requests

8. **Anonymous submissions**: Allow anonymous feature requests?
   - Privacy vs. accountability trade-off

9. **Comment system**: Allow discussion threads on feature requests?
   - Adds complexity but valuable for clarification

10. **Public vs. private requests**: Should all requests be visible to all users?
    - Some requests might reveal workflow issues

### General

11. **Reporting**: What reports are needed for program administration?
    - Annual lecture summary
    - Faculty participation rates
    - Simulation coverage

12. **Integration**: Integration with learning management system (LMS)?

---

## References

- [Existing Academic Block Service](../../backend/app/services/academic_block_service.py)
- [Notification Infrastructure](../../backend/app/notifications/service.py)
- [Celery Task Patterns](../../backend/app/core/celery_app.py)
- [Person Model](../../backend/app/models/person.py)

---

## Appendix A: Sample Lecture Topic Catalog

```python
# Example 18-month rotation topics
SAMPLE_TOPICS = [
    # Month 1
    {"name": "Hypertension Management", "cycle_position": 1, "category": "core_curriculum"},
    {"name": "Diabetes Care Update", "cycle_position": 1, "category": "core_curriculum"},

    # Month 2
    {"name": "Preventive Care Guidelines", "cycle_position": 2, "category": "core_curriculum"},
    {"name": "Pediatric Well-Child Visits", "cycle_position": 2, "category": "specialty"},

    # Month 3
    {"name": "Mental Health in Primary Care", "cycle_position": 3, "category": "core_curriculum"},
    {"name": "Joint Injections", "cycle_position": 3, "category": "procedures"},

    # ... continue for 18 months
]
```

## Appendix B: Sample Simulation Lab Topics

```python
SAMPLE_SIMULATIONS = [
    # Month 1
    {"name": "ACLS Megacode", "cycle_position": 1, "category": "acls", "duration_hours": 3},

    # Month 2
    {"name": "Obstetric Emergency - Shoulder Dystocia", "cycle_position": 2, "category": "ob_emergencies"},

    # Month 3
    {"name": "Pediatric Respiratory Distress", "cycle_position": 3, "category": "pals"},

    # ... continue for 18 months
]
```

---

*This document will be updated as requirements are clarified and implementation progresses.*
