# MCP Usage TODOs for Claude Code CLI

> **Purpose:** Explicit step-by-step instructions for Claude Code to use MCP tools
> **Last Updated:** 2025-12-27

---

## Pre-Flight Checklist (RUN EVERY SESSION)

Before using any MCP tools, Claude Code MUST complete these steps:

### TODO 1: Verify Docker is Running
```bash
docker compose ps
```
**Expected:** All services show "Up" status, especially `mcp-server`, `backend`, `redis`, `db`

**If NOT running:**
```bash
docker compose up -d
```
Wait 30 seconds for services to start.

### TODO 2: Verify MCP Server Health
```bash
docker compose exec mcp-server python -c "from scheduler_mcp.server import mcp; print('MCP OK')"
```
**Expected:** Output shows `MCP OK`

**If FAILS:** Check logs with `docker compose logs mcp-server`

### TODO 3: Verify Backend API Connectivity
```bash
docker compose exec mcp-server curl -s http://backend:8000/health
```
**Expected:** Returns JSON with health status

---

## Using MCP Tools

### Pattern: Schedule Validation

**TODO sequence:**
1. [ ] Verify pre-flight checklist complete
2. [ ] Call `validate_schedule` tool with schedule_id or date range
3. [ ] Check response for violations array
4. [ ] If violations > 0, report to user with severity levels
5. [ ] Log results to `.claude/History/compliance/`

### Pattern: Resilience Check

**TODO sequence:**
1. [ ] Verify pre-flight checklist complete
2. [ ] Call `check_utilization_threshold` tool
3. [ ] Call `run_contingency_analysis` with scenario="n1"
4. [ ] Call `analyze_hub_centrality` to identify critical personnel
5. [ ] Aggregate results into health score
6. [ ] Log results to `.claude/History/resilience/`

### Pattern: Swap Analysis

**TODO sequence:**
1. [ ] Verify pre-flight checklist complete
2. [ ] Call `analyze_swap_candidates` with requester_id and assignment_id
3. [ ] Filter candidates by compatibility_score > 0.7
4. [ ] Check each candidate with `validate_schedule` (simulated swap)
5. [ ] Present ranked options to user
6. [ ] If user approves, call `execute_swap`
7. [ ] Log results to `.claude/History/swaps/`

### Pattern: Schedule Generation

**TODO sequence:**
1. [ ] Verify pre-flight checklist complete
2. [ ] **CRITICAL:** Verify backup exists (check `.claude/History/scheduling/` for recent backup)
3. [ ] If no recent backup, ask user to run backup first
4. [ ] Call `generate_schedule` with date range and algorithm
5. [ ] Call `validate_schedule` on generated schedule
6. [ ] Call `detect_conflicts` on generated schedule
7. [ ] Call `run_contingency_analysis` on generated schedule
8. [ ] Present summary to user
9. [ ] Log results to `.claude/History/scheduling/`

---

## MCP Tool Quick Reference

### Core Scheduling (5 tools)
| Tool | Purpose | Required Params |
|------|---------|-----------------|
| `validate_schedule` | ACGME compliance check | `schedule_id` OR `start_date`, `end_date` |
| `detect_conflicts` | Find double-booking, violations | `start_date`, `end_date` |
| `analyze_swap_candidates` | Find compatible swap partners | `requester_id`, `assignment_id` |
| `generate_schedule` | Create new schedule | `start_date`, `end_date`, `algorithm` |
| `execute_swap` | Execute approved swap | `swap_request_id` |

### Resilience Framework (13 tools)
| Tool | Purpose | Required Params |
|------|---------|-----------------|
| `check_utilization_threshold` | Check 80% threshold | None |
| `get_defense_level` | Current defense tier | None |
| `run_contingency_analysis` | N-1/N-2 simulation | `scenario`, `person_ids` (optional) |
| `get_static_fallbacks` | Pre-computed fallbacks | None |
| `execute_sacrifice_hierarchy` | Load shedding | `target_level`, `simulate` |
| `analyze_homeostasis` | Feedback loops | None |
| `calculate_blast_radius` | Failure containment | `person_id` |
| `analyze_le_chatelier` | Equilibrium analysis | None |
| `analyze_hub_centrality` | Critical personnel | None |
| `assess_cognitive_load` | Decision complexity | None |
| `get_behavioral_patterns` | Preference trails | None |
| `analyze_stigmergy` | Optimization suggestions | None |
| `check_mtf_compliance` | Military compliance | None |

### Background Tasks (4 tools)
| Tool | Purpose | Required Params |
|------|---------|-----------------|
| `start_background_task` | Launch Celery task | `task_type`, `params` |
| `get_task_status` | Poll task progress | `task_id` |
| `cancel_task` | Stop running task | `task_id` |
| `list_active_tasks` | View all tasks | None |

---

## Error Handling TODOs

### If MCP Tool Returns Error

**TODO sequence:**
1. [ ] Check error type (transient vs permanent)
2. [ ] If transient (timeout, connection): retry up to 3 times with 2s delay
3. [ ] If permanent (invalid input, missing resource): report to user
4. [ ] Log error to `.claude/History/incidents/`
5. [ ] If critical operation, suggest rollback

### If Docker Container Not Running

**TODO sequence:**
1. [ ] Run `docker compose up -d`
2. [ ] Wait 30 seconds
3. [ ] Re-run pre-flight checklist
4. [ ] If still failing, check `docker compose logs`
5. [ ] Report specific error to user

### If Backend API Unreachable

**TODO sequence:**
1. [ ] Check if backend container is running: `docker compose ps backend`
2. [ ] Check backend logs: `docker compose logs backend`
3. [ ] Verify database is running: `docker compose ps db`
4. [ ] If all running but still failing, restart: `docker compose restart backend`
5. [ ] Report to user if cannot recover

---

## Logging TODOs

After every MCP operation, Claude Code MUST:

1. [ ] Create timestamp: `YYYY-MM-DD_HHMMSS`
2. [ ] Determine log category: `scheduling`, `swaps`, `compliance`, or `resilience`
3. [ ] Write JSON log to `.claude/History/{category}/`
4. [ ] Update `LATEST.json` symlink if applicable
5. [ ] Include: operation, params, result, duration, any errors

### Log Entry Template
```json
{
  "timestamp": "2025-12-27T10:30:00Z",
  "operation": "validate_schedule",
  "params": {"schedule_id": "SCH-001"},
  "result": {
    "compliant": true,
    "violations": 0,
    "warnings": 2
  },
  "duration_ms": 1250,
  "errors": null
}
```

---

## Integration with CLI (`aapm`)

When user runs CLI commands, Claude Code should:

| CLI Command | MCP Tools to Call |
|-------------|-------------------|
| `aapm schedule validate` | `validate_schedule`, `detect_conflicts` |
| `aapm schedule generate` | (backup check), `generate_schedule`, `validate_schedule` |
| `aapm resilience health` | `check_utilization_threshold`, `get_defense_level` |
| `aapm resilience n1-test` | `run_contingency_analysis` with scenario="n1" |
| `aapm swap find` | `analyze_swap_candidates` |
| `aapm swap execute` | `execute_swap`, then `validate_schedule` |

---

## Safety TODOs (NON-NEGOTIABLE)

### Before Any Write Operation

1. [ ] **VERIFY BACKUP EXISTS** - Check for recent backup (< 2 hours)
2. [ ] **GET USER APPROVAL** - Never auto-execute writes
3. [ ] **LOG PRE-STATE** - Capture before state for rollback

### After Write Operation

1. [ ] **VALIDATE RESULT** - Check ACGME compliance
2. [ ] **LOG OPERATION** - Full audit trail
3. [ ] **OFFER ROLLBACK** - Inform user of rollback window

### Never Do Without Explicit Approval

- Generate schedules
- Execute swaps
- Bulk assign residents
- Modify constraints
- Run database migrations

---

## Session Startup TODO

When starting a new Claude Code session in this repo:

1. [ ] Read `CLAUDE.md` for project context
2. [ ] Read `.claude/CONSTITUTION.md` for rules
3. [ ] Read `.claude/SKILL_INDEX.md` for available skills
4. [ ] Run pre-flight checklist (Docker, MCP, Backend)
5. [ ] Check `.claude/History/*/LATEST.json` for recent state
6. [ ] Ready to accept user commands

---

**END OF MCP USAGE TODOS**

*This file is the authoritative checklist for Claude Code when using MCP tools.*
