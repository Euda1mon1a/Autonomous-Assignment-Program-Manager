# Handoff Kit Template v1

> **Purpose:** Structured context transfer for session continuity
> **Version:** 1.0
> **Created:** 2026-01-19

---

## MCP Discovery

### RAG Queries
```
rag_search("session handoff protocol context transfer")
rag_search("handoff kit template structured")
rag_search("context continuity session recovery")
```

### Related MCP Tools
| Tool | Purpose |
|------|---------|
| `rag_search` | Retrieve prior handoff kits and session context |
| `rag_ingest` | Index completed handoff kit for future discovery |
| `rag_health` | Verify RAG available for context retrieval |
| `get_checkpoint_status_tool` | Retrieve system checkpoint for handoff |

---

## Instructions

Copy this template to create a handoff kit for session transitions. Fill in all sections relevant to your context. Delete sections that don't apply.

**Naming Convention:** `HANDOFF_[DATE]_[TOPIC].md` (e.g., `HANDOFF_20260119_BLOCK10_SCHEDULING.md`)

---

# [HANDOFF_TITLE]

**Date:** [YYYY-MM-DD]
**From:** [AGENT_OR_SESSION_ID]
**To:** [NEXT_SESSION | SPECIFIC_AGENT]
**Priority:** [High | Medium | Low]

---

## 1. Mission Status

### Objective
[One-line description of what was being accomplished]

### Status
- [ ] Not Started
- [ ] In Progress (XX% complete)
- [ ] Blocked
- [ ] Complete

### Summary
[2-3 sentences describing current state]

---

## 2. Work Completed

### Changes Made
| File | Change Type | Description |
|------|-------------|-------------|
| [path/to/file] | [Created/Modified/Deleted] | [Brief description] |

### Commits
```
[git log --oneline -5 or relevant commit hashes]
```

### Tests Run
- [ ] Backend tests: [PASS/FAIL/SKIPPED]
- [ ] Frontend tests: [PASS/FAIL/SKIPPED]
- [ ] Linting: [PASS/FAIL/SKIPPED]

---

## 3. Work Remaining

### Immediate Next Steps
1. [Highest priority action]
2. [Second priority action]
3. [Third priority action]

### Blocked Items
| Item | Blocker | Resolution Path |
|------|---------|-----------------|
| [Task] | [What's blocking] | [How to unblock] |

### Open Questions
1. [Question requiring decision]
2. [Question requiring clarification]

---

## 4. Context & Decisions

### Key Decisions Made
| Decision | Rationale | Impact |
|----------|-----------|--------|
| [What was decided] | [Why] | [What it affects] |

### Relevant Documentation
- [Link or path to relevant doc]
- [Link or path to relevant doc]

### RAG Queries That Helped
```
rag_search('[query that provided useful context]')
```

---

## 5. Technical State

### Database State
- Migrations: [Up to date / Pending: list migrations]
- Backup Status: [Last backup timestamp]

### Environment
- Backend: [Running / Stopped / Error]
- Frontend: [Running / Stopped / Error]
- Docker: [Container status]
- MCP Server: [Connected / Disconnected]

### MCP Status
```
# Run these before handoff to capture state
rag_health()           → [OK / Degraded / Offline]
get_defense_level()    → [GREEN / YELLOW / RED]
check_circuit_breakers() → [All closed / Open: list]
```

**RAG Queries That Informed This Session:**
```
rag_search("[query 1]")
rag_search("[query 2]")
```

### Branch State
```
Current branch: [branch_name]
Commits ahead of main: [N]
Uncommitted changes: [Yes/No - list files if yes]
```

---

## 6. Risks & Warnings

### Known Issues
- [Issue that next session should be aware of]

### Do NOT
- [Action that should be avoided]
- [Another action to avoid]

### Watch For
- [Symptom that indicates a problem]

---

## 7. Agent Recommendations

### Suggested Agents for Continuation
| Agent | Task | Rationale |
|-------|------|-----------|
| [AGENT_NAME] | [Task] | [Why this agent] |

### MCP Tools to Use
| Tool | Purpose |
|------|---------|
| [tool_name] | [What to use it for] |

---

## 8. Audit Trail

### Session Timeline
| Time | Action | Result |
|------|--------|--------|
| [HH:MM] | [What happened] | [Outcome] |

### Governance Compliance
- [ ] Tests pass
- [ ] Linting clean
- [ ] No OPSEC violations
- [ ] Audit trail complete

---

## Appendix: Raw Context

<details>
<summary>Expand for additional context</summary>

### Error Messages
```
[Paste relevant error messages]
```

### Relevant Code Snippets
```python
# [Description of snippet]
[code]
```

### Shell History
```bash
# Relevant commands from session
[commands]
```

</details>

---

*Generated using HANDOFF_KIT_v1 template*
