# Schema Audit Report

**Generated:** 2026-01-11 04:40
**Branch:** fix/mcp-server-tests

## Summary

| Category | Count |
|----------|-------|
| Models in code | 87 |
| Tables in database | 87 |
| ✅ Synced | 75 |
| ❌ Missing from DB | 12 |
| ⚠️ Continuum | 5 |
| 🔍 Extra in DB | 7 |

---

## ❌ Missing from Database (12)

Models with no corresponding table - need migrations:

| Table | Priority | Notes |
|-------|----------|-------|
| `calendar_subscriptions` | TBD | |
| `export_job_executions` | TBD | |
| `export_jobs` | TBD | |
| `oauth2_authorization_codes` | TBD | |
| `pkce_clients` | TBD | |
| `schema_change_events` | TBD | |
| `schema_versions` | TBD | |
| `state_machine_instances` | TBD | |
| `state_machine_transitions` | TBD | |
| `webhook_dead_letters` | TBD | |
| `webhook_deliveries` | TBD | |
| `webhooks` | TBD | |


---

## ⚠️ Continuum Tables (5)

Auto-created by SQLAlchemy-Continuum. **Exclude from Alembic autogenerate.**


- `absences_version`
- `assignments_version`
- `import_staged_absences_version`
- `schedule_runs_version`
- `transaction`


---

## 🔍 Extra Tables (7)

Tables without models - may be legacy or intentionally model-free:


- `absence_version`
- `alembic_version`
- `chaos_experiments`
- `faculty_activity_permissions`
- `metric_snapshots`
- `schedule_diffs`
- `schedule_versions`


---

## Next Steps

1. Add Continuum exclusion to `backend/alembic/env.py`
2. Review missing tables - decide which need migrations
3. Investigate extra tables - orphaned or intentional?
