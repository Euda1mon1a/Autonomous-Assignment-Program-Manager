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

*Document created during Kubernetes evaluation session - December 2025*
