# Kubernetes Evaluation for Residency Scheduler

> **Date:** 2025-12-25
> **Purpose:** Evaluate whether Kubernetes is necessary for airgapped resilience vs DOD-wide scaling
> **TL;DR:** Docker Compose for airgapped 10-year, Kubernetes via Platform One for DOD-wide

---

## Executive Summary

| Scenario | Recommendation | Rationale |
|----------|----------------|-----------|
| **Airgapped 10-year** | Docker Compose | Simplicity wins for long-term maintainability |
| **DOD-wide scaling** | Kubernetes (Platform One) | Required for HA, auto-scaling, multi-site |
| **Current state** | Keep Docker Compose | Works perfectly, don't add complexity |

**The codebase is already Kubernetes-ready** - it just doesn't need Kubernetes yet.

---

## What You Already Have (Current State)

### Infrastructure

```
Current Architecture (Docker Compose)
┌─────────────────────────────────────────────────────────────────┐
│  Single Server (or laptop)                                       │
│                                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ Backend │  │ Frontend│  │ Celery  │  │ Celery  │            │
│  │ FastAPI │  │ Next.js │  │ Worker  │  │ Beat    │            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │            │            │            │                  │
│  ┌────▼────────────▼────────────▼────────────▼────┐            │
│  │                  Nginx Proxy                    │            │
│  └────────────────────┬────────────────────────────┘            │
│                       │                                         │
│  ┌─────────┐  ┌───────▼──┐  ┌─────────┐                        │
│  │ Postgres│  │  Redis   │  │   n8n   │                        │
│  │   15    │  │    7     │  │  (opt)  │                        │
│  └─────────┘  └──────────┘  └─────────┘                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────┐            │
│  │           MCP Server (29+ AI tools)             │            │
│  └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘

✓ Health checks
✓ Auto-restart (restart: unless-stopped)
✓ Volume persistence
✓ Network isolation
✓ Environment configuration
```

### Application-Level Resilience (Already Built)

Your codebase has **4 tiers of resilience** at the **application layer**:

| Tier | Concepts | Status |
|------|----------|--------|
| **Tier 1 - Core** | 80% utilization threshold, N-1/N-2 contingency, Defense in Depth, Static Stability, Sacrifice Hierarchy | ✅ Implemented |
| **Tier 2 - Strategic** | Homeostasis, Blast Radius Isolation, Le Chatelier Equilibrium | ✅ Implemented |
| **Tier 3 - Tactical** | SPC Monitoring, Process Capability (Cp/Cpk), Burnout Epidemiology, Erlang C Coverage, Seismic Detection, Fire Index | ✅ Implemented |
| **Tier 4 - Exotic** | Transcription Factor Scheduler, Cellular Automata | ✅ Implemented |

**This is application/scheduling resilience, not infrastructure resilience.**

Kubernetes would add **infrastructure resilience** (container orchestration), but your **scheduling resilience** is already exceptional.

---

## Scenario 1: Airgapped 10-Year Resilience

### What "10-Year Airgapped" Means

```
Requirements:
- No internet access (ever)
- Single site deployment
- Minimal IT support (new PD every 2-3 years)
- Must survive on whatever hardware is available
- Self-healing without external dependencies
```

### Why Docker Compose Wins for Airgapped

| Factor | Docker Compose | Kubernetes |
|--------|----------------|------------|
| **Complexity** | 1 config file | 50+ YAML files |
| **Learning curve** | 1 day | 2 weeks |
| **Ops knowledge** | Basic Docker | Full SRE skillset |
| **Dependencies** | Docker only | k8s + etcd + container runtime |
| **Version EOL** | Docker stable 5+ years | k8s EOL every 12-15 months |
| **Recovery from failure** | `docker-compose up -d` | Complex cluster recovery |
| **Data persistence** | Simple volumes | PVCs, StorageClasses |
| **Upgrades** | Pull new images | Rolling deployments, CRDs |
| **Debugging** | `docker logs` | kubectl + complex networking |
| **Single-node** | Native | Needs k3s or microk8s |

### What Kubernetes Adds (For Airgapped)

| Feature | Docker Compose Alternative | Airgap Value |
|---------|---------------------------|--------------|
| Auto-restart crashed containers | `restart: unless-stopped` | Already have |
| Health checks | `healthcheck:` in compose | Already have |
| Load balancing | Single server = N/A | Not needed |
| Auto-scaling | Single server = N/A | Not needed |
| Multi-node HA | Not supported | Overkill for single-site |
| Service mesh | Not needed | Overkill for single-site |

### Kubernetes Risk for Airgapped

```
Kubernetes Version Lifecycle:
┌────────────────────────────────────────────────────────────────┐
│ Year 1-2: v1.28 - Supported                                    │
│ Year 2-3: v1.28 - No longer supported, security patches stop   │
│ Year 3-5: v1.28 - Breaking API changes accumulate              │
│ Year 5+:  v1.28 - Container images may not run on old k8s      │
│                                                                │
│ Problem: Kubernetes requires regular updates to stay secure     │
│ Airgapped: Cannot download updates                             │
│ Result: Either vulnerable or requires complex offline patching │
└────────────────────────────────────────────────────────────────┘

Docker Version Lifecycle:
┌────────────────────────────────────────────────────────────────┐
│ Year 1-10: Docker 24.x - Still works                           │
│                                                                │
│ Docker is much more stable for long-term deployment.           │
│ Container images run on any Docker version (backwards compat). │
└────────────────────────────────────────────────────────────────┘
```

### Verdict: Airgapped 10-Year

**Recommendation: Docker Compose**

```
Keep your current setup:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  docker-compose.yml + docker-compose.prod.yml                   │
│                                                                  │
│  + Airgap enhancements from AIRGAP_READINESS_AUDIT.md:          │
│    - .env.airgap.example                                        │
│    - Offline package mirror                                     │
│    - Pre-built Docker images                                    │
│    - PD handoff guide                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Scenario 2: DOD-Wide Scaling

### What "DOD-Wide" Means

```
Requirements:
- Thousands of users across multiple sites
- 99.9%+ uptime (mission critical)
- Multi-region deployment
- Match season traffic spikes (10x load)
- FedRAMP compliance
- IL4/IL5 security
- Audit everything
- Zero-downtime deployments
```

### Why Kubernetes Wins for DOD-Wide

| Requirement | Docker Compose | Kubernetes |
|-------------|----------------|------------|
| **High Availability** | Manual replication | Native (Pod replicas) |
| **Auto-scaling** | Not supported | HPA, VPA, Cluster Autoscaler |
| **Multi-site** | Manual sync | Federation, GitOps |
| **Zero-downtime deploy** | Manual blue/green | Rolling updates native |
| **Self-healing** | Restart only | Full pod/node recovery |
| **Secret management** | .env files | Sealed Secrets, Vault |
| **Service mesh** | Not supported | Istio, Linkerd |
| **Monitoring** | Manual | Prometheus Operator |
| **FedRAMP** | Self-managed | Platform One is authorized |

### DOD Has Kubernetes Infrastructure Already

```
DOD Kubernetes Ecosystem:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Platform One (https://p1.dso.mil/)                             │
│  ├── Big Bang (Kubernetes distribution)                         │
│  │   ├── Istio (service mesh)                                   │
│  │   ├── Keycloak (SSO)                                         │
│  │   ├── Elasticsearch/Kibana (logging)                         │
│  │   ├── Prometheus/Grafana (monitoring)                        │
│  │   └── ArgoCD (GitOps)                                        │
│  │                                                               │
│  └── Iron Bank (hardened container registry)                    │
│      └── Pre-approved, security-scanned images                  │
│                                                                  │
│  Already FedRAMP authorized, IL4/IL5 ready                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

You don't have to build/operate Kubernetes yourself.
Platform One teams handle infrastructure.
You just provide Helm charts + container images.
```

### What You'd Need for DOD-Wide

```
To deploy on Platform One, you'd add:

1. Helm Charts
   helm/
   ├── Chart.yaml
   ├── values.yaml
   ├── templates/
   │   ├── deployment.yaml
   │   ├── service.yaml
   │   ├── ingress.yaml
   │   ├── configmap.yaml
   │   ├── secret.yaml
   │   └── hpa.yaml
   └── values-prod.yaml

2. Iron Bank Container Images
   - Submit to Iron Bank for security scanning
   - Use Iron Bank base images
   - Get approval for deployment

3. GitOps Configuration (ArgoCD)
   gitops/
   ├── apps/
   │   └── residency-scheduler.yaml
   └── base/
       └── kustomization.yaml
```

### Architecture for DOD-Wide

```
DOD-Wide Kubernetes Architecture
┌─────────────────────────────────────────────────────────────────┐
│                       Platform One                               │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Istio Service Mesh                        ││
│  │                                                              ││
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       ││
│  │  │ Backend │  │ Backend │  │ Backend │  │ Backend │       ││
│  │  │ Pod 1   │  │ Pod 2   │  │ Pod 3   │  │ Pod N   │       ││
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       ││
│  │       │            │            │            │              ││
│  │  ┌────▼────────────▼────────────▼────────────▼────┐       ││
│  │  │              Backend Service                    │       ││
│  │  │         (Load Balancer + Health)               │       ││
│  │  └─────────────────────┬───────────────────────────┘       ││
│  │                        │                                    ││
│  │  ┌─────────────────────▼───────────────────────────┐       ││
│  │  │         PostgreSQL StatefulSet (HA)              │       ││
│  │  │  Primary ──► Replica ──► Replica                │       ││
│  │  └──────────────────────────────────────────────────┘       ││
│  │                                                              ││
│  │  ┌──────────────────────────────────────────────────┐       ││
│  │  │         Redis Cluster (HA)                        │       ││
│  │  │  Master ──► Replica ──► Replica                  │       ││
│  │  └──────────────────────────────────────────────────┘       ││
│  │                                                              ││
│  │  ┌──────────────────────────────────────────────────┐       ││
│  │  │         Auto-scaling                              │       ││
│  │  │  Normal: 3 pods  │  Peak: 10 pods                │       ││
│  │  │  CPU > 70% ──► Scale up                          │       ││
│  │  │  CPU < 30% ──► Scale down                        │       ││
│  │  └──────────────────────────────────────────────────┘       ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Verdict: DOD-Wide

**Recommendation: Kubernetes via Platform One**

```
Deploy through Platform One Big Bang:
- Don't build your own k8s cluster
- Use existing DOD infrastructure
- Get FedRAMP/IL4/IL5 for free
- Focus on your app, not infra

Required work:
1. Create Helm charts (1-2 weeks)
2. Submit images to Iron Bank (2-4 weeks approval)
3. Configure GitOps for ArgoCD (1 week)
4. Security review for ATO (ongoing)
```

---

## Comparison Matrix

| Factor | Docker Compose | Kubernetes |
|--------|----------------|------------|
| **Best for** | Single-site, small team | Multi-site, enterprise |
| **Complexity** | Low | High |
| **Ops overhead** | Minimal | Significant |
| **Airgapped** | Excellent | Difficult |
| **10-year survival** | High confidence | Low confidence |
| **Auto-scaling** | No | Yes |
| **Multi-site** | No | Yes |
| **Self-healing** | Basic (restart) | Full (pod/node) |
| **Zero-downtime** | Manual | Native |
| **Learning curve** | 1 day | 2 weeks |
| **DOD ready** | Manual work | Platform One |

---

## What You Already Have That's "Kubernetes-Ready"

Your codebase is **already Kubernetes-compatible**:

### 1. Health Endpoints

```python
# backend/app/api/routes/health.py
@router.get("/health")        # Liveness probe
@router.get("/health/ready")  # Readiness probe
@router.get("/health/live")   # Kubernetes-style
```

Kubernetes uses these for:
- **Liveness probe**: Container alive? (restart if not)
- **Readiness probe**: Ready for traffic? (remove from service if not)

### 2. Configuration via Environment

```bash
# All config via environment variables
DATABASE_URL=...
REDIS_URL=...
SECRET_KEY=...
```

Kubernetes ConfigMaps and Secrets map directly to env vars.

### 3. Stateless Backend

```
Backend containers are stateless:
- No local file storage (uses DB)
- Session state in Redis
- Any pod can handle any request
```

This is ideal for Kubernetes horizontal scaling.

### 4. Resource Definitions (Docker Compose)

```yaml
# Already defined in docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
        reservations:
          memory: 512M
```

These translate directly to Kubernetes resource specs.

### 5. Graceful Shutdown

Your FastAPI app handles SIGTERM gracefully, allowing Kubernetes pod termination.

---

## Recommendations by Timeline

### Now (Keep Docker Compose)

```
Current state: Perfect for single-site deployment
- Don't add Kubernetes complexity
- Focus on completing airgap readiness (from audit)
- Maintain application-level resilience

Action items:
✓ Keep docker-compose.yml
✓ Complete .env.airgap.example
✓ Build offline package mirror
✓ Write PD handoff guide
```

### If Single-Site Grows (Still Docker Compose)

```
Scale to 100-500 users at one hospital:
- Docker Compose still sufficient
- Add manual horizontal scaling (multiple servers)
- Consider Docker Swarm if needed (same compose files)

Action items:
□ Document manual scaling procedure
□ Add HAProxy for load balancing
□ PostgreSQL replication (streaming)
```

### If DOD-Wide (Move to Kubernetes)

```
Scale to thousands of users across DOD:
- Use Platform One/Big Bang
- Submit to Iron Bank
- Implement GitOps with ArgoCD

Action items:
□ Create Helm charts
□ Iron Bank image approval
□ ArgoCD configuration
□ Multi-site data replication strategy
□ Update distributed systems research implementation
```

---

## The "But What If" Questions

### "What if the single server dies?"

**With Docker Compose:**
- Restore from backup to new server
- `docker-compose up -d`
- Time: 1-2 hours manual work

**With Kubernetes:**
- Need multi-node cluster first
- Pod automatically reschedules to healthy node
- Time: 2-5 minutes automatic

**Verdict:** For airgapped single-site, 1-2 hour recovery is acceptable. The complexity cost of Kubernetes doesn't justify faster recovery.

### "What if traffic spikes during match season?"

**With Docker Compose:**
- Pre-provision extra capacity (known spike timing)
- Manual scale-out if needed

**With Kubernetes:**
- HPA auto-scales based on CPU/memory
- Automatic response to traffic

**Verdict:** Match season is predictable (March). Pre-provision for Docker Compose. Auto-scale only valuable for unpredictable spikes.

### "What if we need multi-site eventually?"

**With Docker Compose:**
- Each site runs independent instance
- Manual synchronization (if needed)
- Works for loosely-coupled sites

**With Kubernetes:**
- Federation across clusters
- Global service mesh
- Strong consistency options

**Verdict:** If you need multi-site with strong consistency, Kubernetes makes sense. But your distributed systems research shows application-layer solutions (Byzantine consensus, Raft) that work at the app layer, not infra layer.

---

## Summary

### For Your Current Goal (10-Year Airgapped)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  RECOMMENDATION: DOCKER COMPOSE                                 │
│                                                                  │
│  Reasons:                                                        │
│  1. Simpler = more maintainable over 10 years                   │
│  2. Lower ops knowledge required (new PD every 2-3 years)       │
│  3. More stable across versions                                 │
│  4. Easier airgap packaging                                     │
│  5. Application resilience is already exceptional               │
│                                                                  │
│  Kubernetes adds infrastructure resilience you don't need       │
│  for single-site deployment.                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### For Future Goal (DOD-Wide)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  RECOMMENDATION: KUBERNETES VIA PLATFORM ONE                    │
│                                                                  │
│  Reasons:                                                        │
│  1. DOD already has k8s infrastructure (Platform One)           │
│  2. FedRAMP/IL4/IL5 compliance built-in                         │
│  3. Auto-scaling for 10x traffic spikes                         │
│  4. Multi-site deployment native                                │
│  5. Zero-downtime deployments                                   │
│                                                                  │
│  Don't build your own k8s - use DOD's Platform One.             │
│                                                                  │
│  Prep work (do when DOD-wide confirmed):                        │
│  □ Create Helm charts                                           │
│  □ Submit to Iron Bank                                          │
│  □ Configure ArgoCD                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The Dual-Track Strategy

Your codebase can support both scenarios:

```
                    ┌─────────────────┐
                    │  Your Codebase  │
                    │  (Same code!)   │
                    └────────┬────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                 │
   ┌────────▼────────┐               ┌───────▼────────┐
   │  Docker Compose │               │   Helm Charts  │
   │   (Airgapped)   │               │  (Platform 1)  │
   └─────────────────┘               └────────────────┘
            │                                 │
   ┌────────▼────────┐               ┌───────▼────────┐
   │  Single-Site    │               │   DOD-Wide     │
   │  10-Year        │               │   Scaling      │
   └─────────────────┘               └────────────────┘

Same application, different deployment targets.
No code changes required.
```

---

## Next Steps

### Immediate (This Sprint)
1. Complete airgap readiness items from AIRGAP_READINESS_AUDIT.md
2. No Kubernetes work needed

### When DOD-Wide Confirmed
1. Create Helm chart scaffolding
2. Begin Iron Bank submission process
3. Contact Platform One team for onboarding

### References
- [Platform One](https://p1.dso.mil/)
- [Iron Bank](https://ironbank.dso.mil/)
- [Big Bang](https://repo1.dso.mil/big-bang/bigbang)
- [ArgoCD](https://argoproj.github.io/cd/)

---

## Appendix: DOD Platform Ecosystem (2025)

> **Updated:** December 2025
> **Purpose:** Deep dive into DOD platforms relevant for enterprise scheduling deployment

### DOD AI & Deployment Landscape

The DOD has rapidly matured its AI and DevSecOps ecosystem. For a scheduling application going DOD-wide, understanding these platforms is critical.

```
DOD Platform Ecosystem (December 2025)
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    USER-FACING AI PLATFORMS                      │   │
│  │                                                                  │   │
│  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │   │
│  │  │  GenAI.mil   │     │  Ask Sage    │     │  DHA AI      │    │   │
│  │  │  (Google     │     │  (IL5/IL6    │     │  (Healthcare │    │   │
│  │  │   Gemini)    │     │   Multi-LLM) │     │   specific)  │    │   │
│  │  │              │     │              │     │              │    │   │
│  │  │  3M users    │     │  Army-wide   │     │  PHI-approved│    │   │
│  │  │  IL5         │     │  FedRAMP High│     │  MHS         │    │   │
│  │  └──────────────┘     └──────────────┘     └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    DEPLOYMENT INFRASTRUCTURE                     │   │
│  │                                                                  │   │
│  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │   │
│  │  │ Platform One │     │  Iron Bank   │     │   ArgoCD     │    │   │
│  │  │  Big Bang    │     │  (Hardened   │     │   (GitOps)   │    │   │
│  │  │  (k8s)       │     │   Images)    │     │              │    │   │
│  │  │              │     │              │     │              │    │   │
│  │  │  cATO ready  │     │  1,800+      │     │  Continuous  │    │   │
│  │  │  IL2-IL6     │     │  containers  │     │  Delivery    │    │   │
│  │  └──────────────┘     └──────────────┘     └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### GenAI.mil - Pentagon's Enterprise AI Platform

**Official Launch:** December 9, 2025

> "For the first time ever, by the end of this week, 3 million employees, warfighters, and contractors are going to have AI on their desktop, every single one."
> — Emil Michael, Pentagon Chief Technology Officer

#### Overview

| Aspect | Details |
|--------|---------|
| **URL** | GenAI.mil (CAC required) |
| **Users** | 3 million DOD personnel |
| **Initial Model** | Google Gemini for Government |
| **Security Level** | IL-5 (highly sensitive unclassified) |
| **Future Models** | Anthropic, xAI, OpenAI planned |

#### Key Features

- **Deep Research**: Complex analysis tasks
- **Document Formatting**: Automated report generation
- **Video/Image Analysis**: Multi-modal capabilities
- **RAG + Web Grounding**: Reduces hallucinations via Google Search grounding
- **Data Isolation**: DOD data never trains public models

#### Relevance for Residency Scheduler

```
Integration Opportunity:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Residency Scheduler + GenAI.mil                                │
│                                                                  │
│  Current: MCP Server (29+ tools) for Claude/local AI            │
│                                                                  │
│  Future DOD-wide: Could integrate with GenAI.mil for:           │
│  - Schedule analysis ("Why is Dr. Smith overloaded?")           │
│  - ACGME compliance explanations                                │
│  - Natural language schedule queries                            │
│  - Report generation                                            │
│                                                                  │
│  BUT: Your MCP server already does this locally.                │
│  GenAI.mil is for GENERAL AI tasks, not domain-specific.        │
│  Your specialized scheduling AI > generic GenAI.mil for this.   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Sources:**
- [Pentagon rolls out GenAI platform - Breaking Defense](https://breakingdefense.com/2025/12/pentagon-rolls-out-genai-platform-to-all-personnel-using-googles-gemini/)
- [Google Cloud Powers GenAI.mil](https://www.googlecloudpresscorner.com/2025-12-09-Chief-Digital-and-Artificial-Intelligence-Office-Selects-Google-Clouds-AI-to-Power-GenAI-mil)
- [DOD GenAI.mil Platform - DefenseScoop](https://defensescoop.com/2025/12/09/genai-mil-platform-dod-commercial-ai-models-agentic-tools-google-gemini/)

---

### Ask Sage - FedRAMP High / IL5-IL6 Authorized GenAI

**Status:** Most mature DOD-authorized GenAI platform (as of Dec 2025)

#### Key Achievements

| Metric | Value |
|--------|-------|
| **Army Contract** | $49M / 5 years (Project Athena) |
| **CDAO Partnership** | $10M first year |
| **Security Levels** | FedRAMP High, IL5, IL6, Top Secret |
| **Model Support** | 150+ models (model-agnostic) |
| **PHI Approved** | First and only IL5 GenAI for PHI |

#### Demonstrated Results (Army)

| Capability | Improvement |
|------------|-------------|
| **Coding Speed** | 35x faster |
| **Acquisition Tasks** | 50x productivity |
| **Personnel Reclassification** | 300,000 records in 1 week (saved 50,000 hours) |
| **Document Analysis** | Thousands in minutes vs days |

#### Defense Health Agency Partnership

> **December 8, 2025:** Ask Sage announced enterprise-wide agreement with DHA

This is **directly relevant** for Residency Scheduler:

```
Ask Sage + DHA Integration
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Ask Sage is the ONLY IL5-authorized GenAI approved for PHI     │
│                                                                  │
│  DHA Use Cases:                                                  │
│  - Clinical workflows                                            │
│  - Operational planning                                          │
│  - Administrative automation                                     │
│  - Military Health System innovation                             │
│                                                                  │
│  Residency Scheduling IS an administrative/operational          │
│  workflow within DHA context.                                    │
│                                                                  │
│  Potential: If DOD-wide, could deploy via DHA's Ask Sage        │
│  infrastructure rather than building separate AI integration.   │
│                                                                  │
│  Your MCP Server tools could be exposed through Ask Sage's      │
│  multi-modal architecture.                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Edge AI Capability

Ask Sage Edge enables:
- **Disconnected Operations**: Works without network
- **Zero-Trust Architecture**: Government-grade security
- **150+ AI Models**: Local model selection
- **Cloud Agnostic**: Any cloud or on-premise

**This aligns with your airgapped requirement!** Ask Sage Edge could be a DOD-approved alternative to local MCP server for airgapped sites.

**Sources:**
- [Ask Sage + DOD CDAO Partnership](https://www.asksage.ai/press-releases/ask-sage-partners-with-dod-cdao-and-u-s-army-to-provide-unlimited-access-to-generative-ai-across-combatant-commands-joint-staff-and-office-of-the-secretary-of-defense)
- [Ask Sage IL5 with Microsoft](https://www.asksage.ai/press-releases/ask-sage-announces-generative-ai-army-enterprise-offering-at-il5-in-collaboration-with-microsoft)
- [Ask Sage + DHA Launch](https://www.globenewswire.com/news-release/2025/12/08/3201787/0/en/Ask-Sage-and-the-Defense-Health-Agency-Launch-Enterprise-Wide-Generative-AI-Offering-to-Accelerate-Military-Health-Innovation.html)
- [Pentagon Awards Ask Sage $10M - Breaking Defense](https://breakingdefense.com/2025/06/pentagon-ai-office-army-award-ask-sage-10m-for-genai-expansion/)

---

### Platform One & Big Bang - Deep Dive

#### What Big Bang Actually Is

```
Big Bang Architecture
┌─────────────────────────────────────────────────────────────────────────┐
│  Big Bang = Helm Chart of Helm Charts                                   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  CORE PACKAGES (Required by DevSecOps Reference Architecture)   │   │
│  │                                                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │  Istio   │  │ Gatekeeper│  │   ECK    │  │Prometheus│       │   │
│  │  │ (Mesh)   │  │ (Policy)  │  │(Logging) │  │(Metrics) │       │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  │                                                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │   │
│  │  │ Twistlock│  │ Kiali    │  │ Jaeger   │                      │   │
│  │  │(Runtime) │  │(Observ)  │  │(Tracing) │                      │   │
│  │  └──────────┘  └──────────┘  └──────────┘                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ADDONS (Optional - Enable as needed)                           │   │
│  │                                                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │ ArgoCD   │  │ GitLab   │  │ Keycloak │  │ Vault    │       │   │
│  │  │(GitOps)  │  │(CI/CD)   │  │  (SSO)   │  │(Secrets) │       │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  │                                                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │ Mattermost│ │  MinIO   │  │ Anchore  │  │ Sonarqube│       │   │
│  │  │  (Chat)  │  │(Storage) │  │(Security)│  │(Quality) │       │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  YOUR APPLICATION                                                │   │
│  │                                                                  │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │  Residency Scheduler (Helm Chart)                        │  │   │
│  │  │  - Backend pods (FastAPI)                                │  │   │
│  │  │  - Frontend pods (Next.js)                               │  │   │
│  │  │  - Celery workers                                        │  │   │
│  │  │  - PostgreSQL StatefulSet                                │  │   │
│  │  │  - Redis                                                 │  │   │
│  │  │  - MCP Server (optional)                                 │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Big Bang Deployment Options

| Environment | Description | Your Use Case |
|-------------|-------------|---------------|
| **Cloud** | AWS GovCloud, Azure Gov | DOD-wide internet-connected |
| **On-Premise** | Own hardware | Large MTF with IT staff |
| **Airgapped** | Disconnected/SCIF | Classified or isolated networks |
| **Edge** | Tactical/forward deployed | Not applicable for scheduling |

**Key Insight:** Big Bang supports airgapped deployment! This could be an alternative to Docker Compose for airgapped sites that want enterprise features.

#### Continuous ATO (cATO) Benefits

```
Traditional ATO vs cATO
┌────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  Traditional ATO:                                                       │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Build App → 12-18 month ATO process → Deploy → Repeat         │   │
│  │                                                                 │   │
│  │  Problem: By the time you're authorized, app is outdated       │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  cATO with Platform One:                                                │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Big Bang provides baseline cATO                                │   │
│  │  ↓                                                              │   │
│  │  Your app inherits security posture                            │   │
│  │  ↓                                                              │   │
│  │  Focus on YOUR app's security, not infrastructure              │   │
│  │  ↓                                                              │   │
│  │  Deploy in weeks, not months                                   │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

**Sources:**
- [Big Bang Documentation](https://docs-bigbang.dso.mil/latest/)
- [Big Bang GitHub](https://github.com/DoD-Platform-One/bigbang)
- [Platform One Services](https://p1.dso.mil/services/big-bang)

---

### Iron Bank - Container Security Deep Dive

#### Overview

| Aspect | Details |
|--------|---------|
| **Purpose** | DOD's source for hardened container images |
| **Images Available** | 1,800+ base images |
| **Cost** | Free (DOD funded) |
| **Access** | Public at IL2 |
| **Compliance** | DoD STIG hardening, CIS benchmarks |

#### How to Get Your Images in Iron Bank

```
Iron Bank Submission Process
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  1. PREPARE                                                              │
│     ├── Use approved base image (Ubuntu, UBI, Alpine)                   │
│     ├── Follow Container Hardening Guide                                 │
│     ├── Remove unnecessary packages                                      │
│     └── Set appropriate user (non-root)                                 │
│                                                                          │
│  2. SUBMIT                                                               │
│     ├── Create repo in Repo1 (GitLab)                                   │
│     ├── Add Dockerfile + hardening.manifest.yaml                        │
│     ├── Request onboarding from Iron Bank team                          │
│     └── Submit for pipeline evaluation                                  │
│                                                                          │
│  3. SCAN & EVALUATE                                                      │
│     ├── Automated CVE scanning                                          │
│     ├── STIG compliance check                                           │
│     ├── Container best practices validation                              │
│     └── Manual review for high-risk items                               │
│                                                                          │
│  4. APPROVAL                                                             │
│     ├── Receive Overall Risk Assessment (ORA) score                     │
│     ├── Address any critical findings                                    │
│     └── Image marked "approved" in Iron Bank                            │
│                                                                          │
│  5. CONTINUOUS MONITORING                                                │
│     ├── Weekly CVE rescans                                              │
│     ├── Automated alerts for new vulnerabilities                        │
│     └── Required remediation timelines                                  │
│                                                                          │
│  Timeline: 2-6 weeks depending on complexity and findings               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Images You'd Submit for Residency Scheduler

| Image | Base | Priority |
|-------|------|----------|
| `scheduler-backend` | python:3.11-slim (UBI preferred) | HIGH |
| `scheduler-frontend` | node:20-alpine | HIGH |
| `scheduler-celery` | Same as backend | HIGH |
| `scheduler-mcp` | python:3.11-slim | MEDIUM |

**Note:** PostgreSQL and Redis already have Iron Bank approved images - use those!

**Sources:**
- [Iron Bank Documentation](https://docs-ironbank.dso.mil/overview/)
- [Iron Bank Container Registry](https://ironbank.dso.mil/about)
- [DevSecOps Container Hardening Guide](https://dl.dod.cyber.mil/wp-content/uploads/devsecops/pdf/Final_DevSecOps_Enterprise_Container_Hardening_Guide_1.2.pdf)

---

### DOD-Wide Deployment Decision Tree

```
DOD-Wide Deployment Decision Tree (Updated Dec 2025)
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Is this for Defense Health Agency (DHA)?                               │
│     │                                                                    │
│     ├── YES → Consider Ask Sage integration                             │
│     │         - Already has DHA enterprise agreement                     │
│     │         - IL5 + PHI approved                                       │
│     │         - Could host your scheduling tools                         │
│     │                                                                    │
│     └── NO → Continue to general DOD path                               │
│                                                                          │
│  Is this for general DOD deployment?                                    │
│     │                                                                    │
│     ├── YES → Use Platform One + Big Bang                               │
│     │         │                                                          │
│     │         ├── Step 1: Submit images to Iron Bank                    │
│     │         ├── Step 2: Create Helm charts                            │
│     │         ├── Step 3: Configure for Big Bang                        │
│     │         ├── Step 4: Deploy via ArgoCD (GitOps)                    │
│     │         └── Step 5: Inherit cATO from Platform One                │
│     │                                                                    │
│     └── Single MTF only → Docker Compose                                │
│                           - Simpler operations                           │
│                           - No k8s expertise needed                      │
│                           - Works airgapped 10+ years                    │
│                                                                          │
│  Need AI features in DOD environment?                                   │
│     │                                                                    │
│     ├── Generic AI → GenAI.mil (Gemini)                                 │
│     │   - Available to all 3M DOD personnel                             │
│     │   - Good for research, drafting, analysis                         │
│     │                                                                    │
│     ├── Enterprise AI → Ask Sage                                        │
│     │   - Model-agnostic (150+ models)                                  │
│     │   - IL5/IL6/TS authorized                                         │
│     │   - DHA approved for PHI                                          │
│     │                                                                    │
│     └── Domain-specific AI → Your MCP Server                            │
│         - 29+ scheduling-specific tools                                 │
│         - Works locally/airgapped                                       │
│         - Specialized for residency scheduling                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Strategic Recommendation for DOD-Wide

```
Recommended DOD-Wide Architecture
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  PHASE 1: Local Deployment (Current)                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Docker Compose at single MTF                                    │   │
│  │  - Airgap ready                                                  │   │
│  │  - MCP Server for local AI                                       │   │
│  │  - No external dependencies                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  PHASE 2: DHA Integration (If sponsored by DHA)                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Explore Ask Sage partnership                                    │   │
│  │  - DHA already has enterprise agreement                          │   │
│  │  - Your scheduling tools could be MCP-style plugins              │   │
│  │  - Leverage their IL5 + PHI authorization                        │   │
│  │  - Edge deployment for airgapped sites                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  PHASE 3: Platform One Deployment (Full DOD)                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Big Bang on Platform One                                        │   │
│  │  - Iron Bank hardened images                                     │   │
│  │  - Helm charts for deployment                                    │   │
│  │  - ArgoCD for GitOps                                             │   │
│  │  - Inherit cATO                                                  │   │
│  │  - Auto-scaling for enterprise load                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  All phases use SAME codebase - just different deployment manifests     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Key Contacts & Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Platform One | https://p1.dso.mil/ | DevSecOps platform |
| Iron Bank | https://ironbank.dso.mil/ | Hardened containers |
| Repo1 | https://repo1.dso.mil/ | DOD GitLab |
| Big Bang Docs | https://docs-bigbang.dso.mil/ | Deployment guides |
| Ask Sage | https://www.asksage.ai/ | GenAI platform |
| GenAI.mil | GenAI.mil (CAC required) | Pentagon AI |
| DHA | https://dha.mil/ | Defense Health Agency |

---

*DOD Platform Appendix added December 2025 based on latest announcements*
