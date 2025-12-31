# Prompt Library

> **Last Updated:** 2025-12-31
> **Purpose:** Reusable prompt templates for common AI agent tasks

---

## Table of Contents

1. [ACGME Validation](#acgme-validation)
2. [Code Review](#code-review)
3. [Test Generation](#test-generation)
4. [Documentation](#documentation)
5. [Debugging](#debugging)
6. [Refactoring](#refactoring)
7. [Database Migrations](#database-migrations)
8. [Incident Response](#incident-response)
9. [Compliance Audits](#compliance-audits)
10. [Performance Optimization](#performance-optimization)
11. [Accessibility](#accessibility)
12. [API Design](#api-design)
13. [Query Optimization](#query-optimization)
14. [Error Handling](#error-handling)
15. [Security Hardening](#security-hardening)

---

## ACGME Validation

### Template: Schedule Compliance Check

```
Read the schedule generation logic in [FILE]. Focus on:

1. 80-hour rule implementation
   - How does the system track rolling 4-week averages?
   - What happens when a resident approaches 80 hours?

2. 1-in-7 rule implementation
   - How is the 24-hour off-day requirement tracked?
   - What's the enforcement mechanism?

3. Supervision ratio requirements
   - PGY-1: 1 faculty per 2 residents
   - PGY-2/3: 1 faculty per 4 residents
   - How are ratios calculated and enforced?

Report any violations in a checklist format.
```

### Template: Constraint Validation

```
Validate that the constraint [CONSTRAINT_NAME] in [FILE] is properly:

1. Defined in the constraint catalog
2. Exported in __init__.py
3. Registered with the solver
4. Tested in test_[constraint].py

Report findings as:
- PASS: All validation steps complete
- FAIL: [Specific step that failed]
- WARN: [Edge case or concern]
```

### Template: Compliance Regression Test

```
Write test cases to verify that [REGULATORY_CHANGE] is enforced.

Test structure:
1. Setup: Create baseline schedule violating the new rule
2. Action: Run schedule generation or validation
3. Assert: Verify rule is enforced
4. Edge cases: Test boundary conditions

Ensure tests document:
- The regulatory requirement
- Why the test is important
- Expected behavior when rule is violated
```

---

## Code Review

### Template: Security-Focused Review

```
Review this code for security vulnerabilities:

/home/user/Autonomous-Assignment-Program-Manager/[FILE]

Focus on:
1. Input validation
   - Are all inputs validated with Pydantic?
   - Are file paths validated?

2. Authentication/Authorization
   - Is auth required for sensitive operations?
   - Are role-based checks in place?

3. Data protection
   - Are secrets handled securely?
   - Is sensitive data logged?
   - Are SQL injections prevented (using ORM)?

4. Error messages
   - Do errors leak sensitive information?
   - Are generic error messages used?

Report using severity levels: CRITICAL, WARNING, INFO, GOOD
```

### Template: Performance Review

```
Review [FILE] for performance issues:

1. Database queries
   - Any N+1 queries?
   - Missing eager loading?
   - Inefficient joins?

2. Algorithm efficiency
   - What's the time complexity?
   - Can it be optimized?

3. Memory usage
   - Large data structures?
   - Memory leaks?

4. Async/await
   - Are all I/O operations async?
   - Any blocking calls in async code?

Suggest specific optimizations with impact estimates.
```

### Template: Architecture Review

```
Review [FILE] for architecture compliance:

Check that code follows the layered pattern:
Route (thin) → Controller → Service → Repository → Model

Questions:
1. Is business logic in services or routes?
2. Are database operations in the ORM layer?
3. Are Pydantic schemas used for validation?
4. Are dependencies properly injected?

Identify any architecture violations and suggest fixes.
```

---

## Test Generation

### Template: Unit Test Generation

```
Write unit tests for [FUNCTION_NAME] in [FILE].

Requirements:
1. Coverage target: [COVERAGE_TARGET]
2. Test normal cases + edge cases
3. Test error conditions and exceptions
4. Use pytest fixtures for dependencies
5. Mock external dependencies

Test structure:
- TestClass for each function/class
- test_[function]_[scenario] naming
- Clear assertions with descriptive messages
- Docstrings explaining what's tested

Generate tests that achieve [COVERAGE_TARGET]% coverage.
```

### Template: Integration Test Generation

```
Write integration tests for [FEATURE] that:

1. Test multiple components working together
2. Use actual database connections (or fixtures)
3. Verify API contract
4. Test error paths and edge cases

Test scenarios:
- Happy path
- Input validation failures
- Authorization failures
- Database constraint violations
- Concurrent operations

Generate [N] integration tests.
```

### Template: Fixture Generation

```
Create pytest fixtures for [DOMAIN]:

1. Standard fixtures
   - database session
   - test data builders
   - authentication helpers

2. Domain-specific fixtures
   - Schedule fixtures
   - Person/Assignment fixtures
   - Rotation fixtures

3. Cleanup fixtures
   - Transaction rollback
   - State cleanup
   - Resource cleanup

Fixtures should be reusable and composable.
```

---

## Documentation

### Template: API Documentation

```
Generate API documentation for [ENDPOINT] in [FILE]:

Include:
1. Endpoint path and HTTP method
2. Request body schema (Pydantic model)
3. Response schema (Pydantic model)
4. Authentication requirements
5. Example requests/responses
6. Error responses
7. Rate limits
8. Related endpoints

Format: Markdown suitable for OpenAPI/Swagger
```

### Template: Function Documentation

```
Review and enhance docstrings for [FILE]:

Each function should have:
1. One-line summary
2. Extended description (if needed)
3. Args: parameter list with types
4. Returns: return value and type
5. Raises: exceptions that can be raised
6. Examples: usage examples (if complex)

Format: Google-style docstrings
```

### Template: Architecture Documentation

```
Document the architecture of [COMPONENT]:

1. Purpose: What does it do?
2. Design: How is it structured?
3. Responsibilities: What code is responsible for what?
4. Dependencies: What does it depend on?
5. Integration: How does it connect to other systems?
6. Example usage: Code examples
7. Common patterns: Best practices
8. Gotchas: Common mistakes to avoid
```

---

## Debugging

### Template: Exploration-First Debugging

```
Phase 1: EXPLORATION (DO NOT FIX YET)

Read [FILE] and examine [ERROR_LOG].
Questions to answer:
1. What is the exact error?
2. When does it occur?
3. What code path leads to it?
4. What state exists when it happens?

Document findings without proposing fixes.
```

### Template: Root Cause Analysis

```
Given the symptom: [SYMPTOM]

Analyze to find root cause:
1. Is it a code issue?
   - Logic error?
   - Type error?
   - Resource leak?

2. Is it a configuration issue?
   - Environment variable?
   - Database settings?
   - Third-party API?

3. Is it a concurrency issue?
   - Race condition?
   - Missing locking?
   - Order dependency?

Create hypothesis list ranked by likelihood.
```

### Template: Test-Driven Debugging

```
Step 1: Write failing tests

Create test cases that reproduce [BUG].
- Tests should fail with same error as bug
- Don't create mocks, use real objects
- Ensure tests are deterministic

Step 2: Verify tests fail
Run tests and confirm they fail with expected error.

Step 3: Fix to make tests pass
Implement fix until all tests pass.
Tests should NOT be modified.
```

---

## Refactoring

### Template: Extract Function

```
Refactor [FILE] to extract [FUNCTION]:

Requirements:
1. Extract [CODE_BLOCK] into new function
2. Function signature: [PARAMS] → [RETURN]
3. Update all call sites
4. Write tests for new function
5. Verify tests pass
6. Update any affected documentation

After refactoring:
- All tests should pass
- No behavioral changes
- Code should be more readable
```

### Template: Rename Refactoring

```
Rename [VARIABLE/FUNCTION] to [NEW_NAME] throughout [SCOPE]:

Steps:
1. Find all occurrences
2. Update in order: defs, usages, tests, docs
3. Run tests after each batch
4. Verify IDE refactoring is correct

Check these locations:
- Implementation files
- Test files
- Documentation
- Comments and docstrings
- Database queries (if applicable)
```

### Template: Simplification

```
Simplify [FILE] while maintaining behavior:

Identify opportunities to:
1. Remove unnecessary variables
2. Simplify conditional logic
3. Reduce function length
4. Remove duplication
5. Clarify confusing code

For each change:
1. Implement change
2. Run tests to verify no behavior change
3. Commit separately

Focus on readability without sacrificing clarity.
```

---

## Database Migrations

### Template: Schema Change Migration

```
Create Alembic migration for [CHANGE]:

Process:
1. Modify model in [MODEL_FILE]
2. Create migration: alembic revision --autogenerate -m "[MESSAGE]"
3. Review generated migration in alembic/versions/
4. Test upgrade: alembic upgrade head
5. Test downgrade: alembic downgrade -1
6. Test upgrade again: alembic upgrade head

Ensure migration handles:
- Data preservation
- Index updates
- Constraint changes
- Rollback capability
```

### Template: Data Migration

```
Create migration to transform data in [TABLE]:

Migration must:
1. Migrate existing data without loss
2. Be reversible (downgrade must work)
3. Handle NULL values appropriately
4. Preserve foreign key relationships
5. Update related constraints

Steps:
1. Write upgrade function
2. Write downgrade function
3. Test both directions
4. Document any data transformations
5. Validate data integrity after migration
```

### Template: Safe Migration Deployment

```
Plan deployment of migration [MIGRATION]:

Pre-deployment:
1. Backup database
2. Test migration on staging
3. Estimate execution time
4. Plan rollback procedure

Deployment:
1. Run migration
2. Verify success (check row counts, constraints)
3. Run full test suite
4. Monitor application logs

Rollback plan:
1. If migration fails: downgrade immediately
2. Restore from backup if needed
3. Root cause analysis
```

---

## Incident Response

### Template: Production Incident Diagnosis

```
Incident: [SYMPTOM]
Time: [WHEN]

Phase 1: Gather Facts
- What exactly is broken?
- Who reported it?
- When did it start?
- What changed recently?

Phase 2: Establish Severity
- Is it affecting production?
- How many users impacted?
- Business impact: [HIGH/MEDIUM/LOW]

Phase 3: Root Cause Analysis
Check:
1. Recent deployments
2. Database errors
3. Third-party API failures
4. Resource exhaustion
5. Concurrency issues

Phase 4: Emergency Fix
If cause is clear: implement quick fix
If unclear: deploy workaround

Phase 5: Permanent Fix
Fix root cause, add tests to prevent recurrence
```

### Template: Incident Postmortem

```
Incident Postmortem: [INCIDENT_NAME]

Timeline:
- [TIME]: What happened
- [TIME]: Detection
- [TIME]: Investigation started
- [TIME]: Workaround deployed
- [TIME]: Root cause identified
- [TIME]: Permanent fix deployed

Root Cause:
[Explanation of underlying issue]

Impact:
- Duration: [TIME]
- Users affected: [COUNT]
- Transactions lost: [COUNT]
- Financial impact: [AMOUNT]

Lessons Learned:
1. What could we have detected earlier?
2. How can we prevent this again?
3. What monitoring should we add?

Action Items:
- [ ] Implement permanent fix
- [ ] Add monitoring/alerting
- [ ] Add test coverage
- [ ] Update runbooks
```

### Template: Escalation Checklist

```
When to escalate incident to human:

Escalate immediately when:
- [ ] Production data loss possible
- [ ] Customer-facing service down > 15 minutes
- [ ] Security vulnerability
- [ ] Regulatory compliance risk
- [ ] Multiple system failures

Contact procedure:
1. Notify on-call engineer
2. Provide: incident summary, severity, steps taken
3. Wait for acknowledgment
4. Continue investigation in parallel

Provide escalation with:
- [ ] Clear description of issue
- [ ] Severity assessment
- [ ] Steps already taken
- [ ] Current status
- [ ] Requested action
```

---

## Compliance Audits

### Template: HIPAA Compliance Check

```
Audit [COMPONENT] for HIPAA compliance:

Check:
1. Data Protection
   - Is PHI encrypted at rest?
   - Is PHI encrypted in transit (TLS)?
   - Are backups encrypted?

2. Access Controls
   - Is access logged?
   - Are role-based controls in place?
   - Are default credentials changed?

3. Audit Trails
   - Are all accesses logged?
   - Is log retention adequate?
   - Are logs tamper-proof?

4. Error Handling
   - Do error messages leak PHI?
   - Are errors logged securely?

Report findings as:
- COMPLIANT
- NON-COMPLIANT (with details)
- REQUIRES ATTENTION
```

### Template: Security Audit

```
Comprehensive security audit of [SYSTEM]:

1. Code Review
   - Vulnerabilities (OWASP Top 10)
   - Cryptography (secure algorithms)
   - Input validation

2. Configuration
   - Secrets management
   - Default credentials
   - Unnecessary services

3. Dependencies
   - Vulnerable packages (CVEs)
   - License compliance
   - Outdated versions

4. Operations
   - Monitoring/alerting
   - Incident response
   - Disaster recovery

Report: Risk assessment with recommendations
```

### Template: Data Privacy Review

```
Review [FEATURE] for data privacy compliance:

Questions:
1. What personal data is collected?
2. Is consent obtained?
3. Is data minimized?
4. How long is data retained?
5. Can users access their data?
6. Can users delete their data?
7. Are data processing agreements in place?
8. Is data processing documented?

Report: Privacy assessment and recommendations
```

---

## Performance Optimization

### Template: Performance Profiling

```
Profile [OPERATION] to find bottlenecks:

Methods:
1. Measure baseline performance
2. Use cProfile to identify slow functions
3. Use SQL query profiler for database
4. Use memory profiler for memory leaks
5. Load test to find scalability limits

Commands:
- Python: python -m cProfile -s cumulative script.py
- Pytest: pytest --profile [test]
- k6: k6 run scenarios/[scenario].js

Report:
- Current performance metrics
- Top bottlenecks
- Optimization recommendations
- Expected improvement
```

### Template: Query Optimization

```
Optimize SQL queries in [FILE]:

For each slow query:
1. Analyze execution plan
   - EXPLAIN ANALYZE [QUERY]
   - Identify sequential scans
   - Check for missing indexes

2. Optimize
   - Add indexes
   - Restructure joins
   - Add eager loading (SQLAlchemy)

3. Measure improvement
   - Compare before/after
   - Verify tests still pass
   - Check for side effects

Document:
- Original query and time
- Optimization applied
- New query and time
- Performance improvement %
```

### Template: Scaling Analysis

```
Analyze scaling characteristics of [COMPONENT]:

Questions:
1. How does performance degrade with scale?
2. Where are the hard limits?
3. Can it handle 10x user growth?
4. Where are bottlenecks?

Tests:
- Load testing at various scales
- Stress testing until failure
- Soak testing for memory leaks
- Spike testing for peak handling

Report:
- Performance at various scales
- Identified bottlenecks
- Recommendations for scaling
- Required infrastructure changes
```

---

## Accessibility

### Template: WCAG 2.1 Audit

```
Audit [COMPONENT] for accessibility:

Check:
1. Perceivable
   - Images have alt text
   - Color not sole indicator
   - No flashing content

2. Operable
   - Keyboard navigation works
   - No keyboard traps
   - Sufficient touch target size

3. Understandable
   - Plain language used
   - Consistent navigation
   - Error messages clear

4. Robust
   - Valid HTML
   - Proper ARIA labels
   - Screen reader compatible

Tools:
- axe DevTools browser extension
- WAVE tool
- Screen reader testing (NVDA, JAWS)

Report: WCAG 2.1 level A/AA/AAA compliance
```

### Template: Keyboard Navigation Test

```
Test keyboard navigation for [FEATURE]:

Actions to test:
- Tab through all interactive elements
- Shift+Tab to go backwards
- Enter to activate buttons
- Space to toggle checkboxes
- Arrow keys for lists/menus
- Escape to close modals

Document:
- Expected behavior for each key
- Actual behavior
- Issues found
- Remediation needed
```

---

## API Design

### Template: REST API Review

```
Review [ENDPOINT] for REST API best practices:

Check:
1. Naming
   - Resource-based URLs (nouns, not verbs)
   - Plural collection names
   - Consistent naming patterns

2. HTTP Methods
   - GET for retrieval (no side effects)
   - POST for creation
   - PUT/PATCH for updates
   - DELETE for deletion

3. Status Codes
   - 200: Success
   - 201: Created
   - 204: No content
   - 400: Bad request
   - 401: Unauthorized
   - 403: Forbidden
   - 404: Not found
   - 500: Server error

4. Request/Response
   - Consistent JSON structure
   - Proper content types
   - Error response format

Report: API design assessment
```

### Template: API Contract Testing

```
Create contract tests for [API]:

Test structure:
1. Consumer test
   - What does client expect?
   - Document expected behavior

2. Provider test
   - Does API provide what's expected?
   - Verify compatibility

3. Breaking change detection
   - Run tests on both versions
   - Identify incompatibilities

Tools:
- Pact for contract testing
- OpenAPI generators
- API versioning strategy

Report: Contract compatibility matrix
```

---

## Query Optimization

### Template: Slow Query Investigation

```
Investigate slow query in [FILE]:

Steps:
1. Get query
   - Enable query logging
   - Identify slow query
   - Capture full query and timing

2. Analyze
   - EXPLAIN ANALYZE [QUERY]
   - Identify table scans
   - Check join order
   - Review where clause

3. Optimize
   - Consider indexes
   - Rewrite joins
   - Add LIMIT/OFFSET optimization
   - Use materialized views if needed

4. Verify
   - Test new query
   - Measure performance gain
   - Verify result correctness
   - Check for side effects

Document changes and performance impact.
```

### Template: Index Analysis

```
Analyze index usage for [TABLE]:

Questions:
1. What indexes exist?
2. Which are unused?
3. Which are redundant?
4. What new indexes are needed?

Commands:
- List indexes: \\di [table]
- Check usage: SELECT * FROM pg_stat_user_indexes
- Analyze: ANALYZE [table]

Optimization:
- Remove unused indexes
- Consolidate redundant indexes
- Add missing indexes
- Verify impact on INSERT/UPDATE performance

Report: Index optimization recommendations
```

---

## Error Handling

### Template: Error Handling Review

```
Review error handling in [FILE]:

Check:
1. Exception Types
   - Specific exceptions vs generic Exception
   - Custom exceptions for domain-specific errors
   - Proper exception hierarchy

2. Error Information
   - Errors have descriptive messages
   - Stack traces preserved (but not logged to client)
   - Error codes for machine parsing

3. Error Recovery
   - Can the system recover from errors?
   - Are retries appropriate?
   - Are timeouts reasonable?

4. Error Propagation
   - Errors propagated to right level
   - Not swallowing exceptions silently
   - Proper error response to client

Report: Error handling assessment and improvements
```

### Template: Error Message Audit

```
Review error messages in [COMPONENT]:

Checklist:
- [ ] Messages are user-friendly
- [ ] Messages don't leak sensitive data
- [ ] Messages suggest resolution
- [ ] Log messages are developer-friendly
- [ ] Error codes are documented
- [ ] Errors are consistent

Examples of bad messages:
- "SQLException: Column 'password' not found"
  Fix: "Authentication failed"

- "KeyError: 'user_id' in request"
  Fix: "Missing required parameter: user_id"

Report: Error message improvements needed
```

---

## Security Hardening

### Template: Dependency Security Audit

```
Audit dependencies in [REQUIREMENTS.TXT or PACKAGE.JSON]:

Tools:
- pip-audit (Python)
- npm audit (Node.js)
- OWASP Dependency-Check
- Snyk

Process:
1. Identify vulnerable packages
2. Check for available updates
3. Assess compatibility of updates
4. Plan update strategy
5. Test after updates
6. Document changes

Report:
- Vulnerable packages found
- Severity of each
- Recommended fixes
- Timeline for patching
```

### Template: Secrets Rotation Plan

```
Plan secrets rotation for [SYSTEM]:

Secrets to rotate:
1. API keys
2. Database passwords
3. JWT signing keys
4. Encryption keys
5. Third-party credentials

For each secret:
1. How is it currently stored?
2. How often should it rotate?
3. Can rotation happen without downtime?
4. What's the rollback procedure?
5. How will old secrets be revoked?

Implementation:
- Create secrets rotation mechanism
- Test rotation process
- Document rotation procedures
- Set up automated rotation
- Create alerting for expiration

Report: Secrets management strategy
```

---

## Template Usage Guidelines

### When to Use Templates

1. **Exact Scenario Match** - Use the template as-is if your scenario matches exactly
2. **Partial Match** - Adapt the template, skipping irrelevant sections
3. **New Scenario** - Create a new template following the pattern

### Template Customization

Each template should be customized with:
- `[FILE]` - Actual file paths
- `[FUNCTION_NAME]` - Actual function/class names
- `[COVERAGE_TARGET]` - Specific percentage (e.g., 85%)
- `[SCENARIO]` - Specific scenario description

### Best Practices

1. **Be Specific** - Replace placeholders with actual values
2. **Provide Context** - Include relevant background information
3. **Set Clear Goals** - Define success criteria upfront
4. **Request Deliverables** - Specify exact output format
5. **Ask for Validation** - Request verification steps

---

## Creating Custom Templates

### Template Format

```
### Template: [Category] - [Specific Task]

\`\`\`
[Prompt text with placeholders in [BRACKETS]]

Include:
1. Clear objective
2. Specific steps or checks
3. Success criteria
4. Output format

Example customization:
[Concrete example of prompt with actual values]
\`\`\`
```

### Template Validation

New templates should:
- [ ] Have a clear title
- [ ] Include objective statement
- [ ] List specific checks or steps
- [ ] Define output format
- [ ] Provide customization example
- [ ] Include success criteria

---

## Integration with Skills

Each template should indicate which skill uses it:

| Skill | Uses Templates From |
|-------|-------------------|
| `code-review` | Code Review, Security Hardening |
| `test-writer` | Test Generation, Debugging |
| `security-audit` | Security Hardening, Compliance |
| `acgme-compliance` | ACGME Validation, Compliance |
| `database-migration` | Database Migrations, Query Optimization |
| `pr-reviewer` | Code Review, API Design |

---

## Performance Notes

- Templates are designed to be copied and customized quickly
- Use placeholders sparingly to avoid confusion
- Prefer specific examples over generic descriptions
- Keep templates focused on single task (not meta-work)

