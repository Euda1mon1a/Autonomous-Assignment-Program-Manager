# Claude Web Session Prompt - Tier 1 Independent Work

> **Created:** 2025-12-24
> **For:** Next Claude Web session (parallel to Claude Code IDE work)
> **Constraint:** Read-only or docs-only - no code modifications that conflict with Block 10 development

---

## How to Use

Copy the content below the `---` line into a new Claude Web session to start Tier 1 independent work.

---

## Session Context

You are assisting with documentation and analysis for a **Residency Scheduler** application. This session runs in parallel with Claude Code IDE work on Block 10 development.

**CRITICAL CONSTRAINT:** Do NOT modify any files in:
- `backend/app/scheduling/` (active development)
- `backend/app/resilience/` (active development)
- `backend/app/api/routes/schedule.py` (active development)
- Any test files related to scheduling

**Safe to create/modify:**
- `docs/**/*.md` (documentation)
- `.claude/skills/*.md` (AI skills)
- Planning documents
- Analysis reports

---

## Tasks (In Priority Order)

### Priority 1: API Documentation Review (HIGH)
**Output:** `docs/api/ENDPOINT_CATALOG.md`

Audit all API endpoints and create comprehensive endpoint catalog:
1. Read all files in `backend/app/api/routes/*.py`
2. For each endpoint, document: method, path, auth required, request/response schema
3. Identify any undocumented or inconsistent endpoints
4. Create table of contents organized by domain (auth, scheduling, resilience, etc.)

### Priority 2: Dependency Audit (HIGH)
**Output:** `docs/security/DEPENDENCY_AUDIT.md`

Review dependencies for security and currency:
1. Read `backend/requirements.txt` and `frontend/package.json`
2. Check for known issues with current versions
3. Identify outdated major versions
4. Note any dependencies approaching end-of-life
5. Recommend update priorities

### Priority 3: Test Coverage Analysis (MEDIUM)
**Output:** `docs/development/TEST_COVERAGE_ANALYSIS.md`

Analyze test coverage patterns:
1. List all test files in `backend/tests/`
2. Map tests to source files they cover
3. Identify untested modules or significant gaps
4. Prioritize missing tests by risk (auth, scheduling, data handling)

### Priority 4: Skill Enhancement (MEDIUM)
**Output:** Updates to `.claude/skills/*.md`

Review and enhance AI skills:
1. Read current skills in `.claude/skills/`
2. Identify skills that need more detail or examples
3. Add troubleshooting sections where missing
4. Ensure skills reference current file locations

### Priority 5: Onboarding Guide (LOW)
**Output:** `docs/guides/DEVELOPER_ONBOARDING.md`

Create developer onboarding checklist:
1. Prerequisites (Python, Node, Docker, etc.)
2. Environment setup steps
3. Database migration steps
4. Running tests locally
5. Common first-week tasks

---

## Session Guidelines

1. **Read before writing** - Always explore existing patterns first
2. **No code changes** - This session is documentation-only
3. **Verify file paths** - Use Glob/Grep to confirm locations
4. **Link to sources** - Include file:line references in docs
5. **Check existing docs** - Don't duplicate existing documentation

---

## Files to Reference

| Purpose | Location |
|---------|----------|
| Project guidelines | `CLAUDE.md` |
| Architecture | `docs/architecture/` |
| Existing API docs | `docs/api/` |
| Security policies | `docs/security/` |
| Current skills | `.claude/skills/` |
| Test directory | `backend/tests/` |

---

## Completion Checklist

- [ ] API endpoint catalog created
- [ ] Dependency audit completed
- [ ] Test coverage analysis done
- [ ] At least 2 skills enhanced
- [ ] Onboarding guide drafted
- [ ] All outputs reviewed for accuracy
- [ ] No conflicts with Block 10 work

---

## Notes for Session

- If you need to reference scheduling code, READ ONLY - do not modify
- Create all new docs in appropriate `docs/` subdirectory
- Use markdown tables for structured data
- Include "Last Updated" timestamp in all docs
- Reference `CLAUDE.md` for project conventions

---

*This prompt is designed for independent parallel work that won't interfere with active Block 10 development.*
