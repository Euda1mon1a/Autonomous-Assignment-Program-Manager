# Subagent Capabilities Reference

> **For Subagents:** If you need to know what tools/skills you have access to, read this file.
> **For Commanders:** Include relevant sections when spawning agents, or let them self-discover.

---

## MCP Tools (34 Core + 50 Armory)

All tools prefixed with `mcp__residency-scheduler__`

### Schedule Operations
| Tool | Purpose |
|------|---------|
| `get_schedule` | Retrieve schedule data |
| `create_assignment` | Add assignments |
| `update_assignment` | Modify assignments |
| `delete_assignment` | Remove assignments |
| `generate_schedule` | Auto-generate ACGME-compliant schedules |
| `validate_schedule` | Check compliance against all rules |
| `optimize_schedule` | Improve fairness and coverage |
| `export_schedule` | Convert to Excel/PDF |

### Compliance
| Tool | Purpose |
|------|---------|
| `check_work_hours` | Verify 80-hour rule |
| `check_day_off` | Validate 1-in-7 call |
| `check_supervision` | Confirm supervision ratios |
| `get_violations` | List all violations |
| `generate_compliance_report` | Create audit reports |

### Swaps
| Tool | Purpose |
|------|---------|
| `create_swap` | Initiate swap requests |
| `find_swap_matches` | Find compatible candidates |
| `execute_swap` | Complete approved swaps |
| `rollback_swap` | Revert if issues |
| `get_swap_history` | Audit trail |

### Resilience
| Tool | Purpose |
|------|---------|
| `get_defense_level` | Current defense score (0-10) |
| `get_utilization` | Workload metrics |
| `run_n1_analysis` | Single-absence impact |
| `get_burnout_rt` | Burnout reproduction rate |
| `get_early_warnings` | Emerging stress detection |

### Knowledge Base (RAG)
| Tool | Purpose |
|------|---------|
| `rag_search` | Semantic search (query, top_k, doc_type) |
| `rag_context` | Get relevant context (query, max_tokens) |
| `rag_health` | Check RAG system status |

---

## Skills (Key Categories)

### Core Operations
| Skill | Purpose |
|-------|---------|
| `/scheduling` | Generate ACGME-compliant schedules |
| `/check-compliance` | Audit schedules for violations |
| `/swap` | Execute resident swaps with safety |
| `/optimize-schedule` | Improve schedule quality |

### Code Quality
| Skill | Purpose |
|-------|---------|
| `/lint-fix` | Auto-fix Python/TypeScript lint |
| `/write-tests` | Generate test suites |
| `/review-code` | Review for bugs/security |
| `/debug` | Systematic debugging |

### Git/PR
| Skill | Purpose |
|-------|---------|
| `/commit` | Git commit workflow |
| `/review-pr` | Pull request review |
| `/changelog` | Generate changelogs |

### Multi-Agent
| Skill | Purpose |
|-------|---------|
| `/search-party` | 120-probe codebase recon |
| `/qa-party` | Parallel test/lint/build |
| `/plan-party` | Multi-perspective planning |

### Session
| Skill | Purpose |
|-------|---------|
| `/startup` | Load session context |
| `/startupO` | ORCHESTRATOR mode |
| `/session-end` | Close-out with audit |

---

## RAG Knowledge Base

### Doc Types for Search
| Type | Content |
|------|---------|
| `acgme_rules` | 80-hour limit, 1-in-7, supervision |
| `scheduling_policy` | Block structure, rotations, clinics |
| `swap_system` | Swap workflows, approvals, rollback |
| `resilience_concepts` | N-1/N-2, defense-in-depth |
| `ai_patterns` | Effective prompts, debugging |
| `delegation_patterns` | Auftragstaktik, decision rights |

### Example Queries
```
rag_search("ACGME 80-hour work limit exceptions", doc_type="acgme_rules")
rag_search("how to handle swap conflicts", doc_type="swap_system")
rag_search("Auftragstaktik delegation", doc_type="delegation_patterns")
```

---

## Self-Discovery

If you're a subagent and need capabilities:

1. **Read this file** - You're doing it now
2. **Ask your commander** - They may have specific tools for your mission
3. **Use RAG** - `rag_search("capabilities [your domain]")`
4. **Use MCP_ORCHESTRATION skill** - Discovers and composes tools

---

## Quick Start by Role

### SCHEDULER agents
- Tools: `generate_schedule`, `validate_schedule`, `check_work_hours`
- RAG: `acgme_rules`, `scheduling_policy`
- Skills: `/scheduling`, `/check-compliance`

### QA agents
- Tools: `validate_schedule`, `get_violations`
- Skills: `/write-tests`, `/qa-party`, `/lint-fix`

### SWAP agents
- Tools: `create_swap`, `find_swap_matches`, `execute_swap`
- RAG: `swap_system`
- Skills: `/swap`

### RESILIENCE agents
- Tools: `get_defense_level`, `run_n1_analysis`, `get_burnout_rt`
- RAG: `resilience_concepts`

---

*Last updated: Session 085*
