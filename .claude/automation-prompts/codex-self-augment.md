# Codex Self-Augmentation Prompt

> **Target:** Codex CLI (`gpt-5.3-codex`) or Codex macOS App
> **Branch:** `codex/self-augment-feb17`
> **Scope:** Update Codex guardrails, automation prompts, and feedback log based on lessons from Feb 14-17 triage cycle

---

## Context

You are Codex, updating your own configuration files and automation prompts. A deep audit of your recent output (PRs #1119, #1129-1138, #1144, #1149) identified patterns where you produced genuinely valuable work AND patterns where you introduced bugs. This prompt teaches you to do more of the good and less of the bad.

**Key finding from PR #1149 review (today):** Your type annotation work (adding `ParamSpec`, `TypeVar`, return types to decorator factories) is HIGH VALUE. You correctly identified that `time_async_function` was buggy (`async def` on a decorator factory). But you also removed an intentional `// eslint-disable-next-line @typescript-eslint/no-explicit-any` comment in `useDebounce.ts`, changing `any[]` to `unknown[]`, which broke a test. The developer put that suppression there deliberately because TypeScript's `strictFunctionTypes` makes `unknown[]` incompatible with typed callbacks via contravariance.

**Lesson:** Lint suppression comments exist for reasons. Before removing one, verify the reason is gone. If the comment says `eslint-disable` or `# noqa` or `# type: ignore`, the developer likely hit a real type system limitation — don't silently delete their workaround.

---

## Mandatory Preflight

```bash
git fetch origin && git checkout main && git pull
git status --porcelain  # Must be empty
git checkout -b codex/self-augment-feb17 main
```

---

## Task 1: Update `.codex/AGENTS.md`

Read the current `.codex/AGENTS.md` and make these specific changes:

### 1a. Add new Safety Classification entries

In the "Code Change Safety Classification" table, add these rows:

| Change Type | Safety | Rule |
|---|---|---|
| Add `ParamSpec`/`TypeVar` to decorator factories | SAFE | Preserves function signatures through decoration |
| Add return type annotations to functions | SAFE | Annotation-only, no behavioral change |
| Fix `async def` on non-async decorator factories | SAFE | `async def` on a factory that returns a decorator is always a bug |
| Remove lint suppression comments (`eslint-disable`, `noqa`, `type: ignore`) | **CHECK** | Verify the underlying type issue is actually resolved first. These comments exist because the developer hit a real limitation. |
| Change `any` to `unknown` in TypeScript generics | **CHECK** | May break callers due to contravariance under `strictFunctionTypes`. Test with `npx tsc --noEmit` before committing. |
| Add `.get()` with default to dict access on known-shape dicts | CHECK | Masks `KeyError` bugs with silent empty strings. Only do this on dicts with unknown/dynamic keys. |

### 1b. Add new Known Failure Pattern

After the existing "Defensive Fallback" pattern, add:

```markdown
### "Lint Comment Removal" Anti-Pattern
Removing `// eslint-disable`, `# noqa`, `# type: ignore`, or `@ts-expect-error` comments without verifying the underlying issue is resolved. These comments exist because the developer hit a real type system limitation (e.g., TypeScript contravariance, SQLAlchemy column operators, dynamic metaprogramming). Removing them silently reintroduces the type error the comment was suppressing. **Before removing any suppression comment, verify with the language's type checker that the code compiles cleanly without it.**
```

### 1c. Update MCP tool count

Change `34+ AI tools` to `97+ AI tools` in the Project Context section.

### 1d. Add Schema Drift awareness

After the "Files to NEVER Modify" section, add:

```markdown
## Schema Drift Awareness

Some model files define database tables that have NO Alembic migrations. These tables do not exist in the database. Do not write code that queries them, and do not present them as functional in documentation.

See `docs/development/SCHEMA_DRIFT_TRACKING.md` for the full list (12 tables across 7 model files: webhooks, calendar_subscriptions, export_jobs, oauth2, schema_versions, state_machine).
```

### 1e. Add "Good Pattern" section

After Known Failure Patterns, add a section showing what Codex does WELL (to reinforce):

```markdown
## Proven High-Value Patterns

These patterns from recent Codex output were genuinely useful and should be repeated:

### Decorator Factory Typing
Adding `ParamSpec`/`TypeVar` return types to decorator factories. This preserves the decorated function's signature through the wrapper, enabling proper IDE autocompletion and type checking. Example from PR #1149:

```python
P = ParamSpec("P")
R = TypeVar("R")

def with_timeout(
    timeout: float, error_message: str | None = None
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            ...
```

### Test Determinism
Adding `np.random.seed(42)` as autouse fixtures in tests that use random data. Prevents flaky failures without changing production code.

### Async Decorator Factory Bug Detection
Identifying `async def` on decorator factories (which makes them return coroutines instead of decorators). The factory itself should be a plain `def`; only the inner wrapper should be `async def`.
```

---

## Task 2: Update Root `AGENTS.md`

Read the current root `AGENTS.md` and add one line to the "Known Anti-Patterns to Avoid" list:

```markdown
- Lint Comment Removal: deleting `eslint-disable`, `noqa`, or `type: ignore` comments without verifying the underlying type issue is actually resolved.
```

---

## Task 3: Update Automation Prompt Templates

### 3a. Update `type-hygiene.md`

Add rule 6 to the Type Hygiene Rules:

```
6. Lint suppression comments:
   - NEVER remove `# noqa`, `# type: ignore`, `// eslint-disable`, or `@ts-expect-error` comments
   - These exist because the developer hit a real type system limitation
   - If you think you've fixed the underlying issue, verify with the type checker FIRST:
     Backend: python -m mypy <file> --ignore-missing-imports
     Frontend: npx tsc --noEmit 2>&1 | grep <filename>
   - Only remove the suppression comment if the type checker passes WITHOUT it
```

### 3b. Update `bug-fix.md`

Add rule 6 to the Bug Fix Rules:

```
6. Preserve intentional workarounds:
   - If a file contains `# HACK:`, `# WORKAROUND:`, or lint suppression comments,
     these are intentional. Do NOT remove them as part of a "cleanup."
   - If you believe the workaround is no longer needed, verify by removing it
     and running the relevant checker. If it fails, put it back.
```

### 3c. Create new automation prompt: `decorator-audit.md`

Create `.claude/automation-prompts/decorator-audit.md`:

```markdown
# Decorator Audit Prompt Template

> For: type-hygiene, daily-bug-scan
> Paste the preflight block from `preflight.md` first, then this.

## Decorator Factory Audit

Scan for two high-value patterns in ONE directory per run:

### Pattern 1: Missing return types on decorator factories
Find functions that return decorators but lack return type annotations:

```bash
# Find decorator factories (functions that define and return inner functions)
grep -rn "def decorator\|def wrapper" backend/app/<directory>/ | head -20
```

Add `ParamSpec`/`TypeVar` typing where missing. Use the pattern from PR #1149.

### Pattern 2: `async def` on decorator factories (BUG)
Find decorator factories incorrectly marked as `async def`:

```bash
grep -rn "async def.*operation.*metadata\|async def.*timeout\|async def.*decorator" backend/app/ | grep -v "wrapper\|inner"
```

A decorator FACTORY should be `def`, not `async def`. The inner WRAPPER can be `async def`.
If the factory is `async def`, using `@factory(args)` returns a coroutine object instead of a decorator.

Fix: Change `async def factory_name(...)` to `def factory_name(...)`. Keep the inner wrapper as `async def`.

### Verification
After changes:
```bash
python3 scripts/ops/codex_worktree_env_exec.py -- python -m py_compile <changed_file>
python3 scripts/ops/codex_worktree_env_exec.py -- pytest <related_test_file> -v
```
```

---

## Task 4: Update `.codex/FEEDBACK.md`

Append this entry:

```markdown
## self-augment — 2026-02-17

**Outcome**: completed
**Context**: PR #1149 review revealed both high-value patterns (decorator typing, async factory bug fix, test determinism) and one regression (removed intentional eslint-disable in useDebounce.ts). This self-augment run incorporates both lessons.
**Insight**: Type annotation work on decorator factories is Codex's strongest contribution pattern — preserves function signatures, catches real bugs (async def on factories), and doesn't touch business logic. Lint suppression removal is the highest-risk pattern — looks like cleanup but can reintroduce type errors.
**Suggestion**: Consider adding a `decorator-factory-audit` automation at 01:32 focused specifically on finding untyped decorator factories and `async def` factory bugs. This is high-signal, low-risk work that Codex excels at.
```

---

## Task 5: Create New Automation

Create the automation at `~/.codex/automations/decorator-factory-audit/automation.toml`:

```toml
id = "decorator-factory-audit"
name = "Decorator Factory Audit"
status = "ACTIVE"
rrule = "RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=32;BYDAY=MO,WE,FR"

[prompt]
text = """
## Mandatory Preflight
<paste contents of .claude/automation-prompts/preflight.md>

## Decorator Factory Audit
<paste contents of .claude/automation-prompts/decorator-audit.md>

Target directory for this run: Pick the next unaudited directory from this rotation:
1. backend/app/core/
2. backend/app/middleware/
3. backend/app/services/
4. backend/app/api/routes/
5. backend/app/scheduling/
6. backend/app/resilience/

Check FEEDBACK.md for which directories were already covered. Pick the next one in order.
"""
```

---

## Verification

Before committing:

1. Confirm `.codex/AGENTS.md` still reads cleanly (no broken markdown)
2. Confirm root `AGENTS.md` is under 70 lines (keep it condensed)
3. Confirm all automation prompt templates have the preflight reference
4. Run: `wc -c .codex/AGENTS.md` — should be under 20KB

```bash
git add .codex/AGENTS.md AGENTS.md .codex/FEEDBACK.md .claude/automation-prompts/
git commit -m "$(cat <<'EOF'
chore: codex self-augment — add lint-comment safety, decorator audit, schema drift awareness

Incorporates lessons from PR #1149 review:
- New safety classification for lint suppression removal (CHECK, not SAFE)
- New anti-pattern: "Lint Comment Removal"
- New proven pattern: decorator factory typing with ParamSpec/TypeVar
- Schema drift awareness section (12 tables with no migrations)
- New automation prompt: decorator-factory-audit
- Updated type-hygiene and bug-fix templates
- MCP tool count corrected (97+ not 34+)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"

git push -u origin codex/self-augment-feb17
gh pr create --title "chore: codex self-augment — lint safety, decorator audit, schema drift" --body "$(cat <<'EOF'
## Summary
- Add lint suppression removal as CHECK (not SAFE) in safety classification
- Add "Lint Comment Removal" anti-pattern based on useDebounce.ts incident
- Add "Proven High-Value Patterns" section reinforcing decorator typing
- Add schema drift awareness section
- New automation prompt: decorator-factory-audit
- Update type-hygiene and bug-fix templates with suppression comment rules
- Correct MCP tool count (97+ not 34+)

## Test plan
- [ ] Verify AGENTS.md renders correctly
- [ ] Verify automation prompt templates reference preflight
- [ ] Spot-check safety classification table is complete

🤖 Generated with Codex self-augmentation
EOF
)"
```

---

## What NOT to Change

- Do NOT modify `CLAUDE.md` — that's Claude's domain
- Do NOT modify any Python or TypeScript source code in this run
- Do NOT modify automation schedules for existing automations (only create new ones)
- Do NOT modify `.codex/config.toml` — MCP config is stable
