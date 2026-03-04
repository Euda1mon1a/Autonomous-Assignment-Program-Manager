# Schedule Generation Playbook

**Purpose:** Step-by-step operational guide for generating, validating, and deploying medical residency schedules.

**Target Audience:** Program Coordinators, Scheduling Administrators, Academic Leaders

**Last Updated:** 2025-12-31

---

## Table of Contents

1. [Pre-Generation Checklist](#pre-generation-checklist)
2. [Constraint Configuration](#constraint-configuration)
3. [Generation Execution](#generation-execution)
4. [Validation and Review](#validation-and-review)
5. [Publication Workflow](#publication-workflow)
6. [Rollback Procedures](#rollback-procedures)
7. [Failure Recovery](#failure-recovery)
8. [Post-Generation Verification](#post-generation-verification)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Templates and Checklists](#templates-and-checklists)

---

## Pre-Generation Checklist

**Timeline:** Complete this checklist 2-3 weeks before generation

### Step 1: Data Validation

**Objective:** Ensure all input data is accurate and complete.

#### 1.1 Personnel Data

```bash
# Command: Verify personnel in system
curl -X GET http://localhost:8000/api/admin/personnel/validation \
  -H "Authorization: Bearer $TOKEN"

# Expected Response:
# {
#   "total_residents": 24,
#   "total_faculty": 12,
#   "validation_status": "passed",
#   "issues": []
# }
```

**Checklist:**
- [ ] All residents imported (PGY1, PGY2, PGY3)
- [ ] All faculty loaded with current credentials
- [ ] No missing critical fields (name, role, start_date)
- [ ] Contact information verified
- [ ] No duplicate records

#### 1.2 Credentials and Certifications

```bash
# Command: Validate credentials
curl -X GET http://localhost:8000/api/admin/credentials/expiring \
  -H "Authorization: Bearer $TOKEN"

# Returns: Credentials expiring in next 90 days
```

**Checklist:**
- [ ] All required certifications current (BLS, ACLS, PALS)
- [ ] Training certificates up-to-date
- [ ] No pending credential expirations during schedule period
- [ ] Faculty privileges verified
- [ ] Procedure qualifications current

#### 1.3 Rotation Templates

```bash
# Command: List all rotation templates
curl -X GET http://localhost:8000/api/admin/rotations/templates \
  -H "Authorization: Bearer $TOKEN"

# Response includes: rotation_id, name, hours_per_day, type, required_credentials
```

**Checklist:**
- [ ] All rotations defined for academic year
- [ ] Rotation capacities reasonable
- [ ] Clinical requirements documented
- [ ] Coverage needs specified per rotation
- [ ] Blackout dates configured

#### 1.4 ACGME Constraints

```bash
# Command: Validate ACGME rules engine
curl -X POST http://localhost:8000/api/admin/validate/acgme-constraints \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"check_all": true}'

# Expected Response: All constraints validated successfully
```

**Checklist:**
- [ ] 80-hour rule configured correctly
- [ ] 1-in-7 rule parameters set
- [ ] Supervision ratios match program
- [ ] Max consecutive shift limits configured
- [ ] Minimum rest period between shifts defined

### Step 2: Historical Data Cleanup

```bash
# Command: Archive previous schedules
curl -X POST http://localhost:8000/api/admin/schedules/archive \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fiscal_year": 2025,
    "action": "archive"
  }'
```

**Checklist:**
- [ ] Previous schedules exported for audit trail
- [ ] Old assignments archived
- [ ] Database cleaned of test data
- [ ] Backup created before cleanup

### Step 3: System Health Check

```bash
# Command: Full system health verification
curl -X GET http://localhost:8000/api/health/full \
  -H "Authorization: Bearer $TOKEN"

# Response includes:
# - Database connectivity
# - Redis cache status
# - Celery worker health
# - API response times
```

**Checklist:**
- [ ] Database responding normally
- [ ] Redis cache operational
- [ ] Celery workers online
- [ ] API response times acceptable (< 500ms)
- [ ] No outstanding alerts or warnings

### Pre-Generation Approval

Once all checks pass:

```bash
# Document approval
cat > pre_generation_approval.txt << 'EOF'
DATE: $(date)
APPROVER: [Program Director Name]
ROLE: [Position]

Personnel: VERIFIED ✓
Credentials: VERIFIED ✓
Rotations: VERIFIED ✓
ACGME Rules: VERIFIED ✓
System Health: VERIFIED ✓

APPROVED FOR GENERATION: YES
EOF
```

---

## Constraint Configuration

**Timeline:** Complete this 1-2 weeks before generation

### Step 1: Load Constraint Profile

```bash
# List available constraint profiles
curl -X GET http://localhost:8000/api/admin/constraints/profiles \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "profiles": [
#     {
#       "id": "profile_001",
#       "name": "Standard Program",
#       "created": "2025-06-01",
#       "constraints": [...]
#     }
#   ]
# }
```

### Step 2: Configure Hard Constraints

These MUST be satisfied:

```bash
# POST: Apply hard constraints
curl -X POST http://localhost:8000/api/admin/constraints/apply \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "constraint_type": "hard",
    "rules": [
      {
        "id": "80_hour_rule",
        "name": "80-Hour Weekly Maximum",
        "enabled": true,
        "parameters": {
          "max_hours_per_week": 80,
          "averaging_weeks": 4
        }
      },
      {
        "id": "one_in_seven",
        "name": "One-in-Seven Rest",
        "enabled": true,
        "parameters": {
          "min_days_off": 1,
          "cycle_length_days": 7
        }
      },
      {
        "id": "supervision_ratio",
        "name": "Faculty Supervision",
        "enabled": true,
        "parameters": {
          "pgy1_ratio": "1:2",
          "pgy2_ratio": "1:4",
          "pgy3_ratio": "1:4"
        }
      }
    ]
  }'
```

### Step 3: Configure Soft Constraints

These are optimized but can be relaxed:

```bash
# POST: Apply soft constraints with priorities
curl -X POST http://localhost:8000/api/admin/constraints/soft \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "soft_constraints": [
      {
        "name": "Even Distribution",
        "priority": 1,
        "weight": 10,
        "description": "Distribute shifts evenly across residents"
      },
      {
        "name": "Resident Preference",
        "priority": 2,
        "weight": 5,
        "description": "Accommodate resident scheduling preferences"
      },
      {
        "name": "Call Frequency",
        "priority": 3,
        "weight": 3,
        "description": "Minimize consecutive call assignments"
      },
      {
        "name": "Rotation Balance",
        "priority": 4,
        "weight": 2,
        "description": "Balance rotation assignments across year"
      }
    ]
  }'
```

### Step 4: Configure Resident Preferences

```bash
# POST: Load preference data
curl -X POST http://localhost:8000/api/admin/preferences/load \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "preferences_file": "resident_preferences_2026.csv",
    "format": "csv",
    "override_existing": false
  }'
```

**Expected CSV Format:**
```
resident_id,rotation_preference,date_range,priority
PGY1-001,Inpatient,2026-01-15:2026-02-15,high
PGY2-003,Clinic,2026-03-01:2026-03-31,medium
PGY3-002,Procedures,2026-04-15:2026-05-15,low
```

### Step 5: Review and Approve Configuration

```bash
# GET: Retrieve current constraint configuration
curl -X GET http://localhost:8000/api/admin/constraints/current \
  -H "Authorization: Bearer $TOKEN"

# Document approval
cat > constraint_approval.txt << 'EOF'
CONSTRAINT CONFIGURATION APPROVAL

Generated: $(date)

HARD CONSTRAINTS:
- 80-Hour Rule: YES
- One-in-Seven: YES
- Supervision Ratios: YES

SOFT CONSTRAINTS:
- Even Distribution (Priority 1)
- Resident Preferences (Priority 2)
- Call Frequency (Priority 3)
- Rotation Balance (Priority 4)

APPROVED BY: [Director Name]
SIGNATURE: [Digital Approval]
EOF
```

---

## Generation Execution

**Timeline:** Main generation (2-4 hours typical)

### Step 1: Pre-Generation Backup

```bash
# MANDATORY: Create database backup before generation
docker-compose exec db pg_dump -U scheduler residency_scheduler > \
  backups/schedule_generation_$(date +%Y%m%d_%H%M%S).sql

# Verify backup integrity
ls -lh backups/schedule_generation_*.sql
```

**Verification:**
- [ ] Backup file created
- [ ] File size reasonable (> 1MB)
- [ ] File timestamp correct

### Step 2: Start Generation Job

```bash
# POST: Initiate schedule generation
curl -X POST http://localhost:8000/api/scheduler/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fiscal_year": 2026,
    "blocks_to_schedule": 730,
    "mode": "production",
    "solver": {
      "algorithm": "constraint_programming",
      "timeout_minutes": 120,
      "parallel_workers": 4
    },
    "options": {
      "generate_alternatives": true,
      "num_alternatives": 3,
      "validate_immediately": true
    }
  }'

# Expected Response:
# {
#   "job_id": "gen_20251231_150000",
#   "status": "started",
#   "estimated_completion": "2025-12-31T17:00:00Z"
# }
```

### Step 3: Monitor Generation Progress

```bash
# GET: Poll generation status
curl -X GET http://localhost:8000/api/scheduler/generate/gen_20251231_150000/status \
  -H "Authorization: Bearer $TOKEN"

# Response includes:
# - Current block: 245/730
# - Constraint violations: 0
# - Time elapsed: 45 minutes
# - Estimated remaining: 35 minutes
# - Current allocation rate: 16.2 blocks/minute
```

**Monitoring Dashboard (Optional):**

```bash
# Watch progress in real-time
watch -n 5 'curl -s http://localhost:8000/api/scheduler/generate/gen_20251231_150000/status \
  -H "Authorization: Bearer $TOKEN" | jq "."'
```

### Step 4: Handle Generation Timeout

If generation approaches timeout (default 120 minutes):

```bash
# Check if solver still making progress
curl -X GET http://localhost:8000/api/scheduler/generate/gen_20251231_150000/solver_status \
  -H "Authorization: Bearer $TOKEN"

# If making good progress, extend timeout
curl -X PATCH http://localhost:8000/api/scheduler/generate/gen_20251231_150000/settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"timeout_minutes": 180}'

# If stalled, consider canceling
curl -X POST http://localhost:8000/api/scheduler/generate/gen_20251231_150000/cancel \
  -H "Authorization: Bearer $TOKEN"
```

### Step 5: Generation Complete

```bash
# GET: Retrieve generation results
curl -X GET http://localhost:8000/api/scheduler/generate/gen_20251231_150000/results \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "status": "completed",
#   "blocks_scheduled": 730,
#   "assignments_created": 17520,
#   "violations": 0,
#   "generation_time_minutes": 87,
#   "schedule_quality_score": 0.94
# }
```

---

## Validation and Review

**Timeline:** Review period (3-5 days typical)

### Step 1: Automated Compliance Check

```bash
# POST: Comprehensive validation
curl -X POST http://localhost:8000/api/scheduler/validate/comprehensive \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": "sched_20251231_001",
    "validation_checks": [
      "acgme_compliance",
      "coverage_adequacy",
      "fairness_balance",
      "credential_requirements"
    ]
  }'

# Response includes detailed validation report
```

### Step 2: ACGME Rule Verification

```bash
# Generate ACGME compliance report
curl -X GET http://localhost:8000/api/scheduler/reports/acgme-compliance \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "schedule_id": "sched_20251231_001"
  }'

# Verify:
# - 80-hour rule: All residents within limit
# - 1-in-7 rule: All residents have adequate rest
# - Supervision ratios: All met for all days
```

### Step 3: Manual Review Checklist

Create review tasks for Program Directors and Faculty:

```bash
# Email notification template
cat > schedule_review_notice.txt << 'EOF'
SCHEDULE GENERATION COMPLETE - REVIEW REQUIRED

Schedule ID: sched_20251231_001
Generation Date: 2025-12-31
Fiscal Year: 2026

REVIEW WINDOW: 2025-12-31 to 2026-01-07

Please review your assignments and note any issues:

1. Check your block assignments for:
   - [ ] Preference conflicts
   - [ ] Personal conflicts/leave dates
   - [ ] Credential limitations
   - [ ] Geographic conflicts

2. Report issues by replying to this email with:
   - [ ] Specific dates/rotations affected
   - [ ] Nature of conflict
   - [ ] Severity (critical/moderate/minor)

3. Access schedule at: https://scheduler.app/schedule/review

Questions? Contact: [Scheduler Admin]
EOF
```

### Step 4: Address Review Feedback

```bash
# Categorize feedback received
cat > review_feedback_log.csv << 'EOF'
reporter,date,block_date,issue_type,severity,notes,resolved
PGY1-001,2025-12-31,2026-01-15,personal_conflict,critical,Wedding day scheduled,pending_swap
FAC-002,2026-01-02,2026-02-01,credential,moderate,Needs procedures training,defer_assignment
EOF

# For each critical issue:
# 1. Generate swap options
# 2. Validate alternatives
# 3. Present to requester for approval
# 4. Document decision
```

### Step 5: Approval Sign-Off

```bash
# Collect formal approvals
cat > schedule_approval.txt << 'EOF'
SCHEDULE APPROVAL SIGN-OFF

Schedule ID: sched_20251231_001
Fiscal Year: 2026
Generation Date: 2025-12-31

APPROVALS:

Program Director: _________________ Date: _______
  Reviewed assignments and ACGME compliance

Faculty Leadership: _________________ Date: _______
  Verified call distribution and fairness

Graduate Medical Education: _________________ Date: _______
  Confirmed institutional compliance

Scheduler Administrator: _________________ Date: _______
  Confirmed system status and backup integrity
EOF
```

---

## Publication Workflow

**Timeline:** 1-2 days (after all approvals)

### Step 1: Pre-Publication Preparation

```bash
# Prepare communication materials
cat > publication_checklist.txt << 'EOF'
PRE-PUBLICATION CHECKLIST

Communication:
- [ ] Draft notification email to residents
- [ ] Draft notification email to faculty
- [ ] Post announcement to portal
- [ ] Schedule orientation/Q&A session

System Preparation:
- [ ] Final database backup
- [ ] Final system health check
- [ ] Disable schedule editing mode
- [ ] Enable read-only view for all users

Support Preparation:
- [ ] Notify support staff of schedule release
- [ ] Prepare FAQ document
- [ ] Set up support ticket queue
- [ ] Schedule follow-up support hours
EOF
```

### Step 2: Final System Verification

```bash
# CRITICAL: Final verification before publication
curl -X GET http://localhost:8000/api/scheduler/pre-publication-check \
  -H "Authorization: Bearer $TOKEN"

# Expected results: All GREEN
# - Database integrity: GREEN
# - Backup status: GREEN (backup within last 1 hour)
# - All constraints satisfied: GREEN
# - System capacity: GREEN
# - All required approvals: GREEN
```

### Step 3: Publish Schedule

```bash
# POST: Make schedule visible to residents and faculty
curl -X POST http://localhost:8000/api/scheduler/publish \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": "sched_20251231_001",
    "visibility": "all",
    "effective_date": "2026-01-01",
    "allow_swaps_after_days": 30
  }'

# Response:
# {
#   "status": "published",
#   "published_at": "2025-12-31T18:00:00Z",
#   "residents_notified": 24,
#   "faculty_notified": 12
# }
```

### Step 4: Publish Notifications

```bash
# Send publication notifications
curl -X POST http://localhost:8000/api/notifications/send-bulk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "schedule_published",
    "recipients": "all",
    "message_template": "schedule_published_2026",
    "schedule_id": "sched_20251231_001"
  }'

# Log notification results
curl -X GET http://localhost:8000/api/notifications/status/schedule_published \
  -H "Authorization: Bearer $TOKEN"
```

### Step 5: Post-Publication Monitoring

```bash
# Monitor first 24 hours for issues
watch -n 60 'curl -s http://localhost:8000/api/health/extended \
  -H "Authorization: Bearer $TOKEN" | jq ".system_load, .error_rate"'

# Check for unexpected errors or high support ticket volume
curl -X GET http://localhost:8000/api/admin/support-tickets?hours=24 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Rollback Procedures

**Timeline:** Immediate (if needed)

### Decision Tree: Should We Rollback?

```
Critical Issue Found?
├─ YES: Block of residents unscheduled
│   ├─ ROLLBACK: Restore backup and regenerate
├─ YES: Widespread ACGME violations
│   ├─ ROLLBACK: Restore backup and regenerate
├─ YES: System-level errors affecting all users
│   ├─ ROLLBACK: Restore backup immediately
├─ NO: Minor preference conflicts (< 5% of residents)
│   ├─ PROCEED: Collect feedback, plan improvements
├─ NO: Isolated ACGME violations (1-2 residents)
│   ├─ PROCEED: Execute immediate swaps to resolve
```

### Step 1: Immediate Rollback

```bash
# STEP 1: Halt current schedule
curl -X POST http://localhost:8000/api/scheduler/publish/retract \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": "sched_20251231_001",
    "reason": "critical_issue_detected"
  }'

# STEP 2: Stop all ongoing operations
docker-compose exec backend python -c \
  "from app.services.scheduler import SchedulerService; \
   SchedulerService.abort_all_jobs()"

# STEP 3: Verify no new assignments being made
sleep 30  # Wait for operations to drain
curl -X GET http://localhost:8000/api/scheduler/job-queue \
  -H "Authorization: Bearer $TOKEN" | jq ".active_jobs"
```

### Step 2: Database Rollback

```bash
# STEP 1: Identify correct backup
ls -lt backups/schedule_generation_*.sql | head -5

# STEP 2: Restore from backup
BACKUP_FILE="backups/schedule_generation_20251231_150000.sql"

# Stop backend to release DB connections
docker-compose down backend

# Restore database
docker-compose exec db pg_restore -U scheduler \
  residency_scheduler < "$BACKUP_FILE"

# Restart backend
docker-compose up -d backend

# STEP 3: Verify restoration
curl -X GET http://localhost:8000/api/health \
  -H "Authorization: Bearer $TOKEN"
```

### Step 3: Communication

```bash
# Notify all stakeholders of rollback
cat > rollback_notification.txt << 'EOF'
SCHEDULE GENERATION ROLLBACK NOTIFICATION

Date/Time: $(date)

STATUS: Schedule generation has been rolled back to pre-publication state

REASON: [Brief description of issue]

ACTION TAKEN:
- Schedule retracted from all users
- Database restored to pre-generation state
- System verified operational

NEXT STEPS:
- Investigation ongoing
- Will communicate restart timeline by [time]
- Residents/Faculty should disregard all schedule communications

Questions: Contact [Admin]
EOF

# Send to all stakeholders
curl -X POST http://localhost:8000/api/notifications/send-bulk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "critical_alert",
    "recipients": "all_stakeholders",
    "subject": "SCHEDULE GENERATION ROLLBACK",
    "message": "$(cat rollback_notification.txt)"
  }'
```

### Step 4: Post-Rollback Analysis

```bash
# Gather diagnostic data
cat > rollback_analysis.md << 'EOF'
# Schedule Generation Rollback Analysis

## Issue Description
[Detailed description of what went wrong]

## Timeline
- Generation started: [time]
- Issue detected: [time]
- Rollback initiated: [time]
- Rollback completed: [time]

## Root Cause
[Analysis of root cause]

## Data Collected
[List of logs, metrics, and data reviewed]

## Corrective Actions
1. [Action item 1]
2. [Action item 2]
3. [Action item 3]

## Verification Before Retry
- [ ] Issue resolved
- [ ] System validated
- [ ] Constraints reviewed
- [ ] Full backup created
EOF
```

---

## Failure Recovery

**Timeline:** 4-24 hours (depending on issue severity)

### Common Failure Scenarios

#### Scenario 1: Solver Timeout (Generation Not Completing)

**Symptoms:**
- Generation job running > expected time
- Solver stuck on specific blocks
- Progress bar not moving

**Recovery Steps:**

```bash
# Step 1: Check solver status
curl -X GET http://localhost:8000/api/scheduler/generate/gen_20251231_150000/solver-diagnostics \
  -H "Authorization: Bearer $TOKEN"

# Step 2: Check for constraint conflicts
curl -X POST http://localhost:8000/api/scheduler/validate/constraints \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"check_feasibility": true}'

# Step 3: Identify problematic constraints
# Look for: conflicting hard constraints, unrealistic parameters

# Step 4: Relax soft constraints temporarily
curl -X PATCH http://localhost:8000/api/admin/constraints/soft \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "constraint": "rotation_balance",
    "action": "disable_temporarily",
    "duration_hours": 24
  }'

# Step 5: Retry generation
curl -X POST http://localhost:8000/api/scheduler/generate/retry \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "gen_20251231_150000",
    "continue_from_block": 245
  }'
```

#### Scenario 2: Database Connection Lost

**Symptoms:**
- Database connection errors in logs
- Assignments not being saved
- System becomes read-only

**Recovery Steps:**

```bash
# Step 1: Check database status
docker-compose logs db | tail -50

# Step 2: Verify database is running
docker-compose ps db

# Step 3: If database crashed, restart it
docker-compose restart db

# Step 4: Run database integrity check
docker-compose exec db psql -U scheduler residency_scheduler \
  -c "ANALYZE;"

# Step 5: Resume generation from last checkpoint
curl -X POST http://localhost:8000/api/scheduler/generate/resume \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "gen_20251231_150000",
    "continue_from": "last_checkpoint"
  }'
```

#### Scenario 3: ACGME Violations Found

**Symptoms:**
- Validation reports constraint violations
- Residents assigned beyond work hour limits
- Inadequate rest periods detected

**Recovery Steps:**

```bash
# Step 1: Generate detailed violation report
curl -X GET http://localhost:8000/api/scheduler/reports/violations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": "sched_20251231_001",
    "group_by": "resident"
  }'

# Step 2: Analyze patterns
# Check if violations are systematic or isolated

# Step 3: If systematic (all residents affected):
# Adjust solver parameters and regenerate
curl -X POST http://localhost:8000/api/scheduler/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "fiscal_year": 2026,
    "solver": {
      "algorithm": "constraint_programming",
      "timeout_minutes": 180,  # Increased timeout
      "parallel_workers": 2,   # Reduced for stability
      "constraint_weighting": {
        "80_hour_rule": 1000,  # Highest priority
        "one_in_seven": 500,
        "coverage": 100
      }
    }
  }'

# Step 4: If isolated (1-3 residents affected):
# Use swap executor to resolve
curl -X POST http://localhost:8000/api/scheduler/resolve-violations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": "sched_20251231_001",
    "violations": [
      {
        "resident_id": "PGY1-005",
        "violation_type": "80_hour_rule",
        "week": "2026-01-15",
        "hours": 92
      }
    ],
    "resolution_strategy": "auto_swap"
  }'
```

---

## Post-Generation Verification

**Timeline:** Immediately after publication

### Step 1: System Health Check

```bash
# POST: Full system verification
curl -X POST http://localhost:8000/api/scheduler/post-publication-check \
  -H "Authorization: Bearer $TOKEN"

# Should show all GREEN
```

### Step 2: Spot Check Assignments

```bash
# Sample check: Random residents
curl -X GET http://localhost:8000/api/scheduler/assignments/sample \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sample_size": 10,
    "include_audit": true
  }'

# Verify:
# - All slots assigned
# - No double-bookings
# - Credentials match assignments
# - Rotation types valid
```

### Step 3: Coverage Verification

```bash
# GET: Verify all blocks have adequate coverage
curl -X GET http://localhost:8000/api/scheduler/coverage/analysis \
  -H "Authorization: Bearer $TOKEN"

# Expected: No blocks with zero coverage
```

### Step 4: Performance Baseline

```bash
# Record system performance metrics
cat > post_generation_metrics.json << 'EOF'
{
  "timestamp": "$(date -Iseconds)",
  "schedule_id": "sched_20251231_001",
  "metrics": {
    "total_assignments": $(curl -s http://localhost:8000/api/scheduler/metrics/assignments_count -H "Authorization: Bearer $TOKEN" | jq .count),
    "api_response_time_ms": $(curl -s http://localhost:8000/api/health -H "Authorization: Bearer $TOKEN" | jq .response_time_ms),
    "database_query_time_ms": $(curl -s http://localhost:8000/api/health/db -H "Authorization: Bearer $TOKEN" | jq .query_time_ms),
    "active_users": $(curl -s http://localhost:8000/api/admin/active-users -H "Authorization: Bearer $TOKEN" | jq .count)
  }
}
EOF
```

---

## Troubleshooting Guide

### Issue: "Constraint Satisfaction Failed"

**Cause:** Hard constraints cannot be simultaneously satisfied

**Diagnosis:**
```bash
curl -X POST http://localhost:8000/api/scheduler/diagnose/constraints \
  -H "Authorization: Bearer $TOKEN"
```

**Solution:**
1. Review constraint parameters (too strict?)
2. Check for conflicting constraints
3. Verify data quality (missing residents, rotations, etc.)
4. Relax lower-priority soft constraints
5. Increase solver timeout

### Issue: "Insufficient Coverage for Rotation"

**Cause:** Not enough qualified residents for rotation assignment

**Diagnosis:**
```bash
curl -X GET http://localhost:8000/api/scheduler/coverage/gaps \
  -H "Authorization: Bearer $TOKEN"
```

**Solution:**
1. Verify all required residents have credentials
2. Check rotation capacity is realistic
3. Temporarily disable credential requirements for some rotations
4. Add more faculty to rotation
5. Split rotation into smaller blocks

### Issue: "Memory Exceeded During Generation"

**Cause:** Solver consuming too much system memory

**Diagnosis:**
```bash
docker stats backend
```

**Solution:**
1. Reduce parallel workers (increase solver timeout)
2. Increase Docker container memory limit
3. Close unnecessary processes
4. Reduce number of blocks to schedule per iteration

### Issue: "Database Locking - Cannot Save Assignments"

**Cause:** Another process holding database locks

**Diagnosis:**
```bash
docker-compose exec db psql -U scheduler residency_scheduler \
  -c "SELECT * FROM pg_locks JOIN pg_stat_activity ON pg_locks.pid = pg_stat_activity.pid;"
```

**Solution:**
1. Identify blocking query
2. Terminate if safe: `SELECT pg_terminate_backend(pid);`
3. Restart database if necessary
4. Retry generation

### Issue: "API Timeout Errors"

**Cause:** API taking too long to respond under load

**Diagnosis:**
```bash
curl -w "Response time: %{time_total}s\n" \
  http://localhost:8000/api/scheduler/status
```

**Solution:**
1. Check backend logs for errors
2. Verify database performance
3. Check system CPU/memory usage
4. Restart backend if necessary
5. Scale API instances if in production

---

## Templates and Checklists

### Schedule Generation Approval Checklist

```
SCHEDULE GENERATION APPROVAL CHECKLIST

Schedule ID: _________________
Fiscal Year: _________________
Date Prepared: ________________

PRE-GENERATION:
☐ Personnel data validated
☐ All credentials current
☐ Rotation templates complete
☐ ACGME constraints configured
☐ System health verified
☐ Backup created

GENERATION:
☐ Generation job completed
☐ All blocks scheduled
☐ Zero hard constraint violations
☐ Solver quality score > 0.9
☐ Results reviewed by technical team

VALIDATION:
☐ ACGME compliance verified
☐ Coverage adequacy confirmed
☐ Fairness metrics acceptable
☐ Credential requirements satisfied

REVIEW:
☐ Program director reviewed
☐ Faculty leadership reviewed
☐ Graduate medical education reviewed
☐ Scheduler admin verified

APPROVAL:
☐ All issues addressed
☐ Final backup created
☐ Ready for publication

Approved By: _________________________ Date: ________
```

### Issue Tracking Template

```
SCHEDULE GENERATION ISSUE REPORT

Date Reported: _______________
Reported By: _______________

ISSUE DESCRIPTION:
[Describe the problem]

AFFECTED PARTIES:
- Residents: [List or numbers]
- Faculty: [List or numbers]
- Rotations: [List affected rotations]

SEVERITY:
☐ Critical (blocks schedule publication)
☐ High (affects multiple residents)
☐ Medium (affects 1-3 residents)
☐ Low (preference/minor conflict)

RESOLUTION:
☐ Scheduled swap
☐ Assignment modification
☐ Acknowledged as permanent conflict
☐ Other: [Describe]

RESOLVED BY: _______________
APPROVAL DATE: _______________
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
**Owner:** Scheduling Administration
**Review Cycle:** Annual or as needed
