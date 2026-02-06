# Constitutions Directory

> **Purpose:** Domain-specific guardrails for AI agents
> **Created:** 2025-12-26
> **Structure:** Three-tier constitution system

---

## Overview

This directory contains domain-specific constitutions that complement the main `.claude/CONSTITUTION.md`. Each constitution focuses on a specific aspect of system governance and provides detailed, actionable rules for AI agents.

---

## Constitution Hierarchy

**Precedence order (when conflicts arise):**

1. **SAFETY_CRITICAL.md** (Highest Priority)
   - Non-negotiable safety principles
   - Forbidden operations
   - Patient safety and regulatory compliance
   - Data protection (HIPAA, OPSEC, PERSEC)
   - Emergency procedures

2. **SCHEDULING.md** (Domain-Specific)
   - ACGME compliance rules
   - Schedule validation requirements
   - Constraint hierarchy (Tier 1-4)
   - Resilience thresholds
   - Coverage and fairness requirements

3. **CORE.md** (Universal)
   - CLI-first principles
   - Logging and auditability
   - Security defense-in-depth
   - Error handling and rollback
   - Code quality standards
   - Agent communication

---

## When to Use Which Constitution

### SAFETY_CRITICAL.md

**Use when:**
- Validating operations for safety compliance
- Evaluating forbidden operations (DROP TABLE, force push, etc.)
- Responding to requests that might violate ACGME rules
- Handling emergency override requests
- Protecting PHI, PII, or OPSEC/PERSEC data
- Escalating safety-critical issues

**Key Sections:**
- II. Absolute Prohibitions
- III. Patient Safety Implications
- IV. Military OPSEC/PERSEC Requirements
- V. Forbidden Operations
- VI. Emergency Override Procedures

### SCHEDULING.md

**Use when:**
- Generating or modifying schedules
- Validating ACGME compliance
- Evaluating schedule swaps
- Checking resilience thresholds (N-1, N-2 contingency)
- Assessing coverage requirements
- Calculating fairness metrics
- Managing constraint hierarchies

**Key Sections:**
- II. ACGME Compliance (Tier 0)
- III. Constraint Hierarchy
- IV. Resilience Framework
- V. Schedule Validation Requirements
- VII. Swap Validation

### CORE.md

**Use when:**
- Writing new code or tools
- Implementing CLI interfaces
- Setting up logging and auditing
- Designing security controls
- Handling errors and rollbacks
- Communicating with humans or other agents
- Reviewing code quality

**Key Sections:**
- II. CLI-First, Deterministic Code
- III. Logging & Auditability
- IV. Security Defense-in-Depth
- V. Error Handling & Rollback
- VIII. Code Quality Standards

---

## Examples

### Example 1: User Requests Bypassing ACGME Validation

**Constitution:** SAFETY_CRITICAL.md → Section II.A (Regulatory Violations)

**Response:**
```
I cannot bypass ACGME validation because it violates the Safety-Critical
Constitution Section II.A (Regulatory Violations).

ACGME compliance is a legal requirement enforced by federal regulations.
Violations can result in program accreditation loss, legal liability,
and harm to resident welfare and patient safety.

Alternative: If you need to test edge cases, use the test environment
with synthetic data that allows controlled compliance violations for
testing purposes only.
```

### Example 2: User Asks to Log Resident Names

**Constitution:** SAFETY_CRITICAL.md → Section IV.B (PERSEC Requirements)

**Response:**
```
I cannot log resident names because it violates the Safety-Critical
Constitution Section IV.B (Data Protection - PERSEC).

This system handles military medical residency schedules. Logging resident
names creates Personal Security (PERSEC) risk and could enable targeting
of military personnel.

Alternative: Use anonymized identifiers:
- person_id: UUID
- role: "PGY-1"
- anonymized_name: "Resident_001"
```

### Example 3: User Wants to Generate Schedule Without Backup

**Constitution:** SCHEDULING.md → Section VI.A (Backup Before Generation)

**Response:**
```
I cannot generate a schedule without first creating a backup because it
violates the Scheduling Constitution Section VI.A (Backup Requirements).

This ensures rollback capability if generation fails or produces a
non-compliant schedule. Without backup, we risk data loss or inability
to recover from errors.

I will automatically create a backup before generation. This takes only
a few seconds and provides critical protection.
```

### Example 4: User Wants to Use Interactive Input

**Constitution:** CORE.md → Section II.A (CLI-First Requirements)

**Response:**
```
I cannot use interactive input prompts because it violates the Core
Constitution Section II.A (CLI-First, Deterministic Code).

Interactive prompts break automation, testing, and CI/CD integration.

Alternative: Use environment variables or command-line flags:
- Environment variable: RESIDENT_NAME=value
- Command flag: --resident-name value
- Config file: config.json with resident_name field
```

---

## Constitution Maintenance

### When to Update

**Review constitutions when:**
- Same problem occurs 3+ times despite rules
- Safety rules block legitimate operations (false positives)
- Safety rules miss actual risks (false negatives)
- New regulations or compliance requirements
- Technology changes (framework updates, new tools)
- Security incidents reveal gaps

### Amendment Process

1. **Identify gap** and document the problem
2. **Draft amendment** with specific rule changes
3. **Impact analysis** on existing code and patterns
4. **7-day review period** for stakeholder feedback
5. **Explicit approval** from system architect
6. **Version update** and changelog
7. **Update all agents** with new rules

See individual constitutions for detailed amendment templates.

---

## Cross-References

**Main Constitution:**
- `.claude/CONSTITUTION.md` - Comprehensive rules document

**Related Documentation:**
- `docs/security/DATA_SECURITY_POLICY.md` - Data protection details
- `docs/development/AI_RULES_OF_ENGAGEMENT.md` - AI agent guidelines
- `docs/architecture/SOLVER_ALGORITHM.md` - Scheduling engine details
- `docs/architecture/cross-disciplinary-resilience.md` - Resilience framework

**Implementation:**
- `backend/app/scheduling/acgme_validator.py` - ACGME compliance code
- `backend/app/core/security.py` - Security implementation
- `backend/app/resilience/` - Resilience framework code

---

## Quick Reference

| Topic | Constitution | Section |
|-------|-------------|---------|
| ACGME 80-hour rule | SCHEDULING.md | II.A |
| ACGME 1-in-7 rule | SCHEDULING.md | II.B |
| Supervision ratios | SCHEDULING.md | II.C |
| Constraint hierarchy | SCHEDULING.md | III |
| N-1/N-2 contingency | SCHEDULING.md | IV.B |
| Schedule backup | SCHEDULING.md | VI |
| Swap validation | SCHEDULING.md | VII |
| PHI/PII protection | SAFETY_CRITICAL.md | II.B |
| OPSEC/PERSEC | SAFETY_CRITICAL.md | IV |
| Forbidden git ops | SAFETY_CRITICAL.md | V.A |
| Forbidden DB ops | SAFETY_CRITICAL.md | V.B |
| Emergency overrides | SAFETY_CRITICAL.md | VI |
| Escalation procedures | SAFETY_CRITICAL.md | VII |
| CLI-first design | CORE.md | II |
| Logging requirements | CORE.md | III |
| Security layers | CORE.md | IV |
| Error handling | CORE.md | V |
| Code quality | CORE.md | VIII |

---

## Version Control

All constitutions follow semantic versioning:
- **Major version (X.0.0)**: Breaking changes to rules
- **Minor version (0.X.0)**: New rules or significant clarifications
- **Patch version (0.0.X)**: Minor clarifications or typo fixes

**Current Versions:**
- CORE.md: 1.0.0
- SCHEDULING.md: 1.0.0
- SAFETY_CRITICAL.md: 1.0.0

See individual constitution amendment histories for detailed change logs.

---

**These constitutions work together to ensure safe, compliant, and reliable AI-assisted development.**
