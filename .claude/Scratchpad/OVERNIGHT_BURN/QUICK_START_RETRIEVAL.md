# OVERNIGHT_BURN Quick-Start Retrieval Guide

**Purpose:** Fast reference for agents and developers accessing OVERNIGHT_BURN reconnaissance data
**Status:** Ready to implement immediately
**Last Updated:** 2025-12-30

---

## For Claude Agents: Start Here

### Quick Facts

- **Total:** 208 files, 4.4 MB
- **Format:** 93% markdown + metadata
- **Organization:** 10 domain-specific sessions
- **Key:** Master index coming soon (templates ready)

### Right Now (Use These)

1. **Orientation:** Read domain-specific `README.md` or `INDEX.md`
2. **Quick answers:** Look for `*QUICK_REFERENCE.md` files
3. **Deep dives:** Find `*-patterns.md` files for your domain

### Example Queries

#### "I need backend service patterns"

```
Location: /Users/aaronmontgomery/.../OVERNIGHT_BURN/SESSION_1_BACKEND/
Files:
  - backend-service-patterns.md (45 KB) ← START HERE
  - backend-repository-patterns.md
  - backend-error-handling.md
Related:
  - SESSION_4_SECURITY (auth patterns)
  - SESSION_6_API_DOCS (API design)
```

#### "What are ACGME requirements?"

```
Location: /Users/aaronmontgomery/.../OVERNIGHT_BURN/SESSION_3_ACGME/
Files:
  - README.md ← START HERE
  - acgme-work-hour-rules.md
  - acgme-supervision-ratios.md
  - acgme-program-evaluation.md
Related:
  - SESSION_7_RESILIENCE (contingency planning)
  - SESSION_5_TESTING (compliance testing)
```

#### "What security patterns do we use?"

```
Location: /Users/aaronmontgomery/.../OVERNIGHT_BURN/SESSION_4_SECURITY/
Files:
  - README.md ← START HERE
  - VALIDATION_FINDINGS_SUMMARY.md
  - authorization-audit.md
  - authentication-patterns.md
Related:
  - SESSION_1_BACKEND (API security)
  - SESSION_6_API_DOCS (data security)
```

---

## File Index by Domain

### SESSION_1_BACKEND (Architecture & Patterns)

| File | Purpose | Priority |
|------|---------|----------|
| `BACKEND_AUTH_SUMMARY.md` | Auth flow, tokens, RBAC | P1 |
| `backend-service-patterns.md` | Service layer analysis | P1 |
| `backend-auth-patterns.md` | JWT, passwords, security | P1 |
| `backend-repository-patterns.md` | Data access layer | P1 |
| `backend-model-patterns.md` | ORM models, relationships | P1 |
| `backend-schema-patterns.md` | Pydantic schemas | P1 |
| `backend-config-patterns.md` | Configuration management | P1 |
| `backend-error-handling.md` | Exception patterns | P1 |
| `backend-logging-patterns.md` | Logging strategies | P2 |
| `backend-celery-patterns.md` | Background tasks | P2 |
| `backend-api-routes.md` | Route organization | P2 |

**Best for:** Backend development, API design, service layer patterns

---

### SESSION_2_FRONTEND (React/Next.js)

| File | Purpose | Priority |
|------|---------|----------|
| `README.md` | Frontend overview | P0 |
| `INDEX.md` | Navigation guide | P0 |
| `QUICK_REFERENCE.md` | Quick lookups | P1 |
| `frontend-component-patterns.md` | React component best practices | P1 |
| `next-app-router-patterns.md` | App Router patterns | P1 |
| `state-management-patterns.md` | TanStack Query, context | P1 |
| `accessibility-audit.md` | WCAG compliance | P1 |
| `typescript-patterns.md` | TS in React | P2 |
| `styling-patterns.md` | TailwindCSS patterns | P2 |

**Best for:** Frontend development, React components, UX patterns

---

### SESSION_3_ACGME (Compliance & Rules)

| File | Purpose | Priority |
|------|---------|----------|
| `README.md` | Program evaluation overview | P0 |
| `RECONNAISSANCE_SUMMARY.md` | ACGME requirements summary | P1 |
| `acgme-work-hour-rules.md` | 80-hour, 1-in-7, duty hour rules | P1 |
| `acgme-supervision-ratios.md` | Faculty-to-resident requirements | P1 |
| `acgme-duty-hour-averaging.md` | 4-week rolling average | P1 |
| `acgme-program-evaluation.md` | Full evaluation framework | P1 |
| `acgme-leave-policies.md` | Vacation, sick, CME policies | P2 |
| `evaluation-quick-reference.md` | Quick lookup guide | P2 |
| `compliance-capability-matrix.md` | What system covers | P2 |

**Best for:** Compliance work, schedule validation, ACGME questions

---

### SESSION_4_SECURITY (Authentication & Authorization)

| File | Purpose | Priority |
|------|---------|----------|
| `README.md` | Security overview | P0 |
| `VALIDATION_FINDINGS_SUMMARY.md` | Audit findings | P1 |
| `authorization-audit.md` | Permission model analysis | P1 |
| `authentication-patterns.md` | Login, tokens, sessions | P1 |
| `HIPAA_AUDIT_SUMMARY.txt` | HIPAA compliance status | P1 |
| `vulnerability-audit.md` | Security vulnerabilities | P1 |
| `password-policy.md` | Password requirements | P2 |
| `encryption-patterns.md` | Data encryption strategies | P2 |
| `rate-limiting-patterns.md` | Anti-abuse measures | P2 |

**Best for:** Security implementation, HIPAA compliance, auth patterns

---

### SESSION_5_TESTING (Test Coverage & Strategies)

| File | Purpose | Priority |
|------|---------|----------|
| `README.md` | Testing overview | P0 |
| `SUMMARY.md` | Coverage summary | P0 |
| `backend-test-patterns.md` | Pytest patterns | P1 |
| `frontend-test-patterns.md` | Jest/RTL patterns | P1 |
| `integration-test-patterns.md` | API testing | P1 |
| `mock-strategy.md` | Mocking patterns | P1 |
| `performance-test-patterns.md` | Load/stress testing | P2 |
| `e2e-test-patterns.md` | Playwright E2E tests | P2 |
| `COVERAGE_SUMMARY.txt` | Coverage metrics | P2 |

**Best for:** Writing tests, improving coverage, test patterns

---

### SESSION_6_API_DOCS (REST API & Schemas)

| File | Purpose | Priority |
|------|---------|----------|
| `README.md` | API overview | P0 |
| `ASSIGNMENTS_API_SUMMARY.txt` | Assignments endpoint spec | P1 |
| `persons-api.md` | Persons endpoint spec | P1 |
| `blocks-api.md` | Blocks endpoint spec | P1 |
| `rotations-api.md` | Rotations endpoint spec | P1 |
| `swaps-api.md` | Swaps endpoint spec | P1 |
| `api-error-codes.md` | Error code reference | P1 |
| `authorization-api.md` | Auth endpoint spec | P2 |
| `api-pagination.md` | Pagination patterns | P2 |

**Best for:** API implementation, endpoint design, schema validation

---

### SESSION_7_RESILIENCE (Framework & Best Practices)

| File | Purpose | Priority |
|------|---------|----------|
| `README.md` | Resilience overview | P0 |
| `INDEX.md` | Navigation guide | P0 |
| `resilience-framework.md` | Core concepts & tiers | P1 |
| `n1-n2-contingency.md` | Backup planning | P1 |
| `epidemiology-index.md` | SIR models, burnout Rt | P1 |
| `spc-monitoring.md` | Statistical process control | P1 |
| `circadian-rhythms.md` | Burnout prediction | P2 |
| `chaos-engineering.md` | Failure injection testing | P2 |
| `recovery-patterns.md` | Disaster recovery | P2 |

**Best for:** System resilience, fault tolerance, monitoring

---

### SESSION_8_MCP (AI Integration Tools)

| File | Purpose | Priority |
|------|---------|----------|
| `README.md` | MCP overview | P0 |
| `mcp-tools-database.md` | 34 database tools documented | P1 |
| `QUICK_REFERENCE.md` | 30-second MCP guide | P1 |
| `SESSION_8_FINAL_REPORT.md` | Reconnaissance findings | P1 |
| `tool-categories.md` | Tools by category | P1 |
| `tool-examples.md` | Usage examples | P2 |
| `authentication.md` | JWT, API key setup | P2 |
| `performance-tuning.md` | Optimization tips | P2 |

**Best for:** AI agents accessing database, MCP integration

---

### SESSION_9_SKILLS (Agent Capabilities)

| File | Purpose | Priority |
|------|---------|----------|
| `README.md` | Skills overview | P0 |
| `EXECUTIVE_SUMMARY.md` | Skills summary | P0 |
| `SEARCH_PARTY_FINDINGS_SUMMARY.md` | Skills audit findings | P1 |
| `skill-specifications.md` | All 50+ skill specs | P1 |
| `skill-best-practices.md` | Skill implementation patterns | P1 |
| `skill-maintenance.md` | Keeping skills updated | P2 |
| `skill-enhancement-roadmap.md` | Future improvements | P2 |

**Best for:** Understanding agent capabilities, skill integration

---

### SESSION_10_AGENTS (Agent Architecture)

| File | Purpose | Priority |
|------|---------|----------|
| `README.md` | Agents overview | P0 |
| `INDEX.md` | Navigation guide | P0 |
| `agents-orchestrator-enhanced.md` | Orchestrator spec | P1 |
| `agents-scheduler-enhanced.md` | Scheduler spec | P1 |
| `agents-historian-enhanced.md` | Historian spec | P1 |
| `agents-meta-updater-enhanced.md` | META_UPDATER spec | P1 |
| `agents-architect-enhanced.md` | Architect spec | P2 |
| `coordination-patterns.md` | Multi-agent patterns | P2 |
| `DELIVERY_MANIFEST.md` | What was delivered | P2 |

**Best for:** Agent implementation, coordination patterns

---

## Search Strategies

### Strategy 1: Start with Domain README

**When:** Not sure where to start
**How:**
```
1. Identify domain (backend, security, testing, etc.)
2. Go to SESSION_X_DOMAIN/README.md
3. Follow navigation to specific topics
```

### Strategy 2: Find Quick Reference

**When:** Need quick answers
**How:**
```
1. Look for QUICK_REFERENCE.md in domain
2. Or search filename patterns: *QUICK*, *SUMMARY*, *INDEX*
3. These files have tables, checklists, quick lookups
```

### Strategy 3: Pattern Search

**When:** Looking for best practices
**How:**
```
1. Search for *-patterns.md files
2. Examples: backend-service-patterns.md, state-management-patterns.md
3. These contain code examples and anti-patterns
```

### Strategy 4: Audit/Finding Search

**When:** Need security or quality info
**How:**
```
1. Search for *AUDIT*, *FINDINGS*, *VALIDATION* files
2. Read findings summaries
3. Review recommendations
```

### Strategy 5: Cross-Domain

**When:** Pattern exists in multiple domains
**How:**
```
1. Start in your primary domain
2. Look for "Related:" or "See also:" sections
3. Follow cross-references to other domains
```

---

## Common Lookups

### "How do I...?"

| Question | Location | File |
|----------|----------|------|
| ...implement a REST endpoint? | SESSION_1 + SESSION_6 | backend-api-routes.md + persons-api.md |
| ...write tests for a service? | SESSION_5 | backend-test-patterns.md |
| ...handle authentication? | SESSION_1 + SESSION_4 | backend-auth-patterns.md + authentication-patterns.md |
| ...ensure ACGME compliance? | SESSION_3 + SESSION_5 | acgme-work-hour-rules.md + compliance tests |
| ...build a React component? | SESSION_2 | frontend-component-patterns.md |
| ...optimize database queries? | SESSION_1 | backend-repository-patterns.md |
| ...handle errors gracefully? | SESSION_1 + SESSION_4 | backend-error-handling.md + validation patterns |

### "What is...?"

| Term | Location | File |
|------|----------|------|
| N-1 vulnerability | SESSION_7 | n1-n2-contingency.md |
| ACGME compliance | SESSION_3 | README.md or acgme-work-hour-rules.md |
| Role-Based Access Control | SESSION_4 | authorization-audit.md |
| MCP tools | SESSION_8 | mcp-tools-database.md |
| Resilience framework | SESSION_7 | resilience-framework.md |
| Circadian rhythm impact | SESSION_7 | circadian-rhythms.md |

### "Where is...?"

| Item | Location |
|------|----------|
| RBAC matrix | SESSION_4/authorization-audit.md (table) |
| API error codes | SESSION_6/api-error-codes.md |
| Database schema | SESSION_6/schema-reference.md |
| Tool categories | SESSION_8/tool-categories.md |
| Agent specs | SESSION_10/agents-*-enhanced.md |
| Test coverage | SESSION_5/COVERAGE_SUMMARY.txt |

---

## File Naming Patterns

### Index/Navigation Files

- `README.md` - Domain overview
- `INDEX.md` - Navigation and cross-references
- `QUICK_REFERENCE.md` - Fast lookup guide

### Summary/Overview Files

- `*SUMMARY.md` - Key findings summary
- `*OVERVIEW.md` - High-level overview
- `EXECUTIVE_SUMMARY.md` - Executive digest
- `*FINDINGS_SUMMARY.md` - Investigation findings

### Pattern/Practice Files

- `*-patterns.md` - Code patterns and best practices
- `*-best-practices.md` - Best practice guide
- `*-architecture.md` - Architecture documentation

### Reference/API Files

- `*-api.md` - REST API specification
- `*-reference.md` - Complete reference
- `*-audit.md` - Security/quality audit
- `*-matrix.md` - Feature/requirement matrix

### Reconnaissance Files

- `SEARCH_PARTY_*.md` - SEARCH_PARTY operation reports
- `RECONNAISSANCE_*.md` - Reconnaissance findings
- `INVESTIGATION_*.md` - Investigation results

---

## Tips & Tricks

### Tip 1: Use MASTER_INDEX.md (Coming Soon)

When implemented, this single file will be your navigation hub. Bookmark it.

### Tip 2: File Size Matters

- **<10 KB:** Quick reference, summaries
- **10-30 KB:** Good balance of depth + readability
- **30+ KB:** Deep dives, comprehensive references

Start small, then read larger files for details.

### Tip 3: Cross-Reference Connections

Many files have "See also:" sections. Follow these for related patterns across domains.

### Tip 4: Priority Tagging

- **P0:** Read first (index, navigation)
- **P1:** Read for implementation (patterns, references)
- **P2:** Read for depth (supporting details)
- **P3:** Reference as needed (archive, specialized)

### Tip 5: Search Within Domain First

Most questions are answered within one domain. Expand to cross-domain only if needed.

### Tip 6: Check for Code Examples

Files with many code blocks are especially useful for implementation.

---

## Getting Help

### If you need...

| Need | First Check | Then Check |
|------|------------|-----------|
| **Code examples** | Pattern files in your domain | Related domains' pattern files |
| **Quick answers** | QUICK_REFERENCE.md | Relevant SUMMARY files |
| **Complete spec** | Domain README.md | Full reference files (20+ KB) |
| **Security advice** | SESSION_4 files | SESSION_1 for secure patterns |
| **Test examples** | SESSION_5 pattern files | Your domain's test patterns |
| **API details** | SESSION_6 API files | Your domain's API routes |

### If files don't exist yet

Some files mentioned in this guide don't exist yet (like MASTER_INDEX.md). They're in the implementation plan. For now:

1. Use this quick-start guide as temporary index
2. Navigate by domain folder directly
3. Follow cross-reference suggestions in files

---

## Next Steps

### For Agent Integration

1. Add OVERNIGHT_BURN path to agent context
2. Implement file registry JSON loader
3. Add search utilities to agent tools
4. Use this guide as fallback when vector DB not ready

### For Vector DB Implementation

1. Extract metadata from all files (script provided)
2. Generate embeddings using OpenAI API
3. Load into Chroma or Pinecone
4. Test semantic search queries

### For Users

1. Bookmark this file
2. Use domain-specific README.md for deep dives
3. Search by filename pattern for specific topics
4. Follow cross-references between domains

---

## File Locations Reference

**Base path:** `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Scratchpad/OVERNIGHT_BURN/`

**Domains:**
- `SESSION_1_BACKEND/` - Backend patterns
- `SESSION_2_FRONTEND/` - Frontend patterns
- `SESSION_3_ACGME/` - ACGME compliance
- `SESSION_4_SECURITY/` - Security & auth
- `SESSION_5_TESTING/` - Test coverage
- `SESSION_6_API_DOCS/` - API specifications
- `SESSION_7_RESILIENCE/` - Resilience framework
- `SESSION_8_MCP/` - MCP tools
- `SESSION_9_SKILLS/` - Agent skills
- `SESSION_10_AGENTS/` - Agent architecture

**Key files to bookmark:**
- `RAG_INDEXING_PLAN.md` - Implementation strategy (just created!)
- `QUICK_START_RETRIEVAL.md` - This file
- `SESSION_*/README.md` - Domain entry points
- `MASTER_INDEX.md` - Coming soon!

---

**Last updated:** 2025-12-30 | **Status:** Ready to use
