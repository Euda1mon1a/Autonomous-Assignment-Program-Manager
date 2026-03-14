# MCP Follow-Up Backlog - 2026-03-14

> Status: Draft backlog
> Scope: MCP server, MCP-facing docs, and agent knowledge that must be updated after PRs #1307-#1311

## Purpose

This document captures the MCP work that now needs to happen after the recent:

- primary duty migration to Postgres
- primary duty CRUD API addition
- rotation template preload-classification schema exposure
- hard-to-soft constraint reclassification work

This is not just "add more tools." Some MCP-facing knowledge is now stale and will cause agents to reason from the wrong architecture unless it is corrected.

## Current Reality

Two things are true at the same time:

1. The backend now exposes more DB-backed policy surfaces than before.
2. MCP and agent-facing constraint knowledge still describe parts of the old model.

There is also one backend blocker that affects MCP reliability:

- `ConstraintManager.create_default()` now requires a DB session in some code paths and regressed several callers.

That blocker should be fixed before expanding MCP coverage, because some MCP tools depend on backend constraint endpoints and seed/default-manager paths.

## Priority Summary

| Priority | Workstream | Why |
|---|---|---|
| P0 | Fix backend factory regressions | MCP tools inherit broken backend behavior otherwise |
| P1 | Update MCP constraint/domain knowledge | Agents currently get wrong hard/soft explanations |
| P1 | Add primary duty MCP tools | Human-editable DB policy exists but is not MCP-accessible |
| P2 | Add preload-classification MCP tools | New DB-backed fields are exposed in API schema but not MCP |
| P2 | Refresh MCP docs and RAG-facing architecture docs | Agents still see Airtable and old hard/soft descriptions |
| P3 | Add MCP tests / smoke checks | Prevent drift on future schema changes |

## P0 - Backend Blockers That Affect MCP

These are not MCP files, but they directly affect MCP correctness.

### 1. ConstraintManager factory regression

Problem:

- `ConstraintManager.create_default()` now adds DB-backed primary duty constraints unconditionally.
- `create_resilience_aware()` references `db_session` without defining it.

Impact on MCP:

- Constraint listing, seeding, validation, and any agent workflow that depends on default constraint-manager construction can fail or behave inconsistently.

Files:

- [manager.py](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/scheduling/constraints/manager.py)
- [primary_duty.py](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/scheduling/constraints/primary_duty.py)
- [constraints.py](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/api/routes/constraints.py)
- [constraint_service.py](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/services/constraint_service.py)
- [solvers.py](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/scheduling/solvers.py)

Expected fix:

- Make factory behavior explicit:
  - either require `db_session` at all factory call sites
  - or make DB-backed primary-duty constraints opt-in when no DB session is available
- Add `db_session` parameter to `create_resilience_aware()`
- Re-run constraint-manager tests before MCP follow-up work

### 2. Hard-to-soft semantics are only partially true

Problem:

- Some constraints were retyped to `SoftConstraint` but still add hard `model.Add(...)` feasibility rules.

Impact on MCP:

- MCP explanations that say "soft" will be wrong unless they distinguish:
  - class type
  - actual solver enforcement

Representative files:

- [call_coverage.py](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/scheduling/constraints/call_coverage.py)
- [primary_duty.py](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/scheduling/constraints/primary_duty.py)
- [acgme.py](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/scheduling/constraints/acgme.py)

Expected fix:

- Do not oversimplify MCP knowledge to `hard|soft` only.
- Add a second field such as `solver_enforcement`:
  - `hard`
  - `soft_penalty`
  - `validation_only`
  - `mixed`

## P1 - Update MCP Constraint Knowledge

### Why

Agents currently rely on stale constraint metadata in MCP-side domain context.

### Required changes

Update:

- [domain_context.py](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/mcp-server/src/scheduler_mcp/domain_context.py)

Specifically:

- Change `EightyHourRuleConstraint` from `hard` to `soft_penalty`
- Change `OneInSevenRuleConstraint` from `hard` to `soft_penalty`
- Change `SupervisionRatioConstraint` from `hard` to `validation_only` or `mixed`
- Mark `OvernightCallCoverageConstraint` as `mixed` until penalty refactor is real
- Mark `FacultyPrimaryDutyClinicConstraint` as `mixed` until penalty refactor is real
- Mark `FacultyDayAvailabilityConstraint` as `mixed` until penalty refactor is real
- Remove examples that still assume `explain_constraint()` returns only old-style hard/soft meaning

### Suggested schema change

Current MCP-side explanation payload is too coarse.

Recommended shape:

```json
{
  "type": "soft",
  "solver_enforcement": "mixed",
  "source_of_truth": "backend_db_plus_python",
  "db_tunable": true,
  "short": "Overnight call coverage",
  "description": "Classified as soft, but still enforced with hard CP-SAT equality today.",
  "violation_impact": "Operational coverage failure",
  "fix_options": [
    "Add call-eligible faculty",
    "Adjust FMIT/call inputs",
    "Refactor to penalty variables if true best-effort behavior is desired"
  ]
}
```

### Files to edit

- `mcp-server/src/scheduler_mcp/domain_context.py`
- `docs/api/MCP_TOOLS_REFERENCE.md`
- `docs/api/MCP_TOOL_GUIDE.md`

## P1 - Add Primary Duty MCP Tools

### Why

The backend now has CRUD endpoints for primary duty configs, but MCP does not expose them.

Backend routes already exist:

- `GET /api/v1/primary-duty-configs/`
- `GET /api/v1/primary-duty-configs/{id}`
- `POST /api/v1/primary-duty-configs/`
- `PATCH /api/v1/primary-duty-configs/{id}`
- `DELETE /api/v1/primary-duty-configs/{id}`

### New MCP tools to add

Recommended tool names:

1. `list_primary_duty_configs_tool`
2. `get_primary_duty_config_tool`
3. `create_primary_duty_config_tool`
4. `update_primary_duty_config_tool`
5. `delete_primary_duty_config_tool`

### Request/response schemas

#### `list_primary_duty_configs_tool`

Request:

```json
{}
```

Response:

```json
{
  "configs": [
    {
      "id": "uuid",
      "duty_name": "Program Director",
      "clinic_min_per_week": 0,
      "clinic_max_per_week": 1,
      "available_days": [1, 2, 3]
    }
  ],
  "total_count": 1
}
```

#### `get_primary_duty_config_tool`

Request:

```json
{
  "config_id": "uuid"
}
```

Response:

```json
{
  "success": true,
  "config": {
    "id": "uuid",
    "duty_name": "Program Director",
    "clinic_min_per_week": 0,
    "clinic_max_per_week": 1,
    "available_days": [1, 2, 3]
  }
}
```

#### `create_primary_duty_config_tool`

Request:

```json
{
  "duty_name": "Associate Program Director",
  "clinic_min_per_week": 1,
  "clinic_max_per_week": 2,
  "available_days": [0, 2, 4]
}
```

Response:

```json
{
  "success": true,
  "config": {
    "id": "uuid",
    "duty_name": "Associate Program Director",
    "clinic_min_per_week": 1,
    "clinic_max_per_week": 2,
    "available_days": [0, 2, 4]
  }
}
```

#### `update_primary_duty_config_tool`

Request:

```json
{
  "config_id": "uuid",
  "duty_name": "Program Director",
  "clinic_min_per_week": 0,
  "clinic_max_per_week": 2,
  "available_days": [1, 2, 3, 4]
}
```

Response:

```json
{
  "success": true,
  "config": {
    "id": "uuid",
    "duty_name": "Program Director",
    "clinic_min_per_week": 0,
    "clinic_max_per_week": 2,
    "available_days": [1, 2, 3, 4]
  }
}
```

#### `delete_primary_duty_config_tool`

Request:

```json
{
  "config_id": "uuid"
}
```

Response:

```json
{
  "success": true,
  "message": "Primary duty config deleted"
}
```

### Files to edit

- `mcp-server/src/scheduler_mcp/api_client.py`
- `mcp-server/src/scheduler_mcp/primary_duty_tools.py` (new)
- `mcp-server/src/scheduler_mcp/server.py`
- `docs/api/MCP_TOOLS_REFERENCE.md`
- `docs/api/MCP_TOOL_GUIDE.md`

### API client methods to add

Suggested methods:

- `list_primary_duty_configs()`
- `get_primary_duty_config(config_id: str)`
- `create_primary_duty_config(payload: dict[str, Any])`
- `update_primary_duty_config(config_id: str, payload: dict[str, Any])`
- `delete_primary_duty_config(config_id: str)`

## P2 - Add Rotation Template Preload Classification MCP Tools

### Why

The backend schema now exposes:

- `is_offsite`
- `is_lec_exempt`
- `is_continuity_exempt`
- `is_saturday_off`
- `preload_activity_code`

But MCP does not currently provide a focused way to inspect or update these fields.

### New MCP tools to add

Recommended minimal tool set:

1. `list_rotation_template_preload_configs_tool`
2. `get_rotation_template_preload_config_tool`
3. `update_rotation_template_preload_config_tool`

This keeps the MCP surface focused on the newly data-driven preload classification instead of trying to expose all rotation-template editing at once.

### Request/response schemas

#### `list_rotation_template_preload_configs_tool`

Request:

```json
{}
```

Response:

```json
{
  "templates": [
    {
      "id": "uuid",
      "name": "FMIT",
      "rotation_type": "inpatient",
      "is_offsite": false,
      "is_lec_exempt": true,
      "is_continuity_exempt": true,
      "is_saturday_off": false,
      "preload_activity_code": "FMIT"
    }
  ],
  "total_count": 1
}
```

#### `get_rotation_template_preload_config_tool`

Request:

```json
{
  "template_id": "uuid"
}
```

Response:

```json
{
  "success": true,
  "template": {
    "id": "uuid",
    "name": "TDY",
    "rotation_type": "outpatient",
    "is_offsite": true,
    "is_lec_exempt": true,
    "is_continuity_exempt": true,
    "is_saturday_off": true,
    "preload_activity_code": "TDY"
  }
}
```

#### `update_rotation_template_preload_config_tool`

Request:

```json
{
  "template_id": "uuid",
  "is_offsite": true,
  "is_lec_exempt": true,
  "is_continuity_exempt": true,
  "is_saturday_off": true,
  "preload_activity_code": "TDY"
}
```

Response:

```json
{
  "success": true,
  "template": {
    "id": "uuid",
    "name": "TDY",
    "rotation_type": "outpatient",
    "is_offsite": true,
    "is_lec_exempt": true,
    "is_continuity_exempt": true,
    "is_saturday_off": true,
    "preload_activity_code": "TDY"
  }
}
```

### Files to edit

- `mcp-server/src/scheduler_mcp/api_client.py`
- `mcp-server/src/scheduler_mcp/rotation_template_tools.py` or a dedicated preload tool module
- `mcp-server/src/scheduler_mcp/server.py`
- `docs/api/MCP_TOOLS_REFERENCE.md`
- `docs/api/MCP_TOOL_GUIDE.md`

## P2 - Refresh Agent and RAG Docs Used By MCP-Driven Workflows

These are not MCP code files, but they influence MCP-assisted agents through search and RAG.

### Stale now

- [primary-duty-constraints.md](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docs/architecture/primary-duty-constraints.md)
  - still says Airtable-driven
- [clinic-constraints.md](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docs/architecture/clinic-constraints.md)
  - still says Airtable configuration and still calls primary-duty constraints hard
- [constraints/__init__.py](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/scheduling/constraints/__init__.py)
  - still contains outdated "Airtable-driven" comment for primary duty exports

### Required updates

Update those docs to reflect:

- primary duty source of truth is Postgres
- CRUD API exists
- frontend admin UI is still pending
- hard/soft classification is in transition and some solver semantics remain mixed

## P3 - MCP Tests and Smoke Checks

### Add

1. API client tests for new primary duty methods
2. MCP tool tests for new primary duty tools
3. MCP tool tests for preload-classification tools
4. Domain-context snapshot tests for key constraint metadata

### Minimum smoke checklist

```bash
# Backend
cd backend && pytest tests/scheduling/test_constraint_manager.py -q

# MCP server
cd mcp-server && pytest -q

# Manual smoke
- list_constraints_tool
- get_constraint_tool("80HourRule")
- list_primary_duty_configs_tool
- get_rotation_template_preload_config_tool(template_id)
```

## Recommended Execution Order

1. Fix backend factory regressions.
2. Correct MCP-side constraint knowledge in `domain_context.py`.
3. Add primary duty MCP tools.
4. Add preload-classification MCP tools.
5. Refresh MCP docs and RAG-facing architecture docs.
6. Add tests and smoke checks.

## Definition of Done

The MCP follow-up is done when:

- agents no longer describe primary duty as Airtable/JSON-backed
- agents no longer misclassify ACGME and converted policy constraints as simply "hard"
- MCP can read and mutate primary duty configs
- MCP can inspect and update preload-classification fields on rotation templates
- constraint-related MCP tools work after backend factory fixes
- MCP docs and RAG docs match the actual architecture
