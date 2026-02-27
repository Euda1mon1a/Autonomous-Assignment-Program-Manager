# `.gitignore` Audit

Date: 2026-02-27  
Scope: Rule quality, contradictions, tracked-vs-ignored drift, and high-risk artifact exposure.

## Executive Snapshot

- Tracked files matching ignore rules: **189**
- Untracked ignored files: **103,978**
- Most contradiction-heavy rules:
  - `.gitignore:219` (`.claude/dontreadme/sessions/*.md`) -> 75 tracked files
  - `.gitignore:222` (`.claude/skills/*/`) -> 42 tracked files
  - `.gitignore:218` (`.claude/Scratchpad/SESSION_*.md`) -> 26 tracked files
  - `.gitignore:301` (`.codex/`) -> 8 tracked files

## High-Severity Findings

1. Parent-directory ignore rules conflict with committed policy files.
- Evidence:
  - Ignore parent at [`.gitignore:301`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:301)
  - Unignore children at [`.gitignore:302`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:302)-[`.gitignore:309`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:309)
  - `git check-ignore -v --no-index .codex/AGENTS.md` still reports ignored by rule 301
- Risk: guardrail files appear versioned but ignore semantics are inconsistent and brittle.

2. `LLM/agent` and schedule artifacts are both "ignored" and committed.
- Evidence:
  - `.agent/` ignore rule [`.gitignore:233`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:233)
  - `.claude` session/skills rules [`.gitignore:217`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:217)-[`.gitignore:222`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:222)
  - Scheduling XLSX/XML ignored by [`.gitignore:237`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:237)-[`.gitignore:238`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:238), but tracked files exist under `docs/scheduling/`
- Risk: policy credibility erosion and accidental OPSEC/PII artifact retention.

3. CI-sensitive generated/test artifacts are tracked despite ignore intent.
- Evidence:
  - `frontend/src/types/api-generated-check.ts` ignored by [`.gitignore:257`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:257) but tracked
  - `frontend/playwright-report/index.html` and `frontend/test-results/*` tracked (no explicit ignore for those paths in `.gitignore`)
- Risk: noisy diffs and accidental artifact persistence.

## Medium Findings

1. `.dockerignore` is very broad and may hide useful context in image builds.
- Evidence:
  - `docs/` ignored [`.dockerignore:9`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.dockerignore:9)
  - `.github/` ignored [`.dockerignore:106`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.dockerignore:106)
  - `Makefile` ignored [`.dockerignore:114`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.dockerignore:114)
- Note: may be intentional for minimal images, but it diverges from common debug/repro expectations.

2. Ignore file is carrying dual-purpose policy (privacy + workflow state + WIP feature toggles), making it hard to reason about.
- Examples:
  - WIP route/test ignores [`.gitignore:317`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:317), [`.gitignore:320`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:320)
  - data/script exclusions [`.gitignore:189`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:189)
- Risk: unclear which ignores are permanent policy vs temporary workflow deferrals.

## Low Findings

1. Minor duplication/redundancy in ignore semantics (e.g., repeated environment patterns and broad category overlaps) increases maintenance cost.

## Recommendations (Advice Only)

1. Add a CI check that fails when tracked files match `.gitignore`.
2. Normalize parent-directory unignore patterns (`!.codex/` before child exceptions).
3. Split `.gitignore` sections into explicit classes:
- `security/privacy`
- `build artifacts`
- `local AI workspace`
- `temporary WIP toggles`
4. Remove tracked generated/test run artifacts from source control and enforce path ignores.
5. Add comments with expiration/owner for temporary ignore entries (e.g., WIP routes/tests).

## Commands Used

- `git ls-files --cached --ignored --exclude-standard`
- `git ls-files --others --ignored --exclude-standard`
- `git check-ignore -v --no-index <path>`
- rule aggregation via `git check-ignore` + `sort | uniq -c`
