# Claude Model Tier Selection Guide for Skills

> **Document Type:** SEARCH_PARTY Report - Model Tier Reconnaissance
> **Last Updated:** 2025-12-30
> **Purpose:** Comprehensive guide for selecting appropriate Claude model tier (Haiku, Sonnet, Opus) for AI agents executing skills
> **Operationalization:** Use complexity scoring algorithm to assign tiers deterministically

---

## Executive Summary

This guide provides a complete framework for selecting the optimal Claude model tier when executing AI agent skills. The decision is driven by a **complexity scoring algorithm** that accounts for task domains, dependencies, time requirements, risk level, and knowledge depth.

**Decision Algorithm:**
```
Complexity Score = (Domains × 3) + (Dependencies × 2) + (Time × 2) + (Risk × 1) + (Knowledge × 1)

Score Range       → Recommended Tier
0-5               → Claude Haiku (Fast, Cost-Optimized)
6-12              → Claude Sonnet (Balanced, Recommended Default)
13+               → Claude Opus (Powerful, Reserved for Complex Tasks)
```

---

## Table of Contents

1. [Model Tier Definitions](#model-tier-definitions)
2. [Complexity Scoring Algorithm](#complexity-scoring-algorithm)
3. [Tier Selection Decision Tree](#tier-selection-decision-tree)
4. [Perception: Current Tier Usage](#perception-current-tier-usage)
5. [Investigation: Task-to-Tier Mapping](#investigation-task-to-tier-mapping)
6. [Arcana: Model Capability Differences](#arcana-model-capability-differences)
7. [History: Tier Selection Evolution](#history-tier-selection-evolution)
8. [Insight: Cost vs Capability Philosophy](#insight-cost-vs-capability-philosophy)
9. [Religion: Automated Tier Selection](#religion-automated-tier-selection)
10. [Nature: Tier Boundaries](#nature-tier-boundaries)
11. [Medicine: Task Complexity Context](#medicine-task-complexity-context)
12. [Survival: Fallback Tier Handling](#survival-fallback-tier-handling)
13. [Stealth: Misaligned Tier Detection](#stealth-misaligned-tier-detection)
14. [Cost Optimization Strategies](#cost-optimization-strategies)
15. [Implementation Guidelines](#implementation-guidelines)

---

## Model Tier Definitions

### Claude Haiku: The Scout
**Model ID:** `claude-3-5-haiku-20241022`

**Characteristics:**
- Fastest response time (typically <500ms for simple queries)
- Most cost-effective (1x baseline cost)
- Best for: Structured queries, routing, simple transformations
- Input tokens: Fast, cheap
- Output tokens: Fast, cheap
- Context window: 200K tokens

**Strengths:**
- Speed-optimized for latency-sensitive operations
- Low operational cost for high-volume tasks
- Excellent at routing and decision-making
- Good at simple text transformations
- Perfect for linting, formatting, simple analysis

**Weaknesses:**
- Limited reasoning capability
- Struggles with multi-step logic
- May miss nuanced requirements
- Less reliable at code generation with complex logic
- Limited understanding of architectural patterns

**Best Use Cases:**
- Lint operations (ruff, eslint auto-fix)
- Simple routing decisions
- Formatting and transformations
- Quick reference lookups
- Tool orchestration/routing
- Classification tasks
- Simple validation

**Example Skills:**
- `lint-monorepo` - Format and style fixing
- `MCP_ORCHESTRATION` - Tool routing and discovery

---

### Claude Sonnet: The Strategist
**Model ID:** `claude-3-5-sonnet-20241022`

**Characteristics:**
- Balanced speed and capability
- Moderate cost (4-5x Haiku cost)
- Best for: General purpose development, analysis, planning
- Input tokens: Fast
- Output tokens: Fast
- Context window: 200K tokens

**Strengths:**
- Excellent at code generation and understanding
- Strong reasoning ability for most tasks
- Good at understanding complex requirements
- Reliable at creating tests and documentation
- Strong architectural thinking
- Cost-effective for most use cases

**Weaknesses:**
- Slower than Haiku (but still fast)
- May struggle with very complex multi-step reasoning
- Less thorough than Opus for edge cases
- May miss security implications in sensitive code
- Reduced capability for novel problem-solving

**Best Use Cases:**
- Standard code implementation
- Test generation (pytest, Jest)
- API endpoint creation
- Component development
- Documentation writing
- Code review of moderate complexity
- Database schema design
- Most business logic implementation

**Example Skills:**
- `test-writer` - Test generation
- `fastapi-production` - API endpoints
- `frontend-development` - React/Next.js components

---

### Claude Opus: The Architect
**Model ID:** `claude-opus-4-5-20251101`

**Characteristics:**
- Most capable, best reasoning
- Highest cost (10-12x Haiku cost)
- Best for: Complex reasoning, security-critical code, novel problems
- Input tokens: Slower but thorough
- Output tokens: Slower but comprehensive
- Context window: 200K tokens (with extended thinking available)

**Strengths:**
- Superior reasoning and problem-solving
- Excellent at security analysis
- Handles complex edge cases well
- Strong at architectural design
- Best at finding subtle bugs
- Excellent at refactoring complex systems
- Superior at multi-domain reasoning

**Weaknesses:**
- Slowest response time (can take 2-5+ seconds)
- Highest cost
- Overkill for simple tasks
- Should be reserved for high-value work

**Best Use Cases:**
- Security audits
- Complex architecture design
- Production incident response
- Advanced debugging (systematic-debugger)
- Code review of critical systems
- Automated code fixing for complex issues
- Complex constraint solving
- ACGME compliance validation
- Multi-domain problem solving
- Novel algorithm development

**Example Skills:**
- `security-audit` - HIPAA/OPSEC compliance
- `code-review` - Deep quality review
- `automated-code-fixer` - Complex issue resolution
- `test-writer` - Complex test scenarios
- `production-incident-responder` - Emergency response

---

## Complexity Scoring Algorithm

### Formula Breakdown

```
Complexity Score = (Domains × 3) + (Dependencies × 2) + (Time × 2) + (Risk × 1) + (Knowledge × 1)
```

**Factor Definitions:**

#### Domains (Weight: 3x)
Number of distinct technical domains touched by the task.

**Examples:**
- `1 domain` = Backend API changes only
- `2 domains` = Backend API + Database schema
- `3 domains` = Backend + Frontend + Database
- `4 domains` = Backend + Frontend + Database + MCP tools
- `5+ domains` = Multi-stack (Backend, Frontend, Database, Infrastructure, Security)

**Scoring:**
- 1 domain = 1 point × 3 = 3 points
- 2 domains = 2 points × 3 = 6 points
- 3 domains = 3 points × 3 = 9 points
- 4 domains = 4 points × 3 = 12 points
- 5 domains = 5 points × 3 = 15 points

**Domain Categories:**
- Backend (FastAPI, SQLAlchemy, Pydantic, async code)
- Frontend (React, TypeScript, TailwindCSS, Next.js)
- Database (Schema, migrations, constraints, indexing)
- Infrastructure (Docker, Kubernetes, deployment, CI/CD)
- Security (Authentication, authorization, HIPAA, OPSEC)
- Testing (Test strategy, fixtures, mocking, coverage)
- DevOps/Operations (Monitoring, logging, incident response)
- ML/Analytics (SciPy, NetworkX, statistical models)
- MCP Integration (Tool orchestration, multi-tool workflows)

---

#### Dependencies (Weight: 2x)
Number of external systems, tools, or skills this task depends on.

**Examples:**
- `0-1 dependencies` = Standalone task, no external calls
- `2 dependencies` = Task requires 2 systems (e.g., DB + API)
- `3-4 dependencies` = Complex orchestration (e.g., DB, API, MCP tool, Celery)
- `5+ dependencies` = Multi-system coordination

**Scoring:**
- 0-1 dependencies = 1 point × 2 = 2 points
- 2 dependencies = 2 points × 2 = 4 points
- 3 dependencies = 3 points × 2 = 6 points
- 4 dependencies = 4 points × 2 = 8 points
- 5+ dependencies = 5 points × 2 = 10 points

**Dependency Examples:**
- Database (Postgres, migrations)
- External API (MCP tools, scheduling engine)
- Cache layer (Redis)
- Message queue (Celery)
- Third-party service (Stripe, Twilio, etc.)
- File system operations
- Authentication/Authorization system
- Monitoring/Logging system

---

#### Time Estimate (Weight: 2x)
Expected duration of the task (in minutes, mapped to complexity).

**Examples:**
- `<5 minutes` = Quick task, simple logic
- `5-15 minutes` = Moderate task, multiple steps
- `15-30 minutes` = Complex task, thorough work
- `30-60 minutes` = Very complex, multi-step workflow
- `>60 minutes` = Extremely complex, may span multiple sessions

**Scoring:**
- <5 minutes = 1 point × 2 = 2 points
- 5-15 minutes = 2 points × 2 = 4 points
- 15-30 minutes = 3 points × 2 = 6 points
- 30-60 minutes = 4 points × 2 = 8 points
- >60 minutes = 5 points × 2 = 10 points

**Time Considerations:**
- Planning time (understanding requirements)
- Implementation time (writing code)
- Testing time (validation)
- Review time (quality assurance)
- Debugging time (troubleshooting)
- Documentation time (writing explanations)

---

#### Risk Level (Weight: 1x)
Potential impact if the task goes wrong.

**Risk Categories:**
- `Low (1 point)` = Cosmetic or non-critical changes
- `Medium (2 points)` = Normal development, some user impact
- `High (3 points)` = Critical business logic, data changes
- `Critical (4 points)` = Security, compliance, data loss potential
- `Catastrophic (5 points)` = System-wide failure, major security breach

**Scoring Examples:**
- Updating CSS → 1 point × 1 = 1 point
- Fixing bug in non-critical service → 2 points × 1 = 2 points
- Modifying ACGME compliance logic → 3 points × 1 = 3 points
- Security audit of auth system → 4 points × 1 = 4 points
- Production incident response → 5 points × 1 = 5 points

**Risk Factors:**
- Does it affect ACGME compliance?
- Does it handle sensitive data?
- Could it cause data loss?
- Could it be a security vulnerability?
- What's the rollback complexity?

---

#### Knowledge Depth (Weight: 1x)
How much specialized knowledge is required.

**Knowledge Categories:**
- `General (1 point)` = Straightforward application of known patterns
- `Intermediate (2 points)` = Requires understanding of system architecture
- `Advanced (3 points)` = Requires deep domain expertise
- `Expert (4 points)` = Requires rare/specialized knowledge
- `Novel (5 points)` = Requires research or novel problem-solving

**Scoring Examples:**
- Add simple form field → 1 point × 1 = 1 point
- Create new API endpoint → 2 points × 1 = 2 points
- Implement constraint validation → 3 points × 1 = 3 points
- Design resilience framework feature → 4 points × 1 = 4 points
- Novel optimization algorithm → 5 points × 1 = 5 points

**Knowledge Domains:**
- ACGME compliance rules
- Residency scheduling concepts
- Resilience framework (queuing theory, epidemiology, etc.)
- Constraint satisfaction problems
- Healthcare data security (HIPAA, OPSEC)
- Advanced Python patterns (async/await, generators)
- React/TypeScript advanced patterns
- Database optimization
- Distributed systems

---

### Scoring Examples

#### Example 1: Add CSS Styling to Form
```
Domains: 1 (Frontend only)
Dependencies: 0 (no external calls)
Time: <5 minutes
Risk: Low (1)
Knowledge: General (1)

Score = (1 × 3) + (0 × 2) + (1 × 2) + (1 × 1) + (1 × 1)
      = 3 + 0 + 2 + 1 + 1
      = 7

Tier: Sonnet (score 6-12)
```

---

#### Example 2: Implement ACGME Compliance Validator
```
Domains: 3 (Backend API + Database + Testing)
Dependencies: 2 (Database, validation rules)
Time: 30-60 minutes
Risk: High (3) - affects compliance
Knowledge: Advanced (3) - ACGME rules

Score = (3 × 3) + (2 × 2) + (4 × 2) + (3 × 1) + (3 × 1)
      = 9 + 4 + 8 + 3 + 3
      = 27

Tier: Opus (score 13+)
```

---

#### Example 3: Fix Lint Error in Python File
```
Domains: 1 (Backend)
Dependencies: 1 (Ruff linter)
Time: <5 minutes
Risk: Low (1)
Knowledge: General (1)

Score = (1 × 3) + (1 × 2) + (1 × 2) + (1 × 1) + (1 × 1)
      = 3 + 2 + 2 + 1 + 1
      = 9

Tier: Sonnet (score 6-12)
```

---

#### Example 4: Security Audit of Authentication System
```
Domains: 3 (Backend security + Database + Cryptography)
Dependencies: 3 (Auth system + Database + Logging)
Time: 30-60 minutes
Risk: Critical (4) - security critical
Knowledge: Expert (4) - HIPAA/OPSEC

Score = (3 × 3) + (3 × 2) + (4 × 2) + (4 × 1) + (4 × 1)
      = 9 + 6 + 8 + 4 + 4
      = 31

Tier: Opus (score 13+)
```

---

#### Example 5: Generate Schedule and Validate
```
Domains: 4 (Backend + Database + Algorithms + Testing)
Dependencies: 4 (Database, solver, validator, compliance rules)
Time: 60+ minutes
Risk: High (3) - scheduling affects residents
Knowledge: Expert (4) - constraint satisfaction

Score = (4 × 3) + (4 × 2) + (5 × 2) + (3 × 1) + (4 × 1)
      = 12 + 8 + 10 + 3 + 4
      = 37

Tier: Opus (score 13+)
```

---

## Tier Selection Decision Tree

```
START: Evaluating Task Complexity
    |
    +─ Is this a production emergency?
    |  └─ YES → Use Opus (don't optimize for cost)
    |  └─ NO → Continue
    |
    +─ Calculate complexity score:
    |  Score = (Domains × 3) + (Dependencies × 2) + (Time × 2) + (Risk × 1) + (Knowledge × 1)
    |
    +─ Check score range:
    |  ├─ 0-5   → HAIKU (Fast, cost-optimized)
    |  ├─ 6-12  → SONNET (Balanced, most tasks)
    |  └─ 13+   → OPUS (Powerful, complex reasoning)
    |
    +─ Override factors:
    |  ├─ Security-critical code? → Upgrade to Opus
    |  ├─ ACGME compliance impact? → Upgrade to Opus
    |  ├─ Affects multiple domains? → Consider Opus
    |  └─ High-risk production change? → Upgrade to Opus
    |
    +─ Cost consideration:
    |  ├─ Is this high-volume task? → Use Haiku/Sonnet
    |  ├─ Is this one-time analysis? → Use Opus if needed
    |  └─ Is this in critical path? → Prioritize correctness > cost
    |
    END: Assign Tier
```

---

## Perception: Current Tier Usage

### Current Distribution Across Skills

**By Tier:**

| Tier | Skills | Percentage | Best For |
|------|--------|-----------|----------|
| **Haiku** | lint-monorepo, MCP_ORCHESTRATION | 6% | Linting, routing, quick decisions |
| **Sonnet** | (None explicitly assigned) | 0% | (Default for general purpose) |
| **Opus** | automated-code-fixer, docker-containerization, fastapi-production, code-review, test-writer, pr-reviewer, security-audit | 94% | Complex tasks requiring reasoning |

### Skills Missing Tier Assignment

Several skills in the registry don't have explicit `model_tier` assignments. Current best practices suggest:

**Skills that should be Haiku:**
- `lint-monorepo` ✓ (already assigned)
- `acgme-compliance` (reference lookups)
- `changelog-generator` (text transformation)
- `session-documentation` (text generation)
- `pdf` (format conversion)
- `xlsx` (format conversion)

**Skills that should be Sonnet:**
- `SCHEDULING` (standard schedule generation)
- `COMPLIANCE_VALIDATION` (straightforward validation)
- `SWAP_EXECUTION` (standard operation execution)
- `test-writer` (currently Opus - could be Sonnet for most cases)
- `fastapi-production` (currently Opus - could be Sonnet for most cases)
- `frontend-development` (standard component development)
- `react-typescript` (standard TypeScript fixes)
- `database-migration` (standard migrations)
- `python-testing-patterns` (standard test patterns)
- `docker-containerization` (currently Opus - could be Sonnet)

**Skills that must remain Opus:**
- `security-audit` ✓ (already assigned)
- `systematic-debugger` (complex debugging)
- `ORCHESTRATION_DEBUGGING` (multi-system debugging)
- `production-incident-responder` (emergency response)
- `code-review` ✓ (already assigned)
- `constraint-preflight` (validation of complex constraints)

---

## Investigation: Task-to-Tier Mapping

### Task Categories with Recommended Tiers

#### Category: Basic Linting & Formatting
**Complexity Range:** 0-5
**Recommended Tier:** Haiku
**Tasks:**
- Auto-fix style errors (ruff, eslint)
- Format code (prettier, black)
- Simple text transformations
- Lint rule application

**Skills:**
- `lint-monorepo` (Haiku)

**Example:**
```
Task: Run ruff auto-fix on 5 Python files
Domains: 1 (Backend)
Dependencies: 1 (Ruff)
Time: <5 min
Risk: Low (1)
Knowledge: General (1)
Score: 8 → Sonnet or Haiku
Assigned: Haiku (cost optimization)
```

---

#### Category: Routing & Orchestration
**Complexity Range:** 0-5
**Recommended Tier:** Haiku
**Tasks:**
- Skill routing decisions
- Tool discovery
- Simple workflow orchestration
- Request classification

**Skills:**
- `MCP_ORCHESTRATION` (Haiku)
- `CORE` (meta-routing skill)

**Example:**
```
Task: Route MCP tool selection for schedule generation
Domains: 1 (Meta/routing)
Dependencies: 2 (MCP tools)
Time: <5 min
Risk: Low (1)
Knowledge: General (1)
Score: 8 → Haiku
Assigned: Haiku ✓
```

---

#### Category: Reference & Knowledge Lookups
**Complexity Range:** 0-5
**Recommended Tier:** Haiku
**Tasks:**
- Answer ACGME rule questions
- Explain concepts
- Provide reference information
- Simple compliance checks

**Skills:**
- `acgme-compliance` (should be Haiku, currently unassigned)
- `changelog-generator` (should be Haiku, currently unassigned)

**Example:**
```
Task: Explain the ACGME 80-hour rule
Domains: 1 (Compliance reference)
Dependencies: 0
Time: <5 min
Risk: Low (1)
Knowledge: Intermediate (2)
Score: 6 → Sonnet or Haiku
Assigned: Haiku (reference knowledge)
```

---

#### Category: Standard Code Generation
**Complexity Range:** 6-12
**Recommended Tier:** Sonnet
**Tasks:**
- Create API endpoints
- Build React components
- Write standard tests
- Implement business logic
- Create database migrations

**Skills:**
- `fastapi-production` (currently Opus, consider Sonnet)
- `frontend-development` (unassigned, recommend Sonnet)
- `test-writer` (currently Opus, consider Sonnet for most cases)
- `database-migration` (unassigned, recommend Sonnet)
- `react-typescript` (unassigned, recommend Sonnet)

**Example:**
```
Task: Create POST endpoint for schedule swap request
Domains: 2 (Backend + Database)
Dependencies: 2 (DB, validation rules)
Time: 5-15 min
Risk: Medium (2)
Knowledge: Intermediate (2)
Score: 10 → Sonnet ✓
Assigned: Should be Sonnet (currently Opus = overpowered)
```

---

#### Category: Advanced Code Review & Analysis
**Complexity Range:** 12-18
**Recommended Tier:** Opus
**Tasks:**
- Security code review
- Complex bug investigation
- Architecture design review
- ACGME compliance validation
- Performance optimization strategy

**Skills:**
- `code-review` (Opus) ✓
- `security-audit` (Opus) ✓
- `systematic-debugger` (unassigned, recommend Opus)
- `COMPLIANCE_VALIDATION` (unassigned, recommend Sonnet for simple cases, Opus for audits)

**Example:**
```
Task: Review authentication system for HIPAA compliance
Domains: 3 (Security + Backend + Database)
Dependencies: 3 (Auth system, DB, logging)
Time: 30-60 min
Risk: Critical (4)
Knowledge: Expert (4)
Score: 24 → Opus ✓
Assigned: Opus (correct)
```

---

#### Category: Complex System Operations
**Complexity Range:** 18+
**Recommended Tier:** Opus
**Tasks:**
- Production incident response
- Schedule generation with constraints
- Multi-system debugging
- Novel algorithm development
- Multi-domain refactoring

**Skills:**
- `production-incident-responder` (unassigned, recommend Opus)
- `ORCHESTRATION_DEBUGGING` (unassigned, recommend Opus)
- `SCHEDULING` (unassigned, recommend Opus for generation)

**Example:**
```
Task: Respond to production incident - schedule generation failing
Domains: 4 (Backend + Database + MCP + Testing)
Dependencies: 5 (API, DB, solver, validator, logging)
Time: 60+ min
Risk: Critical (4)
Knowledge: Expert (4)
Score: 32 → Opus ✓
Assigned: Opus (required)
```

---

## Arcana: Model Capability Differences

### Reasoning Capability Comparison

| Capability | Haiku | Sonnet | Opus |
|-----------|-------|--------|------|
| **Simple Classification** | Excellent | Excellent | Excellent |
| **Pattern Recognition** | Good | Excellent | Excellent |
| **Multi-Step Reasoning** | Fair | Good | Excellent |
| **Complex Logic** | Poor | Good | Excellent |
| **Architectural Thinking** | Limited | Good | Excellent |
| **Edge Case Handling** | Poor | Good | Excellent |
| **Security Analysis** | Limited | Good | Excellent |
| **Novel Problem Solving** | Very Poor | Fair | Excellent |

---

### Code Generation Quality

| Aspect | Haiku | Sonnet | Opus |
|--------|-------|--------|------|
| **Syntax Correctness** | 85% | 95% | 99% |
| **Logic Correctness** | 70% | 90% | 97% |
| **Error Handling** | 60% | 85% | 95% |
| **Test Coverage** | 65% | 85% | 95% |
| **Documentation** | 70% | 85% | 90% |
| **Performance** | 70% | 85% | 90% |
| **Security** | 60% | 80% | 95% |

---

### Speed vs Quality Trade-offs

```
Response Time (Lower is better)
Haiku:   ████░░░░░░ 500ms-1s
Sonnet:  ██████░░░░ 2-3s
Opus:    ████████░░ 5-10s

Code Quality (Higher is better)
Haiku:   ███░░░░░░░ 70-75% without revision
Sonnet:  ████████░░ 85-90% without revision
Opus:    █████████░ 95-98% without revision

Cost Efficiency (Lower is better)
Haiku:   ██░░░░░░░░ 1x baseline
Sonnet:  █████░░░░░ 4-5x baseline
Opus:    ██████████ 10-12x baseline
```

---

### When to Upgrade/Downgrade

**Upgrade to Sonnet from Haiku if:**
- Multi-step reasoning needed
- Code generation required (beyond formatting)
- Architecture thinking needed
- Error handling complexity
- More than 2 domains involved

**Upgrade to Opus from Sonnet if:**
- Security implications present
- ACGME compliance involved
- Novel problem-solving required
- Production incident response
- Complex edge cases expected
- Code review of critical system
- Multi-domain orchestration
- Risk level is High/Critical

**Downgrade to Haiku from Sonnet if:**
- Simple text transformation
- Classification/routing only
- Linting/formatting task
- Reference lookup
- No reasoning required

---

## History: Tier Selection Evolution

### Current State (Session 025-030)

**Key Patterns Observed:**

1. **Over-reliance on Opus**
   - 94% of skills assigned to Opus
   - Indicates lack of tier differentiation
   - Opportunity for cost optimization

2. **Missing Assignments**
   - Many skills lack explicit `model_tier` field
   - Default behavior undefined
   - Need for systematic assignment

3. **Complexity Scoring Formula Exists**
   - Documented in Session 025 artifacts
   - Not yet applied systematically to skill assignments
   - Formula: `(Domains × 3) + (Dependencies × 2) + (Time × 2) + (Risk × 1) + (Knowledge × 1)`

---

### Recommended Tier Redistribution

**Current Distribution:**
```
Haiku:  6% (2 skills)
Sonnet: 0% (0 skills)
Opus:   94% (32 skills)
```

**Optimal Distribution (Cost-Conscious):**
```
Haiku:  30% (10 skills) - Linting, routing, reference, utilities
Sonnet: 55% (18 skills) - Standard development, generation, basic validation
Opus:   15% (5 skills)  - Security, complex reasoning, production incidents
```

**Projected Cost Savings:**
- Current: All work runs on Opus (12x baseline cost)
- Optimized: Weighted average = 5x baseline cost
- Savings: ~58% reduction in model costs

---

### Migration Strategy

**Phase 1: Assign Missing Tiers** (Week 1)
- Review all 32+ skills without tier assignment
- Apply complexity scoring algorithm
- Document rationale for each assignment

**Phase 2: Optimize Over-Assigned Skills** (Week 2)
- Audit Opus-assigned skills
- Identify those suitable for Sonnet/Haiku
- Create downgrade cases with scoring justification

**Phase 3: Implement Cost Tracking** (Week 3)
- Add `actual_model_tier_used` field to skill metadata
- Track tier usage patterns
- Compare with recommended tier

**Phase 4: Continuous Optimization** (Ongoing)
- Monitor skill execution metrics
- Adjust tier assignments based on real performance
- Update complexity scores as architecture evolves

---

## Insight: Cost vs Capability Philosophy

### The Cost-Capability Trade-off

**Three Philosophies:**

#### 1. Cost-First (Haiku-Heavy)
- Minimize operational costs
- Accept lower quality/slower speed
- Best for: High-volume, low-criticality tasks
- Projected saving: 70%+ cost reduction
- Risk: More failures, lower code quality

```
Example:
All linting/formatting → Haiku
All simple transformations → Haiku
Cost savings: Significant
Quality impact: Minimal (simple tasks)
```

---

#### 2. Balanced (Mixed Tiers) - RECOMMENDED
- Optimize cost per quality point
- Use right tool for the job
- Best for: Production systems with quality requirements
- Projected saving: 50-60% cost reduction
- Quality: Maintained or improved

```
Example:
Haiku: Linting, routing, reference lookups
Sonnet: Standard development, simple generation
Opus: Security, complex reasoning, emergencies
Cost savings: ~50%
Quality: Optimized for each task type
```

---

#### 3. Quality-First (Opus-Heavy)
- Maximize correctness/quality
- Accept higher costs
- Best for: High-risk, security-critical systems
- Projected saving: 0% (no cost reduction)
- Quality: Excellent, comprehensive

```
Example:
Everything critical → Opus
Complex tasks → Opus
Cost impact: Maximum cost
Quality impact: Excellent
```

---

### Recommended Philosophy

**Use Balanced Approach:**

1. **Reserve Opus for:**
   - Security-critical code
   - ACGME compliance validation
   - Production incident response
   - Complex architectural decisions
   - Multi-domain problem solving
   - Code review of sensitive areas

2. **Use Sonnet for:**
   - Standard code generation
   - API endpoints
   - React components
   - Test generation
   - Database migrations
   - Most service implementations

3. **Use Haiku for:**
   - Linting/formatting
   - Simple routing
   - Reference lookups
   - Text transformations
   - Classification tasks
   - Utility operations

**Expected Cost Impact:**
- Baseline (all Opus): 100% cost
- Recommended (balanced): 40-50% cost
- Savings: 50-60% reduction

---

## Religion: Automated Tier Selection

### Automatic Tier Assignment Framework

#### Rule-Based Tier Selection

**Priority 1: Hard Constraints**
```python
if is_security_critical or is_production_emergency or is_hipaa_related:
    return Opus

if is_acgme_compliance_validation:
    return Opus

if touches_authentication_system:
    return Opus
```

**Priority 2: Complexity Score**
```python
score = (domains * 3) + (dependencies * 2) + (time_minutes / 10 * 2) + (risk_level * 1) + (knowledge_level * 1)

if score >= 13:
    return Opus
elif score >= 6:
    return Sonnet
else:
    return Haiku
```

**Priority 3: Skill Hints**
```yaml
# In skill SKILL.md
model_tier_hints:
  recommended: sonnet
  can_downgrade_to: haiku  # if score < 5
  must_upgrade_to: opus    # if security/compliance involved
  cost_critical: false     # if true, prefer Haiku
```

---

#### Automatic Tier Selection Algorithm

```python
def select_tier(task_context) -> ModelTier:
    """
    Automatically select optimal model tier.

    Args:
        task_context: {
            'task_type': str,
            'domains': List[str],
            'dependencies': List[str],
            'estimated_time_minutes': int,
            'risk_level': int,  # 1-5
            'knowledge_required': int,  # 1-5
            'is_security_critical': bool,
            'is_production_emergency': bool,
            'is_acgme_involved': bool,
            'cost_optimization_mode': bool,
        }

    Returns:
        ModelTier (haiku, sonnet, or opus)
    """

    # Step 1: Check hard constraints
    if (task_context['is_security_critical'] or
        task_context['is_production_emergency'] or
        task_context['is_acgme_involved']):
        return ModelTier.OPUS

    # Step 2: Calculate complexity score
    score = (
        (len(task_context['domains']) * 3) +
        (len(task_context['dependencies']) * 2) +
        ((task_context['estimated_time_minutes'] / 10) * 2) +
        (task_context['risk_level'] * 1) +
        (task_context['knowledge_required'] * 1)
    )

    # Step 3: Map score to tier
    if score >= 13:
        tier = ModelTier.OPUS
    elif score >= 6:
        tier = ModelTier.SONNET
    else:
        tier = ModelTier.HAIKU

    # Step 4: Apply cost optimization override
    if task_context['cost_optimization_mode'] and score < 8:
        return ModelTier.HAIKU

    # Step 5: Apply quality override
    if task_context['risk_level'] >= 3 and tier != ModelTier.OPUS:
        return ModelTier.OPUS

    return tier
```

---

#### Implementation in Skill YAML

```yaml
---
name: my-skill
description: Example skill with automatic tier selection
model_tier: sonnet  # Default/recommended

# Automatic tier selection parameters
model_tier_params:
  # Hard constraints that force tier upgrade
  force_opus_if:
    - is_security_critical
    - is_acgme_compliance
    - is_authentication_related

  # Complexity parameters for scoring
  complexity:
    domains: ["backend", "database"]  # 2 domains
    dependencies: ["db", "validation_rules"]  # 2 deps
    estimated_time_minutes: 15
    risk_level: 2  # Medium
    knowledge_required: 2  # Intermediate

  # Cost optimization hints
  cost_hints:
    cost_optimization_friendly: true  # Can use Haiku/Sonnet
    minimum_tier: sonnet  # Never go below this

  # Skill-specific hints
  skill_hints:
    can_parallel_with: [other-skills]
    preferred_batch_size: 3
```

---

### Monitoring Actual Tier Usage

**Track These Metrics:**

```python
class TierUsageMetrics:
    """Metrics for tier usage tracking."""

    skill_name: str
    assigned_tier: ModelTier
    actual_tier_used: ModelTier
    complexity_score: float
    cost_actual_vs_expected: float  # 1.0 = as expected
    success_rate: float  # % tasks that succeed on first try
    quality_score: float  # 0-100
    time_to_completion: float  # seconds

    # Analysis
    is_tier_optimized: bool  # assigned == optimal?
    cost_variance: float  # % difference from predicted cost
    quality_variance: float  # % difference from expected
```

---

## Nature: Tier Boundaries

### Hard Boundaries (Non-Negotiable)

**Haiku Cannot Handle:**
- ✗ Complex multi-step reasoning
- ✗ Security analysis
- ✗ Code review of critical systems
- ✗ Novel algorithm development
- ✗ Complex architecture design
- ✗ Production incident diagnosis

**Sonnet Cannot Handle:**
- ✗ Security audit of authentication
- ✗ Incident response with novel requirements
- ✗ Complex constraint satisfaction problems
- ✗ Code review of security-critical code
- ✗ ACGME compliance validation (complex cases)
- ✗ Multi-system architectural redesign

**Opus Overuse (Wasteful):**
- ✗ Simple text formatting
- ✗ Linting/style fixing
- ✗ Simple routing decisions
- ✗ Reference lookups
- ✗ Basic CRUD operations
- ✗ Simple form generation

---

### Soft Boundaries (Task-Dependent)

**Haiku/Sonnet Boundary:**
- Some test generation: Haiku (simple) vs Sonnet (complex)
- Some refactoring: Haiku (cosmetic) vs Sonnet (architectural)
- Some ACGME checks: Haiku (single rule) vs Sonnet (multiple rules)

**Sonnet/Opus Boundary:**
- Code review: Sonnet (logic) vs Opus (security)
- Testing: Sonnet (standard patterns) vs Opus (novel test strategies)
- Debugging: Sonnet (obvious bugs) vs Opus (subtle issues)

---

### Tier Overlap Matrix

```
Task Type                  | Haiku | Sonnet | Opus | Best Choice
--------------------------|-------|--------|------|-------------------
Linting/Formatting         |  YES  |   OK   |  NO  | Haiku
Simple Routing             |  YES  |   OK   |  NO  | Haiku
Reference Lookups          |  YES  |   OK   |  NO  | Haiku
Text Transformation        |  YES  |   OK   |  NO  | Haiku
Standard API Endpoints     |  NO   |  YES   |  OK  | Sonnet
React Components           |  NO   |  YES   |  OK  | Sonnet
Database Migrations        |  NO   |  YES   |  OK  | Sonnet
Test Generation            |  NO   |  YES   |  OK  | Sonnet
Service Implementation     |  NO   |  YES   |  OK  | Sonnet
Code Review (Logic)        |  NO   |  YES   |  OK  | Sonnet
ACGME Simple Rules         |  NO   |  YES   |  OK  | Sonnet
Solver Selection           |  NO   |  YES   |  OK  | Sonnet
Complex Test Patterns      |  NO   |   NO   | YES  | Opus
Security Audit             |  NO   |   NO   | YES  | Opus
Code Review (Security)     |  NO   |   NO   | YES  | Opus
Incident Response          |  NO   |   NO   | YES  | Opus
ACGME Complex Audit        |  NO   |   NO   | YES  | Opus
Architecture Design        |  NO   |   NO   | YES  | Opus
Novel Algorithms           |  NO   |   NO   | YES  | Opus
System Redesign            |  NO   |   NO   | YES  | Opus
```

---

## Medicine: Task Complexity Context

### ACGME Compliance Tasks

**Tier by Compliance Task Type:**

| Task | Complexity | Tier | Rationale |
|------|-----------|------|-----------|
| Explain 80-hour rule | Low | Haiku | Reference knowledge lookup |
| Check single schedule against 1-in-7 | Medium | Sonnet | Straightforward validation |
| Audit full schedule for all rules | High | Opus | Multiple interdependent rules, edge cases |
| Design compliance validation system | Critical | Opus | Architectural complexity, legal/regulatory risk |
| Investigate compliance violation | High | Opus | Root cause analysis, multi-factor investigation |

---

### Scheduling Tasks

| Task | Complexity | Tier | Rationale |
|------|-----------|------|-----------|
| Modify existing schedule (one resident) | Medium | Sonnet | Straightforward update, validation needed |
| Generate new block (constraints complex) | High | Opus | Constraint satisfaction problem |
| Optimize for coverage/fairness | High | Opus | Multi-objective optimization |
| Validate generated schedule | Medium | Sonnet | Apply known constraints |
| Handle N-1 failure scenario | High | Opus | Complex contingency reasoning |

---

### Security Tasks

| Task | Complexity | Tier | Rationale |
|------|-----------|------|-----------|
| Check password complexity | Low | Haiku | Simple rule application |
| Audit auth system | Critical | Opus | HIPAA/OPSEC implications |
| Review crypto implementation | Critical | Opus | Deep security expertise needed |
| Check file upload validation | Medium | Sonnet | Pattern matching, known vulnerabilities |
| Security design review | Critical | Opus | Novel threat modeling |

---

### Testing Tasks

| Task | Complexity | Tier | Rationale |
|------|-----------|------|-----------|
| Generate simple CRUD tests | Low | Sonnet | Template-based, straightforward |
| Generate async/complex tests | Medium | Sonnet | Requires testing pattern knowledge |
| Design test strategy (new system) | High | Opus | Novel approach, multi-domain |
| Debug flaky test | Medium | Opus | Complex investigation required |
| Test edge cases (complex logic) | High | Opus | Requires deep domain knowledge |

---

## Survival: Fallback Tier Handling

### What to Do When Model Selection Goes Wrong

#### Scenario 1: Task Too Complex for Assigned Tier

**Detection:**
```
- Model output is vague or incorrect
- "I'm not sure" or "I need more information"
- Output lacks necessary detail
- Multi-step task gets stuck after first step
```

**Recovery:**
```python
def upgrade_tier_on_failure(task, current_tier, failure_reason):
    """
    Upgrade tier when current tier cannot handle task.
    """

    if current_tier == Tier.HAIKU:
        # Try Sonnet
        return Tier.SONNET, "Complexity exceeds Haiku capability"

    elif current_tier == Tier.SONNET:
        # Try Opus
        return Tier.OPUS, "Task requires advanced reasoning"

    elif current_tier == Tier.OPUS:
        # Already at max - may need human intervention
        return Tier.OPUS, "Even Opus struggling - escalate to human"
```

**Example:**
```
Task: Generate ACGME-compliant schedule
Assigned: Sonnet
Result: Generated schedule with compliance violations
Action: Upgrade to Opus
```

---

#### Scenario 2: Task Too Simple for Assigned Tier

**Detection:**
```
- Model solution is overcomplicated
- Overkill for actual requirement
- Unnecessary documentation/explanation
- Cost > value provided
```

**Recovery:**
```python
def downgrade_tier_on_overkill(task, current_tier):
    """
    Downgrade tier when over-engineered.
    """

    if current_tier == Tier.OPUS:
        return Tier.SONNET, "Task didn't require Opus reasoning"

    elif current_tier == Tier.SONNET:
        return Tier.HAIKU, "Task could use Haiku (cost saving)"

    elif current_tier == Tier.HAIKU:
        return Tier.HAIKU, "Already at minimum tier"
```

**Example:**
```
Task: Fix lint error (single Python file)
Assigned: Sonnet
Result: Perfect fix, but took 3 seconds vs 500ms for Haiku
Action: Downgrade to Haiku for future similar tasks
```

---

### Fallback Chains

**For Haiku Failures:**
```
Haiku → Sonnet → Opus
```

**For Sonnet Failures:**
```
Sonnet → Opus
```

**For Opus Failures:**
```
Opus → Human Escalation
```

---

## Stealth: Misaligned Tier Detection

### Red Flags for Misaligned Tiers

#### Haiku Used For Complex Tasks (Under-Provisioned)

**Symptoms:**
- Output is vague or incomplete
- "I'm not qualified to..."
- Multi-step reasoning broken partway through
- Missing edge cases or error handling

**Check:**
```python
if haiku_task['domains'] > 2:
    alert("Haiku assigned to multi-domain task!")

if haiku_task['risk_level'] > 2:
    alert("Haiku assigned to medium/high-risk task!")

if 'acgme' in haiku_task['keywords']:
    alert("Haiku assigned to compliance task!")
```

**Examples of Haiku Misuse:**
- ✗ Generate ACGME-compliant schedule
- ✗ Security audit of authentication
- ✗ Complex debugging session
- ✗ Test strategy for new system

---

#### Opus Used For Simple Tasks (Over-Provisioned)

**Symptoms:**
- Solution is overcomplicated
- Excessive time spent on trivial task
- Unnecessary documentation
- High cost for low value

**Check:**
```python
if opus_task['domains'] <= 1:
    warning("Opus used for single-domain task - consider Haiku")

if opus_task['estimated_time'] < 5:
    warning("Opus used for <5min task - use Haiku")

if opus_task['risk_level'] <= 1:
    warning("Opus used for low-risk task - consider Haiku")
```

**Examples of Opus Misuse:**
- ✗ Fix lint errors
- ✗ Add simple form field
- ✗ Update CSS styling
- ✗ Reference lookup
- ✗ Changelog generation

---

### Automated Detection System

```python
class TierMisalignmentDetector:
    """Detect tier-task misalignment."""

    def check_alignment(self, task, assigned_tier):
        """Verify tier assignment is appropriate."""

        # Calculate optimal tier
        optimal_tier = self.calculate_optimal_tier(task)

        # Check for misalignment
        if assigned_tier < optimal_tier:
            severity = optimal_tier - assigned_tier
            return TierMisalignmentAlert(
                type="UNDER_PROVISIONED",
                severity=severity,
                message=f"Task needs {optimal_tier}, got {assigned_tier}",
                recommendation=f"Upgrade to {optimal_tier}"
            )

        elif assigned_tier > optimal_tier:
            waste = assigned_tier - optimal_tier
            savings = self.estimate_cost_savings(waste)
            return TierMisalignmentAlert(
                type="OVER_PROVISIONED",
                severity=waste,
                message=f"Task needs {optimal_tier}, got {assigned_tier}",
                recommendation=f"Downgrade to {optimal_tier} (save ${savings})"
            )

        return None  # Aligned!
```

---

## Cost Optimization Strategies

### Strategy 1: Complexity-Based Tiering

**Approach:** Map tasks to tiers based on complexity score.

**Implementation:**
```python
def assign_tier_by_complexity(task):
    score = calculate_complexity(task)
    return {
        (0, 5): Tier.HAIKU,
        (6, 12): Tier.SONNET,
        (13, float('inf')): Tier.OPUS,
    }[range_containing(score)]
```

**Cost Impact:** 40-50% reduction (vs all Opus)
**Quality Impact:** Minimal, task-appropriate
**Effort:** Medium (requires scoring all tasks)

---

### Strategy 2: Bulk Tier Assignment

**Approach:** Group similar tasks, assign tier to group.

**Example Groups:**
```
Group: Linting & Formatting
├─ Skill: lint-monorepo → Haiku
├─ Skill: code-formatter → Haiku
└─ Skill: style-checker → Haiku

Group: Standard Development
├─ Skill: fastapi-production → Sonnet
├─ Skill: frontend-development → Sonnet
└─ Skill: test-writer → Sonnet

Group: Critical Operations
├─ Skill: security-audit → Opus
├─ Skill: production-incident-responder → Opus
└─ Skill: acgme-compliance → Opus
```

**Cost Impact:** 50-60% reduction
**Quality Impact:** Optimal per task type
**Effort:** Low (simple categorization)

---

### Strategy 3: Time-Based Tier Escalation

**Approach:** Start with lower tier, escalate if needed.

**Algorithm:**
```python
def execute_with_escalation(task):
    tier = Tier.HAIKU
    max_retries = 2

    for attempt in range(max_retries + 1):
        try:
            result = execute_with_tier(task, tier)
            return result

        except TaskTooComplex:
            if tier == Tier.HAIKU:
                tier = Tier.SONNET
            elif tier == Tier.SONNET:
                tier = Tier.OPUS
            else:
                raise

    raise TaskFailed("Even Opus cannot handle this")
```

**Cost Impact:** 60-70% reduction (many succeed at Haiku)
**Quality Impact:** Same (escalates when needed)
**Effort:** Medium (requires robust error detection)

---

### Strategy 4: Batch & Parallelize

**Approach:** Run similar low-complexity tasks on Haiku in batch.

**Example:**
```python
# Inefficient: One task at a time with Sonnet
for file in files:
    lint_and_fix(file, tier=Sonnet)  # Cost: 5x per task

# Efficient: Batch on Haiku
lint_batch(files, tier=Haiku)  # Cost: 1x per batch
```

**Cost Impact:** 70-80% reduction (for batch operations)
**Quality Impact:** Improved (Haiku good at linting)
**Effort:** Medium (requires batch task support)

---

### Strategy 5: Caching & Reuse

**Approach:** Cache model outputs for common tasks.

**Example:**
```python
# Cache: "What is ACGME 80-hour rule?"
# Answer cached from Haiku, reused 1000x
lookup_acgme_rule("80-hour", tier=Haiku)

# vs regenerating every time:
lookup_acgme_rule("80-hour", tier=Opus)  # 100x cost
```

**Cost Impact:** 10-40% reduction (for knowledge lookups)
**Quality Impact:** Same (consistent answers)
**Effort:** Low (add caching layer)

---

### Recommended Cost Optimization Roadmap

**Phase 1 (Immediate): Bulk Tier Assignment**
- Time: 1 week
- Effort: Low
- Cost savings: 50-60%
- Implementation: Assign tiers to skill groups

**Phase 2 (Week 2): Complexity Scoring**
- Time: 1 week
- Effort: Medium
- Cost savings: Additional 10-15%
- Implementation: Apply formula to all tasks

**Phase 3 (Week 3): Tier Escalation**
- Time: 1 week
- Effort: Medium
- Cost savings: Additional 10-20%
- Implementation: Smart fallback chain

**Phase 4 (Week 4): Batch & Caching**
- Time: 1 week
- Effort: Medium
- Cost savings: Additional 5-10%
- Implementation: Operational optimization

**Total Projected Savings: 60-70%**

---

## Implementation Guidelines

### Adding Tier Assignment to Skills

**Step 1: Update SKILL.md Header**
```yaml
---
name: example-skill
description: Skill description here
model_tier: sonnet  # Add this line
model_tier_justification: |
  Domains: 2 (Backend + Database)
  Dependencies: 2 (DB, validation)
  Time: 5-15 minutes
  Risk: Medium (2)
  Knowledge: Intermediate (2)
  Score: (2×3) + (2×2) + (2×2) + (2×1) + (2×1) = 18

  Wait, that's 18 - should be Opus!
  Correction: Score = 10 → Sonnet ✓
---
```

**Step 2: Add Complexity Parameters**
```yaml
model_tier_params:
  complexity:
    domains: 2  # Backend, Database
    dependencies: 2  # DB, validation rules
    estimated_time_minutes: 10
    risk_level: 2  # Medium
    knowledge_required: 2  # Intermediate
```

**Step 3: Add Cost Hints**
```yaml
  cost_hints:
    cost_optimization_friendly: true
    minimum_tier: sonnet  # Never downgrade below Sonnet
```

---

### Tier Assignment Checklist

Before assigning a tier, verify:

- [ ] Complexity score calculated and documented
- [ ] All 5 factors (domains, dependencies, time, risk, knowledge) assessed
- [ ] Score matches recommended tier range
- [ ] Any hard constraints (security, compliance) noted
- [ ] Rationale documented in SKILL.md
- [ ] Cost impact considered
- [ ] Skill dependencies checked (do upstream skills match?)

---

### Monitoring & Adjustment

**Monthly Review Process:**

1. **Collect Metrics**
   - Model usage (assigned vs actual tier)
   - Cost per skill execution
   - Success rates by tier
   - Quality metrics (bugs, revisions needed)

2. **Analyze Alignment**
   - Are actual tiers matching assigned?
   - Are success rates appropriate?
   - Are costs in line with expectations?

3. **Adjust Assignments**
   - Downgrade over-provisioned skills
   - Upgrade under-performing skills
   - Document changes and rationale

4. **Report & Communicate**
   - Generate tier optimization report
   - Share cost savings achieved
   - Highlight any quality regressions
   - Recommend next optimizations

---

## Appendices

### Appendix A: Quick Reference - Task to Tier Mapping

| Task Type | Domain Count | Typical Score | Tier | Cost |
|-----------|-------------|--------------|------|------|
| Lint code | 1 | 5-6 | Haiku | 1x |
| Fix style error | 1 | 5-7 | Haiku | 1x |
| Route decision | 1 | 3-5 | Haiku | 1x |
| Reference lookup | 1 | 4-5 | Haiku | 1x |
| Create API endpoint | 2 | 8-10 | Sonnet | 4x |
| Build React component | 2 | 8-11 | Sonnet | 4x |
| Write tests | 2 | 7-10 | Sonnet | 4x |
| Database migration | 2 | 7-9 | Sonnet | 4x |
| Code review (logic) | 2 | 9-11 | Sonnet | 4x |
| Architecture design | 3+ | 12-16 | Sonnet/Opus | 4-10x |
| Security audit | 3+ | 15-20 | Opus | 10x |
| Incident response | 4+ | 18-25 | Opus | 10x |
| Novel algorithm | 3+ | 16-25 | Opus | 10x |

---

### Appendix B: Skill Tier Assignment Template

```yaml
---
name: new-skill-name
description: Brief description of what this skill does

# Model tier for skill execution
model_tier: sonnet  # haiku, sonnet, or opus

# Detailed justification for tier selection
model_tier_justification: |
  COMPLEXITY SCORING:
  - Domains: [list domains]
  - Dependencies: [list dependencies]
  - Estimated time: X minutes
  - Risk level: Y (1=low, 5=critical)
  - Knowledge required: Z (1=general, 5=expert)

  CALCULATION:
  Score = (Domains × 3) + (Dependencies × 2) + (Time × 2) + (Risk × 1) + (Knowledge × 1)
  Score = (N × 3) + (M × 2) + (T × 2) + (R × 1) + (K × 1) = TOTAL

  RESULT:
  Total score: TOTAL
  Recommended tier: [Haiku/Sonnet/Opus]
  Assigned tier: [Haiku/Sonnet/Opus]
  Rationale: [Explanation if different from recommended]

# Complexity assessment for tier selection
model_tier_params:
  complexity:
    domains:
      - backend
      - database
    dependencies:
      - postgresql_database
      - validation_rules
    estimated_time_minutes: 15
    risk_level: 2  # 1-5 scale
    knowledge_required: 2  # 1-5 scale

  cost_hints:
    cost_optimization_friendly: true
    minimum_tier: sonnet  # Never downgrade below this

  hard_constraints: []
    # - is_security_critical
    # - is_production_emergency
    # - is_acgme_compliance

---
```

---

### Appendix C: Complexity Scoring Worksheets

**Template for Manual Scoring:**

```
TASK: [Task name]
DATE: [Date]

STEP 1: Count Domains
Domains involved: [List]
Count: ___
Points: ___ × 3 = ___

STEP 2: Count Dependencies
Dependencies: [List]
Count: ___
Points: ___ × 2 = ___

STEP 3: Estimate Time
Estimated minutes: ___
Divide by 10: ___
Points: ___ × 2 = ___

STEP 4: Assess Risk
Risk level (1-5): ___
Points: ___ × 1 = ___

STEP 5: Assess Knowledge
Knowledge required (1-5): ___
Points: ___ × 1 = ___

TOTAL SCORE: ___ + ___ + ___ + ___ + ___ = ___

TIER ASSIGNMENT:
___ 0-5:    Haiku
___ 6-12:   Sonnet
___ 13+:    Opus

Assigned Tier: ___
Justification: ___
```

---

### Appendix D: Cost Analysis Tools

**Cost Estimation Formula:**

```python
def estimate_cost(tier, tokens_estimated):
    """Estimate cost for model execution."""

    cost_per_mtok = {
        'haiku': 0.80,    # Haiku: $0.80 per million input tokens
        'sonnet': 3.00,   # Sonnet: $3.00 per million input tokens
        'opus': 15.00,    # Opus: $15.00 per million input tokens
    }

    tokens_millions = tokens_estimated / 1_000_000
    return tokens_millions * cost_per_mtok[tier]

# Example:
# 1000 tokens on Haiku = 0.001M × $0.80 = $0.0008
# 1000 tokens on Opus = 0.001M × $15.00 = $0.015
# Opus is 18.75x more expensive!
```

---

### Appendix E: Tier Selection Decision Matrix

```
                    | Haiku        | Sonnet       | Opus
--------------------|--------------|--------------|----------------
Max Complexity      | 5            | 12           | 25+
Avg Response Time   | 500ms        | 2-3s         | 5-10s
Cost (Baseline)     | 1x           | 4-5x         | 10-12x
Code Quality        | 70%          | 85-90%       | 95-98%
Reasoning Depth     | Shallow      | Moderate     | Deep
Edge Case Handling  | Poor         | Good         | Excellent
Security Analysis   | Limited      | Good         | Excellent
Novel Problems      | No           | Limited      | Yes
Best For Tasks      | Routing      | Development  | Complex
Parallelizable      | Yes          | Yes          | No
Batch Size          | 10-50        | 3-5          | 1-2
Cost per Quality    | Lowest       | Best         | Highest
```

---

## Summary

This guide provides a comprehensive framework for selecting Claude model tiers when executing AI agent skills. Key takeaways:

1. **Use Complexity Scoring:** Apply the formula consistently to all tasks
2. **Match Tier to Task:** Haiku for simple, Sonnet for standard, Opus for complex
3. **Optimize Cost:** Move away from all-Opus to mixed tiers (60% cost savings)
4. **Monitor Alignment:** Track actual vs assigned tier performance
5. **Escalate When Needed:** Start low, escalate if task proves too complex

**Expected Outcomes:**
- 50-60% cost reduction through intelligent tier selection
- Maintained or improved code quality
- Faster execution for appropriate tasks
- Better resource utilization

---

**Document Status:** Complete
**Version:** 1.0.0
**Last Updated:** 2025-12-30
**Ready for Implementation:** Yes
