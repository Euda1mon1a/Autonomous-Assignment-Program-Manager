# Admin MCP Guide: Using Claude Code for Schedule Management

> **Purpose:** Step-by-step guide for administrators using the Claude Code chat interface to manage residency schedules via MCP tools.

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Available Capabilities](#available-capabilities)
4. [Common Workflows](#common-workflows)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The MCP (Model Context Protocol) interface allows administrators to interact with the scheduling system using natural language. Instead of navigating complex UI forms, you can simply ask Claude to perform scheduling tasks.

### What You Can Do

- **Validate schedules** for ACGME compliance
- **Detect conflicts** and get resolution suggestions
- **Find swap candidates** for coverage requests
- **Run contingency analysis** for workforce planning
- **Monitor system health** via resilience tools
- **Execute background tasks** for long-running operations

### How It Works

1. You type a natural language request
2. Claude selects the appropriate MCP tool(s)
3. The tool queries the scheduling database
4. You receive results in plain language

---

## Getting Started

### Accessing the Chat Interface

1. Log in with Admin or Coordinator credentials
2. Navigate to the Admin Dashboard
3. Find the "Claude Code Assistant" panel
4. Type your request in the chat input

### Session Persistence

Your chat history is automatically saved to your browser's local storage:
- **Sessions persist** across page refreshes
- **Last 20 sessions** are retained
- **Clear** button starts a fresh conversation

### Quick Prompts

Use the quick prompt buttons for common tasks:
- **Generate Schedule** - Create schedule for next rotation block
- **Check Compliance** - Analyze ACGME violations
- **Export Report** - Generate detailed analysis report

---

## Available Capabilities

### Scheduling & Compliance Tools

| Tool | What It Does | Example Prompt |
|------|-------------|----------------|
| `validate_schedule` | Check ACGME compliance | "Validate the schedule for January 2025" |
| `detect_conflicts` | Find double-bookings, gaps | "Are there any scheduling conflicts next week?" |
| `analyze_swap_candidates` | Find swap partners | "Who can cover Dr. Smith's clinic on Tuesday?" |
| `run_contingency_analysis` | Simulate absences | "What if we lose 2 faculty next month?" |

### Resilience Tools

| Tool | What It Does | Example Prompt |
|------|-------------|----------------|
| `check_utilization_threshold` | Check 80% capacity limit | "How close are we to capacity?" |
| `get_defense_level` | Current safety status | "What's our current defense level?" |
| `run_contingency_analysis_resilience` | N-1/N-2 vulnerability | "Can we survive losing any single faculty?" |
| `analyze_hub_centrality` | Find critical dependencies | "Who are our most critical faculty?" |

### Background Tasks

| Tool | What It Does | Example Prompt |
|------|-------------|----------------|
| `start_background_task` | Run long operations | "Start a resilience health check" |
| `get_task_status` | Check task progress | "What's the status of the health check?" |
| `list_active_tasks` | See running tasks | "Show all active background tasks" |

---

## Common Workflows

### Workflow 1: Daily Compliance Check

```
You: "Check for any ACGME violations this week"

Claude: [Runs validate_schedule tool]
        Found 2 violations:
        - Dr. Johnson: 82 hours this week (exceeds 80-hour limit)
        - PGY-1 coverage gap on Wednesday PM

        Recommendations:
        1. Reassign one of Dr. Johnson's Thursday shifts
        2. Assign backup coverage for Wednesday PM
```

### Workflow 2: Handling a Swap Request

```
You: "Dr. Martinez needs someone to cover her Friday clinic"

Claude: [Runs analyze_swap_candidates tool]
        Top swap candidates:
        1. Dr. Chen (92% compatible, available, mutual benefit)
        2. Dr. Patel (85% compatible, requires schedule adjustment)
        3. Dr. Williams (78% compatible, already at 72 hours)

        Recommendation: Dr. Chen is the best match.
```

### Workflow 3: Planning for Extended Absence

```
You: "Dr. Thompson will be out for 6 weeks starting February 1st.
      What's the impact?"

Claude: [Runs run_contingency_analysis tool]
        Impact Assessment:
        - 12 clinic slots need coverage
        - 4 inpatient shifts affected
        - Current coverage rate would drop to 78%

        Resolution Options:
        1. Redistribute among 4 faculty (+3 hours each)
        2. Activate locum coverage for 50% of shifts
        3. Reduce non-essential clinic capacity

        Risk: Option 1 pushes 2 faculty near 80-hour limit.
```

### Workflow 4: System Health Check

```
You: "Give me an overall health assessment of the schedule"

Claude: [Runs multiple resilience tools]
        System Health Report:

        Defense Level: GREEN
        Utilization: 72% (healthy, below 80% threshold)
        N-1 Status: PASS (can survive any single faculty loss)
        N-2 Status: WARNING (3 pair combinations are vulnerable)

        Critical Dependencies:
        - Dr. Smith covers 40% of procedures (high centrality)
        - Weekend coverage relies on 2 faculty

        Recommendations:
        1. Cross-train backup for procedure coverage
        2. Add one more faculty to weekend rotation pool
```

### Workflow 5: Generating a Report

```
You: "Generate a compliance report for the program director"

Claude: [Compiles data from multiple tools]

        === ACGME Compliance Report ===
        Period: December 1-31, 2024

        Summary:
        - Total Residents: 24
        - Violations: 3 (all resolved)
        - Average Weekly Hours: 68.5
        - Supervision Compliance: 100%

        Violation Details:
        [Lists each violation with resolution]

        Trends:
        - Work hours trending down (good)
        - Coverage gaps increased 10% (investigate)

        [Artifact: Download full report as JSON]
```

---

## Best Practices

### Be Specific with Dates

```
Good: "Check compliance for January 15-31, 2025"
Poor: "Check compliance for next month"
```

### Provide Context

```
Good: "Find swap candidates for Dr. Smith's Tuesday AM clinic on Jan 14th"
Poor: "Who can swap with Dr. Smith?"
```

### Use the MCP Capabilities Panel

The capabilities panel (sidebar) shows all available tools with:
- Descriptions of what each tool does
- When to use each tool
- Example prompts you can click to try

### Review Results Carefully

Claude provides recommendations but **you make the final decisions**:
- Verify suggestions make clinical sense
- Consider factors Claude might not know
- Use your judgment on edge cases

### Export Important Results

For records or sharing:
1. Click "Download" on any artifact
2. Use "Export Report" quick prompt
3. Copy important information before clearing

---

## Troubleshooting

### "No active session" Error

The session expired or was cleared. Simply type a new message to start a fresh session.

### Tool Returns Empty Results

- Check date range - ensure dates are valid
- Verify data exists for the period
- Try a broader search first

### Long-Running Operations

Some operations take time (schedule generation, contingency analysis):
1. Claude will start a background task
2. You'll get a task ID
3. Ask "What's the status of task [ID]?" to check progress

### Unexpected Results

If results don't match expectations:
1. Rephrase your request with more detail
2. Break complex requests into simpler steps
3. Check the MCP Capabilities Panel for the right tool

### Connection Issues

If the chat stops responding:
1. Check your network connection
2. Refresh the page
3. Your session history will be preserved

---

## Example Prompts by Use Case

### Compliance & Validation

- "Validate ACGME compliance for all residents this month"
- "Are there any work hour violations in the current block?"
- "Check supervision ratios for PGY-1 residents"
- "Find any rest period violations in the last 2 weeks"

### Coverage & Swaps

- "Who can cover the Friday night call shift?"
- "Find 3 candidates to swap with Dr. Lee's Monday clinic"
- "What's the impact if Dr. Garcia calls in sick tomorrow?"
- "Show current coverage rates by rotation"

### Resilience & Planning

- "Run N-1 contingency analysis for critical rotations"
- "What's our current defense level?"
- "Identify single points of failure in the schedule"
- "How much slack do we have in the system?"

### Reporting

- "Generate a weekly compliance summary"
- "Show work hour trends for the last 3 months"
- "Create an executive summary of schedule health"
- "List all pending swap requests"

### System Operations

- "Show all active background tasks"
- "Start a resilience health check"
- "Cancel task abc-123"
- "Run smoke tests on the system"

---

## Security Notes

- All interactions are authenticated via your admin credentials
- Sensitive data is never sent to external services
- Audit logs track all MCP tool invocations
- Session data is stored locally in your browser only

---

## Getting Help

- **MCP Capabilities Panel**: See all available tools and examples
- **Clear Button**: Start fresh if the conversation gets confusing
- **Export Session**: Save your conversation for reference
- **Documentation**: See `docs/development/CLAUDE_CHAT_BRIDGE.md` for technical details

---

*Last Updated: December 2024*
