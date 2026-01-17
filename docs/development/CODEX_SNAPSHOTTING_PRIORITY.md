# Codex Snapshotting Priority List

> Purpose: speed up Codex runs by preparing snapshotting in a controlled, experimental window.

## Guardrails

- Do not enable snapshotting now.
- Enable snapshotting in `/experimental` overnight only.
- Keep snapshots free of secrets and exclude transient artifacts that bloat size without speeding startup.

## Priority List

| Priority | Task | Outcome |
| --- | --- | --- |
| P0 | Capture baseline timings for common Codex tasks (startup, dependency install, test boot). | A before/after baseline to confirm speed gains. |
| P1 | Define snapshot scope (include caches + dependencies that reduce cold start; exclude logs, temp files, large exports). | A clear include/exclude list for consistent snapshots. |
| P2 | Draft a snapshot runbook with rollback steps and storage location. | Repeatable procedure with a safe recovery path. |
| P3 | Overnight-only enablement in `/experimental`, then run a single snapshot cycle. | First experimental snapshot and measured impact. |
| P4 | Document results and decide whether to keep experimental or promote to default. | Go/no-go decision backed by metrics. |

## Overnight Enablement Checklist

- Confirm it is an overnight window and no active work depends on current settings.
- Enable snapshotting only inside `/experimental`; leave default behavior unchanged.
- Run one snapshot cycle and record timings and disk size.
- Disable if regressions appear or snapshot size grows unexpectedly.
