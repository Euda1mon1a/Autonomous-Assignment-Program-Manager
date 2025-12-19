# Automation Research Summaries

> **Date:** 2025-12-19
> **Source:** ChatGPT Pulse automated research digest
> **Purpose:** Curated external research and recommendations relevant to this repository

---

## Overview

This document captures high-value external research and technical recommendations surfaced through automated monitoring. Each section is filtered for relevance to the Residency Scheduler project.

---

## System Improvement Recommendations

The following recommendations were identified as directly applicable to our architecture:

### 1. Durable Background Solver Execution

**Problem:** Schedule generation can time out, causing clients to retry and potentially create duplicate or partial writes.

**Recommendation:** Use Celery with persistent status tracking for schedule generation.

**Relevance to Our Codebase:**
- `backend/app/scheduling/engine.py` - Schedule generation
- `backend/app/core/celery_app.py` - Existing Celery infrastructure
- `backend/app/repositories/idempotency.py` - Idempotency handling

**Sketch:**
```python
# schedule route - return 202 Accepted with job tracking
@router.post("/schedule/generate", status_code=202)
async def generate_schedule(payload, idem_key: str = Header(...)):
    existing = await idem_repo.get(idem_key)
    if existing: return existing
    job = schedule_task.delay(payload, idem_key)
    await idem_repo.save(idem_key, {"job_id": job.id, "status": "queued"})
    return {"job_id": job.id, "status": "queued"}
```

**Status:** Partially implemented - Celery exists but schedule generation may not use durable tracking.

---

### 2. Generation Lease with Heartbeat

**Problem:** Redis locks can expire while the solver runs, allowing a second worker to obtain the lock and create overlapping writes.

**Recommendation:** Implement fencing tokens with heartbeat to prevent stale workers from publishing.

**Relevance to Our Codebase:**
- `backend/app/scheduling/service.py` - Schedule service
- `backend/app/resilience/` - Existing resilience patterns

**Sketch:**
```python
def try_acquire(redis, key, ttl):
    fence = redis.incr(f"{key}:fence")
    ok = redis.set(key, fence, nx=True, ex=ttl)
    return fence if ok else None

def publish_if_fence_matches(conn, head_id, version_id, token):
    conn.execute(
       "UPDATE schedule_heads SET active_version = :v WHERE id = :id AND last_fence < :f",
       {"v": version_id, "id": head_id, "f": token}
    )
```

**Status:** Not implemented - evaluate for v1.2.0.

---

### 3. Readiness Health Checks

**Problem:** App returns 200 OK but dependencies (DB, Redis) are unavailable, causing partial failures.

**Recommendation:** Add `/health/ready` and `/health/live` endpoints.

**Relevance to Our Codebase:**
- `backend/app/api/routes/health.py` - May need expansion

**Sketch:**
```python
@router.get("/health/ready")
async def ready():
    await db_ping()   # SELECT 1
    await redis.ping()
    return {"status": "ready"}

@router.get("/health/live")
def live():
    return {"status": "alive"}
```

**Status:** Check if readiness probes exist - Docker/k8s deployments need these.

---

### 4. Prometheus/OpenTelemetry Instrumentation

**Problem:** Without fine-grained metrics, high p95 latency is opaque.

**Recommendation:** Emit histograms for solver runtime, lock waits, DB contention.

**Relevance to Our Codebase:**
- `backend/app/resilience/metrics.py` - Existing metrics infrastructure
- `docs/operations/metrics.md` - Metrics documentation

**Suggested Metrics:**
```python
lock_wait = Histogram("lock_wait_seconds", "time waiting for lock")
solver_time = Histogram("solver_runtime_seconds", "solver run time")
assignment_write_total = Counter("assignment_write_total", "assignments written")
assignment_write_conflict_total = Counter("assignment_write_conflict_total", "conflicts")
```

**Status:** Prometheus exists (Session 9 added 34 alert rules) - verify solver instrumentation.

---

## ACGME Research Updates

### 2025-2026 Duty Hour Requirements

**Source:** [ACGME Common Program Requirements](https://www.acgme.org/globalassets/pfassets/programrequirements/2025-reformatted-requirements/cprresidency_2025_reformatted.pdf)

**Key Points (effective September 3, 2025):**

1. **Clinical and educational work hours** terminology now explicitly includes work done from home (EMR inbox work, etc.)

2. **80-hour weekly limit** (averaged over 4 weeks) remains unchanged

3. **14 hours free after 24 hours of clinical assignments** - reinforced in updated requirements

4. **Terminology reframing** - "duty hours" → "clinical and educational work hours"

**Implementation Impact:**
- `backend/app/scheduling/acgme_validator.py` - May need to account for at-home work tracking
- Consider UI for residents to log home administrative work
- Audit current hour calculations against new terminology

**Status:** Review validator against September 2025 requirements.

---

### Schedule Optimization and Burnout Research

**Source:** [PLOS ONE Study](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0236952)

**Finding:** Automated scheduling tools improve:
- First-choice assignment rates
- Reduced conflicts between consecutive shifts
- Perceptions of fairness (correlated with reduced burnout risk)

**Relevance:** Validates our constraint-based approach. Consider adding fairness metrics to analytics dashboard.

---

## Military Medicine Research

### FY 2026 NDAA Updates (Signed December 18, 2025)

**Source:** [Reuters](https://www.reuters.com/business/aerospace-defense/trump-expected-sign-1-trillion-annual-defense-bill-2025-12-18/)

**Key Points:**
- **$901 billion** defense authorization (~$8B above request)
- **Military pay raise** (~3.8-4%) included
- **Troop level restrictions** for Europe and South Korea
- **Quality-of-life provisions** (childcare, education benefits)

**Relevance to Our System:**
- Military residency programs may see budget adjustments
- Deployment patterns could be affected by troop level policies
- STRATEGIC_DECISIONS.md confirms "Military-Primary" market focus

**Action Items:**
- Monitor DoD/VA program restructuring announcements
- No code changes needed yet

---

### DoD Residency Restructuring

**Finding:** No clear published literature on 2024-2025 restructuring impacts specific to Hawaii or TDY handling was found in public indices.

**Recommendation:** Pursue internal DoD/VA sources or policy documents for specific guidance.

---

## Solver & Optimization Landscape

### 2025 Solver Comparison

**Sources:**
- [arXiv - Multi-Objective Genetic Algorithms](https://arxiv.org/abs/2508.20953)
- Our `docs/research/EXPERIMENTAL_RESEARCH_STRATEGY.md`

**Current Landscape:**
- **OR-Tools CP-SAT** remains widely used for constraint-heavy scheduling
- **Multi-objective genetic algorithms** gaining academic interest
- **QUBO/Quantum-inspired** approaches showing promise (see our quantum-physics-scheduler branch)

**Relevance:**
- Our experimental branches (`quantum-physics`, `catalyst-concepts`, `transcription-factors`) align with current research directions
- CP-SAT baseline remains appropriate for production
- Success criteria in EXPERIMENTAL_RESEARCH_STRATEGY.md are reasonable (≥95% quality in ≤50% time)

---

## Healthcare IT Resilience

### Hospital Scheduling Outage Lessons

**Source:** [Censinet - AWS Outage Analysis](https://censinet.com/perspectives/aws-outage-healthcare-digital-backbone)

**Key Lessons from July 2024 Global Outage:**
- Cloud and single-vendor dependencies can cause widespread disruption
- Hundreds of hospitals affected simultaneously
- Scheduling and EHR systems particularly vulnerable

**Relevance to Our Architecture:**
- Self-hosted deployment model (per STRATEGIC_DECISIONS.md) provides resilience
- `backend/app/resilience/` framework addresses cascade failures
- 80% utilization threshold prevents overload failures
- N-1/N-2 contingency analysis catches single points of failure

**Recommendations:**
- Document offline fallback procedures
- Ensure schedule exports (Excel, PDF) work without database connectivity
- Test graceful degradation scenarios

---

## Healthcare Interoperability

### FHIR Scheduling Extensions

**Source:** [FHIR v6.0.0 Schedule Resource](https://build.fhir.org/schedule.html)

**Overview:**
- FHIR defines `Schedule`, `Slot`, and `Appointment` resources
- Profiles and custom extensions available for domain-specific fields
- Healthcare systems increasingly adopting for workflow integration

**Future Opportunity:**
- v2.0+ could expose FHIR-compatible API for EMR integration
- Would enable interoperability with Epic, Cerner, etc.
- Aligns with STRATEGIC_DECISIONS.md consideration of EMR integration

**Status:** Not a priority for v1.x - MyEvaluations integration takes precedence.

---

## iCalendar/Timezone Best Practices

### DST-Safe Recurring Events

**Sources:**
- [RFC 5545 RRULE](https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html)
- [CalConnect Timezone Recommendations](https://standards.calconnect.org/cc/cc-r0602-2006.html)

**Problem:** Recurring meetings can jump an hour at DST transitions.

**Best Practices:**
1. **Use local time + TZID** on DTSTART (not UTC)
2. **Include full VTIMEZONE** component covering all years of the series
3. **Never expand RRULEs in UTC** - expand in local zone
4. **UNTIL must match DTSTART type** - if DTSTART is local with TZID, UNTIL should be UTC

**Safe Pattern:**
```ics
DTSTART;TZID=America/New_York:20250203T090000
RRULE:FREQ=WEEKLY;BYDAY=MO
```

**Relevance:**
- `frontend/src/features/import-export/` - iCalendar export
- STRATEGIC_DECISIONS.md prioritizes "ics/webcal for mobile calendar sync"
- Audit export code for DST handling

---

## AI/LLM Security

### OWASP LLM Top 10 (2025)

**Source:** [OWASP GenAI Security](https://genai.owasp.org/)

**Top Risks:**
1. **Prompt Injection** - May never be fully eliminated; design to contain
2. **Supply Chain/Plugin Risks** - Third-party tools are prime abuse paths
3. **Insecure Output Handling** - Treat LLM output as untrusted
4. **Excessive Agency** - Agents need tight guardrails

**Relevance to Our MCP Infrastructure:**
- Session 9 added 27 MCP tools
- `docs/planning/MCP_INTEGRATION_OPPORTUNITIES.md`
- Apply least-privilege, time-boxed credentials per tool
- Validate/parse LLM responses before they touch code, files, or APIs

**Security Recommendations for MCP Tools:**
1. Use least-privilege, time-boxed credentials per tool
2. Enforce schemas/policies on every function call
3. Sandbox tools; require approvals for effectful actions
4. Maintain allow-lists for domains/connectors
5. Log/replay traces for auditing

---

### Cursor IDE Vulnerabilities (MCPoison, CurXecute)

**Source:** [NVD CVE-2025-54136](https://nvd.nist.gov/vuln/detail/CVE-2025-54136)

**Issue:** Approved MCP configuration files can be silently swapped for malicious commands.

**Relevance:**
- Our MCP server implementation should validate configuration integrity
- Consider signing or checksumming MCP configurations
- Document safe MCP usage practices for developers

---

## References

### ACGME
- [ACGME Common Program Requirements (2025)](https://www.acgme.org/globalassets/pfassets/programrequirements/2025-reformatted-requirements/cprresidency_2025_reformatted.pdf)
- [Summary of Proposed Changes](https://www.acgme.org/programs-and-institutions/programs/common-program-requirements/summary-of-proposed-changes-to-acgme-common-program-requirements-section-vi/)

### Scheduling Research
- [Automated Scheduling Tool Implementation (PLOS ONE)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0236952)
- [Multi-Objective Genetic Algorithm for Healthcare Workforce (arXiv)](https://arxiv.org/abs/2508.20953)

### Healthcare IT
- [AWS Outage Impact on Healthcare (Censinet)](https://censinet.com/perspectives/aws-outage-healthcare-digital-backbone)
- [FHIR Schedule Resource](https://build.fhir.org/schedule.html)

### Security
- [OWASP LLM Top 10](https://genai.owasp.org/)
- [NIST COSAIS Concept Paper](https://csrc.nist.gov/csrc/media/Projects/cosais/documents/NIST-Overlays-SecuringAI-concept-paper.pdf)
- [Cursor IDE Vulnerabilities (Tenable)](https://www.tenable.com/blog/faq-cve-2025-54135-cve-2025-54136-vulnerabilities-in-cursor-curxecute-mcpoison)

### iCalendar Standards
- [RFC 5545 RRULE](https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html)
- [CalConnect Timezone Recommendations](https://standards.calconnect.org/cc/cc-r0602-2006.html)

### Military/Defense
- [FY26 NDAA Summary (Atlantic Council)](https://www.atlanticcouncil.org/dispatches/your-expert-guide-to-the-2026-national-defense-authorization-act/)
- [NDAA Signing (Reuters)](https://www.reuters.com/business/aerospace-defense/trump-expected-sign-1-trillion-annual-defense-bill-2025-12-18/)

### API Best Practices
- [Idempotency Keys in REST APIs (Zuplo)](https://zuplo.com/learning-center/implementing-idempotency-keys-in-rest-apis-a-complete-guide)
- [OpenTelemetry + Prometheus Guide (Grafana)](https://grafana.com/blog/2023/07/20/a-practical-guide-to-data-collection-with-opentelemetry-and-prometheus/)

---

## Action Items Summary

| Priority | Item | Relevant Code | Status |
|----------|------|---------------|--------|
| High | Review ACGME validator against Sept 2025 requirements | `backend/app/scheduling/acgme_validator.py` | Pending |
| High | Audit iCalendar export for DST handling | `frontend/src/features/import-export/` | Pending |
| Medium | Verify solver instrumentation with Prometheus | `backend/app/resilience/metrics.py` | Pending |
| Medium | Review MCP tool security posture | MCP server implementation | Pending |
| Low | Evaluate health/ready endpoints | `backend/app/api/routes/` | Pending |
| Low | Document FHIR opportunity for v2.0+ | `docs/architecture/` | Pending |

---

*This document is auto-generated from external research. Update as new summaries are received.*
