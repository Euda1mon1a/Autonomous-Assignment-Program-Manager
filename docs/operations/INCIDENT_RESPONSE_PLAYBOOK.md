# Incident Response Playbook

**Purpose:** Operational procedures for detecting, responding to, and resolving system incidents and scheduling crises.

**Target Audience:** On-Call Coordinators, System Administrators, Program Directors, IT Support

**Last Updated:** 2025-12-31

---

## Table of Contents

1. [Severity Classification](#severity-classification)
2. [Initial Triage](#initial-triage)
3. [Escalation Procedures](#escalation-procedures)
4. [Communication Templates](#communication-templates)
5. [Resolution Steps by Severity](#resolution-steps-by-severity)
6. [Post-Incident Review](#post-incident-review)
7. [On-Call Rotation](#on-call-rotation)
8. [Rollback Procedures](#rollback-procedures)
9. [Incident Templates](#incident-templates)
10. [Quick Reference](#quick-reference)

---

## Severity Classification

### P1 - CRITICAL (Response: Immediate - 15 min)

**Definition:** System completely unavailable or critical schedule corruption

**Symptoms:**
- System down/completely unreachable
- All users unable to access schedules
- Schedule data corrupt/missing
- Multiple ACGME violations detected across program
- Resident safety at risk

**Resolution Timeline:**
- Initial response: < 15 minutes
- Full resolution: < 4 hours
- No schedule changes during incident

**Example Incidents:**
- Database server crashed
- API completely unresponsive
- Entire schedule deleted accidentally
- System-wide data corruption

**Initial Actions:**
```bash
# 1. DECLARE INCIDENT
echo "P1 INCIDENT DECLARED at $(date)" >> /tmp/incident.log

# 2. NOTIFY ON-CALL LEADERSHIP IMMEDIATELY
# (See Communication section)

# 3. CHECK SYSTEM STATUS
docker-compose ps
docker-compose logs backend | tail -100

# 4. IF DATABASE DOWN: Attempt restart
docker-compose restart db
sleep 30
curl http://localhost:8000/health

# 5. IF API DOWN: Check for errors
docker-compose logs backend | grep -i error | tail -20

# 6. DO NOT CHANGE ANYTHING YET
# Preserve state for forensics
```

### P2 - HIGH (Response: 1 hour)

**Definition:** Significant system degradation or data integrity concerns

**Symptoms:**
- API responding but very slow (> 5 sec per request)
- Some users unable to access (> 10%)
- Scheduling logic producing incorrect assignments
- Known workaround exists

**Resolution Timeline:**
- Initial response: < 30 minutes
- Triage complete: < 1 hour
- Mitigation in place: < 4 hours

**Example Incidents:**
- Database performance degraded
- Memory leak causing slowness
- Specific API endpoint broken
- Batch job failure affecting night's schedule

**Initial Actions:**
```bash
# Check system resources
docker stats --no-stream
curl http://localhost:8000/api/health/extended | jq .

# Check database performance
docker-compose exec db psql -U scheduler -c \
  "SELECT query, mean_time, calls FROM pg_stat_statements \
   ORDER BY mean_time DESC LIMIT 10;"

# If cache issue, clear cache
docker-compose exec redis redis-cli FLUSHDB

# If slow query, check for missing indices
docker-compose exec db psql -U scheduler -c \
  "SELECT schemaname, tablename FROM pg_tables \
   WHERE schemaname != 'pg_catalog';"
```

### P3 - MEDIUM (Response: 4 hours)

**Definition:** Operational issues with workarounds available

**Symptoms:**
- Non-critical feature broken (swap system, reports)
- API endpoint returning errors intermittently
- Cosmetic issues (display problems)
- Performance slightly degraded but acceptable

**Resolution Timeline:**
- Triage: 1 hour
- Workaround provided: 2 hours
- Full fix: 24 hours

**Example Incidents:**
- Report generation failing (but manual process exists)
- Swap approval stuck (but manual approval possible)
- Dashboard slow (but data accessible via API)

### P4 - LOW (Response: Next business day)

**Definition:** Minor issues with no user impact

**Symptoms:**
- Non-critical feature unavailable
- Documentation error
- Very minor cosmetic issue
- Performance optimization needed

**Resolution Timeline:**
- Log issue for future sprint
- Fix during regular maintenance

---

## Initial Triage

### Step 1: Confirm Incident (5 minutes)

```bash
# Answer these questions in order:

# 1. Is anyone currently affected?
# Check: User reports, Slack, Support tickets
if [ no_user_reports ]; then
  echo "Not an incident - resolve as normal issue"
  exit 0
fi

# 2. How many users affected?
user_count=$(curl -s http://localhost:8000/api/admin/affected-users | jq .count)
if [ $user_count -eq 0 ]; then
  severity="P4"
elif [ $user_count -lt 5 ]; then
  severity="P3"
elif [ $user_count -lt 50 ]; then
  severity="P2"
else
  severity="P1"
fi

# 3. Is system completely down?
if ! curl -s http://localhost:8000/health > /dev/null; then
  severity="P1"
fi

# 4. Is schedule data at risk?
# Check database integrity
db_ok=$(docker-compose exec -T db psql -U scheduler residency_scheduler \
  -c "SELECT 1;" 2>/dev/null)
if [ -z "$db_ok" ]; then
  severity="P1"
fi

echo "Incident severity: $severity"
```

**Triage Worksheet:**

```
INCIDENT TRIAGE WORKSHEET

Incident ID: _________________
Reported At: _________________
Reported By: _________________

INITIAL QUESTIONS:

1. Is anyone actually affected right now?
   ☐ Yes - Proceed
   ☐ No - Close as invalid

2. How many users affected?
   Count: _______
   Departments: _________________

3. What feature/system is affected?
   ☐ Schedule viewing
   ☐ Schedule generation
   ☐ Swap processing
   ☐ API/System
   ☐ Other: _____________

4. Can affected users work around it?
   ☐ Yes - What is workaround? _____________
   ☐ No - Proceed immediately

5. Is schedule data at risk?
   ☐ Yes - ESCALATE IMMEDIATELY
   ☐ No - Continue triage

SEVERITY CLASSIFICATION:
Based on above: [P1/P2/P3/P4]

NEXT STEP:
☐ CRITICAL: Escalate immediately
☐ URGENT: Open incident ticket and notify PD
☐ STANDARD: Log and triage in issue queue
☐ ENHANCEMENT: Log for future consideration
```

### Step 2: Collect Diagnostic Data

```bash
# Gather system state immediately

mkdir -p /tmp/incident_${incident_id}
cd /tmp/incident_${incident_id}

# System status
echo "=== SYSTEM STATUS ===" > diagnostics.log
docker-compose ps >> diagnostics.log
docker stats --no-stream >> diagnostics.log

# API health
echo -e "\n=== API HEALTH ===" >> diagnostics.log
curl -s http://localhost:8000/api/health/extended >> diagnostics.log 2>&1

# Recent errors
echo -e "\n=== RECENT ERRORS ===" >> diagnostics.log
docker-compose logs backend 2>&1 | grep -i "error\|exception" | tail -50 >> diagnostics.log

# Database status
echo -e "\n=== DATABASE STATUS ===" >> diagnostics.log
docker-compose exec -T db psql -U scheduler residency_scheduler \
  -c "SELECT version();" >> diagnostics.log 2>&1

# Active connections
echo -e "\n=== DATABASE CONNECTIONS ===" >> diagnostics.log
docker-compose exec -T db psql -U scheduler residency_scheduler \
  -c "SELECT * FROM pg_stat_activity;" >> diagnostics.log 2>&1

# Cache status
echo -e "\n=== CACHE STATUS ===" >> diagnostics.log
docker-compose exec -T redis redis-cli ping >> diagnostics.log 2>&1

echo "Diagnostics collected to: /tmp/incident_${incident_id}/diagnostics.log"
```

### Step 3: Determine Severity Confirmation

```
Is system completely down or data at risk?
├─ YES → P1 (See P1 Resolution)
├─ NO → Is there significant feature broken?
    ├─ YES → P2 (See P2 Resolution)
    └─ NO → Is there minor issue with workaround?
        ├─ YES → P3 (Standard troubleshooting)
        └─ NO → P4 (Log for future sprint)
```

---

## Escalation Procedures

### On-Call Chain of Command

```
On-Call Coordinator (First Contact)
    ↓
Tech Lead (P1-P2 decisions)
    ↓
Program Director (Approval for schedule changes)
    ↓
Chief Medical Officer (Escalation for safety issues)
    ↓
Hospital Incident Command (Critical incidents)
```

### P1 Escalation (IMMEDIATE)

```bash
# STEP 1: Declare P1 incident
incident_id="INC_$(date +%Y%m%d_%H%M%S)"
cat > incident_declaration.txt << EOF
P1 INCIDENT DECLARED

Incident ID: $incident_id
Time: $(date)
Declared By: [Your Name]

SITUATION:
[Brief description of the issue]

IMPACT:
- Users affected: [#]
- Systems affected: [List]
- Schedule impact: [Yes/No]

INITIAL ACTIONS TAKEN:
[List what you've done so far]

NEXT STEPS:
1. Contact Tech Lead immediately
2. Initiate war room call
3. Begin resolution procedures
EOF

# STEP 2: Call Tech Lead immediately (do not wait for email)
# Phone: [On-call phone number]

# STEP 3: Send emergency notification
curl -X POST http://localhost:8000/api/notifications/emergency \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "'$incident_id'",
    "severity": "P1",
    "recipients": ["tech_lead", "on_call", "pd"],
    "message": "P1 Incident: [Brief description]"
  }' 2>/dev/null || \
  echo "API unavailable - proceed with manual notification"

# STEP 4: Send manual notifications if API down
# Tech Lead: [Phone]
# On-Call Coordinator: [Phone]
# Program Director: [Phone]

# STEP 5: Create war room
# Zoom: [War room link]
# Bridge: [Phone bridge number]

# STEP 6: Initiate backup procedures if needed
# See "Rollback Procedures" section
```

### P2 Escalation (30 minutes)

```bash
# STEP 1: Create incident ticket
curl -X POST http://localhost:8000/api/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "P2",
    "title": "[Brief issue description]",
    "description": "[Detailed description including symptoms and impact]",
    "affected_count": [#users],
    "created_by": "coordinator"
  }'

# STEP 2: Notify Tech Lead and Program Director
cat > p2_escalation_email.txt << 'EOF'
P2 INCIDENT CREATED

Incident ID: [ID]
Severity: P2 (High)
Time: [Time]

DESCRIPTION:
[What is happening]

IMPACT:
- Affected Users: [#]
- Affected Systems: [List]
- Workaround Available: [Yes/No]

RESOLUTION TARGET: 4 hours

Next status update: [Time]
EOF

# STEP 3: Begin technical investigation
# (See Resolution Steps section)

# STEP 4: Notify affected stakeholders
# Message: System working on issue, estimated resolution [time]
```

---

## Communication Templates

### P1 Emergency Notification

```
URGENT: SYSTEM INCIDENT P1

TIME: [Time]
INCIDENT ID: [ID]
SEVERITY: CRITICAL

STATUS: System Down - Emergency Response Underway

WHAT'S HAPPENING:
[Explain what is broken in plain language]

WHO IS AFFECTED:
- Residents: YES
- Faculty: YES
- Coordinators: YES

WHAT WE'RE DOING:
1. Emergency team mobilized
2. System diagnosis underway
3. Resolution procedures initiated

ESTIMATED RESOLUTION TIME:
[Best estimate, e.g., "2 hours"]

DO NOT:
- Do not manually change schedules (we may rollback)
- Do not submit new requests yet
- Do not assume your data is lost

WE WILL UPDATE YOU IN 30 MINUTES

For emergencies only: [Emergency number]
```

### P2 Incident Notification

```
SYSTEM ISSUE - P2 (High Priority)

TIME: [Time]
INCIDENT ID: [ID]

WHAT'S AFFECTED:
[Feature/system affected]

USER IMPACT:
[Who is affected and how]

WORKAROUND (if available):
[How to work around it]

ESTIMATED RESOLUTION:
[Timeline]

STATUS UPDATES:
Next update: [Time]

Questions: [Support email/number]
```

### All-Clear Notification

```
INCIDENT RESOLVED

Incident ID: [ID]
Severity: [P1/P2/P3]
Duration: [Time span]

STATUS: RESOLVED

WHAT HAPPENED:
[Summary of issue]

WHAT WE DID:
[How we fixed it]

AFFECTED SYSTEMS: [Are now operating normally]

NO ACTION NEEDED:
Your schedules are intact and accurate.

ROOT CAUSE ANALYSIS:
[Brief explanation of root cause]
This will be reviewed in detail in our post-incident review.

Thank you for your patience.
Support Team
```

---

## Resolution Steps by Severity

### P1 Resolution Procedures

**CRITICAL INCIDENT RESOLUTION PATH**

**Step 1: Immediate Stabilization (First 15 minutes)**

```bash
# DO NOT make changes yet - gather information

# 1. Verify incident
curl http://localhost:8000/api/health 2>&1
echo "Exit code: $?"

# 2. If API down, try basic connectivity
ping -c 1 localhost:8000
docker-compose ps | grep backend

# 3. Check database
docker-compose exec -T db pg_isready -U scheduler

# 4. Check for recent errors in logs
docker-compose logs --tail=200 backend | grep -i "error\|critical"

# 5. Check system resources
df -h  # Disk space
free -h  # Memory
top -bn1 | head -20  # CPU

# DO NOT RESTART YET unless instructed
# Preserve state for forensics
```

**Step 2: Escalation and War Room (15-30 minutes)**

```bash
# Already done in Escalation section
# This step should be happening in parallel
```

**Step 3: Diagnosis (30-60 minutes)**

Based on findings, follow sub-path:

**IF DATABASE CRASHED:**
```bash
# 1. Check database logs
docker-compose logs db | tail -100

# 2. Check disk space
docker-compose exec db df -h

# 3. Attempt restart
docker-compose restart db
sleep 30

# 4. Verify database is accessible
docker-compose exec -T db psql -U scheduler -c "SELECT COUNT(*) FROM assignments;"

# 5. If still down, restore from backup
# See Rollback Procedures section
```

**IF API CRASHED:**
```bash
# 1. Check API logs for errors
docker-compose logs backend | grep -i "error\|exception\|traceback" | tail -50

# 2. Check if database connection is issue
docker-compose exec backend python -c \
  "from app.db.session import SessionLocal; s = SessionLocal(); print('DB OK')"

# 3. Check memory usage
docker stats backend --no-stream

# 4. Attempt restart
docker-compose restart backend
sleep 30

# 5. Verify API responds
curl http://localhost:8000/api/health
```

**IF DATA CORRUPTED:**
```bash
# 1. Get database backup timestamp
ls -lt backups/ | head -5

# 2. Get most recent clean backup
BACKUP_FILE=$(ls -t backups/backup*.sql | head -1)
echo "Using backup: $BACKUP_FILE"

# 3. Restore to previous state
# See Rollback Procedures section

# 4. Alert PD about potential data loss
# Estimate what was lost (time span)
```

**Step 4: Resolution and Verification (60+ minutes)**

Once root cause identified:

```bash
# For each issue type, perform specific remediation
# (See specific resolution paths below)

# CRITICAL: Verify data integrity after fix
docker-compose exec -T db psql -U scheduler residency_scheduler << 'EOF'
-- Check assignment counts
SELECT 'Assignments' as type, COUNT(*) as count FROM assignments
UNION
SELECT 'Persons', COUNT(*) FROM persons
UNION
SELECT 'Blocks', COUNT(*) FROM blocks;

-- Check for orphaned records
SELECT COUNT(*) as orphaned_assignments
FROM assignments
WHERE person_id NOT IN (SELECT id FROM persons);
EOF

# CRITICAL: Verify schedule is valid
curl -X POST http://localhost:8000/api/scheduler/validate/comprehensive \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null || \
  echo "API still recovering"

# CRITICAL: Broadcast all-clear once verified
# (See Communication Templates)
```

### P2 Resolution Procedures

**HIGH PRIORITY INCIDENT RESOLUTION PATH**

```bash
# 1. ISOLATE ISSUE
# Is it API, Database, or External?

# Check API response times
time curl http://localhost:8000/api/assignments | wc -l

# Check database query performance
docker-compose exec -T db psql -U scheduler -c \
  "EXPLAIN ANALYZE SELECT * FROM assignments LIMIT 100;"

# 2. IMPLEMENT WORKAROUND
# While investigating root cause

# Example: If swap API slow, use manual process
# Document workaround for users

# 3. INVESTIGATE ROOT CAUSE
# While workaround in place

# Check logs
docker-compose logs --since 1h backend

# Check database
docker-compose exec -T db psql -U scheduler -c \
  "SELECT query, mean_time, calls FROM pg_stat_statements
   ORDER BY mean_time DESC LIMIT 20;"

# 4. APPLY PERMANENT FIX
# Based on root cause analysis
# May require:
# - Database optimization (index, vacuum)
# - Code fix and restart
# - Configuration change
# - Resource increase

# 5. VERIFY FIX
curl http://localhost:8000/api/health/extended
```

---

## Post-Incident Review

### Step 1: Incident Summary (0-2 hours after resolution)

```bash
# Create incident report
cat > incident_report_${incident_id}.md << 'EOF'
# Incident Report

**Incident ID:** [ID]
**Severity:** [P1/P2/P3/P4]
**Duration:** [Start - End time]
**Total Duration:** [X hours Y minutes]

## Timeline

| Time | Event | Owner |
|------|-------|-------|
| [Time] | Issue detected | [Name] |
| [Time] | Incident declared | [Name] |
| [Time] | Escalation triggered | [Name] |
| [Time] | Root cause identified | [Name] |
| [Time] | Fix applied | [Name] |
| [Time] | All-clear verified | [Name] |

## Impact

- **Users Affected:** [#]
- **Systems Down:** [List]
- **Schedule Changes:** [Yes/No]
- **Data Lost:** [Yes/No - describe if yes]

## Root Cause

[Detailed explanation of what caused the issue]

## Resolution

[What we did to fix it]

## Lessons Learned

1. [What we learned]
2. [What we learned]
3. [What we learned]

## Action Items

- [ ] Item 1 - Owner - Due [Date]
- [ ] Item 2 - Owner - Due [Date]
- [ ] Item 3 - Owner - Due [Date]

EOF

cat incident_report_${incident_id}.md
```

### Step 2: Schedule Post-Incident Review

```bash
# Within 48 hours of resolution (not immediately after)
# When team has recovered

cat > postmortem_invite.txt << 'EOF'
POST-INCIDENT REVIEW MEETING

Incident ID: [ID]
Incident Type: [Describe]
Duration: [How long was it down]

PURPOSE:
Understand what happened and what we can do to prevent it in the future.

ATTENDEES:
- On-call coordinator who reported
- Tech lead who investigated
- System admin involved in fix
- Program director (optional but recommended)

MEETING AGENDA:
1. Timeline review (5 min)
2. What went right (3 min)
3. What went wrong (5 min)
4. Root cause discussion (5 min)
5. Preventive measures (10 min)
6. Assign action items (2 min)

DATE/TIME: [Schedule for next day or two]
DURATION: 30-45 minutes
EOF
```

### Step 3: Preventive Actions

```bash
# Based on post-incident review, implement changes

# Common preventive actions:
# 1. Add monitoring alert for [condition]
# 2. Implement [process improvement]
# 3. Add [system redundancy]
# 4. Fix [code/config issue]
# 5. Improve [documentation]

cat > preventive_actions.txt << 'EOF'
PREVENTIVE ACTIONS FROM INCIDENT [ID]

Action 1: [What we will do]
Owner: [Person]
Target Date: [Date]
Status: [Not Started/In Progress/Complete]

Action 2: [What we will do]
Owner: [Person]
Target Date: [Date]
Status: [Not Started/In Progress/Complete]

Action 3: [What we will do]
Owner: [Person]
Target Date: [Date]
Status: [Not Started/In Progress/Complete]

METRICS TO TRACK:
- [Metric 1]: [Target]
- [Metric 2]: [Target]
- [Metric 3]: [Target]
EOF
```

---

## On-Call Rotation

### On-Call Schedule

```
WEEK 1 (Jan 1-7):
- Mon-Fri: [Name 1]
- Sat-Sun: [Name 2]

WEEK 2 (Jan 8-14):
- Mon-Fri: [Name 3]
- Sat-Sun: [Name 4]

[Continue for full year]
```

### On-Call Responsibilities

**During On-Call Week:**

1. **Availability:**
   - Answer calls within 15 minutes
   - Check email every 30 minutes during business hours
   - Check Slack every 5 minutes during alerts
   - Keep phone within reach 24/7

2. **Triage:**
   - Confirm incident validity
   - Classify severity
   - Collect initial diagnostics
   - Escalate as needed

3. **Communication:**
   - Provide status updates every 30 minutes for P1
   - Provide status updates every 2 hours for P2
   - Provide all-clear once resolved

4. **Documentation:**
   - Log all incidents
   - Record timeline
   - Create incident report
   - Update postmortem

### On-Call Handoff

```
ON-CALL HANDOFF CHECKLIST

Outgoing On-Call: [Name]
Incoming On-Call: [Name]
Date: [Date]
Time: 09:00 AM

KNOWLEDGE TRANSFER:

☐ Current open incidents: [# open]
  - [Incident 1]: [Status]
  - [Incident 2]: [Status]

☐ Known issues being monitored:
  - [Issue 1]: [Workaround]
  - [Issue 2]: [Workaround]

☐ Upcoming maintenance or deploys:
  - [Event 1]: [Time]
  - [Event 2]: [Time]

☐ Contact information updated:
  - Tech Lead: [#]
  - Program Director: [#]
  - On-Call Support: [#]

☐ Tools access verified:
  - SSH/VPN: ✓
  - Monitoring dashboard: ✓
  - Incident tracking: ✓
  - Communication channels: ✓

SIGN-OFF:
Outgoing: _________________________ Date/Time: _______
Incoming: _________________________ Date/Time: _______
```

---

## Rollback Procedures

**When to Rollback:**
- Critical data corruption
- System unrecoverable from running state
- Major incident requiring state reset
- Database integrity issues

**When NOT to Rollback:**
- API performance issue (can be optimized)
- Single feature broken (can be fixed in place)
- Cosmetic issues

**Rollback Decision Tree:**

```
Critical Issue Detected?
├─ Data corrupted/missing?
│   └─ YES → ROLLBACK
├─ Database cannot start?
│   └─ YES → ROLLBACK
├─ System completely unusable?
│   ├─ YES, no other fix possible → ROLLBACK
│   └─ YES, but fix possible → REPAIR
├─ Can we fix without rollback?
│   ├─ YES, < 30 min → REPAIR
│   └─ NO, will take > 1 hour → ROLLBACK
```

### Rollback Steps

```bash
# STEP 1: Locate backup
ls -lt backups/ | head -10
BACKUP_FILE=$(ls -t backups/backup_*.sql | head -1)
echo "Rolling back to: $BACKUP_FILE"
echo "Backup age: $(stat -f%Sm -t '%Y-%m-%d %H:%M:%S' $BACKUP_FILE)"

# STEP 2: Alert all stakeholders
# IMPORTANT: This is destructive, need approval

cat > rollback_alert.txt << 'EOF'
CRITICAL SYSTEM ROLLBACK IN PROGRESS

All system changes since [time] are being DISCARDED.

Please:
1. Stop all schedule changes
2. Do not submit requests
3. Schedules may change back to previous state
4. We will notify you when complete

Estimated completion: [time]
EOF

# Send alert

# STEP 3: Stop all services
docker-compose down
sleep 10

# STEP 4: Restore database
echo "Restoring database from backup..."
docker-compose up -d db
sleep 10

docker-compose exec -T db \
  psql -U scheduler residency_scheduler < $BACKUP_FILE

echo "Database restore complete"

# STEP 5: Verify restoration
docker-compose exec -T db psql -U scheduler -c \
  "SELECT COUNT(*) as assignments FROM assignments;"

# STEP 6: Restart all services
docker-compose up -d
sleep 30

# STEP 7: Verify system
curl http://localhost:8000/api/health

# STEP 8: Notify completion
cat > rollback_complete.txt << 'EOF'
SYSTEM ROLLBACK COMPLETE

Database restored to state at: [time]

Changes between [start time] and [end time] have been rolled back.

WHAT TO DO NOW:
1. Review schedule - may have changed
2. Repeat any important manual entries
3. We will conduct full review

Apologies for the disruption.
Support Team
EOF
```

---

## Incident Templates

### Incident Log Entry Template

```
INCIDENT LOG ENTRY

Date: [Date]
Incident ID: [ID]
Reporter: [Name]

INCIDENT DETAILS:
- Severity: [P1/P2/P3/P4]
- Component: [API/DB/Schedule/Swap/Reports/Other]
- Description: [What happened]

SYMPTOMS:
- Symptom 1: [Description]
- Symptom 2: [Description]

TIMELINE:
- [Time]: Issue detected
- [Time]: Investigation began
- [Time]: Root cause found
- [Time]: Resolution applied
- [Time]: Verified fixed
- Duration: [X hours Y minutes]

ROOT CAUSE: [What caused it]

RESOLUTION: [How we fixed it]

IMPACT:
- Users affected: [#]
- Services down: [List]
- Data lost: [None/Description]
- SLA impact: [Yes/No]

ACTION ITEMS:
- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

Signed: _________________ Date: _________
```

### Issue Analysis Template

```
INCIDENT ANALYSIS FORM

Incident ID: _________________

ROOT CAUSE ANALYSIS (5 Whys):

1. What happened?
   [Description]

2. Why did it happen?
   [First level cause]

3. Why did that happen?
   [Second level cause]

4. Why did that happen?
   [Third level cause]

5. Why did that happen?
   [Root cause - the fundamental issue]

CONTRIBUTING FACTORS:
- Factor 1: [Description]
- Factor 2: [Description]
- Factor 3: [Description]

PREVENTIVE MEASURES:
- Measure 1: [How to prevent]
- Measure 2: [How to prevent]
- Measure 3: [How to prevent]

CORRECTIVE ACTIONS:
- Action 1: [What we will do] - Owner: [Name] - Due: [Date]
- Action 2: [What we will do] - Owner: [Name] - Due: [Date]
- Action 3: [What we will do] - Owner: [Name] - Due: [Date]
```

---

## Quick Reference

### Emergency Numbers

```
Tech Lead: [Number]
Program Director: [Number]
On-Call Coordinator: [Number]
Hospital Operator: [Number]
Chief Medical Officer: [Number]
```

### Key Commands

```bash
# System Status
docker-compose ps
docker-compose logs -f backend

# Database
docker-compose exec db psql -U scheduler residency_scheduler

# API
curl http://localhost:8000/api/health

# Restart Services
docker-compose restart backend
docker-compose restart db

# View Incidents
curl http://localhost:8000/api/incidents

# Create Incident (if API up)
curl -X POST http://localhost:8000/api/incidents ...
```

### Key Files

- Incident log: `/var/log/scheduler/incidents.log`
- Backups: `./backups/backup_*.sql`
- Diagnostics: `/tmp/incident_*/`
- Config: `./backend/.env`

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
**Owner:** Operations/IT
**Review Cycle:** Quarterly or after major incidents
