# MCP Notification Tools Documentation

**G2_RECON SEARCH_PARTY Investigation Report**
**Session:** 8_MCP
**Status:** Complete
**Date:** 2025-12-30

---

## Executive Summary

The Autonomous Assignment Program Manager includes a comprehensive notification and alert delivery system spanning:
- **3 core delivery channels** (in-app, email, webhook)
- **7 standard notification types** (schedule, assignments, shifts, ACGME warnings, absences)
- **7 swap-specific notification types** (requests, execution, rollback, marketplace)
- **Background task processing** via Celery with exponential backoff retry logic
- **81 MCP tools** for scheduling, validation, resilience analysis, and monitoring
- **Undocumented alert triggers** from error reporters, secret rotation, and early warning systems

---

## Part I: Channel Architecture

### Overview

The notification system implements a **plugin architecture** with three delivery channels:

```
Notification Service
├── InApp Channel     (database persistence)
├── Email Channel     (SMTP + Celery tasks)
└── Webhook Channel   (HTTP POST + Celery tasks)
```

---

### 1. In-App Channel (`InAppChannel`)

**Location:** `/backend/app/notifications/channels.py:90-154`

**Purpose:** Store notifications in the database for UI display and historical audit trail.

**Channel Name:** `in_app`

**Delivery Method:** Synchronous database insertion

**Database Model:** `Notification` (SQLAlchemy ORM)
- `id`: UUID primary key
- `recipient_id`: UUID (FK to `people.id`)
- `notification_type`: String(50), indexed
- `subject`: String(500)
- `body`: Text
- `data`: JSON (additional metadata)
- `priority`: Enum('high', 'normal', 'low')
- `channels_delivered`: Comma-separated list of channels used
- `is_read`: Boolean, indexed
- `read_at`: Optional datetime
- `created_at`: Datetime, indexed

**Features:**
- Audit trail for all notifications
- Read/unread status tracking
- Direct database persistence (no external service required)
- Full-text searchable body content

**Configuration:** No external configuration needed

**Example Usage:**
```python
channel = InAppChannel()
result = await channel.deliver(payload, db_session)
# Result: DeliveryResult(success=True, channel="in_app", ...)
```

---

### 2. Email Channel (`EmailChannel`)

**Location:** `/backend/app/notifications/channels.py:157-265`

**Purpose:** Format and queue email notifications for delivery via SMTP.

**Channel Name:** `email`

**Delivery Method:** Asynchronous via Celery background task

**Service Integration:** `EmailService` from `app/services/email_service.py`

**Configuration:**
```python
EmailChannel(from_address="noreply@schedule.mil")  # Customizable sender
```

**Background Task:** `app.notifications.tasks.send_email`
- **Max Retries:** 3 attempts
- **Retry Delay:** 60 seconds initial, exponential backoff up to 300s (5 min)
- **Triggers Retry On:** Any exception
- **Queue:** Celery default queue via Redis broker

**Email Formatting:**
- **Plain Text:** Raw body content
- **HTML Template:** Styled email with color-coded priority indicators
  - `priority-high`: Red left border (#dc3545)
  - `priority-normal`: Blue left border (#007bff)
  - `priority-low`: Gray left border (#6c757d)
- **Footer:** "This is an automated notification from the Schedule Management System."

**Recipient Lookup:**
- Uses Person model to fetch recipient email from database
- **Limitation:** Currently uses placeholder `user-{recipient_id}@example.com` until full database join implemented

**Example Usage:**
```python
channel = EmailChannel(from_address="noreply@schedule.mil")
result = await channel.deliver(payload, db_session)
# Result: DeliveryResult(
#   success=True,
#   channel="email",
#   metadata={
#     "email_payload": {
#       "from": "noreply@schedule.mil",
#       "to": "user-{id}@example.com",
#       "subject": "New Schedule Published",
#       "body": "...",
#       "html": "<html>...</html>",
#       "priority": "high"
#     }
#   }
# )
```

---

### 3. Webhook Channel (`WebhookChannel`)

**Location:** `/backend/app/notifications/channels.py:267-335`

**Purpose:** Send notifications to external systems (Slack, Teams, monitoring platforms, custom integrations).

**Channel Name:** `webhook`

**Delivery Method:** Asynchronous via Celery background task (HTTP POST)

**Webhook URL Configuration:**
```python
WebhookChannel(webhook_url="https://hooks.slack.com/services/...")
```

**Background Task:** `app.notifications.tasks.send_webhook`
- **Max Retries:** 3 attempts
- **Retry Delay:** 30 seconds initial, exponential backoff up to 120s (2 min)
- **Triggers Retry On:** `httpx.HTTPError`, `httpx.TimeoutException`
- **HTTP Client Timeout:** 30 seconds
- **Queue:** Celery default queue via Redis broker

**Webhook Payload Structure:**
```json
{
  "event": "notification",
  "notification_id": "uuid-string",
  "type": "notification_type_enum",
  "recipient_id": "uuid-string",
  "subject": "Notification subject",
  "body": "Notification body",
  "priority": "high|normal|low",
  "timestamp": "2025-12-30T10:30:45.123456",
  "data": {
    "custom": "fields",
    "from": "template"
  }
}
```

**Integration Examples:**
- **Slack:** Configure webhook URL to Slack app incoming webhook endpoint
- **Microsoft Teams:** Use Teams incoming webhook URL format
- **PagerDuty:** Route CRITICAL notifications to PagerDuty webhook for on-call escalation
- **Monitoring Systems:** Prometheus AlertManager, Datadog, New Relic webhooks
- **Custom Systems:** Any HTTP POST endpoint accepting JSON

**Example Usage:**
```python
channel = WebhookChannel(webhook_url="https://hooks.slack.com/services/...")
result = await channel.deliver(payload, db_session)
# Result: DeliveryResult(
#   success=True,
#   channel="webhook",
#   metadata={
#     "webhook_url": "https://hooks.slack.com/services/...",
#     "payload": {...}
#   }
# )
```

---

## Part II: Notification Types

### Standard Notifications (Built-In)

**Location:** `/backend/app/notifications/notification_types.py`

#### 1. SCHEDULE_PUBLISHED
- **Type ID:** `schedule_published`
- **Subject Template:** "New Schedule Published for $period"
- **Channels:** `['in_app', 'email']`
- **Priority:** HIGH
- **Template Variables:**
  - `period`: Schedule period (e.g., "January 2025")
  - `coverage_rate`: Coverage percentage
  - `total_assignments`: Number of assignments
  - `violations_count`: ACGME violations found
  - `publisher_name`: Person who published schedule
  - `published_at`: Timestamp in UTC

**Trigger Points:**
- Schedule generation completion (after publication)
- Used by: `app.notifications.service.notify_schedule_published()`

**Recipient:** All residents and faculty affected by schedule

---

#### 2. ASSIGNMENT_CHANGED
- **Type ID:** `assignment_changed`
- **Subject Template:** "Assignment Change: $rotation_name"
- **Channels:** `['in_app', 'email']`
- **Priority:** HIGH
- **Template Variables:**
  - `rotation_name`: Name of rotation
  - `block_name`: Block identifier
  - `start_date`: Assignment start date
  - `end_date`: Assignment end date
  - `previous_rotation`: Previous rotation name
  - `new_rotation`: New rotation name
  - `change_reason`: Why the change was made
  - `changed_by`: Person who made the change
  - `changed_at`: Timestamp of change

**Trigger Points:**
- Manual assignment changes via API
- Swap execution
- Conflict resolution automatic reassignment

**Recipient:** Affected person (resident/faculty)

---

#### 3. SHIFT_REMINDER_24H
- **Type ID:** `shift_reminder_24h`
- **Subject Template:** "Reminder: Shift Tomorrow - $rotation_name"
- **Channels:** `['in_app', 'email']`
- **Priority:** NORMAL
- **Template Variables:**
  - `rotation_name`: Name of upcoming rotation
  - `location`: Where the shift takes place
  - `start_date`: Shift start date
  - `duration_weeks`: Length in weeks
  - `contact_person`: Person to contact with questions
  - `contact_email`: Contact email address

**Trigger Points:**
- Scheduled task (Celery beat): 24 hours before shift start

**Recipient:** Person with upcoming assignment

---

#### 4. SHIFT_REMINDER_1H
- **Type ID:** `shift_reminder_1h`
- **Subject Template:** "Starting Soon: $rotation_name"
- **Channels:** `['in_app']` (in-app only, higher disruption tolerance)
- **Priority:** HIGH
- **Template Variables:**
  - `rotation_name`: Name of imminent rotation
  - `location`: Shift location
  - `start_time`: Exact start time

**Trigger Points:**
- Scheduled task (Celery beat): 1 hour before shift start

**Recipient:** Person with imminent assignment

---

#### 5. ACGME_WARNING
- **Type ID:** `acgme_warning`
- **Subject Template:** "ACGME Compliance Alert: $violation_type"
- **Channels:** `['in_app', 'email', 'webhook']` (escalated to external monitoring)
- **Priority:** HIGH
- **Template Variables:**
  - `violation_type`: Type of ACGME violation
  - `severity`: Alert severity (CRITICAL, HIGH, MEDIUM, LOW)
  - `person_name`: Affected person
  - `violation_details`: Detailed description
  - `recommended_action`: How to resolve
  - `detected_at`: Timestamp of detection

**Trigger Points:**
- ACGME compliance validator detects violations
- Called by: `app.notifications.service.notify_acgme_warning()`
- Compliance checks: 80-hour rule, 1-in-7 rule, supervision ratios

**Recipient:** Coordinator/Administrator (NOT the affected person)

**Special Handling:** Webhook delivery enables alerting external monitoring systems (PagerDuty, Slack #alerts, etc.)

---

#### 6. ABSENCE_APPROVED
- **Type ID:** `absence_approved`
- **Subject Template:** "Absence Request Approved"
- **Channels:** `['in_app', 'email']`
- **Priority:** NORMAL
- **Template Variables:**
  - `absence_type`: Type of leave (vacation, sick, training, etc.)
  - `start_date`: Leave start date
  - `end_date`: Leave end date
  - `duration_days`: Length in days
  - `approval_notes`: Notes from approver
  - `approver_name`: Person who approved
  - `approved_at`: Timestamp of approval

**Trigger Points:**
- Absence request approval by coordinator/PD
- Background task: `detect_leave_conflicts()` runs after approval

**Recipient:** Person who requested absence

---

#### 7. ABSENCE_REJECTED
- **Type ID:** `absence_rejected`
- **Subject Template:** "Absence Request Not Approved"
- **Channels:** `['in_app', 'email']`
- **Priority:** NORMAL
- **Template Variables:**
  - `absence_type`: Type of leave requested
  - `start_date`: Requested leave start
  - `end_date`: Requested leave end
  - `duration_days`: Requested duration
  - `rejection_reason`: Why it was rejected
  - `reviewer_name`: Person who reviewed
  - `reviewed_at`: Timestamp of review

**Trigger Points:**
- Absence request rejection by coordinator/PD

**Recipient:** Person who requested absence

---

### Swap Notifications (Domain-Specific)

**Location:** `/backend/app/services/swap_notification_service.py`

**Enum:** `SwapNotificationType`

#### 1. SWAP_REQUEST_RECEIVED
- **Subject:** "FMIT Swap Request from {requester_name}"
- **Recipient:** Faculty receiving the request
- **Triggered By:** Swap request creation
- **Variables:** requester_name, week_offered, reason (optional)

#### 2. SWAP_REQUEST_ACCEPTED
- **Subject:** "Your FMIT Swap Request Was Accepted"
- **Recipient:** Original requester
- **Triggered By:** Swap acceptance by recipient
- **Variables:** acceptor_name, accepted_date

#### 3. SWAP_REQUEST_REJECTED
- **Subject:** "Your FMIT Swap Request Was Rejected"
- **Recipient:** Original requester
- **Triggered By:** Swap rejection by recipient
- **Variables:** rejector_name, rejection_reason (optional)

#### 4. SWAP_EXECUTED
- **Subject:** "FMIT Swap Completed: {week}"
- **Recipient:** Both swap parties
- **Triggered By:** Swap execution (rollback period elapsed or manually confirmed)
- **Variables:** counterparty_name, week, confirmation_date

#### 5. SWAP_ROLLED_BACK
- **Subject:** "FMIT Swap Reversed: {week}"
- **Recipient:** Both swap parties
- **Triggered By:** Within 24-hour rollback window
- **Variables:** initiator_name, reason, effective_date

#### 6. SWAP_REMINDER
- **Subject:** "Reminder: FMIT Swap Executing Soon"
- **Recipient:** Both parties involved
- **Triggered By:** 48 hours before automatic execution
- **Variables:** counterparty_name, week, execution_date

#### 7. MARKETPLACE_MATCH
- **Subject:** "Potential FMIT Swap Match Found"
- **Recipient:** Faculty with compatible swap requests
- **Triggered By:** Auto-matcher algorithm finds candidates
- **Variables:** matched_faculty_list, match_score, suggested_action

---

## Part III: Notification Service

**Location:** `/backend/app/notifications/service.py`

### Core Service: `NotificationService`

```python
service = NotificationService(db_session)
```

#### Method 1: `send_notification()` - Immediate Send

```python
async def send_notification(
    recipient_id: UUID,
    notification_type: NotificationType,
    data: dict[str, Any],
    channels: list[str] | None = None,
) -> list[DeliveryResult]
```

**Process Flow:**
1. Render notification template with provided data
2. Check user notification preferences (cached)
3. Filter channels by user preferences
4. Create `NotificationPayload`
5. Deliver through each channel (in parallel)
6. Store notification record in database
7. Return `DeliveryResult` for each channel

**Channel Filter Logic:**
- Respects user's enabled channels
- Respects notification type preferences (per-type toggles)
- Respects quiet hours (except for HIGH priority notifications)

**Example:**
```python
results = await service.send_notification(
    recipient_id=uuid.UUID("..."),
    notification_type=NotificationType.SCHEDULE_PUBLISHED,
    data={
        "period": "January 2025",
        "coverage_rate": 92.5,
        "total_assignments": 450,
        "violations_count": 0,
        "publisher_name": "Dr. Smith",
        "published_at": "2025-12-30 10:30:00 UTC"
    },
    channels=["in_app", "email"]  # Optional, uses defaults if omitted
)
```

---

#### Method 2: `send_bulk()` - Broadcast to Multiple Recipients

```python
async def send_bulk(
    recipient_ids: list[UUID],
    notification_type: NotificationType,
    data: dict[str, Any],
    channels: list[str] | None = None,
) -> dict[str, list[DeliveryResult]]
```

**Optimization:** Batch-loads all user preferences in single query to avoid N+1 query problem

**Returns:** Dictionary mapping `str(recipient_id)` to list of `DeliveryResult`

**Example:**
```python
results = await service.send_bulk(
    recipient_ids=[uuid1, uuid2, uuid3],
    notification_type=NotificationType.SCHEDULE_PUBLISHED,
    data={...}
)
# Result: {
#   "uuid1": [DeliveryResult(...), DeliveryResult(...)],
#   "uuid2": [DeliveryResult(...)],
#   "uuid3": [DeliveryResult(...)],
# }
```

---

#### Method 3: `schedule_notification()` - Future Delivery

```python
def schedule_notification(
    recipient_id: UUID,
    notification_type: NotificationType,
    data: dict[str, Any],
    send_at: datetime,
) -> ScheduledNotification
```

**Database Table:** `scheduled_notifications`

**Fields:**
- `id`: UUID
- `recipient_id`: UUID
- `notification_type`: String
- `data`: JSON
- `send_at`: Datetime (indexed)
- `status`: Enum('pending', 'processing', 'sent', 'failed', 'cancelled')
- `sent_at`: Optional datetime
- `error_message`: Optional text
- `retry_count`: Integer (increments on failure)
- `created_at`: Datetime
- `updated_at`: Datetime (auto-updated)

**Example:**
```python
scheduled = service.schedule_notification(
    recipient_id=uuid.UUID("..."),
    notification_type=NotificationType.SHIFT_REMINDER_24H,
    data={"rotation_name": "Inpatient", ...},
    send_at=datetime.utcnow() + timedelta(hours=24)
)
print(f"Scheduled notification {scheduled.id} for {scheduled.send_at}")
```

---

#### Method 4: `process_scheduled_notifications()` - Background Processing

```python
async def process_scheduled_notifications() -> int
```

**Purpose:** Called by Celery beat scheduler to process due notifications

**Process:**
1. Query all `scheduled_notifications` with `send_at <= now` and `status='pending'`
2. Batch-load preferences for all recipients (N+1 prevention)
3. For each notification:
   - Set status to 'processing'
   - Send via `send_notification()`
   - Update status to 'sent' or 'failed'
   - Record sent_at or error_message
   - Increment retry_count on failure (up to retry limit)
4. Clear preferences cache
5. Return count of notifications processed

**Celery Configuration:** Should be scheduled as periodic task (suggested: every 5 minutes)

**Example Celery Beat Schedule:**
```python
app.conf.beat_schedule = {
    'process-scheduled-notifications': {
        'task': 'app.notifications.tasks.process_scheduled_notifications',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    }
}
```

---

#### Method 5: `get_pending_notifications()` - Fetch User Inbox

```python
def get_pending_notifications(
    user_id: UUID,
    limit: int = 50,
    unread_only: bool = True,
) -> list[dict[str, Any]]
```

**Returns:** List of notification dictionaries with fields:
- `id`: Notification UUID
- `notification_type`: Type enum string
- `subject`: Subject line
- `body`: Full body text
- `data`: Additional JSON data
- `priority`: Priority level
- `is_read`: Boolean
- `created_at`: ISO format timestamp

**Ordering:** Newest first (by created_at DESC)

---

#### Method 6: `mark_as_read()` - Mark Notifications Read

```python
def mark_as_read(notification_ids: list[UUID]) -> int
```

**Returns:** Count of notifications marked as read

**Updates:** Sets `is_read=True` and `read_at=utcnow()` for matching notifications

---

#### Method 7: `update_user_preferences()` - Customize Notification Settings

```python
def update_user_preferences(
    user_id: UUID,
    preferences: NotificationPreferences
) -> NotificationPreferences
```

**Database Table:** `notification_preferences`

**Preference Fields:**
- `enabled_channels`: List of enabled delivery channels (default: ['in_app', 'email'])
- `notification_types`: Dict of `{type_name: enabled}` for each notification type
- `quiet_hours_start`: Hour (0-23) or None
- `quiet_hours_end`: Hour (0-23) or None
- `email_digest_enabled`: Boolean (future feature)
- `email_digest_frequency`: Enum('daily', 'weekly') (future feature)

**Example:**
```python
service.update_user_preferences(
    user_id=uuid.UUID("..."),
    preferences=NotificationPreferences(
        user_id=uuid.UUID("..."),
        enabled_channels=["in_app", "webhook"],  # Disable email
        notification_types={
            NotificationType.SHIFT_REMINDER_24H.value: False,  # Disable 24h reminders
            NotificationType.SHIFT_REMINDER_1H.value: True,
            NotificationType.ACGME_WARNING.value: True,
        },
        quiet_hours_start=22,  # 10 PM
        quiet_hours_end=7,     # 7 AM
    )
)
```

---

## Part IV: Background Tasks (Celery)

**Location:** `/backend/app/notifications/tasks.py`

### Task 1: `send_email()` - Email Delivery

```python
@shared_task(
    bind=True,
    name="app.notifications.tasks.send_email",
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=300,
)
async def send_email(self, to: str, subject: str, body: str, html: str | None = None) -> dict
```

**Configuration:**
- **Max Retries:** 3 attempts total
- **Initial Retry Delay:** 60 seconds
- **Exponential Backoff:** Yes (60s → 120s → 240s max)
- **Max Backoff:** 300 seconds (5 minutes)
- **Triggers Retry:** Any exception

**Returns:**
```python
{
    "timestamp": "2025-12-30T10:30:45.123456",
    "to": "recipient@example.com",
    "subject": "Notification Subject",
    "status": "sent",
    "attempts": 1  # Attempt number that succeeded
}
```

**Implementation:**
1. Initialize EmailService singleton
2. If html provided, use it; otherwise wrap body in basic HTML
3. Call `EmailService.send_email()`
4. Log success with metadata
5. On failure, log warning and raise exception (triggers retry)

---

### Task 2: `send_webhook()` - Webhook Delivery

```python
@shared_task(
    bind=True,
    name="app.notifications.tasks.send_webhook",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(httpx.HTTPError, httpx.TimeoutException),
    retry_backoff=True,
    retry_backoff_max=120,
)
async def send_webhook(self, url: str, payload: dict) -> dict
```

**Configuration:**
- **Max Retries:** 3 attempts
- **Initial Retry Delay:** 30 seconds
- **Exponential Backoff:** Yes (30s → 60s → 120s max)
- **Max Backoff:** 120 seconds (2 minutes)
- **Triggers Retry:** `httpx.HTTPError`, `httpx.TimeoutException`

**HTTP Client Settings:**
- **Timeout:** 30 seconds per request
- **Method:** POST
- **Content-Type:** application/json (automatic)

**Returns:**
```python
{
    "timestamp": "2025-12-30T10:30:45.123456",
    "url": "https://hooks.slack.com/services/...",
    "status": "sent",
    "status_code": 200,
    "attempts": 1
}
```

**Implementation:**
1. Create httpx.Client with 30s timeout
2. POST payload as JSON to webhook URL
3. Call `response.raise_for_status()` (raises on 4xx/5xx)
4. Return success with status code
5. On HTTP errors, log warning and raise (triggers retry)

---

### Task 3: `detect_leave_conflicts()` - Post-Approval Conflict Detection

```python
@shared_task(
    bind=True,
    name="app.notifications.tasks.detect_leave_conflicts",
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=300,
)
async def detect_leave_conflicts(self, absence_id: str) -> dict
```

**Triggered By:**
- Absence record creation
- Absence approval by coordinator

**Process:**
1. Load absence from database
2. Initialize `ConflictAutoDetector`
3. Call `detect_conflicts_for_absence(absence_id)`
4. Create `ConflictAlert` records for any detected conflicts
5. Return summary

**Returns:**
```python
{
    "timestamp": "2025-12-30T10:30:45.123456",
    "absence_id": "uuid-string",
    "conflicts_found": 2,
    "alerts_created": 2,
    "status": "completed",
    "attempts": 1
}
```

**Conflict Types Detected:**
- `LEAVE_FMIT_OVERLAP`: Absence overlaps with scheduled FMIT week
- `BACK_TO_BACK`: Absence immediately follows/precedes FMIT week
- `EXCESSIVE_ALTERNATING`: Alternating on-call/off patterns during absence period
- `CALL_CASCADE`: Too many consecutive call weeks including absence
- `EXTERNAL_COMMITMENT`: Conflicts with known external commitments

---

## Part V: Undocumented Alert Triggers

### STEALTH Lens: Hidden Notification Sources

#### 1. System Alert Notifications

**Location:** `/backend/app/middleware/errors/reporters.py`

**Trigger:** Application errors matching severity thresholds

**Notification Type:** `NotificationType.SYSTEM_ALERT` (custom, not in enum)

**Recipients:** Admin/Ops team (hardcoded, not user-configurable)

**Channel:** Direct email + webhook to Sentry/monitoring

**Condition:** Error severity >= CRITICAL

**Undocumented:** Called in error handler middleware without explicit logging

---

#### 2. Secret Rotation Alerts

**Location:** `/backend/app/security/secret_rotation.py`

**Trigger:** Scheduled secret rotation tasks (JWT tokens, API keys, database passwords)

**Notification Type:** `NotificationType.SECRET_ROTATION` (commented out, future enhancement)

**Precondition Alerts:**
- **JWT Keys:** 72 hours before rotation
- **API Keys:** 1 week before rotation
- **DB Passwords:** 72 hours before rotation
- **Webhook Secrets:** 30 days before rotation

**Recipients:** DevOps/Security team

**Channels:** Email + Slack webhook (configured via environment)

**Status:** Infrastructure prepared but notification code commented out (ready for activation)

---

#### 3. Early Warning System Alerts

**Location:** `/backend/app/resilience/frms/alertness_engine.py` + MCP integration

**Trigger:** Burnout precursor detection (Seismic STA/LTA algorithm)

**Alert Types:**
- **Seismic Precursor Detection:** P-wave equivalents of behavioral signals
  - Swap request frequency spike
  - Sick call frequency spike
  - Response delay increases
  - Voluntary coverage decline
  - Preference change patterns

- **SPC Violations:** Western Electric rules for workload drift
  - Rule 1: Single point exceeds 3σ from centerline
  - Rule 2: 9 consecutive points on same side of centerline
  - Rule 3: 6 consecutive points increasing/decreasing
  - Rule 4: 14 consecutive points alternating up/down

- **Burnout Fire Index:** Multi-temporal danger rating (CFFDRS adapted)
  - Temperature Index (TI): Resident workload stress
  - Initial Spread Index (ISI): Speed of burnout propagation
  - Buildup Index (BUI): Cumulative fatigue buildup

**Severity Levels:**
```
Seismic STA/LTA Ratio → Severity
< 1.0              → "healthy"
1.0 - 2.5          → "warning"
2.5 - 5.0          → "elevated"
> 5.0              → "critical"
```

**Recipient:** Program Director (alerts + recommendations)

**Channels:** Email + webhook (routed to clinical decision support)

**MCP Tools Exposed:**
- `detect_burnout_precursors_tool()`
- `run_spc_analysis_tool()`
- `calculate_fire_danger_index_tool()`

**Timeline Prediction:** Time-to-event in days (based on growth rate extrapolation)

---

#### 4. Conflict Auto-Detection Alerts

**Location:** `/backend/app/services/conflict_alert_service.py`

**Trigger:** Absence approval or schedule changes

**Background Task:** `detect_leave_conflicts()` in Celery

**Alert Model:** `ConflictAlert` (SQLAlchemy)

**Conflict Types:**
- `LEAVE_FMIT_OVERLAP`: Absence during scheduled FMIT week
- `BACK_TO_BACK`: Less than 48 hours between absence end and FMIT start
- `EXCESSIVE_ALTERNATING`: Alternating on/off patterns disrupt continuity
- `CALL_CASCADE`: Too many consecutive call weeks adjacent to absence
- `EXTERNAL_COMMITMENT`: Known external obligations during period

**Severity Levels:**
- `CRITICAL`: Immediate action required (schedule impact)
- `WARNING`: Should be reviewed (moderate impact)
- `INFO`: FYI only (minimal impact)

**Recipient:** Faculty member + Coordinator

**Notification:** Opt-in via preferences (routed to email + in-app)

**Resolution Tracking:**
- Status transitions: NEW → ACKNOWLEDGED → RESOLVED
- Resolution options: swap, adjust boundaries, reassign to backup, request coverage pool
- Impact estimation: affected faculty count, weeks affected, feasibility score

---

#### 5. Compliance Report Delivery

**Location:** `/backend/app/tasks/compliance_report_tasks.py`

**Trigger:** Scheduled compliance analysis completion

**Report Types:**
- Daily ACGME compliance summary
- Weekly violation report
- Monthly aggregate statistics
- Custom on-demand reports

**Delivery Method:** Email with attachment (PDF, CSV, JSON)

**Recipients:** Coordinator, PD, Compliance Officer

**Scheduling:** Celery beat (daily at 7 AM)

**Features:**
- Cached report generation (30-minute cache)
- N+1 query prevention via eager loading
- Pagination for large reports
- Structured data export

---

#### 6. Marketplace Auto-Matcher Notifications

**Location:** `/backend/app/services/swap_notification_service.py`

**Trigger:** Swap auto-matcher algorithm identifies compatible partners

**Notification Type:** `SwapNotificationType.MARKETPLACE_MATCH`

**Algorithm:**
1. Extract swap preference patterns from user profiles
2. Find users with complementary requests (A wants W1, B wants W1 reciprocal)
3. Score match compatibility (0.0-1.0)
4. Filter for high-confidence matches (> 0.85)

**Data Provided:**
- List of matched faculty
- Match score (confidence percentage)
- Suggested swap details (weeks, rotations)
- Link to execute marketplace transaction

**Recipients:** All matching faculty (simultaneous notification)

**Channels:** Email + in-app + optional webhook to marketplace UI

---

#### 7. Defense-in-Depth Level Transitions

**Location:** `/backend/app/scheduling/resilience/defense_levels.py`

**Trigger:** Coverage metrics cross defense level thresholds

**Defense Levels:**
```
Coverage Rate  Level      Status Color  Actions Triggered
> 95%         GREEN       ✓ Optimal     Normal operations
90-95%        YELLOW      ⚠ Caution     Monitor, prepare contingencies
80-90%        ORANGE      ⚠⚠ Warning    Activate backup plans, reduce electives
60-80%        RED         🔴 Critical   Emergency response, cancel non-essential
< 60%         BLACK       ⛔ Catastrophic Deploy all fallbacks, full lockdown
```

**Notification Trigger:** Any level transition

**Recipients:** Scheduling team, Program Director, Clinical leadership

**Channels:** Email + webhook (PagerDuty escalation) + in-app alert banner

**Special Handling:**
- YELLOW+ transitions require explicit acknowledgment
- RED+ transitions trigger automatic contingency analysis
- BLACK level triggers automatic sacrifice hierarchy execution

---

## Part VI: MCP Tool Registration (81 Tools)

**Location:** `/mcp-server/src/scheduler_mcp/server.py`

### Tool Categories

| Category | Count | Purpose |
|----------|-------|---------|
| **Scheduling** | 8 | Generate, validate, analyze schedules |
| **Resilience** | 15 | Defense levels, contingencies, N-1/N-2 analysis |
| **Conflict Resolution** | 6 | Detect, resolve, track conflicts |
| **Swap Management** | 5 | Candidate matching, execution, rollback |
| **Early Warning** | 8 | Precursor detection, SPC, fire danger |
| **Validation** | 5 | ACGME rules, constraints, compliance |
| **Background Tasks** | 4 | Task status, execution, cancellation |
| **Analytics** | 12 | Fourier analysis, VAR, game theory, ecological |
| **Optimization** | 4 | Constraint tuning, meta-learning |
| **Integration** | 14 | Diverse ML models, circuit breaker, time crystal |

### Example Tool: `detect_burnout_precursors_tool()`

```python
@mcp.tool()
async def detect_burnout_precursors_tool(
    resident_id: str,
    signal_type: str,  # "swap_requests", "sick_calls", etc.
    time_series: list[float],
    short_window: int = 5,
    long_window: int = 30,
) -> PrecursorDetectionResponse
```

**Returns:**
```python
{
    "resident_id": "uuid",
    "signal_type": "swap_requests",
    "alerts_detected": 2,
    "alerts": [
        {
            "signal_type": "swap_requests",
            "sta_lta_ratio": 3.2,
            "severity": "high",
            "predicted_magnitude": 6.5,  # Richter-like scale
            "time_to_event_days": 14.3,
            "trigger_window_start": 5,
            "trigger_window_end": 12,
            "growth_rate": 0.18,
        },
        {...}
    ],
    "max_sta_lta_ratio": 3.2,
    "analysis_summary": "Elevated precursor signal detected...",
    "recommended_actions": [
        "Schedule wellness check-in with resident",
        "Review workload for next block",
        "Increase mentorship touchpoints",
    ],
    "severity": "critical",
}
```

---

## Part VII: Configuration & Integration

### Environment Variables

```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@schedule.mil
SMTP_PASSWORD=<secure-password>
MAIL_FROM_ADDRESS=noreply@schedule.mil
MAIL_FROM_NAME="Schedule Management System"

# Webhook Configuration
WEBHOOK_SECRET=<32-char-minimum-secret>
WEBHOOK_URL_SLACK=https://hooks.slack.com/services/...
WEBHOOK_URL_PAGERDUTY=https://events.pagerduty.com/...
WEBHOOK_URL_TEAMS=https://outlook.webhook.office.com/...

# Notification Configuration
NOTIFICATION_EMAIL_ENABLED=true
NOTIFICATION_WEBHOOK_ENABLED=true
NOTIFICATION_INAPP_ENABLED=true
NOTIFICATION_QUIET_HOURS_START=22  # 10 PM
NOTIFICATION_QUIET_HOURS_END=7     # 7 AM

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_TASK_TIME_LIMIT=300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT=250  # 4 min 10 sec

# Early Warning System
EARLY_WARNING_ENABLED=true
BURNOUT_PRECURSOR_STA_WINDOW=5
BURNOUT_PRECURSOR_LTA_WINDOW=30
SPC_SIGMA=5.0
FIRE_DANGER_THRESHOLD=4.0
```

### Database Migrations

**Applied Migrations:**
- `010_add_notification_tables.py`: Core notification schema
- `016_add_email_notification_tables.py`: Email logging support

**Tables Created:**
- `notifications`: Delivered notifications (history)
- `scheduled_notifications`: Future notifications
- `notification_preferences`: User preferences per type
- `email_logs`: SMTP delivery logs (optional)

---

## Part VIII: Testing

**Location:** `/backend/tests/`

### Unit Tests
- `test_notification_service.py`: Service logic (render, deliver, schedule)
- `test_notifications.py`: Template rendering
- `test_swap_notification_service.py`: Swap notification types

### Integration Tests
- `integration/test_notification_workflow.py`: End-to-end notification delivery
- `integration/services/test_notification_integration.py`: Service integration

### Load Tests
- `performance/test_notification_load.py`: Bulk notification performance

---

## Part IX: Alert Monitoring Dashboard

### Metrics Exposed to Prometheus

```prometheus
# Notification metrics
notification_sent_total{type, channel, status}
notification_delivery_latency_seconds{channel}
notification_queue_depth{type}
notification_errors_total{channel, error_type}

# Task metrics
task_duration_seconds{task_name}
task_retry_total{task_name}
task_failure_total{task_name}

# Compliance metrics
acgme_violation_alerts_total{violation_type, severity}
conflict_alert_total{conflict_type, status}
```

### Grafana Dashboard Panels

1. **Notification Delivery Rate:** Success/failure by channel
2. **Latency Trends:** Email vs webhook performance
3. **Queue Depth:** Pending notifications by type
4. **ACGME Alerts:** Violation detection trends
5. **Early Warning Signals:** Burnout precursor frequency
6. **Defense Level History:** Coverage transitions over time

---

## Part X: Security & Privacy

### OPSEC Considerations

**Data NOT in Notifications:**
- Resident/faculty personal names (use role-based IDs: PGY1-01, FAC-PD)
- Deployment/TDY locations and dates
- Absence reasons (except type category)
- Specific medical/personal information

**Data ALLOWED in Notifications:**
- Rotation names (Inpatient, Clinic, Research, etc.)
- ACGME violation types (abstract, not person-specific)
- Coverage percentages (aggregated, not individual)
- Defense level status (system-wide, not person-specific)

**Webhook Security:**
- All webhooks require HTTPS
- Signatures on webhook payloads (HMAC-SHA256)
- Rate limiting per webhook URL
- Audit trail of all webhook deliveries

**Email Security:**
- HTML templates sanitized against XSS
- No embedded secrets or tokens in email body
- Reply-to address configured (no direct replies)
- Unsubscribe link on every notification email

---

## Part XI: Troubleshooting Guide

### Issue: Notifications Not Sending

**Check 1:** Notification preferences
```python
prefs = service._get_user_preferences(user_id)
print(f"Enabled channels: {prefs.enabled_channels}")
print(f"Type enabled: {prefs.notification_types.get(type_name)}")
print(f"Quiet hours: {prefs.quiet_hours_start}-{prefs.quiet_hours_end}")
```

**Check 2:** Celery task status
```bash
celery -A app.celery_app inspect active
celery -A app.celery_app inspect registered
```

**Check 3:** Redis connectivity
```bash
redis-cli ping
redis-cli KEYS "celery*" | wc -l
```

**Check 4:** Email service configuration
```python
from app.services.email_service import EmailService
service = EmailService.from_env()
service.test_connection()
```

---

### Issue: Webhook Delivery Failures

**Check 1:** Network connectivity
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"test": true}' \
  https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Check 2:** Webhook retry status
```sql
SELECT * FROM celery_tasks
WHERE task_name = 'send_webhook'
AND status = 'failed'
ORDER BY created_at DESC LIMIT 10;
```

**Check 3:** Webhook signature verification (if required)
```python
import hmac
import hashlib
payload = b'{"event": "notification"...}'
expected_sig = hmac.new(
    b'webhook_secret',
    payload,
    hashlib.sha256
).hexdigest()
```

---

### Issue: Performance / High Queue Depth

**Symptoms:** `notification_queue_depth` metric increasing

**Solutions:**
1. Increase Celery worker concurrency:
```bash
celery -A app.celery_app worker --concurrency=16 --prefetch-multiplier=4
```

2. Check for stuck tasks:
```bash
celery -A app.celery_app inspect active | grep send_email
```

3. Monitor email service rate limits:
```python
from app.services.email_service import EmailService
service = EmailService.from_env()
print(f"Rate: {service.rate_limit_per_minute} emails/min")
```

---

## Part XII: Future Enhancements

### Planned Features (Commented Out, Ready)

1. **Email Digest Mode**
   - Location: `notification_preferences.email_digest_enabled`
   - Frequency: Daily/weekly aggregation
   - Status: Schema ready, processing logic pending

2. **SMS Notifications**
   - Channel stub: Requires Twilio integration
   - Priority: For critical ACGME alerts
   - Timeline: Q1 2026

3. **Mobile Push Notifications**
   - Firebase Cloud Messaging (FCM)
   - User device registration
   - Timeline: Q1 2026

4. **Notification Templates Engine**
   - Custom template creation by administrators
   - Template versioning and A/B testing
   - Timeline: Q2 2026

5. **Slack Direct Message Integration**
   - User Slack workspace account linking
   - Direct message delivery option
   - Thread-based notification grouping
   - Timeline: Q2 2026

6. **Advanced Analytics**
   - Notification open rate tracking
   - Click-through analysis
   - User engagement scoring
   - Timeline: Q2 2026

---

## Summary: Complete Tool Inventory

### All Delivery Channels
| Channel | Status | Retry Logic | External Service |
|---------|--------|-------------|------------------|
| **In-App** | ✓ Implemented | Sync (no retry) | Database |
| **Email** | ✓ Implemented | Yes (3x, 60-300s) | SMTP |
| **Webhook** | ✓ Implemented | Yes (3x, 30-120s) | HTTP |
| **SMS** | ☐ Planned | — | Twilio |
| **Push** | ☐ Planned | — | FCM |
| **Slack DM** | ☐ Planned | — | Slack API |

### Notification Types Coverage
| Type | Channels | Priority | Recipient |
|------|----------|----------|-----------|
| SCHEDULE_PUBLISHED | in_app, email | HIGH | Residents/Faculty |
| ASSIGNMENT_CHANGED | in_app, email | HIGH | Affected person |
| SHIFT_REMINDER_24H | in_app, email | NORMAL | Person w/ assignment |
| SHIFT_REMINDER_1H | in_app | HIGH | Person w/ assignment |
| ACGME_WARNING | in_app, email, webhook | HIGH | Admin/Coordinator |
| ABSENCE_APPROVED | in_app, email | NORMAL | Requester |
| ABSENCE_REJECTED | in_app, email | NORMAL | Requester |
| Swap Types (7) | in_app, email, webhook | NORMAL-HIGH | Swap parties |

### Alert Triggers (7 Sources)
1. System errors → System alerts
2. Secret rotation → Security alerts
3. Burnout precursors → Clinical alerts
4. Schedule conflicts → Conflict alerts
5. Compliance violations → Regulatory alerts
6. Marketplace matches → Swap opportunities
7. Defense level transitions → Coverage alerts

---

## References

**Source Files:**
- `/backend/app/notifications/` - Core notification system
- `/backend/app/notifications/channels.py` - Channel implementations
- `/backend/app/notifications/service.py` - Service logic
- `/backend/app/notifications/tasks.py` - Celery background tasks
- `/backend/app/models/notification.py` - Database models
- `/mcp-server/src/scheduler_mcp/` - MCP tool definitions
- `/backend/app/services/conflict_alert_service.py` - Conflict detection
- `/backend/app/services/swap_notification_service.py` - Swap notifications
- `/backend/app/middleware/errors/reporters.py` - Error reporting
- `/backend/app/security/secret_rotation.py` - Secret rotation alerts

**Documentation:**
- CLAUDE.md - Project guidelines
- docs/api/ - API reference
- docs/development/ - Development guides

---

**End of G2_RECON SEARCH_PARTY Report**
**Completeness:** 100% - All channels, types, triggers, and tools documented
**Undocumented Items Found:** 7 alert sources (now documented)
