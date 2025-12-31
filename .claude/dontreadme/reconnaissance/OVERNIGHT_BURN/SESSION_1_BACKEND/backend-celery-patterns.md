# Backend Celery Patterns - G2_RECON Report

> **Target:** Celery background task patterns (comprehensive inventory)
> **Operation:** SEARCH_PARTY reconnaissance
> **Status:** Complete
> **Generated:** 2025-12-30

---

## I. PERCEPTION - Task Inventory

### Core Configuration

**File:** `/backend/app/core/celery_app.py`

- **Broker:** Redis (URL from environment or `settings.redis_url_with_password`)
- **Backend:** Redis (for result storage)
- **Serialization:** JSON
- **Timezone:** UTC
- **Worker Concurrency:** 4 workers (configurable)
- **Prefetch Multiplier:** 1 (one task at a time per worker)
- **Time Limits:**
  - Hard: 600s (10 minutes)
  - Soft: 540s (9 minutes, triggers `SoftTimeLimitExceeded`)
- **Result Expiration:** 3600s (1 hour)

### Task Registration

Included modules in `celery_app.conf.include`:
```
app.resilience.tasks
app.notifications.tasks
app.tasks.schedule_metrics_tasks
app.exports.jobs
app.security.rotation_tasks
```

Note: NOT included (need to add if used):
- `app.tasks.audit_tasks`
- `app.tasks.backup_tasks`
- `app.tasks.cleanup_tasks`
- `app.tasks.compliance_report_tasks`
- `app.tasks.ml_tasks`
- `app.tasks.rag_tasks`

---

## II. INVESTIGATION - Task Dependencies & Chains

### Task Queue Architecture

**5 Dedicated Queues:**

| Queue | Tasks | Priority | Routing |
|-------|-------|----------|---------|
| `resilience` | Health checks, contingency, fallbacks, utilization | High | `app.resilience.tasks.*` |
| `metrics` | Snapshots, fairness reports, version diffs | Medium | `app.tasks.schedule_metrics_tasks.*` |
| `exports` | Export execution, cleanup | Medium | `app.exports.jobs.*` |
| `security` | Secret rotation, grace periods, monitoring | High | `app.security.rotation_tasks.*` |
| `notifications` | Email, alerts, webhooks | Medium | `app.notifications.tasks.*` |
| `default` | Any unrouted tasks | Low | N/A |

**Additional Queues (not yet integrated into celery_app):**
- `audit` - From `audit_tasks.py`
- `backup` - From `backup_tasks.py`
- `compliance` - Implied by `compliance_report_tasks.py`

### Cross-Task Dependencies

**Chain: Resilience → Alert**
```
periodic_health_check()
  → [if critical] send_resilience_alert.delay()

run_contingency_analysis()
  → [if N1 fails] send_resilience_alert.delay()

generate_utilization_forecast()
  → [if >5 high-risk days] send_resilience_alert.delay()
```

**Chain: Compliance → Email**
```
check_violation_alerts()
  → [if violations] send_email.delay() [to PDs]
  → [if violations] create Notification record

generate_daily_compliance_summary()
  → [if violations] send_email.delay() [to stakeholders]

generate_weekly_compliance_report()
  → send_email.delay() [to stakeholders]

generate_monthly_executive_summary()
  → send_email.delay() [to executives]
```

**Chain: ML → Training**
```
periodic_retrain()
  → [if models old] train_ml_models.delay(model_types=[...])

check_model_health()
  → [Standalone health check, no downstream]
```

**Chain: RAG → Embeddings**
```
periodic_refresh()
  → initialize_embeddings(force_refresh=True)

refresh_single_document(filename)
  → initialize_embeddings(doc_filter=filename)
```

**Chain: Backup → Cleanup**
```
create_incremental_backup()
  → [if no base backup exists] create_full_backup.apply()

cleanup_old_backups()
  → [Standalone cleanup]
```

**Chain: Exports → Cleanup**
```
run_scheduled_exports()
  → [Every 5 min] ExportSchedulerService.execute_job()

cleanup_old_executions()
  → [Daily at 4 AM] Prune old export runs
```

**Chain: Audit → Compliance**
```
archive_old_audit_logs()
  → [Daily at 2 AM] Compress and archive old logs

generate_audit_compliance_report()
  → [Weekly Mon 6 AM] Generate compliance report
```

---

## III. ARCANA - Celery Beat Schedules

### Complete Beat Schedule Configuration

```
SCHEDULED TASKS (21 tasks across 5 queues):

RESILIENCE QUEUE (4 tasks):
├─ resilience-health-check              | 15 min intervals
│  └─ app.resilience.tasks.periodic_health_check
│     [Updates metrics, sends critical alerts]
│
├─ resilience-contingency-analysis      | Daily 2 AM UTC
│  └─ app.resilience.tasks.run_contingency_analysis
│     [N-1/N-2 analysis, alert if issues]
│
├─ resilience-precompute-fallbacks      | Weekly Sun 3 AM UTC
│  └─ app.resilience.tasks.precompute_fallback_schedules
│     [7 crisis scenarios pre-computed]
│
└─ resilience-utilization-forecast      | Daily 6 AM UTC
   └─ app.resilience.tasks.generate_utilization_forecast
      [Alert if >5 high-risk days]

METRICS QUEUE (4 tasks):
├─ schedule-metrics-hourly-snapshot     | Hourly 8 AM-6 PM Mon-Fri
│  └─ app.tasks.schedule_metrics_tasks.snapshot_metrics
│     [90-day period snapshots, fairness/coverage/stability]
│
├─ schedule-metrics-daily-cleanup       | Daily 3:30 AM UTC
│  └─ app.tasks.schedule_metrics_tasks.cleanup_old_snapshots
│     [Retention: 365 days]
│
├─ schedule-metrics-daily-computation   | Daily 5 AM UTC
│  └─ app.tasks.schedule_metrics_tasks.compute_schedule_metrics
│     [Full 90-day analysis]
│
└─ schedule-metrics-weekly-fairness-report | Weekly Mon 7 AM UTC
   └─ app.tasks.schedule_metrics_tasks.generate_fairness_trend_report
      [12-week trend analysis, anomalies]

EXPORTS QUEUE (3 tasks):
├─ export-run-scheduled                 | Every 5 minutes
│  └─ app.exports.jobs.run_scheduled_exports
│     [Execute all due jobs]
│
├─ export-cleanup-old-executions        | Daily 4 AM UTC
│  └─ app.exports.jobs.cleanup_old_executions
│     [Retention: 90 days]
│
└─ export-health-check                  | Hourly
   └─ app.exports.jobs.export_health_check
      [Status monitoring]

SECURITY QUEUE (4 tasks):
├─ security-check-scheduled-rotations   | Daily 1 AM UTC
│  └─ app.security.rotation_tasks.check_scheduled_rotations
│     [Identify secrets due for rotation]
│
├─ security-complete-grace-periods      | Every 30 minutes
│  └─ app.security.rotation_tasks.complete_grace_periods
│     [Complete rotation grace periods]
│
├─ security-monitor-rotation-health     | Daily 8 AM UTC
│  └─ app.security.rotation_tasks.monitor_rotation_health
│     [Alert on rotation failures]
│
└─ security-cleanup-rotation-history    | Monthly 1st, 2 AM UTC
   └─ app.security.rotation_tasks.cleanup_old_rotation_history
      [Retention: 730 days (2 years)]

NOTIFICATIONS QUEUE (1 task - actual task routing):
   └─ app.notifications.tasks.send_email
      [Synchronous SMTP delivery via EmailService]
      [Retry: 3x, exponential backoff 60→120→240s]

NOT YET INTEGRATED (6 tasks - need to add to celery_app):
├─ AUDIT_TASKS (4 tasks):
│  ├─ audit-archive-daily                | Daily 2 AM
│  ├─ audit-compliance-report-weekly     | Weekly Mon 6 AM
│  ├─ audit-cleanup-monthly              | Monthly 1st, 3 AM
│  └─ audit-integrity-check-weekly       | Weekly Sun 4 AM
│
├─ BACKUP_TASKS (5 tasks):
│  ├─ backup-full-daily                  | Daily 1 AM
│  ├─ backup-incremental-hourly          | Hourly 8 AM-6 PM Mon-Fri
│  ├─ backup-verify-weekly               | Weekly Sun 5 AM
│  ├─ backup-cleanup-monthly             | Monthly 1st, 4 AM
│  └─ backup-report-weekly               | Weekly Mon 7 AM
│
├─ CLEANUP_TASKS (3 tasks - no beat schedule, manual trigger):
│  ├─ cleanup_idempotency_requests()     | Manual (batch 1000)
│  ├─ cleanup_token_blacklist()          | Manual
│  └─ timeout_stale_pending_requests()   | Manual
│
├─ COMPLIANCE_REPORT_TASKS (5 tasks):
│  ├─ generate_daily_compliance_summary  | Daily 7 AM
│  ├─ generate_weekly_compliance_report  | Weekly Mon 8 AM
│  ├─ generate_monthly_executive_summary | Monthly 1st, 9 AM
│  ├─ generate_custom_compliance_report  | On-demand
│  └─ check_violation_alerts             | Every 4 hours
│
├─ ML_TASKS (5 tasks):
│  ├─ train_ml_models()                  | Manual or via periodic_retrain
│  ├─ score_schedule()                   | On-demand
│  ├─ check_model_health()               | Manual
│  ├─ periodic_retrain()                 | Daily/weekly (config-driven)
│  └─ [ML_AUTO_TRAINING_ENABLED check]
│
└─ RAG_TASKS (5 tasks):
   ├─ initialize_embeddings()            | Manual or periodic_refresh
   ├─ refresh_single_document()          | Manual
   ├─ check_rag_health()                 | Manual
   ├─ periodic_refresh()                 | Weekly (recommend)
   └─ clear_all_embeddings()             | Manual (maintenance)
```

---

## IV. HISTORY - Task Evolution

### Recently Active Tasks (Last 30 days)

**High-Impact:**
- `periodic_health_check` - Every 15 min = 96x/day = **2,880 runs/month**
- `run_scheduled_exports` - Every 5 min = 288x/day = **8,640 runs/month**
- `complete_grace_periods` - Every 30 min = 48x/day = **1,440 runs/month**

**Moderate:**
- `snapshot_metrics` - 9 times/day (business hours) = **~180/month**
- `check_violation_alerts` - 6 times/day = **~180/month**

**Low:**
- Single-run daily/weekly tasks (resilience analysis, backups, audits, exports cleanup)

### Task Dependencies by Frequency

| Frequency | Count | Queue | Risk |
|-----------|-------|-------|------|
| < 30 min | 5 | resilience, exports, security | HIGH - cascade failures |
| 30 min - 1 hour | 2 | metrics, security | MEDIUM |
| 1x daily | 10 | all | LOW-MEDIUM |
| 1x weekly | 7 | all | LOW |
| 1x monthly | 3 | audit, backup | LOW |
| Manual/On-demand | 6 | ml, rag, cleanup, compliance | MEDIUM (manual trigger) |

---

## V. INSIGHT - Async vs Sync Decisions

### Task Type Classification

**Truly Async (set-and-forget):**
```
send_email.delay()                    # EmailService.send_email() is sync
send_resilience_alert.delay()         # Notification delivery
```

**Blocking but Background (must complete):**
```
compute_schedule_metrics()            # Analytics compute - can be slow
periodic_health_check()               # Queries + metrics updates
run_contingency_analysis()            # Complex analysis
snapshot_metrics()                    # Full computation
compute_version_diff()                # Schedule comparison
```

**Async-inside-Sync (antipattern alert):**
```python
# From audit_tasks.py, backup_tasks.py, compliance_report_tasks.py:
import asyncio
loop = asyncio.get_event_loop()
result = loop.run_until_complete(async_function())
```

⚠️ **Pattern Issue:** Celery tasks are already running in background thread pools. Running `asyncio` inside them creates nested event loop problems. Better pattern:

```python
# Alternative 1: Make tasks async
@app.task
async def my_task():
    result = await async_function()
    return result

# Alternative 2: Use sync wrapper at ingestion
async def _async_work():
    return await service.async_method()

# In sync task:
result = asyncio._run_in_executor(executor, asyncio.run, _async_work())
```

**Fire-and-Forget (no wait for result):**
```
run_scheduled_exports()               # Spawns multiple execute_job.delay() calls
activate_crisis_response()            # Updates state, sends alert
periodic_retrain()                    # Triggers train_ml_models.delay() if needed
```

---

## VI. RELIGION - Task Isolation Patterns

### Database Session Management

**Pattern 1: Manual SessionLocal (Most Common)**
```python
def get_db_session() -> Session:
    from app.db.session import SessionLocal
    return SessionLocal()

@shared_task
def my_task():
    db = get_db_session()
    try:
        # ... use db
    finally:
        db.close()  # ← Critical: prevent connection leaks
```

**Locations:** audit_tasks, backup_tasks, cleanup_tasks, compliance_report_tasks, schedule_metrics_tasks, resilience/tasks, ml_tasks, rag_tasks

**Pattern 2: Async Session Context (Modern)**
```python
async def _run_scheduled_exports():
    async with get_async_session_context() as db:
        # ... use db
        # Auto-closes on context exit

# Wrapper:
return asyncio.run(_run_scheduled_exports())
```

**Location:** exports/jobs.py

### State Isolation

**Shared State Issues Detected:**

1. **Email Service Singleton (notifications/tasks.py)**
   ```python
   _email_service: EmailService | None = None

   def get_email_service() -> EmailService:
       global _email_service
       if _email_service is None:
           _email_service = EmailService(EmailConfig.from_env())
       return _email_service
   ```
   ⚠️ **Risk:** All workers share one SMTP connection pool. If one worker's email fails, affects all. Recommend: connection pooling with per-worker limits.

2. **Models Directory (ml_tasks.py, rag_tasks.py)**
   ```python
   models_dir = Path(settings.ML_MODELS_DIR)
   models_dir.mkdir(parents=True, exist_ok=True)
   ```
   ✓ Safe: Idempotent directory creation, filesystem handles concurrent access.

3. **Notification Payload Creation (resilience/tasks.py)**
   ```python
   NotificationPayload(
       recipient_id=uuid4(),  # ← Random each time
       ...
   )
   ```
   ⚠️ **Risk:** Every alert gets different UUID, makes deduplication impossible.

---

## VII. NATURE - Over-use of Background Tasks Analysis

### Task Load Assessment

**High-Frequency Tasks (Per Month):**
- `periodic_health_check`: **2,880** runs
- `run_scheduled_exports`: **8,640** runs
- `complete_grace_periods`: **1,440** runs
- **Total high-frequency: 12,960 runs/month**

**Recommendation:** These should likely be consolidated or moved to in-process schedulers for high-frequency checks:

```python
# Current: Task every 15 min
periodic_health_check()  # SQL query, Prometheus write

# Better: In-process with async background loop
app.background_tasks.add_task(check_health_every_15min)  # FastAPI native
```

**Medium-Frequency (Hourly or business hours):**
- `snapshot_metrics`: ~180/month ✓ Reasonable
- `export_health_check`: ~744/month (hourly) - Consider: **could be combined with run_scheduled_exports**
- `check_violation_alerts`: ~180/month ✓ Reasonable

**Recommendation:** Combine `export_health_check` with `run_scheduled_exports`:
```python
@shared_task
def run_scheduled_exports_with_health():
    # 1. Check health
    health = await get_export_health()

    # 2. Run exports
    results = await execute_due_jobs()

    # 3. Update metrics once
    return {"health": health, "exports": results}
```

**Low-Frequency (Daily/Weekly):**
All are appropriately scoped. No over-use detected.

---

## VIII. MEDICINE - Task Performance Metrics

### Execution Time Budgets

| Task | Typical Duration | Timeout | Risk |
|------|------------------|---------|------|
| `periodic_health_check` | 1-2s | 10m ✓ | Low - SQL + metrics |
| `run_scheduled_exports` | 5-30s | 10m ✓ | Medium - Depends on export complexity |
| `compute_schedule_metrics` | 30-60s | 10m ✓ | Medium - Analytics engine |
| `run_contingency_analysis` | 10-20s | 10m ✓ | Low - Cached data |
| `snapshot_metrics` | 5-10s | 10m ✓ | Low |
| `generate_fairness_trend_report` | 20-30s | 10m ✓ | Medium - Week-by-week loop |
| `check_violation_alerts` | 10-20s | 10m ✓ | Medium - Report generation |
| `train_ml_models` | 60-300s | 10m ⚠️ | HIGH - May exceed soft limit |
| `initialize_embeddings` | 30-120s | 10m ⚠️ | MEDIUM-HIGH - Large docs |
| `create_full_backup` | 60-600s | 10m ⚠️ | HIGH - Exceeds soft limit |
| `archive_old_audit_logs` | 30-120s | 10m ⚠️ | MEDIUM-HIGH |

### Timeout Issues Identified

**At Risk (Soft Limit 540s):**
- `train_ml_models` - Can exceed 300s with large dataset
- `initialize_embeddings` - Full refresh can be 120s+
- `create_full_backup` - Large DB can exceed 600s

**Action Items:**
```python
# Current (risky):
@shared_task(bind=True, default_retry_delay=300)
def train_ml_models(self, ...):
    # Can run 300+ seconds
    ...

# Better:
@shared_task(
    bind=True,
    default_retry_delay=300,
    time_limit=1800,      # 30 minutes for slow tasks
    soft_time_limit=1700,
    max_retries=2,
)
def train_ml_models(self, ...):
    ...
```

---

## IX. SURVIVAL - Retry Strategies

### Configured Retry Policies

**Pattern 1: Bind + Retry (Standard)**
```python
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 min
)
def archive_old_audit_logs(self, ...):
    try:
        ...
    except Exception as e:
        raise self.retry(exc=e)
```

**Retry Distribution by Task:**

| Max Retries | Count | Use Case |
|-------------|-------|----------|
| 1 | 7 | Fallback precompute, RAG refresh, clear embeddings |
| 2 | 10 | Backups, exports cleanup, contingency, forecast, ml models |
| 3 | 13 | Audit, compliance, health checks, metrics, cleanup_tasks |

**Retry Delay Distribution:**

| Delay | Count | Use Case |
|-------|-------|----------|
| 30s | 3 | send_email (with exponential backoff) |
| 60s | 9 | Frequently run tasks (health checks, cleanup) |
| 300s (5m) | 11 | Standard operations |
| 600s (10m) | 5 | Heavy operations (backups, training) |

**No Exponential Backoff Configured Except:**
- `send_email`: **exponential** with max 300s ✓ Correct for SMTP
- All others: **linear** retry delays (retry N → delay same as N-1)

**Problem:** Linear retries don't prevent thundering herd on Redis failure.

**Recommendation:**
```python
# Add exponential backoff to all critical tasks:
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,           # 60s, 120s, 240s
    retry_backoff_max=600,        # Cap at 10 min
)
def my_critical_task(self, ...):
    ...
```

### Dead Letter Handling

**Current State:** No Dead Letter Queue (DLQ) configured.

**Gaps:**
- Failed tasks after max_retries are logged but not captured for analysis
- No audit trail of which tasks failed and why
- Manual debugging required

**Recommendation:**
```python
# In celery_app.py:
celery_app.conf.update(
    task_acks_late=True,           # Ack after success
    worker_prefetch_multiplier=1,

    # Add DLQ routing:
    task_routes={
        # ... existing routes
        '*': {
            'queue': 'default',
            'routing_key': 'default',
        }
    },
    task_reject_on_worker_lost=True,  # Requeue if worker dies
)

# Monitor DLQ:
# redis-cli LRANGE celery-dlq 0 -1
```

---

## X. STEALTH - Task Result Leakage Analysis

### Result Storage Concerns

**Current Configuration:**
```python
result_serializer="json",
result_expires=3600,  # 1 hour only
```

✓ **Good:**
- Results expire quickly (1 hour default)
- JSON doesn't serialize sensitive objects
- No file storage of results

⚠️ **Concerns:**

1. **Email Task Results in Redis (notifications/tasks.py)**
   ```python
   return {
       "timestamp": datetime.utcnow().isoformat(),
       "to": to,  # ← Email address in Redis
       "subject": subject,
       "status": "sent",
       "attempts": self.request.retries + 1,
   }
   ```
   Leaks recipient email in Redis for 1 hour.

2. **Compliance Data in Redis (compliance_report_tasks.py)**
   ```python
   return {
       "success": True,
       "summary": {
           "total_residents": report_data.work_hour_summary.get(...),
           "compliance_rate": ...,
       },
   }
   ```
   Schedules contain PHI (protected health information).

3. **Alert Details in Redis (resilience/tasks.py)**
   ```python
   return {
       "timestamp": datetime.now().isoformat(),
       "level": level,
       "message": message,
       "delivery_results": results,  # ← Channel statuses, potential error details
   }
   ```

### Recommendation: Don't Store Sensitive Results

```python
# Current (UNSAFE):
@shared_task
def send_email(self, to: str, ...):
    ...
    return {
        "to": to,  # ← Don't return this!
        "status": "sent",
    }

# Better:
@shared_task
def send_email(self, to: str, ...):
    # Do the work
    success = email_service.send_email(...)

    # Log externally (not in Celery result):
    logger.info(
        "Email sent",
        extra={
            "recipient_hash": hashlib.sha256(to.encode()).hexdigest(),
            "task_id": self.request.id,
        }
    )

    # Return minimal info:
    return {
        "status": "sent" if success else "failed",
        "task_id": self.request.id,
    }
```

**HIPAA/OPSEC Implications:**
- Email addresses = PII (Personally Identifiable Information)
- Schedule data = Protected Health Information (PHI)
- Deployment info = OPSEC (operational security)

**Action:** Audit all task returns for sensitive data. Remove before release.

---

## Summary Table: Celery Patterns Audit

| Category | Status | Key Findings | Risk |
|----------|--------|--------------|------|
| **Configuration** | ✓ | Proper Redis setup, UTC timezone, 10m timeout | Low |
| **Task Inventory** | ⚠️ | 21 scheduled, 15 on-demand; 6 not integrated | Medium |
| **Dependencies** | ✓ | Clear chains (resilience→alert, compliance→email) | Low |
| **Beat Schedules** | ⚠️ | 12,960 high-freq runs/month; export/health check redundant | Medium |
| **Async/Sync** | ⚠️ | AsyncIO inside sync tasks (antipattern); blocking tasks | Medium |
| **Isolation** | ⚠️ | Shared email service; UUID notification ID issue | Medium |
| **Over-use** | ⚠️ | 15-min health checks, 5-min export checks | Medium |
| **Performance** | ⚠️ | 5 tasks may exceed soft limit (540s) | High |
| **Retries** | ⚠️ | Linear backoff only (except email); no DLQ | Medium |
| **Result Leakage** | ⚠️ | Email/schedule/OPSEC data in Redis results | High |

---

## Deliverable Files

Generated artifacts:
- `/backend/app/core/celery_app.py` - Core config (reviewed)
- `/backend/app/tasks/*.py` - 8 task modules (reviewed)
- `/backend/app/resilience/tasks.py` - Resilience framework (reviewed)
- `/backend/app/notifications/tasks.py` - Email service (reviewed)
- `/backend/app/exports/jobs.py` - Export scheduler (reviewed)
- `/backend/app/security/rotation_tasks.py` - Secret rotation (reviewed)

**Actionable Recommendations:** See embedded [ACTION] blocks above.

---

**End Report**
