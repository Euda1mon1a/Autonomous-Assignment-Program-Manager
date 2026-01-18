# Current Changes Review (2026-01-17)

## Findings

1. High - Rollback backups for `time_of_day="ALL"` only capture the AM slot, so a full-day draft change can lose the PM assignment on restore. `backend/app/scheduling/schedule_publish_staging.py:277`
2. High - Backup serialization/restore omits key HalfDayAssignment fields (e.g., `block_assignment_id`, `overridden_by`, `overridden_at`, `updated_at`), so rollback may not restore provenance or overrides. `backend/app/scheduling/schedule_publish_staging.py:298` `backend/app/scheduling/schedule_publish_staging.py:403`
3. High - Rest-period calculation assumes `date` objects; if schedule data is serialized to strings, `_calculate_rest_hours` will attempt date arithmetic on strings and can raise `TypeError`, failing compliance validation. `backend/app/scheduling/validators/work_hour_validator.py:341`
4. Medium - 24+4 and rest-period checks build shift data from `assignments` only; `call_assignments` are excluded, so extended call duty may not be validated. `backend/app/scheduling/acgme_compliance_engine.py:231` `backend/app/scheduling/acgme_compliance_engine.py:273`
5. Medium - Performance profiling defaults to `num_residents=20`/`num_blocks=100` because `SchedulingContext` lacks those fields, which can understate complexity and skip warnings on real workloads. `backend/app/scheduling/constraint_validator.py:567`
6. Medium - MCP SSE fallback treats `0.0.0.0` as non-localhost, while HTTP auth treats it as localhost; if HTTP setup fails and SSE fallback is used with `MCP_HOST=0.0.0.0`, startup can fail unexpectedly. `mcp-server/src/scheduler_mcp/server.py:5348` `mcp-server/src/scheduler_mcp/server.py:5536`
7. Low - Startup log points to a non-existent `python -m app.cli create-admin` command; the documented CLI uses `app.cli user create ...`, so operators get misdirected. `backend/app/main.py:145`
8. Low - Queue task "whitelist" allows any `app.services.*` task via prefix, which conflicts with the stated goal of only allowing known safe tasks. `backend/app/api/routes/queue.py:65`

## Open Questions / Assumptions

- Are the new rollback backup/staging utilities expected to be wired into `schedule_draft_service` in this change set, or are they intentionally staged for later integration?
- Are schedule `date` values for compliance validation always `date` objects, or do they sometimes arrive as strings (e.g., JSON payloads or cached data)?
- Should call duty be represented in `assignments` (and thus included in shift_data), or should `call_assignments` be merged into shift validation?

## Change Summary

- Security hardening: GraphQL auth enforcement, queue task allowlist, MCP API key restrictions.
- Compliance enhancements: rest-period and 24+4 rule validation, constraint validation expansion.
- Performance: query prefetching in ACGME validator and FMIT health, new scheduling profiler heuristics.
- Rollback infrastructure: assignment backups, draft staging utilities, new migration.
- Notifications: outbox-driven email notifications for assignments, swaps, conflicts.

## Tests

- Not run (review-only).
