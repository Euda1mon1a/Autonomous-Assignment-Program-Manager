# Skill Validation Test Suite

> **Last Updated:** 2025-12-31
> **Purpose:** Comprehensive testing framework for validating all 40+ AI agent skills

---

## Table of Contents

1. [Test Framework Overview](#test-framework-overview)
2. [Skill Validation Checklist](#skill-validation-checklist)
3. [Core Skills Testing (12 skills)](#core-skills-testing)
4. [Enhanced Skills Testing (6 skills)](#enhanced-skills-testing)
5. [New Skills Testing (10 skills)](#new-skills-testing)
6. [Integration Testing](#integration-testing)
7. [Performance Benchmarks](#performance-benchmarks)
8. [Validation Report Template](#validation-report-template)

---

## Test Framework Overview

### Validation Criteria

Every skill must satisfy:

1. **Structural Requirements**
   - [ ] YAML frontmatter present and valid
   - [ ] All required fields present
   - [ ] Parallel hints configured
   - [ ] Escalation triggers defined

2. **Content Requirements**
   - [ ] Clear activation rules
   - [ ] Methodology documented
   - [ ] 2+ integration points
   - [ ] Validation checklist included
   - [ ] Quick reference commands
   - [ ] Common patterns shown
   - [ ] Error handling documented

3. **Functional Requirements**
   - [ ] Skill activates in correct scenarios
   - [ ] Output format matches specification
   - [ ] Integration with dependencies works
   - [ ] Escalation triggered appropriately

4. **Quality Requirements**
   - [ ] No spelling/grammar errors
   - [ ] Consistent formatting
   - [ ] Examples accurate and tested
   - [ ] Commands actually work
   - [ ] File paths absolute (not relative)

---

## Skill Validation Checklist

### For Each Skill, Verify:

```yaml
Skill: [name]
Location: /home/user/Autonomous-Assignment-Program-Manager/.claude/skills/[name]/SKILL.md

YAML Frontmatter:
  - [ ] name field: [value]
  - [ ] description field: [value]
  - [ ] model_tier field: [value]
  - [ ] parallel_hints present: [yes/no]
  - [ ] escalation_triggers present: [yes/no]
  - [ ] context_hints present: [yes/no]

Content Sections:
  - [ ] "When This Skill Activates" section
  - [ ] Methodology with 2+ phases
  - [ ] Integration with other skills (2+)
  - [ ] Quick reference commands (3+)
  - [ ] Common patterns (2+ good, 2+ bad)
  - [ ] Validation checklist (5+ items)
  - [ ] Error handling documented
  - [ ] References section

Code Examples:
  - [ ] Python examples syntactically correct
  - [ ] TypeScript examples syntactically correct
  - [ ] Commands use absolute paths
  - [ ] Examples are realistic and testable

Consistency Checks:
  - [ ] Links to related skills correct
  - [ ] References to files accurate
  - [ ] Terminology consistent throughout
  - [ ] No conflicting instructions
```

---

## Core Skills Testing (12 skills)

### Test Suite 1: Code Quality Skills (5 skills)

#### 1.1 code-review

**Structural Test:**
```bash
# Verify YAML
grep "^name: code-review" /home/user/Autonomous-Assignment-Program-Manager/.claude/skills/code-review/SKILL.md
# Should return: name: code-review

# Verify parallel hints
grep "can_parallel_with" /home/user/Autonomous-Assignment-Program-Manager/.claude/skills/code-review/SKILL.md
# Should include: test-writer, lint-monorepo
```

**Content Test:**
- [ ] Reviews Python code correctly
- [ ] Identifies security issues
- [ ] Provides specific fixes
- [ ] Escalates auth/crypto changes
- [ ] Output matches report template

**Integration Test:**
```
Workflow: code-review → test-writer
1. code-review finds missing tests
2. test-writer generates tests
3. code-review validates tests
Result: Tests added and reviewed
```

#### 1.2 test-writer

**Functional Test:**
```
Input: Function needing tests
Output: Test file with:
  - Test class structure
  - Fixtures
  - Happy path tests
  - Error case tests
  - Edge case tests
Verify: Tests execute and pass
```

**Coverage Test:**
- [ ] Unit test templates provided
- [ ] Integration test patterns shown
- [ ] Fixture generation explained
- [ ] Coverage targets specified
- [ ] Pytest patterns aligned with project

#### 1.3 lint-monorepo

**Structural Test:**
- [ ] Python linting rules specified
- [ ] TypeScript linting rules specified
- [ ] Auto-fix procedures documented
- [ ] Commands provided for both languages

**Functional Test:**
```bash
# Test Python linting
cd /home/user/Autonomous-Assignment-Program-Manager/backend
ruff check app/ --show-source | head

# Test TypeScript linting
cd /home/user/Autonomous-Assignment-Program-Manager/frontend
npm run lint 2>&1 | head
```

#### 1.4 security-audit

**Content Verification:**
- [ ] OWASP Top 10 coverage mentioned
- [ ] Authentication checks documented
- [ ] HIPAA/PERSEC considerations noted
- [ ] Secret detection methods provided
- [ ] Escalation for crypto code

#### 1.5 code-quality-monitor

**Integration Verification:**
- [ ] Works with linting skills
- [ ] Works with security-audit
- [ ] Works with test-writer
- [ ] Quality gates defined
- [ ] Thresholds documented

### Test Suite 2: Database Skills (2 skills)

#### 1.6 database-migration

**Validation Test:**
- [ ] Migration workflow clearly described
- [ ] Upgrade procedure documented
- [ ] Downgrade procedure documented
- [ ] Testing steps provided
- [ ] Rollback strategy explained
- [ ] Integration with Alembic clear

**Content Verification:**
```
Sections present:
  - [ ] Schema change migration process
  - [ ] Data migration process
  - [ ] Safe migration deployment
  - [ ] Verification procedures
  - [ ] Rollback procedures
```

#### 1.7 constraint-preflight

**Integration Test:**
- [ ] Works with code-review
- [ ] Validates constraints before commit
- [ ] Checks constraint registration
- [ ] Verifies testing coverage
- [ ] Reports registration status

### Test Suite 3: Review and PR Skills (2 skills)

#### 1.8 pr-reviewer

**Functional Test:**
- [ ] PR context analysis works
- [ ] Changes summary generated
- [ ] Quality gates checked
- [ ] Recommendations provided
- [ ] Integration points identified

#### 1.9 check-codex

**Content Verification:**
- [ ] Codex feedback format understood
- [ ] Integration with code-review
- [ ] GitHub API usage documented
- [ ] Approval workflow clear

### Test Suite 4: Architecture and Design (3 skills)

#### 1.10 fastapi-production

**Content Verification:**
- [ ] FastAPI patterns documented
- [ ] Async/await best practices shown
- [ ] SQLAlchemy 2.0 patterns included
- [ ] Pydantic v2 usage shown
- [ ] Error handling middleware explained

#### 1.11 context-aware-delegation

**Integration Test:**
- [ ] Agent context isolation explained
- [ ] Prompt templates provided
- [ ] Information preservation documented
- [ ] Self-contained context achieved

#### 1.12 agent-factory

**Content Verification:**
- [ ] AGENT_FACTORY.md patterns referenced
- [ ] Archetype selection process clear
- [ ] Validation against CONSTITUTION.md mentioned
- [ ] Agent specification template provided

---

## Enhanced Skills Testing (6 skills)

### Test Suite 5: Enhanced Core Skills

#### 2.1 acgme-compliance (ENHANCED)

**Structural Test:**
```bash
# Verify enhancements
grep "model_tier: opus" /home/user/Autonomous-Assignment-Program-Manager/.claude/skills/acgme-compliance/SKILL.md
grep "parallel_hints:" /home/user/Autonomous-Assignment-Program-Manager/.claude/skills/acgme-compliance/SKILL.md
grep "escalation_triggers:" /home/user/Autonomous-Assignment-Program-Manager/.claude/skills/acgme-compliance/SKILL.md
# All should return matches
```

**Content Verification:**
- [ ] Phase 1: Data Gathering documented
- [ ] Phase 2: Rule-by-Rule Analysis detailed
- [ ] Phase 3: Issue Prioritization explained
- [ ] Phase 4: Solution Development steps clear
- [ ] Integration points with 3+ skills
- [ ] Context management guidance provided
- [ ] Validation checklist with 10+ items
- [ ] Quick reference commands (4+)
- [ ] Common patterns (good and bad)
- [ ] Error recovery procedures

**Functional Test:**
```
Scenario: Resident with potential 80-hour violation
1. Run validation
2. Identify specific violation
3. Propose solution
4. Verify solution doesn't create new issues
Result: Clear recommendation on fix
```

#### 2.2 code-review (ENHANCED)

**Verification:**
- [ ] Security focus emphasized
- [ ] OWASP patterns documented
- [ ] Integration with 3+ skills
- [ ] Escalation triggers for sensitive code
- [ ] Context hints configured

#### 2.3 test-writer (ENHANCED)

**Verification:**
- [ ] Coverage targets specified by layer
- [ ] Pytest patterns enhanced
- [ ] Jest patterns included
- [ ] Integration with code-review
- [ ] Validation checklist included

#### 2.4 database-migration (ENHANCED)

**Verification:**
- [ ] Rollback procedures detailed
- [ ] Testing strategy comprehensive
- [ ] Schema change patterns
- [ ] Data migration patterns
- [ ] Safe deployment guide

#### 2.5 pr-reviewer (ENHANCED)

**Verification:**
- [ ] Checklist integration complete
- [ ] Quality gates documented
- [ ] Approval workflow clear
- [ ] Integration with code-review
- [ ] Validation procedures

#### 2.6 security-audit (ENHANCED)

**Verification:**
- [ ] OWASP Top 10 explicit
- [ ] HIPAA considerations included
- [ ] Military data handling (OPSEC/PERSEC)
- [ ] Escalation for crypto code
- [ ] Integration with code-review

---

## New Skills Testing (10 skills)

### Test Suite 6: New Specialized Skills

#### 3.1 schedule-validator

**Verification:**
- [ ] 4 validation phases documented
- [ ] ACGME compliance integration
- [ ] Coverage analysis included
- [ ] Validation report template
- [ ] Integration with acgme-compliance
- [ ] Quick commands provided

**Functional Test:**
```
Input: Generated schedule
Outputs:
  - Data integrity check
  - ACGME compliance status
  - Coverage analysis
  - Operational feasibility
Result: Pass/fail determination
```

#### 3.2 resilience-monitor

**Verification:**
- [ ] Health check methodology
- [ ] N-1/N-2 analysis documented
- [ ] Metrics collection explained
- [ ] Alerting integration
- [ ] Dashboard information

#### 3.3 swap-analyzer

**Verification:**
- [ ] Swap type classification clear
- [ ] Feasibility analysis detailed
- [ ] ACGME impact assessment
- [ ] Coverage impact analysis
- [ ] Common swap scenarios covered
- [ ] Integration with acgme-compliance
- [ ] Integration with swap-execution

**Functional Test:**
```
Input: Proposed swap (Resident A ↔ Resident B)
Analysis:
  - Rotation compatibility
  - ACGME compliance impact
  - Coverage implications
  - Risk assessment
Output: APPROVED / CONDITIONAL / BLOCKED
```

#### 3.4 coverage-reporter

**Verification:**
- [ ] Python coverage analysis
- [ ] TypeScript coverage analysis
- [ ] Gap identification
- [ ] Trend analysis
- [ ] Integration with test-writer
- [ ] Quick commands

#### 3.5 deployment-validator

**Verification:**
- [ ] Pre-deployment checklist
- [ ] Code quality gates
- [ ] Database readiness checks
- [ ] Risk assessment matrix
- [ ] Deployment scenarios covered
- [ ] Escalation decision tree
- [ ] Commands provided

#### 3.6 api-documenter

**Verification:**
- [ ] OpenAPI generation explained
- [ ] Endpoint documentation format
- [ ] Schema documentation
- [ ] Example request/response
- [ ] Integration with code-review

#### 3.7 performance-profiler

**Verification:**
- [ ] Python profiling methods
- [ ] Query optimization analysis
- [ ] Load testing integration
- [ ] Bottleneck identification
- [ ] Optimization recommendations

#### 3.8 dependency-auditor

**Verification:**
- [ ] Python dependency scanning (pip-audit)
- [ ] Node.js dependency scanning (npm audit)
- [ ] CVE identification
- [ ] Update recommendations
- [ ] Integration with security-audit

#### 3.9 migration-planner

**Verification:**
- [ ] Migration planning methodology
- [ ] Dependency analysis
- [ ] Risk assessment
- [ ] Testing strategy
- [ ] Integration with database-migration

#### 3.10 incident-responder

**Verification:**
- [ ] Incident classification
- [ ] Triage procedures
- [ ] Root cause analysis
- [ ] Remediation steps
- [ ] Postmortem template
- [ ] Escalation procedures

---

## Integration Testing

### Test Suite 7: Cross-Skill Integration

#### Integration Test 1: Code Review Workflow

```
Workflow: code-review → test-writer → lint-monorepo → pr-reviewer

Test Steps:
1. code-review finds issues
   Expected: CRITICAL/WARNING/INFO findings

2. test-writer adds tests
   Expected: Tests generated for coverage gaps

3. lint-monorepo formats code
   Expected: Code passes all linting

4. pr-reviewer validates
   Expected: Ready for approval

Result: Successful workflow completion
```

**Validation:** All steps execute without errors

#### Integration Test 2: Schedule Deployment Workflow

```
Workflow: safe-schedule-generation → schedule-validator → acgme-compliance → deployment-validator

Test Steps:
1. safe-schedule-generation creates schedule
   Expected: Schedule file generated

2. schedule-validator checks structure
   Expected: Data integrity confirmed

3. acgme-compliance verifies rules
   Expected: Compliance status reported

4. deployment-validator pre-flight checks
   Expected: Deployment readiness confirmed

Result: Schedule ready for deployment
```

**Validation:** All compliance checks pass

#### Integration Test 3: Bug Fix Workflow

```
Workflow: systematic-debugger → test-writer → code-review → deployment-validator

Test Steps:
1. systematic-debugger identifies root cause
   Expected: Root cause documented

2. test-writer creates regression test
   Expected: Test reproduces bug, fails initially

3. code-review validates fix
   Expected: Fix is correct and complete

4. deployment-validator confirms safety
   Expected: Ready for production

Result: Bug fix validated and approved
```

**Validation:** Complete workflow executes successfully

---

## Performance Benchmarks

### Skill Performance Expectations

| Skill | Typical Runtime | Max Acceptable | Notes |
|-------|---|---|---|
| code-review | 2-5 min | 10 min | Depends on code size |
| test-writer | 3-10 min | 15 min | Depends on complexity |
| lint-monorepo | 1-2 min | 5 min | Fast, parallel safe |
| acgme-compliance | 1-3 min | 5 min | Database dependent |
| schedule-validator | 2-5 min | 10 min | Depends on schedule size |
| security-audit | 3-5 min | 10 min | Depends on code size |
| database-migration | Varies | 30 min | Data volume dependent |
| deployment-validator | 2-5 min | 10 min | Checks only, no execution |

### Parallel Execution Benchmarks

```
Baseline (Sequential): 45 minutes
Parallel (Optimal):    15 minutes (3x speedup)

Configuration:
- Batch A: code-review, test-writer (parallel)
- Batch B: lint-monorepo, security-audit (parallel)
- Sequential: database-migration, deployment-validator
```

---

## Validation Report Template

Use this template to document skill validation results:

```markdown
# Skill Validation Report

**Date:** [DATE]
**Validator:** [NAME]
**Status:** [COMPLETE / INCOMPLETE / FAILED]

## Skills Validated

### Core Skills (12)
- [ ] code-review: [PASS / FAIL / PARTIAL]
- [ ] test-writer: [PASS / FAIL / PARTIAL]
- [ ] lint-monorepo: [PASS / FAIL / PARTIAL]
- [ ] security-audit: [PASS / FAIL / PARTIAL]
- [ ] code-quality-monitor: [PASS / FAIL / PARTIAL]
- [ ] database-migration: [PASS / FAIL / PARTIAL]
- [ ] constraint-preflight: [PASS / FAIL / PARTIAL]
- [ ] pr-reviewer: [PASS / FAIL / PARTIAL]
- [ ] check-codex: [PASS / FAIL / PARTIAL]
- [ ] fastapi-production: [PASS / FAIL / PARTIAL]
- [ ] context-aware-delegation: [PASS / FAIL / PARTIAL]
- [ ] agent-factory: [PASS / FAIL / PARTIAL]

### Enhanced Skills (6)
- [ ] acgme-compliance (enhanced): [PASS / FAIL / PARTIAL]
- [ ] code-review (enhanced): [PASS / FAIL / PARTIAL]
- [ ] test-writer (enhanced): [PASS / FAIL / PARTIAL]
- [ ] database-migration (enhanced): [PASS / FAIL / PARTIAL]
- [ ] pr-reviewer (enhanced): [PASS / FAIL / PARTIAL]
- [ ] security-audit (enhanced): [PASS / FAIL / PARTIAL]

### New Skills (10)
- [ ] schedule-validator: [PASS / FAIL / PARTIAL]
- [ ] resilience-monitor: [PASS / FAIL / PARTIAL]
- [ ] swap-analyzer: [PASS / FAIL / PARTIAL]
- [ ] coverage-reporter: [PASS / FAIL / PARTIAL]
- [ ] deployment-validator: [PASS / FAIL / PARTIAL]
- [ ] api-documenter: [PASS / FAIL / PARTIAL]
- [ ] performance-profiler: [PASS / FAIL / PARTIAL]
- [ ] dependency-auditor: [PASS / FAIL / PARTIAL]
- [ ] migration-planner: [PASS / FAIL / PARTIAL]
- [ ] incident-responder: [PASS / FAIL / PARTIAL]

## Integration Tests
- [ ] Code review workflow: [PASS / FAIL]
- [ ] Schedule deployment workflow: [PASS / FAIL]
- [ ] Bug fix workflow: [PASS / FAIL]
- [ ] Custom workflow tests: [DESCRIBE]

## Issues Found

### Critical Issues
1. [Issue 1 - requires fix]
2. [Issue 2 - requires fix]

### Warnings
1. [Issue 1 - should fix]
2. [Issue 2 - should fix]

### Recommendations
1. [Suggestion 1]
2. [Suggestion 2]

## Summary

**Total Skills Tested:** 28
**Passed:** [N]
**Partial:** [N]
**Failed:** [N]
**Success Rate:** [X]%

**Recommendation:** [APPROVED / NEEDS WORK / BLOCKED]

## Sign-Off

Validated by: [Name]
Date: [Date]
Approved by: [Name, if applicable]

```

---

## Running the Full Test Suite

### Automated Test Execution

```bash
# From project root
cd /home/user/Autonomous-Assignment-Program-Manager

# 1. Validate all skill files exist
find .claude/skills -name "SKILL.md" | wc -l
# Should show: 28+ skills

# 2. Validate YAML frontmatter
for file in .claude/skills/*/SKILL.md; do
  echo "Checking: $file"
  grep -q "^name:" "$file" && echo "  ✓ name field" || echo "  ✗ MISSING name"
  grep -q "^description:" "$file" && echo "  ✓ description" || echo "  ✗ MISSING description"
done

# 3. Run integration tests
# (Skill-specific tests would be defined in pytest)
pytest .claude/tests/test_skills/ -v

# 4. Generate validation report
python -m .claude.tools.validate_skills --output=VALIDATION_REPORT.md
```

---

## Success Criteria

All skills are validated and operational when:

1. ✓ All 28 skills have valid YAML frontmatter
2. ✓ All required sections present in each skill
3. ✓ All integration tests pass
4. ✓ No broken cross-skill references
5. ✓ Command examples work correctly
6. ✓ Performance within acceptable ranges
7. ✓ No duplicate skill names or functionality
8. ✓ Escalation triggers appropriately tested
9. ✓ Parallel hints accurately configured
10. ✓ Documentation complete and accurate

---

## Maintenance

### Regular Validation

- Weekly: Spot-check 5 random skills
- Monthly: Full validation suite
- After any skill modification: Re-validate that skill
- After framework changes: Re-validate all affected skills

### Updating Tests

When skills are modified:
1. Update this test suite
2. Re-run affected tests
3. Update validation report
4. Document changes

---

## References

- SKILL_ENHANCEMENT_GUIDE.md
- PROMPT_LIBRARY.md
- CONTEXT_PATTERNS.md
- Individual skill SKILL.md files

