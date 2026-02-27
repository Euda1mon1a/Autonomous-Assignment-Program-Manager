# Competitive Intelligence: Residency Scheduling Software Market

No files to upload. Paste this prompt directly.

---

## Context

I'm building a military Family Medicine residency scheduling system (FastAPI + Next.js + OR-Tools CP-SAT solver). Before going to production, I need to understand the competitive landscape — what exists, what works, what's missing, and where there's whitespace.

**My system's key differentiators (to validate against competitors):**
- CP-SAT constraint programming solver (not just rule-based)
- ACGME compliance baked into constraints (80-hour, 1-in-7, supervision ratios)
- Military-specific features (deployment recovery, TDY handling, sacrifice hierarchy)
- Cross-disciplinary resilience framework (45+ modules from physics, ecology, epidemiology)
- Excel import/export (coordinators live in Excel)
- Swap management with automated compatibility matching

---

## Section 1: Major Players — Deep Dive

Research each of these residency/physician scheduling platforms in depth:

### Tier 1 (Market Leaders)
1. **Amion** (amion.com) — The incumbent. Most residency programs use it.
2. **QGenda** (qgenda.com) — Enterprise physician scheduling. Acquired by PerfectServe.
3. **MedHub** (medhub.com) — GME management platform with scheduling.
4. **New Innovations** (new-innov.com) — Residency management suite.
5. **TigerConnect** (tigerconnect.com) — Clinical communication + scheduling.

### Tier 2 (Emerging/Niche)
6. **Housestaff** (if still active) — Residency-specific scheduling
7. **ShiftAdmin** (shiftadmin.com) — Physician shift scheduling
8. **Lightning Bolt** (lightning-bolt.com) — Now part of PerfectServe/QGenda
9. **OpenTempo** (opentempo.com) — Academic medical scheduling
10. **Shift Scheduler Pro** or similar newer entrants

For EACH platform, report:
- **Pricing model** (per provider/month, per program, enterprise?)
- **Scheduling approach** (rule-based, optimization, manual with assist?)
- **ACGME compliance** (built-in validation? Real-time monitoring? Reporting?)
- **Swap/trade management** (self-service? Approval workflow? Auto-matching?)
- **Mobile app** (native? PWA? Feature parity?)
- **Excel interop** (import? Export? Live sync?)
- **API availability** (REST? GraphQL? Webhooks? Documentation quality?)
- **Integration ecosystem** (EMR, payroll, credentialing, LMS?)
- **User reviews** (G2, Capterra, Reddit r/Residency, SDN forums)
- **Military/DoD adoption** (any known military medical center deployments?)

---

## Section 2: Feature Matrix

Build a comparison matrix across all platforms for these feature categories:

### Scheduling Engine
- Auto-generation (full schedule from scratch)
- Optimization method (CP, IP, heuristic, manual)
- Constraint handling (hard vs soft, priority levels)
- Multi-block/annual scheduling
- What-if scenario modeling
- Schedule stability / anti-churn

### Compliance
- ACGME work hour tracking (real-time vs retrospective)
- Duty hour violation alerts
- Supervision ratio monitoring
- 1-in-7 day off tracking
- Moonlighting hour tracking
- Board certification/procedure tracking

### User Experience
- Drag-and-drop schedule editing
- Mobile schedule viewing
- Push notifications for changes
- Resident preference collection
- Self-service swap requests
- Calendar sync (iCal, Google, Outlook)

### Administration
- Multi-site / multi-program support
- Role-based access control
- Audit trail
- Custom reporting
- Data export formats
- Backup/restore

### Integration
- EMR integration (Epic, Cerner, CPRS/VistA)
- Payroll system integration
- Credentialing system integration
- Learning management integration
- Single sign-on (SAML, OAuth)

---

## Section 3: User Pain Points

Search Reddit (r/Residency, r/medicine, r/medicalschool), Student Doctor Network forums, and review sites for:

1. **What residents hate** about current scheduling software
2. **What program coordinators hate** about current scheduling software
3. **What program directors hate** about current scheduling software
4. **Common failure modes** — when does scheduling software break down?
5. **Switching stories** — programs that switched from one system to another, and why

Deliver: Top 20 user pain points ranked by frequency, with source links.

---

## Section 4: Military/DoD Specific

Research:
1. **Which scheduling software do military residency programs currently use?** (TAMC, BAMC, Madigan, Walter Reed, etc.)
2. **DHA/DoD procurement requirements** for medical software (FedRAMP? DISA STIG? ATO process?)
3. **Military-specific scheduling challenges** that civilian tools don't handle (deployment rotations, TDY, PCS transitions, combat casualty care training requirements)
4. **JSGME (Joint Surgeon General's Medical Education)** policies affecting scheduling
5. **Existing military scheduling tools** — does DHA have any internal/custom solutions?

---

## Section 5: Whitespace & Opportunity

Based on Sections 1-4, identify:

1. **Features NO competitor has** that would be genuinely valuable
2. **Features every competitor has** that we MUST have (table stakes)
3. **Underserved segments** (small programs, military, rural, specific specialties)
4. **Technology gaps** — where competitors use outdated approaches that modern tech could leapfrog
5. **Pricing gaps** — where there's room for a different pricing model
6. **Open-source opportunity** — is there demand for an open-source residency scheduler?

Deliver: SWOT analysis of our system vs. the market, with specific feature recommendations prioritized by impact.

---

## Section 6: Market Sizing

Quick estimates:
1. **Total addressable market** — How many ACGME-accredited residency programs exist? How many residents?
2. **Military subset** — How many military GME programs? How many military residents?
3. **Typical contract values** — What do programs pay annually for scheduling software?
4. **Growth trends** — Is the market growing? New regulations driving adoption?

Deliver: Back-of-envelope market sizing with sources.
