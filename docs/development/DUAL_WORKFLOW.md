# Dual-Workflow Pattern

> **Purpose:** Enable parallel AI workflows for engineering and human deliverables
> **Created:** 2026-01-16
> **Status:** Active

---

## Overview

This pattern separates work between two AI assistants running in parallel:

| Agent | Domain | Workspace | Outputs |
|-------|--------|-----------|---------|
| **Primary Claude** (CLI) | Engineering | `backend/`, `frontend/`, `.claude/` | Code, tests, migrations |
| **Claude Cowork** | Deliverables | `workspace/` (gitignored) | Docs, presentations, proposals |

**Benefits:**
- Concurrent progress on code and documentation
- Cowork cannot break the codebase
- Clean git history (workspace is gitignored)
- Focused context for each agent

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Human Orchestrator                          │
│                    (reviews, approves, directs)                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│   Primary Claude      │       │   Claude Cowork       │
│   (CLI Session)       │       │   (Parallel)          │
├───────────────────────┤       ├───────────────────────┤
│ Domain: Engineering   │       │ Domain: Deliverables  │
│ - Backend code        │       │ - IRB protocols       │
│ - Frontend code       │       │ - Presentations       │
│ - Tests               │       │ - Proposals           │
│ - Database            │       │ - Reports             │
│ - Infrastructure      │       │ - Consent forms       │
├───────────────────────┤       ├───────────────────────┤
│ Workspace:            │       │ Workspace:            │
│ backend/              │       │ workspace/            │
│ frontend/             │       │ (gitignored)          │
│ .claude/              │       │                       │
│ docs/ (technical)     │       │                       │
└───────────────────────┘       └───────────────────────┘
```

---

## When to Use Each Agent

### Primary Claude (Engineering)

- Backend/frontend code changes
- Database migrations
- Test writing
- API development
- Infrastructure/Docker
- Technical documentation in `docs/`

### Claude Cowork (Deliverables)

- IRB protocols and consent forms
- PowerPoint/slide decks
- Grant proposals
- Reports for stakeholders
- Word-ready documents
- Any human-facing non-code deliverable

---

## Workspace Structure

The `workspace/` folder is **gitignored** - safe for drafts and deliverables.

```
workspace/
├── README.md                 # Guidelines for AI assistants
├── research/                 # IRB, consent, study protocols
├── presentations/            # Slides, briefings
├── exports/                  # Data extracts, reports
├── drafts/                   # Work-in-progress
└── cowork-scratch/           # Temporary working files
```

---

## Task Handoff Process

### Option 1: Use `/cowork-handoff` Skill

```
/cowork-handoff research irb-submission
/cowork-handoff presentations quarterly-review
```

This creates:
- Task folder in `workspace/<domain>/`
- `TASK_<name>.md` with objectives
- Copies relevant context files

### Option 2: Manual Setup

1. **Primary Claude creates context**

```
workspace/research/
├── TASK_<name>.md            # Task brief with objectives
├── CONTEXT_<source>.md       # Copied relevant docs
└── CONTEXT_<source>.py       # Copied relevant code
```

2. **Give Cowork scoped access**

Only provide access to the workspace folder:
```
/path/to/project/workspace/
```

3. **Cowork produces deliverables**

Outputs stay in workspace, don't pollute codebase.

4. **Human reviews and promotes**

If needed, move polished docs to `docs/` or share externally.

---

## Task Brief Template

Create a `TASK_<name>.md` file with:

```markdown
# Task: <Name>

## Objective
<Clear statement of what to produce>

## Context Files (in this folder)
| File | Contents |
|------|----------|
| `CONTEXT_<name>.md` | <description> |

## Deliverables
1. `<filename>.md` - <description>
2. `<filename>.md` - <description>

## Key Facts
- <Relevant fact 1>
- <Relevant fact 2>

## Style Notes
- <Any formatting preferences>
```

---

## Guidelines for Cowork

When working in `workspace/`:

1. **No code** - Code goes in `backend/` or `frontend/`
2. **No secrets** - Don't put credentials here either
3. **Ephemeral OK** - Feel free to delete/reorganize
4. **Human review expected** - These are drafts for human polish
5. **Prefer Markdown** - Converts easily to Word/PDF
6. **Reference codebase** - But don't duplicate code

---

## Example: IRB Submission

**Primary Claude prepares:**
```
workspace/research/
├── TASK_irb_submission.md           # Task brief
├── CONTEXT_technical_roadmap.md     # Feature design
├── CONTEXT_survey_schemas.py        # Survey questions
└── CONTEXT_tan_2026_study.pdf       # Research paper
```

**Cowork produces:**
```
workspace/research/
├── IRB_PROTOCOL.md         # Formal study protocol
├── INFORMED_CONSENT.md     # Consent language
├── DATA_MANAGEMENT_PLAN.md # Privacy/retention
└── SURVEY_INSTRUMENTS.md   # Full instruments
```

**Human reviews** and either:
- Submits to IRB directly
- Moves approved docs to `docs/research/`

---

## Related

- `workspace/README.md` - Guidelines in the workspace folder
- `/cowork-handoff` skill - Automates task handoff
- `.claude/Governance/HIERARCHY.md` - Agent hierarchy
