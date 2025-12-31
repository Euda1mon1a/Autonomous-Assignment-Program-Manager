***REMOVED*** MCP Tool Usage Guide

> **Comprehensive guide to using Model Context Protocol (MCP) tools for residency scheduling**
>
> **Audience**: Clinicians, administrators, and AI developers
> **Last Updated**: 2025-12-30
> **Version**: 1.0

---

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Architecture & Connection](***REMOVED***architecture--connection)
3. [Tool Categories](***REMOVED***tool-categories)
4. [Getting Started](***REMOVED***getting-started)
5. [Core Scheduling Workflows](***REMOVED***core-scheduling-workflows)
6. [Resilience Monitoring Workflows](***REMOVED***resilience-monitoring-workflows)
7. [Advanced Analytics Workflows](***REMOVED***advanced-analytics-workflows)
8. [Configuration & Authentication](***REMOVED***configuration--authentication)
9. [Error Handling & Troubleshooting](***REMOVED***error-handling--troubleshooting)
10. [Best Practices](***REMOVED***best-practices)
11. [Complete Tool Reference](***REMOVED***complete-tool-reference)

---

***REMOVED******REMOVED*** Overview

***REMOVED******REMOVED******REMOVED*** What is MCP?

Model Context Protocol (MCP) is a standard protocol that allows AI assistants to interact with external tools and data sources. For the Residency Scheduler, MCP provides **97+ tools** that enable AI agents to:

- **Validate schedules** against ACGME compliance rules
- **Detect conflicts** and propose resolutions
- **Monitor resilience** and predict burnout risk
- **Optimize staffing** using cross-disciplinary science
- **Run simulations** for what-if analysis
- **Generate reports** for compliance audits

***REMOVED******REMOVED******REMOVED*** Why Use MCP Tools?

**Traditional Approach:**
```
Clinician → Manual spreadsheet → Email coordinator → Wait for response → Manual fix
```

**MCP-Enabled Approach:**
```
Clinician → Natural language request to AI → MCP tools analyze → Instant insights → Auto-generated fixes
```

**Example Conversation:**
```
User: "Check if next month's schedule violates ACGME work hour rules"
AI: [Uses validate_schedule tool]
    "Found 3 violations:
     - PGY2-03 exceeds 80h/week in week 2 (82.5 hours)
     - PGY1-01 missing 1-in-7 day off in week 3
     - Supervision ratio violated on Jan 15 AM block"
```

***REMOVED******REMOVED******REMOVED*** Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Assistant                                │
│                  (Claude, ChatGPT, etc.)                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ Natural language requests
                     │
┌────────────────────▼────────────────────────────────────────────┐
│                    MCP Server                                    │
│                   (FastMCP Framework)                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │  Scheduling    │  │   Resilience   │  │    Analytics   │    │
│  │     Tools      │  │     Tools      │  │     Tools      │    │
│  │   (8 tools)    │  │   (12 tools)   │  │   (77 tools)   │    │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘    │
│           │                   │                   │             │
│           └───────────────────┼───────────────────┘             │
│                               │                                 │
├───────────────────────────────┼─────────────────────────────────┤
│                               │                                 │
│                    ┌──────────▼──────────┐                      │
│                    │    API Client       │                      │
│                    │  (Authentication)   │                      │
│                    └──────────┬──────────┘                      │
└───────────────────────────────┼─────────────────────────────────┘
                                │
                                │ HTTPS + JWT
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                    Backend API (FastAPI)                         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Scheduling  │  │  Compliance  │  │  Resilience  │          │
│  │    Engine    │  │  Validator   │  │  Framework   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                     │
│                  ┌────────▼────────┐                            │
│                  │    Database     │                            │
│                  │   (PostgreSQL)  │                            │
│                  └─────────────────┘                            │
└──────────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Key Security Features

1. **No Direct Database Access**: MCP server connects via FastAPI backend, not directly to the database
2. **JWT Authentication**: All API calls require valid authentication tokens
3. **Data Sanitization**: PII is filtered through the API layer
4. **Resource Limits**: Container limits prevent runaway processes (1 CPU, 2GB RAM)
5. **Network Isolation**: MCP server runs in isolated Docker network

---

***REMOVED******REMOVED*** Architecture & Connection

***REMOVED******REMOVED******REMOVED*** How MCP Tools Work

**Step-by-step execution flow:**

1. **User Request**: Natural language input to AI assistant
   ```
   "Find faculty who can swap call with Dr. Smith on Jan 15"
   ```

2. **AI Reasoning**: Assistant determines which MCP tool to use
   ```
   Tool: analyze_swap_candidates
   Parameters: person_id="smith-123", block_date="2025-01-15"
   ```

3. **MCP Server**: Receives tool call, validates parameters
   ```python
   ***REMOVED*** Pydantic validation
   request = SwapCandidateRequest(
       person_id="smith-123",
       block_date=date(2025, 1, 15)
   )
   ```

4. **API Client**: Authenticates and calls backend
   ```python
   headers = {"Authorization": f"Bearer {jwt_token}"}
   response = await client.post("/api/v1/schedule/swaps/candidates",
                                 json=request.dict(),
                                 headers=headers)
   ```

5. **Backend Processing**: Query database, run algorithms
   ```sql
   SELECT * FROM persons WHERE id IN (
       SELECT person_id FROM assignments
       WHERE block_id = ? AND rotation_id IN (...)
   )
   ```

6. **Response**: Structured data returned to AI
   ```json
   {
     "candidates": [
       {"name": "Dr. Jones", "compatibility_score": 0.95},
       {"name": "Dr. Lee", "compatibility_score": 0.87}
     ]
   }
   ```

7. **AI Synthesis**: Natural language summary for user
   ```
   "I found 2 compatible swap candidates:
    1. Dr. Jones (95% match) - Same rotation, available
    2. Dr. Lee (87% match) - Cross-rotation swap possible"
   ```

***REMOVED******REMOVED******REMOVED*** Deployment Modes

***REMOVED******REMOVED******REMOVED******REMOVED*** Production Mode (Docker Container)

```bash
***REMOVED*** Start all services including MCP server
docker-compose up -d

***REMOVED*** View MCP server logs
docker-compose logs -f mcp-server

***REMOVED*** Verify MCP server is running
docker-compose exec mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Tools: {len(mcp.tools)}')"
```

**Container Configuration:**
- **Image**: Custom Python image with FastMCP
- **Network**: Internal `app-network` (no external access)
- **Resources**: 1 CPU core, 2GB RAM limit
- **Security**: `no-new-privileges:true`, non-root user
- **Health Check**: HTTP health endpoint on port 8080

***REMOVED******REMOVED******REMOVED******REMOVED*** Development Mode (Local Python)

```bash
***REMOVED*** Install MCP server package
cd mcp-server
pip install -e .

***REMOVED*** Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/residency_scheduler"
export API_BASE_URL="http://localhost:8000"
export API_USERNAME="admin"
export API_PASSWORD="your_password"

***REMOVED*** Run MCP server
python -m scheduler_mcp.server
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Claude Code Integration

**Docker exec (Default - Recommended):**

`.mcp.json`:
```json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "docker",
      "args": ["compose", "exec", "-T", "mcp-server",
               "python", "-m", "scheduler_mcp.server"],
      "transport": "stdio"
    }
  }
}
```

**Local Python (Alternative):**

`.mcp.json`:
```json
{
  "mcpServers": {
    "residency-scheduler-local": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "cwd": "mcp-server/src",
      "disabled": false,
      "env": {
        "API_BASE_URL": "http://localhost:8000",
        "API_USERNAME": "admin",
        "API_PASSWORD": "${SCHEDULER_API_PASSWORD}"
      }
    }
  }
}
```

---

***REMOVED******REMOVED*** Tool Categories

The 97+ MCP tools are organized into 7 categories:

***REMOVED******REMOVED******REMOVED*** 1. Core Scheduling Tools (8 tools)

**Purpose**: Basic schedule operations and validation

| Tool | Purpose | Typical Use Case |
|------|---------|------------------|
| `validate_schedule` | ACGME compliance check | "Is next month's schedule compliant?" |
| `detect_conflicts` | Find double-bookings and violations | "Check for conflicts in Q1" |
| `analyze_swap_candidates` | Find compatible swap matches | "Who can cover Dr. Smith's call?" |
| `run_contingency_analysis` | N-1/N-2 vulnerability assessment | "Can we survive if Dr. Jones deploys?" |
| `start_background_task` | Launch long-running analysis | "Generate full year metrics" |
| `get_task_status` | Poll task completion | "Is the analysis done?" |
| `cancel_task` | Stop running task | "Cancel that slow computation" |
| `list_active_tasks` | View all running tasks | "What's currently running?" |

***REMOVED******REMOVED******REMOVED*** 2. Resilience Framework Tools (12 tools)

**Purpose**: Monitor system health and prevent cascade failures

| Tool | Purpose | Cross-Disciplinary Source |
|------|---------|---------------------------|
| `check_utilization_threshold` | 80% queuing theory threshold | Telecommunications (Erlang) |
| `get_defense_level` | 5-tier defense status | Nuclear Safety |
| `run_contingency_analysis_resilience` | N-1/N-2 analysis | Power Grid Engineering |
| `get_static_fallbacks` | Pre-computed emergency schedules | AWS Static Stability |
| `execute_sacrifice_hierarchy` | Triage-based load shedding | Emergency Medicine |
| `analyze_homeostasis` | Feedback loop monitoring | Human Physiology |
| `calculate_blast_radius` | Failure containment zones | AWS Fault Isolation |
| `analyze_le_chatelier` | Equilibrium shift analysis | Chemistry |
| `analyze_hub_centrality` | Single point of failure detection | Network Theory |
| `assess_cognitive_load` | Decision fatigue (7±2 limit) | Cognitive Psychology |
| `get_behavioral_patterns` | Emergent preferences | Swarm Intelligence |
| `analyze_stigmergy` | Indirect coordination signals | Ant Colony Optimization |

***REMOVED******REMOVED******REMOVED*** 3. Early Warning Tools (4 tools)

**Purpose**: Detect burnout precursors before crisis occurs

| Tool | Purpose | Scientific Basis |
|------|---------|------------------|
| `detect_burnout_precursors` | STA/LTA seismic detection | Earthquake Early Warning (Seismology) |
| `run_spc_analysis` | Western Electric Rules | Semiconductor Manufacturing (Six Sigma) |
| `calculate_fire_danger_index` | Multi-temporal burnout risk | Canadian Forest Fire System (CFFDRS) |
| `calculate_batch_fire_danger` | Bulk FWI analysis | Wildfire Science |

***REMOVED******REMOVED******REMOVED*** 4. Burnout Epidemiology Tools (3 tools)

**Purpose**: Model burnout spread through social networks

| Tool | Purpose | Scientific Basis |
|------|---------|------------------|
| `calculate_burnout_rt` | Reproduction number | Infectious Disease Epidemiology (SIR Models) |
| `simulate_burnout_spread` | Network contagion simulation | Network Epidemiology (NDlib) |
| `identify_superspreaders` | High-centrality nodes | Contact Tracing |

***REMOVED******REMOVED******REMOVED*** 5. Optimization Tools (3 tools)

**Purpose**: Staffing and schedule quality optimization

| Tool | Purpose | Scientific Basis |
|------|---------|------------------|
| `optimize_erlang_coverage` | Queuing-based staffing | Telecommunications (Erlang C) |
| `calculate_process_capability` | Six Sigma quality metrics | Manufacturing (Cp/Cpk) |
| `assess_schedule_fairness` | Equity analysis | Operations Research |

***REMOVED******REMOVED******REMOVED*** 6. Composite Resilience Tools (4 tools)

**Purpose**: Unified risk scores from multiple analytics

| Tool | Purpose | Components |
|------|---------|------------|
| `get_unified_critical_index` | Single 0-100 risk score | Utilization + Defense + Rt + Fire Index |
| `assess_creep_fatigue` | Materials science fatigue | Larson-Miller Parameter |
| `calculate_recovery_distance` | Minimum edits to recover | Operations Research |
| `analyze_transcription_triggers` | Genetic regulatory networks | Molecular Biology |

***REMOVED******REMOVED******REMOVED*** 7. Exotic Research Tools (20 tools)

**Purpose**: Cutting-edge cross-disciplinary analytics

| Tool Category | Tools | Scientific Basis |
|---------------|-------|------------------|
| **Kalman Filter** | 2 tools | Control Theory (noise filtering, trend extraction) |
| **Fourier/FFT** | 3 tools | Signal Processing (cycle detection, harmonic resonance) |
| **Game Theory** | 3 tools | Economics (Nash equilibria, swap prediction) |
| **Value-at-Risk** | 4 tools | Financial Engineering (probabilistic risk bounds) |
| **Lotka-Volterra** | 4 tools | Ecology (predator-prey supply/demand cycles) |
| **Hopfield Attractor** | 4 tools | Neuroscience (energy landscape, stable patterns) |

***REMOVED******REMOVED******REMOVED*** 8. Circuit Breaker Tools (4 tools)

**Purpose**: Service resilience and fault tolerance

| Tool | Purpose | Pattern |
|------|---------|---------|
| `check_circuit_breakers` | View all breaker states | Circuit Breaker Pattern |
| `get_breaker_health` | Health metrics and history | Observability |
| `test_half_open_breaker` | Manual recovery test | Circuit Breaker Pattern |
| `override_circuit_breaker` | Force open/close (emergency) | Manual Override |

***REMOVED******REMOVED******REMOVED*** 9. Deployment Tools (7 tools)

**Purpose**: CI/CD and deployment validation

| Tool | Purpose | Use Case |
|------|---------|----------|
| `get_deployment_status` | Current deployment info | "What's running in prod?" |
| `list_deployments` | Historical deployments | "Show staging deployments" |
| `validate_deployment` | Pre-deploy checks | "Can I deploy to prod?" |
| `run_smoke_tests` | Post-deploy validation | "Verify staging works" |
| `run_security_scan` | Vulnerability scanning | "Any security issues?" |
| `promote_to_production` | Deploy to production | "Push staging to prod" |
| `rollback_deployment` | Emergency rollback | "Revert last deploy" |

---

***REMOVED******REMOVED*** Getting Started

***REMOVED******REMOVED******REMOVED*** Prerequisites

Before using MCP tools, ensure:

1. **Backend API is running**:
   ```bash
   docker-compose up -d backend
   curl http://localhost:8000/health
   ***REMOVED*** Should return: {"status": "healthy"}
   ```

2. **MCP server is running**:
   ```bash
   docker-compose up -d mcp-server
   docker-compose logs mcp-server | grep "Tools:"
   ***REMOVED*** Should show: Tools: 97
   ```

3. **API credentials are configured**:
   ```bash
   ***REMOVED*** Check .env file has:
   API_USERNAME=admin
   API_PASSWORD=your_secure_password
   ```

4. **Claude Code is configured**:
   ```bash
   ***REMOVED*** Verify .mcp.json exists
   cat .mcp.json
   ```

***REMOVED******REMOVED******REMOVED*** First Tool Call (Validation Check)

**Natural language request:**
```
"Check if the schedule from January 1-31, 2025 is ACGME compliant"
```

**What happens behind the scenes:**

1. AI recognizes this needs the `validate_schedule` tool
2. MCP server receives call with parameters:
   ```json
   {
     "start_date": "2025-01-01",
     "end_date": "2025-01-31",
     "check_work_hours": true,
     "check_supervision": true,
     "check_rest_periods": true
   }
   ```
3. API client authenticates and calls backend
4. Backend runs ACGME validator
5. Response returned:
   ```json
   {
     "is_valid": false,
     "overall_compliance_rate": 0.92,
     "total_issues": 5,
     "critical_issues": 2,
     "issues": [...]
   }
   ```
6. AI synthesizes natural language response

**Expected AI response:**
```
The January schedule has 5 ACGME compliance issues:

CRITICAL ISSUES (2):
• PGY2-03: 80-hour rule violated in week 2 (worked 82.5 hours)
• PGY1-01: Missing 1-in-7 rest period in week 3

WARNINGS (3):
• Low supervision ratio on Jan 15 AM (2 PGY-1s with 0 faculty)
• Consecutive duty approaching 28-hour limit: PGY3-02 on Jan 22
• Borderline work hours: PGY2-01 averaged 79.5h in rolling 4-week period

Overall compliance: 92%

Recommendations:
1. Redistribute PGY2-03's hours in week 2
2. Add rest day for PGY1-01 in week 3
3. Ensure faculty coverage on Jan 15 AM
```

***REMOVED******REMOVED******REMOVED*** Understanding Tool Responses

All MCP tools return **structured Pydantic models** that AI assistants parse. Here's what a typical response looks like:

**Raw JSON (what the tool returns):**
```json
{
  "is_valid": false,
  "overall_compliance_rate": 0.92,
  "total_issues": 5,
  "critical_issues": 2,
  "warning_issues": 3,
  "info_issues": 0,
  "issues": [
    {
      "severity": "critical",
      "rule_type": "work_hours",
      "person_id": "abc-123",
      "role": "PGY-2",
      "date_range": ["2025-01-08", "2025-01-14"],
      "message": "Work hours exceeded 80h/week threshold",
      "details": {
        "actual_hours": 82.5,
        "limit": 80.0,
        "violation_margin": 2.5
      },
      "suggested_fix": "Reduce assignment on Jan 13-14 by 3 hours"
    }
  ],
  "validated_at": "2025-01-30T14:32:15Z",
  "date_range": ["2025-01-01", "2025-01-31"]
}
```

**Natural language (what AI shows you):**
```
✗ Schedule validation failed (92% compliant)

Critical Issues (2):
1. PGY-2 worked 82.5 hours in week of Jan 8-14 (limit: 80h)
   → Suggested fix: Reduce Jan 13-14 assignment by 3 hours

2. PGY-1 missing required 24-hour rest period in week 3
   → Suggested fix: Add rest day on Jan 18 or 19
```

---

***REMOVED******REMOVED*** Core Scheduling Workflows

***REMOVED******REMOVED******REMOVED*** Workflow 1: Schedule Validation Before Publication

**Scenario**: You've generated a new schedule and want to ensure ACGME compliance before publishing to residents.

**Step 1: Validate the schedule**
```
"Validate the schedule for Block 10 (April 1 - June 30, 2025)"
```

**Tool used**: `validate_schedule`

**Parameters**:
- `start_date`: "2025-04-01"
- `end_date`: "2025-06-30"
- `check_work_hours`: true
- `check_supervision`: true
- `check_rest_periods`: true
- `check_consecutive_duty`: true

**Expected response**:
```
✓ Schedule is ACGME compliant (100%)

Summary:
• 0 violations detected
• All residents within 80h/week limit
• All 1-in-7 rest periods satisfied
• Supervision ratios maintained
• No consecutive duty violations

Safe to publish.
```

**If violations found:**
```
✗ Schedule has 3 ACGME violations

CRITICAL (must fix before publishing):
1. PGY2-03: 82.5 hours in week of April 15-21 (limit: 80h)
   → Fix: Remove Night Float shift on April 20

2. PGY1-01: No 24-hour rest period from April 8-14
   → Fix: Remove clinic on April 12

WARNINGS (review recommended):
3. PGY3-02: 79.8 hours in week of May 6-12 (approaching limit)
   → Monitor: Consider lightening load if possible
```

***REMOVED******REMOVED******REMOVED*** Workflow 2: Conflict Detection After Leave Approval

**Scenario**: A faculty member just submitted emergency leave. Check if this creates conflicts.

**Step 1: Detect conflicts**
```
"Dr. Smith submitted emergency leave for Jan 15-17. Check for conflicts."
```

**Tool used**: `detect_conflicts`

**Parameters**:
- `start_date`: "2025-01-15"
- `end_date`: "2025-01-17"
- `conflict_types`: ["double_booking", "supervision_gap", "leave_overlap"]
- `include_auto_resolution`: true

**Expected response**:
```
⚠ 2 conflicts detected for Jan 15-17

CONFLICT 1: Supervision Gap
• Date: Jan 15 AM
• Issue: No faculty coverage for 2 PGY-1 residents
• Severity: CRITICAL
• Auto-resolution available: Yes
  → Option 1: Assign Dr. Jones (95% compatible)
  → Option 2: Assign Dr. Lee (87% compatible)

CONFLICT 2: Leave Overlap
• Date: Jan 16
• Issue: Dr. Smith's leave overlaps with Dr. Brown's approved PTO
• Severity: WARNING
• Impact: Clinic coverage thin (only 1 faculty for 4 residents)
• Auto-resolution: No (manual review needed)
```

**Step 2: Auto-resolve if possible**
```
"Apply auto-resolution option 1 for the supervision gap"
```

**Tool used**: (Backend API call via Claude Code)

**Result**:
```
✓ Auto-resolution applied

Changes made:
• Assigned Dr. Jones to Jan 15 AM block
• Updated supervision ratio: 2 PGY-1 → 1 faculty (compliant)
• No ACGME violations created

Remaining conflicts: 1 (manual review needed)
```

***REMOVED******REMOVED******REMOVED*** Workflow 3: Finding Swap Candidates

**Scenario**: Dr. Smith needs to swap their call shift on January 20th. Find compatible candidates.

**Step 1: Analyze swap candidates**
```
"Find swap candidates for Dr. Smith's call shift on January 20"
```

**Tool used**: `analyze_swap_candidates`

**Parameters**:
- `person_id`: "smith-123" (resolved from name)
- `block_date`: "2025-01-20"
- `max_candidates`: 10

**Expected response**:
```
Found 5 compatible swap candidates for Dr. Smith's call (Jan 20):

1. Dr. Jones ⭐⭐⭐⭐⭐ (98% match)
   • Same rotation (Inpatient)
   • Available on Jan 20
   • Recent swap history: 2 this month (not overloaded)
   • Credentials match: BLS, ACLS, PALS ✓
   • Work hours buffer: 15.5h (safe to add shift)

2. Dr. Lee ⭐⭐⭐⭐ (87% match)
   • Cross-rotation (Procedures → Inpatient)
   • Available on Jan 20
   • Credential gap: Needs PALS refresher (expires Feb 1) ⚠
   • Work hours buffer: 8.2h (tight but compliant)

3. Dr. Brown ⭐⭐⭐ (75% match)
   • Same rotation (Inpatient)
   • Partial availability (PM only, not full call)
   • Work hours: Near limit (only 5h buffer)

4-5. [Lower compatibility candidates...]

Recommendation: Dr. Jones is the best match.
```

**Step 2: Execute the swap**
```
"Create a swap request between Dr. Smith and Dr. Jones for Jan 20"
```

(This uses backend API, not an MCP tool directly)

**Result**:
```
✓ Swap request created

Swap Details:
• Type: One-to-one swap
• Dr. Smith gives: Jan 20 Call (12h)
• Dr. Jones gives: Jan 27 Call (12h)
• Status: Pending approval
• Compliance check: ✓ Passed (no ACGME violations)
• Approval required by: Program Director

Next steps:
• Email sent to PD for approval
• 24-hour rollback window after approval
```

***REMOVED******REMOVED******REMOVED*** Workflow 4: Contingency Analysis (N-1 Planning)

**Scenario**: Dr. Johnson might be deploying. Can the program survive without them?

**Step 1: Run contingency analysis**
```
"Run N-1 contingency analysis for Dr. Johnson's potential deployment from Feb 1 - May 31"
```

**Tool used**: `run_contingency_analysis`

**Parameters**:
- `scenario`: "faculty_absence"
- `affected_person_ids`: ["johnson-456"]
- `start_date`: "2025-02-01"
- `end_date`: "2025-05-31"
- `auto_resolve`: false (just assess, don't modify)

**Expected response**:
```
⚠ N-1 CONTINGENCY ANALYSIS: Dr. Johnson Deployment

Impact Assessment:
• Duration: 4 months (Feb 1 - May 31)
• Affected Rotations: Inpatient, Procedures, Clinic
• Coverage Gaps: 48 blocks
• Compliance Violations (if unaddressed): 12 critical
• Workload Increase: +18.5% for remaining faculty
• Feasibility Score: 0.45 (MARGINAL - intervention required)

Critical Gaps:
1. Inpatient Call: 16 uncovered shifts
2. Procedures Half-Day: 12 uncovered sessions
3. Supervision Ratio: 8 violations (too many residents per faculty)

Resolution Options:

OPTION 1: Redistribute to Existing Faculty (Recommended)
• Strategy: Increase workload for 4 faculty members
• Affected: Dr. Smith, Dr. Lee, Dr. Brown, Dr. Wilson
• Estimated Effort: HIGH
• Success Probability: 75%
• Details:
  - Dr. Smith: +4 call shifts/month (within ACGME limits)
  - Dr. Lee: +3 clinic days/month
  - Dr. Brown: +2 procedures sessions/month
  - Dr. Wilson: +2 call shifts/month
• ⚠ Warning: Brings Dr. Smith to 95% of work hour limit

OPTION 2: Hire Temporary Coverage
• Strategy: Contract locum tenens for 4 months
• Estimated Cost: $80,000 - $100,000
• Lead Time: 4-6 weeks
• Success Probability: 90%
• Details: Full replacement for Dr. Johnson's schedule

OPTION 3: Reduce Resident Coverage (Not Recommended)
• Strategy: Temporarily reduce supervision ratios
• Compliance Risk: HIGH (ACGME violations)
• Success Probability: 20%
• Details: Would require ACGME waiver

Recommended Action: OPTION 1 (redistribute) with backup plan for OPTION 2 if Dr. Smith shows burnout signs.
```

**Step 2: Simulate option 1**
```
"Simulate the redistribution plan (Option 1). Will it maintain ACGME compliance?"
```

(Uses backend scheduling engine)

**Result**:
```
✓ Simulation complete: Redistribution plan is ACGME compliant

Modified Schedule Summary:
• Dr. Smith: 76.5 avg hours/week (limit: 80h) ✓
• Dr. Lee: 68.2 avg hours/week ✓
• Dr. Brown: 71.0 avg hours/week ✓
• Dr. Wilson: 74.5 avg hours/week ✓
• All 1-in-7 rest periods satisfied ✓
• Supervision ratios maintained ✓

Resilience Metrics:
• Utilization: 81% (above 80% threshold) ⚠
• Defense Level: ORANGE (heightened alert)
• Burnout Rt: 1.15 (spreading burnout risk) ⚠
• Fire Danger Index: MODERATE

⚠ Caution: System is at elevated stress. Monitor closely for:
- Increased swap requests (early warning sign)
- Sick calls (behavioral precursor)
- Decreased morale (survey residents monthly)

Recommended Safeguards:
1. Pre-compute static fallback schedule for N-2 scenario
2. Weekly utilization monitoring
3. Monthly wellness check-ins with Dr. Smith
4. Keep locum contract ready (Option 2 backup)
```

---

***REMOVED******REMOVED*** Resilience Monitoring Workflows

***REMOVED******REMOVED******REMOVED*** Workflow 5: Daily Resilience Health Check

**Scenario**: Program Coordinator runs a daily health check to catch issues early.

**Step 1: Check unified critical index**
```
"What's the current resilience status?"
```

**Tool used**: `get_unified_critical_index`

**Parameters**: (none - uses current date)

**Expected response**:
```
RESILIENCE HEALTH REPORT
Date: 2025-01-30

🟢 OVERALL STATUS: HEALTHY (Score: 32/100)

Component Breakdown:
┌────────────────────────────┬────────┬─────────────┐
│ Component                  │ Score  │ Status      │
├────────────────────────────┼────────┼─────────────┤
│ Utilization (Erlang)       │   75%  │ 🟢 Normal   │
│ Defense Level              │ Level 2│ 🟢 Control  │
│ Burnout Rt (Epidemiology)  │   0.85 │ 🟢 Stable   │
│ Fire Danger Index (CFFDRS) │     18 │ 🟢 Low      │
└────────────────────────────┴────────┴─────────────┘

Unified Critical Index: 32 (🟢 LOW RISK)
Trend: Stable (no change from yesterday)

✓ No immediate concerns
✓ All early warning systems GREEN
✓ No precursor alerts detected

Next scheduled check: 2025-01-31 08:00
```

**Step 2: Check defense level details**
```
"What's the current defense-in-depth level?"
```

**Tool used**: `get_defense_level`

**Parameters**:
- `coverage_rate`: 0.95 (calculated from schedule)

**Expected response**:
```
DEFENSE-IN-DEPTH STATUS

Current Level: 2 (CONTROL)
Coverage Rate: 95%

Level Descriptions:
1. PREVENTION (100% coverage)
   • Design to prevent problems before they occur
   • Full staffing, optimal schedules

2. CONTROL (90-99% coverage) ← YOU ARE HERE
   • Detect and respond to emerging issues
   • Minor gaps, active monitoring
   • Actions: Weekly utilization checks, swap auto-matching

3. SAFETY_SYSTEMS (80-89% coverage)
   • Automated safety responses activate
   • Moderate gaps, load shedding triggers
   • Actions: Activate sacrifice hierarchy (yellow level)

4. CONTAINMENT (70-79% coverage)
   • Limit damage spread to zones
   • Severe gaps, blast radius isolation
   • Actions: Restrict cross-zone borrowing

5. EMERGENCY (<70% coverage)
   • Crisis response mode
   • Critical gaps, system failure imminent
   • Actions: Deploy static fallback schedules

Assessment: Operating normally with active monitoring.
```

***REMOVED******REMOVED******REMOVED*** Workflow 6: Early Warning Detection

**Scenario**: Monitor residents for early signs of burnout.

**Step 1: Check STA/LTA precursors**
```
"Check PGY2-03 for burnout precursors in the last 30 days"
```

**Tool used**: `detect_burnout_precursors`

**Parameters**:
- `resident_id`: "pgy2-03-id"
- `signal_type`: "swap_requests"
- `time_series`: [0, 1, 0, 1, 0, 2, 3, 5, 7, 8] (last 30 days of swap requests)
- `short_window`: 5 (5-day moving average)
- `long_window`: 30 (30-day baseline)

**Expected response**:
```
⚠ PRECURSOR ALERT DETECTED

Resident: PGY2-03
Signal: Swap Request Frequency
Analysis Period: Last 30 days

🔴 ELEVATED RISK DETECTED

STA/LTA Analysis:
• Max STA/LTA Ratio: 4.2 (trigger threshold: 3.0)
• Alerts Detected: 2
• Severity: ELEVATED (approaching critical)

Alert Timeline:
1. Day 25: STA/LTA = 3.5 (WARNING)
   • 5-day average: 5.2 requests/day
   • 30-day baseline: 1.5 requests/day
   • Interpretation: Sudden increase in swap requests

2. Day 28: STA/LTA = 4.2 (ELEVATED)
   • 5-day average: 6.8 requests/day
   • 30-day baseline: 1.6 requests/day
   • Interpretation: Sustained elevated swap behavior

Behavioral Pattern:
• Baseline: 1-2 swap requests/month (normal)
• Recent: 8 swap requests in last 5 days (abnormal)
• This is a classic burnout precursor signal

Recommended Actions:
1. IMMEDIATE: Schedule wellness check-in with PGY2-03
2. URGENT: Review recent work hour data (possible overwork)
3. Monitor: Check for other precursor signals (sick calls, response delays)
4. Intervention: Consider temporary workload reduction
5. Follow-up: Re-assess in 7 days

Comparison to Peers:
• PGY2 Cohort Average: 2.1 swaps/month
• PGY2-03: 8 swaps in 5 days (4x normal)

⚠ This pattern precedes burnout in 78% of historical cases.
Early intervention recommended.
```

**Step 2: Check SPC work hour analysis**
```
"Run SPC analysis on PGY2-03's work hours for the last 8 weeks"
```

**Tool used**: `run_spc_analysis`

**Parameters**:
- `resident_id`: "pgy2-03-id"
- `weekly_hours`: [62, 65, 68, 72, 74, 76, 78, 79.5]
- `target_hours`: 60.0
- `sigma`: 5.0

**Expected response**:
```
⚠ SPC ANALYSIS: PROCESS OUT OF CONTROL

Resident: PGY2-03
Analysis Period: 8 weeks
Target: 60 hours/week (σ = 5.0)

🔴 WESTERN ELECTRIC VIOLATIONS: 3

Violation 1: RULE 2 (CRITICAL)
• Rule: 2 of 3 consecutive points beyond 2-sigma
• Detected: Weeks 6-8
• Values: 76h, 78h, 79.5h (all above UCL-2σ = 70h)
• Severity: CRITICAL
• Interpretation: Process shift detected - sustained overwork

Violation 2: RULE 3 (WARNING)
• Rule: 4 of 5 consecutive points beyond 1-sigma
• Detected: Weeks 4-8
• Values: 72h, 74h, 76h, 78h, 79.5h (all above UCL-1σ = 65h)
• Severity: WARNING
• Interpretation: Upward trend confirmed

Violation 3: RULE 4 (INFO)
• Rule: 8 consecutive points on same side of centerline
• Detected: All 8 weeks above 60h target
• Severity: INFO
• Interpretation: Persistent above-target workload

Control Limits:
• UCL (3σ): 75 hours/week
• UCL (2σ): 70 hours/week
• UCL (1σ): 65 hours/week
• Centerline: 60 hours/week
• LCL (1σ): 55 hours/week

Actual Statistics:
• Mean: 71.7 hours/week
• Std Dev: 5.8 hours/week
• Trend: +2.5 hours/week (increasing)

Process Capability:
• Cp: 0.85 (INCAPABLE - below 1.0 threshold)
• Cpk: 0.68 (POOR - process not centered)
• Interpretation: Current process cannot reliably stay within 80h limit

🚨 CRITICAL FINDING: PGY2-03 is trending toward ACGME violation

Predicted Violation:
• If trend continues: Will exceed 80h/week in 2 weeks
• Confidence: 85%

Recommended Actions:
1. URGENT: Reduce workload immediately (target: 65-70h/week)
2. Investigate root cause:
   - Excessive call shifts?
   - Inefficient clinic workflows?
   - Covering for absent colleagues?
3. Monitor daily for next 2 weeks
4. Re-run SPC analysis after intervention

Combined Assessment (SPC + STA/LTA):
• Swap requests: ELEVATED (4.2x baseline)
• Work hours: OUT OF CONTROL (trending toward violation)
• Conclusion: IMMINENT BURNOUT RISK

⚠ Immediate intervention required within 48 hours.
```

***REMOVED******REMOVED******REMOVED*** Workflow 7: Burnout Epidemiology

**Scenario**: One resident burned out last month. Will it spread?

**Step 1: Calculate burnout reproduction number**
```
"Calculate burnout Rt after PGY1-02's burnout last month"
```

**Tool used**: `calculate_burnout_rt`

**Parameters**:
- `burnout_cases`: [
    {"resident_id": "pgy1-02", "date": "2025-01-15", "severity": 0.8}
  ]
- `social_network_edges`: (loaded from schedule swap network)
- `recovery_rate`: 0.1 (10% recovery per week)

**Expected response**:
```
BURNOUT EPIDEMIOLOGY REPORT

Reproduction Number (Rt): 1.35
Status: 🔴 SPREADING

Interpretation:
• Rt > 1.0 means burnout is spreading through the network
• Each burned-out resident will cause 1.35 additional burnout cases
• Without intervention, burnout will grow exponentially

SIR Model Projection (Next 4 Weeks):

Week 1:
• Susceptible: 18 residents
• Infected (burned out): 1.35 residents (predicted)
• Recovered: 0.1 residents

Week 2:
• Susceptible: 16.5 residents
• Infected: 2.1 residents
• Recovered: 0.3 residents

Week 4:
• Susceptible: 12 residents
• Infected: 4.5 residents (24% of program)
• Recovered: 0.8 residents

Peak Burnout: Week 6 (5.2 residents, 28%)

Network Analysis:
• Index Case: PGY1-02
• Direct Contacts: 6 residents (high swap frequency)
• High-Risk Contacts:
  - PGY1-03: 8 swaps/month with PGY1-02 (85% infection risk)
  - PGY2-01: 5 swaps/month with PGY1-02 (62% infection risk)
  - PGY1-01: 4 swaps/month with PGY1-02 (48% infection risk)

Transmission Pathways:
1. Emotional contagion via swap coordination
2. Workload redistribution (covering for burned-out colleague)
3. Social network effects (shared complaints, low morale)

Recommended Interventions:

IMMEDIATE (Target: Reduce Rt below 1.0):
1. Isolate PGY1-02 workload (don't redistribute to close contacts)
2. Hire temporary coverage to prevent overwork cascade
3. Wellness check-ins with high-risk contacts (PGY1-03, PGY2-01)

MEDIUM-TERM:
4. Improve working conditions program-wide (reduce Rt)
5. Increase recovery rate (counseling, wellness resources)
6. Break transmission chains (limit swap network density)

Predicted Impact of Interventions:
• With intervention: Rt drops to 0.75 → burnout contained
• Without intervention: Rt stays 1.35 → 28% burnout in 6 weeks

⚠ Urgent action required to prevent burnout epidemic.
```

***REMOVED******REMOVED******REMOVED*** Workflow 8: Fire Danger Index (Multi-Temporal Burnout)

**Scenario**: Assess burnout risk using multi-timescale analysis (like wildfire danger).

**Step 1: Calculate fire danger index**
```
"Calculate burnout fire danger for PGY2-03"
```

**Tool used**: `calculate_fire_danger_index`

**Parameters**:
- `resident_id`: "pgy2-03"
- `recent_hours`: 158.5 (last 2 weeks)
- `monthly_load`: 285.0 (last 3 months average)
- `yearly_satisfaction`: 0.45 (job satisfaction 0-1 scale)
- `workload_velocity`: 2.5 (hours/week increase rate)

**Expected response**:
```
🔥 BURNOUT FIRE DANGER REPORT

Resident: PGY2-03
Overall Danger: VERY HIGH (FWI: 68.2)

🔴 EXTREME BURNOUT RISK - IMMEDIATE ACTION REQUIRED

Component Analysis (Canadian Fire Weather Index):

1. FFMC (Fine Fuel Moisture Code): 85.3
   • Timescale: Last 2 weeks
   • Interpretation: Recent workload (immediate kindling)
   • Hours: 158.5 hours in 2 weeks (79.25 avg/week)
   • Status: 🔴 CRITICAL (approaching 80h limit)
   • Like dry grass: One spark (additional stress) will ignite

2. DMC (Duff Moisture Code): 72.1
   • Timescale: Last 3 months
   • Interpretation: Medium-term accumulation (smoldering ember)
   • Monthly load: 285 hours/month (71.25/week avg)
   • Status: 🟠 HIGH (sustained overwork)
   • Like deep soil dryness: Takes months to accumulate, months to recover

3. DC (Drought Code): 88.7
   • Timescale: Past year
   • Interpretation: Long-term satisfaction erosion (structural dryness)
   • Yearly satisfaction: 0.45 (55% dissatisfaction)
   • Status: 🔴 CRITICAL (severe morale deficit)
   • Like multi-year drought: Deep resilience depletion

4. ISI (Initial Spread Index): 18.5
   • Interpretation: Rate of spread if burnout ignites
   • Workload velocity: +2.5 hours/week
   • Status: 🟠 HIGH (rapid escalation potential)

5. BUI (Buildup Index): 78.4
   • Interpretation: Combined medium + long-term fuel
   • Status: 🔴 CRITICAL (dangerous accumulation)

6. FWI (Fire Weather Index): 68.2
   • Overall Danger: VERY HIGH
   • Percentile: 92nd (worse than 92% of residents)

Danger Class: VERY HIGH (60-80)
Fire Behavior:
• Ignition: Very easy (any additional stressor)
• Spread: Rapid (will escalate quickly)
• Intensity: Severe (major burnout event)
• Suppression: Very difficult (hard to reverse)

Real-World Translation:
• This is the equivalent of "Red Flag Warning" in wildfire terms
• All it takes is one more incident (bad patient outcome, personal crisis, additional call shift)
• Burnout will ignite suddenly and spread rapidly
• Recovery will take months even with intervention

Historical Comparison:
• Similar FWI scores preceded 8 out of 9 burnout crises in past 2 years
• Average time to burnout after reaching FWI > 60: 12 days

Recommended Actions:

🚨 IMMEDIATE (Next 24 Hours):
1. Remove PGY2-03 from all non-essential duties
2. Cancel next week's call shift (find coverage)
3. Mandatory wellness day this week
4. Emergency check-in with Program Director

⏰ URGENT (Next 7 Days):
5. Reduce target hours to 60/week (from current 79)
6. Provide counseling/mental health resources
7. Investigate root causes (excessive call? inefficient workflows?)
8. Implement daily check-ins

📅 SHORT-TERM (Next 30 Days):
9. Monitor weekly with follow-up FWI calculations
10. Target satisfaction improvement (exit interviews, surveys)
11. Redistribute chronic workload issues
12. Build recovery plan (aim for FWI < 40)

Without Intervention:
• Predicted burnout: 85% chance in next 2 weeks
• Predicted severity: Severe (may leave program)
• Predicted spread: High (Rt = 1.35 from earlier analysis)

With Intervention:
• Predicted FWI in 30 days: 42 (HIGH → MODERATE)
• Recovery timeline: 3-4 months to reach LOW
• Success rate: 70% if actions taken immediately

⚠ This is a fire weather RED FLAG WARNING.
Do NOT ignore. Act within 24 hours.
```

---

***REMOVED******REMOVED*** Advanced Analytics Workflows

***REMOVED******REMOVED******REMOVED*** Workflow 9: Kalman Filter Trend Analysis

**Scenario**: Workload data is noisy. Extract the true underlying trend.

**Step 1: Analyze workload trend**
```
"Filter PGY2-03's noisy workload data and predict next 5 weeks"
```

**Tool used**: `analyze_workload_trend`

**Parameters**:
- `workload_history`: [58, 62, 59, 67, 61, 71, 68, 75, 72, 78, 74, 79.5]
- `process_noise`: 1.0
- `measurement_noise`: 2.0
- `prediction_steps`: 5

**Expected response**:
```
KALMAN FILTER WORKLOAD ANALYSIS

Raw Data (Noisy):
Week:  1    2    3    4    5    6    7    8    9   10   11   12
Hours: 58   62   59   67   61   71   68   75   72   78   74  79.5

Filtered Data (True Trend):
Week:  1    2    3    4    5    6    7    8    9   10   11   12
Hours: 58.2 60.1 61.3 63.2 64.5 66.8 68.1 70.5 72.0 74.2 75.8 77.3

Predictions (Next 5 Weeks):
Week: 13   14   15   16   17
Hours: 78.5 79.8 81.2 82.5 83.9

95% Confidence Intervals:
Week 13: [76.8, 80.2]
Week 14: [77.5, 82.1]
Week 15: [78.1, 84.3]
Week 16: [78.5, 86.5]
Week 17: [78.8, 89.0]

Trend Analysis:
• Direction: INCREASING
• Strength: 0.89 (STRONG upward trend)
• Smoothness: 0.85 (consistent increase, not erratic)
• Average increase: +1.6 hours/week

🚨 CRITICAL FINDING: Predicted ACGME Violation

• Week 15 (3 weeks from now): 81.2 hours (violates 80h limit)
• Confidence: 75% (upper bound of 95% CI exceeds 80h)
• Weeks 16-17: High probability of sustained violations

Interpretation:
The noisy raw data obscures a clear upward trend. After filtering noise, the Kalman filter reveals PGY2-03 is on a collision course with ACGME limits.

Recommended Actions:
1. Immediate workload reduction (target: 70h/week)
2. Investigate root cause of +1.6h/week increase
3. Re-measure in 2 weeks to confirm trend reversal

Comparison to SPC Analysis:
• SPC detected "out of control" in weeks 6-8
• Kalman filter confirms this is not random noise but a real trend
• Prediction aligns with SPC forecast (violation in 2 weeks)
```

***REMOVED******REMOVED******REMOVED*** Workflow 10: Fourier Cycle Detection

**Scenario**: Detect natural cycles in schedule patterns to align with ACGME windows.

**Step 1: Detect schedule cycles**
```
"Analyze daily swap request frequency for the last 60 days to find cycles"
```

**Tool used**: `detect_schedule_cycles`

**Parameters**:
- `signal`: [daily swap counts for 60 days]
- `sampling_period_days`: 1.0
- `top_n_periods`: 5

**Expected response**:
```
FOURIER ANALYSIS: SCHEDULE CYCLES

Dominant Period: 7.2 days
Periodicity Detected: ✓ Yes (strong weekly cycle)

Top 5 Detected Periods:

1. 7.2 days ⭐⭐⭐⭐⭐
   • Power: 245.3
   • Interpretation: Weekly cycle
   • Alignment: Matches 7-day ACGME rest period
   • Recommendation: Align schedule changes to week boundaries

2. 14.1 days ⭐⭐⭐⭐
   • Power: 87.6
   • Interpretation: Bi-weekly pattern
   • Alignment: Half of 28-day ACGME window
   • Recommendation: Use for bi-weekly rotation changes

3. 28.3 days ⭐⭐⭐
   • Power: 52.1
   • Interpretation: Monthly cycle
   • Alignment: Matches 28-day ACGME work hour window
   • Recommendation: Schedule major changes on 28-day boundaries

4. 3.5 days ⭐⭐
   • Power: 31.2
   • Interpretation: Mid-week surge
   • Likely cause: Wednesday/Thursday swap requests peak
   • Recommendation: Batch swap processing on Thursdays

5. 5.8 days ⭐
   • Power: 18.7
   • Interpretation: Workweek cycle (Mon-Fri)
   • Likely cause: Administrative work happens weekdays

Signal-to-Noise Ratio: 4.7 (STRONG signal)

Implications for Scheduling:
✓ Current schedule naturally aligns with ACGME 7-day and 28-day windows
✓ Residents prefer weekly rhythms (biological/social circadian)
✓ No dissonant frequencies detected (schedule is harmonious)

Recommendations:
1. Preserve 7-day cycle structure (don't break weekly patterns)
2. Avoid schedule changes mid-week (conflicts with 7.2-day cycle)
3. Align rotation changes to 28-day boundaries
4. Batch administrative work on Thursdays (3.5-day cycle peak)
```

***REMOVED******REMOVED******REMOVED*** Workflow 11: Game Theory Swap Prediction

**Scenario**: Predict which residents will request swaps before they ask.

**Step 1: Analyze Nash stability**
```
"Analyze schedule stability for next month - will residents want to swap?"
```

**Tool used**: `analyze_nash_stability`

**Parameters**:
- `schedule_matrix`: [assignment data for next month]
- `preference_matrix`: [resident preferences]

**Expected response**:
```
GAME THEORY ANALYSIS: SCHEDULE STABILITY

Nash Equilibrium Status: ⚠ UNSTABLE (56% stable)

Overall Stability:
• Stable residents: 11 out of 19 (58%)
• Unstable residents: 8 (42%)
• Expected swap requests: 12-15
• Confidence: 78%

Unstable Assignments (Deviation Incentives):

1. PGY2-03: Inpatient Week 3 → Clinic
   • Current utility: 4.2
   • Preferred utility: 7.8 (clinic)
   • Deviation incentive: +3.6 (STRONG)
   • Prediction: Will request swap with 85% probability
   • Suggested match: PGY2-01 (wants inpatient, currently on clinic)

2. PGY1-02: Call Friday → Call Wednesday
   • Current utility: 3.1
   • Preferred utility: 6.5 (Wednesday call easier to cover)
   • Deviation incentive: +3.4 (STRONG)
   • Prediction: Will request swap with 80% probability

3. PGY3-01: Procedures AM → Procedures PM
   • Current utility: 5.2
   • Preferred utility: 7.0 (PM fits childcare)
   • Deviation incentive: +1.8 (MODERATE)
   • Prediction: Will request swap with 55% probability

[5 more unstable assignments...]

Blocked Pareto Improvements:
• PGY2-03 ↔ PGY2-01 swap would benefit BOTH (win-win)
• Currently blocked by administrative friction
• Recommendation: Auto-approve this swap (no downside)

Coordination Failures:
• 3 pairs of residents want each other's assignments
• They don't know this (lack of information)
• Recommendation: Show "mutual interest" notifications

Proactive Recommendations:

IMMEDIATE:
1. Pre-approve PGY2-03 ↔ PGY2-01 swap (Pareto improvement)
2. Notify 3 pairs of mutual swap interest
3. Expect 12-15 swap requests next month (prepare coordinator)

STRATEGIC:
4. Collect preference data earlier (improve initial schedule)
5. Use preference-aware scheduling algorithm
6. Target 80%+ Nash stability (currently 56%)

Comparison to Last Month:
• Last month stability: 68% → 12 swaps
• This month stability: 56% → predicted 15 swaps (25% increase)
• Root cause: More call shifts (less flexible)
```

***REMOVED******REMOVED******REMOVED*** Workflow 12: Value-at-Risk (Coverage Risk)

**Scenario**: What's the probability of a coverage gap next month?

**Step 1: Calculate coverage VaR**
```
"What's the 95th percentile coverage gap risk for February?"
```

**Tool used**: `calculate_coverage_var`

**Parameters**:
- `coverage_history`: [daily coverage rates for last 180 days]
- `confidence_level`: 0.95
- `forecast_horizon_days`: 28

**Expected response**:
```
VALUE-AT-RISK ANALYSIS: COVERAGE GAPS

Coverage VaR (95% confidence): 2.3 uncovered blocks/day

Interpretation:
• 95% of days will have ≤ 2.3 uncovered blocks
• 5% of days will have > 2.3 uncovered blocks (tail risk)
• Expected worst day: 4.1 uncovered blocks
• Probability of ANY gap: 18%

Distribution Analysis:
• Mean coverage: 99.2%
• Standard deviation: 1.8%
• 5th percentile (best): 100% coverage
• 50th percentile (median): 99.5% coverage
• 95th percentile (VaR): 95.2% coverage (2.3 blocks short)
• 99th percentile (CVaR): 92.1% coverage (4.1 blocks short)

Historical Context:
• Last 6 months VaR: 1.8 blocks/day
• Current forecast: 2.3 blocks/day (28% worse)
• Trend: INCREASING risk

Risk Decomposition (What drives gaps?):
1. Faculty absence (40% of risk)
   • Sick leave: 15%
   • PTO: 12%
   • TDY/Deployment: 13%

2. Resident absence (35% of risk)
   • Sick leave: 20%
   • Conference: 10%
   • Parental leave: 5%

3. Schedule conflicts (25% of risk)
   • Double-bookings: 10%
   • Swap failures: 8%
   • Late cancellations: 7%

High-Risk Days (February):
• Feb 17 (President's Day): 4.8 blocks at risk (holiday effect)
• Feb 14 (Valentine's Day): 3.2 blocks at risk (high PTO)
• Feb 28 (End of month): 3.1 blocks at risk (rotation turnover)

Monte Carlo Simulation (10,000 scenarios):
• Best case (5th percentile): 0.2 blocks/day avg
• Expected case (50th): 1.1 blocks/day avg
• Worst case (95th): 2.3 blocks/day avg
• Catastrophic (99th): 4.1 blocks/day avg

Recommended Actions:

IMMEDIATE:
1. Pre-staff high-risk days (Feb 14, 17, 28)
2. Restrict PTO on Feb 17 (3 faculty already approved)
3. Activate on-call backup for Feb 17

STRATEGIC:
4. Target VaR < 1.5 blocks/day (reduce from 2.3)
5. Build 20% buffer capacity (currently 5%)
6. Improve absence prediction (use historical patterns)

Cost-Benefit:
• Cost of 1 extra faculty: $500/day
• Cost of uncovered block: $2,000/block (locum rate)
• Expected savings: 2.3 blocks/day × 5% days × $2,000 = $6,440/month
• ROI: 29% (hire 1 extra faculty on high-risk days)
```

***REMOVED******REMOVED******REMOVED*** Workflow 13: Lotka-Volterra Supply/Demand Cycles

**Scenario**: Predict future coverage crunch using predator-prey dynamics.

**Step 1: Analyze supply/demand cycles**
```
"Analyze the last year of coverage data to predict future crunches"
```

**Tool used**: `analyze_supply_demand_cycles`

**Parameters**:
- `faculty_count_history`: [weekly faculty counts for 52 weeks]
- `demand_history`: [weekly coverage demand for 52 weeks]

**Expected response**:
```
LOTKA-VOLTERRA ANALYSIS: SUPPLY/DEMAND DYNAMICS

Predator-Prey Model Fit: ✓ Strong (R² = 0.87)

Equations:
• dF/dt = αF - βFD   (Faculty dynamics)
• dD/dt = δFD - γD   (Demand dynamics)

Where:
• F = Faculty supply
• D = Coverage demand
• α = 0.05 (faculty growth rate)
• β = 0.02 (demand suppression effect)
• δ = 0.03 (demand growth from faculty availability)
• γ = 0.08 (demand decay rate)

Equilibrium Point:
• F* = 18.5 faculty (stable level)
• D* = 42.3 blocks/week (stable demand)

Current State:
• F = 16 faculty (13.5% BELOW equilibrium) ⚠
• D = 45 blocks/week (6.4% ABOVE equilibrium) ⚠

Status: 🔴 UNSTABLE (oscillating around equilibrium)

Predicted Oscillation:

Next 6 Months Forecast:
┌────────┬──────────┬────────┬─────────────────┐
│ Month  │ Faculty  │ Demand │ Coverage Status │
├────────┼──────────┼────────┼─────────────────┤
│ Feb    │   15.8   │  46.2  │ 🔴 CRUNCH       │
│ Mar    │   15.2   │  47.8  │ 🔴 SEVERE CRUNCH│
│ Apr    │   15.0   │  48.5  │ 🔴 PEAK CRISIS  │
│ May    │   15.5   │  47.1  │ 🟠 CRUNCH       │
│ Jun    │   16.8   │  44.2  │ 🟡 TIGHT        │
│ Jul    │   18.2   │  41.5  │ 🟢 RECOVERY     │
└────────┴──────────┴────────┴─────────────────┘

Peak Crisis: April (15.0 faculty, 48.5 blocks/week)
• Coverage ratio: 3.23 blocks/faculty (unsustainable)
• Predicted gap: 6.5 uncovered blocks/week
• Staff will be overworked → expect burnout surge

Recovery: July (18.2 faculty, 41.5 blocks/week)
• Coverage ratio: 2.28 blocks/faculty (healthy)
• Predicted gap: 0.2 uncovered blocks/week

Oscillation Period: 9.2 months
• This is a natural boom-bust cycle
• Driven by delayed feedback (hiring lags demand by 3 months)

Root Causes:
1. Faculty hiring is reactive (not predictive)
2. 3-month hiring delay creates phase lag
3. Demand spikes are not anticipated (PCS season, deployments)

Intervention Scenarios:

SCENARIO 1: Hire 3 faculty in February
• Effect: Dampen oscillation amplitude by 40%
• April crisis: 6.5 → 4.0 uncovered blocks
• Cost: $450,000/year (3 faculty)

SCENARIO 2: Reduce demand (sacrifice hierarchy)
• Effect: Lower equilibrium demand from 42 → 38 blocks/week
• April crisis: 6.5 → 3.2 uncovered blocks
• Cost: Reduced non-essential services

SCENARIO 3: Improve hiring speed (2-month lead time)
• Effect: Reduce phase lag, stabilize oscillations
• Long-term: Smaller, faster cycles (easier to manage)

Recommended Strategy: COMBINATION
1. Immediate: Hire 2 faculty in February (partial SCENARIO 1)
2. Medium-term: Implement sacrifice hierarchy (SCENARIO 2)
3. Long-term: Predictive hiring (SCENARIO 3)

Expected Outcome:
• April crisis: 6.5 → 2.1 uncovered blocks (68% reduction)
• Stabilize system within 12 months
• Prevent future boom-bust cycles
```

---

***REMOVED******REMOVED*** Configuration & Authentication

***REMOVED******REMOVED******REMOVED*** Environment Variables

**Required for all deployments:**

```bash
***REMOVED*** Backend API connection
API_BASE_URL=http://backend:8000  ***REMOVED*** Docker: use service name
                                   ***REMOVED*** Local: http://localhost:8000

***REMOVED*** Authentication credentials
API_USERNAME=admin                 ***REMOVED*** Scheduler API username
API_PASSWORD=your_secure_password  ***REMOVED*** REQUIRED: Must be set

***REMOVED*** Database (if using direct DB access - not recommended)
DATABASE_URL=postgresql://user:password@db:5432/residency_scheduler
```

**Optional configuration:**

```bash
***REMOVED*** Timeouts and limits
API_TIMEOUT=30.0                   ***REMOVED*** Request timeout in seconds
MAX_CONCURRENT_TASKS=10            ***REMOVED*** Max parallel background tasks

***REMOVED*** Celery (for async task management)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

***REMOVED*** Logging
LOG_LEVEL=INFO                     ***REMOVED*** DEBUG, INFO, WARNING, ERROR
MCP_LOG_FILE=/var/log/mcp-server.log

***REMOVED*** Security
MCP_RATE_LIMIT=100                 ***REMOVED*** Max requests per minute
MCP_ENABLE_AUDIT_LOG=true          ***REMOVED*** Log all tool invocations
```

***REMOVED******REMOVED******REMOVED*** Docker Configuration

**docker-compose.yml:**

```yaml
services:
  mcp-server:
    build:
      context: ./mcp-server
      dockerfile: Dockerfile
    container_name: scheduler-mcp
    restart: unless-stopped

    ***REMOVED*** Environment variables
    environment:
      - API_BASE_URL=http://backend:8000
      - API_USERNAME=${API_USERNAME}
      - API_PASSWORD=${API_PASSWORD}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO

    ***REMOVED*** Resource limits
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

    ***REMOVED*** Security
    security_opt:
      - no-new-privileges:true
    user: "mcp:mcp"  ***REMOVED*** Non-root user

    ***REMOVED*** Network
    networks:
      - app-network

    ***REMOVED*** Health check
    healthcheck:
      test: ["CMD", "python", "-c", "from scheduler_mcp.server import mcp; exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3

    ***REMOVED*** Dependencies
    depends_on:
      - backend
      - redis

networks:
  app-network:
    driver: bridge
    internal: false  ***REMOVED*** Allow external access for Claude Code
```

***REMOVED******REMOVED******REMOVED*** Authentication Flow

**Step-by-step JWT authentication:**

1. **MCP server starts**: Loads credentials from environment
   ```python
   config = APIConfig(
       base_url=os.environ["API_BASE_URL"],
       username=os.environ["API_USERNAME"],
       password=os.environ["API_PASSWORD"]
   )
   ```

2. **First tool call**: Triggers login
   ```python
   ***REMOVED*** Auto-login on first request
   response = await client.post(
       "/api/v1/auth/login/json",
       json={"username": username, "password": password}
   )
   token = response.json()["access_token"]
   ```

3. **Token caching**: Stored in memory for session
   ```python
   self._token = token  ***REMOVED*** Valid for 24 hours
   ```

4. **Subsequent calls**: Use cached token
   ```python
   headers = {"Authorization": f"Bearer {self._token}"}
   response = await client.get("/api/v1/...", headers=headers)
   ```

5. **Token refresh**: Auto-refresh on 401 Unauthorized
   ```python
   if response.status_code == 401:
       await self._login()  ***REMOVED*** Re-authenticate
       ***REMOVED*** Retry request with new token
   ```

***REMOVED******REMOVED******REMOVED*** Security Best Practices

**DO:**
✓ Use strong passwords (min 12 characters, mixed case, numbers, symbols)
✓ Rotate API credentials every 90 days
✓ Use environment variables (never hardcode credentials)
✓ Enable audit logging (`MCP_ENABLE_AUDIT_LOG=true`)
✓ Review audit logs monthly
✓ Run MCP server in isolated Docker network
✓ Use HTTPS for production (terminate SSL at load balancer)

**DON'T:**
✗ Commit credentials to git (use .env, add to .gitignore)
✗ Share API credentials across environments (dev ≠ prod)
✗ Disable security features (keep `no-new-privileges:true`)
✗ Run MCP server as root user
✗ Expose MCP server directly to internet (use VPN or firewall)

---

***REMOVED******REMOVED*** Error Handling & Troubleshooting

***REMOVED******REMOVED******REMOVED*** Common Error Codes

| Error Code | Meaning | Common Causes | How to Fix |
|------------|---------|---------------|------------|
| `SERVICE_UNAVAILABLE` | Backend API is down | Docker container stopped, network issue | Check `docker-compose ps`, restart backend |
| `AUTHENTICATION_FAILED` | Login failed | Wrong username/password, expired token | Verify `.env` credentials, check API logs |
| `VALIDATION_ERROR` | Invalid parameters | Wrong date format, missing required field | Check tool documentation, fix parameters |
| `TIMEOUT` | Operation took too long | Complex query, database slow | Increase `API_TIMEOUT`, optimize query |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Rapid-fire tool calls | Slow down, batch operations |
| `NOT_FOUND` | Resource doesn't exist | Invalid ID, deleted entity | Verify ID exists in database |
| `CIRCUIT_OPEN` | Circuit breaker tripped | Repeated failures | Wait for circuit to close (30-60s), fix root cause |

***REMOVED******REMOVED******REMOVED*** Error Response Format

All MCP tool errors follow this structure:

```json
{
  "error_code": "SERVICE_UNAVAILABLE",
  "message": "Backend API is not responding",
  "details": {
    "api_url": "http://backend:8000",
    "timeout": 30.0,
    "retry_count": 3
  },
  "retry_after": 60,
  "correlation_id": "abc-123-def-456",
  "timestamp": "2025-01-30T14:32:15Z"
}
```

**Fields:**
- `error_code`: Machine-readable error type (see table above)
- `message`: Human-readable explanation
- `details`: Additional context (safe to show users)
- `retry_after`: Seconds to wait before retrying (optional)
- `correlation_id`: Unique ID for tracing logs
- `timestamp`: When error occurred

***REMOVED******REMOVED******REMOVED*** Troubleshooting Workflows

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem: "Backend API is unavailable"

**Symptoms:**
```
Error: SERVICE_UNAVAILABLE
Backend API is not responding at http://backend:8000
```

**Diagnosis:**
```bash
***REMOVED*** Check if backend is running
docker-compose ps backend

***REMOVED*** Check backend logs
docker-compose logs backend | tail -50

***REMOVED*** Test backend health endpoint
curl http://localhost:8000/health
```

**Common causes:**
1. Backend container crashed → `docker-compose restart backend`
2. Database connection failed → `docker-compose logs db`
3. Network issue → `docker network inspect scheduler_app-network`

**Fix:**
```bash
***REMOVED*** Restart backend
docker-compose restart backend

***REMOVED*** If that doesn't work, full restart
docker-compose down
docker-compose up -d

***REMOVED*** Verify health
curl http://localhost:8000/health
***REMOVED*** Should return: {"status": "healthy"}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem: "Authentication failed"

**Symptoms:**
```
Error: AUTHENTICATION_FAILED
Invalid username or password
```

**Diagnosis:**
```bash
***REMOVED*** Check environment variables
docker-compose exec mcp-server env | grep API

***REMOVED*** Check backend user exists
docker-compose exec backend python -c \
  "from app.db.session import SessionLocal; \
   from app.models.person import Person; \
   db = SessionLocal(); \
   users = db.query(Person).filter(Person.role == 'ADMIN').all(); \
   print([u.username for u in users])"
```

**Common causes:**
1. Wrong password in `.env`
2. User doesn't exist in database
3. User account disabled

**Fix:**
```bash
***REMOVED*** Option 1: Reset password via CLI
docker-compose exec backend python scripts/reset_admin_password.py

***REMOVED*** Option 2: Create new admin user
docker-compose exec backend python scripts/create_admin.py \
  --username admin \
  --password "your_secure_password"

***REMOVED*** Update .env file
echo "API_USERNAME=admin" >> .env
echo "API_PASSWORD=your_secure_password" >> .env

***REMOVED*** Restart MCP server to pick up new credentials
docker-compose restart mcp-server
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem: "Tool execution timeout"

**Symptoms:**
```
Error: TIMEOUT
Operation exceeded 30 second timeout
```

**Diagnosis:**
```bash
***REMOVED*** Check which tool is slow
docker-compose logs mcp-server | grep "TIMEOUT"

***REMOVED*** Check database performance
docker-compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT query, state, wait_event, query_start
      FROM pg_stat_activity
      WHERE state != 'idle'
      ORDER BY query_start DESC LIMIT 10;"
```

**Common causes:**
1. Complex query (e.g., analyzing full year of data)
2. Database not indexed properly
3. Too many concurrent requests

**Fix:**
```bash
***REMOVED*** Option 1: Increase timeout
***REMOVED*** In docker-compose.yml, add:
environment:
  - API_TIMEOUT=120.0  ***REMOVED*** Increase from 30 to 120 seconds

***REMOVED*** Option 2: Use background tasks for long operations
"Start a background task for full year resilience analysis"
***REMOVED*** Then poll with:
"What's the status of that task?"

***REMOVED*** Option 3: Optimize database (check indexes)
docker-compose exec backend python scripts/analyze_slow_queries.py
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem: "Rate limit exceeded"

**Symptoms:**
```
Error: RATE_LIMIT_EXCEEDED
Too many requests. Retry after 60 seconds.
```

**Diagnosis:**
```bash
***REMOVED*** Check rate limit settings
docker-compose exec mcp-server env | grep RATE_LIMIT

***REMOVED*** Check request log
docker-compose logs mcp-server | grep "rate_limit" | tail -20
```

**Fix:**
```bash
***REMOVED*** Option 1: Wait 60 seconds (rate limit resets)

***REMOVED*** Option 2: Increase rate limit (if legitimate use)
***REMOVED*** In docker-compose.yml:
environment:
  - MCP_RATE_LIMIT=500  ***REMOVED*** Increase from 100 to 500 req/min

***REMOVED*** Option 3: Batch operations instead of rapid-fire
***REMOVED*** Instead of:
"Check resident 1"
"Check resident 2"
"Check resident 3"
***REMOVED*** Do:
"Check residents 1, 2, and 3 in a single query"
```

***REMOVED******REMOVED******REMOVED*** Logging and Debugging

**Enable debug logging:**

```bash
***REMOVED*** In docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG

***REMOVED*** Restart MCP server
docker-compose restart mcp-server

***REMOVED*** View debug logs
docker-compose logs -f mcp-server
```

**Example debug output:**
```
[2025-01-30 14:32:15] DEBUG - Tool call: validate_schedule
[2025-01-30 14:32:15] DEBUG - Parameters: {
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
[2025-01-30 14:32:15] DEBUG - API call: GET /api/v1/schedule/validate
[2025-01-30 14:32:16] DEBUG - Response: 200 OK (1.23s)
[2025-01-30 14:32:16] DEBUG - Result: {
  "is_valid": false,
  "total_issues": 5
}
```

**Audit log format:**
```
[2025-01-30 14:32:15] AUDIT - user=admin tool=validate_schedule params={"start_date":"2025-01-01"} result=success duration=1.23s
[2025-01-30 14:35:22] AUDIT - user=admin tool=detect_conflicts params={"start_date":"2025-01-15"} result=error error_code=TIMEOUT duration=30.01s
```

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** For Clinicians

**1. Start with validation before publication**
Always validate schedules before publishing to residents:
```
"Validate Block 10 schedule before I publish it"
```

**2. Use early warning tools proactively**
Don't wait for burnout - monitor weekly:
```
"Run SPC analysis on all PGY-2 residents for the last 8 weeks"
```

**3. Check contingency plans for known absences**
Plan ahead for deployments, TDY, parental leave:
```
"Dr. Smith is deploying Feb 1 - May 31. Run N-1 analysis and show me resolution options."
```

**4. Batch swap approvals**
Process swaps in batches, not one-by-one:
```
"Show me all pending swap requests and check each for compliance"
```

**5. Use natural language - don't worry about syntax**
AI will figure out what you mean:
```
✓ "Is next month compliant?"
✓ "Check ACGME rules for Block 10"
✓ "Will we survive if Dr. Jones deploys?"
```

***REMOVED******REMOVED******REMOVED*** For Program Coordinators

**1. Set up automated daily checks**
Create a morning routine:
```
"Give me the daily resilience health report"
"Any conflicts in the next 7 days?"
"Show pending swap requests"
```

**2. Monitor burnout indicators weekly**
```
"Run fire danger index for all residents"
"Calculate burnout Rt for the program"
"Check for STA/LTA precursor alerts"
```

**3. Use background tasks for heavy analysis**
Don't wait for slow queries:
```
"Start a background task for full year metrics computation"
[Later...] "What's the status of that task?"
```

**4. Review audit logs monthly**
Track who's using tools and what they're finding:
```bash
docker-compose logs mcp-server | grep AUDIT | tail -100
```

***REMOVED******REMOVED******REMOVED*** For Developers

**1. Use typed parameters**
MCP tools use Pydantic - pass correct types:
```python
***REMOVED*** Good
date_str = "2025-01-01"  ***REMOVED*** ISO format string
hours = 82.5  ***REMOVED*** float
enabled = true  ***REMOVED*** boolean

***REMOVED*** Bad
date_str = "01/01/2025"  ***REMOVED*** Wrong format
hours = "82.5"  ***REMOVED*** String instead of float
enabled = "true"  ***REMOVED*** String instead of boolean
```

**2. Handle errors gracefully**
All tools can fail - catch errors:
```python
try:
    result = await validate_schedule(start_date, end_date)
except MCPToolError as e:
    if e.error_code == MCPErrorCode.SERVICE_UNAVAILABLE:
        ***REMOVED*** Retry with exponential backoff
    elif e.error_code == MCPErrorCode.VALIDATION_ERROR:
        ***REMOVED*** Fix parameters and retry
    else:
        ***REMOVED*** Log and alert
```

**3. Use circuit breakers for resilience**
Circuit breaker tools protect against cascading failures:
```
***REMOVED*** Check before critical operations
"Check circuit breaker health before running heavy analysis"
```

**4. Enable audit logging in production**
Track all tool usage:
```yaml
environment:
  - MCP_ENABLE_AUDIT_LOG=true
  - MCP_AUDIT_LOG_PATH=/var/log/mcp-audit.log
```

**5. Monitor performance metrics**
Track slow tools:
```bash
***REMOVED*** Extract slow queries from logs
docker-compose logs mcp-server | grep "duration=" | awk '$NF > 5.0'
```

***REMOVED******REMOVED******REMOVED*** For AI Agents

**1. Choose the right tool for the job**
- **Validation** → `validate_schedule`
- **Conflict detection** → `detect_conflicts`
- **Swap matching** → `analyze_swap_candidates`
- **Burnout detection** → `detect_burnout_precursors`, `calculate_fire_danger_index`
- **Long-term analysis** → `start_background_task`

**2. Combine tools for complete analysis**
Example: Complete burnout assessment
```
1. detect_burnout_precursors (STA/LTA early warning)
2. run_spc_analysis (work hour control chart)
3. calculate_fire_danger_index (multi-temporal risk)
4. calculate_burnout_rt (spread prediction)
5. analyze_workload_trend (Kalman filter trend)
```

**3. Explain results in natural language**
Users don't want JSON - synthesize insights:
```
Instead of:
{"rt": 1.35, "status": "spreading"}

Say:
"⚠ Burnout is spreading (Rt = 1.35). Each burned-out resident will cause 1.35 additional cases. Without intervention, 28% of residents will be burned out in 6 weeks."
```

**4. Provide actionable recommendations**
Always include next steps:
```
Instead of:
"ACGME violation detected"

Say:
"ACGME violation: PGY2-03 worked 82.5h in week of Jan 8-14 (limit: 80h).
→ Recommended fix: Remove 3 hours from Jan 13-14 assignments.
→ Suggested swap: Find coverage for Jan 13 PM clinic (use analyze_swap_candidates tool)."
```

**5. Use correlation IDs for tracing**
When errors occur, include correlation ID:
```
"Error occurred (correlation ID: abc-123-def). Check logs with:
docker-compose logs mcp-server | grep abc-123-def"
```

---

***REMOVED******REMOVED*** Complete Tool Reference

***REMOVED******REMOVED******REMOVED*** Core Scheduling Tools (8 tools)

***REMOVED******REMOVED******REMOVED******REMOVED*** validate_schedule
**Purpose**: Validate schedule against ACGME work hour rules

**Parameters**:
- `start_date` (required): ISO date string (YYYY-MM-DD)
- `end_date` (required): ISO date string (YYYY-MM-DD)
- `check_work_hours` (optional): Boolean, default true
- `check_supervision` (optional): Boolean, default true
- `check_rest_periods` (optional): Boolean, default true
- `check_consecutive_duty` (optional): Boolean, default true

**Returns**: `ScheduleValidationResult`
- `is_valid`: Boolean
- `overall_compliance_rate`: Float (0.0-1.0)
- `total_issues`: Integer
- `critical_issues`: Integer
- `issues`: List of ValidationIssue objects

**Example**:
```
"Validate the schedule from Jan 1-31, 2025"
```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** detect_conflicts
**Purpose**: Detect scheduling conflicts and auto-resolution options

**Parameters**:
- `start_date` (required): ISO date string
- `end_date` (required): ISO date string
- `conflict_types` (optional): List of ConflictType enums
- `include_auto_resolution` (optional): Boolean, default true

**Conflict Types**:
- `double_booking`: Same person assigned to multiple blocks
- `work_hour_violation`: ACGME 80h/week exceeded
- `rest_period_violation`: Missing 1-in-7 rest period
- `supervision_gap`: Insufficient faculty coverage
- `leave_overlap`: Leave conflicts
- `credential_mismatch`: Missing required credentials

**Returns**: `ConflictDetectionResult`
- `conflicts`: List of ConflictInfo objects
- `auto_resolutions`: List of ResolutionOption objects
- `total_conflicts`: Integer
- `critical_conflicts`: Integer

**Example**:
```
"Check for conflicts from Jan 15-17 after Dr. Smith's emergency leave"
```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** analyze_swap_candidates
**Purpose**: Find compatible swap matches for schedule changes

**Parameters**:
- `person_id` (required): UUID string
- `assignment_id` (optional): UUID string (specific assignment)
- `block_id` (optional): UUID string (specific block)
- `max_candidates` (optional): Integer, default 10

**Returns**: `SwapCandidateResponse`
- `candidates`: List of SwapCandidate objects
- `total_candidates`: Integer
- `recommended_candidate_id`: UUID string

**Candidate Scoring**:
- Rotation compatibility: 40%
- Credential match: 25%
- Work hour buffer: 20%
- Swap history: 15%

**Example**:
```
"Find swap candidates for Dr. Smith's call shift on Jan 20"
```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** run_contingency_analysis
**Purpose**: N-1/N-2 vulnerability assessment for faculty absences

**Parameters**:
- `scenario` (required): ContingencyScenario enum
- `affected_person_ids` (required): List of UUID strings
- `start_date` (required): ISO date string
- `end_date` (required): ISO date string
- `auto_resolve` (optional): Boolean, default false

**Scenarios**:
- `faculty_absence`: Single faculty member unavailable
- `resident_absence`: Single resident unavailable
- `emergency_coverage`: Multiple simultaneous absences
- `mass_absence`: Large-scale event (e.g., mass casualty)

**Returns**: `ContingencyAnalysisResult`
- `scenario`: ContingencyScenario
- `impact`: ImpactAssessment
- `resolution_options`: List of ResolutionOption objects
- `recommended_option_id`: UUID string

**Example**:
```
"Run N-1 analysis for Dr. Johnson's deployment Feb 1 - May 31"
```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** start_background_task
**Purpose**: Launch long-running analysis in background (Celery)

**Parameters**:
- `task_type` (required): TaskType enum
- `parameters` (required): Dict of task-specific parameters

**Task Types**:
- `resilience_health_check`: Full resilience analysis
- `contingency_analysis`: N-1/N-2 vulnerability scan
- `metrics_computation`: Schedule metrics for date range
- `fallback_precomputation`: Generate static fallback schedules
- `utilization_forecast`: Predict future utilization
- `fairness_report`: Equity analysis across cohorts

**Returns**: `BackgroundTaskResult`
- `task_id`: UUID string (use for polling)
- `status`: "queued" | "running" | "completed" | "failed"
- `estimated_duration`: Seconds (approximate)
- `created_at`: Timestamp

**Example**:
```
"Start a background task for full year resilience analysis"
```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** get_task_status
**Purpose**: Poll status of background task and retrieve results

**Parameters**:
- `task_id` (required): UUID string (from start_background_task)

**Returns**: `TaskStatusResult`
- `task_id`: UUID string
- `status`: "queued" | "running" | "completed" | "failed"
- `progress`: Float (0.0-1.0)
- `result`: Dict (if completed)
- `error`: String (if failed)
- `created_at`: Timestamp
- `completed_at`: Timestamp (if done)

**Example**:
```
"What's the status of task abc-123-def?"
```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** cancel_task
**Purpose**: Cancel a running or queued background task

**Parameters**:
- `task_id` (required): UUID string

**Returns**: `CancelTaskResult`
- `task_id`: UUID string
- `cancelled`: Boolean
- `message`: String

**Example**:
```
"Cancel that slow computation (task abc-123)"
```

---

***REMOVED******REMOVED******REMOVED******REMOVED*** list_active_tasks
**Purpose**: View all currently running or queued tasks

**Parameters**: (none)

**Returns**: `ActiveTasksResult`
- `tasks`: List of TaskStatusResult objects
- `total_active`: Integer
- `total_queued`: Integer
- `total_running`: Integer

**Example**:
```
"Show all active background tasks"
```

---

***REMOVED******REMOVED******REMOVED*** Resilience Framework Tools (12 tools)

See [RESILIENCE_MCP_INTEGRATION.md](mcp-server/RESILIENCE_MCP_INTEGRATION.md) for detailed documentation.

Quick reference:
- `check_utilization_threshold` - 80% Erlang queuing threshold
- `get_defense_level` - Nuclear safety 5-tier defense
- `run_contingency_analysis_resilience` - Power grid N-1/N-2
- `get_static_fallbacks` - AWS static stability
- `execute_sacrifice_hierarchy` - Emergency triage
- `analyze_homeostasis` - Physiology feedback loops
- `calculate_blast_radius` - AWS fault isolation
- `analyze_le_chatelier` - Chemistry equilibrium
- `analyze_hub_centrality` - Network theory SPOF
- `assess_cognitive_load` - Psychology 7±2 limit
- `get_behavioral_patterns` - Swarm intelligence
- `analyze_stigmergy` - Ant colony optimization

---

***REMOVED******REMOVED******REMOVED*** Early Warning Tools (4 tools)

See [MCP_TOOLS_REFERENCE.md](docs/api/MCP_TOOLS_REFERENCE.md) for detailed documentation.

Quick reference:
- `detect_burnout_precursors` - Seismic STA/LTA
- `run_spc_analysis` - Six Sigma Western Electric Rules
- `calculate_fire_danger_index` - Wildfire CFFDRS
- `calculate_batch_fire_danger` - Bulk FWI calculation

---

***REMOVED******REMOVED******REMOVED*** Exotic Research Tools (20 tools)

See [EXOTIC_RESEARCH_TOOLS.md](mcp-server/docs/EXOTIC_RESEARCH_TOOLS.md) for detailed documentation.

Quick reference by domain:
- **Kalman Filter** (2): trend extraction, anomaly detection
- **Fourier/FFT** (3): cycle detection, harmonic resonance, spectral entropy
- **Game Theory** (3): Nash stability, swap prediction, coordination failures
- **Value-at-Risk** (4): coverage VaR, workload VaR, Monte Carlo, CVaR
- **Lotka-Volterra** (4): supply/demand cycles, capacity crunch prediction
- **Hopfield Attractor** (4): energy landscape, stable patterns, basin depth

---

***REMOVED******REMOVED******REMOVED*** Circuit Breaker Tools (4 tools)

Quick reference:
- `check_circuit_breakers` - View all breaker states
- `get_breaker_health` - Health metrics and failure history
- `test_half_open_breaker` - Manual recovery test
- `override_circuit_breaker` - Emergency manual override

---

***REMOVED******REMOVED******REMOVED*** Deployment Tools (7 tools)

Quick reference:
- `get_deployment_status` - Current deployment info
- `list_deployments` - Historical deployments by environment
- `validate_deployment` - Pre-deploy readiness checks
- `run_smoke_tests` - Post-deploy validation
- `run_security_scan` - Vulnerability scanning
- `promote_to_production` - Push to production
- `rollback_deployment` - Emergency rollback

---

***REMOVED******REMOVED*** Appendix: Cross-References

***REMOVED******REMOVED******REMOVED*** Related Documentation

- **[AI Agent User Guide](AI_AGENT_USER_GUIDE.md)**: Overview of AI agent architecture (skills + MCP + ADK)
- **[MCP Tools Reference](../api/MCP_TOOLS_REFERENCE.md)**: Technical API reference for all tools
- **[Resilience MCP Integration](../../mcp-server/RESILIENCE_MCP_INTEGRATION.md)**: Resilience framework tools
- **[Exotic Research Tools](../../mcp-server/docs/EXOTIC_RESEARCH_TOOLS.md)**: Advanced analytics tools
- **[Async Tools](../../mcp-server/ASYNC_TOOLS.md)**: Background task management
- **[MCP Admin Guide](../admin-manual/mcp-admin-guide.md)**: Administrator configuration guide
- **[Schedule Generation Runbook](SCHEDULE_GENERATION_RUNBOOK.md)**: Step-by-step scheduling workflow

***REMOVED******REMOVED******REMOVED*** External Resources

- **[Model Context Protocol Specification](https://modelcontextprotocol.io/)**: Official MCP documentation
- **[FastMCP Framework](https://github.com/jlowin/fastmcp)**: MCP server framework
- **[Claude Code Documentation](https://docs.anthropic.com/claude/docs/claude-code)**: AI assistant integration
- **[ACGME Work Hour Requirements](https://www.acgme.org/what-we-do/accreditation/common-program-requirements/)**: Regulatory reference

---

***REMOVED******REMOVED*** Changelog

**Version 1.0 (2025-12-30)**:
- Initial comprehensive guide
- 97+ tool documentation
- Workflow examples for clinicians, coordinators, developers
- Configuration and troubleshooting sections
- Complete error code reference

---

***REMOVED******REMOVED*** Feedback

This guide is a living document. If you encounter issues or have suggestions:

1. **GitHub Issues**: [Create an issue](https://github.com/your-org/residency-scheduler/issues)
2. **Email**: scheduler-dev@your-org.mil
3. **Slack**: ***REMOVED***scheduler-support

---

**End of MCP Tool Usage Guide**
