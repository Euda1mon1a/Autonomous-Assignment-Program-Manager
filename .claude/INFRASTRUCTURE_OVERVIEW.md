***REMOVED*** Personal AI Infrastructure Overview

**Created:** 2025-12-26
**Purpose:** Comprehensive guide to the AAPM AI Infrastructure

---

***REMOVED******REMOVED*** Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   User / Claude Code                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   CLI (cli/aapm)     │  ← Router & Orchestrator
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐    ┌──────────┐    ┌──────────┐
    │ Skills │    │   MCP    │    │  Hooks   │
    │        │    │  Tools   │    │          │
    └────────┘    └──────────┘    └──────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  History (Logs)      │
              │  - scheduling/       │
              │  - swaps/            │
              │  - compliance/       │
              │  - resilience/       │
              └──────────────────────┘
```

---

***REMOVED******REMOVED*** Components

***REMOVED******REMOVED******REMOVED*** 1. CLI Entrypoint (`cli/aapm`)

**Purpose:** Unified command-line interface for all scheduling operations

**Features:**
- Routes commands to appropriate Skills or MCP tools
- Triggers post-operation Hooks
- Manages execution flow and error handling
- Provides consistent UX across all operations

**Location:** `/cli/aapm`

**Commands:**
- `schedule` - Schedule generation and validation
- `schedule-audit` - ACGME compliance auditing
- `swap` - Swap request management
- `resilience` - Resilience testing
- `incident` - Incident response
- `skill-update` - Skill management
- `test` - Test execution

**Usage:**
```bash
aapm schedule generate 2026-03-12 2026-04-08
aapm swap execute SWP-001
aapm resilience n1-test
aapm incident respond
```

---

***REMOVED******REMOVED******REMOVED*** 2. Hooks (`/.claude/Hooks/`)

**Purpose:** Define what to capture after each operation type

**Hooks capture:**
- Operation metadata (timestamp, user, duration)
- Input parameters
- Results and validation
- Constraint impacts
- Recommendations

***REMOVED******REMOVED******REMOVED******REMOVED*** Available Hooks

| Hook | Triggered By | Captures |
|------|--------------|----------|
| `post-schedule-generation.md` | Schedule generation | Solver stats, constraints, violations, coverage |
| `post-swap-execution.md` | Swap execution | Swap details, validation, fairness impact |
| `post-compliance-audit.md` | Compliance audit | Violations, trends, recommendations |
| `post-resilience-test.md` | Resilience testing | Health score, N-1/N-2, critical personnel |

***REMOVED******REMOVED******REMOVED******REMOVED*** Hook Template

```markdown
***REMOVED*** Post-Operation Hook

**Trigger:** After operation completes

***REMOVED******REMOVED*** What to Capture
***REMOVED******REMOVED******REMOVED*** 1. Metadata
***REMOVED******REMOVED******REMOVED*** 2. Parameters
***REMOVED******REMOVED******REMOVED*** 3. Results
***REMOVED******REMOVED******REMOVED*** 4. Impact

***REMOVED******REMOVED*** Where to Store
**Location:** `.claude/History/operation-type/`

***REMOVED******REMOVED*** Format Specification
JSON schema...

***REMOVED******REMOVED*** Trigger Conditions
When to execute this hook...
```

---

***REMOVED******REMOVED******REMOVED*** 3. Methodologies (`/.claude/Methodologies/`)

**Purpose:** Thinking frameworks for AI agents solving complex problems

**Methodologies provide:**
- Core concepts and definitions
- Step-by-step procedures
- Decision trees and algorithms
- Best practices and common pitfalls

***REMOVED******REMOVED******REMOVED******REMOVED*** Available Methodologies

| Methodology | Purpose | Use When |
|-------------|---------|----------|
| `constraint-propagation.md` | CSP problem-solving | Adding/debugging constraints |
| `resilience-thinking.md` | Design for failure | Planning for disruptions |
| `surgical-swaps.md` | Minimal-impact changes | Making schedule adjustments |
| `incident-response.md` | Crisis management | Handling production failures |

***REMOVED******REMOVED******REMOVED******REMOVED*** Methodology Structure

```markdown
***REMOVED*** Methodology Name

**Purpose:** What this methodology is for

***REMOVED******REMOVED*** When to Use
- Scenario 1
- Scenario 2

***REMOVED******REMOVED*** Core Concepts
- Concept 1
- Concept 2

***REMOVED******REMOVED*** Step-by-Step Procedures
1. Step 1
2. Step 2

***REMOVED******REMOVED*** Quick Reference
Decision trees, checklists...
```

---

***REMOVED******REMOVED******REMOVED*** 4. History (`/.claude/History/`)

**Purpose:** Persistent storage of operation logs for analysis and auditing

**Directory Structure:**
```
.claude/History/
├── scheduling/
│   ├── generation_YYYY-MM-DD_HHMMSS.json
│   ├── LATEST.json (symlink to most recent)
│   └── summary_YYYY-MM.json (monthly aggregates)
├── swaps/
│   ├── swap_YYYY-MM-DD_HHMMSS_<swap-id>.json
│   ├── INDEX.json (all swaps index)
│   └── summary_YYYY-MM.json
├── compliance/
│   ├── audit_YYYY-MM-DD_HHMMSS.json
│   ├── LATEST.json
│   ├── dashboard.json (real-time metrics)
│   └── report_YYYY-MM.md (monthly report)
└── resilience/
    ├── test_YYYY-MM-DD_HHMMSS.json
    ├── LATEST.json
    ├── dashboard.json
    └── report_YYYY-MM.md
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Log Retention Policy

| Age | Action |
|-----|--------|
| < 30 days | Keep all |
| 30-90 days | Keep significant (violations, failures) |
| 90-365 days | Keep monthly samples |
| > 365 days | Aggregate statistics only |

**Exception:** Compliance audits kept indefinitely (regulatory requirement)

---

***REMOVED******REMOVED*** Data Flow Examples

***REMOVED******REMOVED******REMOVED*** Example 1: Schedule Generation

```
1. User executes:
   $ aapm schedule generate 2026-03-12 2026-04-08

2. CLI routes to:
   - safe-schedule-generation skill

3. Skill executes:
   - Verify backup exists
   - Call MCP tool: generate_schedule
   - Validate results

4. Hook triggered:
   - post-schedule-generation.md

5. Data captured:
   - Solver statistics
   - Constraint evaluation results
   - Violations found
   - Coverage analysis
   - Resilience metrics

6. Written to:
   - .claude/History/scheduling/generation_2025-12-26_143000.json
   - .claude/History/scheduling/LATEST.json (updated)

7. User notified:
   - Generation complete
   - 3 violations found
   - Coverage: 96.4%
   - N-1 compliant: true
```

***REMOVED******REMOVED******REMOVED*** Example 2: Swap Execution

```
1. User executes:
   $ aapm swap execute SWP-20251226-001

2. CLI routes to:
   - swap-management skill

3. Skill executes:
   - Validate swap request
   - Check ACGME compliance
   - Execute via MCP tool: execute_swap
   - Send notifications

4. Hook triggered:
   - post-swap-execution.md

5. Data captured:
   - Swap details (before/after)
   - Validation results
   - Constraint impact
   - Resilience impact
   - Audit trail

6. Written to:
   - .claude/History/swaps/swap_2025-12-26_144500_SWP-001.json
   - .claude/History/swaps/INDEX.json (updated)

7. User notified:
   - Swap executed successfully
   - Fairness improved (Gini: 0.15 → 0.12)
   - Rollback available until 2025-12-27 14:45
```

***REMOVED******REMOVED******REMOVED*** Example 3: Resilience Test

```
1. User executes:
   $ aapm resilience n1-test

2. CLI routes to:
   - MCP tool: run_contingency_analysis_resilience_tool

3. Tool executes:
   - Test removal of each person individually
   - Calculate impact for each scenario
   - Identify critical personnel

4. Hook triggered:
   - post-resilience-test.md

5. Data captured:
   - N-1 analysis results
   - Critical personnel list
   - Defense level
   - Recovery time estimates
   - Mitigation recommendations

6. Written to:
   - .claude/History/resilience/test_2025-12-26_160000.json
   - .claude/History/resilience/dashboard.json (updated)

7. User notified:
   - N-1 compliant: false
   - 1 critical failure: FAC-PD (procedures)
   - Recommendation: Cross-train backup
```

***REMOVED******REMOVED******REMOVED*** Example 4: Incident Response

```
1. Automated detection or user executes:
   $ aapm incident respond

2. CLI loads:
   - production-incident-responder skill
   - incident-response.md methodology
   - Latest resilience test data
   - Recent error logs

3. Methodology guides:
   - OODA Loop (Observe, Orient, Decide, Act)
   - Root cause analysis (5 Whys)
   - Mitigation strategies
   - Post-mortem template

4. Incident resolved:
   - Timeline documented
   - Root cause identified
   - Action items created

5. Written to:
   - docs/incidents/INCIDENT_2025-12-26.md
   - .claude/History/scheduling/ (if rollback executed)

6. Follow-up:
   - Post-mortem review scheduled
   - Action items tracked
   - Lessons learned shared
```

---

***REMOVED******REMOVED*** Usage Patterns

***REMOVED******REMOVED******REMOVED*** For Claude Code Sessions

***REMOVED******REMOVED******REMOVED******REMOVED*** Pattern 1: Route via CLI

```markdown
User: "Generate schedule for Block 10"

Claude: I'll use the AAPM CLI to route to the appropriate skill:

```bash
aapm schedule generate 2026-03-12 2026-04-08
```

This will:
1. Invoke safe-schedule-generation skill
2. Verify backup exists
3. Generate schedule via CP-SAT solver
4. Validate ACGME compliance
5. Log results to History/scheduling/
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Pattern 2: Load Methodology

```markdown
User: "Debug this constraint violation"

Claude: Let me load the constraint-propagation methodology:

```bash
cat .claude/Methodologies/constraint-propagation.md
```

Based on the methodology, I'll:
1. Isolate the conflict (minimal unsatisfiable subset)
2. Analyze constraint interactions
3. Visualize propagation flow
4. Identify root cause
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Pattern 3: Analyze History

```markdown
User: "How has our swap fairness trended?"

Claude: Analyzing swap history:

```bash
cat .claude/History/swaps/summary_2025-*.json | \
  jq '{month, fairness_improvement}'
```

Results:
- September: +0.02 (slight improvement)
- October: +0.03
- November: +0.05
- December: +0.04

Average fairness improvement per swap: +0.035
Trend: Consistent positive impact
```

***REMOVED******REMOVED******REMOVED*** For Automated Agents

```python
***REMOVED*** Scheduled resilience check
def daily_resilience_check():
    """Run daily N-1 test and alert if issues found."""
    result = subprocess.run(
        ["aapm", "resilience", "n1-test"],
        capture_output=True
    )

    ***REMOVED*** Load latest result
    with open(".claude/History/resilience/LATEST.json") as f:
        test_result = json.load(f)

    ***REMOVED*** Alert on failures
    if not test_result["n1_analysis"]["compliant"]:
        send_alert(
            severity="high",
            message=f"N-1 compliance failed: {len(test_result['n1_analysis']['failures'])} failures",
            details=test_result["n1_analysis"]["failures"]
        )
```

---

***REMOVED******REMOVED*** Integration Points

***REMOVED******REMOVED******REMOVED*** With Existing Skills

**Skills use CLI for:**
- Triggering other skills (orchestration)
- Logging operations (via hooks)
- Loading methodologies (for guidance)

**Example:**
```python
***REMOVED*** In safe-schedule-generation skill
def generate_schedule(params):
    ***REMOVED*** Load methodology for constraint debugging
    methodology = read_file(".claude/Methodologies/constraint-propagation.md")

    ***REMOVED*** Generate schedule
    result = solver.solve(params)

    ***REMOVED*** Trigger logging hook
    trigger_hook("post-schedule-generation", result)

    return result
```

***REMOVED******REMOVED******REMOVED*** With MCP Tools

**CLI routes to MCP tools:**
- `resilience health` → `check_resilience_health_tool`
- `resilience n1-test` → `run_contingency_analysis_resilience_tool`
- `resilience identify-critical` → `analyze_hub_centrality`

**MCP tools log to History:**
```python
***REMOVED*** In MCP tool
def check_resilience_health():
    result = calculate_resilience_metrics()

    ***REMOVED*** Write to History (hook handles this)
    log_resilience_test(result)

    return result
```

***REMOVED******REMOVED******REMOVED*** With Backend API

**CLI can invoke API directly:**
```bash
***REMOVED*** Via MCP tool or direct curl
aapm schedule generate 2026-03-12 2026-04-08
***REMOVED*** → MCP tool: generate_schedule
***REMOVED*** → API: POST /api/v1/schedule/generate
```

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** For AI Agents

1. **Always check History before operations**
   - Load LATEST.json to understand current state
   - Review recent trends
   - Learn from past failures

2. **Use Methodologies for complex problems**
   - Don't reinvent the wheel
   - Follow proven procedures
   - Reference decision trees

3. **Trigger Hooks consistently**
   - Every write operation should log
   - Include all required sections
   - Update dashboards

4. **Route through CLI when possible**
   - Consistent error handling
   - Automatic hook triggering
   - User-friendly output

***REMOVED******REMOVED******REMOVED*** For Developers

1. **Add Hooks for new operations**
   - Define what to capture
   - Specify storage location
   - Document JSON schema

2. **Create Methodologies for new domains**
   - Document thinking processes
   - Include decision trees
   - Provide examples

3. **Extend CLI for new features**
   - Add routing logic
   - Update help text
   - Test error cases

4. **Maintain History integrity**
   - Never delete compliance logs
   - Follow retention policies
   - Keep schemas consistent

---

***REMOVED******REMOVED*** File Inventory

***REMOVED******REMOVED******REMOVED*** CLI
- `cli/aapm` - Main CLI executable (514 lines)
- `cli/README.md` - CLI documentation

***REMOVED******REMOVED******REMOVED*** Hooks (4 files)
- `.claude/Hooks/post-schedule-generation.md` (368 lines)
- `.claude/Hooks/post-swap-execution.md` (427 lines)
- `.claude/Hooks/post-compliance-audit.md` (483 lines)
- `.claude/Hooks/post-resilience-test.md` (567 lines)

***REMOVED******REMOVED******REMOVED*** Methodologies (4 files)
- `.claude/Methodologies/constraint-propagation.md` (655 lines)
- `.claude/Methodologies/resilience-thinking.md` (712 lines)
- `.claude/Methodologies/surgical-swaps.md` (634 lines)
- `.claude/Methodologies/incident-response.md` (597 lines)

***REMOVED******REMOVED******REMOVED*** History (directories)
- `.claude/History/scheduling/`
- `.claude/History/swaps/`
- `.claude/History/compliance/`
- `.claude/History/resilience/`

**Total:** 1 CLI + 8 documentation files + 4 history directories

---

***REMOVED******REMOVED*** Future Enhancements

***REMOVED******REMOVED******REMOVED*** Planned Features

1. **Interactive Mode**
   ```bash
   aapm interactive
   ***REMOVED*** Drop into REPL-style interface
   ```

2. **Watch Mode**
   ```bash
   aapm watch resilience
   ***REMOVED*** Continuous monitoring with live updates
   ```

3. **History Analysis Commands**
   ```bash
   aapm analyze compliance --period 30d
   aapm analyze swaps --fairness-trend
   aapm analyze resilience --critical-personnel
   ```

4. **Export/Import**
   ```bash
   aapm export schedule --format csv
   aapm import people --from people.csv
   ```

5. **Configuration Management**
   ```bash
   aapm config set api.url http://prod-api:8000
   aapm config get mcp.port
   ```

***REMOVED******REMOVED******REMOVED*** Potential Integrations

- **Slack/Teams notifications** on critical events
- **Grafana dashboards** from History JSON logs
- **Jupyter notebooks** for History analysis
- **GitHub Actions** for automated testing
- **Cron jobs** for scheduled resilience checks

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** CLI Issues

**Problem:** Command not found
```bash
***REMOVED*** Solution: Check PATH or use full path
export PATH="$PATH:/path/to/cli"
***REMOVED*** Or
/path/to/cli/aapm help
```

**Problem:** Permission denied
```bash
***REMOVED*** Solution: Make executable
chmod +x cli/aapm
```

***REMOVED******REMOVED******REMOVED*** Hook Issues

**Problem:** Hook not triggering
```bash
***REMOVED*** Check hook file exists
ls .claude/Hooks/post-*.md

***REMOVED*** Check CLI is calling trigger_hook()
grep "trigger_hook" cli/aapm
```

**Problem:** History not writing
```bash
***REMOVED*** Check directory exists and is writable
ls -ld .claude/History/*/
chmod -R u+w .claude/History/
```

***REMOVED******REMOVED******REMOVED*** Methodology Issues

**Problem:** Methodology not loading
```bash
***REMOVED*** Check file exists
ls .claude/Methodologies/*.md

***REMOVED*** Check file readable
cat .claude/Methodologies/constraint-propagation.md
```

---

***REMOVED******REMOVED*** Contributing

***REMOVED******REMOVED******REMOVED*** Adding a New Hook

1. Create `.claude/Hooks/post-new-operation.md`
2. Define capture requirements
3. Specify JSON schema
4. Add to CLI `trigger_hook()` calls
5. Test logging functionality
6. Update this overview

***REMOVED******REMOVED******REMOVED*** Adding a New Methodology

1. Create `.claude/Methodologies/new-framework.md`
2. Document core concepts
3. Provide step-by-step procedures
4. Include decision trees/checklists
5. Add examples
6. Update this overview

***REMOVED******REMOVED******REMOVED*** Extending the CLI

1. Edit `cli/aapm`
2. Add new command routing function
3. Update help text
4. Add hook triggers
5. Test all code paths
6. Update `cli/README.md`

---

***REMOVED******REMOVED*** Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Project guidelines
- [AI Agent User Guide](../docs/guides/AI_AGENT_USER_GUIDE.md) - Agent usage
- [Agent Skills Reference](../docs/development/AGENT_SKILLS.md) - All skills
- [MCP Tools Audit](../docs/planning/MCP_TOOLS_AUDIT.md) - Available tools

---

*Infrastructure created 2025-12-26 for autonomous AI-assisted schedule management*
