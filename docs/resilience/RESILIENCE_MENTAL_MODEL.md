# Resilience Framework Mental Model

> **Audience:** Humans who need to understand what the resilience modules actually do vs. what they might intuitively think.
>
> **Last Updated:** 2026-01-27

---

## The Big Picture

The resilience framework borrows concepts from:
- Power grid engineering (defense levels, N-1/N-2)
- Queuing theory (Erlang C, utilization)
- Epidemiology (SIR model, R₀)
- Manufacturing (SPC, control charts)
- Physics (catastrophe theory, metastability)

**Key insight:** These aren't metaphors. The math actually transfers because the underlying dynamics are similar.

---

## Module-by-Module: Intuition vs. Reality

### 1. Defense Levels (GREEN → BLACK)

**Location:** `engine/defense_level_calculator.py`

#### Common Intuition
"It's a traffic light. GREEN = good, RED = bad. Just a visualization."

#### What It Actually Does
It's a **graduated response system** with automatic escalation rules:

| Level | Utilization | What Happens |
|-------|-------------|--------------|
| GREEN | <80% | Normal operations, no action |
| YELLOW | 80-90% | Early warning, proactive measures |
| ORANGE | 90-95% | Degraded ops, activate contingencies |
| RED | >95% | Critical, emergency protocols |
| BLACK | Cascade | System failure, mutual aid |

**The key misconception:** Defense levels aren't just labels. Each level has **different response procedures**. Going from YELLOW to ORANGE isn't cosmetic - it triggers different operational modes.

**When it matters:** The system doesn't wait until RED to act. YELLOW triggers proactive rebalancing before problems cascade.

---

### 2. Circuit Breaker

**Location:** `circuit_breaker/`

#### Common Intuition
"It stops bad requests. Like a fuse."

#### What It Actually Does
It's a **state machine** with three states:

```
CLOSED (normal) → OPEN (failing) → HALF-OPEN (testing) → CLOSED
                      ↑                    ↓
                      ←─────── still failing ←──────
```

- **CLOSED:** Requests pass through. Failures are counted.
- **OPEN:** Requests are rejected immediately (fail-fast). No load on failing service.
- **HALF-OPEN:** Allow limited requests to test recovery.

**The key misconception:** "Open" doesn't mean "allowing traffic." It means "circuit is broken, no current flows." The naming is from electrical engineering, not intuitive.

**When it matters:** When a downstream service is failing, hammering it makes things worse. The circuit breaker **protects the failing service** by stopping requests, not just the caller.

---

### 3. N-1 / N-2 Contingency

**Location:** `contingency/n1_analyzer.py`, `n2_analyzer.py`

#### Common Intuition
"Check if we can survive losing one person. Simple redundancy."

#### What It Actually Does
N-1 analysis asks: "For EVERY single-point failure, does the schedule still work?"

This is **combinatorial**:
- N-1: Check every resident individually (O(n) scenarios)
- N-2: Check every pair (O(n²) scenarios)

**The key misconception:** "We have backup" doesn't mean N-1 compliant. N-1 means **every scenario** has a viable response, not just "we have some backup somewhere."

Example:
- 10 residents, 3 are backups
- Resident A's absence → Backup 1 covers ✓
- Resident B's absence → Backup 1 covers ✓
- Resident C's absence → Backup 1 covers ✓
- Resident D's absence → Only Backup 1 can cover, but Backup 1 is already committed to A/B/C scenarios... ✗

**When it matters:** N-1 failures are rare individually but guaranteed eventually. "We've never needed it" isn't an argument - power grids run for decades between major failures, but they still require N-1 compliance.

---

### 4. Erlang C / Utilization (80% Rule)

**Location:** `queuing/erlang_c.py`

#### Common Intuition
"80% is the target. Higher is more efficient."

#### What It Actually Does
Erlang C models queue behavior. The math shows:

| Utilization | Queue Behavior |
|-------------|----------------|
| 60% | Short, stable queues |
| 80% | Queues growing noticeably |
| 90% | Queues growing fast |
| 95% | Queue explosion |
| 99% | Effectively infinite wait |

**The key misconception:** 80% isn't a "target to hit." It's a **ceiling to stay under**. Going from 80% to 90% isn't "10% more efficient" - it's "queues 3x longer."

The formula is non-linear:
```
Average wait ∝ ρ / (1 - ρ)

At 80%: 0.8 / 0.2 = 4 units
At 90%: 0.9 / 0.1 = 9 units (2.25x worse)
At 95%: 0.95 / 0.05 = 19 units (4.75x worse)
```

**When it matters:** "We're at 92% utilization" sounds efficient. It means queues are exploding. The instinct to "maximize utilization" is wrong for queuing systems.

---

### 5. Burnout Fire Index (Multi-Temporal)

**Location:** `burnout_fire_index.py`

#### Common Intuition
"Count hours worked. More hours = more burnout."

#### What It Actually Does
Adapts the Canadian Forest Fire Danger Rating System. Burnout requires **multiple time scales** to align:

| Component | Time Scale | What It Measures |
|-----------|------------|------------------|
| FFMC | 2 weeks | Recent acute stress |
| DMC | 3 months | Medium-term accumulation |
| DC | 1 year | Long-term satisfaction erosion |
| ISI | Rate | How fast things are getting worse |
| BUI | Combined | Total accumulated burden |
| FWI | Final | Composite danger rating |

**The key misconception:** A single bad week doesn't cause burnout. A year of mild overwork might. The model captures **temporal alignment** - when short, medium, and long-term stressors converge.

**When it matters:** Someone working 70 hours this week after a year of 40-hour weeks is different from someone working 70 hours this week after 6 months of 60-hour weeks. Same "fine fuel" (FFMC), different "duff layer" (DMC).

---

### 6. SIR Epidemiology (Burnout Spread)

**Location:** `epidemiology/sir_model.py`

#### Common Intuition
"Burnout is contagious like a cold. Infected people spread it."

#### What It Actually Does
Models burnout as an **epidemic process**, not literal contagion:

- **S (Susceptible):** Residents who could burn out
- **I (Infected):** Residents currently burned out
- **R (Recovered):** Residents who recovered (or left)

The "transmission" is workload redistribution:
1. Resident A burns out
2. A's work redistributes to others
3. Others now overworked → higher burnout probability
4. Cascade effect

**The key misconception:** It's not mood contagion or "negativity spreading." It's **workload cascade**. The math is the same as epidemics because the dynamics are the same: one failure increases load on others.

**Key metric - R₀:**
- R₀ < 1: Burnout declining (each case causes <1 new case)
- R₀ = 1: Stable (endemic)
- R₀ > 1: Epidemic growth

**When it matters:** If R₀ > 1, burnout will grow exponentially until intervention. Tracking R₀ tells you if your interventions are working.

---

### 7. SPC Control Charts

**Location:** `spc/control_chart.py`, `spc/western_electric.py`

#### Common Intuition
"Set a threshold. Alert when crossed. Simple."

#### What It Actually Does
Statistical Process Control detects **process changes**, not just threshold violations:

- **Control limits:** ±3σ from baseline (not arbitrary thresholds)
- **Western Electric Rules:** 8 rules that detect subtle shifts

Example rules:
1. One point beyond 3σ → Obvious outlier
2. 2 of 3 points beyond 2σ → Drift starting
3. 8 consecutive on same side of center → Process shifted

**The key misconception:** A value "within limits" isn't necessarily fine. Eight consecutive values slightly below center (Rule 4) indicates a process shift even though no individual point violated limits.

**When it matters:** SPC catches problems **before** threshold violations. A trend of 6 increasing values might all be "in control" but signals something changed.

---

### 8. Catastrophe Theory (Tipping Points)

**Location:** `exotic/catastrophe.py`

#### Common Intuition
"Predict when someone will suddenly quit. Magic."

#### What It Actually Does
Models how **smooth parameter changes** cause **sudden behavioral jumps**:

```
Cusp potential: V(x) = x⁴/4 + ax²/2 + bx

When parameters (a, b) cross the bifurcation set,
the stable equilibrium suddenly jumps to a new position.
```

**The key misconception:** It's not prediction of specific events. It identifies **parameter regions** where sudden changes become likely. It cannot predict "Tuesday at 3pm" but it can identify "we're in a region where small pushes cause big changes."

**When it matters:** A resident might tolerate increasing stress smoothly until a threshold - then suddenly quit. The "sudden" quit was actually predictable from the parameter trajectory approaching the bifurcation boundary.

---

## Common Misconceptions Summary

| Module | Wrong Intuition | Correct Understanding |
|--------|-----------------|----------------------|
| Defense Levels | Traffic light visualization | Graduated response system with different protocols |
| Circuit Breaker | "Open" means allowing traffic | "Open" means circuit broken, traffic blocked |
| N-1 Analysis | "We have backup" = compliant | Every single-failure scenario must have response |
| Utilization | 80% is a target to hit | 80% is a ceiling to stay under |
| Burnout Index | Hours worked = burnout risk | Multiple time scales must align |
| SIR Model | Mood is contagious | Workload redistributes, causing cascade |
| SPC | Threshold alerts | Process change detection |
| Catastrophe | Predict specific events | Identify parameter regions of instability |

---

## When To Use What

### Daily Operations
- **Defense Levels:** Dashboard indicator, automated escalation
- **Utilization:** Capacity planning, shift sizing
- **SPC:** Anomaly detection in metrics

### Weekly Analysis
- **N-1:** Verify schedule robustness
- **SIR R₀:** Track burnout trajectory
- **Burnout Index:** Individual risk assessment

### Strategic Planning
- **N-2:** Extreme scenario planning
- **Catastrophe Theory:** Identify systemic vulnerabilities
- **Erlang C:** Staffing model optimization

---

## The Meta-Misconception

The biggest misconception: "These are just fancy metrics."

**Reality:** Each module encodes **domain knowledge** from fields that have solved similar problems:
- Power grids have prevented blackouts for decades using N-1
- Call centers optimized staffing using Erlang C
- Manufacturing achieved Six Sigma using SPC
- Epidemiologists predicted COVID waves using SIR

The resilience framework doesn't invent new science - it **applies proven science** to scheduling.

---

## Quick Reference

### Good States
- Defense: GREEN
- Utilization: 60-75%
- N-1: All scenarios covered
- R₀: <1 (declining)
- SPC: No rule violations
- Burnout Index: <20 (LOW)

### Warning States
- Defense: YELLOW
- Utilization: 75-80%
- N-1: Most scenarios covered
- R₀: ~1 (stable)
- SPC: Zone B violations
- Burnout Index: 20-40 (MODERATE)

### Critical States
- Defense: ORANGE/RED
- Utilization: >80%
- N-1: Uncovered scenarios exist
- R₀: >1 (epidemic)
- SPC: Zone A violations
- Burnout Index: >40 (HIGH+)

---

*Document created January 2026.*
