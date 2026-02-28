# Repository Audit (Master)

Date: 2026-02-27  
Scope: Full repository read-only diagnosis (no implementation changes), including `.gitignore`, CI/CD, backend/frontend quality posture, and LLM/agent governance folders.

## Executive Summary

Overall status is **at-risk** from a delivery/governance standpoint, not from immediate runtime breakage of core app paths.

Top blockers:
1. **Migration reliability and deploy safety gaps**: Alembic graph loading is coupled to runtime settings validation, and CD does not enforce actual migration execution before deploy.
2. **Quality signal dilution**: frontend lint baseline is 17,505 warnings, backend mypy baseline is 4,160 errors, and many CI checks are informational/non-blocking.
3. **Type-contract gate bug**: CI checks `src/types/generated-api.ts`, but the generator writes `src/types/api-generated.ts`.
4. **Governance drift**: agent governance is configured OFF while docs imply operational guardrails.
5. **Repo hygiene drift**: 189 files are currently tracked while also matching `.gitignore` rules.

## Methods and Evidence

Primary diagnostics executed:
- `python3 scripts/ops/stack_audit.py --quick` (report: `.claude/dontreadme/stack-health/2026-02-26_222846.md`)
- `mypy app --ignore-missing-imports --no-error-summary` in `backend/`
- `npm run lint`, `npm run type-check`, `npm run type-check:all`, `npm audit --json` in `frontend/`
- `.gitignore` contradiction scan: `git ls-files --cached --ignored --exclude-standard`
- Manual read-through of key workflows/configs and three parallel explorer audits (backend/infra, frontend, LLM/governance)

Key measured outputs:
- Stack audit status: **YELLOW** ([stack report](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/dontreadme/stack-health/2026-02-26_222846.md#L4))
- Frontend lint warnings: **17,505** ([stack report](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/dontreadme/stack-health/2026-02-26_222846.md#L11))
- Backend mypy errors: **4,160** ([stack report](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/dontreadme/stack-health/2026-02-26_222846.md#L14))
- Migration checks: **ERROR** ([stack report](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/dontreadme/stack-health/2026-02-26_222846.md#L15))
- Backups: **none found** ([stack report](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/dontreadme/stack-health/2026-02-26_222846.md#L289))
- Frontend `npm audit`: **3 vulnerabilities** (1 high, 2 moderate)

## Findings (By Severity)

### Critical

1. Alembic migration loading is coupled to full app config validation, causing migration commands to fail under common CI/local env states.
- Evidence:
  - [`backend/alembic/versions/20260219_add_gt_tables.py:13`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/alembic/versions/20260219_add_gt_tables.py:13)
  - [`backend/alembic/env.py:8`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/alembic/env.py:8)
  - [`backend/app/core/config.py:343`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/core/config.py:343)
  - Stack failure trace in [report](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/dontreadme/stack-health/2026-02-26_222846.md#L112)
- Risk: migration commands can fail before evaluating schema state, reducing deploy confidence.

2. CD workflow does not enforce real migration execution before deployment.
- Evidence:
  - [`cd.yml:124`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/cd.yml:124)
  - [`cd.yml:195`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/cd.yml:195)
  - Migration job comments/no-op at [`cd.yml:291`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/cd.yml:291), [`cd.yml:303`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/cd.yml:303)
- Risk: code deploy can outrun schema readiness.

3. API type-sync CI gate checks a non-existent/incorrect target path.
- Evidence:
  - CI diff target [`ci.yml:357`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/ci.yml:357)
  - Generator output file [`frontend/scripts/generate-api-types.sh:40`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/scripts/generate-api-types.sh:40)
- Risk: false pass/fail on API contract drift.

### High

1. Backend + celery services all run `alembic upgrade head` at startup.
- Evidence:
  - [`backend/docker-entrypoint.sh:21`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/docker-entrypoint.sh:21)
  - Service definitions using same image path: [`docker-compose.yml:53`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docker-compose.yml:53), [`docker-compose.yml:105`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docker-compose.yml:105), [`docker-compose.yml:143`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docker-compose.yml:143)
- Risk: migration race/lock timing issues and boot fragility.

2. Frontend lint signal is currently non-actionable due warning volume.
- Evidence:
  - 17,505 warnings confirmed by local run and stack report ([report line 11](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/dontreadme/stack-health/2026-02-26_222846.md#L11))
  - Related config and generated-file exposure: [`frontend/eslint.config.js:16`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/eslint.config.js:16), [`frontend/src/types/api-generated.ts`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/src/types/api-generated.ts)
- Risk: real regressions are buried in noise.

3. Backend and MCP typing debt is large and mostly non-blocking.
- Evidence:
  - Backend mypy: 4,160 errors (`mypy app`)
  - MCP mypy: 163 errors (`mypy src` in `mcp-server/`)
  - Non-blocking CI posture in [`quality-gates.yml:191`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/quality-gates.yml:191), [`ci-lite.yml:117`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/ci-lite.yml:117)
- Risk: type system not preventing regressions in many paths.

4. Quality Gates defines frontend E2E but does not include it in final enforcement `needs`.
- Evidence:
  - E2E job exists at [`quality-gates.yml:424`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/quality-gates.yml:424)
  - Final gate needs at [`quality-gates.yml:739`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/quality-gates.yml:739)
- Risk: green gate can ship without E2E participation.

5. CI E2E path mismatch: uses `test:e2e` rather than CI-tuned command/config.
- Evidence:
  - [`frontend/package.json:17`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/package.json:17)
  - [`frontend/package.json:19`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/package.json:19)
  - [`ci.yml:227`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/ci.yml:227)
- Risk: unstable/incorrect E2E assumptions in CI.

6. Rate-limit client identification trusts raw `X-Forwarded-For` in active middleware path.
- Evidence:
  - [`backend/app/core/slowapi_limiter.py:42`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/core/slowapi_limiter.py:42)
  - Active middleware setup [`backend/app/main.py:342`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/main.py:342)
  - Trusted-proxy-aware alternative exists in [`backend/app/core/rate_limit.py:243`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/core/rate_limit.py:243)
- Risk: spoofable identifiers can weaken abuse controls.

7. MCP server local config allows broad unauthenticated access when exposed beyond localhost.
- Evidence:
  - Local compose sets dev bypass and 0.0.0.0 binding at [`docker-compose.local.yml:322`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docker-compose.local.yml:322), [`docker-compose.local.yml:327`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docker-compose.local.yml:327)
  - Middleware bypass behavior in [`mcp-server/src/scheduler_mcp/server.py:5718`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/mcp-server/src/scheduler_mcp/server.py:5718), [`mcp-server/src/scheduler_mcp/server.py:5756`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/mcp-server/src/scheduler_mcp/server.py:5756)
- Risk: unintended network exposure of tool endpoints.

### Medium

1. Frontend type-check policy is inconsistent.
- Observed:
  - `npm run type-check` exits 0
  - `npm run type-check:all` exits 2 with 99 TS errors
- Evidence:
  - Scripts in [`frontend/package.json:11`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/package.json:11), [`frontend/package.json:12`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/package.json:12)
- Risk: local and CI expectations diverge.

2. Test discovery fragmentation in frontend.
- Evidence:
  - Jest scoped to `__tests__` patterns only at [`frontend/jest.config.js:24`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/jest.config.js:24)
  - Playwright root config `testDir` differs from nested config ([`frontend/playwright.config.ts:12`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/playwright.config.ts:12), [`frontend/e2e/playwright.config.ts:11`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/e2e/playwright.config.ts:11))
- Risk: tests can exist but not run.

3. Readiness checks are weaker than they appear.
- Evidence:
  - Docker health check targets `/health` at [`docker-compose.yml:96`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docker-compose.yml:96)
  - Stack audit API checks skip auth-required validations ([report lines 281-282](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/dontreadme/stack-health/2026-02-26_222846.md#L281))
- Risk: “healthy” status may miss important dependency failures.

4. Runtime/version drift across docs and environments.
- Evidence:
  - README frontend stack says Next 14 ([`README.md:219`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/README.md:219)); package has Next 15 ([`frontend/package.json:43`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/package.json:43))
  - CI node 20 ([`ci.yml:22`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/ci.yml:22)); Volta node 22 ([`frontend/package.json:89`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/frontend/package.json:89))
  - Backend Docker Python 3.12 ([`backend/Dockerfile:19`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/Dockerfile:19)); CI Python 3.11 ([`ci.yml:21`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/ci.yml:21))
- Risk: environment-specific failures and debugging friction.

5. Missing local tooling reduces repeatability of security audit workflow.
- Observed:
  - `gitleaks` not installed locally
  - `pip-audit` not installed locally
- Risk: security checks depend on CI only and may not run pre-merge locally.

### Low

1. CI Lite permits zero-test pass-through.
- Evidence: [`ci-lite.yml:217`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.github/workflows/ci-lite.yml:217)

2. `.dockerignore` excludes development-critical files (`docs/`, `.github/`, `Makefile`), which may be intentional but is broad.
- Evidence: [`.dockerignore:9`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.dockerignore:9), [`.dockerignore:106`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.dockerignore:106), [`.dockerignore:114`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.dockerignore:114)

## Priority Advice (No Implementation Performed)

1. **Stabilize migration/deploy safety first**: decouple migration loading from full runtime config; enforce real migration step in CD.
2. **Fix API type-sync gate path bug immediately**: this is a high-leverage correctness check.
3. **Convert warning-noise into useful signal**: exclude generated files from lint/type enforcement and introduce ratcheting thresholds.
4. **Harden enforcement semantics**: include frontend E2E in final Quality Gates needs or explicitly remove it.
5. **Align environments**: standardize Node/Python versions and update README stack matrix.
6. **Close governance drift**: either enable governance path or formally deprecate dead controls.

## Related Detailed Reports

- [.gitignore audit](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docs/reviews/2026-02-27_gitignore-audit.md)
- [LLM/agents governance audit](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docs/reviews/2026-02-27_llm-agents-governance-audit.md)
