***REMOVED*** AAPM CLI - Personal AI Infrastructure

Command-line interface for the Autonomous Assignment Program Manager.

---

***REMOVED******REMOVED*** Installation

```bash
***REMOVED*** Add to PATH (optional)
export PATH="$PATH:/path/to/Autonomous-Assignment-Program-Manager/cli"

***REMOVED*** Or create symlink
ln -s /path/to/Autonomous-Assignment-Program-Manager/cli/aapm /usr/local/bin/aapm
```

***REMOVED******REMOVED*** Quick Start

```bash
***REMOVED*** Show help
aapm help

***REMOVED*** List available skills
aapm skill-update list

***REMOVED*** Generate schedule for Block 10
aapm schedule generate 2026-03-12 2026-04-08

***REMOVED*** Run compliance audit
aapm schedule-audit current

***REMOVED*** Test resilience
aapm resilience n1-test
```

---

***REMOVED******REMOVED*** Architecture

The AAPM CLI serves as a **router** to Claude skills and MCP tools:

```
User Command → CLI Router → Skill/MCP Tool → Action
                           → Hook (logging)
                           → History (storage)
```

***REMOVED******REMOVED******REMOVED*** Example Flow

```bash
$ aapm swap execute SWP-001

1. CLI routes to: swap-management skill
2. Skill executes swap via MCP tool
3. Post-swap-execution hook triggered
4. Swap log written to: .claude/History/swaps/
5. User notified of result
```

---

***REMOVED******REMOVED*** Commands

***REMOVED******REMOVED******REMOVED*** Schedule Management

| Command | Description | Skill/Tool |
|---------|-------------|------------|
| `schedule generate <start> <end>` | Generate schedule | safe-schedule-generation |
| `schedule validate [id]` | Validate ACGME compliance | acgme-compliance |
| `schedule verify [id]` | Human verification checklist | schedule-verification |

***REMOVED******REMOVED******REMOVED*** Swap Management

| Command | Description | Skill/Tool |
|---------|-------------|------------|
| `swap find <person> <date>` | Find swap candidates | swap-management |
| `swap execute <swap-id>` | Execute swap | swap-management |
| `swap rollback <swap-id>` | Rollback swap | swap-management |

***REMOVED******REMOVED******REMOVED*** Resilience Testing

| Command | Description | Skill/Tool |
|---------|-------------|------------|
| `resilience health` | Overall resilience score | MCP: check_resilience_health_tool |
| `resilience n1-test` | N-1 contingency test | MCP: run_contingency_analysis |
| `resilience n2-test` | N-2 contingency test | MCP: run_contingency_analysis |
| `resilience identify-critical` | Find single points of failure | MCP: analyze_hub_centrality |

***REMOVED******REMOVED******REMOVED*** Compliance Auditing

| Command | Description | Skill/Tool |
|---------|-------------|------------|
| `schedule-audit [id]` | Run full audit | acgme-compliance |
| `schedule-audit report [id]` | Generate report | acgme-compliance |

***REMOVED******REMOVED******REMOVED*** Incident Response

| Command | Description | Skill/Tool |
|---------|-------------|------------|
| `incident respond` | Activate incident response | production-incident-responder |
| `incident status` | Check incident status | System check |

---

***REMOVED******REMOVED*** Hooks and History

***REMOVED******REMOVED******REMOVED*** Hooks

Post-operation hooks define **what to capture** after operations:

| Hook | Triggered By | Storage |
|------|--------------|---------|
| `post-schedule-generation.md` | Schedule generation | `History/scheduling/` |
| `post-swap-execution.md` | Swap execution | `History/swaps/` |
| `post-compliance-audit.md` | Compliance audit | `History/compliance/` |
| `post-resilience-test.md` | Resilience testing | `History/resilience/` |

***REMOVED******REMOVED******REMOVED*** History

Operation logs stored in `.claude/History/`:

```
.claude/History/
├── scheduling/
│   ├── generation_2025-12-26_143000.json
│   ├── LATEST.json (symlink)
│   └── summary_2025-12.json
├── swaps/
│   ├── swap_2025-12-26_144500_SWP-001.json
│   ├── INDEX.json
│   └── summary_2025-12.json
├── compliance/
│   ├── audit_2025-12-26_150000.json
│   ├── LATEST.json
│   ├── dashboard.json
│   └── report_2025-12.md
└── resilience/
    ├── test_2025-12-26_160000.json
    ├── LATEST.json
    ├── dashboard.json
    └── report_2025-12.md
```

---

***REMOVED******REMOVED*** Methodologies

Thinking frameworks for AI agents:

| Methodology | Purpose | Use When |
|-------------|---------|----------|
| `constraint-propagation.md` | Constraint satisfaction | Adding/modifying constraints |
| `resilience-thinking.md` | Design for failure | Planning for disruptions |
| `surgical-swaps.md` | Minimal-impact changes | Making schedule adjustments |
| `incident-response.md` | Systematic crisis response | Handling failures |

***REMOVED******REMOVED******REMOVED*** Loading Methodologies

```bash
***REMOVED*** In Claude session:
***REMOVED*** "Load the constraint-propagation methodology and analyze this constraint bug"

***REMOVED*** CLI automatically references methodologies in relevant skills
aapm incident respond  ***REMOVED*** Loads incident-response.md
```

---

***REMOVED******REMOVED*** Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AAPM_API_URL` | `http://localhost:8000` | Backend API URL |
| `AAPM_MCP_HOST` | `localhost` | MCP server host |
| `AAPM_MCP_PORT` | `8080` | MCP server port |
| `AAPM_LOG_LEVEL` | `INFO` | Logging verbosity |

---

***REMOVED******REMOVED*** Examples

***REMOVED******REMOVED******REMOVED*** Schedule Generation

```bash
***REMOVED*** Generate Block 10 schedule
aapm schedule generate 2026-03-12 2026-04-08

***REMOVED*** Expected output:
***REMOVED*** ℹ Routing to: safe-schedule-generation skill
***REMOVED*** ⚠ This will invoke the safe-schedule-generation skill
***REMOVED*** ⚠ Ensure backup exists before proceeding!
***REMOVED*** Skill: safe-schedule-generation
***REMOVED*** Action: generate
***REMOVED*** Parameters: 2026-03-12 2026-04-08
***REMOVED*** ℹ Triggering hook: post-schedule-generation

***REMOVED*** Check generation log:
cat .claude/History/scheduling/LATEST.json
```

***REMOVED******REMOVED******REMOVED*** Swap Execution

```bash
***REMOVED*** Find swap candidates
aapm swap find FAC-001 2026-03-15

***REMOVED*** Execute swap
aapm swap execute SWP-20251226-001

***REMOVED*** Check swap log:
cat .claude/History/swaps/INDEX.json
```

***REMOVED******REMOVED******REMOVED*** Resilience Testing

```bash
***REMOVED*** Run health check
aapm resilience health

***REMOVED*** Test N-1 contingency
aapm resilience n1-test

***REMOVED*** Identify critical personnel
aapm resilience identify-critical

***REMOVED*** Check resilience dashboard:
cat .claude/History/resilience/dashboard.json
```

***REMOVED******REMOVED******REMOVED*** Incident Response

```bash
***REMOVED*** Activate incident response
aapm incident respond

***REMOVED*** This loads:
***REMOVED*** 1. production-incident-responder skill
***REMOVED*** 2. incident-response.md methodology
***REMOVED*** 3. Latest resilience test data
***REMOVED*** 4. Recent error logs
```

---

***REMOVED******REMOVED*** Integration with Claude Code

***REMOVED******REMOVED******REMOVED*** CLI as Skill Router

Claude Code sessions can use CLI commands to invoke skills:

```markdown
User: "Generate schedule for Block 10"

Claude: I'll use the AAPM CLI to route to the safe-schedule-generation skill.

```bash
aapm schedule generate 2026-03-12 2026-04-08
```

This will:
1. Verify backup exists
2. Invoke safe-schedule-generation skill
3. Trigger post-schedule-generation hook
4. Write log to History/scheduling/
```

***REMOVED******REMOVED******REMOVED*** History Analysis

Claude can analyze historical data:

```markdown
User: "How has our compliance score trended?"

Claude: Let me analyze the compliance audit history:

```bash
cat .claude/History/compliance/audit_*.json | jq '.compliance_summary.compliance_score'
```

Based on the last 5 audits:
- Dec 26: 94.2%
- Nov 26: 89.5%
- Oct 26: 87.3%
- Sep 26: 85.1%
- Aug 26: 83.8%

Trend: Improving (+10.4 points over 4 months)
```

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** CLI Not Found

```bash
***REMOVED*** Ensure executable
chmod +x /path/to/cli/aapm

***REMOVED*** Add to PATH
export PATH="$PATH:/path/to/cli"
```

***REMOVED******REMOVED******REMOVED*** Missing Dependencies

```bash
***REMOVED*** Install required tools
apt-get install curl jq python3
```

***REMOVED******REMOVED******REMOVED*** Skill Not Found

```bash
***REMOVED*** List available skills
aapm skill-update list

***REMOVED*** Sync skills from repo
aapm skill-update sync
```

***REMOVED******REMOVED******REMOVED*** Hook Not Triggering

```bash
***REMOVED*** Check hook file exists
ls -la .claude/Hooks/post-*.md

***REMOVED*** Check History directory writable
ls -ld .claude/History/
```

---

***REMOVED******REMOVED*** Development

***REMOVED******REMOVED******REMOVED*** Adding New Commands

Edit `cli/aapm` and add to routing function:

```bash
cmd_new_feature() {
    local subcommand="${1:-help}"
    shift || true

    case "$subcommand" in
        action1)
            print_info "Routing to: skill-name"
            echo "Skill: skill-name"
            echo "Action: action1"
            trigger_hook "post-new-feature"
            ;;
        *)
            print_error "Unknown subcommand: $subcommand"
            return 1
            ;;
    esac
}
```

***REMOVED******REMOVED******REMOVED*** Adding New Hooks

Create `.claude/Hooks/post-new-operation.md`:

```markdown
***REMOVED*** Post-New-Operation Hook

**Trigger:** After new operation completes

***REMOVED******REMOVED*** What to Capture

***REMOVED******REMOVED******REMOVED*** 1. Operation Metadata
...

***REMOVED******REMOVED*** Where to Store

**Location:** `.claude/History/new-operation/`
...
```

***REMOVED******REMOVED******REMOVED*** Adding New Methodologies

Create `.claude/Methodologies/new-thinking-framework.md`:

```markdown
***REMOVED*** New Thinking Framework

**Purpose:** Description of when to use this methodology

***REMOVED******REMOVED*** Core Concepts
...
```

---

***REMOVED******REMOVED*** Related Documentation

- [AI Agent User Guide](../docs/guides/AI_AGENT_USER_GUIDE.md) - Complete guide
- [Skills Reference](../docs/development/AGENT_SKILLS.md) - All skills
- [MCP Tools Audit](../docs/planning/MCP_TOOLS_AUDIT.md) - Available tools
- [CLAUDE.md](../CLAUDE.md) - Project guidelines

---

***REMOVED******REMOVED*** License

Part of the Autonomous Assignment Program Manager project.
