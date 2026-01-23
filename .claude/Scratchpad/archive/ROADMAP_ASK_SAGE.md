# Ask Sage Integration Roadmap

> **Document Type:** Strategic Planning
> **Classification:** Future State (Contingent on Local Deployment Success)
> **Audience:** Program Director / Technical Leadership
> **Last Updated:** 2026-01-06
> **Session:** USASOC Strategic Mission

---

## Executive Summary

This roadmap outlines the path from successful local deployment to DOD-wide availability via Ask Sage integration. This is a **2-5 year strategic initiative** that requires formal acquisition channels, not a quick technical integration.

**Key Insight:** Ask Sage announced their DHA partnership in December 2025. Their platform supports edge deployment and MCP-style tool integration - making the Residency Scheduler's 83+ MCP tools a natural fit. However, the path to IL5 PHI integration requires substantial security hardening that goes far beyond the current implementation.

---

## Current State vs. Target State

```
CURRENT STATE (Local Deployment)          TARGET STATE (Ask Sage / IL5)
┌────────────────────────────────────┐    ┌────────────────────────────────────┐
│                                    │    │                                    │
│  Security Level: IL2/IL3 Equivalent│    │  Security Level: IL5               │
│  ├── JWT + RBAC auth              │    │  ├── CAC/PKI authentication        │
│  ├── Bcrypt password hashing      │    │  ├── Zero-trust architecture       │
│  ├── Rate limiting                │    │  ├── Continuous monitoring         │
│  └── Audit logging                │    │  └── STIG-hardened infrastructure  │
│                                    │    │                                    │
│  Data: Local PostgreSQL           │    │  Data: IL5-authorized cloud        │
│  ├── All PII stays on-premise     │    │  ├── FedRAMP High authorized       │
│  ├── No external transmission     │    │  ├── DOD CC SRG Level 5            │
│  └── .gitignore protections       │    │  └── FISMA Moderate (minimum)      │
│                                    │    │                                    │
│  Users: Single MTF                │    │  Users: Multi-MTF / Enterprise     │
│  ├── Coordinator primary          │    │  ├── Federated identity (CAC)      │
│  ├── Excel exports for others     │    │  ├── Role-based multi-tenant       │
│  └── Manual data entry            │    │  └── Integration with MHS Genesis  │
│                                    │    │                                    │
│  AI: MCP Server (local)           │    │  AI: Ask Sage Platform             │
│  ├── 83+ scheduling tools         │    │  ├── IL5-approved LLM              │
│  ├── Claude Code integration      │    │  ├── Tool marketplace              │
│  └── RAG knowledge base           │    │  └── Enterprise governance         │
│                                    │    │                                    │
└────────────────────────────────────┘    └────────────────────────────────────┘
```

---

## IL5 Gap Analysis

### What We Have (IL2/IL3 Equivalent)

| Capability | Current Implementation | IL5 Readiness |
|------------|----------------------|---------------|
| **Authentication** | JWT + httpOnly cookies | Ready for upgrade |
| **Authorization** | 8-tier RBAC (Admin -> MSA) | Compliant |
| **Password Security** | Bcrypt hashing, 12+ char min | Compliant |
| **Session Management** | Token blacklist, refresh rotation | Compliant |
| **Audit Logging** | SQLAlchemy-Continuum versioning | Compliant |
| **Input Validation** | Pydantic schemas, SQLAlchemy ORM | Compliant |
| **Rate Limiting** | Redis-backed sliding window | Compliant |
| **Error Handling** | Sanitized responses, no stack traces | Compliant |
| **Secret Management** | Environment variables, rotation support | Needs enhancement |

### What's Missing for IL5

| Requirement | Status | Effort Estimate |
|-------------|--------|-----------------|
| **CAC/PKI Authentication** | Not implemented | 2-4 weeks |
| **PIV/CAC card integration** | Not implemented | 2-4 weeks |
| **SAML 2.0 / OIDC (DoD IdP)** | Stubs exist, not complete | 1-2 weeks |
| **Continuous Monitoring** | Not implemented | 4-8 weeks |
| **SIEM Integration** | Not implemented | 2-4 weeks |
| **STIG Hardening** | Partial (Dockerfile best practices) | 4-8 weeks |
| **FedRAMP Controls** | Infrastructure-level, not app | Vendor responsibility |
| **FIPS 140-2 Encryption** | Not enforced | 1-2 weeks |
| **Vulnerability Scanning** | GitHub Dependabot only | 1-2 weeks |
| **Penetration Testing** | Not performed | 2-4 weeks (external) |

### Gap Details

#### 1. CAC/PKI Authentication

**Current:** Username/password authentication with JWT tokens.

**Required for IL5:**
- CAC smart card reader integration
- PIV certificate validation
- DoD PKI trust chain
- Fallback to SAML 2.0 via DoD IdP

**Implementation Path:**
```python
# backend/app/auth/sso/cac_provider.py (stub exists)
# Needs implementation of:
# - PKCS#11 interface for CAC reader
# - X.509 certificate parsing
# - DoD root CA validation
# - Certificate revocation checking (OCSP/CRL)
```

**Effort:** 2-4 weeks development + 2-4 weeks testing/certification

#### 2. Continuous Monitoring (ConMon)

**Current:** Basic health checks, Prometheus metrics (optional).

**Required for IL5:**
- Real-time security event correlation
- Automated vulnerability scanning
- Configuration drift detection
- Anomaly detection
- Compliance dashboard (NIST 800-53 controls)

**Implementation Path:**
- Integrate with SIEM (Splunk, ELK, or DoD-approved)
- Deploy vulnerability scanner (Tenable, Qualys)
- Implement SCAP compliance scanning
- Create ConMon automation playbooks

**Effort:** 4-8 weeks development + ongoing operational overhead

#### 3. STIG Hardening

**Current:** Multi-stage Docker builds, non-root user, minimal attack surface.

**Required for IL5:**
- Full STIG checklist for:
  - PostgreSQL
  - Redis
  - Python runtime
  - Docker/Kubernetes
  - Application layer
- Automated STIG compliance validation
- Remediation documentation

**Effort:** 4-8 weeks + Iron Bank approval process (6-12 weeks)

#### 4. FedRAMP Controls

**Current:** Not applicable (local deployment).

**For Cloud (Ask Sage):**
- FedRAMP High authorization required for IL5
- Ask Sage provides this if using their platform
- Residency Scheduler becomes a "tenant application"
- Our responsibility: Application-level controls only

**Key Insight:** FedRAMP is an infrastructure problem, not an application problem. If deploying on Ask Sage or Platform One, they handle FedRAMP. We inherit their authorization.

---

## Ask Sage Integration Architecture

```
Ask Sage IL5 Integration
┌─────────────────────────────────────────────────────────────────────────┐
│                     Ask Sage Platform (FedRAMP High)                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        Ask Sage Core                              │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────┐  │  │
│  │  │ IL5 LLM   │  │ Identity  │  │ Governance│  │ Tool Registry │  │  │
│  │  │ (Claude)  │  │ (CAC/SSO) │  │ & Audit   │  │ (MCP Compat)  │  │  │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └───────┬───────┘  │  │
│  │        │              │              │                │          │  │
│  │        └──────────────┼──────────────┴────────────────┘          │  │
│  │                       │                                           │  │
│  └───────────────────────┼───────────────────────────────────────────┘  │
│                          │                                              │
│  ┌───────────────────────┼───────────────────────────────────────────┐  │
│  │         Residency Scheduler (Tool Provider)                       │  │
│  │                       │                                           │  │
│  │  ┌────────────────────▼────────────────────┐                     │  │
│  │  │         MCP Tool Interface               │                     │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ │                     │  │
│  │  │  │Scheduling│ │Compliance│ │Resilience│ │ ... 80+ more tools  │  │
│  │  │  │  Tools   │ │  Tools   │ │  Tools   │ │                     │  │
│  │  │  └──────────┘ └──────────┘ └──────────┘ │                     │  │
│  │  └─────────────────────────────────────────┘                     │  │
│  │                       │                                           │  │
│  │  ┌────────────────────▼────────────────────┐                     │  │
│  │  │         Scheduler Backend                │                     │  │
│  │  │  (FastAPI + SQLAlchemy + OR-Tools)      │                     │  │
│  │  └─────────────────────────────────────────┘                     │  │
│  │                       │                                           │  │
│  │  ┌────────────────────▼────────────────────┐                     │  │
│  │  │         IL5 PostgreSQL                   │                     │  │
│  │  │  (FedRAMP High, encrypted at rest)       │                     │  │
│  │  └─────────────────────────────────────────┘                     │  │
│  │                                                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Edge Deployment Option (Air-gapped MTFs)                               │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Local Ask Sage Node → Local Scheduler → Sync when connected      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Integration Points

1. **MCP Tool Registration**
   - Residency Scheduler's 83+ tools register with Ask Sage tool marketplace
   - Tools are invoked by Ask Sage's LLM when users ask scheduling questions
   - Example: "Generate next week's schedule for PGY-2 residents"

2. **Identity Federation**
   - Ask Sage handles CAC/SSO authentication
   - Residency Scheduler receives verified identity claims
   - RBAC decisions based on federated roles

3. **Data Residency**
   - PostgreSQL runs in Ask Sage's IL5 environment
   - No data leaves FedRAMP boundary
   - Multi-tenant isolation per MTF

4. **Edge Deployment**
   - For air-gapped MTFs, Ask Sage supports edge nodes
   - Scheduler runs locally, syncs when connectivity available
   - This matches our current local deployment model

---

## Acquisition Timeline Reality

```
DOD Acquisition Reality Check
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Phase 1: Local Pilot (YOU ARE HERE)                                    │
│  Timeline: 0-6 months                                                   │
│  ├── Deploy at your MTF                                                 │
│  ├── Collect metrics (time saved, compliance catches)                   │
│  ├── Document success stories                                           │
│  └── Build coalition with other PDs                                     │
│                                                                          │
│  Phase 2: Hospital-Wide Expansion                                       │
│  Timeline: 6-12 months                                                  │
│  ├── Brief hospital leadership on pilot success                         │
│  ├── Expand to other residency programs                                 │
│  ├── Formalize IT support relationship                                  │
│  └── Prepare DHA pitch deck                                             │
│                                                                          │
│  Phase 3: DHA Engagement                                                │
│  Timeline: 12-24 months                                                 │
│  ├── Contact DHA Education & Training Directorate                       │
│  ├── Submit to DHA Innovation pipeline                                  │
│  ├── Explore Ask Sage integration path                                  │
│  └── Begin Platform One / Iron Bank process                            │
│                                                                          │
│  Phase 4: Enterprise Deployment                                         │
│  Timeline: 24-36+ months                                                │
│  ├── Complete Iron Bank hardening                                       │
│  ├── Achieve cATO through Platform One                                  │
│  ├── Ask Sage tool marketplace listing                                  │
│  └── Multi-MTF rollout coordination                                     │
│                                                                          │
│  Total Realistic Timeline: 2-5 years                                    │
│                                                                          │
│  CRITICAL UNDERSTANDING:                                                │
│  ├── You own Phase 1-2                                                  │
│  ├── You contribute to Phase 3-4                                        │
│  └── DOD owns Phase 4 execution                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Platform One / Iron Bank Path

If pursuing DOD-wide deployment through Platform One:

### Iron Bank Container Hardening

**What's Required:**
1. Base images from Iron Bank (Python, Node.js, PostgreSQL)
2. STIG compliance documentation
3. Vulnerability scan results (zero critical, minimal high)
4. Container signing

**Current Status:**
- Dockerfile uses multi-stage builds (good)
- Non-root user (good)
- Minimal attack surface (good)
- NOT using Iron Bank base images (gap)

**Effort:** 6-12 weeks for full Iron Bank approval

### Platform One Onboarding

**Process:**
1. Request access to Repo1 (DOD GitLab)
2. Submit Iron Bank container requests
3. Create Helm charts for Big Bang deployment
4. Pass security gate reviews
5. Achieve cATO (Continuous Authority to Operate)

**Contact:** https://p1.dso.mil/

---

## Ask Sage Engagement Strategy

### Why Ask Sage?

1. **DHA Partnership** (announced Dec 2025)
   - Already authorized for DOD medical AI
   - Handles IL5 compliance infrastructure

2. **MCP Compatibility**
   - Ask Sage supports tool integration
   - Our 83+ MCP tools are a natural fit
   - Claude (Anthropic) is their LLM partner

3. **Edge Deployment**
   - Supports air-gapped deployments
   - Matches our local-first architecture

### Engagement Approach

**Phase 1: Technical Evaluation**
- Contact Ask Sage Government team
- Request sandbox environment
- Test MCP tool integration
- Evaluate data residency options

**Phase 2: Partnership Discussion**
- Present local deployment success metrics
- Discuss integration requirements
- Explore pricing/licensing models
- Identify technical integration work

**Phase 3: Formal Integration**
- Security documentation exchange
- API integration development
- Testing and certification
- Deployment planning

### Key Questions for Ask Sage

1. What's the process for adding custom MCP tools to the platform?
2. How do you handle multi-tenant data isolation for different MTFs?
3. What's the timeline for IL5 authorization for new integrations?
4. Do you support edge deployment for air-gapped facilities?
5. What's the pricing model for government entities?

---

## Security Hardening Checklist for IL5

Before Ask Sage integration, close these gaps:

### Authentication

- [ ] Implement CAC/PIV authentication module
- [ ] Integrate with DoD Identity Provider (SAML 2.0)
- [ ] Add certificate validation chain
- [ ] Implement session binding to certificate

### Encryption

- [ ] Enable FIPS 140-2 compliant crypto
- [ ] Implement TLS 1.3 only (disable 1.2)
- [ ] Encrypt database at rest (PostgreSQL TDE)
- [ ] Encrypt Redis cache (TLS)

### Monitoring

- [ ] Integrate with SIEM platform
- [ ] Implement security event logging
- [ ] Add anomaly detection
- [ ] Create ConMon dashboard

### Hardening

- [ ] Complete STIG checklist for all components
- [ ] Migrate to Iron Bank base images
- [ ] Implement container signing
- [ ] Pass vulnerability scan (zero critical)

### Documentation

- [ ] System Security Plan (SSP)
- [ ] Security Assessment Report (SAR)
- [ ] Plan of Action and Milestones (POA&M)
- [ ] Continuous Monitoring Strategy

---

## Cost-Benefit Analysis

### Current Local Deployment

| Item | Cost |
|------|------|
| Software Licensing | $0 (open source) |
| Hardware (VM/server) | $0-2K (existing infrastructure) |
| Maintenance | Your time |
| **Total Year 1** | **~$0-2K** |

### Commercial Alternative

| Item | Cost |
|------|------|
| Typical scheduler license | $50K-200K/year |
| Implementation | $20K-50K |
| Customization | $30K-100K |
| **Total Year 1** | **$100K-350K** |

### Ask Sage / IL5 Path

| Item | Cost |
|------|------|
| Security hardening effort | $50K-150K (contractor time) |
| Iron Bank certification | $20K-50K (if contracted) |
| Ask Sage platform fees | TBD (government pricing) |
| Ongoing compliance | $20K-50K/year |
| **Total Year 1** | **$100K-300K** |

**Key Insight:** The Ask Sage path is expensive but provides DOD-wide leverage. The local path is free but limited to your MTF. The value proposition is in coalition-building - if multiple programs want this, the per-program cost drops dramatically.

---

## Recommended Next Steps

### Immediate (This Month)

1. Complete local deployment successfully
2. Document time savings and compliance catches
3. Present to DIO for formal pilot approval

### Near-Term (This Quarter)

1. Brief other Program Directors
2. Collect testimonials from coordinators
3. Prepare 1-page leadership proposal

### Medium-Term (This Year)

1. Contact DHA Education & Training
2. Explore Ask Sage technical evaluation
3. Begin Iron Bank container hardening

### Long-Term (Next Year+)

1. Submit to Platform One
2. Formalize Ask Sage integration
3. Coordinate multi-MTF rollout

---

## Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Ask Sage integration costs exceed budget | Medium | High | Seek DHA/CDAO sponsorship |
| Iron Bank process takes longer than expected | High | Medium | Start early, expect 6-12 months |
| Local deployment doesn't prove value | Low | High | Focus on measurable metrics |
| DOD adopts different solution | Medium | High | Keep code open, stay involved |
| Security gaps block IL5 | Medium | High | Invest in hardening early |

---

## Conclusion

The path from local deployment to Ask Sage integration is a multi-year strategic initiative. Success depends on:

1. **Proving value locally first** - This is your foundation
2. **Building coalition** - Other programs wanting the solution
3. **Investing in security** - IL5 requires real hardening work
4. **Engaging formal channels** - DHA, Platform One, Ask Sage
5. **Accepting role evolution** - From owner to contributor

The good news: The architecture is sound. The MCP tools are ready. The local deployment model works. What's needed is time, advocacy, and strategic engagement with DOD acquisition processes.

---

## References

- DHA Education & Training: https://www.health.mil/Military-Health-Topics/Education-and-Training
- Platform One: https://p1.dso.mil/
- Iron Bank: https://ironbank.dso.mil/
- Ask Sage: https://www.asksage.ai/
- FedRAMP Marketplace: https://marketplace.fedramp.gov/

---

*This roadmap is contingent on successful local deployment. See ROADMAP_LOCAL_DEPLOYMENT.md for Phase 1.*
