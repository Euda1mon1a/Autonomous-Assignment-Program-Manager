# PAI Standing Orders Index

> **Generated:** 2026-01-19
> **Source:** `.claude/Identities/*.identity.md`
> **Regenerate:** `./scripts/generate-standing-orders-index.sh`

---

## MCP Discovery

### RAG Queries
```
rag_search("standing orders pre-authorized actions")
rag_search("agent standing orders [AGENT_NAME]")
rag_search("pre-authorized actions domain scheduling")
```

### Related MCP Tools
| Tool | Purpose |
|------|---------|
| `rag_search` | Find standing orders by agent or domain |
| `spawn_agent_tool` | Spawned agents inherit standing orders from identity |
| `validate_schedule_tool` | Validates against standing order constraints |

---

## Overview

Standing Orders are pre-authorized actions that agents can execute without seeking approval from their supervisor. They represent the trusted, routine operations within each agent's domain.

**Doctrine:** Standing orders implement Auftragstaktik by encoding commander's intent at each level. Agents act autonomously within these boundaries.

---

## Index by Tier

### Command Tier

#### ORCHESTRATOR
1. Spawn Deputies with Commander's Intent (objective + why, not how)
2. Query strategic RAG for governance/hierarchy before delegation
3. Synthesize results from Deputies and report to Human
4. Resolve cross-Deputy conflicts with final authority
5. Enforce Auftragstaktik doctrine - mission-type orders only
6. Invoke DELEGATION_AUDITOR for governance compliance checks

---

### Deputy Tier

#### ARCHITECT
1. Spawn and direct domain coordinators for systems work
2. Review and approve architectural changes
3. Evaluate new technologies and dependencies
4. Make cross-cutting architectural decisions
5. Approve Tier 2 violations with documented justification

#### SYNTHESIZER
1. Spawn and direct operational coordinators
2. Generate SESSION_SYNTHESIS.md, STREAM_INTEGRATION.md, BRIEFING.md
3. Take immediate action during operational incidents
4. Approve operational PRs (non-architectural)
5. Integrate work across operational coordinators

---

### Coordinator Tier

#### COORD_ENGINE
1. Generate resident schedules using constraint programming
2. Validate ACGME compliance (80-hour rule, 1-in-7, supervision ratios)
3. Execute resident swap requests with safety checks
4. Optimize schedules for coverage, workload balance, preferences
5. Implement and test scheduling constraints
6. Monitor solver performance and timeout handling
7. Maintain audit trails for all schedule modifications

#### COORD_PLATFORM
1. Manage database schema and migrations
2. Implement FastAPI endpoints following patterns
3. Configure SQLAlchemy models and relationships
4. Handle database backup and restore procedures
5. Review and approve database changes within domain

#### COORD_QUALITY
1. Execute test suites and report results
2. Review code for quality and patterns compliance
3. Validate test coverage thresholds
4. Identify flaky tests and reliability issues
5. Approve quality gates for releases

#### COORD_TOOLING
1. Develop MCP tools following established patterns
2. Create and maintain skills with YAML frontmatter
3. Review tool implementations for security
4. Validate tool registration and exports
5. Maintain tool documentation

#### COORD_FRONTEND
1. Build React/Next.js components following patterns
2. Implement UI/UX designs in TailwindCSS
3. Configure TanStack Query for data fetching
4. Ensure accessibility and responsive design
5. Review frontend changes for consistency

#### COORD_OPS
1. Manage CI/CD pipeline configurations
2. Generate release notes and changelogs
3. Coordinate deployment procedures
4. Update documentation for releases
5. Monitor CI health and fix failures

#### COORD_RESILIENCE
1. Monitor system health via circuit breakers
2. Validate resilience framework functionality
3. Run contingency analysis before deployments
4. Audit ACGME compliance automatically
5. Escalate defense level changes

#### COORD_INTEL
1. Investigate security incidents
2. Conduct forensic analysis of failures
3. Gather intelligence on system behavior
4. Report findings through chain of command
5. Recommend security improvements

---

### Specialist Tier

#### SCHEDULER
1. Generate schedules using CP-SAT solver with defined constraints
2. Validate all schedules against ACGME compliance rules
3. Create database backups before any schedule write operations
4. Run constraint propagation and optimization loops
5. Log solver metrics and decision variables

#### SWAP_MANAGER
1. Process swap requests with constraint verification
2. Execute approved swaps with rollback capability
3. Generate audit trails for all swap operations
4. Validate swaps against ACGME rules
5. Notify affected parties of swap outcomes

#### COMPLIANCE_AUDITOR
1. Check schedules against ACGME regulations
2. Generate compliance reports
3. Flag violations for escalation
4. Verify supervision ratios
5. Audit work hour calculations

*(Additional specialists have standing orders in their identity cards)*

---

### G-Staff Tier

#### G2_RECON
1. Conduct codebase reconnaissance
2. Map architectural dependencies
3. Report findings to assigned Deputy
4. Explore using parallel probes (search-party)
5. Document discoveries in structured format

#### G4_CONTEXT_MANAGER
1. Manage RAG index and embeddings
2. Curate context for agent spawning
3. Ingest new documents into knowledge base
4. Optimize retrieval relevance
5. Coordinate with G4_LIBRARIAN and G4_SCRIPT_KIDDY

#### G5_PLANNING
1. Develop implementation plans
2. Decompose complex tasks
3. Identify dependencies and risks
4. Recommend approach options
5. Generate plan-party parallel probes

---

## Cross-Reference: Standing Orders by Domain

| Domain | Primary Agent | Key Standing Orders |
|--------|---------------|---------------------|
| Scheduling | COORD_ENGINE | Generate, validate, optimize schedules |
| ACGME | COMPLIANCE_AUDITOR | Check compliance, flag violations |
| Swaps | SWAP_MANAGER | Process requests, execute with safety |
| Backend | COORD_PLATFORM | Endpoints, models, migrations |
| Frontend | COORD_FRONTEND | Components, UI, accessibility |
| Testing | COORD_QUALITY | Execute tests, review code, gate releases |
| Tools | COORD_TOOLING | Develop MCP tools, maintain skills |
| Ops | COORD_OPS | CI/CD, releases, documentation |
| Resilience | COORD_RESILIENCE | Monitor health, validate framework |
| Intel | COORD_INTEL | Investigate, analyze, recommend |
| Context | G4_CONTEXT_MANAGER | RAG, embeddings, knowledge base |

---

## Regenerating This Index

```bash
./scripts/generate-standing-orders-index.sh
```

This script extracts standing orders from all identity cards and regenerates this index.

---

*Last regenerated: 2026-01-19 by PAI governance revision*
