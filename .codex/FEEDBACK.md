# Codex Automation Feedback Log

> Append findings after each automation run. Read this before starting work to learn from past runs.
> Format: `## [automation-name] — YYYY-MM-DD HH:MM` followed by outcome, overlap, insight, suggestion.

---

## Initial Setup — 2026-02-10

**Context**: Multi-agent coordination established. Claude coder (Opus 4.6, Mac Mini) handles mechanical TODO.md tasks during the day. Codex handles deeper analysis during sleep hours (0100-0500 HST). `sync-claude-activity.sh` runs every 15 min on the laptop to keep `RECENT_ACTIVITY.md` and `TODO.md` in sync.

**Known overlap areas**:
- Type hints / mypy — both agents may work on this. Claude does it via TODO items; Codex via `check-for-mypy-issues` and `type-coverage-expansion`. Check RECENT_ACTIVITY.md before starting.
- Lint fixes — Claude does bulk fixes; Codex validates. If Claude already fixed it, report "nothing-to-do".
- Test coverage — Claude writes tests from TODO items; Codex scans for gaps. Complementary but check for overlap.

**Suggestion**: If 3+ consecutive runs of an automation find nothing to do, consider reducing its frequency or disabling it.

## self-augment — 2026-02-17

**Outcome**: completed
**Context**: PR #1149 review revealed both high-value patterns (decorator typing, async factory bug fix, test determinism) and one regression (removed intentional eslint-disable in useDebounce.ts). This self-augment run incorporates both lessons.
**Insight**: Type annotation work on decorator factories is Codex's strongest contribution pattern — preserves function signatures, catches real bugs (async def on factories), and doesn't touch business logic. Lint suppression removal is the highest-risk pattern — looks like cleanup but can reintroduce type errors.
**Suggestion**: Consider adding a `decorator-factory-audit` automation at 01:32 focused specifically on finding untyped decorator factories and `async def` factory bugs. This is high-signal, low-risk work that Codex excels at.
