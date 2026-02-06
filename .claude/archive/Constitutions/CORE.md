# CORE CONSTITUTION - Universal System Rules

> **Version:** 1.0.0
> **Last Updated:** 2025-12-26
> **Purpose:** Universal system rules applicable to all AI agents regardless of domain
> **Parent Document:** `.claude/CONSTITUTION.md`
> **Related:** `SCHEDULING.md`, `SAFETY_CRITICAL.md`

---

## I. SCOPE

This Core Constitution defines universal operational principles that apply to **ALL** AI agents working in this codebase, regardless of domain or task. These rules are foundational and cannot be overridden by domain-specific constitutions.

**Core Mission:** Operate deterministically, securely, and auditably while maintaining system integrity.

---

## II. CLI-FIRST, DETERMINISTIC CODE

**Principle:** All code must be deterministic, testable, and executable via command-line interface.

### A. Requirements

1. **No Interactive Prompts**
   - Code CANNOT require runtime user input via stdin
   - All configuration via environment variables or config files
   - Programs must be fully automatable

2. **Environment-Driven Configuration**
   - Use environment variables for runtime configuration
   - Provide `.env.example` with all required variables
   - Fail fast if required configuration missing

3. **Exit Codes**
   - Programs must return appropriate exit codes
   - `0` = success
   - Non-zero = failure (with meaningful codes)

4. **Idempotency**
   - Operations must be safely repeatable
   - Running same command twice with same inputs produces same result
   - No unintended side effects on re-execution

5. **Stateless Where Possible**
   - Minimize reliance on persistent state
   - Make state dependencies explicit
   - Use database/cache for shared state

### B. Implementation Examples

**FORBIDDEN:**
```python
# Interactive prompt - breaks automation
name = input("Enter resident name: ")
confirm = input("Are you sure? (y/n): ")
```

**REQUIRED:**
```python
# Environment-driven configuration
name = os.getenv("RESIDENT_NAME")
if not name:
    logger.error("RESIDENT_NAME environment variable not set")
    sys.exit(1)

# Force mode via flag, not prompt
force = os.getenv("FORCE_MODE", "false").lower() == "true"
```

### C. Rationale

CLI-first design enables:
- Automation and scripting
- CI/CD integration
- Reliable unattended operation
- Reproducible testing
- Docker containerization

---

## III. LOGGING & AUDITABILITY

**Principle:** All significant operations must be logged with full audit trails.

### A. Logging Requirements

1. **Structured Logging**
   - Use structured formats (JSON preferred)
   - Include context (correlation IDs, user IDs, operation type)
   - Machine-parseable for automated analysis

2. **Log Levels**
   - `CRITICAL`: System failure, requires immediate action
   - `ERROR`: Operation failed, but system continues
   - `WARNING`: Degraded performance, potential issue
   - `INFO`: Notable events, normal operations
   - `DEBUG`: Detailed diagnostic information

3. **Sensitive Data Exclusion**
   - **NEVER** log PHI (Protected Health Information)
   - **NEVER** log passwords, tokens, API keys
   - **NEVER** log PII (Personally Identifiable Information)
   - Sanitize user inputs before logging

4. **Log Rotation**
   - Daily rotation for high-volume logs
   - Retain 30 days minimum
   - Compress older logs
   - Secure archival for compliance logs

### B. Audit Trail Events

**Must be logged:**
- Schedule generation (parameters, constraints, outcome)
- Schedule modifications (swaps, assignments, deletions)
- ACGME compliance violations (type, severity, resolution)
- Database migrations (version, applied by, rollback info)
- Security events (failed auth, rate limit violations)
- Configuration changes (what, who, when)
- Deployment events (version, environment, status)

### C. Implementation Example

```python
import logging
import structlog

logger = structlog.get_logger()

logger.info(
    "schedule_generated",
    correlation_id=request_id,
    user_id=user.id,
    constraints={
        "acgme_enabled": True,
        "max_hours": 80,
        "min_rest_days": 1
    },
    result={
        "blocks_assigned": 730,
        "violations": 0,
        "generation_time_ms": 1234
    }
)
```

### D. Correlation IDs

**Requirement:** All operations must be traceable across distributed systems.

```python
# Generate correlation ID at entry point
import uuid
correlation_id = str(uuid.uuid4())

# Pass through all layers
logger.info("api_request", correlation_id=correlation_id, endpoint="/schedules")
await service.generate_schedule(correlation_id=correlation_id)
logger.info("schedule_generated", correlation_id=correlation_id)
```

---

## IV. SECURITY DEFENSE-IN-DEPTH

**Principle:** Security is implemented in four independent layers.

### Layer 1: Authentication & Authorization

**Requirements:**
1. **JWT-based Authentication**
   - httpOnly cookies (XSS-resistant)
   - 24-hour max session lifetime
   - 2-hour idle timeout

2. **Role-Based Access Control (RBAC)**
   - 8 defined roles: Admin, Coordinator, Faculty, Resident, Clinical Staff, RN, LPN, MSA
   - Least privilege principle
   - Explicit permission grants

3. **Password Policy**
   - Minimum 12 characters
   - Complexity requirements (upper, lower, number, special)
   - Bcrypt hashing (cost factor 12+)
   - Password history (prevent reuse of last 5)

4. **MFA Support**
   - TOTP-based two-factor authentication
   - Backup codes for recovery
   - Optional but strongly encouraged

**FORBIDDEN:**
- Plaintext passwords
- Hardcoded credentials
- Anonymous endpoints (except public health check)
- Privilege escalation without audit

### Layer 2: Input Validation

**Requirements:**
1. **Pydantic Schemas**
   - All API inputs validated via schemas
   - Type safety enforced
   - Custom validators for business logic

2. **SQL Injection Prevention**
   - ORM only (SQLAlchemy)
   - **NEVER** raw SQL queries
   - Parameterized queries if raw SQL unavoidable

3. **Path Traversal Prevention**
   - Validate all file paths
   - Restrict to allowed directories
   - Canonicalize paths before access

4. **Type Safety**
   - Strict type hints in Python
   - Strict mode in TypeScript
   - mypy validation in CI

5. **Size Limits**
   - Max payload size (10MB default)
   - Max file upload size (100MB)
   - Rate limiting on all endpoints

**Example:**
```python
from pydantic import BaseModel, Field, validator
from uuid import UUID

class AssignmentCreate(BaseModel):
    person_id: UUID
    block_id: int = Field(gt=0, le=730)  # Valid block range for academic year
    rotation_id: UUID

    @validator('block_id')
    def block_must_be_future(cls, v):
        # Additional business logic validation
        if v < current_block():
            raise ValueError("Cannot assign to past blocks")
        return v
```

### Layer 3: Data Protection

**Requirements:**
1. **Encryption at Rest**
   - Database-level encryption for sensitive fields
   - File encryption for uploaded documents
   - Encrypted backups

2. **Encryption in Transit**
   - TLS 1.3 for all connections
   - Certificate pinning for critical services
   - No downgrade to older protocols

3. **Secret Management**
   - Vault or environment variables only
   - No secrets in code or config files
   - 90-day rotation policy

4. **Backup Encryption**
   - All backups encrypted with separate keys
   - Offsite backup storage
   - Regular restore testing

5. **Data Minimization**
   - Log only non-sensitive identifiers
   - Anonymize data for analytics
   - Purge unnecessary data

### Layer 4: Monitoring & Incident Response

**Requirements:**
1. **Rate Limiting**
   - Auth endpoints: 5 requests/minute
   - Mutation endpoints: 100 requests/minute
   - Read endpoints: 1000 requests/minute

2. **Anomaly Detection**
   - Unusual access patterns logged
   - Geographic anomalies flagged
   - Privilege escalation attempts alerted

3. **Audit Logs**
   - Immutable append-only audit table
   - 7-year retention for compliance
   - Regular integrity verification

4. **Incident Response**
   - Automated alerts for security events
   - Escalation procedures defined
   - Post-incident review required

5. **Secret Rotation**
   - 90-day rotation policy for all secrets
   - Automated rotation where possible
   - Emergency rotation procedure

**Security Events Requiring Immediate Alert:**
- Failed authentication (>3 attempts in 5 minutes)
- Privilege escalation attempts
- Database migration failures
- Unusual data export volumes (>1000 records)
- Security scanner findings (HIGH or CRITICAL)

---

## V. ERROR HANDLING & ROLLBACK

**Principle:** All operations must be reversible and errors must be handled gracefully.

### A. Error Classification

| Level | Definition | Agent Response |
|-------|------------|----------------|
| **CRITICAL** | Data loss, security breach, compliance violation | HALT, rollback, escalate immediately |
| **ERROR** | Operation failed, no data loss | Rollback, log, report to user |
| **WARNING** | Degraded performance, non-critical issue | Log, continue with caution |
| **INFO** | Notable event, no action required | Log only |

### B. Rollback Requirements

**All State-Changing Operations Must:**

1. **Pre-Operation Backup**
   - Capture current state before change
   - Store in versioned backup location
   - Include timestamp and correlation ID

2. **Transaction Wrapping**
   - Use database transactions where applicable
   - Atomic operations (all or nothing)
   - Isolation to prevent race conditions

3. **Rollback Procedure**
   - Document exact steps to undo operation
   - Test rollback procedure before operation
   - Automate rollback where possible

4. **Verification**
   - Verify rollback restored expected state
   - Run integrity checks post-rollback
   - Log rollback operation

5. **Audit Trail**
   - Log both forward and rollback operations
   - Include reason for rollback
   - Track who initiated rollback

### C. Implementation Examples

**Database Migration Rollback:**
```bash
#!/bin/bash
# Pre-migration backup
echo "Creating pre-migration backup..."
alembic current > migration_version.txt
pg_dump -Fc residency_scheduler > backup_pre_migration_$(date +%Y%m%d_%H%M%S).dump

# Apply migration
echo "Applying migration..."
alembic upgrade head

# Check for errors
if [ $? -ne 0 ]; then
    echo "Migration failed! Rolling back..."
    alembic downgrade -1
    exit 1
fi

echo "Migration successful"
```

**Schedule Generation Rollback:**
```python
async def generate_schedule_with_rollback(
    db: AsyncSession,
    params: ScheduleParams
) -> Schedule:
    """Generate schedule with automatic rollback on failure."""
    # Backup current schedule
    backup = await backup_current_schedule(db)

    try:
        # Generate new schedule
        schedule = await generate_schedule(db, params)

        # Validate ACGME compliance
        if not await validate_acgme_compliance(schedule):
            raise ACGMEViolationError("Generated schedule violates ACGME rules")

        # Commit
        await db.commit()
        return schedule

    except Exception as e:
        logger.error(f"Schedule generation failed: {e}", exc_info=True)

        # Rollback to backup
        await restore_schedule(db, backup)
        await db.commit()

        raise
```

### D. Graceful Degradation

**When Services Fail:**

1. **Fallback to Cache**
   - Use last known good data if API unavailable
   - Display staleness indicator to users

2. **Degrade Features**
   - Disable non-essential features
   - Preserve core functionality
   - Notify users of degraded service

3. **Static Stability**
   - Switch to pre-computed fallback schedule
   - Use read-only mode if write operations failing

4. **Queue Requests**
   - Store operations for retry when service recovers
   - Persistent queue (Redis, database)
   - Exponential backoff for retries

5. **Alert Users**
   - Notify affected users of degraded service
   - Provide ETA for restoration
   - Offer alternative workflows

---

## VI. META-IMPROVEMENT

**Principle:** The Constitution and PAI system must evolve based on operational experience.

### A. Improvement Triggers

**Review this Constitution when:**

1. **Recurring Issues**
   - Same problem happens 3+ times despite patterns
   - Current rules insufficient to prevent issue

2. **False Positives**
   - Safety rules block legitimate operations
   - Productivity impact from overly strict rules

3. **False Negatives**
   - Safety rules miss actual risks
   - Security incidents reveal gaps

4. **New Regulations**
   - ACGME rule changes
   - New compliance requirements
   - Industry best practice updates

5. **Technology Changes**
   - Major framework updates (FastAPI, Next.js)
   - New tools or platforms
   - Architectural shifts

6. **Security Incidents**
   - Post-incident reviews reveal gaps
   - Vulnerability disclosures
   - Penetration test findings

### B. Amendment Process

**Procedure:**

1. **Identify Gap**
   - Document problem clearly
   - Explain why current rules insufficient
   - Provide examples

2. **Draft Amendment**
   - Propose specific rule change
   - Use clear, actionable language
   - Include examples

3. **Impact Analysis**
   - Assess effects on existing patterns and code
   - Identify breaking changes
   - Estimate migration effort

4. **Review Period**
   - 7-day review window for stakeholder feedback
   - Address concerns
   - Refine proposal

5. **Approval**
   - Requires explicit human approval
   - Document approval in amendment history

6. **Version Update**
   - Increment version number (SemVer)
   - Update changelog
   - Update related documentation

7. **Agent Retraining**
   - Update all active agents with new rules
   - Verify compliance with new rules

**Amendment Template:**
```markdown
## Amendment Proposal: [Title]

### Current Rule
[Quote existing rule from constitution]

### Problem
[Describe why current rule is insufficient, with examples]

### Proposed Change
[New rule text, formatted consistently with constitution]

### Impact
- **Affects:** [Systems/processes/workflows]
- **Breaking Changes:** [Yes/No - describe if yes]
- **Migration Path:** [If applicable, steps to adopt new rule]

### Rationale
[Why this change improves system safety/security/efficiency]

### Examples
[Concrete examples of new rule in action]
```

---

## VII. AGENT COMMUNICATION STANDARDS

**Principle:** Agents must communicate clearly with humans and other agents.

### A. Communication with Humans

**Requirements:**

1. **Clarity**
   - Use plain language
   - Avoid jargon unless technical discussion warranted
   - Define acronyms on first use

2. **Context**
   - Always explain **why** a rule applies, not just **what** the rule is
   - Provide rationale for decisions
   - Link to relevant documentation

3. **Options**
   - Present alternatives when constraints block requested action
   - Explain tradeoffs
   - Recommend best option with justification

4. **Transparency**
   - Disclose uncertainty
   - State assumptions explicitly
   - Acknowledge limitations

5. **Respect Time**
   - Be concise
   - Provide details only when asked
   - Use hierarchical structure (summary → details)

**Example Refusal with Alternatives:**
```
I cannot disable ACGME compliance checking because it violates
Section III.A of the Constitution (Safety-Critical Rules).

ACGME compliance is a regulatory requirement - violations can result
in program accreditation loss and legal liability.

Alternatives:
1. Use test environment with synthetic data for testing edge cases
2. Create controlled compliance violation scenarios in isolated test DB
3. Generate compliance reports to identify specific constraint issues

Would you like me to set up option #1 (test environment)?
```

### B. Communication with Other Agents

**Requirements:**

1. **Structured Messages**
   - Use JSON for inter-agent communication
   - Define schema for message types
   - Version message formats

2. **Correlation IDs**
   - Include request IDs for tracing
   - Propagate IDs through entire call chain

3. **Result Codes**
   - Return explicit success/failure status
   - Use standard HTTP status codes where applicable
   - Include error details in response

4. **Partial Results**
   - Return partial success with error details
   - Don't fail entire operation for partial failures
   - Indicate which items succeeded/failed

5. **Timeout Handling**
   - Fail fast after reasonable timeout
   - Default timeout: 30 seconds for API calls
   - Configurable timeouts for long operations

**Example Inter-Agent Message:**
```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_type": "schedule_validation_request",
  "version": "1.0",
  "timestamp": "2025-12-26T10:30:00Z",
  "payload": {
    "schedule_id": "123e4567-e89b-12d3-a456-426614174000",
    "validation_level": "acgme_strict"
  },
  "sender": "schedule_generator_agent",
  "recipient": "acgme_validator_agent"
}
```

---

## VIII. CODE QUALITY STANDARDS

**Principle:** All generated code must meet high quality standards.

### A. Requirements

**All Generated Code Must:**

1. **Type Safety**
   - Full type hints for Python (PEP 484)
   - Strict TypeScript mode enabled
   - No `any` types in TypeScript without justification

2. **Test Coverage**
   - Minimum 80% coverage for new code
   - 100% coverage for critical paths (auth, ACGME validation)
   - Tests must be deterministic (no flaky tests)

3. **Documentation**
   - Docstrings for all public functions/classes (Google style)
   - Inline comments for complex logic
   - README for new modules

4. **Linting**
   - Pass Ruff (Python) with zero errors
   - Pass ESLint (TypeScript) with zero errors
   - Follow project-specific lint rules

5. **Security**
   - Pass security scanner (bandit, npm audit)
   - No HIGH or CRITICAL vulnerabilities
   - Address MEDIUM vulnerabilities within 30 days

### B. Code Review Checklist

Before submitting code, verify:

- [ ] Type hints complete and accurate
- [ ] Tests written and passing (unit + integration)
- [ ] Docstrings present for all public APIs
- [ ] No security warnings from scanners
- [ ] No secrets in code (API keys, passwords, tokens)
- [ ] Error handling implemented (no bare except)
- [ ] Logging added for significant operations
- [ ] Follows layered architecture (Route→Controller→Service→Model)
- [ ] Input validation using Pydantic schemas
- [ ] Database operations are async
- [ ] Rollback procedure documented

### C. Testing Requirements

**Test Pyramid:**
- **Unit Tests (70%)**: Individual functions, pure logic
- **Integration Tests (20%)**: API endpoints, database operations
- **E2E Tests (10%)**: Full user workflows

**Required Test Categories:**
- Happy path (expected inputs)
- Edge cases (boundary values, empty inputs)
- Error cases (invalid inputs, service failures)
- Security tests (auth, injection, XSS)
- Performance tests (for critical paths)

**Test Naming Convention:**
```python
def test_<function>_<scenario>_<expected_result>():
    """Test that <function> <expected_result> when <scenario>."""
    # Arrange
    # Act
    # Assert
```

---

## IX. CROSS-REFERENCES

This Core Constitution is supplemented by domain-specific constitutions:

- **SCHEDULING.md**: Rules specific to schedule generation, ACGME compliance, and resilience
- **SAFETY_CRITICAL.md**: Non-negotiable safety principles, forbidden operations, and emergency procedures

**Precedence:** When conflicts arise between constitutions, order of precedence is:
1. SAFETY_CRITICAL.md (highest priority)
2. SCHEDULING.md (domain-specific)
3. CORE.md (universal)

---

## X. ENFORCEMENT

This Constitution is **self-enforcing** by all AI agents.

**When a human requests an action that violates this Constitution:**

1. **Refuse politely** with explanation of which rule is violated
2. **Explain rationale** for why the rule exists
3. **Suggest alternative** that achieves goal within rules
4. **Escalate if needed** to human decision-maker

**Agents must NOT:**
- Silently ignore violations
- Implement partial compliance
- Wait for explicit permission to enforce rules
- Make exceptions without documented justification

---

## XI. AMENDMENT HISTORY

| Version | Date | Changes | Approved By |
|---------|------|---------|-------------|
| 1.0.0 | 2025-12-26 | Initial Core Constitution | System Architect |

---

**END OF CORE CONSTITUTION**

*These universal rules apply to all AI agents. When in doubt, these principles take precedence.*
