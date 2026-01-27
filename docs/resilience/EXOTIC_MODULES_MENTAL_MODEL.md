# Exotic Resilience Modules Mental Model

> **Audience:** Humans trying to understand the physics/biology-inspired resilience modules.
>
> **Last Updated:** 2026-01-27

---

## Why "Exotic"?

These modules borrow concepts from:
- Condensed matter physics (spin glass, metastability)
- Thermodynamics (entropy, free energy, phase transitions)
- Chemistry (Le Chatelier's principle)
- Materials science (creep, fatigue)
- Biology (gene regulation, ant colonies)

They're "exotic" because they're not standard software patterns. But the math transfers because **scheduling systems exhibit the same dynamics** as these physical systems.

---

## Module Reference

### 1. Spin Glass Model

**Location:** `exotic/spin_glass.py`

**Source:** Condensed matter physics (Edwards-Anderson model, 1975)

#### Common Intuition
"Generate random schedule variations."

#### What It Actually Does
Models **frustrated constraints** - situations where not all pairwise preferences can be satisfied simultaneously.

**Physical analogy:**
- Imagine magnets where each pair wants to align, but the geometry makes it impossible for all to align
- The system has many "ground states" (equally good but different configurations)

**Scheduling application:**
- Resident A wants Mondays off
- Resident B wants to work with A
- B wants Mondays off
- Cannot satisfy all three → frustration

**Key outputs:**
- `frustration`: Degree of unresolvable conflict (0-1)
- `diversity_score`: How different the generated schedules are
- `energy`: Quality metric (lower = better)

**When to use:** When preferences conflict and there's no single "best" schedule. Generate diverse alternatives and let humans choose.

---

### 2. Metastability Detection

**Location:** `exotic/metastability.py`

**Source:** Statistical mechanics (Kramers escape rate, 1940)

#### Common Intuition
"Check if the schedule is stuck."

#### What It Actually Does
Detects when a system is in a **local minimum** - stable against small changes but not globally optimal.

**Physical analogy:**
- A ball in a valley between two hills
- Stable against small pushes
- But a bigger push would send it to a lower valley

**Key insight:** Metastable states can persist for a long time, then suddenly collapse when a perturbation exceeds the **activation energy barrier**.

**Scheduling application:**
- Organization has "always done it this way"
- Small changes don't help (local minimum)
- A reorganization could find a much better schedule
- But reorganization has a "cost" (the barrier)

**Key outputs:**
- `barrier_height`: How much disruption needed to escape
- `escape_rate`: Probability of spontaneous transition
- `lifetime`: Expected time before transition
- `is_metastable`: Boolean flag

**When to use:** When schedules seem "stuck" but aren't obviously bad. Identifies when a major reorganization might help.

---

### 3. Catastrophe Theory

**Location:** `exotic/catastrophe.py`

**Source:** Dynamical systems (Rene Thom, 1972)

#### Common Intuition
"Predict when someone will suddenly quit."

#### What It Actually Does
Models how **smooth parameter changes** cause **discontinuous behavior jumps**.

**The cusp catastrophe:**
```
Potential: V(x) = x^4/4 + ax^2/2 + bx

As parameters (a, b) change smoothly,
the stable equilibrium can suddenly JUMP to a new position.
```

**Physical analogy:**
- Slowly bending a ruler
- At some point it suddenly snaps to the other side
- The "snap" is discontinuous even though the bending was smooth

**Scheduling application:**
- Morale degrades gradually (smooth parameter change)
- At some threshold, sudden mass resignation (discontinuous jump)
- The "tipping point" is predictable from parameter trajectories

**Key outputs:**
- `a_critical`, `b_critical`: Parameter values where jumps occur
- `jump_magnitude`: Size of the discontinuity
- `hysteresis_width`: How far back parameters must go to reverse

**When to use:** Identify parameter regions where small changes could cause big effects. Early warning for organizational tipping points.

---

### 4. Entropy Analysis

**Location:** `thermodynamics/entropy.py`

**Source:** Information theory (Shannon, 1948)

#### Common Intuition
"Measure chaos/randomness in the schedule."

#### What It Actually Does
Measures **predictability and distribution evenness**.

**Shannon entropy:** H = -Σ p(i) log p(i)

- **High entropy:** Assignments evenly distributed (unpredictable)
- **Low entropy:** Concentrated in few slots/people (predictable)

**Scheduling application:**
- `person_entropy`: Are assignments spread across faculty, or concentrated?
- `rotation_entropy`: Are rotations used evenly, or a few dominate?
- `time_entropy`: Are slots filled evenly across time?

**Key insight:** Both extremes are bad:
- Too low: Overloads on specific people/times
- Too high: No structure, hard to plan around

**When to use:** Detect imbalances in workload distribution. Ensure variety in rotation assignments.

---

### 5. Phase Transitions

**Location:** `thermodynamics/phase_transitions.py`

**Source:** Critical phenomena (Scheffer et al., 2009)

#### Common Intuition
"Detect sudden changes."

#### What It Actually Does
Detects **early warning signals** that precede sudden system transitions.

**Universal early warning signals:**
1. **Variance increase**: Fluctuations grow before transition
2. **Autocorrelation increase**: System "remembers" longer (critical slowing down)
3. **Skewness changes**: Distribution becomes asymmetric
4. **Flickering**: Rapid switching between states

**Physical analogy:**
- Water approaching boiling point
- Bubbles appear (increased variance)
- Temperature fluctuations last longer (autocorrelation)
- Eventually: phase transition to vapor

**Scheduling application:**
- Burnout rates fluctuating more → transition coming
- Coverage issues autocorrelating week-to-week → critical slowing down
- Morale flickering between high and low → bistability

**When to use:** Continuous monitoring of metrics. These signals appear BEFORE the transition, providing time to intervene.

---

### 6. Free Energy

**Location:** `thermodynamics/free_energy.py`

**Source:** Statistical mechanics (Helmholtz)

#### Common Intuition
"Another quality metric."

#### What It Actually Does
Balances **constraint satisfaction** (energy) against **flexibility** (entropy).

**Helmholtz free energy:** F = U - TS

- **U (internal energy):** Cost of constraint violations
- **T (temperature):** Exploration parameter
- **S (entropy):** Configuration diversity

**Key insight:** The best schedule isn't necessarily the one with lowest violations (U). It's the one with lowest **free energy** - balancing quality against flexibility.

**Why this matters:**
- Schedule A: 0 violations, but rigid (low S) → F = 0 - 0 = 0
- Schedule B: 2 violations, but flexible (high S) → F = 2 - 1×3 = -1
- Schedule B is better (lower F) despite more violations

**When to use:** Compare schedules that differ in constraint tightness. A slightly worse but more flexible schedule may be preferable.

---

### 7. Le Chatelier's Principle

**Location:** `le_chatelier.py`

**Source:** Physical chemistry (Le Chatelier, 1884)

#### Common Intuition
"The system will compensate for stress."

#### What It Actually Does
Models how systems **partially counteract** applied stress.

**The principle:** When stressed, a system shifts to reduce the stress. But the compensation is always **partial**.

**Scheduling application:**
- Stress: Lose 2 faculty members
- Response: Overtime, cross-coverage, deferred leave
- New equilibrium: Higher workload per person, but sustainable

**Key insight:** The system WILL compensate, but:
1. Compensation has costs (overtime → fatigue)
2. New equilibrium differs from old
3. Fighting the new equilibrium is often futile

**Types of compensation tracked:**
- `OVERTIME`: Extra hours (unsustainable long-term)
- `CROSS_COVERAGE`: Covering unfamiliar areas (quality risk)
- `DEFERRED_LEAVE`: Postponed time off (debt accumulates)
- `SERVICE_REDUCTION`: Reduced scope (capability loss)
- `QUALITY_TRADE`: Lower standards (dangerous)

**When to use:** After capacity changes, predict how the system will adapt and what the new equilibrium will look like.

---

### 8. Creep/Fatigue

**Location:** `creep_fatigue.py`

**Source:** Materials science

#### Common Intuition
"Track cumulative stress."

#### What It Actually Does
Models two distinct failure modes:

**Creep (constant load over time):**
- Primary: Adaptation phase (strain rate decreasing)
- Secondary: Steady state (sustainable)
- Tertiary: Accelerating damage (approaching failure)

**Fatigue (cyclic loading):**
- S-N curves: Higher stress = fewer cycles to failure
- Miner's Rule: D = Σ(n_i / N_i), failure when D ≥ 1.0

**Scheduling application:**
- Creep: Sustained high workload without breaks
- Fatigue: Rotation changes, shift pattern variations

**Key insight:**
- Creep and fatigue are different mechanisms
- Same total stress can cause different outcomes depending on pattern
- 60 hours/week for 10 weeks (creep) ≠ alternating 80/40 weeks (fatigue)

**Key outputs:**
- `creep_stage`: PRIMARY/SECONDARY/TERTIARY
- `miner_damage`: Cumulative fatigue damage (0-1)
- `time_to_failure`: Predicted time until burnout

**When to use:** Distinguish between sustained overwork and cyclical stress patterns. Different interventions needed.

---

### 9. Stigmergy (Ant Colony)

**Location:** `stigmergy.py`

**Source:** Swarm intelligence (Grasse, 1959)

#### Common Intuition
"AI learns preferences."

#### What It Actually Does
Models **indirect coordination** through environment modification.

**Ant colony analogy:**
- Ants deposit pheromones on paths
- Other ants follow stronger trails
- Good paths get reinforced, bad paths evaporate
- No central coordinator needed

**Scheduling application:**
- "Pheromones" = recorded preferences
- Accepted assignments reinforce trails
- Complaints weaken trails
- Trails evaporate over time (recency matters)

**Key insight:** Preferences are **emergent** from behavior, not just declared. Someone who says they hate Mondays but never complains about Monday assignments actually doesn't mind.

**Trail types:**
- `PREFERENCE`: Positive affinity for slots
- `AVOIDANCE`: Negative affinity
- `SWAP_AFFINITY`: Willingness to trade with specific people
- `WORKLOAD`: Preferred work patterns
- `SEQUENCE`: Preferred assignment sequences

**When to use:** Learning implicit preferences from behavior. Resolving conflicts through trail strength rather than arbitrary rules.

---

### 10. Transcription Factors

**Location:** `transcription_factors.py`

**Source:** Molecular biology (gene regulation)

#### Common Intuition
"Fancy constraint weighting."

#### What It Actually Does
Models constraints as "genes" regulated by context-dependent "transcription factors."

**Biological analogy:**
- DNA (constraints) is always present
- Transcription factors (context) determine which genes are "expressed"
- Same genome, different expression in different tissues

**Scheduling application:**
- Constraint: "Maximum 60 hours/week"
- Normal context: Strictly enforced (TF inactive)
- Emergency context: Relaxed (TF activates "emergency" program)
- The constraint exists in both, but its effective weight changes

**Key concepts:**
- **Master regulators:** Patient safety TF always active, controls hierarchy
- **Cascade effects:** One TF activates another
- **Combinatorial logic:** Multiple TFs needed for specific outcomes
- **Chromatin state:** System mode determines accessible constraints

**When to use:** Context-sensitive constraint management. Graceful degradation under stress. Different operational modes (normal vs. crisis).

---

## Quick Reference

| Module | Source | Key Metric | Use When |
|--------|--------|------------|----------|
| Spin Glass | Physics | Frustration score | Conflicting preferences |
| Metastability | Physics | Barrier height | Schedule seems stuck |
| Catastrophe | Math | Critical parameters | Detecting tipping points |
| Entropy | Info theory | Distribution evenness | Checking balance |
| Phase Transitions | Physics | Variance/autocorrelation | Early warning |
| Free Energy | Thermodynamics | F = U - TS | Comparing flexibility |
| Le Chatelier | Chemistry | Compensation cost | After capacity changes |
| Creep/Fatigue | Materials | Miner's damage | Sustained vs cyclic stress |
| Stigmergy | Biology | Trail strength | Learning preferences |
| Transcription | Biology | TF activation | Context-sensitive rules |

---

## The Meta-Pattern

All exotic modules share a structure:
1. **Physical/biological system** with well-understood dynamics
2. **Mathematical formulation** that captures those dynamics
3. **Scheduling analog** where the same dynamics apply
4. **Actionable outputs** for decision-making

The insight isn't "scheduling is like physics." It's "scheduling exhibits the same mathematical patterns as these physical systems, so the same analytical tools apply."

---

*Document created January 2026.*
