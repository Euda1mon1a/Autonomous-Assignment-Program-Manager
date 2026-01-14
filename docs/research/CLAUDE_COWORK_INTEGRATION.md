# Claude Cowork Integration Research

> **Date:** 2026-01-13
> **Status:** Research Preview Analysis
> **Author:** Claude (Opus 4.5)

---

## Executive Summary

Anthropic released **Claude Cowork** on January 12, 2026—a desktop agent that extends Claude Code's capabilities to non-technical users. Built on the same Claude Agent SDK, Cowork enables file management, document processing, and browser automation through a GUI interface. This document analyzes how Cowork could augment the Residency Scheduler's existing Claude infrastructure.

---

## What is Claude Cowork?

### Overview

Claude Cowork is described as "Claude Code for the rest of your work." It's a research preview feature in the Claude Desktop macOS application that allows users to grant Claude access to specific folders for autonomous file operations.

### Key Technical Features

| Feature | Description |
|---------|-------------|
| **Sandboxed Execution** | Uses Apple's VZVirtualMachine (Virtualization Framework) with custom Linux root filesystem |
| **File Access** | Read, edit, and create files in user-designated folders |
| **Agentic Architecture** | Plans and executes steps independently; spawns parallel sub-agents |
| **Browser Integration** | Pairs with "Claude in Chrome" extension for web automation |
| **Built-in VM** | Isolation for safe execution of terminal commands |

### Availability

- **Platform:** macOS only (Windows planned)
- **Subscription:** Max subscribers ($100-$200/month)
- **Status:** Research preview
- **Limitations:** No cross-device sync, no session memory

### Development Note

Anthropic built Cowork in ~10 days using Claude Code itself, demonstrating the power of AI-assisted development.

---

## Current Claude Integration in This Project

The Residency Scheduler already has an extensive Claude integration:

| Category | Count | Purpose |
|----------|-------|---------|
| Agents | 55 | Domain-specific specialists (SCHEDULER, COMPLIANCE_AUDITOR, etc.) |
| Identities | 55 | Boot context for each agent |
| Skills | 34+ | Reusable capabilities (SCHEDULING, SWAP_EXECUTION, etc.) |
| Slash Commands | 35 | CLI shortcuts (/generate-schedule, /verify-schedule, etc.) |
| Hooks | 4 | Pre-tool validation, session lifecycle |
| MCP Tools | 29+ | Validation, resilience, compliance checking |

### Key Frameworks Already in Place

1. **PAI² Framework** - Parallel Agentic Infrastructure + Personal AI philosophy
2. **Auftragstaktik Doctrine** - Mission-type orders enabling specialist autonomy
3. **Constitutional Governance** - Non-negotiable rules for ACGME compliance
4. **MCP Orchestration** - 4 primary workflows with confidence frameworks

---

## Augmentation Opportunities

### 1. Non-Technical Stakeholder Interfaces

**Current Gap:** Claude Code requires CLI proficiency. Program coordinators, chiefs, and administrative staff may not be comfortable with terminal interfaces.

**Cowork Solution:**

```
┌─────────────────────────────────────────────────────────────┐
│  CURRENT: Developer Workflow                                │
│  ─────────────────────────────────────────────────────────  │
│  Developer → Claude Code CLI → MCP Tools → Schedule Output  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  PROPOSED: Dual-Track Workflow                              │
│  ─────────────────────────────────────────────────────────  │
│  Developer → Claude Code CLI → MCP Tools → Schedule Output  │
│                                    ↓                        │
│  Coordinator → Claude Cowork → Export Folder → Reports      │
└─────────────────────────────────────────────────────────────┘
```

**Use Cases:**
- Program coordinators generating weekly reports from exported data
- Chiefs reviewing compliance summaries without technical knowledge
- Administrative staff organizing schedule-related documents

### 2. Document Processing Pipeline

**Current Gap:** PDF/XLSX export exists but requires developer invocation via `/export-pdf` or `/export-xlsx` commands.

**Cowork Solution:**

| Task | Current Method | Cowork Method |
|------|----------------|---------------|
| Generate monthly report | Developer runs `/export-pdf` | Coordinator: "Create monthly report from this folder" |
| Organize schedule exports | Manual file management | "Sort these by date and rename with resident names" |
| Extract data from receipts | Not supported | "Create expense spreadsheet from these screenshots" |
| Compile training materials | Manual aggregation | "Build a training guide from these policy documents" |

### 3. Browser Automation for External Systems

**Current Gap:** MCP tools operate on internal data. External systems (email, calendars, hospital portals) require manual interaction.

**Cowork + Chrome Extension:**

```
Cowork Folder              Chrome Extension           External System
     │                           │                          │
     ├──── Schedule JSON ───────►├──── Fill Form ──────────►│ Hospital Calendar
     │                           │                          │
     ├──── Swap Request ────────►├──── Submit ─────────────►│ Duty Roster Portal
     │                           │                          │
     ◄──── Confirmation ─────────┤◄──── Scrape ─────────────┤ Email Confirmation
```

**Potential Workflows:**
- Syncing approved schedules to external hospital calendars
- Submitting official swap requests to administrative systems
- Extracting policy updates from hospital portals

### 4. Onboarding and Documentation

**Current Gap:** New developers must read extensive `.claude/` documentation. Training materials are scattered.

**Cowork Solution:**

```markdown
User Prompt: "Create an onboarding guide for new developers from the .claude/ folder"

Cowork Actions:
1. Reads CLAUDE.md, CONSTITUTION.md, HIERARCHY.md
2. Identifies key concepts (Auftragstaktik, PAI², MCP tools)
3. Generates structured onboarding document
4. Creates quick-reference cards for common workflows
```

### 5. Session Handoff Automation

**Current Gap:** Session handoffs require manual scratchpad updates and HANDOFF.md creation.

**Cowork Enhancement:**

```
End of Claude Code Session
         │
         ▼
    Export Session Notes to Cowork Folder
         │
         ▼
    Cowork: "Organize these notes into a handoff document"
         │
         ▼
    Structured HANDOFF.md with:
    - Completed tasks
    - Blockers encountered
    - Recommended next steps
    - Files modified
```

---

## Integration Architecture

### Proposed Folder Structure

```
/exports/                          # Cowork-accessible folder
├── schedules/                     # Generated schedule outputs
│   ├── 2026-01-week-02.json
│   └── 2026-01-week-02.pdf
├── reports/                       # Compliance and status reports
│   ├── acgme-audit-2026-01.md
│   └── resilience-dashboard.html
├── handoffs/                      # Session continuity
│   ├── SESSION_053_HANDOFF.md
│   └── SESSION_054_NOTES.txt
├── inbox/                         # Items for Cowork to process
│   ├── receipt-screenshots/
│   └── policy-updates/
└── outbox/                        # Cowork-generated outputs
    ├── expense-report.xlsx
    └── onboarding-guide.pdf
```

### Workflow Integration Points

```
┌────────────────────────────────────────────────────────────────────┐
│                    CLAUDE ECOSYSTEM                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │ Claude Code │    │   MCP       │    │  Claude     │            │
│  │    CLI      │───►│  Server     │◄───│  Cowork     │            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
│        │                   │                  │                    │
│        │                   │                  │                    │
│        ▼                   ▼                  ▼                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │  Codebase   │    │  Database   │    │  /exports/  │            │
│  │  Editing    │    │  Operations │    │  Folder     │            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  USERS                                                             │
│  ───────                                                           │
│  Developers ─────────────────► Claude Code                         │
│  Coordinators ───────────────► Claude Cowork                       │
│  Chiefs ─────────────────────► Claude Cowork (read-only reports)   │
│  Admin Staff ────────────────► Claude Cowork (document processing) │
└────────────────────────────────────────────────────────────────────┘
```

---

## Security Considerations

### OPSEC/PERSEC Compliance

| Risk | Mitigation |
|------|------------|
| PHI in exported files | Use synthetic IDs, never real names |
| Cowork accessing sensitive folders | Restrict to `/exports/` only |
| Prompt injection via malicious files | Vet all files before placing in inbox |
| Browser automation credentials | Never store credentials in Cowork-accessible folders |

### Recommended Policies

1. **Folder Isolation:** Cowork should ONLY access `/exports/`, never codebase or `.env` files
2. **Data Sanitization:** All exports must use synthetic identifiers per existing OPSEC rules
3. **Audit Trail:** Log all Cowork operations via session notes
4. **Human Review:** Cowork outputs destined for external systems require human approval

---

## Implementation Roadmap

### Phase 1: Research Preview Exploration (Current)

- [ ] Document Cowork capabilities as they evolve
- [ ] Identify pilot use cases with low-risk data
- [ ] Establish `/exports/` folder convention

### Phase 2: Pilot Integration

- [ ] Configure Cowork folder access for one coordinator
- [ ] Test report generation from sanitized schedule exports
- [ ] Evaluate Chrome extension for calendar sync

### Phase 3: Workflow Automation

- [ ] Integrate session handoff exports into Cowork pipeline
- [ ] Automate monthly compliance report generation
- [ ] Build onboarding material generation workflow

### Phase 4: Full Integration

- [ ] Add Cowork-specific slash commands for exports
- [ ] Create MCP tool → Cowork export bridge
- [ ] Document coordinator workflows in admin manual

---

## Comparison: Claude Code vs Claude Cowork

| Aspect | Claude Code | Claude Cowork |
|--------|-------------|---------------|
| **Interface** | CLI (terminal) | GUI (Desktop app) |
| **Users** | Developers | Non-technical staff |
| **File Access** | Full codebase | Designated folders only |
| **Operations** | Code editing, git, tests | File management, documents |
| **Automation** | MCP tools, scripts | Browser + file operations |
| **Session Memory** | Hooks, scratchpad | None (currently) |
| **Platform** | Cross-platform | macOS only |
| **Availability** | Pro+ subscribers | Max subscribers only |

### Complementary, Not Competing

Claude Code and Claude Cowork serve different audiences with different needs:

```
                    Technical Skill Level
                    ─────────────────────►
        Low                              High
         │                                │
         │    ┌──────────────┐            │
         │    │    Claude    │            │
         │    │    Cowork    │            │
         │    └──────────────┘            │
         │              ┌─────────────────┤
         │              │  Claude Code    │
         │              └─────────────────┤
         │                                │
         ▼                                ▼
    Non-Technical                   Developer
    Stakeholders                    Operations
```

---

## Recommendations

### Immediate Actions

1. **Subscribe to Max Plan** for one coordinator to pilot Cowork
2. **Create `/exports/` folder** with documented structure
3. **Establish data sanitization** guidelines for Cowork-bound files

### Medium-Term Goals

1. **Develop export scripts** that output Cowork-friendly formats
2. **Train coordinators** on Cowork for document processing
3. **Document browser automation** patterns for external systems

### Long-Term Vision

A unified Claude ecosystem where:
- **Developers** use Claude Code for implementation
- **Coordinators** use Cowork for document processing and exports
- **Both** leverage MCP tools for scheduling operations
- **Handoffs** flow seamlessly between CLI and GUI interfaces

---

## Sources

- [VentureBeat: Anthropic launches Cowork](https://venturebeat.com/technology/anthropic-launches-cowork-a-claude-desktop-agent-that-works-in-your-files-no)
- [Simon Willison: First impressions of Claude Cowork](https://simonwillison.net/2026/Jan/12/claude-cowork/)
- [TechCrunch: Claude Cowork without the code](https://techcrunch.com/2026/01/12/anthropics-new-cowork-tool-offers-claude-code-without-the-code/)
- [Silicon Republic: Claude Code for non-coding work](https://www.siliconrepublic.com/machines/anthropic-cowork-claude-code-for-non-coding-work)
- [Axios: Anthropic's Claude moves further into the cubicle](https://www.axios.com/2026/01/12/ai-anthropic-claude-jobs)
- [Fortune: Claude Cowork threatens startups](https://fortune.com/2026/01/13/anthropic-claude-cowork-ai-agent-file-managing-threaten-startups/)
- [IT Pro: Everything about Claude Cowork](https://www.itpro.com/technology/artificial-intelligence/everything-you-need-to-know-about-anthropic-claude-cowork)
- [SiliconANGLE: Cowork is accessible Claude Code](https://siliconangle.com/2026/01/12/anthropics-cowork-accessible-version-claude-code/)

---

*This research document will be updated as Claude Cowork exits research preview and additional capabilities are announced.*
