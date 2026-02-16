# Residency Scheduler Master Guide

> **Version:** 1.0 | **Last Updated:** 2026-01-10

Comprehensive consolidated reference for the Military Medical Residency Scheduling System.

**Role-Specific Quick Start:**
- [Program Coordinators](START_HERE_COORDINATOR.md)
- [System Administrators](START_HERE_ADMIN.md)
- [Developers](START_HERE_DEVELOPER.md)

---

## Table of Contents

1. [System Overview](#part-1-system-overview)
2. [ACGME Compliance Essentials](#part-2-acgme-compliance-essentials)
3. [Core Workflows](#part-3-core-workflows)
4. [Administration](#part-4-administration)
5. [Troubleshooting](#part-5-troubleshooting)
6. [Quick Reference](#part-6-quick-reference)
7. [Appendices](#appendices)

---

# Part 1: System Overview

## What is Residency Scheduler?

The Residency Scheduler is a full-stack application for managing medical residency schedules with automated ACGME compliance monitoring. Built for military medical training programs, it handles:

- **Automated Schedule Generation** - Constraint-based optimization
- **ACGME Compliance Monitoring** - 80-hour rule, 1-in-7, supervision ratios
- **Emergency Coverage** - N-1/N-2 contingency planning
- **Swap Management** - Faculty and resident shift trades
- **Procedure Credentialing** - Tracking faculty qualifications
- **Resilience Framework** - Cross-industry risk management patterns

## Key Capabilities

| Feature | Description |
|---------|-------------|
| Schedule Generation | OR-Tools CP-SAT, greedy, and hybrid algorithms |
| Compliance Validation | Real-time ACGME rule checking |
| Drag-and-Drop UI | Annual and block schedule views |
| Swap Marketplace | Request, approve, and execute swaps |
| Data Import/Export | Excel, CSV, JSON, iCal |
| Audit Trail | Complete change history |
| API Access | REST API with OpenAPI documentation |
| AI Tools | 34+ MCP tools for Claude Code integration |

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer (Next.js)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    API Gateway (Nginx)                       │
│                  SSL/TLS, Rate Limiting                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 Application Layer (FastAPI)                  │
│        Routes → Controllers → Services → Repositories        │
│                    Background Tasks (Celery)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      Data Layer                              │
│     PostgreSQL         Redis           Prometheus           │
│     (Primary DB)       (Cache)         (Metrics)            │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | FastAPI | 0.109.0 |
| ORM | SQLAlchemy | 2.0.25 (async) |
| Validation | Pydantic | 2.5.3 |
| Migrations | Alembic | 1.13.1 |
| Frontend | Next.js | 14.0.4 |
| UI | React | 18.2.0 |
| Styling | TailwindCSS | 3.3.0 |
| Data Fetching | TanStack Query | 5.17.0 |
| Database | PostgreSQL | 15 |
| Cache/Broker | Redis | Latest |
| Background | Celery | 5.x |

---

# Part 2: ACGME Compliance Essentials

## Overview

The Accreditation Council for Graduate Medical Education (ACGME) establishes duty hour requirements to ensure resident well-being and patient safety. Violations can result in program citation, probation, or loss of accreditation.

## Key Numbers at a Glance

| Requirement | Limit | Averaging |
|-------------|-------|-----------|
| Maximum work hours | **80 hours/week** | 4-week rolling |
| Minimum day off | **1 day per 7 days** | 4-week rolling |
| Rest between shifts | **10 hours** minimum | N/A |
| Maximum shift length | **24 hours** (+4hr handoff) | N/A |
| PGY-1 max shift | **16 hours** | Strict |
| In-house call | **Every 3rd night** max | 4-week |
| PGY-1 supervision | **1:2** faculty:resident | N/A |
| PGY-2/3 supervision | **1:4** faculty:resident | N/A |

## 80-Hour Maximum Work Week

Residents must not exceed **80 hours per week** averaged over a rolling 4-week period.

**Counts Toward Limit:**
- Direct patient care
- Educational conferences
- Administrative duties
- In-house call (including sleep time)
- Moonlighting

**Does NOT Count:**
- Personal study outside work
- Voluntary research outside scheduled time

**Compliance Color Coding:**
- **Green**: < 75 hours (safe)
- **Yellow**: 75-79 hours (warning)
- **Red**: ≥ 80 hours (violation)

## 1-in-7 Day Off Rule

Residents must have at least one 24-hour period free every 7 days, averaged over 4 weeks.

**Implementation:**
- Continuous 24-hour period
- 4 days off per 28-day period minimum
- Cannot be scheduled immediately before/after night float

## Maximum Shift Length

### Standard (All Residents)
- **24 hours** maximum clinical duty
- **+4 hours** for handoff and education (28 hours total)
- **10 hours** rest required after

### PGY-1 Residents
- **16 hours** strict maximum
- No additional handoff time permitted
- Enhanced supervision required

## Supervision Ratios

| PGY Level | Ratio | Requirements |
|-----------|-------|--------------|
| PGY-1 | 1:2 | Direct supervision, faculty immediately available |
| PGY-2 | 1:4 | Faculty available for consultation |
| PGY-3 | 1:4 | Progressive independence |

## In-House Call Frequency

- Maximum **every 3rd night** (averaged over 4 weeks)
- ~9-10 in-house call shifts per 28-day period
- Home call does not count toward this limit

## Compliance Monitoring in the System

The system automatically:
1. Validates compliance before finalizing assignments
2. Calculates rolling 4-week averages
3. Prevents assignments that would violate limits
4. Alerts when residents approach thresholds
5. Generates compliance reports for ACGME

---

# Part 3: Core Workflows

## Schedule Generation Lifecycle

### Overview
Schedules are generated in 4-week "blocks." The academic year (July 1 - June 30) contains 13 blocks.

### Step-by-Step Process

1. **Prepare Data**
   - Verify all residents and faculty are in system
   - Enter known absences (vacation, conferences, etc.)
   - Check rotation templates are current

2. **Configure Generation**
   - Select date range (typically 4-week block)
   - Choose algorithm:
     - **greedy**: Fast, good quality (testing)
     - **cp_sat**: Slow, optimal quality (production)
     - **hybrid**: Balanced speed/quality
   - Set timeout (default: 300 seconds)

3. **Generate Schedule**
   - System validates constraints
   - Algorithm assigns residents to rotations
   - ACGME compliance checked automatically

4. **Review and Adjust**
   - Check Daily Manifest for coverage gaps
   - Review compliance dashboard
   - Make manual adjustments if needed

5. **Publish**
   - Export to Excel for distribution
   - Sync with calendar systems (iCal)

### Playbook Reference
See [Schedule Generation Playbook](playbooks/SCHEDULE_GENERATION_PLAYBOOK.md) for detailed procedures.

## Swap Management Process

### Swap Types

| Type | Description | Approval |
|------|-------------|----------|
| One-to-One | Direct exchange between two people | Coordinator |
| One-to-Empty | Fill an uncovered slot | Auto-approved |
| Chain Swap | Multi-party rotation | Coordinator |

### Workflow

1. **Request Submitted**
   - Requester identifies assignment to swap
   - System finds compatible matches
   - Request enters pending queue

2. **Validation**
   - ACGME compliance check
   - Coverage verification
   - No double-booking

3. **Approval**
   - Coordinator reviews request
   - Approve/deny with comments
   - Notification sent to parties

4. **Execution**
   - Assignments updated
   - Audit trail created
   - Confirmation sent

5. **Rollback (if needed)**
   - Within 72-hour window
   - Requires coordinator action
   - Full reversion to previous state

### Playbook Reference
See [Swap Processing Playbook](playbooks/SWAP_PROCESSING_PLAYBOOK.md) for detailed procedures.

## Absence Management

### Absence Types

| Type | Lead Time | Coverage Required |
|------|-----------|-------------------|
| Vacation | 30 days | Yes |
| Sick | 0 days | Auto-covered |
| Conference | 14 days | Yes |
| TDY/Deployment | ASAP | Yes |
| Parental Leave | Per policy | Yes |
| Administrative | Varies | Depends |

### Workflow

1. **Request Submission**
   - Person submits via portal
   - Specify dates, type, notes

2. **Review**
   - System checks coverage impact
   - Coordinator notified

3. **Approval**
   - Coordinator approves/denies
   - Coverage arranged if needed

4. **Schedule Update**
   - Assignments marked as absent
   - Backup coverage assigned

## Compliance Monitoring

### Dashboard Elements

| Element | Description |
|---------|-------------|
| Compliance Score | Overall program health (0-100%) |
| Active Violations | Count of current violations |
| At-Risk Residents | Approaching limits |
| Weekly Hours Chart | Distribution visualization |

### Violation Severity

| Level | Description | Action |
|-------|-------------|--------|
| Warning | Approaching limit | Monitor |
| Violation | Limit exceeded | Immediate correction |
| Critical | Repeated/severe | Escalate to program director |

### Weekly Review Process

1. Check compliance dashboard Monday AM
2. Review any new violations
3. Identify at-risk residents
4. Take corrective action
5. Document in audit log

---

# Part 4: Administration

## User Management

### Roles and Permissions

| Role | View | Edit | Generate | Admin |
|------|------|------|----------|-------|
| Admin | All | All | Yes | Yes |
| Coordinator | All | All | Yes | No |
| Faculty | Assigned | No | No | No |
| Resident | Own | No | No | No |

### Account Operations

**Create Account:**
1. Admin → Users → Add User
2. Enter email, name, role
3. Set temporary password
4. User receives welcome email

**Deactivate Account:**
1. Admin → Users → Select User
2. Click Deactivate
3. Confirm action
4. User can no longer login

**Reset Password:**
```bash
cd backend
python -m app.cli user reset-password --email user@example.com
```

## System Configuration

### Key Settings

| Setting | Location | Description |
|---------|----------|-------------|
| Academic Year | Settings → General | July 1 start date |
| ACGME Parameters | Settings → Compliance | Hour limits, ratios |
| Scheduling Algorithm | Settings → Generation | Default algorithm |
| Email Settings | .env file | SMTP configuration |

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `docker-compose.yml` | Container configuration |
| `alembic.ini` | Database migrations |

## Backup Procedures

### Backup Schedule

| Type | Frequency | Retention |
|------|-----------|-----------|
| Full Database | Daily 2 AM | 30 days |
| Transaction Log | Hourly | 7 days |
| Configuration | On change | Forever |

### Manual Backup

```bash
# Database backup
docker-compose exec db pg_dump -U scheduler residency_scheduler > backup_$(date +%Y%m%d).sql

# Verify backup
ls -la backup_*.sql
```

### Restore Procedure

```bash
# 1. Stop services
docker-compose down

# 2. Restore database
docker-compose up -d db
docker-compose exec -T db psql -U scheduler residency_scheduler < backup.sql

# 3. Restart all services
docker-compose up -d
```

## Maintenance Windows

### Recommended Schedule

| Task | Frequency | Duration |
|------|-----------|----------|
| Security patches | Monthly | 1 hour |
| Database vacuum | Weekly | 30 min |
| Log rotation | Daily | Automatic |
| Full system restart | Monthly | 15 min |

### Pre-Maintenance Checklist

- [ ] Notify users 48 hours in advance
- [ ] Verify backup completed
- [ ] Document current state
- [ ] Prepare rollback plan
- [ ] Schedule off-peak time

---

# Part 5: Troubleshooting

## Common Issues by Symptom

### Schedule Won't Generate

**Symptoms:** Generation times out or fails

**Causes and Solutions:**

| Cause | Solution |
|-------|----------|
| Too many constraints | Reduce date range, try greedy algorithm |
| Insufficient coverage | Add more available faculty/residents |
| Conflicting requirements | Review constraint conflicts |
| Timeout too short | Increase timeout to 600s |

```bash
# Try greedy algorithm
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -d '{"algorithm": "greedy", "timeout_seconds": 600, ...}'
```

### Compliance Shows Violations

**Symptoms:** Red alerts in compliance dashboard

**Investigation Steps:**

1. Click violation to see details
2. Check affected resident's schedule
3. Review recent changes
4. Identify root cause
5. Apply correction

**Common Fixes:**
- Remove extra assignment
- Add day off
- Swap with available resident

### Users Can't Login

**Symptoms:** 401 Unauthorized or login fails

**Causes and Solutions:**

| Cause | Solution |
|-------|----------|
| Wrong password | Reset password |
| Account deactivated | Reactivate account |
| Token expired | Refresh token |
| Session timeout | Re-login |

```bash
# Reset password
cd backend
python -m app.cli user reset-password --email user@example.com
```

### System Slow

**Symptoms:** Pages take >3 seconds to load

**Investigation:**

```bash
# Check container resources
docker stats

# Check database connections
docker-compose exec db psql -U scheduler -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis memory
docker-compose exec redis redis-cli INFO memory
```

**Solutions:**
- Increase container memory limits
- Restart services
- Check for runaway queries
- Clear Redis cache

### Containers Won't Start

**Symptoms:** `docker-compose up` fails

**Diagnostic Steps:**

```bash
# Check logs
docker-compose logs backend

# Check container status
docker-compose ps

# Reset everything
docker-compose down -v
docker-compose up -d
```

## Emergency Procedures

### System Down - Immediate Response

1. **Assess** - Check all containers: `docker-compose ps`
2. **Logs** - Review recent logs: `docker-compose logs --tail=200`
3. **Restart** - Try restart: `docker-compose restart`
4. **Escalate** - If unresolved after 15 min, escalate

### Data Recovery

1. **Stop writes** if possible
2. **Identify backup** to restore
3. **Follow restore procedure** (see Backup section)
4. **Verify data integrity** after restore

### Security Incident

1. **Contain** - Isolate affected systems
2. **Preserve** - Don't delete logs
3. **Escalate** - Contact security team
4. **Document** - Record all actions

---

# Part 6: Quick Reference

## Common Commands

### Docker Operations

```bash
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose restart        # Restart all services
docker-compose logs -f        # Follow logs
docker-compose ps             # Check status
docker-compose exec backend bash  # Shell into backend
```

### Database Operations

```bash
# Connect to database
docker-compose exec db psql -U scheduler -d residency_scheduler

# Apply migrations
cd backend && alembic upgrade head

# Create migration
alembic revision --autogenerate -m "short_description"

# Backup
docker-compose exec db pg_dump -U scheduler residency_scheduler > backup.sql
```

### Schedule Generation

```bash
# Via CLI
cd backend
python -m app.cli schedule generate \
  --start 2025-07-01 --end 2025-09-30 \
  --algorithm cp_sat

# Via API
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-07-01", "end_date": "2025-09-30", "algorithm": "cp_sat"}'
```

### Compliance Check

```bash
# CLI
python -m app.cli compliance check --verbose

# API
curl "http://localhost:8000/api/v1/compliance/validate?start_date=2025-07-01&end_date=2025-09-30"
```

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/schedule/generate` | POST | Generate schedule |
| `/api/v1/compliance/validate` | GET | Validate compliance |
| `/api/v1/people` | GET/POST | List/create people |
| `/api/v1/absences` | GET/POST | List/create absences |
| `/api/v1/swaps/execute` | POST | Execute swap |
| `/api/v1/auth/login` | POST | Login |
| `/health` | GET | Health check |

## Port Reference

| Service | Port |
|---------|------|
| Frontend | 3000 |
| Backend API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| MCP Server | 8080 |

## Scheduling Algorithms

| Algorithm | Speed | Quality | Use Case |
|-----------|-------|---------|----------|
| `greedy` | Fast | Good | Testing, quick generation |
| `cp_sat` | Slow | Excellent | Production, optimal |
| `pulp` | Medium | Very Good | Balanced |
| `hybrid` | Medium | Excellent | Best of both |

## ACGME Quick Reference

| Rule | Limit |
|------|-------|
| Weekly hours | 80 hrs (4-week avg) |
| Day off | 1 per 7 days (4-week avg) |
| Rest between shifts | 10 hours min |
| Max shift | 24 + 4 hrs handoff |
| PGY-1 max shift | 16 hours |
| In-house call | Every 3rd night max |
| PGY-1 supervision | 1:2 |
| PGY-2/3 supervision | 1:4 |

---

# Appendices

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **ACGME** | Accreditation Council for Graduate Medical Education |
| **Block** | 4-week scheduling period |
| **Call** | On-duty period outside normal hours |
| **Coverage** | Required staffing for a rotation/shift |
| **PGY** | Post-Graduate Year (residency level) |
| **Rotation** | Clinical assignment type (e.g., ICU, Clinic) |
| **Swap** | Exchange of assignments between people |
| **TDY** | Temporary Duty Assignment (military) |

## Appendix B: Role Permissions Matrix

| Permission | Admin | Coordinator | Faculty | Resident |
|------------|-------|-------------|---------|----------|
| View all schedules | ✓ | ✓ | Assigned | Own |
| Edit schedules | ✓ | ✓ | ✗ | ✗ |
| Generate schedules | ✓ | ✓ | ✗ | ✗ |
| Manage users | ✓ | ✗ | ✗ | ✗ |
| System settings | ✓ | ✗ | ✗ | ✗ |
| Request swaps | ✓ | ✓ | ✓ | ✓ |
| Approve swaps | ✓ | ✓ | ✗ | ✗ |
| View compliance | ✓ | ✓ | ✓ | Own |
| Export data | ✓ | ✓ | ✓ | Own |

## Appendix C: Index to Detailed Documentation

### For Users
- [Full User Guide](user-guide/USER_GUIDE.md)
- [Dashboard Guide](user-guide/dashboard.md)
- [Swap Guide](user-guide/swaps.md)
- [Export Guide](user-guide/exports.md)

### For Administrators
- [Admin Manual](admin-manual/README.md)
- [Backup Guide](admin-manual/backup.md)
- [User Management](admin-manual/users.md)
- [MCP Admin Guide](admin-manual/mcp-admin-guide.md)

### For Developers
- [CLAUDE.md](../CLAUDE.md) - Project guidelines
- [Development Setup](development/setup.md)
- [API Reference](api/README.md)
- [Architecture](architecture/README.md)

### Playbooks
- [Schedule Generation](playbooks/SCHEDULE_GENERATION_PLAYBOOK.md)
- [Swap Processing](playbooks/SWAP_PROCESSING_PLAYBOOK.md)
- [Compliance Audit](playbooks/COMPLIANCE_AUDIT_PLAYBOOK.md)
- [Incident Response](playbooks/INCIDENT_RESPONSE_PLAYBOOK.md)

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-10 | Initial consolidated guide |

---

*This guide consolidates information from across the documentation. For detailed procedures, refer to the linked documents.*
