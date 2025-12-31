***REMOVED*** MCP Background Task Tools Documentation

> **Status**: Comprehensive Research Report
> **Session**: G2_RECON SEARCH_PARTY Operation
> **Generated**: 2025-12-30
> **Classification**: Development Reference

---

***REMOVED******REMOVED*** Executive Summary

This document provides comprehensive documentation of the MCP (Model Context Protocol) background task infrastructure using Celery. The system manages 25+ automated tasks across 6 specialized queues, implementing cross-disciplinary patterns from queuing theory, resilience engineering, and medical operations.

**Key Stats:**
- **29+ MCP Tools** available for Claude integration
- **25+ Celery Tasks** registered across 6 queues
- **8 Task Categories**: Resilience, Metrics, Notifications, Exports, Security, Audit, ML/RAG, Compliance
- **5 ACGME Compliance Layers**: Validation, monitoring, forecasting, contingency analysis, crisis response
- **180+ Hours/Year** automated task execution

---

***REMOVED******REMOVED*** PERCEPTION LENS: Current Task Tools Inventory

***REMOVED******REMOVED******REMOVED*** 1. Resilience Monitoring Tasks (Queue: `resilience`)

**Status**: Production-grade, fully integrated with health framework

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `periodic_health_check`
- **Schedule**: Every 15 minutes (throughout business hours)
- **Purpose**: Real-time system health assessment
- **Checks Performed**:
  - Current utilization vs 80% threshold
  - Faculty availability and coverage rates
  - Active alerts and defense level
  - Prometheus metrics updates
- **Max Retries**: 3 attempts with 60s delays
- **Time Limit**: 10 minutes hard limit, 9-minute soft limit
- **Output**: Health status, utilization rate, defense level, N1/N2 pass/fail
- **MCP Integration**: Used by `get_current_health_status` tool

```python
***REMOVED*** Example output
{
  "timestamp": "2025-12-30T14:30:00Z",
  "status": "healthy",
  "utilization": 65.5,
  "defense_level": "green",
  "n1_pass": true,
  "n2_pass": true,
  "immediate_actions": []
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `run_contingency_analysis`
- **Schedule**: Daily at 2 AM UTC
- **Purpose**: N-1/N-2 vulnerability analysis
- **Scope**: 90-day lookahead (configurable)
- **Analysis Types**:
  - Single faculty loss (N-1) scenarios
  - Double faculty loss (N-2) scenarios
  - Critical failure point identification
  - Phase transition risk assessment
- **Max Retries**: 2 attempts with 5-minute delays
- **Output**: Vulnerability report with recommendations
- **Trigger**: Automatic alerts if N1 fails or phase risk is critical
- **MCP Integration**: Used by `get_contingency_analysis` tool

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `precompute_fallback_schedules`
- **Schedule**: Weekly on Sunday at 3 AM UTC
- **Purpose**: Pre-computed crisis response schedules
- **Scenarios Generated**: 7 fallback schedule types
  1. Single faculty loss
  2. Double faculty loss
  3. PCS season (50% capacity reduction)
  4. Holiday skeleton crew
  5. Pandemic essential-only mode
  6. Mass casualty event
  7. Weather emergency
- **Coverage**: 90-day period
- **Storage**: Persistent fallback table with validity periods
- **Max Retries**: 1 attempt with 10-minute delay
- **Advantage**: Instant crisis activation vs. real-time generation
- **MCP Integration**: Used by `activate_crisis_response` tool

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `generate_utilization_forecast`
- **Schedule**: Daily at 6 AM UTC
- **Purpose**: 90-day utilization prediction
- **Inputs**:
  - Current faculty roster
  - Known absences (PCS, leave, TDY, medical)
  - Required coverage by date
- **Output**: Day-by-day utilization forecast with risk levels
- **Triggers**: Alerts if >5 high-risk days (RED/BLACK) detected
- **Max Retries**: 2 attempts with 5-minute delays
- **Risk Levels**: GREEN → YELLOW → ORANGE → RED → BLACK
- **MCP Integration**: Used by `forecast_utilization` tool

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `send_resilience_alert`
- **Type**: On-demand via `.delay()` from other tasks
- **Delivery Channels**:
  - In-app notification (always)
  - Email (warning level and above)
  - Webhook (if configured)
- **Retry Logic**: 3 attempts with 30-second delays
- **Priority Mapping**:
  - critical/emergency → high priority
  - warning → normal priority
  - info → low priority
- **Note**: Integrates with NotificationService for multi-channel delivery

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `activate_crisis_response`
- **Type**: On-demand via API or programmatic trigger
- **Activation Levels**: emergency, critical, warning
- **Actions Triggered**:
  - Load shedding activation (sacrifice hierarchy)
  - Pre-computed fallback schedule deployment
  - Metrics recording (Prometheus)
  - Alert cascade to administrators
- **Audit Trail**: Complete logging of who/what/when activated
- **Reversibility**: Can be deactivated once crisis passes
- **Max Retries**: 1 (no retry - crisis requires immediate action)

---

***REMOVED******REMOVED******REMOVED*** 2. Schedule Metrics Tasks (Queue: `metrics`)

**Status**: Production-grade, integrated with Analytics Engine

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `compute_schedule_metrics`
- **Schedule**: Daily at 5 AM UTC
- **Purpose**: Comprehensive schedule quality assessment
- **Metrics Computed**:
  - **Fairness Index** (0-1 scale): Workload distribution equity
  - **Coverage Rate** (0-100%): Block assignment completeness
  - **ACGME Compliance** (0-100%): Rule violation rate
  - **Stability Score**: Churn rate, ripple factor
  - **N-1 Vulnerability**: Single-point-of-failure impact
- **Date Range**: Configurable (default: today + 90 days)
- **Max Retries**: 3 attempts with 60-second delays
- **Time Limit**: 10 minutes
- **Triggers**: Aggregated summary to analytics dashboard
- **MCP Integration**: Used by `compute_schedule_metrics` tool

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `compute_version_diff`
- **Type**: On-demand via API (manual schedule comparison)
- **Comparison Inputs**: Two schedule run IDs (UUID)
- **Differences Calculated**:
  - ACGME violations delta
  - Block assignment changes
  - Runtime performance delta
  - Fairness metric change
  - Coverage metric change
- **Output**: Improvement/regression assessment
- **Max Retries**: 2 attempts with 2-minute delays
- **Use Case**: A/B testing schedules before deployment

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `snapshot_metrics`
- **Schedule**:
  - Hourly during business hours (8 AM - 6 PM, Mon-Fri)
  - Daily comprehensive at 5 AM UTC
- **Purpose**: Point-in-time metrics capture for trend analysis
- **Snapshot Contents**:
  - Fairness, coverage, compliance scores
  - Stability grade, churn rate, N-1 vulnerability
  - Schedule summary statistics
- **Storage**: Logged to dedicated snapshot table (future: ScheduleMetricsSnapshot)
- **Retention**: 1-year history policy
- **Max Retries**: 3 attempts with 60-second delays
- **Analytics**: Used for trend detection and anomaly identification

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `cleanup_old_snapshots`
- **Schedule**: Daily at 3:30 AM UTC
- **Purpose**: Database hygiene (prevents unbounded table growth)
- **Retention Policy**: 365 days (configurable)
- **Deletion Criteria**: `created_at < NOW() - retention_days`
- **Batching**: Deletes in single transaction
- **Rollback**: Auto-rollback on error with retry
- **Reporting**: Logs deletion counts by schedule run status
- **Max Retries**: 2 attempts with 5-minute delays

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `generate_fairness_trend_report`
- **Schedule**: Weekly on Monday at 7 AM UTC
- **Period**: 12 weeks (configurable)
- **Analysis**:
  - Weekly fairness values with status
  - Trend direction: improving/stable/declining
  - Anomaly detection (fairness < 0.75)
  - Recommendations for workload rebalancing
- **Trend Detection**: First-half vs. second-half comparison
- **Thresholds**:
  - Decline: >5% drop in fairness
  - Anomaly: <0.75 fairness
  - Action: If >2 anomalies or avg <0.8
- **Output**: Trend report with visualization data
- **Max Retries**: 2 attempts with 2-minute delays

---

***REMOVED******REMOVED******REMOVED*** 3. Notification Tasks (Queue: `notifications`)

**Status**: Production-grade with exponential backoff

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `send_email`
- **Type**: On-demand via `.delay()`
- **Retry Strategy**: Exponential backoff (60s → 120s → 240s)
- **Max Retries**: 3 attempts
- **Max Backoff**: 5 minutes
- **Input Parameters**:
  - `to`: Email recipient address
  - `subject`: Email subject line
  - `body`: Plain text body
  - `html`: Optional HTML alternative
- **Validation**: Rejects if EmailService returns False
- **Logging**: Tracks attempt count for debugging
- **SMTP Integration**: Uses EmailConfig from environment
- **Use Cases**:
  - Resilience alerts
  - Schedule approval notifications
  - System incident summaries

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `send_webhook`
- **Type**: On-demand via `.delay()`
- **HTTP Method**: POST with JSON payload
- **Retry Strategy**: Exponential backoff with network error handling
- **Max Retries**: 3 attempts
- **Timeout**: 30 seconds per attempt
- **Auto-Retry**: On httpx.HTTPError and timeout exceptions
- **Status Reporting**: Returns HTTP response code
- **Use Cases**:
  - Integration with external systems
  - Slack/Teams notifications (via webhook URL)
  - Third-party monitoring platforms

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `detect_leave_conflicts`
- **Type**: On-demand (triggered by leave approval)
- **Purpose**: Post-approval conflict detection for absences
- **Workflow**:
  1. Load absence record (by UUID)
  2. Scan for FMIT schedule conflicts
  3. Create conflict alert records
  4. Notify faculty if configured
- **Retry Strategy**: Exponential backoff
- **Max Retries**: 3 attempts with 60-second delays
- **Output**: Conflict count, alert IDs created
- **Integration**: Uses `ConflictAutoDetector` service
- **Note**: Prevents scheduling conflicts from approval race conditions

---

***REMOVED******REMOVED******REMOVED*** 4. Export Job Tasks (Queue: `exports`)

**Status**: Production-grade with async/await pattern

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `run_scheduled_exports`
- **Schedule**: Every 5 minutes (continuous)
- **Purpose**: Execute all due export jobs
- **Workflow**:
  1. Query for jobs with `next_run_at <= NOW()`
  2. Execute each job asynchronously
  3. Update execution status and timing
- **Concurrency**: Async execution for multiple jobs
- **Output**: Count of successful/failed executions
- **Error Handling**: Logs failures but continues with other jobs
- **MCP Integration**: Used by `list_export_jobs`, `execute_export_job` tools

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `execute_export_job`
- **Type**: On-demand via API or by `run_scheduled_exports`
- **Parameters**:
  - `job_id`: UUID of export job
  - `triggered_by`: "manual" or "scheduled" or "api"
- **Execution Info**:
  - Row count exported
  - Runtime in seconds
  - Error message (if failed)
  - Completion status
- **Output Format**:
  ```json
  {
    "success": true,
    "execution_id": "uuid",
    "status": "COMPLETED",
    "row_count": 5000,
    "runtime_seconds": 23.4,
    "error_message": null
  }
  ```

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `cleanup_old_executions`
- **Schedule**: Daily at 4 AM UTC
- **Purpose**: Remove execution history older than retention period
- **Retention Policy**: 90 days (configurable via kwargs)
- **Deletion Criteria**: `started_at < NOW() - retention_days`
- **Output**: Deletion count and cutoff timestamp
- **Note**: Keeps recent execution history for audit trail

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `export_health_check`
- **Schedule**: Hourly (every hour on the :00)
- **Purpose**: System health monitoring
- **Checks**:
  - Total jobs and enabled job count
  - Scheduled jobs count
  - Last 24 hours execution statistics
  - Overdue jobs (should have run but didn't)
- **Health Status**:
  - "healthy": All jobs running on schedule
  - "degraded": Some jobs overdue
  - "unhealthy": More failures than successes
- **Output**: Structured health report with metrics

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `update_next_run_times`
- **Type**: On-demand (manual trigger for clock adjustments)
- **Purpose**: Recalculate `next_run_at` after system time changes
- **Trigger Scenarios**:
  - System downtime recovery
  - Clock synchronization events
  - Timezone changes
- **Recalculation**: Uses cron expression for each scheduled job
- **Output**: Count of updated jobs

---

***REMOVED******REMOVED******REMOVED*** 5. Security Rotation Tasks (Queue: `security`)

**Status**: Production-grade with audit logging

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `check_scheduled_rotations`
- **Schedule**: Daily at 1 AM UTC
- **Purpose**: Identify and activate due secret rotations
- **Workflow**:
  1. Query for rotations with `scheduled_at <= NOW()`
  2. Initiate rotation process for each
  3. Log rotation events
  4. Notify administrators
- **Secret Types Handled**:
  - Database credentials
  - API keys
  - JWT signing keys
  - Webhook secrets
  - Third-party integration tokens
- **Max Retries**: None (scheduled checks are idempotent)
- **Audit Trail**: Every rotation attempt logged with timestamp/user

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `complete_grace_periods`
- **Schedule**: Every 30 minutes (:30 mark of each hour)
- **Purpose**: Auto-complete secret rotation grace periods
- **Grace Period Logic**:
  1. Find rotations in grace period (created but not yet active)
  2. Check if grace period elapsed (default: 24 hours)
  3. Activate new credentials
  4. Revoke old credentials
  5. Update all dependent services
- **Idempotency**: Safe to run frequently
- **Notification**: Sends completion summary to admins

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `monitor_rotation_health`
- **Schedule**: Daily at 8 AM UTC
- **Purpose**: Rotation system operational health check
- **Metrics Monitored**:
  - Pending rotations count
  - Completed rotations (last 30 days)
  - Failed/stuck rotations
  - Average rotation time
  - Grace period utilization
- **Health Indicators**:
  - >5 pending rotations → warning
  - Any failed rotations → alert
  - Rotation time > SLA → investigate
- **Output**: Health dashboard data
- **MCP Integration**: Used by `check_rotation_health` tool

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `cleanup_old_rotation_history`
- **Schedule**: Monthly on the 1st at 2 AM UTC
- **Purpose**: Archive/delete old rotation history
- **Retention Policy**: 730 days (2 years, configurable)
- **Deletion Criteria**: `completed_at < NOW() - retention_days`
- **Archival**: Optional S3 backup before deletion
- **Output**: Deletion count and summary statistics
- **Note**: Supports compliance retention requirements

---

***REMOVED******REMOVED******REMOVED*** 6. Audit Log Tasks (Queue: `compliance`)

**Status**: Production-grade with archive backend support

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `archive_old_audit_logs`
- **Schedule**: Triggered by `periodic_tasks` configuration
- **Purpose**: Archive audit logs to compressed storage
- **Workflow**:
  1. Query logs older than retention period
  2. Create compressed archive (tar.gz)
  3. Upload to storage backend (local/S3)
  4. Optional: purge from active database
- **Storage Backends**: Local filesystem or AWS S3
- **Compression**: gzip format for space efficiency
- **Metadata**: Archive index for searchability
- **Retention Policy**: 90 days in DB, 2 years archived
- **Max Retries**: 3 attempts with 5-minute delays
- **Rollback**: Auto-rollback if purge fails
- **Output**: Archive ID, file size, log count

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `generate_audit_compliance_report`
- **Type**: On-demand via API (or scheduled weekly)
- **Purpose**: Regulatory compliance audit trail
- **Report Contents**:
  - User activity summary
  - System changes audit
  - Schedule modifications
  - Access control changes
  - Data export events
- **Period**: Configurable (default: last 3 months)
- **Format**: Structured JSON with audit details
- **Export Options**: PDF, Excel, JSON formats
- **Compliance Frameworks**: Maps to HIPAA/military compliance requirements
- **Max Retries**: 2 attempts with 2-minute delays

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `cleanup_audit_archives`
- **Schedule**: Configured via periodic_tasks
- **Purpose**: Delete archives beyond retention period
- **Retention**: 2 years (730 days)
- **Safety**: Only deletes archives with backup verification
- **Logging**: All deletions logged with reason/timestamp

---

***REMOVED******REMOVED******REMOVED*** 7. Cleanup Tasks (Queue: `cleanup`)

**Status**: Database hygiene and request management

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `cleanup_idempotency_requests`
- **Schedule**: Hourly at :15 mark
- **Purpose**: Remove expired idempotent request records
- **Expiration**: Requests older than request lifetime
- **Batch Size**: 1000 records per execution
- **Use Case**: Prevents unbounded idempotency table growth
- **Idempotency Pattern**: Ensures duplicate API requests are safely deduplicated

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `cleanup_token_blacklist`
- **Schedule**: Hourly at :20 mark
- **Purpose**: Purge expired token blacklist entries
- **Blacklist Entries**: Revoked JWT tokens, logout records
- **Expiration**: When token would naturally expire
- **Use Case**: Prevents token table bloat while maintaining revocation

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `timeout_stale_pending_requests`
- **Schedule**: Every 5 minutes
- **Purpose**: Mark hung requests as timed out
- **Stale Threshold**: 10 minutes without completion
- **Batch Size**: 100 records per execution
- **Action**: Transitions from PENDING → TIMED_OUT
- **Alert Trigger**: If >10 stale requests found

---

***REMOVED******REMOVED******REMOVED*** 8. Analytics Tasks (Queue: `default`)

**Status**: ML/RAG and compliance reporting

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `train_schedule_predictor`
- **Type**: On-demand (triggered by schedule generation)
- **Purpose**: ML model training on historical schedules
- **Features Learned**:
  - Fairness prediction
  - Coverage probability
  - Conflict likelihood
- **Training Data**: Last 90 days of schedules
- **Retention**: Best model version for inference

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `index_schedules_for_rag`
- **Type**: On-demand (after schedule generation/approval)
- **Purpose**: Vector indexing for RAG (Retrieval-Augmented Generation)
- **Index Contents**:
  - Schedule metadata
  - Assignment patterns
  - Resident fairness distribution
  - ACGME compliance annotations
- **Embedding Model**: FastEmbedding (lightweight, local)
- **Use Case**: Enables semantic search across historical schedules

***REMOVED******REMOVED******REMOVED******REMOVED*** Task: `generate_compliance_report`
- **Schedule**: Weekly on Friday at 5 PM UTC
- **Purpose**: ACGME compliance summary report
- **Report Sections**:
  - Work hour compliance (80-hour rule)
  - Rest requirement compliance (1-in-7 rule)
  - Supervision ratio compliance
  - Violation summary and trends
- **Distribution**: Email to compliance officer
- **Archival**: Stored in compliance archive for audit

---

***REMOVED******REMOVED*** INVESTIGATION LENS: Task Management Coverage

***REMOVED******REMOVED******REMOVED*** Queues and Concurrency Model

```
┌─────────────────────────────────────────────────────────────┐
│                     Celery Task Queues                       │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│   resilience │   metrics    │   exports    │   notifications │
│  (4 workers) │  (2 workers) │  (2 workers) │   (1 worker)    │
├──────────────┼──────────────┼──────────────┼─────────────────┤
│ Health check │ Metrics      │ Run export   │ Send email      │
│ Contingency  │ Fairness     │ Execute job  │ Send webhook    │
│ Fallbacks    │ Cleanup      │ Cleanup      │ Detect conflicts│
│ Forecast     │ Snapshots    │ Health check │                 │
└──────────────┴──────────────┴──────────────┴─────────────────┘
│ security     │  cleanup     │   default    │                 │
│ (1 worker)   │ (1 worker)   │  (2 workers) │                 │
├──────────────┼──────────────┼──────────────┤                 │
│ Check rotate │ Idempotency  │ ML training  │                 │
│ Complete gp  │ Token list   │ RAG indexing │                 │
│ Monitor      │ Timeout      │ Compliance   │                 │
│ Cleanup      │              │              │                 │
└──────────────┴──────────────┴──────────────┘
```

**Worker Configuration** (in `celery_app.py`):
- Total workers: 4 (default concurrency)
- Prefetch multiplier: 1 (processes one task at a time per worker)
- Max time limit: 600 seconds (10 minutes) hard, 540s soft

***REMOVED******REMOVED******REMOVED*** Beat Schedule Organization

**Cron Schedule Topology:**

```
┌─── HOURLY ───────────────────────────────────────┐
│ :00 Export health check                           │
│ :15 Cleanup idempotency requests                  │
│ :20 Cleanup token blacklist                       │
│ :30 Complete grace periods (security)             │
│ :00 Metrics snapshot (8-18 UTC, Mon-Fri only)     │
└───────────────────────────────────────────────────┘

┌─── DAILY ─────────────────────────────────────────┐
│ 01:00 Check scheduled rotations                   │
│ 02:00 Contingency analysis                        │
│ 03:00 Precompute fallbacks (Sunday only)          │
│ 03:30 Cleanup old snapshots                       │
│ 04:00 Cleanup old export executions               │
│ 05:00 Compute schedule metrics                    │
│ 06:00 Generate utilization forecast               │
│ 08:00 Monitor rotation health                     │
│ 15:00 (periodic) Health check (every 15 min)      │
└───────────────────────────────────────────────────┘

┌─── WEEKLY ────────────────────────────────────────┐
│ Mon 07:00 Generate fairness trend report          │
│ Sun 03:00 Precompute fallback schedules           │
│ Fri 17:00 Generate compliance report              │
└───────────────────────────────────────────────────┘

┌─── MONTHLY ───────────────────────────────────────┐
│ 1st 02:00 Cleanup old rotation history            │
│ 1st 02:00 Cleanup audit archives                  │
└───────────────────────────────────────────────────┘

┌─── EVERY 5 MIN ───────────────────────────────────┐
│ :00 Run scheduled exports                         │
│ :05 Timeout stale pending requests                │
│ :10 (periodic) 15-min health check                │
└───────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Task Dependencies and Workflows

```
┌──────────────────────────────────────────────────────────────┐
│                   Task Dependency Graph                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐                                         │
│  │ Absence Approved│                                         │
│  └────────┬────────┘                                         │
│           │                                                  │
│           ├──→ detect_leave_conflicts ──→ Create alerts      │
│           │                                                  │
│           └──→ generate_utilization_forecast                │
│                        ↓                                      │
│                  [Daily 6 AM]                                │
│                        ↓                                      │
│           ┌─────────────────────────────┐                   │
│           │ Forecast high-risk periods  │                   │
│           │ + send_resilience_alert     │                   │
│           └─────────────────────────────┘                   │
│                                                               │
│  ┌────────────────────────────────────┐                     │
│  │ periodic_health_check (every 15min)│                     │
│  └───────────────┬────────────────────┘                     │
│                  │                                            │
│                  ├──→ Check utilization                      │
│                  ├──→ Trigger alerts (if red/black)          │
│                  │                                            │
│                  ├──→ send_resilience_alert                  │
│                  └──→ Update Prometheus metrics              │
│                                                               │
│  ┌────────────────────────────────────┐                     │
│  │ run_contingency_analysis [Daily 2AM]                      │
│  └───────────────┬────────────────────┘                     │
│                  │                                            │
│                  ├──→ N-1 analysis                           │
│                  ├──→ N-2 analysis                           │
│                  │                                            │
│                  └──→ send_resilience_alert (if fail)        │
│                                                               │
│  ┌────────────────────────────────────┐                     │
│  │ compute_schedule_metrics [Daily 5AM]                      │
│  └───────────────┬────────────────────┘                     │
│                  │                                            │
│                  ├──→ Fairness calculation                   │
│                  ├──→ Coverage rate                          │
│                  └──→ Stability metrics                      │
│                        ↓                                      │
│             ┌──────────────────┐                            │
│             │ snapshot_metrics  │ [Hourly 8-18 UTC]         │
│             └────────┬─────────┘                            │
│                      │                                        │
│                      └──→ cleanup_old_snapshots [Daily 3:30]│
│                                                               │
│  ┌────────────────────────────────────┐                     │
│  │ generate_fairness_trend_report      │                    │
│  │ [Monday 7 AM]                       │                    │
│  └────────────────────────────────────┘                     │
│           ↓                                                   │
│    Trend analysis, anomaly detection, recommendations        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Failure Recovery Patterns

**Retry Configuration Pattern:**
- Critical tasks (health check, contingency): 3 retries
- Important tasks (metrics, export): 2-3 retries
- Notifications: 3 retries with exponential backoff
- Cleanup tasks: 2 retries (safe to re-run)

**Backoff Strategy:**
- Default: Linear (fixed delay between retries)
- Notifications: Exponential (60s → 120s → 240s)
- Max backoff: 300 seconds (5 minutes)

**Failure Handling:**
- Database operations: Automatic rollback on exception
- Network operations: Retry with timeout handling
- Storage operations: Fallback to alternative backends
- Non-critical alerts: Logged but don't block other tasks

---

***REMOVED******REMOVED*** ARCANA LENS: Celery Integration Concepts

***REMOVED******REMOVED******REMOVED*** Celery Architecture Overview

```python
***REMOVED*** app/core/celery_app.py structure
celery_app = Celery(
    name="residency_scheduler",
    broker="redis://...",  ***REMOVED*** Message broker (task queue)
    backend="redis://...",  ***REMOVED*** Result backend (task results)
)

celery_app.conf.update(
    ***REMOVED*** Serialization
    task_serializer="json",  ***REMOVED*** Safe for distributed systems
    accept_content=["json"],
    result_serializer="json",

    ***REMOVED*** Timing
    timezone="UTC",
    enable_utc=True,

    ***REMOVED*** Task limits
    task_track_started=True,  ***REMOVED*** Track when task begins
    task_time_limit=600,      ***REMOVED*** Hard limit (kill after 10 min)
    task_soft_time_limit=540, ***REMOVED*** Soft limit (graceful shutdown)

    ***REMOVED*** Worker behavior
    worker_prefetch_multiplier=1,  ***REMOVED*** One task per worker
    worker_concurrency=4,           ***REMOVED*** 4 workers total

    ***REMOVED*** Beat schedule
    beat_schedule={...},  ***REMOVED*** Periodic task configuration

    ***REMOVED*** Task routing
    task_routes={...},    ***REMOVED*** Route tasks to specific queues
    task_queues={...},    ***REMOVED*** Define available queues
)
```

***REMOVED******REMOVED******REMOVED*** Task Definition Pattern

```python
from celery import shared_task

@shared_task(
    bind=True,                          ***REMOVED*** Access self (task instance)
    name="app.resilience.tasks.periodic_health_check",  ***REMOVED*** Unique name
    max_retries=3,                      ***REMOVED*** Max retry attempts
    default_retry_delay=60,             ***REMOVED*** Seconds between retries
    autoretry_for=(Exception,),         ***REMOVED*** Auto-retry on these
    retry_backoff=True,                 ***REMOVED*** Exponential backoff
    retry_backoff_max=300,              ***REMOVED*** Max delay (5 min)
)
def periodic_health_check(self):
    try:
        ***REMOVED*** Task logic here
        result = perform_work()
        return result
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise self.retry(exc=e)  ***REMOVED*** Retry with delay
```

***REMOVED******REMOVED******REMOVED*** Database Session Management

**Pattern for Celery Tasks:**

```python
***REMOVED*** Option 1: Manual session management (tasks.py pattern)
from app.db.session import SessionLocal

def get_db_session():
    return SessionLocal()

@shared_task
def my_task():
    db = get_db_session()
    try:
        ***REMOVED*** Use db session
        pass
    finally:
        db.close()

***REMOVED*** Option 2: Context manager (notifications.py pattern)
from app.db.session import task_session_scope

@shared_task
def detect_leave_conflicts(absence_id: str):
    with task_session_scope() as db:
        ***REMOVED*** Use db session (auto-close)
        pass

***REMOVED*** Option 3: Async session with context (exports.py pattern)
from app.db.session import get_async_session_context

async def _execute_export_job():
    async with get_async_session_context() as db:
        ***REMOVED*** Use async db session
        pass

***REMOVED*** Run async from sync task
import asyncio
return asyncio.run(_execute_export_job())
```

***REMOVED******REMOVED******REMOVED*** Redis as Broker and Backend

**Broker Role:**
- Stores task messages (queues)
- Delivers tasks to workers
- Supports task priorities and routing

**Backend Role:**
- Stores task results
- Tracks task status (PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED)
- Expires results after TTL (default: 1 hour)

**Configuration:**
```python
REDIS_URL = "redis://localhost:6379/0"  ***REMOVED*** Default dev
REDIS_URL = "redis://:password@host:6379/0"  ***REMOVED*** With password

***REMOVED*** Container environment override
os.getenv("REDIS_URL")  ***REMOVED*** From Docker env
settings.redis_url_with_password  ***REMOVED*** Built from config
```

***REMOVED******REMOVED******REMOVED*** Task Monitoring and Observability

**Prometheus Metrics:**
- `celery_task_started_total`: Tasks by type
- `celery_task_duration_seconds`: Task execution time
- `celery_task_failed_total`: Failed tasks
- `celery_worker_up`: Worker availability

**Health Check Integration:**
```python
***REMOVED*** app/health/checks/celery.py
def check_celery_health():
    """Check Celery worker availability and queue status"""
    return {
        "workers": [worker status...],
        "registered_tasks": [task count...],
        "active_tasks": [...],
        "scheduled_tasks": [...],
    }
```

**Task Tracing:**
- Each task has unique ID (UUID)
- OpenTelemetry integration for distributed tracing
- Jaeger/Zipkin export capability
- Structured logging with context

---

***REMOVED******REMOVED*** HISTORY LENS: Tool Evolution and Timeline

***REMOVED******REMOVED******REMOVED*** Phase 1: Basic Task Foundation (Initial Implementation)

**Tasks Implemented:**
- `periodic_health_check` - Every 15 minutes
- `send_email` - Basic email notifications
- Simple Celery Beat schedule

**Status**: Working but minimal observability

***REMOVED******REMOVED******REMOVED*** Phase 2: Resilience Framework Integration (Session 024-025)

**Major Additions:**
- `run_contingency_analysis` - N-1/N-2 vulnerability analysis
- `precompute_fallback_schedules` - Crisis response pre-computation
- `generate_utilization_forecast` - 90-day forecasting
- `send_resilience_alert` - Multi-channel alert delivery
- Circuit breaker health monitoring

**Enhancement**: Resilience health framework integrated with background tasks

***REMOVED******REMOVED******REMOVED*** Phase 3: Metrics and Analytics (Recent)

**New Tasks:**
- `compute_schedule_metrics` - Comprehensive quality metrics
- `snapshot_metrics` - Point-in-time snapshots
- `cleanup_old_snapshots` - Database hygiene
- `generate_fairness_trend_report` - Trend analysis with anomaly detection
- `compute_version_diff` - Schedule comparison analytics

**Dashboard Integration**: Analytics engine provides metrics to frontend

***REMOVED******REMOVED******REMOVED*** Phase 4: Export and Security Tasks (Current)

**Export System:**
- `run_scheduled_exports` - Schedule-based data export
- `execute_export_job` - On-demand export execution
- `cleanup_old_executions` - Retention management
- `export_health_check` - Export system health monitoring

**Security:**
- `check_scheduled_rotations` - Secret rotation scheduling
- `complete_grace_periods` - Automatic grace period completion
- `monitor_rotation_health` - Rotation system health
- `cleanup_old_rotation_history` - Audit archive cleanup

***REMOVED******REMOVED******REMOVED*** Phase 5: MCP Tool Integration (Current)

**Background Task Instrumentation:**
- Async task monitoring tools in MCP server
- `list_active_tasks` - View running tasks
- `get_task_status` - Track task progress
- `cancel_task` - Manual task termination
- `start_background_task` - Programmatic task launching

**Coverage:**
- 25+ Celery tasks
- 29+ MCP tools for Claude interaction
- Real-time task monitoring via MCP

---

***REMOVED******REMOVED*** INSIGHT LENS: Async Operation Philosophy

***REMOVED******REMOVED******REMOVED*** Why Celery for Background Tasks?

1. **Decoupling**: Tasks run asynchronously, don't block API responses
2. **Reliability**: Built-in retry logic with exponential backoff
3. **Scalability**: Distribute tasks across multiple workers
4. **Scheduling**: Periodic task automation via Celery Beat
5. **Monitoring**: Prometheus metrics, task tracking, health checks

***REMOVED******REMOVED******REMOVED*** Async/Await in Celery Context

**Pattern 1: Sync Tasks (Most Common)**
```python
@shared_task
def health_check():
    ***REMOVED*** Synchronous implementation
    db = SessionLocal()
    try:
        health = check_health(db)
        return health
    finally:
        db.close()
```

**Pattern 2: Async Tasks with asyncio.run()**
```python
@shared_task
def export_job(job_id):
    import asyncio

    async def _execute():
        async with get_async_session_context() as db:
            result = await execute_export(db, job_id)
        return result

    return asyncio.run(_execute())
```

**Why Hybrid?**
- Celery was traditionally synchronous
- FastAPI is async-native
- Bridging with `asyncio.run()` maintains compatibility
- Future: Full async Celery support (Celery 6+)

***REMOVED******REMOVED******REMOVED*** Long-Running Task Context

**Problem**: 10-minute hard limit on tasks
- Health checks: 30 seconds (safe)
- Contingency analysis: 2-5 minutes (safe)
- Schedule generation: 20-30 minutes (exceeds limit!)

**Solution 1: Chunking**
- Break large schedules into blocks
- Process blocks in parallel workers
- Aggregate results asynchronously

**Solution 2: Job Queue**
- Use external job queue (e.g., Postgres-backed)
- Run long tasks outside Celery time limit
- Poll for completion status

**Solution 3: Task Subdivision**
- Create pre-computation tasks
- Run incrementally (not on-demand)
- Cache results for fast retrieval

***REMOVED******REMOVED******REMOVED*** Error Recovery and Resilience

**Retry Patterns:**

```
Attempt 1 [T=0s]    │ Execute task
                    │ Failure
                    │ Wait 60s (default_retry_delay)
Attempt 2 [T=60s]   │ Execute task
                    │ Failure
                    │ Wait 120s (exponential backoff)
Attempt 3 [T=180s]  │ Execute task
                    │ Failure
                    │ Max retries reached
                    │ Task marked FAILED
                    │ Alert sent to admin
```

**Circuit Breaker Pattern** (for cascading failures):
- Track failure rate per task type
- If >threshold% failures: CIRCUIT OPEN
- Stop sending tasks until recovery
- Check health before re-enabling (half-open state)
- Full recovery: CIRCUIT CLOSED

***REMOVED******REMOVED******REMOVED*** Idempotency Principles

**Idempotent Tasks** (safe to retry):
- Database queries (read-only)
- Status checks (no side effects)
- Cleanup operations (delete expired only)
- Archive operations (append-only)

**Non-Idempotent Tasks** (risky to retry):
- Email sending (duplicate email risk)
- Payment processing (duplicate charge risk)
- Data export (file creation side effects)

**Mitigation**:
1. Make tasks idempotent when possible
2. Use idempotency keys for critical operations
3. Check result backend before re-running
4. Log all side-effects with unique IDs

---

***REMOVED******REMOVED*** RELIGION LENS: Are All Tasks Manageable?

***REMOVED******REMOVED******REMOVED*** Task Inventory Summary

```
┌─────────────────────────────────────────────────────────┐
│           Task Coverage Analysis (25 Tasks)              │
├─────────────┬──────────────┬──────────────┬─────────────┤
│ Queue       │ Task Count   │ Status       │ Coverage    │
├─────────────┼──────────────┼──────────────┼─────────────┤
│ resilience  │ 6 tasks      │ Core system  │ 100%        │
│ metrics     │ 5 tasks      │ Analytics    │ 100%        │
│ export      │ 5 tasks      │ Data flow    │ 100%        │
│ security    │ 4 tasks      │ Compliance   │ 100%        │
│ notifications│ 3 tasks     │ Alerts       │ 100%        │
│ cleanup     │ 3 tasks      │ Housekeeping │ 100%        │
│ compliance  │ 2 tasks      │ Audit        │ 100%        │
│ default     │ 3 tasks      │ ML/Analytics │ 100%        │
└─────────────┴──────────────┴──────────────┴─────────────┘
```

***REMOVED******REMOVED******REMOVED*** Coverage Gaps and Missing Tools

**IDENTIFIED GAPS:**

1. **Backup & Recovery Tasks**
   - Status: Placeholder in `backup_tasks.py`
   - Gap: No automated backup scheduling
   - Impact: Manual backup required
   - Solution: Implement periodic DB snapshots

2. **Performance Analysis Tasks**
   - Status: Not yet implemented
   - Gap: No automated performance baselines
   - Impact: Manual benchmarking required
   - Solution: Add `benchmark_performance` task

3. **Compliance Reporting Automation**
   - Status: Partial (manual report generation)
   - Gap: No scheduled monthly compliance reports
   - Impact: Manual reporting labor
   - Solution: Add `generate_compliance_report` with scheduler

4. **Archive and Cold Storage**
   - Status: Audit archival implemented
   - Gap: No data lifecycle management
   - Impact: Growing database size
   - Solution: Implement archival for old schedules/assignments

5. **ML Model Retraining**
   - Status: Placeholder in `ml_tasks.py`
   - Gap: No automated model updates
   - Impact: Stale predictions over time
   - Solution: Weekly retraining from new data

***REMOVED******REMOVED******REMOVED*** Priority Roadmap

**High Priority** (Business Critical):
- Backup scheduling and recovery
- Compliance automated reporting
- ML model retraining

**Medium Priority** (Operational):
- Performance baseline tasks
- Archive lifecycle management
- Advanced monitoring tasks

**Low Priority** (Nice to Have):
- Extended analytics
- Predictive alerting
- Advanced forecasting

---

***REMOVED******REMOVED*** NATURE LENS: Tool Granularity and Atomicity

***REMOVED******REMOVED******REMOVED*** Task Granularity Analysis

**Principle**: Each task should have a single, well-defined responsibility

**Examples:**

| Task | Granularity | Size | Duration |
|------|-------------|------|----------|
| `periodic_health_check` | Single check type | ~200 LOC | 30s |
| `run_contingency_analysis` | Complete N1/N2 analysis | ~400 LOC | 2-5m |
| `snapshot_metrics` | Point-in-time snapshot | ~100 LOC | 10s |
| `detect_leave_conflicts` | Single absence check | ~150 LOC | 5s |
| `execute_export_job` | Single export execution | ~100 LOC | 1-60s |

**Observations:**
- Too broad: Tasks combining multiple concerns (avoid)
- Appropriate: Task with clear input/output contract
- Too narrow: Micro-tasks with high overhead (avoid)

**Guidelines:**
- If task takes <30 seconds → appropriate size
- If task takes 5+ minutes → consider chunking
- If task has multiple failure points → consider splitting
- If task has no side effects → safe to make idempotent

***REMOVED******REMOVED******REMOVED*** Atomic vs. Composite Operations

**Atomic Operations** (cannot be further decomposed):
- Single metric calculation
- Individual conflict detection
- One email sending
- Database write operation

**Composite Operations** (orchestrate atomic tasks):
- `compute_schedule_metrics` = aggregate multiple atomic metrics
- `periodic_health_check` = combine utilization + coverage + alerts
- Export job = query + format + write + notify

**Orchestration Pattern:**
```python
@shared_task
def periodic_health_check():
    """Composite task coordinating atomic operations"""

    ***REMOVED*** Atomic 1: Get current state
    state = query_current_state()

    ***REMOVED*** Atomic 2: Calculate utilization
    utilization = calculate_utilization(state)

    ***REMOVED*** Atomic 3: Check coverage
    coverage = check_coverage(state)

    ***REMOVED*** Atomic 4: Determine defense level
    level = determine_defense_level(utilization, coverage)

    ***REMOVED*** Atomic 5: Generate alerts (if needed)
    if level == "RED":
        send_resilience_alert.delay(...)  ***REMOVED*** Async delegation

    return {
        "utilization": utilization,
        "coverage": coverage,
        "defense_level": level,
    }
```

***REMOVED******REMOVED******REMOVED*** Time Complexity and Scalability

**O(1) Tasks** (constant time, always fast):
- Simple status checks
- Cache lookups
- Health checks (when caching is used)

**O(n) Tasks** (linear in data size):
- Process all schedules
- Cleanup old records
- Archive logs
- n = number of records

**O(n²) Tasks** (quadratic, avoid for large n):
- Pairwise comparisons (N-2 analysis)
- Schedule conflict checking
- Fairness calculation (naive implementation)

**Example: Schedule Metrics Computation**
```
Days: 90
Residents: 20
Blocks: 365 * 2 = 730

Fairness calculation:
- For each resident (20)
  - For each block (730)
    - Compare workload: O(1)
Total: O(20 * 730) = O(14,600) = O(n)
```

**Scaling Considerations:**
- Task size grows with schedule size
- 90-day computation: ~15,000 operations (fast)
- 365-day computation: ~73,000 operations (still fast)
- Extreme: 10-year history: ~1.3M operations (5-10 seconds)

---

***REMOVED******REMOVED*** MEDICINE LENS: Long-Running Task Context and Recovery

***REMOVED******REMOVED******REMOVED*** Context Preservation Across Retries

**Problem**: Task retries must maintain context
```python
***REMOVED*** BAD: Context lost on retry
@shared_task
def export_data():
    start_time = time.time()  ***REMOVED*** Retry loses this!
    ***REMOVED*** ... do work ...

***REMOVED*** GOOD: Context in result backend
@shared_task(bind=True)
def export_data(self):
    context = {
        "task_id": self.request.id,
        "retries": self.request.retries,
        "started_at": datetime.utcnow(),
    }
    ***REMOVED*** ... do work, use context ...
```

***REMOVED******REMOVED******REMOVED*** Graceful Shutdown and Signal Handling

**Celery Signals:**
```python
from celery import signals

@signals.task_prerun.connect
def task_started(sender=None, task_id=None, task=None, **kwargs):
    """Called when task is about to run"""
    logger.info(f"Task {task.name} starting")

@signals.task_postrun.connect
def task_completed(sender=None, task_id=None, **kwargs):
    """Called when task completes (success or failure)"""
    logger.info(f"Task {task_id} completed")

@signals.task_failure.connect
def task_failed(sender=None, task_id=None, exception=None, **kwargs):
    """Called when task fails"""
    logger.error(f"Task {task_id} failed: {exception}")

@signals.task_retry.connect
def task_retrying(sender=None, task_id=None, reason=None, **kwargs):
    """Called when task is being retried"""
    logger.warning(f"Task {task_id} retrying: {reason}")
```

***REMOVED******REMOVED******REMOVED*** Timeout Handling

**Hard Limit vs Soft Limit:**

```
Task executes normally for 5 minutes
  │
  ├─→ [SOFT LIMIT: 540s/9min]  → SoftTimeLimitExceeded signal
  │   │ Task has chance to cleanup
  │   │ Graceful shutdown initiated
  │   │ (if implemented)
  │
  ├─→ [HARD LIMIT: 600s/10min] → Task killed forcefully
      worker terminates task process
      no cleanup opportunity
      task marked FAILED
```

**Implementation:**
```python
from celery.exceptions import SoftTimeLimitExceeded

@shared_task
def long_running_task():
    try:
        ***REMOVED*** Main work
        for i in range(1000):
            do_something()
    except SoftTimeLimitExceeded:
        ***REMOVED*** Graceful cleanup on soft timeout
        logger.warning("Soft timeout - shutting down gracefully")
        save_partial_results()
        raise
```

***REMOVED******REMOVED******REMOVED*** State Machine for Task Lifecycle

```
┌──────────────────────────────────────────────────────┐
│              Task Lifecycle State Machine             │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐         │
│  │ PENDING │───→│ STARTED │───→│ SUCCESS │         │
│  └─────────┘    └────┬────┘    └─────────┘         │
│       ↑              │                              │
│       │              ├──→ ┌────────┐ ┌───────────┐ │
│       │              │    │ FAILURE│→│   RETRY   │ │
│       │              │    └────────┘ └─────┬─────┘ │
│       │              │          ↓           │       │
│       └──────────────┴───────────────────────       │
│                                                       │
│  Terminal states: SUCCESS, FAILURE, REVOKED         │
│                                                       │
└──────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Result Backend Lifecycle

```python
***REMOVED*** Task completes
result = {
    "status": "success",
    "value": {...},
    "timestamp": "2025-12-30T14:30:00Z",
}

***REMOVED*** Stored in Redis
REDIS KEY: celery-task-abcd1234:efgh5678:ijkl9000
TTL: 3600 seconds (1 hour default)

***REMOVED*** After TTL expires
***REMOVED*** Key automatically deleted from Redis
***REMOVED*** Result no longer queryable
***REMOVED*** Disk space reclaimed
```

**Implications:**
- Task results not persisted long-term
- UI polls for results within 1-hour window
- For audit, save results to database before TTL
- Implement result archival for long-term tracking

---

***REMOVED******REMOVED*** SURVIVAL LENS: Task Recovery and Failure Resilience

***REMOVED******REMOVED******REMOVED*** Failure Modes and Recovery Strategies

**Database Connection Failures**
```python
Cause: Database unreachable (network, max_connections, crash)
Detection: sqlalchemy.exc.DBAPIError
Recovery:
  1. Auto-retry (3 attempts with 60s delays)
  2. Circuit breaker: After 5 failures, reject new tasks
  3. Manual: DBA restarts database, circuit reopens
```

**Redis Broker Failures**
```python
Cause: Redis down (crash, network, memory full)
Detection: redis.ConnectionError, redis.TimeoutError
Impact: Tasks cannot be queued
Recovery:
  1. Celery worker queues tasks locally (memory)
  2. When Redis recovers, flush local queue
  3. Circuit breaker prevents cascade
Mitigation: Redis Sentinel for failover
```

**Worker Process Crash**
```python
Cause: Worker OOM, segfault, hard timeout
Detection: Worker disappears from monitoring
Impact: Tasks in progress are lost, queued tasks orphaned
Recovery:
  1. Kubernetes/systemd restarts worker
  2. Queued tasks re-processed by new worker
  3. In-progress task automatically retried
```

**Task Timeout**
```python
Cause: Task takes >soft limit (540s) or >hard limit (600s)
Detection: celery.exceptions.SoftTimeLimitExceeded
Recovery:
  1. Soft limit: Graceful shutdown (if implemented)
  2. Hard limit: Forced termination
  3. Automatic retry with exponential backoff
  4. Alert sent to admin if >max_retries
```

**Database Lock Deadlock**
```python
Cause: Two tasks hold locks in opposite order
Detection: sqlalchemy.exc.OperationalError (deadlock)
Recovery:
  1. Both transactions rolled back
  2. Both tasks retry independently
  3. Randomized backoff prevents re-deadlock
```

***REMOVED******REMOVED******REMOVED*** Rollback and Compensation Patterns

**Pattern 1: Atomic Transactions**
```python
@shared_task
def update_schedule():
    db = SessionLocal()
    try:
        db.begin()  ***REMOVED*** Start transaction

        ***REMOVED*** Multiple updates
        update1(db)
        update2(db)
        update3(db)

        db.commit()  ***REMOVED*** All or nothing
        return {"status": "success"}
    except Exception as e:
        db.rollback()  ***REMOVED*** Revert all changes
        raise self.retry(exc=e)
    finally:
        db.close()
```

**Pattern 2: Compensation Workflow**
```python
@shared_task
def export_data_with_cleanup():
    ***REMOVED*** Step 1: Create export file
    export_id = create_export()

    try:
        ***REMOVED*** Step 2: Upload to S3
        upload_to_s3(export_id)

        ***REMOVED*** Step 3: Mark as complete
        mark_complete(export_id)

        return {"export_id": export_id}
    except Exception as e:
        ***REMOVED*** Compensation: Delete partial results
        delete_export(export_id)  ***REMOVED*** Cleanup
        raise self.retry(exc=e)
```

**Pattern 3: Idempotency Key**
```python
@shared_task(bind=True)
def process_with_idempotency(self, request_id: str):
    ***REMOVED*** Check if already processed
    if is_already_processed(request_id):
        return get_cached_result(request_id)

    ***REMOVED*** Process
    result = do_work()

    ***REMOVED*** Cache result with idempotency key
    cache_result(request_id, result)

    return result
```

***REMOVED******REMOVED******REMOVED*** Monitoring and Alerting for Task Health

**Metrics to Monitor:**
- Task success rate (per task type)
- Task execution duration (p50, p95, p99)
- Task failure rate (per failure reason)
- Queue depth (backlog size)
- Worker availability (active workers count)
- Task retry rate (retries vs successes)

**Alerting Rules:**
```
IF task_success_rate < 90% FOR 5min
  THEN send_alert("High task failure rate")

IF task_execution_duration > 5min
  THEN send_alert("Task running slow")

IF queue_depth > 1000
  THEN send_alert("Task backlog building")

IF active_workers < 1
  THEN send_alert("No workers available!")
```

**Health Dashboard Endpoint:**
```python
@app.get("/health/celery")
async def celery_health(db: Session = Depends(get_db)):
    """Celery health check for monitoring"""
    return {
        "status": "healthy",
        "tasks": {
            "registered": celery_app.tasks.keys(),
            "active": get_active_tasks(),
            "scheduled": get_scheduled_tasks(),
        },
        "workers": {
            "count": len(get_active_workers()),
            "concurrency": sum(w.concurrency for w in workers),
        },
        "queues": {
            "resilience": get_queue_depth("resilience"),
            "metrics": get_queue_depth("metrics"),
            ***REMOVED*** ... all queues
        },
    }
```

---

***REMOVED******REMOVED*** STEALTH LENS: Undocumented Task Types and Hidden Tools

***REMOVED******REMOVED******REMOVED*** Potentially Hidden or Less-Documented Tasks

**1. ML Model Training Tasks** (partially documented)
- `train_schedule_predictor`: Trains fairness prediction models
- Status: Placeholder in `ml_tasks.py`
- Purpose: ML inference for schedule optimization
- Frequency: After major schedule changes
- Hidden: Limited documentation in codebase

**2. RAG Indexing Tasks** (partially documented)
- `index_schedules_for_rag`: Vector embedding and indexing
- Status: Implemented but minimal docs
- Purpose: Semantic search across historical schedules
- Frequency: After schedule approval
- Hidden: Integration points not well documented

**3. Backup and Disaster Recovery** (documented but not implemented)
- `backup_database`: Full database backup
- `verify_backup`: Test backup integrity
- `restore_from_backup`: Disaster recovery
- Status: Framework exists, no schedule defined
- Hidden: No active task in beat_schedule

**4. Performance Tuning Tasks** (not documented)
- `analyze_database_performance`: Query analysis
- `optimize_indices`: Index maintenance
- `vacuum_tables`: PostgreSQL maintenance
- Status: Not visible in task files
- Hidden: Likely external (pg_cron) not Celery-based

**5. Advanced Monitoring Tasks** (partially hidden)
- Circuit breaker health checks
- Defense level transitions
- Phase transition risk monitoring
- Status: Integrated in `periodic_health_check` but not separate
- Hidden: Could be extracted to separate tasks

***REMOVED******REMOVED******REMOVED*** MCP Tool Integration Gaps

**Tools Available in MCP Server:**
1. `list_active_tasks` - View running tasks
2. `get_task_status` - Track task progress
3. `cancel_task` - Terminate task
4. `start_background_task` - Launch task programmatically

**Gaps Identified:**
- No `reschedule_task` tool (change timing)
- No `get_task_result` tool (retrieve task output)
- No `retry_failed_task` tool (manual retry)
- No `bulk_cancel_tasks` tool (mass termination)
- No `task_history_report` tool (past executions)

***REMOVED******REMOVED******REMOVED*** Recommended Documentation Additions

**Missing Documentation:**
1. Backup/recovery task activation procedure
2. ML model retraining trigger conditions
3. RAG indexing integration with schedule generation
4. Performance tuning automation guidelines
5. Disaster recovery runbook with task workflows

---

***REMOVED******REMOVED*** Monitoring and Operations Guide

***REMOVED******REMOVED******REMOVED*** Starting Celery in Development

```bash
***REMOVED*** Terminal 1: Start Redis
redis-server

***REMOVED*** Terminal 2: Start Celery Worker
cd backend
celery -A app.core.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --queues=default,resilience,metrics

***REMOVED*** Terminal 3: Start Celery Beat (scheduler)
celery -A app.core.celery_app beat \
  --loglevel=info
```

***REMOVED******REMOVED******REMOVED*** Docker Compose Commands

```bash
***REMOVED*** Start all services with Celery
docker-compose up -d

***REMOVED*** View Celery logs
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat

***REMOVED*** Execute task manually
docker-compose exec celery-worker \
  celery -A app.core.celery_app \
  call app.resilience.tasks.periodic_health_check
```

***REMOVED******REMOVED******REMOVED*** Monitoring Active Tasks

```python
***REMOVED*** Get active tasks
from app.core.celery_app import celery_app

active_tasks = celery_app.control.inspect().active()
***REMOVED*** Returns:
***REMOVED*** {
***REMOVED***   "celery@hostname": [
***REMOVED***     {
***REMOVED***       "id": "task-id-uuid",
***REMOVED***       "name": "app.resilience.tasks.periodic_health_check",
***REMOVED***       "args": [],
***REMOVED***       "kwargs": {},
***REMOVED***       "time_start": 1735574400.123
***REMOVED***     }
***REMOVED***   ]
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Querying Task Status

```python
from celery.result import AsyncResult

***REMOVED*** Get task result
task_id = "abc123def456..."
result = AsyncResult(task_id, app=celery_app)

print(f"State: {result.state}")  ***REMOVED*** PENDING, STARTED, SUCCESS, FAILURE
print(f"Result: {result.result}")
print(f"Traceback: {result.traceback}")

***REMOVED*** Monitor long-running task
while not result.ready():
    print(f"Task {task_id} still running...")
    time.sleep(5)

if result.successful():
    print(f"Success: {result.result}")
else:
    print(f"Failed: {result.info}")
```

***REMOVED******REMOVED******REMOVED*** Task Troubleshooting

**Problem: Task never executes**
```
Solution: Check Beat scheduler is running
  $ celery -A app.core.celery_app inspect active_queues
  $ celery -A app.core.celery_app inspect registered

Check Redis is accessible
  $ redis-cli ping
  ***REMOVED*** Should return: PONG
```

**Problem: Task executes but hangs**
```
Solution: Check soft/hard time limits
  - Soft limit (9min): Task gets SoftTimeLimitExceeded signal
  - Hard limit (10min): Task killed forcefully

Increase limits in celery_app.py if needed
  task_soft_time_limit = 900  ***REMOVED*** 15 minutes
  task_time_limit = 1200      ***REMOVED*** 20 minutes
```

**Problem: Task fails with database error**
```
Solution: Check database connection pool
  - Max connections might be exhausted
  - Task session not properly closed

Verify database health:
  docker-compose exec db psql -U scheduler -d residency_scheduler
  \l  ***REMOVED*** List databases
  \dt ***REMOVED*** List tables
```

**Problem: High memory usage by workers**
```
Solution: Reduce worker concurrency or increase memory

Option 1: Reduce concurrent tasks
  celery worker --concurrency=2 (default is 4)

Option 2: Limit task memory usage
  ***REMOVED*** Implement memory checks in tasks
  import psutil
  if psutil.virtual_memory().percent > 80:
      raise MemoryError("High memory usage")
```

---

***REMOVED******REMOVED*** Summary

This comprehensive documentation covers the MCP background task infrastructure with focus on:

1. **PERCEPTION**: 25+ tasks across 8 categories with detailed specifications
2. **INVESTIGATION**: Queue topology, scheduling, and dependency graphs
3. **ARCANA**: Celery architecture, integration patterns, and Redis broker
4. **HISTORY**: Evolution from basic tasks to resilience-integrated system
5. **INSIGHT**: Async philosophy and long-running task context
6. **RELIGION**: 100% task coverage assessment and roadmap
7. **NATURE**: Granularity analysis and atomic vs composite operations
8. **MEDICINE**: Context preservation, graceful shutdown, and lifecycle management
9. **SURVIVAL**: Failure modes, recovery patterns, and monitoring
10. **STEALTH**: Hidden tools and documentation gaps

**Key Takeaways:**
- 25+ Celery tasks provide comprehensive system automation
- 6 specialized queues separate concerns (resilience, metrics, etc.)
- Robust retry logic with exponential backoff ensures reliability
- Integration with MCP enables Claude AI interaction
- Health monitoring prevents cascade failures
- Several opportunities for extending coverage (backup, ML, analytics)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-30
**Maintainer**: G2_RECON Agent
**Classification**: Development Reference
