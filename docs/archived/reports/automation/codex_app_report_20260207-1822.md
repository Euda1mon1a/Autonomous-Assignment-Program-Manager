# Codex App Automation Report

- Generated: 2026-02-07 18:22
- Worktree root: `/Users/aaronmontgomery/.codex/worktrees`
- Repo origin: `github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager`
- Worktrees scanned: 2
- Worktrees reported: 2

## Summary

| Worktree | Branch | Last commit | Changes | Signal | Noise |
|---|---|---|---:|---:|---:|
| `/Users/aaronmontgomery/.codex/worktrees/1201/Autonomous-Assignment-Program-Manager` | `HEAD` | `ecac9155 chore: quick wins — deps, skill, and mock tool labels (#839)` | 26 | 26 | 0 |
| `/Users/aaronmontgomery/.codex/worktrees/4231/Autonomous-Assignment-Program-Manager` | `HEAD` | `ecac9155 chore: quick wins — deps, skill, and mock tool labels (#839)` | 27 | 25 | 2 |

## Details

### /Users/aaronmontgomery/.codex/worktrees/1201/Autonomous-Assignment-Program-Manager
- Branch: `HEAD`
- Last commit: `ecac9155 chore: quick wins — deps, skill, and mock tool labels (#839)`
- Changes: 26 (signal 26 / noise 0)
- Top-level buckets: .gitignore:1, Makefile:1, Procfile.local:1, README.md:1, backend:3, docs:6, env.example:1, mcp-server:2, scripts:10

Status:
```
M .env.example
 M .gitignore
 M Makefile
 M README.md
 M backend/.env.example
 M backend/app/core/celery_app.py
 M backend/app/core/config.py
 M docs/api/index.md
 M docs/development/setup.md
 M docs/getting-started/index.md
 M docs/getting-started/installation.md
 M mcp-server/README.md
 M scripts/start-celery.sh
 M scripts/start-local.sh
 M scripts/start-mcp.sh
?? Procfile.local
?? docs/getting-started/macos-local.md
?? docs/operations/local-runbook.md
?? mcp-server/.env.example
?? scripts/dev/local-db-init.sh
?? scripts/dev/local-services-start.sh
?? scripts/dev/local-services-stop.sh
?? scripts/dev/setup-macos.sh
?? scripts/dev/start-local.sh
?? scripts/dev/status-local.sh
?? scripts/dev/stop-local.sh
```
Diffstat:
```
.env.example                         |   4 +-
 .gitignore                           |   1 +
 Makefile                             | 279 ++++++++++++++++++-----------------
 README.md                            |  86 +++++------
 backend/.env.example                 |  11 +-
 backend/app/core/celery_app.py       |   2 +-
 backend/app/core/config.py           |  12 +-
 docs/api/index.md                    |   8 +-
 docs/development/setup.md            |  99 ++++++-------
 docs/getting-started/index.md        | 157 +++-----------------
 docs/getting-started/installation.md | 191 ++++++------------------
 mcp-server/README.md                 |  53 +++----
 scripts/start-celery.sh              |   2 +-
 scripts/start-local.sh               | 144 +-----------------
 scripts/start-mcp.sh                 |  88 ++---------
 15 files changed, 355 insertions(+), 782 deletions(-)
```

### /Users/aaronmontgomery/.codex/worktrees/4231/Autonomous-Assignment-Program-Manager
- Branch: `HEAD`
- Last commit: `ecac9155 chore: quick wins — deps, skill, and mock tool labels (#839)`
- Changes: 27 (signal 25 / noise 2)
- Top-level buckets: .claude:2, README.md:1, akefile:1, backend:17, mcp-server:5, scripts:1

Status:
```
M Makefile
 M README.md
 M backend/app/api/routes/rate_limit.py
 M backend/app/api/routes/schedule.py
 M backend/app/auth/sso/saml_provider.py
 M backend/app/core/slowapi_limiter.py
 M backend/app/core/xml_security.py
 M backend/app/scheduling/engine.py
 M backend/app/schemas/schedule.py
 M backend/app/services/block_schedule_export_service.py
 M backend/app/services/export/xml_exporter.py
 M backend/app/services/half_day_xml_exporter.py
 M backend/app/services/schedule_xml_exporter.py
 M backend/app/services/tamc_color_scheme.py
 M backend/app/services/xml_to_xlsx_converter.py
 M backend/app/utils/rosetta_xml_validator.py
 M backend/requirements.txt
 M backend/scripts/backfill_external_rotation_saturday_off.py
 M backend/tests/test_slowapi_limiter.py
 M mcp-server/src/scheduler_mcp/tools/executor.py
 M mcp-server/src/scheduler_mcp/tools/schedule/create_assignment.py
 M mcp-server/tests/conftest.py
 M mcp-server/tests/test_server.py
 M mcp-server/tests/tools/test_tool_integration.py
 M scripts/start-local.sh
?? .claude/dontreadme/stack-health/2026-02-07_154449.json
?? .claude/dontreadme/stack-health/2026-02-07_160038.json
```
Diffstat:
```
Makefile                                           | 22 ++++-
 README.md                                          | 22 +++--
 backend/app/api/routes/rate_limit.py               | 23 ++++--
 backend/app/api/routes/schedule.py                 | 93 +++++++++++++++++++++-
 backend/app/auth/sso/saml_provider.py              |  6 +-
 backend/app/core/slowapi_limiter.py                | 72 +++++++++++++----
 backend/app/core/xml_security.py                   |  5 +-
 backend/app/scheduling/engine.py                   | 39 ++++-----
 backend/app/schemas/schedule.py                    |  4 +-
 .../app/services/block_schedule_export_service.py  |  5 +-
 backend/app/services/export/xml_exporter.py        |  6 +-
 backend/app/services/half_day_xml_exporter.py      | 11 ++-
 backend/app/services/schedule_xml_exporter.py      |  6 +-
 backend/app/services/tamc_color_scheme.py          |  6 +-
 backend/app/services/xml_to_xlsx_converter.py      |  6 +-
 backend/app/utils/rosetta_xml_validator.py         |  5 +-
 backend/requirements.txt                           |  1 +
 .../backfill_external_rotation_saturday_off.py     |  9 +--
 backend/tests/test_slowapi_limiter.py              | 25 ++++--
 mcp-server/src/scheduler_mcp/tools/executor.py     |  6 +-
 .../tools/schedule/create_assignment.py            | 47 +++++++++--
 mcp-server/tests/conftest.py                       | 12 ++-
 mcp-server/tests/test_server.py                    |  2 +
 mcp-server/tests/tools/test_tool_integration.py    | 24 +++---
 scripts/start-local.sh                             |  6 +-
 25 files changed, 352 insertions(+), 111 deletions(-)
```
