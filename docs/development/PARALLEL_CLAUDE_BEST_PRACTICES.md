***REMOVED*** Parallel Claude Best Practices

> **Created:** 2025-12-24
> **Purpose:** Coordination patterns for Claude Code (Web) and Claude Code (IDE) working in parallel
> **Audience:** Human operators, Claude Web sessions, Claude IDE sessions

---

***REMOVED******REMOVED*** Executive Summary

This document defines the coordination model for parallel AI-assisted development using:
- **Claude Code (Web)** - Browser-based, no PII access, documentation and analysis focus
- **Claude Code (IDE)** - Local terminal, full access, database and testing focus
- **Human** - Strategic oversight, approval authority, PII source

---

***REMOVED******REMOVED*** Agent Access Model

***REMOVED******REMOVED******REMOVED*** Capability Matrix

| Capability | Claude (Web) | Claude Code (IDE) | Human |
|------------|--------------|-------------------|-------|
| **Read source code** | Yes | Yes | Yes |
| **Edit source code** | Yes | Yes | Yes |
| **Run tests** | No (can review) | Yes | Yes |
| **Access database** | No | Yes | Yes |
| **View PII** | No | Yes | Yes |
| **Create PII** | No | No | Yes |
| **Approve PRs** | No | No | Yes |
| **Push to remote** | Yes (own branch) | Yes (own branch) | Yes |
| **Merge to main** | No | No | Yes |

***REMOVED******REMOVED******REMOVED*** PII Boundaries

| Data Type | Claude (Web) | Claude Code (IDE) |
|-----------|--------------|-------------------|
| Source code | Full access | Full access |
| Test fixtures (synthetic) | Full access | Full access |
| Anonymized metrics | Full access | Full access |
| Real names | Never | Full access |
| Real schedules | Never | Full access |
| Database dumps | Never | Full access |
| Airtable exports | Never | Full access |

---

***REMOVED******REMOVED*** Parallel Work Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: Independent Streams

When tasks have no dependencies:

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Code (IDE)              │  Claude (Web)             │
├─────────────────────────────────┼───────────────────────────┤
│  Database seeding               │  Documentation updates    │
│  Integration tests              │  Code review (no PII)     │
│  Schedule generation            │  Architecture analysis    │
│  Real data validation           │  Algorithm documentation  │
└─────────────────────────────────┴───────────────────────────┘
```

**Rules:**
- Each agent works on separate files
- No file should be edited by both agents simultaneously
- Both can read any source file
- Commit to separate branches

***REMOVED******REMOVED******REMOVED*** Pattern 2: Checkpoint Handoff

When Claude (Web) needs data from Claude Code (IDE):

```
Claude Code (IDE)                    Claude (Web)
─────────────────                    ────────────
1. Complete data task
2. Export sanitized metrics
3. Commit and document
4. Signal "Checkpoint N complete"
                                     5. Receive sanitized data
                                     6. Perform analysis
                                     7. Document findings
                                     8. Signal ready for next
```

**Handoff Protocol:**
1. Claude Code (IDE) exports data using `export_sanitized_metrics.py`
2. Claude Code (IDE) updates checkpoint status in roadmap doc
3. Human shares sanitized JSON with Claude (Web)
4. Claude (Web) performs analysis
5. Claude (Web) updates roadmap with findings

***REMOVED******REMOVED******REMOVED*** Pattern 3: Code Review Loop

When Claude (Web) reviews code written by Claude Code (IDE):

```
Claude Code (IDE)                    Claude (Web)
─────────────────                    ────────────
1. Write implementation
2. Commit to feature branch
3. Push to remote
                                     4. Read code via Glob/Grep/Read
                                     5. Invoke `code-review` skill
                                     6. Document findings
                                     7. Suggest improvements
8. Apply approved changes
9. Update tests
10. Push updates
```

---

***REMOVED******REMOVED*** Communication Protocols

***REMOVED******REMOVED******REMOVED*** Document-Based Communication

Since agents cannot directly message each other, use documents:

| Document | Purpose | Updated By |
|----------|---------|------------|
| `BLOCK_10_ROADMAP.md` | Checkpoint status, task ownership | Both agents |
| `SESSION_CAPABILITIES.md` | Available tools and skills | Claude (Web) |
| `CHANGELOG.md` | User-facing changes | Both agents |
| Session notes (`SESSION_*.md`) | Session summaries | Active agent |

***REMOVED******REMOVED******REMOVED*** Status Signaling

Use checkbox markers in roadmap documents:

```markdown
***REMOVED******REMOVED******REMOVED*** Checkpoint 2: Schedule Generation

| Task | Status |
|------|--------|
| Generate schedule | ✅ Complete |
| Export metrics | ✅ Complete |
| Web analysis | 🔄 In Progress |
| Recommendations | ⏳ Pending |
```

***REMOVED******REMOVED******REMOVED*** Blocking Issues

If an agent is blocked, document in roadmap:

```markdown
***REMOVED******REMOVED*** Current Blockers

| ***REMOVED*** | Blocker | Owner | Resolution |
|---|---------|-------|------------|
| 1 | Need sanitized metrics | Claude (Web) | Waiting for IDE export |
| 2 | DB connection failing | Claude Code (IDE) | Check Docker status |
```

---

***REMOVED******REMOVED*** Safe Work Allocation

***REMOVED******REMOVED******REMOVED*** Claude (Web) Safe Tasks

These tasks require no PII or database access:

***REMOVED******REMOVED******REMOVED******REMOVED*** Tier 1: No Dependencies
- Document solver algorithms
- Review MCP tool implementations
- Audit security patterns (code only)
- Update CLAUDE.md
- Consolidate API documentation
- Add TypeDoc/JSDoc comments
- Review error handling patterns

***REMOVED******REMOVED******REMOVED******REMOVED*** Tier 2: Needs Sanitized Data
- Analyze coverage gaps
- Identify constraint hotspots
- Recommend solver tuning
- Generate fairness reports
- Evaluate workload distribution

***REMOVED******REMOVED******REMOVED******REMOVED*** Tier 3: Code Quality
- Fix eslint warnings (frontend)
- Add missing type annotations
- Review test coverage gaps
- Improve error messages
- Refactor complex functions

***REMOVED******REMOVED******REMOVED*** Claude Code (IDE) Tasks

These tasks require full access:

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Operations
- Seed database from Airtable exports
- Run schedule generation
- Execute database migrations
- Query for debugging

***REMOVED******REMOVED******REMOVED******REMOVED*** Testing with Real Data
- Integration tests with DB
- Swap matching tests
- ACGME compliance validation
- UI testing with real schedules

***REMOVED******REMOVED******REMOVED******REMOVED*** Export Operations
- Generate production Excel exports
- Create PDF reports
- Export sanitized metrics for Web analysis

---

***REMOVED******REMOVED*** Branch Coordination

***REMOVED******REMOVED******REMOVED*** Branch Naming Convention

| Agent | Pattern | Example |
|-------|---------|---------|
| Claude (Web) | `claude/<task>-<session-id>` | `claude/plan-block-10-roadmap-IDOo9` |
| Claude Code (IDE) | `claude/<task>-<session-id>` | `claude/seed-db-block10-XyZ12` |
| Human | `feature/<description>` | `feature/add-notification-system` |

***REMOVED******REMOVED******REMOVED*** Avoiding Conflicts

1. **Check for active branches before starting:**
   ```bash
   git fetch origin
   git branch -r | grep claude/
   ```

2. **Use separate file domains:**
   - Claude (Web): `docs/`, `.github/`, non-PII code review
   - Claude Code (IDE): `backend/`, `frontend/`, database files

3. **Coordinate via roadmap document:**
   - Before starting, check roadmap for active tasks
   - Update roadmap when starting/completing tasks

***REMOVED******REMOVED******REMOVED*** Merge Strategy

1. Both agents create PRs targeting `origin/main`
2. Human reviews and merges
3. After merge, both agents rebase their working branches:
   ```bash
   git fetch origin main
   git rebase origin/main
   ```

---

***REMOVED******REMOVED*** Skill Usage by Agent

***REMOVED******REMOVED******REMOVED*** Skills Safe for Claude (Web)

| Skill | Use Case |
|-------|----------|
| `code-review` | Review implementations, identify issues |
| `security-audit` | Audit code for vulnerabilities |
| `acgme-compliance` | Reference ACGME rules (no data needed) |
| `test-writer` | Design test cases (mock data only) |
| `automated-code-fixer` | Fix lint/type errors |
| `code-quality-monitor` | Check quality gates |
| `changelog-generator` | Generate release notes from git |
| `pr-reviewer` | Review PR changes |
| `systematic-debugger` | Plan debugging approach |
| `database-migration` | Review migration files |

***REMOVED******REMOVED******REMOVED*** Skills Requiring Claude Code (IDE)

| Skill | Reason |
|-------|--------|
| `safe-schedule-generation` | Needs database access |
| `swap-management` | Needs real faculty data |
| `schedule-optimization` | Needs database for solver |
| `production-incident-responder` | Needs live system access |
| `xlsx` | May contain PII in exports |
| `pdf` | May contain PII in reports |

---

***REMOVED******REMOVED*** MCP Tool Safety

***REMOVED******REMOVED******REMOVED*** Read-Only Tools (Safe for Any Agent)

```
validate_schedule
detect_conflicts
analyze_swap_candidates
health_check
get_task_status
list_active_tasks
check_utilization_threshold
get_defense_level
```

***REMOVED******REMOVED******REMOVED*** Write Tools (Claude Code IDE Only)

```
generate_schedule (missing - needs implementation)
execute_swap (missing - needs implementation)
bulk_assign (missing - needs implementation)
start_background_task
cancel_task
```

***REMOVED******REMOVED******REMOVED*** Placeholder Tools (Return Mock Data)

These exist but return simulated data:
```
analyze_homeostasis
get_static_fallbacks
execute_sacrifice_hierarchy
calculate_blast_radius
analyze_le_chatelier
analyze_hub_centrality
assess_cognitive_load
get_behavioral_patterns
analyze_stigmergy
check_mtf_compliance
```

---

***REMOVED******REMOVED*** Error Handling

***REMOVED******REMOVED******REMOVED*** If Claude (Web) Accidentally Receives PII

1. **Do not process or store the data**
2. **Inform the human immediately:**
   ```
   WARNING: Received data that appears to contain PII.
   Please verify this data should be shared with Claude (Web).
   I will not process this until confirmed safe.
   ```
3. **Request sanitized version instead**

***REMOVED******REMOVED******REMOVED*** If Agents Edit Same File

1. **Check git status before committing:**
   ```bash
   git fetch origin
   git diff origin/<other-agent-branch> -- <file>
   ```

2. **If conflict detected:**
   - Stop and document the conflict
   - Let human resolve which version to keep
   - Rebase after resolution

***REMOVED******REMOVED******REMOVED*** If Database Operation Fails

1. **Claude Code (IDE) should:**
   - Check for recent backup
   - Document error in session notes
   - Attempt rollback if appropriate
   - Signal blocker in roadmap

2. **Claude (Web) should:**
   - Wait for IDE resolution
   - Continue with non-dependent tasks
   - Document waiting status

---

***REMOVED******REMOVED*** Session Startup Checklist

***REMOVED******REMOVED******REMOVED*** For Claude (Web)

```markdown
- [ ] Read CLAUDE.md for project context
- [ ] Read BLOCK_10_ROADMAP.md for current status
- [ ] Read SESSION_CAPABILITIES.md for available tools
- [ ] Check for pending Tier 1-3 tasks
- [ ] Verify no PII in provided context
- [ ] Identify independent work to begin
```

***REMOVED******REMOVED******REMOVED*** For Claude Code (IDE)

```markdown
- [ ] Read CLAUDE.md for project context
- [ ] Read BLOCK_10_ROADMAP.md for current status
- [ ] Verify database connectivity: `docker compose ps`
- [ ] Check for recent backup: `ls -la backups/postgres/`
- [ ] Identify checkpoint tasks to complete
- [ ] Plan sanitized export for Web handoff
```

***REMOVED******REMOVED******REMOVED*** For Human

```markdown
- [ ] Review roadmap for current checkpoint
- [ ] Decide which agent works on which tasks
- [ ] Share any required sanitized data with Web
- [ ] Review and merge completed PRs
- [ ] Approve strategic decisions
```

---

***REMOVED******REMOVED*** Anti-Patterns to Avoid

***REMOVED******REMOVED******REMOVED*** Don't Do This

| Anti-Pattern | Why It's Bad | Do This Instead |
|--------------|--------------|-----------------|
| Claude (Web) queries database | PII exposure | Request sanitized export |
| Both agents edit same file | Merge conflicts | Allocate files by domain |
| Skip checkpoint documentation | Lost coordination | Always update roadmap |
| Share raw Airtable exports with Web | Contains real names | Use anonymization script |
| Push to main directly | Bypasses review | Always use PR workflow |
| Ignore blocker signals | Wastes effort | Address blockers first |

***REMOVED******REMOVED******REMOVED*** Warning Signs

- Claude (Web) sees actual names in data → Stop, request sanitization
- Multiple `claude/` branches active → Check for conflicts
- Roadmap not updated in hours → Check agent status
- Tests failing after parallel work → Check for integration issues

---

***REMOVED******REMOVED*** Quick Reference Commands

***REMOVED******REMOVED******REMOVED*** Claude (Web) Commands

```bash
***REMOVED*** Read code for review
Read: backend/app/scheduling/engine.py

***REMOVED*** Search for patterns
Grep: pattern="def.*schedule" glob="*.py"

***REMOVED*** Find files
Glob: pattern="**/*constraint*.py"

***REMOVED*** Invoke skill
Skill: code-review
Skill: security-audit
```

***REMOVED******REMOVED******REMOVED*** Claude Code (IDE) Commands

```bash
***REMOVED*** Database operations
docker compose exec db psql -U scheduler -d residency_scheduler

***REMOVED*** Run tests
cd backend && pytest

***REMOVED*** Generate schedule
docker compose exec backend python -m app.scheduling.engine --block 10

***REMOVED*** Export sanitized metrics
python scripts/export_sanitized_metrics.py --block 10 -o /tmp/metrics.json

***REMOVED*** Create backup before risky operations
./scripts/backup-db.sh --docker
```

---

***REMOVED******REMOVED*** Version History

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-24 | Claude (Web) | Initial document creation |

---

*This document should be updated as new patterns emerge from parallel work sessions.*
