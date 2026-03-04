# Optional Modules Assessment

> **Author:** Claude Code Analysis
> **Date:** 2026-01-18
> **Status:** Draft for CCLU Review
> **Purpose:** Comprehensive inventory of optional/supplementary modules with gap analysis

---

## Executive Summary

This document provides a complete assessment of optional modules that enhance the Residency Scheduler beyond its core functionality. The analysis reveals that **the project is more feature-complete than expected**, with most anticipated optional modules already implemented.

**Key Findings:**
- 18+ optional modules already implemented
- 4 modules identified as missing with high potential value
- FHIR integration deprioritized (2+ year horizon)

---

## Table of Contents

1. [Current Optional Modules](#current-optional-modules)
2. [Missing Modules (Recommended)](#missing-modules-recommended)
3. [Deprioritized Modules](#deprioritized-modules)
4. [Implementation Roadmap](#implementation-roadmap)
5. [Architecture Patterns](#architecture-patterns)

---

## Current Optional Modules

### Tier 1: AI & Intelligence Layer

| Module | Location | Status | Description |
|--------|----------|--------|-------------|
| **MCP Server** | `mcp-server/` | ✅ Active | 29+ AI scheduling tools via Model Context Protocol |
| **pgvector/RAG** | `backend/app/services/embedding_service.py` | ✅ Active | Local embeddings (all-MiniLM-L6-v2), agent memory, document search |
| **Ollama LLM** | `docker-compose.ollama.yml` | ✅ Available | Local LLM inference (llama3.2, mistral) - HIPAA-compliant, no cloud dependency |
| **ML Scoring** | `backend/app/core/config.py` | ⚙️ Configurable | Preference prediction, conflict detection, workload optimization (disabled by default) |

### Tier 2: Observability & Monitoring

| Module | Location | Status | Description |
|--------|----------|--------|-------------|
| **OpenTelemetry** | Backend config | ✅ Configurable | Distributed tracing with Jaeger/Zipkin support |
| **Prometheus** | `monitoring/` | ✅ Separate compose | Metrics collection and alerting |
| **Grafana** | `monitoring/` | ✅ Separate compose | Visualization dashboards |
| **Loki + Promtail** | `monitoring/` | ✅ Separate compose | Log aggregation and search |
| **Node/cAdvisor Exporters** | `monitoring/` | ✅ Separate compose | Host and container metrics |

### Tier 3: Integration & Export

| Module | Location | Status | Description |
|--------|----------|--------|-------------|
| **iCal/Webcal Sync** | `backend/app/api/routes/calendar.py` | ✅ Complete | Full webcal subscription system with token-based feeds |
| **PDF Reports** | `backend/app/services/reports/pdf_generator.py` | ✅ Complete | ReportLab-based generator with TOC, headers/footers |
| **Webhook System** | `backend/app/webhooks/` | ✅ Complete | Event subscriptions, delivery retry, dead letter queue |
| **Email Notifications** | `backend/app/notifications/channels_core.py` | ✅ Complete | SMTP via Celery with templating |
| **Excel Import/Export** | `backend/app/services/` | ✅ Complete | XLSX parsing for schedule data |

### Tier 4: Development & Testing

| Module | Location | Status | Description |
|--------|----------|--------|-------------|
| **K6 Load Testing** | `load-tests/` | ✅ Available | Performance testing with multiple scenarios |
| **Slack Bot** | `slack-bot/` | ✅ Available | Claude Code bridge for interactive development |
| **Shadow Traffic** | Backend config | ⚙️ Configurable | A/B testing via request duplication |

### Tier 5: Infrastructure

| Module | Location | Status | Description |
|--------|----------|--------|-------------|
| **Nginx + SSL** | `nginx/` | ✅ Available | Reverse proxy with Let's Encrypt |
| **S3 Storage Backend** | Backend config | ⚙️ Configurable | Cloud storage for uploads (default: local) |
| **Virus Scanning** | Backend config | ⚙️ Configurable | ClamAV integration for uploads |

### Tier 6: Disabled/Pending

| Module | Location | Status | Reason |
|--------|----------|--------|--------|
| **n8n Workflows** | `n8n/` | ⚠️ Disabled | CVE-2026-21858 (Ni8mare RCE) - awaiting patch |

---

## Missing Modules (Recommended)

### 1. Feature Flag System

**Priority:** HIGH
**Effort:** Medium (2-3 days)
**Value:** Safe rollouts of scheduling algorithm changes

**Problem Solved:**
- Currently no way to gradually roll out solver changes
- New constraint logic is all-or-nothing deployment
- No kill-switch for problematic features

**Recommended Options:**

| Tool | Type | Pros | Cons |
|------|------|------|------|
| [GrowthBook](https://www.growthbook.io) | Open Source | Self-hosted, A/B testing built-in | Requires setup |
| [Unleash](https://www.getunleash.io) | Open Source | Data sovereignty, lightweight | Less analytics |
| [OpenFeature](https://openfeature.dev) | Standard | Vendor-agnostic SDK | Need separate backend |

**Suggested Implementation:**
```python
# backend/app/core/config.py
FEATURE_FLAGS_ENABLED: bool = False
FEATURE_FLAGS_PROVIDER: str = "growthbook"  # or "unleash", "openfeature"
FEATURE_FLAGS_API_KEY: str = ""
FEATURE_FLAGS_REFRESH_INTERVAL: int = 60  # seconds
```

**Use Cases:**
- Roll out "solver v2" to 10% of schedule generations
- A/B test new UI components
- Kill-switch for experimental resilience features
- Gradual migration to new constraint engine

---

### 2. SMS/Pager Notifications (Twilio)

**Priority:** HIGH
**Effort:** Low (1 day)
**Value:** Critical for medical on-call workflows

**Problem Solved:**
- Medical environments still rely on pagers and SMS
- Email alone is insufficient for urgent notifications
- On-call residents need immediate swap/coverage alerts

**Implementation Approach:**

The notification channel abstraction already exists. Add `SmsChannel`:

```python
# backend/app/notifications/channels/sms.py
class SmsChannel(NotificationChannel):
    """SMS delivery via Twilio."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number

    async def deliver(self, payload: NotificationPayload) -> DeliveryResult:
        # Get recipient phone from user profile
        # Send via Twilio API
        # Return result
```

**Configuration:**
```python
# backend/app/core/config.py
SMS_ENABLED: bool = False
SMS_PROVIDER: str = "twilio"  # or "aws_sns"
TWILIO_ACCOUNT_SID: str = ""
TWILIO_AUTH_TOKEN: str = ""
TWILIO_FROM_NUMBER: str = ""
```

**Use Cases:**
- Swap request notifications
- Emergency coverage alerts
- 24-hour on-call reminders
- Escalation chains (if no response, notify backup)

---

### 3. SSO/SAML Integration

**Priority:** MEDIUM (High for DoD deployment)
**Effort:** High (1-2 weeks)
**Value:** Enterprise authentication, CAC support

**Problem Solved:**
- Military environments require CAC (Common Access Card) authentication
- Hospital systems use enterprise SSO (Okta, Azure AD, etc.)
- Currently only local username/password auth

**Recommended Libraries:**
- `python-saml` or `pysaml2` for SAML 2.0
- `authlib` for OAuth2/OIDC

**Configuration:**
```python
# backend/app/core/config.py
SSO_ENABLED: bool = False
SSO_PROVIDER: str = "saml"  # or "oidc"
SAML_METADATA_URL: str = ""
SAML_ENTITY_ID: str = ""
SAML_ACS_URL: str = ""
```

**Considerations:**
- Requires coordination with IT security team
- Certificate management complexity
- User provisioning/deprovisioning workflows
- Role mapping from IdP groups

---

### 4. Flower (Celery Dashboard)

**Priority:** MEDIUM
**Effort:** Very Low (1 hour)
**Value:** Background job visibility

**Problem Solved:**
- No visibility into Celery task queue status
- Debugging failed tasks requires log diving
- Can't monitor task throughput or latency

**Implementation:**

Add to `docker-compose.yml`:
```yaml
flower:
  image: mher/flower:2.0
  command: celery --broker=redis://redis:6379/0 flower --port=5555
  ports:
    - "5555:5555"
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - FLOWER_BASIC_AUTH=${FLOWER_USER}:${FLOWER_PASSWORD}
  depends_on:
    - redis
    - celery-worker
  profiles:
    - monitoring
```

**Security Note:** Always enable basic auth or restrict to internal network.

---

## Deprioritized Modules

### FHIR/HL7 Integration

**Status:** Deprioritized (2+ year horizon)
**Rationale:**
- Requirements unclear until specific EHR target identified
- Standards evolving (FHIR R5 emerging)
- Implementation now risks building wrong thing
- High effort with no immediate user value

**Recommendation:** Design data models to be FHIR-compatible (already satisfied). Defer implementation until:
1. Specific EHR integration requirement identified (MHS GENESIS, Epic, Cerner)
2. Interface specification provided by hospital IT
3. Compliance requirements clarified

### GraphQL API

**Status:** Not recommended currently
**Rationale:**
- REST API is sufficient for current UI needs
- Adds complexity without clear benefit
- TanStack Query handles data fetching well

### Multi-Tenancy

**Status:** Future consideration
**Rationale:**
- Solve for one program first
- Architectural complexity significant
- Data isolation requirements need specification

### Mobile Push Notifications (FCM/APNs)

**Status:** Blocked on mobile app
**Rationale:**
- No mobile app exists yet
- SMS covers urgent notification use case
- Implement when mobile app is developed

---

## Implementation Roadmap

### Phase 1: Quick Wins (Week 1)

| Task | Effort | Owner | Notes |
|------|--------|-------|-------|
| Add Flower to docker-compose | 1 hour | DevOps | Use monitoring profile |
| Create feature flag config stubs | 2 hours | Backend | No provider yet, just config |

### Phase 2: High-Value Additions (Weeks 2-3)

| Task | Effort | Owner | Notes |
|------|--------|-------|-------|
| Integrate GrowthBook/Unleash | 2 days | Backend | Start with solver flags |
| Add SMS channel (Twilio) | 1 day | Backend | Extend notification system |
| Create SMS templates | 0.5 days | Backend | Swap, coverage, reminder |

### Phase 3: Enterprise Features (When Required)

| Task | Effort | Owner | Notes |
|------|--------|-------|-------|
| SSO/SAML integration | 1-2 weeks | Backend + Security | Requires IdP coordination |
| CAC authentication | 1 week | Backend + Security | DoD-specific |

---

## Architecture Patterns

### Docker Compose Overlay Pattern

The project follows a clean separation of optional modules via compose file overlays:

```
docker-compose.yml           # Core stack (required)
docker-compose.local.yml     # Development overrides
docker-compose.ollama.yml    # Local LLM
docker-compose.k6.yml        # Load testing
docker-compose.monitoring.yml # Observability stack
```

**Recommendation:** Continue this pattern for new modules:
```
docker-compose.flower.yml    # Celery dashboard
docker-compose.growthbook.yml # Feature flags (if self-hosted)
```

### Configuration Pattern

All optional features use environment-variable toggles with sensible defaults:

```python
# Pattern: FEATURE_ENABLED + FEATURE_* settings
SMS_ENABLED: bool = False
SMS_PROVIDER: str = "twilio"
SMS_FROM_NUMBER: str = ""
```

### Notification Channel Pattern

New notification channels should follow the existing abstraction:

```python
class NotificationChannel(ABC):
    @abstractmethod
    async def deliver(self, payload: NotificationPayload) -> DeliveryResult:
        pass
```

Register in `AVAILABLE_CHANNELS` dict for dynamic selection.

---

## Appendix: Module Inventory Summary

### By Status

| Status | Count | Examples |
|--------|-------|----------|
| ✅ Active/Complete | 14 | MCP, RAG, iCal, PDF, Webhooks |
| ⚙️ Configurable | 5 | ML Scoring, Shadow Traffic, S3 |
| ✅ Available (separate compose) | 6 | Prometheus, Grafana, K6, Ollama |
| ⚠️ Disabled | 1 | n8n (CVE) |
| ❌ Missing (recommended) | 4 | Feature Flags, SMS, SSO, Flower |
| 🔮 Future/Deprioritized | 4 | FHIR, GraphQL, Multi-tenancy, Mobile Push |

### By Effort to Implement

| Effort | Modules |
|--------|---------|
| Very Low (< 1 day) | Flower |
| Low (1-2 days) | SMS/Twilio |
| Medium (3-5 days) | Feature Flags |
| High (1-2 weeks) | SSO/SAML |
| Very High (1+ month) | FHIR, Multi-tenancy |

---

## Review Checklist

- [ ] Confirm feature flag priority and provider selection
- [ ] Validate SMS requirement for go-live
- [ ] Clarify SSO timeline based on deployment target
- [ ] Approve Flower addition to monitoring profile
- [ ] Confirm FHIR deprioritization is acceptable

---

*Document generated by Claude Code analysis. Last updated: 2026-01-18*
