# ChatGPT Pulse Review Topics

## System Overview (Context for ChatGPT)

The **Residency Scheduler** is a production-ready medical residency program scheduling system for a **military residency program**. Key facts:

- **Problem**: Automates complex scheduling while ensuring ACGME (medical accreditation) compliance
- **Unique Challenge**: Military programs face "PCS season" where 50% of faculty can be lost to permanent change of station orders simultaneously
- **No External Relief**: Government constraints preclude hiring locums/temporary staff
- **Must Degrade Gracefully**: When you can't meet all obligations, which ones do you sacrifice?

The system incorporates resilience concepts from nuclear engineering, power grids, biology, psychology, queuing theory, and network science.

---

## Capabilities to Understand

### 1. Constraint-Based Scheduling
- 730 scheduling blocks per academic year (AM/PM sessions)
- Multiple solvers: greedy, constraint programming (OR-Tools), linear programming (PuLP), hybrid
- Automatic ACGME compliance validation (80-hour work week, 1-in-7 day off, supervision ratios)

### 2. Resilience Framework (3 Tiers Implemented)

**Tier 1 - Critical:**
- 80% utilization threshold (queuing theory - exponential wait times above this)
- Defense in Depth (5 safety levels from nuclear engineering)
- N-1/N-2 contingency analysis (power grid concepts - can we survive losing 1-2 key people?)
- Static stability (pre-computed fallback schedules)
- Sacrifice hierarchy (triage medicine - what gets cut first)

**Tier 2 - Strategic:**
- Homeostasis feedback loops (biological adaptation)
- Blast radius isolation (contain failures to zones)
- Le Chatelier's principle (equilibrium shifts under stress)

**Tier 3 - Tactical:**
- Cognitive load management (prevent decision fatigue)
- Stigmergy scheduling (swarm intelligence - emergent preferences)
- Hub vulnerability analysis (network theory - key person risk)

### 3. Sacrifice Hierarchy (Load Shedding)

When capacity is insufficient, activities are cut in this order:
1. **PATIENT_SAFETY** - NEVER sacrifice (ICU, OR, trauma)
2. **ACGME_REQUIREMENTS** - Program survival depends on accreditation
3. **CONTINUITY_OF_CARE** - Follow-ups, chronic disease (deferrable)
4. **EDUCATION_CORE** - Didactics, simulation
5. **RESEARCH** - Important but not urgent
6. **ADMINISTRATION** - First to cut, last to restore
7. **EDUCATION_OPTIONAL** - Conferences, electives

Load shedding levels: NORMAL → YELLOW → ORANGE → RED → BLACK → CRITICAL

---

## Issues for ChatGPT to Marinate On

### Category A: Ethics & Philosophy

#### A1. The Sacrifice Hierarchy Order
Is the current ordering ethically sound? Consider:
- Should research ever come before core education? (Future patients vs current trainees)
- Is administration really lowest priority? (Documentation affects patient safety too)
- What about faculty wellness? (Not explicitly in hierarchy - should burnout prevention be a category?)
- Is "ACGME Requirements" correctly prioritized above "Continuity of Care"? (Accreditation ensures program survival, but individual patients might suffer)

#### A2. Pre-Crisis Decision Making
The system philosophy is: "Decisions made during crisis are worse than decisions made beforehand."
- Is this always true?
- What context-dependent factors might the pre-made hierarchy miss?
- How do you balance algorithmic efficiency with human judgment in edge cases?

#### A3. Transparency vs. Morale
Should residents and junior faculty know exactly how the sacrifice hierarchy works?
- Transparency builds trust, but knowing "education will be cut first" could demoralize
- How do you communicate "you matter, but less than patient safety" without damaging culture?

---

### Category B: Organizational & Communication

#### B1. Stakeholder Buy-In
The TODO list includes: "Get sign-off on what gets cut first during crisis"
- How do you get leadership buy-in on a sacrifice hierarchy?
- What if different stakeholders have fundamentally different priorities?
- How do you handle the political dynamics of explicit prioritization?

#### B2. Cross-Training Strategy
N-1/N-2 analysis reveals "hub" faculty who are single points of failure.
- How do you convince specialists to cross-train without feeling replaceable?
- What's the right balance between specialization (excellence) and cross-training (resilience)?
- How do you make cross-training part of culture vs. burden?

#### B3. Crisis Communication Templates
When activating load shedding, what do you tell:
- Residents whose education is being reduced?
- Faculty whose research time is being cut?
- Patients whose follow-ups are being deferred?
- Hospital administration who see metrics declining?

---

### Category C: Psychology & Human Factors

#### C1. Cognitive Load During Crisis
The system tracks "decision fatigue" and can auto-defer low-priority decisions.
- What decisions should NEVER be auto-deferred even during high cognitive load?
- How do you know when a human needs to override the algorithm?
- Is there a "too helpful" level of automation that deskills coordinators?

#### C2. The Psychology of Gradual Degradation
Going from NORMAL → YELLOW → ORANGE → RED → BLACK creates a "boiling frog" effect.
- How do you maintain urgency without panic?
- When does acceptance of degraded state become complacency?
- How do you celebrate recovery (returning to NORMAL) without implying previous levels were failures?

#### C3. Faculty Burnout Detection
The "homeostasis" module tracks stress indicators, but:
- What behavioral signals should trigger concern? (Scheduling metrics vs. soft signals)
- Is surveillance-based burnout detection ethical?
- How do you act on burnout data without creating stigma?

---

### Category D: Technical & Architectural

#### D1. The 80% Utilization Cliff
Queuing theory says systems degrade exponentially above 80% utilization.
- Is 80% the right threshold for medical scheduling? (Different from call centers?)
- How do you convince administrators that 20% "slack" isn't waste?
- What's the right metric for "utilization" in medical education? (Clock hours? Case volume? Cognitive load?)

#### D2. Hub Vulnerability vs. Expertise Concentration
NetworkX centrality analysis identifies "key person risk."
- Is high centrality always bad? (Some functions SHOULD be concentrated in experts)
- How do you distinguish "healthy expertise" from "dangerous dependency"?
- What's the minimum redundancy for each function type?

#### D3. Stigmergy and Emergent Preferences
The system records scheduling preferences and lets patterns emerge (swarm intelligence).
- What preferences should be honored vs. overridden? (Comfort vs. growth)
- Could emergent preferences encode bias? (Senior faculty always get preferred slots)
- How do you balance individual preferences with equity?

---

### Category E: Tier 4 Research Questions (Future)

#### E1. Minimum Viable Population
Ecology concept: below a certain population, extinction becomes inevitable.
- What's the MVP for a residency program? (Minimum faculty to maintain accreditation AND quality)
- Are there "functional extinctions" where program survives but quality collapses?
- How do you recognize you're below MVP before it's too late?

#### E2. Phase Transitions
Like water becoming ice, systems can shift suddenly from stable to chaotic.
- What are the leading indicators of phase transition in scheduling?
- Can you reverse a phase transition, or is hysteresis permanent?
- Historical analysis: what patterns preceded past crises?

#### E3. Entropy Accumulation
Second law of thermodynamics: disorder increases over time.
- Does schedule complexity accumulate "entropy" that requires periodic resets?
- Is there a "complexity budget" that gets spent on accommodating exceptions?
- Should you periodically "defragment" schedules even when not required?

---

### Category F: Military-Specific Challenges

#### F1. PCS Season Planning
Permanent Change of Station orders cluster in summer months.
- How far in advance can you predict departures? (Orders come 6 months out, but confirmed later)
- How do you plan around uncertainty? (Might lose 3 faculty, might lose 6)
- Is there a "point of no return" where a bad PCS season becomes unrecoverable?

#### F2. Deployment Integration
Faculty may be deployed with short notice.
- How do you maintain schedule integrity when deployment is unpredictable?
- Should deployed faculty have any remote responsibilities?
- How do you handle return-to-practice credentialing?

#### F3. Military Culture Factors
- How does military hierarchy affect willingness to challenge schedules?
- Are there cultural barriers to admitting burnout in military medicine?
- How do you balance "mission first" culture with sustainable operations?

---

## Questions for ChatGPT to Address

1. **Philosophy**: Review the sacrifice hierarchy. Is it ethically sound? What's missing?

2. **Communication**: Draft talking points for explaining load shedding to different audiences (residents, faculty, admin, patients).

3. **Psychology**: What burnout indicators should the system track? How do you act on them ethically?

4. **Strategy**: How do you get organizational buy-in on a sacrifice hierarchy before crisis hits?

5. **Research**: What questions from Tier 4 deserve investigation? How would you study them?

6. **Culture**: How do you build a culture that accepts graceful degradation as strength, not failure?

7. **Edge Cases**: What scenarios might break the sacrifice hierarchy? When should humans override the algorithm?

8. **Recovery**: How do you know when to start restoring sacrificed activities? What order? How fast?

---

## What Success Looks Like

If ChatGPT provides valuable input, the outcomes might include:
- Refined sacrifice hierarchy with ethical justifications
- Communication templates for crisis activation
- Burnout detection criteria and response protocols
- Stakeholder engagement strategy for getting buy-in
- Research agenda for Tier 4 investigations
- Cultural change recommendations

---

## How to Use This Document

Copy this document and share with ChatGPT with a prompt like:

> "I'm building a medical residency scheduling system that needs to handle crisis situations gracefully. I'd like your perspective on [specific category or question]. Please consider the context provided and give me your honest assessment, including concerns or alternative approaches."

Or for a broader review:

> "Review this system's approach to graceful degradation in medical scheduling. What's sound? What concerns you? What's missing?"
