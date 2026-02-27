# Exotic Physics & Cross-Disciplinary Research for Scheduling Optimization

Upload all files from this folder, then paste the prompt below.

---

## System Context

Military Family Medicine residency scheduling system using Google OR-Tools CP-SAT solver (>=9.8,<9.9). The solver assigns activities to half-day slots across 28-day blocks for ~12 residents (PGY 1-3) and ~8 faculty, with 25+ soft constraint penalty weights forming a multi-objective optimization landscape.

**What you're looking at:**
- `solver/` — The actual CP-SAT solver with 25+ penalty weights and constraint priority system
- `exotic/` — Already-implemented physics-inspired modules (spin glass, foam topology, catastrophe theory, metastability)
- `thermodynamics/` — Implemented thermodynamic modules (entropy, free energy, phase transitions)
- `resilience/` — Cross-disciplinary modules (homeostasis from physiology, Le Chatelier from chemistry, creep/fatigue from materials science, stigmergy from swarm intelligence, circadian from chronobiology)
- `research/` — Existing research docs covering time crystals, thermodynamic foundations, and an exotic candidates review

**Key insight:** The 25-weight penalty function in `activity_solver.py` defines an energy landscape. The constraint priorities in `constraints_config.py` define a hierarchy. Together they create a frustrated optimization surface — exactly the kind of system where statistical physics, topology, and complex systems theory apply.

---

## Section 1: Gap Analysis — What's Missing from the Physics Toolkit

**Files:** All uploaded files

Review every implemented module and research document. Then identify:

1. **Which physics/math domains are NOT yet represented** that would provide novel insight for this scheduling problem? Consider:
   - Percolation theory (when does the schedule "break through" from feasible to infeasible?)
   - Renormalization group (coarse-graining the constraint hierarchy — which constraints can be abstracted away at different scales?)
   - Topological data analysis / persistent homology (what is the "shape" of the feasible schedule space?)
   - KAM theorem / near-integrable systems (how robust is the schedule to small perturbations?)
   - Ising model extensions beyond spin glass (mean field theory for schedule ensembles?)
   - Reaction-diffusion systems (how do coverage gaps propagate across the schedule?)
   - Random matrix theory (spectral properties of the constraint coupling matrix?)

2. **Which existing modules have the wrong physics metaphor** or are using it superficially?

3. **Which implemented concepts overlap** and could be unified under a common mathematical framework?

Deliver: Ranked list of top 10 unexplored approaches with: concept name, source field, specific application to this scheduler, expected insight, implementation complexity (trivial/moderate/hard), and 2-3 key references.

---

## Section 2: Phase Transition Criticality

**Files:** `solver/activity_solver.py`, `solver/constraints_config.py`, `thermodynamics/phase_transitions.py`, `exotic/catastrophe.py`

The CP-SAT solver operates near the SAT-UNSAT boundary — adding one more constraint can flip the problem from feasible to infeasible. This is a classic phase transition in computational complexity.

Research:
1. **SAT-UNSAT phase transitions in constraint satisfaction problems** — What does the literature say about the critical constraint density for problems of this structure (~12 workers × 56 slots × 6 activities × 25 constraints)?
2. **Random constraint satisfaction ensembles** — Can we estimate WHERE our problem sits relative to the critical threshold?
3. **Algorithmic implications** — Do CP-SAT solvers exhibit critical slowing near the phase boundary? What search strategies help?
4. **Early warning signals** — Can we detect from the solver's behavior (runtime, conflict count, restarts) that we're approaching the phase boundary before it becomes infeasible?

Deliver: Mathematical framework for estimating this system's distance from criticality, with practical metrics extractable from OR-Tools solver logs.

---

## Section 3: Fluctuation-Dissipation & Non-Invasive Stress Testing

**Files:** `resilience/homeostasis.py`, `thermodynamics/entropy.py`, `thermodynamics/free_energy.py`

The fluctuation-dissipation theorem (FDT) says you can predict a system's response to perturbation by measuring its natural fluctuations — WITHOUT actually perturbing it.

**Application:** Instead of running N contingency simulations ("what if Dr. X is absent?"), measure natural schedule variability and infer resilience from it.

Research:
1. **FDT in complex networks** — Recent papers applying FDT to network systems (scheduling is a bipartite graph)
2. **Noise spectrum analysis** — White noise (healthy) vs. pink/red noise (critical) in scheduling metrics
3. **Generalized FDT for far-from-equilibrium systems** — Schedules are dissipative structures, not equilibrium. What corrections apply?
4. **Practical implementation** — What time series do we need to collect? How long a history? What spectral analysis method?

Deliver: Concrete algorithm for predicting faculty-loss resilience from historical schedule fluctuation data, with confidence bounds.

---

## Section 4: Topological Data Analysis for Schedule Space

**Files:** `solver/activity_solver.py`, `exotic/foam_topology.py`

Persistent homology and TDA can reveal the "shape" of high-dimensional data. The feasible schedule space is a high-dimensional polytope defined by constraint intersections.

Research:
1. **TDA applied to combinatorial optimization** — Any work on analyzing feasible regions of constraint programs?
2. **Persistent homology for scheduling** — Can Betti numbers tell us about the connectivity and holes in the schedule space?
3. **Practical TDA libraries** — What Python libraries (ripser, gudhi, giotto-tda) could analyze schedule solution sets?
4. **Foam topology connection** — The existing `foam_topology.py` uses Plateau's laws. How does this relate to formal TDA? Can they be unified?

Deliver: Research summary with assessment of whether TDA provides actionable insight for a scheduling system of this scale, or if it's computationally intractable.

---

## Section 5: Swarm Intelligence & Collective Computation

**Files:** `resilience/stigmergy.py`, `exotic/spin_glass.py`

The existing stigmergy module uses ant-colony pheromone trails. The spin glass module uses replica exchange. Both are forms of collective computation.

Research:
1. **Ant colony optimization (ACO) for scheduling** — State of the art for nurse rostering / personnel scheduling
2. **Particle swarm optimization (PSO)** — Hybrid with CP-SAT as a local search engine
3. **Evolutionary strategies for weight tuning** — CMA-ES for the 25-weight penalty landscape
4. **Multi-agent reinforcement learning** — Recent work on RL for combinatorial optimization (2023-2026)
5. **Collective intelligence for human-in-the-loop** — How to incorporate coordinator preferences as a "social force" in the optimization

Deliver: Top 3 most promising swarm/collective approaches with: expected improvement over current CP-SAT-only approach, integration difficulty, and Python library recommendations.

---

## Section 6: Quantum-Inspired Approaches

**Files:** `solver/activity_solver.py`, `exotic/spin_glass.py`, `exotic/metastability.py`

NOT actual quantum computing — but quantum-inspired classical algorithms:

Research:
1. **Simulated quantum annealing** — Does SQA outperform SA for frustrated scheduling problems?
2. **QAOA-inspired heuristics** — Quantum Approximate Optimization Algorithm patterns adapted for classical CP-SAT
3. **Tensor network methods** — Can MPS/DMRG techniques efficiently sample from the schedule distribution?
4. **Variational approaches** — VQE-inspired warm-start strategies for the CP-SAT solver

Deliver: Honest assessment of whether quantum-inspired methods add value for this problem size (~12×56×6 = ~4000 binary variables), or if classical CP-SAT is already sufficient.

---

## Section 7: Network Science for Schedule Graphs

**Files:** `resilience/homeostasis.py`, `solver/constraints_config.py`

The schedule is a bipartite graph (residents ↔ activities) with temporal layers. The constraint system creates coupling between nodes.

Research:
1. **Small-world properties** — Does the constraint coupling network have small-world topology? Implications for failure propagation?
2. **Percolation theory** — At what node removal rate does the schedule lose coverage connectivity?
3. **Community detection** — Can graph clustering reveal natural "scheduling groups" that should be handled as units?
4. **Centrality measures for scheduling** — Beyond the existing hub analysis — what do betweenness, eigenvector, and Katz centrality reveal about schedule vulnerability?
5. **Temporal networks** — The schedule has a time dimension. How do temporal network metrics apply?

Deliver: Specific network metrics worth computing for this scheduling system, with interpretation guide for non-physicists (coordinators).

---

## Section 8: Literature Synthesis & Unifying Framework

After completing Sections 1-7, synthesize:

1. **Is there a unifying mathematical framework** that connects the thermodynamic, topological, network, and swarm approaches? (Hint: look at statistical field theory, information geometry, or category theory as potential unifiers)
2. **Priority ranking** — Which 5 approaches should be implemented first, considering: insight value, implementation effort, novelty (not already in our codebase), and practical utility for a 12-resident scheduling system?
3. **Research roadmap** — What experiments would validate or invalidate these approaches for scheduling? Design a 3-month research plan.

Deliver: Executive summary with top 5 recommendations and a concrete research roadmap.
