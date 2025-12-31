# Database Models Status Report

**Generated:** 2025-12-16
**Database:** PostgreSQL (SQLAlchemy 2.0.45)
**Migrations:** Alembic 1.17.2

---

## Summary

| Category | Tables | Status |
|----------|--------|--------|
| Core Scheduling | 8 | ✅ Active |
| Credentialing | 2 | ✅ Active |
| Certification | 2 | ✅ Active |
| Resilience Tier 1 | 5 | ✅ Active |
| Resilience Tier 2 | 9 | ✅ Active |
| Resilience Tier 3 | 8 | ✅ Active |
| **Total** | **34** | |

---

## Core Scheduling Models (8 tables)

| Model | Table | Purpose | Status |
|-------|-------|---------|--------|
| `User` | `users` | Authentication & role-based access | ✅ |
| `Person` | `people` | Residents and faculty members | ✅ |
| `Block` | `blocks` | Half-day scheduling units (730/year) | ✅ |
| `RotationTemplate` | `rotation_templates` | Reusable activity patterns | ✅ |
| `Assignment` | `assignments` | Core schedule - person to block mapping | ✅ |
| `Absence` | `absences` | Leave, deployment, TDY tracking | ✅ |
| `CallAssignment` | `call_assignments` | Overnight/weekend call tracking | ✅ |
| `ScheduleRun` | `schedule_runs` | Schedule generation audit trail | ✅ |

---

## Credentialing & Certification Models (4 tables)

| Model | Table | Purpose | Status |
|-------|-------|---------|--------|
| `Procedure` | `procedures` | Medical procedures requiring supervision | ✅ |
| `ProcedureCredential` | `procedure_credentials` | Faculty procedure certifications | ✅ |
| `CertificationType` | `certification_types` | Certification definitions (BLS, ACLS, etc.) | ✅ |
| `PersonCertification` | `person_certifications` | Individual certification tracking | ✅ |

---

## Resilience System Models (22 tables)

### Tier 1 - Critical Response (5 tables)

| Model | Table | Purpose | Status |
|-------|-------|---------|--------|
| `ResilienceHealthCheck` | `resilience_health_checks` | System health snapshots | ✅ |
| `ResilienceEvent` | `resilience_events` | Resilience event audit log | ✅ |
| `SacrificeDecision` | `sacrifice_decisions` | Load shedding decisions | ✅ |
| `FallbackActivation` | `fallback_activations` | Pre-computed fallback activations | ✅ |
| `VulnerabilityRecord` | `vulnerability_records` | N-1/N-2 vulnerability analysis | ✅ |

### Tier 2 - Strategic (9 tables)

| Model | Table | Purpose | Status |
|-------|-------|---------|--------|
| `FeedbackLoopState` | `feedback_loop_states` | Homeostasis monitoring | ✅ |
| `AllostasisRecord` | `allostasis_records` | Cumulative stress tracking | ✅ |
| `PositiveFeedbackAlert` | `positive_feedback_alerts` | Amplification detection | ✅ |
| `SchedulingZoneRecord` | `scheduling_zones` | Blast radius isolation | ✅ |
| `ZoneFacultyAssignmentRecord` | `zone_faculty_assignments` | Zone assignments | ✅ |
| `ZoneBorrowingRecord` | `zone_borrowing_records` | Cross-zone borrowing | ✅ |
| `ZoneIncidentRecord` | `zone_incidents` | Zone incident tracking | ✅ |
| `EquilibriumShiftRecord` | `equilibrium_shifts` | Equilibrium shift analysis | ✅ |
| `SystemStressRecord` | `system_stress_records` | System stress tracking | ✅ |
| `CompensationRecord` | `compensation_records` | Stress compensation responses | ✅ |

### Tier 3 - Tactical (8 tables)

| Model | Table | Purpose | Status |
|-------|-------|---------|--------|
| `CognitiveSessionRecord` | `cognitive_sessions` | Coordinator decision sessions | ✅ |
| `CognitiveDecisionRecord` | `cognitive_decisions` | Individual decision tracking | ✅ |
| `PreferenceTrailRecord` | `preference_trails` | Stigmergic preferences | ✅ |
| `TrailSignalRecord` | `trail_signals` | Preference trail signals | ✅ |
| `FacultyCentralityRecord` | `faculty_centrality` | Network centrality analysis | ✅ |
| `HubProtectionPlanRecord` | `hub_protection_plans` | Critical faculty protection | ✅ |
| `CrossTrainingRecommendationRecord` | `cross_training_recommendations` | Training recommendations | ✅ |

---

## Migration History

| Version | File | Description | Status |
|---------|------|-------------|--------|
| 001 | `001_initial_schema.py` | Core tables | ✅ Applied |
| 002 | `002_add_absence_blocking_and_person_capacity.py` | Enhanced absences | ✅ Applied |
| 003 | `003_add_acgme_audit_fields.py` | ACGME audit trail | ✅ Applied |
| 004 | `004_add_resilience_tables.py` | Tier 1 resilience | ✅ Applied |
| 005 | `005_add_tier2_resilience_tables.py` | Tier 2 resilience | ✅ Applied |
| 006 | `006_add_tier3_resilience_tables.py` | Tier 3 resilience | ✅ Applied |
| 007 | `007_add_procedure_credentialing.py` | Procedures & credentials | ✅ Applied |
| 008 | `008_add_certification_tracking.py` | Certification system | ✅ Applied |

---

## File Structure

```
backend/
├── app/
│   ├── db/
│   │   ├── base.py          # SQLAlchemy Base
│   │   ├── session.py       # Engine & session management
│   │   └── types.py         # GUID, JSONType, StringArrayType
│   ├── models/
│   │   ├── user.py
│   │   ├── person.py
│   │   ├── block.py
│   │   ├── rotation_template.py
│   │   ├── assignment.py
│   │   ├── absence.py
│   │   ├── call_assignment.py
│   │   ├── schedule_run.py
│   │   ├── procedure.py
│   │   ├── procedure_credential.py
│   │   ├── certification.py
│   │   └── resilience.py    # 22 resilience tables
│   └── core/
│       └── config.py        # DATABASE_URL
└── alembic/
    └── versions/            # 8 migration files
```

---

## Database Configuration

- **Primary:** `postgresql://scheduler:scheduler@localhost:5432/residency_scheduler`
- **Fallback:** SQLite support via cross-database type definitions
- **Primary Key Type:** UUID (GUID)
- **JSON Support:** JSONB (PostgreSQL) / TEXT (SQLite)
- **Array Support:** ARRAY (PostgreSQL) / JSON-serialized TEXT (SQLite)
