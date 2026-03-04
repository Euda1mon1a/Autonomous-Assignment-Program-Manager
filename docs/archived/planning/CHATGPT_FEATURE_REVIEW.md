# ChatGPT Feature Review: Codex & Pulse

> **Date:** 2025-12-18
> **Purpose:** Questions to explore when evaluating OpenAI's Codex and Pulse for potential workflow improvements

---

## OpenAI Codex (Autonomous Coding Agent)

Codex is a cloud-based software engineering agent powered by codex-1 (optimized o3) and GPT-5-Codex. It can work autonomously for 7+ hours on complex tasks, running in isolated environments with full codebase access.

### Questions to Explore

#### 1. Multi-Agent Parallel Task Handling
Given our `PARALLEL_10_TERMINAL_ORCHESTRATION.md` approach:
- How does Codex coordinate multiple parallel agents working on the same codebase?
- What conflict resolution exists when agents touch the same files?
- Can you specify dependencies between parallel tasks?

#### 2. Test-Driven Iteration
Codex "iteratively runs tests until passing":
- Does it understand domain-specific test markers (e.g., `pytest -m acgme`)?
- How does it handle complex validation logic like ACGME compliance rules?
- Can it be configured with custom test commands beyond standard `pytest`/`npm test`?

#### 3. Large Refactor Capability
- Could it handle cross-cutting refactors like "convert resilience framework to async/await" across `backend/app/resilience/*.py`?
- How does it maintain consistency across multiple related files?
- What's the largest refactor scope it can handle reliably?

#### 4. PR Quality
- What do auto-generated PRs look like?
- Commit message style and description quality?
- Does it follow existing repo conventions?

#### 5. Codebase Understanding
- How well does it understand existing architecture patterns?
- Can it reference and follow patterns from `ARCHITECTURE.md`?
- How does it handle domain-specific concepts (ACGME rules, medical scheduling)?

---

## ChatGPT Pulse (Proactive AI Assistant)

Pulse delivers personalized morning briefings based on chats, memory, and connected apps (Gmail, Google Calendar). Currently Pro-only ($200/month).

### Questions to Explore

#### 1. Calendar Integration for Scheduling Systems
- Could it surface alerts like "ACGME compliance deadline approaching"?
- Can it integrate with custom calendar data beyond Google Calendar?
- How would it handle medical residency schedule data?

#### 2. Proactive Research & Monitoring
- Can "overnight research based on chats" track GitHub issues and summarize them?
- Could it monitor CI/CD pipeline status and surface failures?
- How customizable are the research topics?

#### 3. Team Collaboration
- Can multiple team members share Pulse configurations?
- How does it handle project-specific context vs personal preferences?

---

## Comparison Points for Our Project

| Feature | Codex | Pulse | Our Current Approach |
|---------|-------|-------|---------------------|
| Parallel task execution | Cloud agents | N/A | 10-terminal orchestration |
| Test automation | Built-in iteration | N/A | pytest + Jest + Playwright |
| Proactive monitoring | Via PR reviews | Morning briefs | Celery background tasks |
| Calendar/scheduling | N/A | Google Calendar | Custom ACGME scheduler |

---

## Next Steps

1. [x] Test Codex on a medium-complexity feature branch
2. [x] Evaluate PR quality against our CONTRIBUTING.md standards
3. [ ] Assess Pulse calendar integration feasibility
4. [ ] Compare autonomous task completion times

---

## Codex Evaluation Results (2025-12-18)

We tested Codex on a task to "Locate tasks in agents.md" which resulted in changes across 6 backend files. Here's what we learned:

### What Codex Does Well ✅

| Task Type | Example | Quality |
|-----------|---------|---------|
| **Bug fixes** | Removed incorrect `// 2` division in swap counting | Excellent |
| **Import corrections** | Fixed non-existent module paths (`app.api.deps` → `app.core.security`) | Excellent |
| **Type hint fixes** | `callable` → `Callable`, explicit `datetime.date` annotations | Good |
| **Defensive coding** | Added null-safety (`??` operators), `.filter(Boolean)` | Good |
| **Security defaults** | Auto-generate secrets instead of empty strings | Good (with caveats) |

### What Codex Does Poorly ❌

| Task Type | Example | Problem |
|-----------|---------|---------|
| **Large service rewrites** | Attempted to replace 589-line audit_service.py | Gutted working code, replaced with stubs returning empty data |
| **Domain-specific logic** | Removed ACGME compliance checking, user resolution | Didn't understand business requirements |
| **Complete implementations** | New `AuditService` class had stub methods: `return []` | Passes tests but breaks functionality |

### Key Finding: Test-Passing ≠ Correctness

Codex ran `pytest backend/tests/test_audit_service.py` and it passed. However, the tests only covered basic operations—the 400+ lines of lost business logic (user resolution, entity names, ACGME override detection) were never tested.

**Lesson:** Codex optimizes for test passage, not functional correctness.

---

## Codex Usage Guidelines

### RECOMMENDED Tasks for Codex

```
✅ Fix import errors and module path issues
✅ Fix type annotation problems (mypy errors)
✅ Fix obvious bugs caught by tests (off-by-one, null checks)
✅ Update dependencies and fix deprecation warnings
✅ Standardize code formatting and style issues
✅ Add null-safety and defensive coding patterns
✅ Fix linter warnings and static analysis issues
```

### AVOID Giving Codex These Tasks

```
❌ Rewrite or refactor entire service files
❌ Add new features requiring domain knowledge
❌ Modify business logic (ACGME rules, scheduling constraints)
❌ Change architectural patterns
❌ Consolidate or merge related modules
❌ Implement complex validation logic
```

### Codex Task Prompt Template

When assigning tasks to Codex, use this structure:

```markdown
## Task Type: Bug Fix / Import Fix / Type Annotation Fix

## Scope: (specific file paths only)
- backend/app/core/config.py
- backend/app/models/calendar_subscription.py

## Specific Instructions:
- Fix the import error on line X
- Do NOT modify business logic
- Do NOT add new classes or methods
- Do NOT refactor surrounding code

## Testing:
- Run: pytest backend/tests/test_specific_file.py
- Verify: imports resolve correctly

## Constraints:
- Changes should be < 20 lines total
- Preserve all existing functionality
- Do not remove any code unless it's clearly dead
```

### Review Checklist for Codex PRs

Before accepting any Codex changes:

- [ ] **Line count sanity check**: Large additions (+100 lines) require manual review
- [ ] **Imports preserved**: No schema/model classes redefined locally
- [ ] **Stub detection**: Search for `return []` or `return {}` patterns
- [ ] **Business logic intact**: Compare functions before/after
- [ ] **Test coverage**: Does the test suite actually cover the changed logic?
- [ ] **Domain concepts**: Are ACGME, compliance, scheduling terms still present?

---

## References

- [Introducing Codex | OpenAI](https://openai.com/index/introducing-codex/)
- [Introducing upgrades to Codex | OpenAI](https://openai.com/index/introducing-upgrades-to-codex/)
- [Introducing ChatGPT Pulse | OpenAI](https://openai.com/index/introducing-chatgpt-pulse/)
- [OpenAI launches ChatGPT Pulse | TechCrunch](https://techcrunch.com/2025/09/25/openai-launches-chatgpt-pulse-to-proactively-write-you-morning-briefs/)
