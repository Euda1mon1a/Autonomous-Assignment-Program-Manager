# AI Agent Instructions

This document provides guidance for AI coding assistants (Codex, Claude, etc.) working on this codebase.

## Project Overview

**Residency Scheduler** - A medical residency program scheduling system with ACGME compliance validation. The system manages complex scheduling for medical residency programs while ensuring compliance with federal regulations.

### Tech Stack
- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery/Redis
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **Monitoring**: Prometheus, Grafana, Loki

---

## Instruction File Discovery (Claude Code vs Codex CLI)

Two AI systems work on this repo. They read **different files** by default. Understanding this prevents guardrails from being invisible to one system.

### Claude Code (Opus 4.6 / Sonnet 4.5)

| Priority | File | Scope |
|----------|------|-------|
| 1 | `CLAUDE.md` (repo root) | Always injected into context |
| 2 | `.claude/` directory | Project settings, memory, skills |
| 3 | MCP tools (97+) | Validation, compliance, RAG search |
| 4 | Pre-commit hooks (30+) | Enforce rules at commit time |
| 5 | `~/.claude/projects/.../memory/` | Private auto memory (per-project, persistent) |

**Key point:** Claude Code does NOT read `AGENTS.md` unless told to. All project guardrails live in `CLAUDE.md`.

### Codex CLI (GPT-5.3-codex)

| Priority | File | Scope |
|----------|------|-------|
| 1 | `~/.codex/AGENTS.md` | Global instructions (if exists) |
| 2 | `AGENTS.override.md` | Per-directory override (root → CWD walk) |
| 3 | `AGENTS.md` | Per-directory instructions (root → CWD walk) |
| 4 | `project_doc_fallback_filenames` | Config: extra files to read (e.g., `CLAUDE.md`) |
| 5 | `.codex/config.toml` | Repo-level Codex configuration |

**Key point:** Codex does NOT read `CLAUDE.md` unless configured as a fallback in `project_doc_fallback_filenames`. It also does NOT run pre-commit hooks during file modification (only at `git commit`).

### Current Configuration (post-Feb 2026 fix)

After the Feb 2026 audit, both systems are configured to cross-read:

```toml
# ~/.codex/config.toml AND .codex/config.toml
project_doc_fallback_filenames = ["AGENTS.md", "CLAUDE.md"]
project_doc_max_bytes = 65536
```

### Guardrail File Hierarchy

| File | Purpose | Read by Claude | Read by Codex |
|------|---------|----------------|---------------|
| `CLAUDE.md` | Full project rules, security, API contracts | Always | Via fallback config |
| `AGENTS.md` (root) | Condensed hard boundaries | If referenced | Always at startup |
| `.codex/AGENTS.md` | Full Codex rules + anti-patterns | If referenced | Always (directory walk) |
| `docs/development/AGENTS.md` | This file: monitoring patterns, shared context | If referenced | If referenced |

### Why This Matters (Feb 2026 Lesson)

On Feb 14, 2026, an audit of Codex CLI output on `continuous/codex-work` found **20 issues (3 P1)** across 101 modified files. Root cause: all guardrails (validation rules, security requirements, "never modify" lists) were in `CLAUDE.md` — a file Codex never read. `.codex/AGENTS.md` line 179 said "See CLAUDE.md" but that was a dead reference.

**Fix:** Inline all critical guardrails directly into the files each system reads. The fallback config is belt-and-suspenders — the primary defense is having rules IN the file, not just referencing another file.

### Known Codex Failure Patterns (from audit)

These patterns recurred when Codex lacked guardrails. They are now documented in `.codex/AGENTS.md` and root `AGENTS.md` as FORBIDDEN:

| Pattern | Risk | Description |
|---------|------|-------------|
| Flexible Validation | P1 | Removes Pydantic `min_length`, `max_length`, `ge`, `le` constraints |
| Route Alias | P1 | Registers same router at multiple URL prefixes |
| Normalization Layer | P2 | Adds backend `_normalize_*()` functions (axios already handles this) |
| Improved Error Messages | P2 | Replaces generic errors with `str(e)`, leaking internals |
| Defensive Fallback | P2 | Wraps ops in try/except with silent alternate path |
| Type Weakening | P2 | Changes `dict[str, int]` to `dict[str, Any]`, adds `extra="allow"` |
| Smuggled Changes | P2 | Changes algorithm constants while calling commit "import cleanup" |

### Enforcement Layers

| Layer | Claude Code | Codex CLI |
|-------|-------------|-----------|
| Instruction files | `CLAUDE.md` (always) | `AGENTS.md` (always) |
| Pre-commit hooks | 30+ hooks enforce at commit | Same hooks at `git commit` only |
| MCP tools | 97+ tools for validation | Same tools if MCP configured |
| Runtime validation | Pydantic, SQLAlchemy constraints | Same (runtime) |
| File modification | Hooks fire during edits | No enforcement during edits |

**Gap:** Codex modifies files freely, then hooks only catch violations at commit time. If Codex commits with `--no-verify` or the hook doesn't cover the pattern, violations slip through.

### Codex Model Tiers

Two Codex models are available. Default stays on full 5.3-Codex for automations; Spark is opt-in for interactive use.

| Model | ID | Speed | Context | Best For |
|-------|----|-------|---------|----------|
| 5.3-Codex | `gpt-5.3-codex` | Standard | 192K | Nightly automations, multi-file tasks, deep analysis |
| 5.3-Codex-Spark | `gpt-5.3-codex-spark` | 1000+ tok/s | 128K | Interactive pairing, quick single-file fixes |

**Spark** (Feb 2026, Cerebras WSE-3) is a speed-optimized variant. All guardrails still apply. Spark should self-limit to single-file scope; multi-file or FORBIDDEN-category tasks stay on regular Codex or Claude.

---

## Codex Background Monitoring Instructions

When performing background code health assessments, focus on these categories of subtle issues that accumulate over time.

### 🔴 Priority 1: Code Rot Detection

#### 1.1 Stubbed/Placeholder Code
Look for functions that appear complete but are actually placeholders:

```python
# Search patterns:
# - "# TODO" in function bodies
# - "# Placeholder" comments
# - Functions returning hardcoded False/None
# - "pass" as sole implementation
```

**Known issues to track:**
- `backend/app/services/swap_executor.py:60-62` - TODOs indicate non-functional persistence
- `backend/app/services/swap_executor.py:84-93` - `rollback_swap()` and `can_rollback()` return hardcoded False

#### 1.2 Silent Failure Patterns
Identify exception handlers that swallow errors:

```python
# Anti-patterns to flag:
except (ValueError, TypeError):
    pass  # Silent failure - no logging

except Exception as e:
    continue  # Error ignored
```

**Known issues:**
- `backend/app/api/routes/portal.py:443,451,547,556` - Invalid dates silently disappear

#### 1.3 Placeholder Workarounds
Find temporary hacks that assume future fixes:

```python
# Example anti-pattern:
target_faculty_id = faculty.id  # Placeholder
```

**Known issues:**
- `backend/app/api/routes/portal.py:271` - Uses faculty's own ID as placeholder for marketplace requests

---

### 🟡 Priority 2: Consistency Drift

#### 2.1 DateTime Handling
The codebase mixes UTC and local time. Flag any new instances:

```python
# Inconsistent - should pick ONE:
datetime.utcnow()  # Some files use this
datetime.now()     # Other files use this
```

**Recommendation:** Standardize on `datetime.now(timezone.utc)` per Python 3.11+ best practices.

#### 2.2 Response Format Consistency
Three response patterns exist - flag divergence:

| Pattern | Example Location | When to Use |
|---------|------------------|-------------|
| Inline dict | `portal.py:380` | Avoid - use Pydantic |
| Pydantic schema | `portal.py:114` | Preferred |
| Service result | `swap_request_service.py:232` | For service layer |

#### 2.3 Error Handling Patterns
Ensure consistent HTTPException usage:
- Include error codes
- Don't expose internal details to clients
- Log before raising

---

### 🟢 Priority 3: Type Safety Erosion

#### 3.1 Untyped Dictionaries
Flag new uses of `dict[str, Any]` in core business logic:

```python
# Anti-pattern in service/business logic:
def process_data(data: dict[str, Any]) -> dict[str, Any]:
    ...

# Preferred - use TypedDict or Pydantic:
class ProcessInput(TypedDict):
    field1: str
    field2: int
```

**Known hotspot:** `backend/app/resilience/mtf_compliance.py` - 40+ occurrences

#### 3.2 Type Ignore Comments
Track and reduce `# type: ignore` usage:

**Known issues:**
- `backend/app/resilience/simulation/__init__.py:42`
- `backend/app/resilience/simulation/base.py:20,177`

#### 3.3 Missing Type Annotations
Flag functions without return type hints in core modules:

```python
# Missing annotation:
def _get_week_start(any_date):  # No type hint!
    ...

# Should be:
def _get_week_start(any_date: date) -> date:
    ...
```

---

### 🔵 Priority 4: Documentation Drift

#### 4.1 Docstring vs Implementation
Compare docstrings against actual behavior:

**Known issue:**
- `portal.py:51-55` - Docstring promises "conflict indicators" but `has_conflict` always returns `False`

#### 4.2 TODO Age Tracking
Flag TODOs older than 6 months. Check git blame for age.

#### 4.3 Dead Documentation References
Verify referenced docs exist:
- ~~`docs/TODO_RESILIENCE.md`~~ - Fixed: now references `docs/architecture/resilience.md`

---

### ⚪ Priority 5: Performance Patterns

#### 5.1 N+1 Query Detection
Look for patterns that trigger multiple queries:

```python
# Potential N+1:
assignments = db.query(Assignment).all()
for a in assignments:
    print(a.block.date)  # Lazy load per iteration
```

**Known hotspots:** `portal.py` has 54+ `.all()` queries

#### 5.2 Missing Eager Loading
Flag relationship access without `joinedload`/`selectinload`:

```python
# Should use eager loading:
.options(joinedload(Assignment.block))
```

---

## Assessment Output Format

When reporting findings, use this structure:

```markdown
## Code Health Assessment - [DATE]

### Critical Issues (Action Required)
| File:Line | Category | Description | Age |
|-----------|----------|-------------|-----|
| ... | ... | ... | ... |

### Warnings (Monitor)
| File:Line | Category | Description | Age |
|-----------|----------|-------------|-----|
| ... | ... | ... | ... |

### Improvements (Nice to Have)
| File:Line | Category | Description |
|-----------|----------|-------------|
| ... | ... | ... |

### Metrics
- Total TODOs: X (Y new since last assessment)
- Type coverage: X%
- Silent exception handlers: X
- Placeholder code blocks: X
```

---

## Files to Prioritize

These files have the highest concentration of known issues:

1. `backend/app/services/swap_executor.py` - Stub implementations
2. `backend/app/api/routes/portal.py` - Multiple pattern issues
3. `backend/app/notifications/tasks.py` - Stubbed email/webhook
4. `backend/app/resilience/mtf_compliance.py` - Type safety

---

## What NOT to Flag

- Test files using mocks/stubs (intentional)
- `# type: ignore` on third-party library issues
- TODOs in test files
- Placeholder data in fixtures/seeds

---

## Conventions to Enforce

1. **Imports**: Group stdlib, third-party, local with blank lines
2. **Logging**: Use structured logging with context
3. **Errors**: Raise specific exceptions, not generic `Exception`
4. **Types**: Prefer Pydantic models over raw dicts
5. **Queries**: Use repository pattern, not inline queries in routes
