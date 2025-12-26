# Strategic Decisions: Direction & Priorities

> **Status:** ✅ DECISIONS MADE (2025-12-18) | IMPLEMENTED (2025-12-26)
> **Generated:** 2025-12-18
> **Last Updated:** 2025-12-26
> **Purpose:** Document key strategic decisions for project direction

---

## Executive Summary: Decisions Made

| # | Decision | Choice | Notes |
|---|----------|--------|-------|
| 1 | Target User | **Single residency → Multi-program** | Start single, expand to hospital-wide |
| 2 | Next Feature | **Email Notifications** | Priority on mobile calendar (ics/webcal) |
| 3 | Deployment | **Self-hosted** | May use Render later based on adoption |
| 4 | Integration | **MyEvaluations** | EMR integration will never happen |
| 5 | License | **MIT** | Fully open source |
| 6 | Market Focus | **Military Medicine** | Unique needs, specialized features |
| 7 | AI/ML | **Push automation to limit** | ML for program analytics, test if LLM needed |

### Key Insights
- **Mobile calendar access is critical** - Residents want schedules on phones (ics/webcal)
- **Excel export sufficient for some** - Not everyone needs full app access
- **Military-first** - Optimize for DoD/VA program requirements
- **Automation maximized** - Push scheduling automation as far as possible

---

## Current State Summary

### What This Repository Does

**Residency Scheduler** is a **production-ready, full-stack medical residency program scheduling application** that solves complex scheduling challenges for medical education programs.

#### Core Problem Solved
Medical residency programs involve intricate scheduling with strict regulatory requirements:
- 80-hour work week limits (averaged over 4 weeks)
- Mandatory 1-in-7 day off
- Supervision ratios (PGY-1: 1:2, PGY-2/3: 1:4)
- Procedure credentialing requirements
- Emergency coverage for deployments and leave

The system **automates** this process using constraint-based algorithms while maintaining **ACGME compliance**.

#### Current Capabilities (v1.0.0)

| Feature | Status | Description |
|---------|--------|-------------|
| Schedule Generation | Complete | Greedy algorithm with constraint satisfaction |
| ACGME Compliance | Complete | 80-hour rule, 1-in-7 rule, supervision ratios |
| Absence Management | Complete | Vacation, deployment, TDY, medical, conference |
| Swap Marketplace | Complete | Auto-matching 5-factor algorithm |
| Procedure Credentialing | Complete | Track qualifications, expiration alerts |
| Resilience Framework | Complete | 80% utilization, N-1/N-2 analysis |
| Analytics Dashboard | Complete | Fairness metrics, compliance visualization |
| Export Functionality | Complete | Excel, PDF, iCalendar |
| Role-Based Access | Complete | 8 roles: Admin to MSA |
| Audit Logging | Complete | Full activity trail |

#### Technology Stack
- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL 15, Celery/Redis
- **Frontend**: Next.js 14, React 18, TailwindCSS, TanStack Query
- **Monitoring**: Prometheus, Grafana, Loki

#### Code Metrics
- **Backend**: 228 Python files (~40,000 lines)
- **Frontend**: 197 TypeScript files (~30,000 lines)
- **Documentation**: 32 markdown files
- **Test Coverage**: 70%+ target

---

## Strategic Questions Requiring Decision

### 1. Target User Base

**Question:** Who is the primary customer for this system?

| Option | Description | Implications |
|--------|-------------|--------------|
| **A: Single Institution** | Optimize for one residency program | Simplest deployment, focused features |
| **B: Multi-Program** | Support multiple specialties within one institution | Shared infrastructure, program isolation |
| **C: Multi-Institutional SaaS** | Enterprise offering across hospitals | Multi-tenancy, data isolation, pricing |

**Current Architecture Fit:**
- Option A: Fully supported today
- Option B: Requires program isolation (partially designed)
- Option C: Requires multi-tenancy, SSO, and significant infrastructure

**Recommendation Needed:** Which target should guide v1.1.0 - v2.0 development?

---

### 2. Next Major Feature Priority

**Question:** Which v1.1.0/v1.2.0 features should be prioritized?

| Feature | Effort | User Value | Revenue Potential | Dependencies |
|---------|--------|------------|-------------------|--------------|
| **Email Notifications** | 2 weeks | High | Low | SMTP server |
| **Bulk Import/Export** | 2 weeks | High | Medium | None |
| **Mobile App** | 8 weeks | Medium | Medium | API versioning |
| **AI/ML Optimization** | 12 weeks | High | High | Data volume |
| **SSO/LDAP** | 4 weeks | Medium | High | IT coordination |
| **External API** | 3 weeks | Medium | High | Security audit |

**Current Roadmap Sequence:**
1. v1.1.0: Email Notifications + Bulk Import
2. v1.2.0: Mobile App + Advanced Analytics
3. v2.0+: Enterprise features (SSO, multi-tenancy)

**Recommendation Needed:** Is this sequence correct? Any feature that should jump ahead?

---

### 3. Deployment Model

**Question:** How will customers deploy and run this system?

| Option | Description | Implications |
|--------|-------------|--------------|
| **A: Self-Hosted** | Customers run their own infrastructure | Documentation-heavy, less control |
| **B: Cloud SaaS** | Managed infrastructure | Hosting costs, data security |
| **C: Hybrid** | Both options with data portability | More complexity, wider market |

**Considerations:**
- Data sensitivity and security
- IT department preferences (control vs convenience)
- Support model (on-call vs. ticket-based)

**Recommendation Needed:** Which model aligns with business goals?

---

### 4. Integration Priorities

**Question:** Which external systems should be integrated first?

| System | Integration Type | Value | Complexity |
|--------|-----------------|-------|------------|
| **MyEvaluations** | Bidirectional | High | Medium |
| **EMR (Epic/Cerner)** | Read-only | High | High |
| **Time Tracking (Kronos)** | Write-only | Medium | Low |
| **Calendar (Google/Outlook)** | Bidirectional | Medium | Low |
| **Learning Management** | Write-only | Low | Medium |

**Current State:**
- iCalendar export exists (one-way)
- No EMR integration
- No evaluation system integration

**Recommendation Needed:** Which integration would unlock the most value?

---

### 5. Open Source vs Commercial

**Question:** What is the licensing and monetization strategy?

| Option | Description | Implications |
|--------|-------------|--------------|
| **A: Fully Open Source** | MIT license, community-driven | Community contributions, no direct revenue |
| **B: Open Core** | Core open, premium features commercial | Balance community + revenue |
| **C: Source-Available** | Viewable source, commercial license | Enterprise-focused, less community |

**Current State:** Not formally licensed

**Recommendation Needed:** What is the business model?

---

### 6. Military vs Civilian Focus

**Question:** Should the system optimize for military medical programs specifically?

**Current Military-Specific Features:**
- Deployment absence tracking with orders
- TDY (Temporary Duty) management
- FMIT (Faculty Member In Training) weeks
- Military-style call patterns

**Options:**
| Option | Description | Implications |
|--------|-------------|--------------|
| **A: Military-Primary** | Optimize for DoD/VA programs | Niche market, specialized features |
| **B: Civilian-Primary** | Focus on civilian programs | Larger market, simpler compliance |
| **C: Dual-Market** | Support both with configuration | More testing, broader appeal |

**Recommendation Needed:** Which market is the priority?

---

### 7. AI/ML Investment Level

**Question:** How much should be invested in AI/ML capabilities?

| Level | Features | Investment | Timeline |
|-------|----------|------------|----------|
| **None** | Current algorithms only | $0 | Now |
| **Basic** | Schedule recommendations | $10K-30K | 3 months |
| **Advanced** | NLP queries, anomaly detection | $50K-100K | 6 months |
| **Full AI** | Autonomous scheduling, predictions | $200K+ | 12+ months |

**Current State:**
- Greedy algorithm with constraint satisfaction
- No ML models
- No NLP interface

**Recommendation Needed:** What level of AI investment is appropriate for the target market?

---

## Decision Matrix Template

For each decision, please indicate:

```
Decision: [1-7]
Choice: [A/B/C or specific priority]
Rationale: [Why this choice]
Timeline: [When needed]
Blockers: [Any dependencies or concerns]
```

---

## Questions for Human Stakeholder

### Immediate Decisions (Block development)
1. Should T2 (Email Infrastructure) proceed as planned for v1.1.0?
2. Is the current deployment target (single institution) correct?
3. Should military-specific features remain a priority?

### Strategic Decisions (Shape roadmap)
4. What is the 12-month revenue goal?
5. Is there a target customer/institution already identified?
6. Are there compliance requirements beyond ACGME?

### Resource Questions
7. How many parallel development streams can be sustained?
8. Is external API integration a priority for ecosystem partners?
9. Should community/open-source contributions be encouraged?

---

## Confirmed Path (Human Decision - 2025-12-18)

| Decision | Choice | Implementation Priority | Status (Dec 2025) |
|----------|--------|------------------------|-------------------|
| 1. Target User | **B: Multi-Program** | Start single residency, architect for hospital-wide expansion | On track |
| 2. Next Feature | **Email Notifications** | v1.1.0 - Include ics/webcal for mobile calendar sync | Pending |
| 3. Deployment | **A: Self-Hosted** | Document for self-hosting, evaluate Render for future | 🔧 Docker hardened |
| 4. Integration | **MyEvaluations** | v1.2.0 - Bidirectional sync with evaluation system | Pending |
| 5. License | **MIT** | Add LICENSE file, enable community contributions | ✅ Complete |
| 6. Market Focus | **A: Military-Primary** | Optimize for DoD/VA, military-specific features first | Active |
| 7. AI Investment | **ML Analytics + Max Automation** | Push automation limits, ML for program insights, evaluate LLM later | **🔧 PAI IMPLEMENTED** |

**Legend:** 🔧 = Implemented (pending local validation) | ✅ = Validated by user

### December 2025 Implementation Progress

> **Note**: "Implemented" means code is developed and CI tests pass. Pending user validation in local environment before marked complete.

**Decision 7 - AI Investment: MAJOR MILESTONE**

The Personal AI Infrastructure (PAI) has been implemented, exceeding the original "push automation limits" goal:

| Component | Status | Details |
|-----------|--------|---------|
| **34 Agent Skills** | 🔧 Implemented | Tier 1-4 skills for development, scheduling, operations |
| **27 Slash Commands** | 🔧 Implemented | Rapid task execution for common workflows |
| **34 MCP Tools** | 🔧 Implemented | AI-accessible scheduling operations (up from 4) |
| **4 Operational Modes** | 🔧 Implemented | Interactive, Autonomous, Review, Emergency |
| **Multi-Agent Orchestration** | 🔧 Implemented | Parallel terminal execution (up to 10) |

**Key AI Capabilities Developed (Pending Validation):**
- Autonomous schedule generation and verification
- Constraint validation and conflict detection
- Swap candidate analysis and execution
- ACGME compliance monitoring
- Resilience framework integration
- Cross-disciplinary analytics (SPC, SIR models, Erlang coverage)

**Decision 3 - Deployment: Docker Hardening Implemented**
- Non-root user containers
- Multi-stage builds for security
- Read-only filesystems where applicable
- Improved secret management

> All December 2025 features await local validation before being marked complete.

---

## Action Items Based on Decisions

### If Decision 1 = A (Single Institution)
- Remove multi-tenancy from v2.0 roadmap
- Focus on depth of features over breadth
- Simplify deployment documentation

### If Decision 1 = C (Multi-Institutional SaaS)
- Prioritize SSO/LDAP in v1.2.0
- Add multi-tenancy architecture
- Plan security audit

### If Decision 2 = Mobile App (jumped ahead)
- Create `/api/v2/` mobile-optimized endpoints
- Add push notification infrastructure
- Delay email notifications to v1.2.0

### If Decision 5 = B (Open Core)
- Define which features are "premium"
- Add license key validation
- Create enterprise tier documentation

---

## Appendix: Competitive Landscape

### Existing Solutions
| Product | Focus | Weakness |
|---------|-------|----------|
| Amion | General scheduling | Limited ACGME |
| Qgenda | Enterprise | Expensive, complex |
| New Innovations | Residency management | Older technology |
| MedHub | Residency tracking | Not scheduling-focused |

### Differentiators
- **ACGME-first**: Built-in compliance validation
- **Modern stack**: Next.js + FastAPI
- **Resilience focus**: Cross-industry concepts
- **Open source potential**: Community-driven development

---

*This document requires human input to finalize strategic direction.*
*Once decisions are made, update this document and notify the development team.*
