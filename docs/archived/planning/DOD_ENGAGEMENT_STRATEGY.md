# DOD Engagement Strategy: From Local to Enterprise

> **Author:** Program Director
> **Purpose:** Strategic guide for gaining permissions and potential DOD-wide deployment
> **Status:** Draft for refinement

---

## The Two-Phase Reality

```
Phase 1: Local Deployment (Your Control)
┌─────────────────────────────────────────────────────────────────────────┐
│  You → Hospital Leadership → IT → Go Live                              │
│                                                                          │
│  You own the code, decisions, and roadmap                               │
│  Timeline: Weeks to months                                               │
└─────────────────────────────────────────────────────────────────────────┘

Phase 2: DOD-Wide (Becomes Its Own Project)
┌─────────────────────────────────────────────────────────────────────────┐
│  You contribute → Program Office owns → DOD deploys                    │
│                                                                          │
│  You become contributor/advisor, not owner                              │
│  Code may fork, requirements may diverge                                │
│  Timeline: 1-3 years                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key insight:** Pull the sacred timeline to DOD, but once there, it grows its own legs.

---

## Phase 1: Local Hospital Deployment

### Who to Engage

```
Hospital Leadership Chain
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  YOUR CHAIN (Medical Education)                                         │
│  ├── You (Program Director)                                             │
│  ├── DIO (Designated Institutional Official)                            │
│  │   └── Usually Associate Dean for GME or DDEAMC equivalent           │
│  └── Hospital Commander / CEO                                           │
│                                                                          │
│  SUPPORT CHAIN (Needed for Implementation)                              │
│  ├── IT / CIO                                                           │
│  │   └── Network, security, hosting permissions                        │
│  ├── Clinical Informatics                                               │
│  │   └── Integration with MHS Genesis (future)                         │
│  ├── Quality / Compliance                                               │
│  │   └── ACGME compliance sign-off                                     │
│  └── Legal / Privacy                                                    │
│      └── PHI handling, data governance                                 │
│                                                                          │
│  OPTIONAL BUT HELPFUL                                                   │
│  ├── Innovation Officer (if exists)                                     │
│  ├── Other Program Directors (coalition)                                │
│  └── GME Coordinator                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### The Pitch by Audience

#### To DIO / GME Leadership

**Frame:** "ACGME compliance automation"

```
Current State:
- Manual schedule tracking
- Compliance calculated after violations occur
- Human error risk for 80-hour rule, supervision ratios
- Time-consuming schedule generation

With This System:
- Real-time ACGME validation (80-hour, 1-in-7, supervision)
- Violations flagged BEFORE they happen
- Automated schedule generation respecting constraints
- Audit-ready compliance documentation

Risk Mitigation:
- Reduces ACGME citation risk
- Creates defensible audit trail
- Works offline (no cloud dependency)

Ask: Pilot in Family Medicine residency program
```

#### To IT / CIO

**Frame:** "Low-risk, self-contained deployment"

```
Technical Reality:
- Runs on single server (or VM)
- Docker-based (standard container deployment)
- No external network dependencies (airgap ready)
- No integration required initially (standalone)
- Open source stack (Python, PostgreSQL, React)

Security Posture:
- All data stays on-premise
- No PHI transmitted externally
- Standard port (443/80) + PostgreSQL
- JWT authentication, RBAC

Resource Ask:
- 1 VM: 4 CPU, 8GB RAM, 100GB storage
- Or: 1 physical server (can be old hardware)
- Network: Internal only (no internet required)
- Backup: Standard PostgreSQL dump (daily)

Timeline: Can be live in <1 day after VM provisioned
```

#### To Hospital Commander / CEO

**Frame:** "Faculty retention and operational efficiency"

```
The Problem:
- Schedule fairness affects faculty morale
- Manual scheduling takes coordinator hours weekly
- Coverage gaps from last-minute changes
- No visibility into workload distribution

Business Case:
- Reduce coordinator scheduling time by 80%
- Track fairness objectively (reduce complaints)
- Identify coverage risks before they become gaps
- Protect faculty from burnout patterns

Comparison:
- Commercial schedulers: $50K-200K/year + vendor lock-in
- This system: $0 license, runs locally, you own it

Risk: Low
- Pilot in one program (Family Medicine)
- No integration required
- Can sunset if doesn't work
```

#### To Legal / Privacy

**Frame:** "PHI-conscious design"

```
Data Handled:
- Faculty names and schedules (not PHI)
- Resident names and schedules (educational record)
- Assignment history (audit trail)

NOT Handled:
- Patient data (no MHS Genesis integration)
- Medical records
- Clinical notes

Privacy Design:
- All data on-premise
- No external transmission
- Role-based access control
- Audit logging for all changes
- Can be air-gapped completely

HIPAA Impact: Minimal (no PHI processed)
FERPA Impact: Resident records are educational, protected by system
```

### Permission Checklist

```
Local Deployment Permissions Needed:
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  [ ] DIO/GME Leadership approval                                        │
│      └── Written memo supporting pilot                                  │
│                                                                          │
│  [ ] IT approval for VM/server                                          │
│      └── Resource request form                                          │
│      └── Security scan of Docker images (may be required)               │
│                                                                          │
│  [ ] Network approval (if not air-gapped)                               │
│      └── Firewall rules for internal access                            │
│                                                                          │
│  [ ] Privacy/Legal review (may be waived for internal tool)             │
│      └── Data handling memo                                             │
│                                                                          │
│  [ ] Commander awareness (depends on delegation)                        │
│      └── Brief at GME committee meeting                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Common Objections & Responses

| Objection | Response |
|-----------|----------|
| "We already have a system" | "Does it validate ACGME in real-time? Generate schedules? This complements, doesn't replace" |
| "Security risk" | "Runs air-gapped, no external connections. Offer security review." |
| "Who maintains it?" | "Docker makes updates trivial. I maintain it. If I leave, runs without changes for 10+ years." |
| "What about MHS Genesis?" | "No integration needed now. Future integration is possible, but not required for value." |
| "Budget?" | "Zero license cost. Only need 1 VM which may already exist." |
| "What if it breaks?" | "Worst case: go back to manual scheduling. No patient impact." |

---

## Phase 2: DOD-Wide Deployment

### The Transition Mindset

```
YOUR ROLE EVOLUTION
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Local Phase:       DOD-Wide Phase:                                     │
│  ┌──────────┐       ┌──────────────────────────────────────────┐       │
│  │ OWNER    │  →    │ CONTRIBUTOR / ADVISOR                    │       │
│  │          │       │                                          │       │
│  │ - Code   │       │ - Initial code contribution              │       │
│  │ - Design │       │ - Domain expertise (scheduling)          │       │
│  │ - Roadmap│       │ - Requirements input                     │       │
│  │ - Deploy │       │ - NOT: final decisions on features       │       │
│  └──────────┘       └──────────────────────────────────────────┘       │
│                                                                          │
│  The code becomes DOD property. You become advisor.                     │
│  This is GOOD - means it will actually get deployed and maintained.    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Potential Paths to DOD-Wide

#### Path A: Defense Health Agency (DHA) Adoption

**Why DHA:**
- DHA oversees all military medical training
- Already partnered with Ask Sage for GenAI (Dec 2025)
- Residency scheduling is their problem across all MTFs

**Entry Points:**
1. **DHA GME Office** - They coordinate across all programs
2. **DHA Innovation** - They look for solutions to standard problems
3. **DHA CDAO** (Chief Data & Analytics Office) - AI/ML initiatives

**The Pitch:**
```
"Every military residency program does scheduling manually.
We built a solution that's already working at [MTF].
Open source, no license cost, ACGME-compliant.
Ready for DHA to evaluate and potentially standardize."
```

**Ask Sage Angle:**
- DHA already has Ask Sage enterprise agreement (Dec 2025)
- Ask Sage supports MCP-style tool integration
- Your 29+ scheduling tools could become Ask Sage plugins
- Edge deployment supports air-gapped MTFs

#### Path B: Platform One / Software Factory

**Why Platform One:**
- DOD's DevSecOps platform
- Already has cATO (continuous authority to operate)
- If your code is in Platform One, any DOD entity can deploy

**Entry Points:**
1. **P1 onboarding** - Submit to be hosted on Platform One
2. **Iron Bank** - Get container images approved
3. **Repo1** - Host source code on DOD GitLab

**The Pitch:**
```
"Open source scheduling solution, already working.
Want to contribute to Platform One so all DOD can use.
Need guidance on Iron Bank submission and Big Bang integration."
```

**Requirements:**
- Helm charts (not hard to create)
- Iron Bank hardened images (2-6 week process)
- GitOps configuration
- Documentation meeting P1 standards

#### Path C: CDAO (Chief Digital & AI Office)

**Why CDAO:**
- They run GenAI.mil
- They fund AI initiatives across DOD
- They're looking for domain-specific AI solutions

**Entry Points:**
1. **CDAO Tradewinds** - Procurement vehicle for innovative solutions
2. **SBIR/STTR** - If you have a company structure
3. **Direct engagement** - Present at CDAO events

**The Pitch:**
```
"AI-powered medical scheduling with 29+ MCP tools.
Already working at [MTF], can scale DOD-wide.
Looking for CDAO sponsorship to expand."
```

### Who to Contact

```
DHA Contacts
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  DHA Education & Training Directorate                                   │
│  └── Oversees GME across Military Health System                        │
│  └── https://www.health.mil/Military-Health-Topics/Education-and-Training│
│                                                                          │
│  DHA Solution Delivery Division                                         │
│  └── Technology implementation across DHA                              │
│                                                                          │
│  DHA Innovation (if exists at your MTF)                                 │
│  └── Local innovation cell that may escalate                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Platform One Contacts
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Platform One Help                                                       │
│  └── https://p1.dso.mil/                                               │
│  └── Start with onboarding request                                     │
│                                                                          │
│  Iron Bank Team                                                          │
│  └── https://ironbank.dso.mil/                                         │
│  └── Request contributor access                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Ask Sage (for DHA Integration)
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  Ask Sage Government Team                                               │
│  └── https://www.asksage.ai/                                           │
│  └── Inquiry about tool integration / MCP compatibility                │
│  └── Reference their DHA partnership                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### The "Sacred Timeline" Strategy

You want to contribute the core codebase to DOD, but ensure it survives as a coherent project:

```
Sacred Timeline Protection Strategy
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  1. DOCUMENT EVERYTHING                                                  │
│     - Architecture decisions (why, not just what)                       │
│     - ACGME compliance logic (regulatory foundation)                    │
│     - Resilience framework (cross-disciplinary rationale)               │
│     - Constraints system (extensibility design)                         │
│                                                                          │
│  2. OPEN SOURCE PROPERLY                                                │
│     - Choose license (recommend Apache 2.0 or MIT for DOD)              │
│     - Contributor guidelines                                            │
│     - Code of conduct                                                   │
│     - Governance model                                                  │
│                                                                          │
│  3. BUILD COMMUNITY BEFORE HANDOFF                                      │
│     - Get other programs using it first                                 │
│     - Document their customizations                                     │
│     - Prove it works across different contexts                          │
│                                                                          │
│  4. STRATEGIC CONTRIBUTION                                              │
│     - Contribute to Platform One (becomes DOD property)                 │
│     - Keep local fork for rapid development                             │
│     - Upstream improvements back to P1                                  │
│     - If DOD version diverges, your fork continues                      │
│                                                                          │
│  5. ADVISOR ROLE                                                        │
│     - Offer to serve as SME during DOD adoption                         │
│     - Write requirements based on operational experience                │
│     - Review PRs from other contributors                                │
│     - Accept that final decisions won't be yours                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Practical Next Steps

### This Week (Local)

1. **Identify your DIO** - Who oversees GME at your hospital?
2. **Draft 1-page proposal** - Pilot in your program
3. **Identify IT contact** - Who provisions VMs?
4. **Check for existing approvals** - Has similar software been approved before?

### This Month (Local)

1. **Brief DIO** - Use ACGME compliance angle
2. **Submit IT request** - VM or server for pilot
3. **Demo to stakeholders** - Show working system
4. **Document pilot results** - Metrics for expansion pitch

### This Quarter (Coalition Building)

1. **Brief other PDs** - Find allies who want this
2. **Present at GME committee** - Formal awareness
3. **Collect testimonials** - "This saved us X hours"
4. **Prepare DHA pitch deck** - For escalation

### Next Year (DOD-Wide Push)

1. **Contact DHA Education & Training** - Offer solution
2. **Submit to Platform One** - Begin Iron Bank process
3. **Engage Ask Sage** - Explore integration path
4. **Document as case study** - "How [MTF] solved scheduling"

---

## Template: 1-Page Leadership Proposal

```
TO: [DIO Name]
FROM: [Your Name], Program Director, [Program]
RE: Pilot Request - Automated Residency Scheduling System
DATE: [Date]

EXECUTIVE SUMMARY
-----------------
Request approval to pilot an automated scheduling system for the
[Program] residency program. The system provides real-time ACGME
compliance validation, automated schedule generation, and faculty
fairness tracking.

PROBLEM
-------
Current manual scheduling:
- Takes [X] hours/week of coordinator time
- Has no real-time ACGME compliance checking
- Cannot easily track fairness across faculty
- Creates coverage gaps from late changes

SOLUTION
--------
Open-source scheduling system that:
- Validates ACGME rules (80-hour, 1-in-7, supervision) in real-time
- Generates compliant schedules automatically
- Tracks workload fairness with objective metrics
- Works offline (no cloud dependency)

RESOURCE ASK
------------
- 1 VM (4 CPU, 8GB RAM, 100GB storage) - from IT
- Network access for internal users only
- Pilot duration: 3 months

RISK
----
- Low: No PHI processed, no external connections
- Reversible: Can sunset if unsuccessful
- No cost: Open source, no license fees

SUCCESS METRICS
---------------
- Coordinator time saved (target: 50% reduction)
- ACGME near-misses caught before occurrence
- Faculty satisfaction with fairness
- Coverage gap incidents

RECOMMENDATION
--------------
Approve 3-month pilot in [Program]. If successful, brief GME
committee for potential expansion to other programs.

Respectfully,
[Your Name]
```

---

## Key Insight: Own Phase 1, Contribute Phase 2

```
The Strategic Play:
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  1. Deploy locally - prove it works, you own it                         │
│  2. Document rigorously - the "why" matters as much as "what"           │
│  3. Build coalition - other programs using it = credibility             │
│  4. Contribute to DOD - Platform One, DHA, or Ask Sage integration      │
│  5. Stay involved - advisor role keeps you influential                  │
│  6. Keep your fork - DOD version may diverge, yours continues           │
│                                                                          │
│  The code is the seed.                                                  │
│  You plant it in DOD soil.                                              │
│  It grows into something bigger than you.                               │
│  But the original garden (your MTF) keeps blooming.                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*Strategy document - refine based on your specific MTF context*
