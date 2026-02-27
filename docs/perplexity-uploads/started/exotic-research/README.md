# Exotic Physics & Cross-Disciplinary Research Upload

Upload folder for Perplexity Computer sessions focused on novel physics, topology, network science, and complex systems approaches to scheduling optimization.

## Usage

1. Upload all files from this folder to Perplexity Computer
2. Paste the contents of `PROMPT.md` as the session prompt
3. Perplexity Computer will work through 8 research sections

## File Manifest

| Upload Path | Original Source Path | Size |
|-------------|---------------------|------|
| **solver/** (optimization context) | | |
| `solver/activity_solver.py` | `backend/app/scheduling/activity_solver.py` | 156K |
| `solver/constraints_config.py` | `backend/app/scheduling/constraints/config.py` | 22K |
| **exotic/** (already implemented) | | |
| `exotic/spin_glass.py` | `backend/app/resilience/exotic/spin_glass.py` | 11K |
| `exotic/foam_topology.py` | `backend/app/resilience/exotic/foam_topology.py` | 15K |
| `exotic/catastrophe.py` | `backend/app/resilience/exotic/catastrophe.py` | 12K |
| `exotic/metastability.py` | `backend/app/resilience/exotic/metastability.py` | 11K |
| **thermodynamics/** (already implemented) | | |
| `thermodynamics/entropy.py` | `backend/app/resilience/thermodynamics/entropy.py` | 13K |
| `thermodynamics/free_energy.py` | `backend/app/resilience/thermodynamics/free_energy.py` | 14K |
| `thermodynamics/phase_transitions.py` | `backend/app/resilience/thermodynamics/phase_transitions.py` | 19K |
| **resilience/** (cross-disciplinary) | | |
| `resilience/homeostasis.py` | `backend/app/resilience/homeostasis.py` | 45K |
| `resilience/le_chatelier.py` | `backend/app/resilience/le_chatelier.py` | 29K |
| `resilience/creep_fatigue.py` | `backend/app/resilience/creep_fatigue.py` | 21K |
| `resilience/stigmergy.py` | `backend/app/resilience/stigmergy.py` | 29K |
| `resilience/circadian_model.py` | `backend/app/resilience/circadian_model.py` | 29K |
| **research/** (existing analysis) | | |
| `research/ADR-009-time-crystal-scheduling.md` | `docs/architecture/decisions/ADR-009-time-crystal-scheduling.md` | 7K |
| `research/circadian-workload-resonance.md` | `docs/architecture/circadian-workload-resonance.md` | 19K |
| `research/EXOTIC_CANDIDATES_REVIEW.md` | `docs/resilience/EXOTIC_CANDIDATES_REVIEW.md` | 6K |
| `research/THERMODYNAMIC_RESEARCH_SUMMARY.md` | `docs/research/THERMODYNAMIC_RESEARCH_SUMMARY.md` | 18K |

## Research Sections

| # | Section | Focus |
|---|---------|-------|
| 1 | Gap Analysis | What physics domains are NOT yet represented? |
| 2 | Phase Transition Criticality | SAT-UNSAT boundary, critical constraint density |
| 3 | Fluctuation-Dissipation | Non-invasive stress testing from natural variability |
| 4 | Topological Data Analysis | Shape of feasible schedule space, persistent homology |
| 5 | Swarm Intelligence | ACO, PSO, CMA-ES, multi-agent RL for scheduling |
| 6 | Quantum-Inspired Approaches | SQA, QAOA heuristics, tensor networks (classical) |
| 7 | Network Science | Percolation, community detection, temporal networks |
| 8 | Literature Synthesis | Unifying framework + top 5 recommendations |

## Disciplines Already Represented in Codebase

- Statistical mechanics (spin glass, Boltzmann, entropy)
- Thermodynamics (free energy, phase transitions, dissipative structures)
- Topology (foam topology / Plateau's laws)
- Catastrophe theory (cusp catastrophe for tipping points)
- Materials science (creep/fatigue for burnout)
- Chemistry (Le Chatelier equilibrium)
- Physiology (homeostasis, allostatic load)
- Chronobiology (circadian phase response curves)
- Swarm intelligence (stigmergy / ant colony)
- Ecology (keystone species — in main resilience/, not uploaded)
- Epidemiology (contagion model — in main resilience/, not uploaded)
- Nuclear engineering (defense in depth — in main resilience/, not uploaded)
- Telecommunications (Erlang queueing — in main resilience/, not uploaded)

## Notes

- This folder is gitignored — contains copies, not originals
- No PII: all source code and sanitized research docs
- Total size: ~476K
- The solver files provide context on the optimization problem; the rest show what physics metaphors are already implemented so Perplexity can focus on what's NEW
