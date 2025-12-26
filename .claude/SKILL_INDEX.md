# SKILL INDEX - Personal AI Infrastructure Metadata & Routing

> **Purpose:** Complete skill registry, routing logic, and discovery layer for the PAI
> **Version:** 1.0.0
> **Last Updated:** 2025-12-26
> **Total Skills:** 34

---

## Table of Contents

1. [Complete Skill Registry](#complete-skill-registry)
2. [Routing Rules](#routing-rules)
3. [Agent-Skill Matrix](#agent-skill-matrix)
4. [Skill Dependencies](#skill-dependencies)
5. [Tags Taxonomy](#tags-taxonomy)
6. [Discovery Queries](#discovery-queries)
7. [Quick Reference](#quick-reference)

---

## Complete Skill Registry

### Tier 1: Core Scheduling Skills (Kai Pattern)

#### SCHEDULING
```yaml
name: SCHEDULING
path: .claude/skills/SCHEDULING/
domain: residency/scheduling
tags: [core, generation, constraints, ACGME, optimization]
difficulty: advanced
pattern: kai
agents: [SCHEDULER, ARCHITECT, ORCHESTRATOR]
tools: [generate_schedule, validate_schedule, detect_conflicts]
inputs: [date_range, residents, rotations, constraints, preferences]
outputs: [schedule_json, compliance_report, metrics, alternatives]
dependencies: [COMPLIANCE_VALIDATION, safe-schedule-generation]
estimated_duration: 2-10 minutes
safety_critical: true
```

**When to Use:**
- Generating new academic year or block schedules
- Optimizing existing schedules for coverage/fairness
- Resolving systemic scheduling conflicts
- Training on scheduling system workflow

**Intent Mappings:**
- "generate schedule" → SCHEDULING
- "optimize schedule" → SCHEDULING
- "balance workload" → SCHEDULING
- "improve coverage" → SCHEDULING

---

#### COMPLIANCE_VALIDATION
```yaml
name: COMPLIANCE_VALIDATION
path: .claude/skills/COMPLIANCE_VALIDATION/
domain: residency/compliance
tags: [core, validation, ACGME, regulatory, audit]
difficulty: intermediate
pattern: kai
agents: [COMPLIANCE_AUDITOR, SCHEDULER, VALIDATOR]
tools: [validate_acgme_compliance, get_compliance_summary]
inputs: [schedule_id, date_range, audit_type]
outputs: [compliance_report, violations, remediation_plan, metrics]
dependencies: []
estimated_duration: 30-90 seconds
safety_critical: true
```

**When to Use:**
- Pre-deployment schedule validation
- Monthly/quarterly ACGME audits
- Post-swap compliance checking
- Historical trend analysis

**Intent Mappings:**
- "validate compliance" → COMPLIANCE_VALIDATION
- "check ACGME" → COMPLIANCE_VALIDATION
- "audit schedule" → COMPLIANCE_VALIDATION
- "find violations" → COMPLIANCE_VALIDATION

---

#### RESILIENCE_SCORING
```yaml
name: RESILIENCE_SCORING
path: .claude/skills/RESILIENCE_SCORING/
domain: resilience/analytics
tags: [core, analysis, n-1, contingency, health]
difficulty: advanced
pattern: kai
agents: [RESILIENCE_ENGINEER, ANALYST]
tools: [get_schedule_health, run_contingency_analysis_resilience_tool]
inputs: [schedule_id, failure_scenarios, simulation_params]
outputs: [health_score, critical_residents, fragile_rotations, recovery_plan]
dependencies: []
estimated_duration: 1-5 minutes
safety_critical: false
```

**When to Use:**
- Evaluating schedule before deployment
- Monthly resilience health checks
- N-1/N-2 failure simulation
- Identifying critical personnel

**Intent Mappings:**
- "check resilience" → RESILIENCE_SCORING
- "what if resident absent" → RESILIENCE_SCORING
- "n-1 analysis" → RESILIENCE_SCORING
- "schedule health" → RESILIENCE_SCORING

---

#### SWAP_EXECUTION
```yaml
name: SWAP_EXECUTION
path: .claude/skills/SWAP_EXECUTION/
domain: residency/operations
tags: [core, execution, swaps, validation, rollback]
difficulty: intermediate
pattern: kai
agents: [SWAP_COORDINATOR, VALIDATOR]
tools: [execute_swap, analyze_swap_candidates, validate_swap_compliance]
inputs: [swap_request, requester_id, target_id, reason]
outputs: [swap_record, validation_result, audit_trail]
dependencies: [COMPLIANCE_VALIDATION, RESILIENCE_SCORING]
estimated_duration: 10-30 seconds
safety_critical: true
```

**When to Use:**
- Processing faculty/resident swap requests
- Validating swap feasibility
- Executing validated swaps
- Rolling back problematic swaps

**Intent Mappings:**
- "execute swap" → SWAP_EXECUTION
- "process swap request" → SWAP_EXECUTION
- "rollback swap" → SWAP_EXECUTION
- "validate swap" → SWAP_EXECUTION

---

#### MCP_ORCHESTRATION
```yaml
name: MCP_ORCHESTRATION
path: .claude/skills/MCP_ORCHESTRATION/
domain: meta/orchestration
tags: [meta, orchestration, tools, composition, error-handling]
difficulty: advanced
pattern: kai
agents: [ORCHESTRATOR, TOOL_ROUTER]
tools: [ALL_36_MCP_TOOLS]
inputs: [workflow_definition, tool_chain, parameters]
outputs: [execution_plan, results, performance_metrics]
dependencies: []
estimated_duration: varies
safety_critical: false
```

**When to Use:**
- Multi-tool workflows (2+ MCP tools)
- Complex scheduling operations
- Error recovery from failed MCP calls
- Performance optimization of tool chains

**Intent Mappings:**
- "orchestrate tools" → MCP_ORCHESTRATION
- "chain MCP tools" → MCP_ORCHESTRATION
- "handle MCP error" → MCP_ORCHESTRATION
- "discover tools" → MCP_ORCHESTRATION

---

#### ORCHESTRATION_DEBUGGING
```yaml
name: ORCHESTRATION_DEBUGGING
path: .claude/skills/ORCHESTRATION_DEBUGGING/
domain: meta/debugging
tags: [meta, debugging, troubleshooting, incident, diagnosis]
difficulty: advanced
pattern: kai
agents: [DEBUGGER, INCIDENT_RESPONDER]
tools: [celery_task_status, check_background_tasks]
inputs: [error_report, symptoms, system_state]
outputs: [root_cause, fix_recommendations, incident_report]
dependencies: [MCP_ORCHESTRATION, systematic-debugger]
estimated_duration: 5-30 minutes
safety_critical: false
```

**When to Use:**
- MCP tool failures
- Agent communication breakdowns
- Constraint engine errors
- Database operation timeouts

**Intent Mappings:**
- "debug MCP failure" → ORCHESTRATION_DEBUGGING
- "tool not responding" → ORCHESTRATION_DEBUGGING
- "agent error" → ORCHESTRATION_DEBUGGING
- "investigate timeout" → ORCHESTRATION_DEBUGGING

---

#### CORE
```yaml
name: CORE
path: .claude/skills/CORE/
domain: meta/routing
tags: [meta, registry, routing, delegation, coordination]
difficulty: foundational
pattern: kai
agents: [ORCHESTRATOR, ALL_AGENTS]
tools: []
inputs: [task_description, context]
outputs: [skill_selection, routing_decision, delegation_plan]
dependencies: []
estimated_duration: < 1 second
safety_critical: false
```

**When to Use:**
- Automatic skill routing
- Agent delegation decisions
- Skill discovery
- Progressive disclosure

**Intent Mappings:**
- N/A (invoked automatically by all agents)

---

### Tier 2: Domain-Specific Skills (Legacy Pattern)

#### acgme-compliance
```yaml
name: acgme-compliance
path: .claude/skills/acgme-compliance/
domain: residency/compliance
tags: [compliance, ACGME, reference, knowledge]
difficulty: beginner
pattern: legacy
agents: [COMPLIANCE_AUDITOR, SCHEDULER]
tools: [validate_acgme_compliance]
inputs: [schedule_id, question]
outputs: [answer, rules_reference, validation_result]
dependencies: []
estimated_duration: 10-30 seconds
safety_critical: false
```

**When to Use:**
- Answering ACGME questions (reference knowledge)
- Quick compliance checks
- Understanding ACGME rules

**Difference from COMPLIANCE_VALIDATION:** This skill provides reference knowledge and simple checks. Use COMPLIANCE_VALIDATION for systematic audits and remediation workflows.

---

#### schedule-optimization
```yaml
name: schedule-optimization
path: .claude/skills/schedule-optimization/
domain: residency/scheduling
tags: [scheduling, optimization, solvers, constraints]
difficulty: advanced
pattern: legacy
agents: [SCHEDULER, ARCHITECT]
tools: [generate_schedule, benchmark_solvers]
inputs: [constraints, objectives, solver_params]
outputs: [optimized_schedule, pareto_frontier, solver_metrics]
dependencies: [acgme-compliance]
estimated_duration: 2-10 minutes
safety_critical: true
```

**When to Use:**
- Deep dive into solver algorithms (CP-SAT, PuLP, greedy)
- Pareto optimization for competing objectives
- Solver benchmarking

**Difference from SCHEDULING:** This skill focuses on solver algorithms. Use SCHEDULING for the complete end-to-end workflow.

---

#### swap-management
```yaml
name: swap-management
path: .claude/skills/swap-management/
domain: residency/operations
tags: [swaps, matching, workflow]
difficulty: intermediate
pattern: legacy
agents: [SWAP_COORDINATOR]
tools: [analyze_swap_candidates, get_swap_auto_match]
inputs: [requester_id, assignment_id]
outputs: [candidates, compatibility_scores, recommendations]
dependencies: [acgme-compliance]
estimated_duration: 10-30 seconds
safety_critical: false
```

**When to Use:**
- Finding swap candidates (matching algorithm)
- Understanding swap workflows

**Difference from SWAP_EXECUTION:** This skill focuses on matching/discovery. Use SWAP_EXECUTION for the complete lifecycle including validation and execution.

---

#### safe-schedule-generation
```yaml
name: safe-schedule-generation
path: .claude/skills/safe-schedule-generation/
domain: operations/safety
tags: [safety, backup, deployment, database]
difficulty: intermediate
pattern: legacy
agents: [DEPLOYMENT_MANAGER, SCHEDULER]
tools: []
inputs: [schedule_id, write_operation]
outputs: [backup_confirmation, deployment_status]
dependencies: [database-migration]
estimated_duration: 1-2 minutes
safety_critical: true
```

**When to Use:**
- Before ANY database write to assignment tables
- Schedule deployment
- Backup/rollback procedures

---

#### schedule-verification
```yaml
name: schedule-verification
path: .claude/skills/schedule-verification/
domain: residency/operations
tags: [verification, checklist, human-review]
difficulty: beginner
pattern: legacy
agents: [REVIEWER, COORDINATOR]
tools: []
inputs: [schedule_id, block_number]
outputs: [verification_checklist, issues_found, approval_status]
dependencies: [acgme-compliance]
estimated_duration: 5-10 minutes (human)
safety_critical: false
```

**When to Use:**
- Human review of generated schedules
- Sanity checking solver output
- Block 10 or other critical schedule review

---

### Tier 3: Development & Code Quality Skills

#### test-writer
```yaml
name: test-writer
path: .claude/skills/test-writer/
domain: development/testing
tags: [testing, pytest, jest, coverage]
difficulty: intermediate
pattern: legacy
agents: [TEST_ENGINEER, DEVELOPER]
tools: []
inputs: [code_file, coverage_gaps, test_type]
outputs: [test_files, coverage_report]
dependencies: []
estimated_duration: 2-5 minutes
safety_critical: false
```

**Intent Mappings:**
- "write tests" → test-writer
- "improve coverage" → test-writer
- "create fixtures" → test-writer

---

#### code-review
```yaml
name: code-review
path: .claude/skills/code-review/
domain: development/quality
tags: [review, quality, security, best-practices]
difficulty: intermediate
pattern: legacy
agents: [REVIEWER, ARCHITECT]
tools: []
inputs: [changed_files, pr_context]
outputs: [review_comments, security_issues, recommendations]
dependencies: [security-audit]
estimated_duration: 3-10 minutes
safety_critical: false
```

**Intent Mappings:**
- "review code" → code-review
- "check for bugs" → code-review
- "code quality" → code-review

---

#### automated-code-fixer
```yaml
name: automated-code-fixer
path: .claude/skills/automated-code-fixer/
domain: development/automation
tags: [automation, fixing, linting, type-checking]
difficulty: intermediate
pattern: legacy
agents: [FIXER, DEVELOPER]
tools: []
inputs: [failing_tests, lint_errors, type_errors]
outputs: [fixed_code, test_results, quality_gates]
dependencies: [lint-monorepo, test-writer]
estimated_duration: 1-5 minutes
safety_critical: false
```

**Intent Mappings:**
- "fix tests" → automated-code-fixer
- "fix lint errors" → automated-code-fixer
- "resolve type errors" → automated-code-fixer

---

#### code-quality-monitor
```yaml
name: code-quality-monitor
path: .claude/skills/code-quality-monitor/
domain: development/quality
tags: [quality, monitoring, gates, enforcement]
difficulty: beginner
pattern: legacy
agents: [QUALITY_GATE, REVIEWER]
tools: []
inputs: [pr_number, changed_files]
outputs: [quality_report, gate_status, metrics]
dependencies: [code-review, automated-code-fixer]
estimated_duration: 1-3 minutes
safety_critical: false
```

**Intent Mappings:**
- "check quality" → code-quality-monitor
- "enforce standards" → code-quality-monitor
- "quality gates" → code-quality-monitor

---

#### lint-monorepo
```yaml
name: lint-monorepo
path: .claude/skills/lint-monorepo/
domain: development/tooling
tags: [linting, ruff, eslint, auto-fix]
difficulty: beginner
pattern: legacy
agents: [LINTER, FIXER]
tools: []
inputs: [file_paths, auto_fix_flag]
outputs: [lint_results, fixed_files]
dependencies: []
estimated_duration: 30-90 seconds
safety_critical: false
```

**Intent Mappings:**
- "lint code" → lint-monorepo
- "fix style" → lint-monorepo
- "run ruff" → lint-monorepo

---

#### systematic-debugger
```yaml
name: systematic-debugger
path: .claude/skills/systematic-debugger/
domain: development/debugging
tags: [debugging, troubleshooting, tdd, root-cause]
difficulty: advanced
pattern: legacy
agents: [DEBUGGER, DEVELOPER]
tools: []
inputs: [bug_report, symptoms, error_logs]
outputs: [root_cause, fix_plan, regression_tests]
dependencies: [test-writer, code-review]
estimated_duration: 10-60 minutes
safety_critical: false
```

**Intent Mappings:**
- "debug issue" → systematic-debugger
- "investigate bug" → systematic-debugger
- "root cause analysis" → systematic-debugger

---

#### constraint-preflight
```yaml
name: constraint-preflight
path: .claude/skills/constraint-preflight/
domain: residency/development
tags: [constraints, validation, testing, registration]
difficulty: intermediate
pattern: legacy
agents: [SCHEDULER, DEVELOPER]
tools: []
inputs: [constraint_file, constraint_name]
outputs: [preflight_report, registration_status, test_coverage]
dependencies: [test-writer, schedule-optimization]
estimated_duration: 2-5 minutes
safety_critical: true
```

**Intent Mappings:**
- "add constraint" → constraint-preflight
- "verify constraint registered" → constraint-preflight
- "test new constraint" → constraint-preflight

---

#### solver-control
```yaml
name: solver-control
path: .claude/skills/solver-control/
domain: residency/operations
tags: [solver, control, timeout, monitoring]
difficulty: intermediate
pattern: legacy
agents: [SCHEDULER, CONTROLLER]
tools: [celery_task_cancel]
inputs: [solver_task_id, timeout_seconds]
outputs: [solver_status, abort_confirmation]
dependencies: [schedule-optimization]
estimated_duration: 1-10 seconds
safety_critical: false
```

**Intent Mappings:**
- "abort solver" → solver-control
- "monitor generation" → solver-control
- "kill schedule job" → solver-control

---

### Tier 4: Infrastructure & Operations Skills

#### database-migration
```yaml
name: database-migration
path: .claude/skills/database-migration/
domain: infrastructure/database
tags: [database, migration, alembic, schema]
difficulty: intermediate
pattern: legacy
agents: [DBA, DEVELOPER]
tools: []
inputs: [model_changes, migration_message]
outputs: [migration_file, rollback_plan, data_integrity_checks]
dependencies: []
estimated_duration: 2-5 minutes
safety_critical: true
```

**Intent Mappings:**
- "create migration" → database-migration
- "modify schema" → database-migration
- "rollback database" → database-migration

---

#### docker-containerization
```yaml
name: docker-containerization
path: .claude/skills/docker-containerization/
domain: infrastructure/containers
tags: [docker, containers, orchestration, deployment]
difficulty: intermediate
pattern: legacy
agents: [DEVOPS, DEVELOPER]
tools: []
inputs: [dockerfile, docker_compose_config]
outputs: [optimized_config, build_instructions, security_scan]
dependencies: []
estimated_duration: 5-15 minutes
safety_critical: false
```

**Intent Mappings:**
- "optimize dockerfile" → docker-containerization
- "fix container" → docker-containerization
- "docker-compose" → docker-containerization

---

#### fastapi-production
```yaml
name: fastapi-production
path: .claude/skills/fastapi-production/
domain: development/backend
tags: [fastapi, async, api, sqlalchemy, pydantic]
difficulty: intermediate
pattern: legacy
agents: [BACKEND_DEVELOPER, ARCHITECT]
tools: []
inputs: [endpoint_spec, route_requirements]
outputs: [route_code, schema_code, tests]
dependencies: [database-migration, test-writer]
estimated_duration: 5-15 minutes
safety_critical: false
```

**Intent Mappings:**
- "create api endpoint" → fastapi-production
- "fastapi route" → fastapi-production
- "async database operation" → fastapi-production

---

#### frontend-development
```yaml
name: frontend-development
path: .claude/skills/frontend-development/
domain: development/frontend
tags: [nextjs, react, tailwind, tanstack-query]
difficulty: intermediate
pattern: legacy
agents: [FRONTEND_DEVELOPER, DESIGNER]
tools: []
inputs: [component_spec, page_requirements]
outputs: [component_code, page_code, tests]
dependencies: [react-typescript, test-writer]
estimated_duration: 10-30 minutes
safety_critical: false
```

**Intent Mappings:**
- "create component" → frontend-development
- "build page" → frontend-development
- "nextjs app router" → frontend-development

---

#### react-typescript
```yaml
name: react-typescript
path: .claude/skills/react-typescript/
domain: development/frontend
tags: [typescript, react, types, patterns]
difficulty: intermediate
pattern: legacy
agents: [FRONTEND_DEVELOPER, TYPE_CHECKER]
tools: []
inputs: [component_file, type_errors]
outputs: [fixed_code, type_definitions]
dependencies: []
estimated_duration: 2-10 minutes
safety_critical: false
```

**Intent Mappings:**
- "fix typescript" → react-typescript
- "type react component" → react-typescript
- "generic hooks" → react-typescript

---

#### python-testing-patterns
```yaml
name: python-testing-patterns
path: .claude/skills/python-testing-patterns/
domain: development/testing
tags: [pytest, async, fixtures, mocking]
difficulty: advanced
pattern: legacy
agents: [TEST_ENGINEER, DEVELOPER]
tools: []
inputs: [test_requirements, async_code]
outputs: [test_code, fixtures, mocking_strategy]
dependencies: [test-writer]
estimated_duration: 5-15 minutes
safety_critical: false
```

**Intent Mappings:**
- "async tests" → python-testing-patterns
- "complex fixtures" → python-testing-patterns
- "mock strategy" → python-testing-patterns

---

### Tier 5: Workflow & Process Skills

#### pr-reviewer
```yaml
name: pr-reviewer
path: .claude/skills/pr-reviewer/
domain: workflow/git
tags: [pr, review, github, quality-gates]
difficulty: intermediate
pattern: legacy
agents: [REVIEWER, QUALITY_GATE]
tools: []
inputs: [pr_number, changed_files]
outputs: [review_comments, approval_status, pr_description]
dependencies: [code-review, code-quality-monitor]
estimated_duration: 5-15 minutes
safety_critical: false
```

**Intent Mappings:**
- "review pr" → pr-reviewer
- "check pull request" → pr-reviewer
- "generate pr description" → pr-reviewer

---

#### changelog-generator
```yaml
name: changelog-generator
path: .claude/skills/changelog-generator/
domain: workflow/documentation
tags: [changelog, release, documentation]
difficulty: beginner
pattern: legacy
agents: [RELEASE_MANAGER, DEVELOPER]
tools: []
inputs: [git_range, release_version]
outputs: [changelog_markdown, release_notes]
dependencies: []
estimated_duration: 2-5 minutes
safety_critical: false
```

**Intent Mappings:**
- "generate changelog" → changelog-generator
- "release notes" → changelog-generator
- "document changes" → changelog-generator

---

#### session-documentation
```yaml
name: session-documentation
path: .claude/skills/session-documentation/
domain: workflow/documentation
tags: [documentation, session, knowledge-capture]
difficulty: beginner
pattern: legacy
agents: [DOCUMENTER, KNOWLEDGE_KEEPER]
tools: []
inputs: [session_context, decisions_made]
outputs: [session_summary, knowledge_artifacts]
dependencies: []
estimated_duration: 5-10 minutes
safety_critical: false
```

**Intent Mappings:**
- "document session" → session-documentation
- "capture decisions" → session-documentation
- "summarize work" → session-documentation

---

### Tier 6: Emergency & Incident Response Skills

#### production-incident-responder
```yaml
name: production-incident-responder
path: .claude/skills/production-incident-responder/
domain: operations/incident
tags: [incident, emergency, crisis, production]
difficulty: advanced
pattern: legacy
agents: [INCIDENT_RESPONDER, ON_CALL]
tools: [check_resilience_health, run_contingency_analysis_resilience_tool]
inputs: [incident_report, symptoms]
outputs: [diagnosis, mitigation_plan, recovery_steps]
dependencies: [systematic-debugger, safe-schedule-generation]
estimated_duration: 10-60 minutes
safety_critical: true
```

**Intent Mappings:**
- "production down" → production-incident-responder
- "emergency response" → production-incident-responder
- "system failure" → production-incident-responder

---

### Tier 7: Security & Compliance Skills

#### security-audit
```yaml
name: security-audit
path: .claude/skills/security-audit/
domain: security/compliance
tags: [security, hipaa, persec, opsec, audit]
difficulty: advanced
pattern: legacy
agents: [SECURITY_AUDITOR, COMPLIANCE_OFFICER]
tools: []
inputs: [code_files, data_handling_code]
outputs: [security_report, vulnerabilities, recommendations]
dependencies: []
estimated_duration: 10-30 minutes
safety_critical: true
```

**Intent Mappings:**
- "security audit" → security-audit
- "check hipaa" → security-audit
- "find vulnerabilities" → security-audit
- "opsec review" → security-audit

---

### Tier 8: Specialized Utility Skills

#### pdf
```yaml
name: pdf
path: .claude/skills/pdf/
domain: utilities/documents
tags: [pdf, generation, reports]
difficulty: beginner
pattern: legacy
agents: [REPORT_GENERATOR, ADMIN]
tools: []
inputs: [schedule_data, report_type]
outputs: [pdf_file, printable_schedule]
dependencies: []
estimated_duration: 30-90 seconds
safety_critical: false
```

**Intent Mappings:**
- "generate pdf" → pdf
- "printable schedule" → pdf
- "create report" → pdf

---

#### xlsx
```yaml
name: xlsx
path: .claude/skills/xlsx/
domain: utilities/documents
tags: [excel, import, export, spreadsheet]
difficulty: beginner
pattern: legacy
agents: [DATA_IMPORTER, ADMIN]
tools: []
inputs: [excel_file, schedule_data]
outputs: [imported_data, excel_export]
dependencies: []
estimated_duration: 30-90 seconds
safety_critical: false
```

**Intent Mappings:**
- "import excel" → xlsx
- "export to excel" → xlsx
- "parse spreadsheet" → xlsx

---

#### test-scenario-framework
```yaml
name: test-scenario-framework
path: .claude/skills/test-scenario-framework/
domain: testing/scenarios
tags: [testing, scenarios, end-to-end, edge-cases]
difficulty: advanced
pattern: legacy
agents: [TEST_ENGINEER, QA]
tools: [generate_schedule, validate_acgme_compliance, execute_swap]
inputs: [scenario_type, parameters]
outputs: [scenario_results, test_report, regression_suite]
dependencies: [test-writer, SCHEDULING, SWAP_EXECUTION]
estimated_duration: 5-30 minutes
safety_critical: false
```

**Intent Mappings:**
- "run scenario" → test-scenario-framework
- "test edge cases" → test-scenario-framework
- "end-to-end test" → test-scenario-framework

---

## Routing Rules

### Intent → Skill Mapping

| User Intent | Primary Skill | Secondary Skills |
|-------------|---------------|------------------|
| **Schedule Generation** |
| "generate schedule" | SCHEDULING | COMPLIANCE_VALIDATION, safe-schedule-generation |
| "optimize schedule" | SCHEDULING | schedule-optimization |
| "balance workload" | SCHEDULING | RESILIENCE_SCORING |
| **Compliance & Validation** |
| "validate compliance" | COMPLIANCE_VALIDATION | - |
| "check ACGME" | COMPLIANCE_VALIDATION | acgme-compliance |
| "audit schedule" | COMPLIANCE_VALIDATION | - |
| "is schedule compliant?" | acgme-compliance | COMPLIANCE_VALIDATION |
| **Swaps & Operations** |
| "execute swap" | SWAP_EXECUTION | COMPLIANCE_VALIDATION |
| "find swap candidates" | swap-management | SWAP_EXECUTION |
| "rollback swap" | SWAP_EXECUTION | - |
| **Resilience & Health** |
| "check resilience" | RESILIENCE_SCORING | - |
| "what if resident absent?" | RESILIENCE_SCORING | - |
| "n-1 analysis" | RESILIENCE_SCORING | - |
| "schedule health" | RESILIENCE_SCORING | - |
| **Development & Code** |
| "write tests" | test-writer | python-testing-patterns |
| "review code" | code-review | security-audit, code-quality-monitor |
| "fix tests" | automated-code-fixer | test-writer |
| "debug issue" | systematic-debugger | ORCHESTRATION_DEBUGGING |
| **Infrastructure** |
| "create migration" | database-migration | safe-schedule-generation |
| "create api endpoint" | fastapi-production | test-writer, security-audit |
| "build component" | frontend-development | react-typescript, test-writer |
| **Emergency** |
| "production down" | production-incident-responder | systematic-debugger |
| "system failure" | production-incident-responder | ORCHESTRATION_DEBUGGING |
| **Security** |
| "security audit" | security-audit | code-review |
| "check hipaa" | security-audit | - |

---

### Domain → Skill Mapping

| Domain | Skills |
|--------|--------|
| **residency/scheduling** | SCHEDULING, schedule-optimization, constraint-preflight, solver-control |
| **residency/compliance** | COMPLIANCE_VALIDATION, acgme-compliance |
| **residency/operations** | SWAP_EXECUTION, swap-management, schedule-verification, safe-schedule-generation |
| **resilience/analytics** | RESILIENCE_SCORING |
| **meta/orchestration** | MCP_ORCHESTRATION, CORE |
| **meta/debugging** | ORCHESTRATION_DEBUGGING, systematic-debugger |
| **development/testing** | test-writer, python-testing-patterns, test-scenario-framework |
| **development/quality** | code-review, code-quality-monitor, lint-monorepo, automated-code-fixer |
| **development/backend** | fastapi-production, database-migration |
| **development/frontend** | frontend-development, react-typescript |
| **infrastructure** | docker-containerization, database-migration |
| **security** | security-audit |
| **operations/incident** | production-incident-responder |
| **workflow** | pr-reviewer, changelog-generator, session-documentation |
| **utilities** | pdf, xlsx |

---

### Complexity → Skill Routing

#### Simple Queries (Direct Answer)
- Use general Claude capabilities
- Reference skills: acgme-compliance, CORE

#### Intermediate Tasks (Single Skill)
- swap-management, test-writer, code-review, database-migration
- Estimated: 2-15 minutes

#### Complex Tasks (Multi-Skill Composition)
- SCHEDULING (→ COMPLIANCE_VALIDATION → safe-schedule-generation)
- code-review (→ security-audit → code-quality-monitor)
- Estimated: 15-60 minutes

#### Critical Operations (Safety Skills First)
- safe-schedule-generation (BEFORE any database writes)
- production-incident-responder (for emergencies)
- security-audit (for auth/PHI changes)

---

## Agent-Skill Matrix

### Agent Types

| Agent Type | Description | Primary Skills |
|------------|-------------|----------------|
| **ORCHESTRATOR** | Coordinates multi-agent workflows | CORE, MCP_ORCHESTRATION |
| **SCHEDULER** | Schedule generation and optimization | SCHEDULING, schedule-optimization, constraint-preflight |
| **COMPLIANCE_AUDITOR** | ACGME validation and auditing | COMPLIANCE_VALIDATION, acgme-compliance |
| **SWAP_COORDINATOR** | Swap processing and matching | SWAP_EXECUTION, swap-management |
| **RESILIENCE_ENGINEER** | Health metrics and failure analysis | RESILIENCE_SCORING |
| **DEBUGGER** | Systematic debugging and RCA | systematic-debugger, ORCHESTRATION_DEBUGGING |
| **DEVELOPER** | Code implementation | fastapi-production, frontend-development, test-writer |
| **TEST_ENGINEER** | Test generation and validation | test-writer, python-testing-patterns, test-scenario-framework |
| **REVIEWER** | Code and PR review | code-review, pr-reviewer, code-quality-monitor |
| **SECURITY_AUDITOR** | Security and compliance auditing | security-audit |
| **DBA** | Database operations | database-migration |
| **DEVOPS** | Infrastructure and deployment | docker-containerization, safe-schedule-generation |
| **INCIDENT_RESPONDER** | Production incident response | production-incident-responder |

---

### Skill Access by Agent

```yaml
ORCHESTRATOR:
  can_invoke: [ALL_SKILLS]
  primary: [CORE, MCP_ORCHESTRATION]

SCHEDULER:
  can_invoke: [SCHEDULING, schedule-optimization, COMPLIANCE_VALIDATION, RESILIENCE_SCORING, constraint-preflight, solver-control, safe-schedule-generation]
  primary: [SCHEDULING, schedule-optimization]

COMPLIANCE_AUDITOR:
  can_invoke: [COMPLIANCE_VALIDATION, acgme-compliance, SCHEDULING, schedule-verification]
  primary: [COMPLIANCE_VALIDATION, acgme-compliance]

SWAP_COORDINATOR:
  can_invoke: [SWAP_EXECUTION, swap-management, COMPLIANCE_VALIDATION, RESILIENCE_SCORING]
  primary: [SWAP_EXECUTION, swap-management]

RESILIENCE_ENGINEER:
  can_invoke: [RESILIENCE_SCORING, ORCHESTRATION_DEBUGGING, production-incident-responder, test-scenario-framework]
  primary: [RESILIENCE_SCORING]

DEBUGGER:
  can_invoke: [systematic-debugger, ORCHESTRATION_DEBUGGING, test-writer, code-review]
  primary: [systematic-debugger, ORCHESTRATION_DEBUGGING]

DEVELOPER:
  can_invoke: [fastapi-production, frontend-development, react-typescript, database-migration, test-writer, lint-monorepo, automated-code-fixer]
  primary: [fastapi-production, frontend-development]

TEST_ENGINEER:
  can_invoke: [test-writer, python-testing-patterns, test-scenario-framework, code-quality-monitor]
  primary: [test-writer, python-testing-patterns]

REVIEWER:
  can_invoke: [code-review, pr-reviewer, code-quality-monitor, security-audit]
  primary: [code-review, pr-reviewer]

SECURITY_AUDITOR:
  can_invoke: [security-audit, code-review, COMPLIANCE_VALIDATION]
  primary: [security-audit]
```

---

## Skill Dependencies

### Dependency Graph

```
CORE (foundational, no dependencies)
├─> MCP_ORCHESTRATION
│   └─> ORCHESTRATION_DEBUGGING
│       └─> systematic-debugger
│           └─> test-writer
│
├─> COMPLIANCE_VALIDATION (foundational)
│   ├─> SCHEDULING
│   │   └─> schedule-optimization
│   │       └─> solver-control
│   ├─> SWAP_EXECUTION
│   │   └─> swap-management
│   └─> acgme-compliance
│
├─> RESILIENCE_SCORING (foundational)
│   └─> SWAP_EXECUTION
│
├─> safe-schedule-generation
│   └─> database-migration
│       └─> fastapi-production
│
├─> security-audit (foundational)
│   └─> code-review
│       ├─> pr-reviewer
│       └─> code-quality-monitor
│           └─> automated-code-fixer
│               └─> lint-monorepo
│
├─> test-writer (foundational)
│   ├─> python-testing-patterns
│   ├─> test-scenario-framework
│   └─> constraint-preflight
│
└─> production-incident-responder
    ├─> systematic-debugger
    └─> safe-schedule-generation
```

---

### Critical Dependencies (Safety-Critical Skills)

**SCHEDULING depends on:**
- COMPLIANCE_VALIDATION (validate output)
- safe-schedule-generation (backup before write)

**SWAP_EXECUTION depends on:**
- COMPLIANCE_VALIDATION (swap must maintain compliance)
- RESILIENCE_SCORING (check impact on health)

**safe-schedule-generation depends on:**
- database-migration (backup/restore procedures)

**production-incident-responder depends on:**
- systematic-debugger (root cause analysis)
- safe-schedule-generation (rollback capability)

**security-audit depends on:**
- None (foundational security review)

---

## Tags Taxonomy

### Domain Tags

| Tag | Description | Skills |
|-----|-------------|--------|
| `core` | Essential scheduling/residency skills | SCHEDULING, COMPLIANCE_VALIDATION, RESILIENCE_SCORING, SWAP_EXECUTION |
| `meta` | Meta-level orchestration/routing | CORE, MCP_ORCHESTRATION, ORCHESTRATION_DEBUGGING |
| `residency` | Domain-specific residency operations | SCHEDULING, COMPLIANCE_VALIDATION, SWAP_EXECUTION, schedule-optimization, acgme-compliance, swap-management, safe-schedule-generation, schedule-verification, constraint-preflight, solver-control |
| `resilience` | Resilience framework and analytics | RESILIENCE_SCORING |
| `development` | Software development skills | test-writer, code-review, automated-code-fixer, fastapi-production, frontend-development, react-typescript, python-testing-patterns |
| `infrastructure` | Infrastructure and DevOps | docker-containerization, database-migration |
| `security` | Security and compliance | security-audit |
| `workflow` | Process and workflow management | pr-reviewer, changelog-generator, session-documentation |
| `utilities` | Utility skills | pdf, xlsx |

---

### Type Tags

| Tag | Description | Skills |
|-----|-------------|--------|
| `generation` | Generate new artifacts | SCHEDULING, schedule-optimization, test-writer, changelog-generator |
| `validation` | Validate existing artifacts | COMPLIANCE_VALIDATION, acgme-compliance, code-quality-monitor |
| `execution` | Execute operations | SWAP_EXECUTION, safe-schedule-generation |
| `analysis` | Analyze and report | RESILIENCE_SCORING, systematic-debugger, code-review |
| `debugging` | Debug and troubleshoot | systematic-debugger, ORCHESTRATION_DEBUGGING |
| `orchestration` | Multi-tool/agent coordination | MCP_ORCHESTRATION, CORE |
| `documentation` | Create documentation | changelog-generator, session-documentation |
| `review` | Review code or schedules | code-review, pr-reviewer, schedule-verification |
| `testing` | Test-related skills | test-writer, python-testing-patterns, test-scenario-framework |
| `fixing` | Automated fixing | automated-code-fixer, lint-monorepo |

---

### Complexity Tags

| Tag | Description | Skills |
|-----|-------------|--------|
| `simple` | Simple, quick operations | acgme-compliance, lint-monorepo, pdf, xlsx, changelog-generator |
| `intermediate` | Moderate complexity | COMPLIANCE_VALIDATION, SWAP_EXECUTION, swap-management, test-writer, code-review, database-migration, fastapi-production, frontend-development, safe-schedule-generation |
| `advanced` | Complex, multi-step operations | SCHEDULING, RESILIENCE_SCORING, MCP_ORCHESTRATION, ORCHESTRATION_DEBUGGING, schedule-optimization, systematic-debugger, python-testing-patterns, security-audit, production-incident-responder, test-scenario-framework, constraint-preflight, solver-control |

---

### Safety Tags

| Tag | Description | Skills |
|-----|-------------|--------|
| `safety_critical` | Errors can cause production issues | SCHEDULING, COMPLIANCE_VALIDATION, SWAP_EXECUTION, safe-schedule-generation, database-migration, production-incident-responder, security-audit, constraint-preflight |
| `audit_trail_required` | Must log all actions | SWAP_EXECUTION, safe-schedule-generation, production-incident-responder |
| `backup_required` | Must backup before operation | safe-schedule-generation, database-migration |

---

## Discovery Queries

### Example Queries → Skill Mappings

| Query | Skills Involved | Reasoning |
|-------|----------------|-----------|
| **"Is this schedule ACGME compliant?"** | acgme-compliance OR COMPLIANCE_VALIDATION | Simple query → acgme-compliance<br>Systematic audit → COMPLIANCE_VALIDATION |
| **"What happens if resident X is absent?"** | RESILIENCE_SCORING | N-1 failure simulation |
| **"Execute a swap between A and B"** | SWAP_EXECUTION | Direct swap execution request |
| **"Generate Q2 2025 schedule"** | SCHEDULING → COMPLIANCE_VALIDATION → safe-schedule-generation | Full pipeline |
| **"Find who can swap with Dr. Smith"** | swap-management | Matching algorithm |
| **"Review this PR before merge"** | pr-reviewer → code-review → security-audit | Multi-skill review |
| **"Debug why schedule generation failed"** | systematic-debugger → ORCHESTRATION_DEBUGGING → SCHEDULING | Systematic debug workflow |
| **"Create migration for Person table"** | database-migration | Schema change |
| **"Check if MCP tools are working"** | MCP_ORCHESTRATION | Tool discovery and health check |
| **"Production database down!"** | production-incident-responder → systematic-debugger | Emergency response |
| **"Write tests for swap_executor.py"** | test-writer → python-testing-patterns | Test generation with async patterns |
| **"Is this code secure?"** | security-audit → code-review | Security-first review |
| **"Optimize solver performance"** | schedule-optimization → solver-control | Deep solver expertise |
| **"Document this session"** | session-documentation | Knowledge capture |
| **"Export schedule to Excel"** | xlsx | Utility export |

---

### Discovery by MCP Tool

| MCP Tool | Related Skills |
|----------|----------------|
| `generate_schedule` | SCHEDULING, schedule-optimization, safe-schedule-generation |
| `validate_acgme_compliance` | COMPLIANCE_VALIDATION, acgme-compliance |
| `execute_swap` | SWAP_EXECUTION, swap-management |
| `analyze_swap_candidates` | swap-management, SWAP_EXECUTION |
| `get_schedule_health` | RESILIENCE_SCORING |
| `run_contingency_analysis_resilience_tool` | RESILIENCE_SCORING, production-incident-responder |
| `detect_conflicts` | SCHEDULING, schedule-optimization |
| `celery_task_status` | ORCHESTRATION_DEBUGGING, MCP_ORCHESTRATION |
| `check_background_tasks` | ORCHESTRATION_DEBUGGING |
| `validate_deployment` | safe-schedule-generation |
| `benchmark_solvers` | schedule-optimization, solver-control |

---

## Quick Reference

### Skill Selection Decision Tree

```
User Request
    |
    ├─ Explicit skill named? ──YES──> Invoke named skill
    |                          |
    |                          NO
    |                          |
    ├─ Production emergency? ──YES──> production-incident-responder
    |                         |
    |                         NO
    |                         |
    ├─ Database write operation? ──YES──> safe-schedule-generation → [target skill]
    |                              |
    |                              NO
    |                              |
    ├─ Match intent keywords ──────────> Use Intent Mapping Table
    |                              |
    |                              NO MATCH
    |                              |
    ├─ Match domain keywords ──────────> Use Domain Mapping Table
    |                              |
    |                              NO MATCH
    |                              |
    └─ Use general Claude capabilities (read, explain, analyze)
```

---

### Common Workflows

#### Schedule Generation Workflow
```
1. safe-schedule-generation (backup)
2. SCHEDULING (generate)
3. COMPLIANCE_VALIDATION (validate)
4. RESILIENCE_SCORING (check health)
5. schedule-verification (human review)
```

#### Code Change Workflow
```
1. [Make changes]
2. test-writer (create tests)
3. lint-monorepo (auto-fix style)
4. code-review (review quality)
5. security-audit (if touching auth/PHI)
6. code-quality-monitor (gates)
7. pr-reviewer (final review)
```

#### Swap Request Workflow
```
1. swap-management (find candidates)
2. SWAP_EXECUTION (validate + execute)
3. COMPLIANCE_VALIDATION (post-swap check)
4. RESILIENCE_SCORING (health impact)
```

#### Incident Response Workflow
```
1. production-incident-responder (assess)
2. ORCHESTRATION_DEBUGGING (if MCP/tool failure)
   OR systematic-debugger (if code bug)
3. automated-code-fixer (apply fix)
4. test-writer (regression tests)
5. safe-schedule-generation (rollback if needed)
```

---

### Progressive Disclosure Levels

**Level 1: General Analysis**
- Use: General Claude capabilities
- Example: "Explain how the scheduler works"
- No skill needed

**Level 2: Reference Knowledge**
- Use: acgme-compliance, CORE
- Example: "What's the ACGME 80-hour rule?"
- Quick reference, no execution

**Level 3: Single-Skill Execution**
- Use: Most intermediate skills
- Example: "Write tests for this service"
- Isolated task, single domain

**Level 4: Multi-Skill Composition**
- Use: SCHEDULING, SWAP_EXECUTION, code-review pipelines
- Example: "Generate and validate Q2 schedule"
- Orchestrated workflow

**Level 5: Agent Delegation**
- Use: CORE → spawn specialized agents
- Example: "Generate schedule, review code changes, update docs"
- Parallel multi-agent coordination

---

### Skill Pattern Comparison

| Feature | Kai Pattern | Legacy Pattern |
|---------|-------------|----------------|
| **Structure** | SKILL.md + Workflows/ + Reference/ | SKILL.md only |
| **Complexity** | Advanced, multi-phase | Simple, single-purpose |
| **Workflows** | Documented in separate files | Inline in SKILL.md |
| **Examples** | SCHEDULING, COMPLIANCE_VALIDATION | test-writer, code-review |
| **Use Case** | Complex domain operations | Targeted single tasks |
| **Composability** | High (designed for chaining) | Medium (can be composed) |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-26 | Initial SKILL_INDEX.md creation with all 34 skills |

---

## Maintenance Notes

**When Adding New Skill:**
1. Add entry to appropriate tier section
2. Update routing rules (intent/domain/complexity mappings)
3. Update agent-skill matrix if new agent type
4. Update dependency graph if has dependencies
5. Add appropriate tags
6. Add discovery query examples
7. Increment skill count in header

**When Deprecating Skill:**
1. Mark as deprecated in registry entry
2. Set sunset date
3. Document replacement skill
4. Update routing rules to point to replacement
5. Create migration guide

**When Refactoring Skill:**
1. Update metadata (especially dependencies, tools)
2. Verify routing rules still correct
3. Update examples if interface changed
4. Bump version in skill's SKILL.md

---

**END OF SKILL INDEX**

*This index is the authoritative registry for the Personal AI Infrastructure. Keep it synchronized with .claude/skills/ directory.*
