# AAPM Merge Roadmap — Human-in-the-Loop Policy

> Which agent changes can eventually auto-merge vs which always need human eyes.
> Start conservative. Earn trust incrementally.

---

## Current State: ALL branches require manual review

No auto-merge for AAPM. Every `claude/*` and `codex/*` branch is reviewed by human before merge. The `aapm-review.sh` Opus agent provides a pre-review (APPROVE / NEEDS_WORK / BLOCK verdicts) but does NOT merge.

---

## Tier 1: Always Human-in-the-Loop (NEVER auto-merge)

These touch scheduling logic, compliance, or domain knowledge that lives in Aaron's head.

| Category | Why | Examples |
|----------|-----|---------|
| **Scheduling engine** | Constraint logic, solver parameters, block assignment rules | `backend/app/scheduling/engine.py`, `acgme_validator.py`, constraint files |
| **ACGME compliance** | Regulatory rules, work hour calculations, supervision ratios | Any file in `scheduling/`, compliance validators |
| **Domain models** | Schema changes cascade everywhere, need migration planning | `backend/app/models/*.py`, Alembic migrations |
| **Business logic** | Swap rules, faculty assignment logic, coverage calculations | `services/swap_*.py`, `services/schedule_*.py`, `services/faculty_*.py` |
| **Security** | Auth, permissions, OPSEC/PERSEC, data handling | `core/security.py`, `core/config.py`, auth routes |
| **API contracts** | Breaking changes affect frontend, MCP, external consumers | Route signatures, schema changes, response format changes |
| **Infrastructure** | Docker, CI/CD, deployment, database config | `docker-compose.yml`, `.github/`, `alembic.ini` |
| **MCP tools** | Agent capabilities, validation logic | `mcp-server/src/tools/` |

**Why these can never auto-merge**: The scheduling logic encodes institutional knowledge (rotation patterns, faculty preferences, MTF constraints, call rules) that no AI agent fully understands. A "fix" that looks correct syntactically could break a scheduling invariant that only Aaron knows about.

---

## Tier 2: Opus Pre-Review Required (auto-merge candidate — FUTURE)

These are mechanical improvements where Opus review is sufficient quality gate. NOT enabled yet — requires track record of accurate Opus reviews.

| Category | Criteria for auto-merge | Gate |
|----------|------------------------|------|
| **Lint fixes** | ruff/eslint auto-fixes, formatting only | Opus APPROVE + tests pass |
| **Type annotations** | Adding types to untyped code (no logic changes) | Opus APPROVE + mypy passes |
| **Dead code removal** | Removing clearly unused imports, functions, variables | Opus APPROVE + tests pass |
| **Test additions** | New tests only (no source changes) | Opus APPROVE + all tests pass |
| **Documentation** | Docstrings, README, comments (no code changes) | Opus APPROVE |
| **Dependency updates** | Patch/minor version bumps (no breaking changes) | Opus APPROVE + tests pass |

**Graduation criteria** (before enabling auto-merge for any tier-2 category):
1. 20+ consecutive APPROVE verdicts from Opus that human also agreed with
2. Zero false-positive APPROVEs (Opus said APPROVE but human would have blocked)
3. Human explicitly enables the category in `aapm-review.sh` config

---

## Tier 3: Auto-merge Ready (FUTURE — after trust established)

Categories that have graduated from Tier 2 after meeting all criteria.

| Category | Enabled date | Notes |
|----------|-------------|-------|
| (none yet) | — | Earning trust first |

---

## Roadmap

### Phase 1: Manual Everything (CURRENT — Feb 2026)
- All branches require human merge
- Opus reviews provide pre-screening (APPROVE/NEEDS_WORK/BLOCK)
- Review verdicts logged to `~/.openclaw/state/aapm-review/review-log.md`
- Track Opus accuracy: human agrees/disagrees with each verdict

### Phase 2: Track Record (target: Mar 2026)
- Compare Opus verdicts vs human decisions for 4+ weeks
- Identify categories where Opus consistently matches human judgment
- Build confidence in specific categories

### Phase 3: Selective Auto-merge (target: when ready)
- Enable auto-merge for graduated Tier 2 categories ONLY
- Add pre-merge test gate (tests must pass on branch before merge)
- Human still reviews all Tier 1 changes
- Weekly digest of auto-merged changes for human awareness

### Phase 4: Steady State
- Most mechanical changes auto-merge after Opus review
- Scheduling/compliance/security always human-reviewed
- Exception: any change touching >5 files or >500 lines bumps to human review regardless of category

---

## How to Review Branches

```bash
# On laptop — fetch Mini branches
git fetch mini

# See what's waiting
git branch -r | grep mini/claude

# Review a specific branch
git log main..mini/claude/2026-02-10-fix-something --oneline
git diff main..mini/claude/2026-02-10-fix-something

# Merge if approved
git merge mini/claude/2026-02-10-fix-something --no-ff

# Or cherry-pick specific commits
git cherry-pick <sha>
```

Check the Opus review first: `~/.openclaw/state/aapm-review/review-log.md` (on Mini) or via iMessage reports.

---

## Tracking Opus Accuracy

After each human review, note whether Opus agreed:

| Date | Branch | Opus Verdict | Human Verdict | Match? |
|------|--------|-------------|---------------|--------|
| (start tracking here) | | | | |

When a category reaches 20+ matches with 0 misses, it's a candidate for Tier 2 graduation.
