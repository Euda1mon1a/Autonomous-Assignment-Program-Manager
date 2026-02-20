# Database Seeding Guide

> Comprehensive reference for populating the development database with mock data.

## Quick Start

All seed scripts are in `backend/` and should be run from that directory using the venv:

```bash
cd backend

# Full environment seed (core entities: users, people, rotations, blocks, call)
.venv/bin/python scripts/seed_antigravity.py --clear

# Feature-specific seeds (run AFTER seed_antigravity.py)
.venv/bin/python seed_game_theory.py
.venv/bin/python seed_wellness.py
.venv/bin/python seed_notifications.py
.venv/bin/python seed_resilience.py
.venv/bin/python seed_swaps.py
```

> [!WARNING]
> Feature seed scripts use async sessions (`asyncpg`). If you get `ModuleNotFoundError`, ensure you're using `.venv/bin/python`, not the system Python.

---

## Seed Script Inventory

| Script                        | Tables                                                                                                                                                                                                      | Rows Created | Prerequisites                                |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | -------------------------------------------- |
| `scripts/seed_antigravity.py` | users, people, blocks, rotations, call_assignments, absences                                                                                                                                                | ~200+        | None (use `--clear` for clean slate)         |
| `scripts/seed_data.py`        | Legacy seeder                                                                                                                                                                                               | Varies       | Deprecated; use `seed_antigravity.py`        |
| `seed_game_theory.py`         | config_strategies, game_theory_tournaments, tournament_matches                                                                                                                                              | ~8           | `seed_antigravity.py` (needs people)         |
| `seed_wellness.py`            | surveys, wellness_accounts, survey_responses, hopfield_positions                                                                                                                                            | ~35          | `seed_antigravity.py` (needs people)         |
| `seed_notifications.py`       | email_templates, notification_preferences, notifications, email_logs                                                                                                                                        | ~32          | `seed_antigravity.py` (needs users)          |
| `seed_resilience.py`          | scheduling_zones, zone_faculty_assignments, resilience_events, feedback_loop_states, allostasis_records, equilibrium_shifts, cognitive_sessions, cognitive_decisions, zone_incidents, system_stress_records | ~38          | `seed_antigravity.py` (needs people + users) |
| `seed_swaps.py`               | swap_records, swap_approvals                                                                                                                                                                                | ~9           | `seed_antigravity.py` (needs people + users) |

---

## Architecture Notes

### Raw SQL vs ORM

Some seed scripts use **raw SQL** (`text()`) instead of SQLAlchemy ORM models. This is intentional — several tables have **schema drift** where the ORM model defines columns not present in the actual database (or with different names). See [SCHEMA_DRIFT_REPORT.md](SCHEMA_DRIFT_REPORT.md) for details.

Scripts using raw SQL:
- `seed_resilience.py` — all inserts
- `seed_swaps.py` — all inserts (avoids `swaptype` enum issue)

Scripts using ORM:
- `seed_game_theory.py` — via service layer
- `seed_wellness.py` — via direct ORM
- `seed_notifications.py` — via direct ORM

### Idempotency

All feature seed scripts check for existing data before inserting (via `count_rows()` or `SELECT` queries). They can be safely re-run without creating duplicates. To re-seed from scratch, either:
1. Truncate the specific tables manually, or
2. Run `seed_antigravity.py --clear` to reset everything

### Datetime Handling

Feature seed scripts use `datetime.now(UTC)` (timezone-aware) for timestamp fields. This follows the project-wide convention established in PRs #1162-#1168 which migrated all `datetime.utcnow()` calls. The `utcnow()` function is deprecated in Python 3.12+.

Import pattern:
```python
from datetime import UTC, datetime, timedelta
now = datetime.now(UTC)
```

### Check Constraints

Several resilience tables have CHECK constraints on enum columns. Valid values:

| Table                   | Column               | Valid Values                                                                                                                                                                                                            |
| ----------------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `resilience_events`     | `event_type`         | health_check, crisis_activated, crisis_deactivated, fallback_activated, fallback_deactivated, load_shedding_activated, load_shedding_deactivated, defense_level_changed, threshold_exceeded, n1_violation, n2_violation |
| `scheduling_zones`      | `zone_type`          | inpatient, outpatient, education, research, admin, on_call                                                                                                                                                              |
| `scheduling_zones`      | `status`             | green, yellow, orange, red, black                                                                                                                                                                                       |
| `scheduling_zones`      | `containment_level`  | none, soft, moderate, strict, lockdown                                                                                                                                                                                  |
| `system_stress_records` | `stress_type`        | faculty_loss, demand_surge, quality_pressure, time_compression, resource_scarcity, external_pressure                                                                                                                    |
| `feedback_loop_states`  | `deviation_severity` | none, minor, moderate, major, critical                                                                                                                                                                                  |
| `allostasis_records`    | `allostasis_state`   | homeostasis, allostasis, allostatic_load, allostatic_overload                                                                                                                                                           |
| `equilibrium_shifts`    | `equilibrium_state`  | stable, compensating, stressed, unsustainable, critical                                                                                                                                                                 |
| `zone_incidents`        | `severity`           | minor, moderate, severe, critical                                                                                                                                                                                       |
| `compensation_records`  | `compensation_type`  | overtime, cross_coverage, deferred_leave, service_reduction, efficiency_gain, backup_activation, quality_trade                                                                                                          |

---

## CLI Seeder

A CLI-based seeder exists at `cli/commands/db_seed.py` for use with the app's CLI interface. This is an alternative entry point that wraps the same seeding logic.

---

## Verification

After seeding, verify data counts:

```bash
cd backend && .venv/bin/python -c "
from sqlalchemy import create_engine, text
from app.core.config import get_settings
engine = create_engine(get_settings().DATABASE_URL)
with engine.connect() as conn:
    for t in ['people', 'users', 'scheduling_zones',
              'swap_records', 'resilience_events',
              'surveys', 'notification_preferences',
              'allostasis_records', 'cognitive_sessions']:
        r = conn.execute(text(f'SELECT count(*) FROM {t}'))
        print(f'{t}: {r.scalar()}')
"
```

---

## Related Documentation

- [Schema Drift Report](SCHEMA_DRIFT_REPORT.md) — Known mismatches between ORM models and DB schema
- [Resilience API](../api/RESILIENCE_API.md) — Resilience endpoints
- [Swaps API](../api/SWAPS_API.md) — Swap endpoints
- [Best Practices](BEST_PRACTICES_AND_GOTCHAS.md) — General development patterns
