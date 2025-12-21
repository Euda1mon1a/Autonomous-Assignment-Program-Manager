***REMOVED*** Scheduling Libraries Research

> **Research Date:** 2025-12-21
> **Purpose:** Evaluate existing libraries for implementing the Unified Autonomous Scheduling Architecture and Workforce Resilience Engineering Architecture

---

***REMOVED******REMOVED*** Executive Summary

This research evaluates existing Python libraries that could support the implementation of two advanced scheduling architectures:

1. **Unified Autonomous Scheduling Architecture** - Immune-Tensegrity Market model
2. **Workforce Resilience Engineering Architecture** - Safety-Critical Scheduler model

***REMOVED******REMOVED******REMOVED*** Key Findings

| Category | Recommended Libraries | Integration Priority |
|----------|----------------------|---------------------|
| **Already in Repo** | NetworkX, OR-Tools, NumPy/SciPy, pymoo | ✅ Available |
| **High Priority (P1)** | pyspc, manufacturing, ndlib, aisp | Add immediately |
| **Medium Priority (P2)** | pyworkforce, obspy | Add for advanced features |
| **Low Priority (P3)** | cffdrs_py, rgpy | Reference implementations |

---

***REMOVED******REMOVED*** Part 1: Unified Autonomous Scheduling Architecture Libraries

***REMOVED******REMOVED******REMOVED*** 1.1 Economic Layer: Mechanism Design & Auction Theory

***REMOVED******REMOVED******REMOVED******REMOVED*** VCG Auction Libraries

| Library | Source | Status | Notes |
|---------|--------|--------|-------|
| [VCG-Auction-Mechanism](https://github.com/ZhuangDingyi/VCG-Auction-Mechanism) | GitHub | Academic | McGill COMP 553 implementation |
| [kqshan/vcg-auction](https://github.com/kqshan/vcg-auction) | GitHub | General | Multi-item VCG auctions |
| [QuantEcon GC_Mechanism](https://python.quantecon.org/house_auction.html) | QuantEcon | Educational | Good for learning |

**Recommendation:** Implement custom VCG based on existing patterns. No production-ready library exists.

***REMOVED******REMOVED******REMOVED******REMOVED*** Karma/Scrip Mechanism

| Library | Source | Status | Notes |
|---------|--------|--------|-------|
| [Karma Framework](https://arxiv.org/html/2407.05132) | Academic | Python/GPL 3.0 | Full game-theoretic implementation |

**Key Features:**
- Three-step approach: Modeling → Optimization → Simulation
- Nash equilibrium computation
- Multi-agent system simulation
- Well-documented, open-source (Python, PEP8, GPL 3.0)

**Reference:** [A Self-Contained Karma Economy](https://link.springer.com/article/10.1007/s13235-023-00503-0) (Dynamic Games and Applications, 2023)

**Use Case for Repo:** Shift swap bidding, on-call assignment allocation

---

***REMOVED******REMOVED******REMOVED*** 1.2 Immunological Layer: Artificial Immune Systems (AIS)

***REMOVED******REMOVED******REMOVED******REMOVED*** Primary Library: AISP

| Library | Install | Python | Features |
|---------|---------|--------|----------|
| [aisp](https://github.com/AIS-Package/aisp) | `pip install aisp` | 3.10+ | RNSA, BNSA, AIRS, Clonal Selection |

**Key Features:**
- **Negative Selection Algorithm (NSA):** Generates detectors that identify anomalies
- **Clonal Selection (CLONALG):** Adaptive mutation for solution refinement
- **Real-Valued NSA (RNSA):** Supports continuous state vectors
- Example notebooks for Iris, Geyser, Mushroom datasets

**Use Case for Repo:**
- Detect "Non-Self" schedule states (constraint violations, anomalous patterns)
- Automatic deadlock resolution via digital antibodies (micro-schedule patches)

**Code Example:**
```python
from aisp.NSA import RNSA

***REMOVED*** Train on valid schedules (Self)
detector = RNSA(N=100, r=0.1)
detector.fit(valid_schedule_vectors)

***REMOVED*** Monitor for anomalies (Non-Self)
if detector.predict(current_state) == 1:
    trigger_clonal_selection_repair()
```

**Documentation:** [AISP Docs](https://ais-package.github.io/docs/intro/)

---

***REMOVED******REMOVED******REMOVED*** 1.3 Physics Layer: Structural Rigidity & Tensegrity

***REMOVED******REMOVED******REMOVED******REMOVED*** Pebble Game Algorithm (Rigidity Analysis)

| Library | Source | Status | Notes |
|---------|--------|--------|-------|
| [TRAMbio](https://link.springer.com/article/10.1186/s12859-025-06300-3) | BMC Bioinformatics | **NEW (Oct 2025)** | (k,ℓ)-sparse graphs, Laman recognition |
| [Pebble-Game](https://github.com/CharlesLiu7/Pebble-Game) | GitHub | Academic | Direct paper implementation |

**TRAMbio Key Features:**
- General class of pebble game algorithms for (k,ℓ)-sparse graphs
- Recognizes Laman graphs (planar bar-and-joint rigidity)
- Domain-agnostic despite molecular biology focus
- O(n²) basic algorithm, O(nm) for dense graphs

**Use Case for Repo:**
- Identify over-constrained ("stressed") schedule regions
- Detect under-constrained ("floppy") areas needing additional constraints
- Model: Tasks = Nodes, Constraints = Edges

***REMOVED******REMOVED******REMOVED******REMOVED*** Force Density Method (Tensegrity Solver)

| Library | Source | Language | Notes |
|---------|--------|----------|-------|
| [TsgFEM](https://github.com/Muhao-Chen/Tensegrity_Finite_Element_Method_TsgFEM) | GitHub | MATLAB/Python | Full FEM for tensegrity |
| SciPy sparse solvers | Built-in | Python | `scipy.sparse.linalg.spsolve` |

**Force Density Equation:** `F · x = p`
- `x`: Vector of node coordinates (timestamps)
- `F`: Force Density Matrix (topology + stiffness)
- `p`: External anchor forces (e.g., "Start Time = 0")

**SciPy Implementation:**
```python
from scipy.sparse.linalg import spsolve
from scipy.sparse import csr_matrix

***REMOVED*** Build force density matrix F from constraint graph
F = build_force_density_matrix(constraints)
p = build_anchor_vector(fixed_times)

***REMOVED*** Direct solve - no iteration needed
x = spsolve(F, p)  ***REMOVED*** Stable schedule timestamps
```

**Use Case for Repo:**
- Global equilibrium schedule finding
- Instant feasibility determination via linear solve

---

***REMOVED******REMOVED******REMOVED*** 1.4 Governor Layer: Renormalization Group (RG)

| Library | Source | Status | Notes |
|---------|--------|--------|-------|
| [rgpy](https://github.com/jqhoogland/rgpy) | GitHub | ML-focused | RG + Machine Learning |
| [FlowPy](https://www.sciencedirect.com/science/article/abs/pii/S0010465513000994) | ScienceDirect | Research | Functional RG equations |
| [NRG Ljubljana](http://nrgljubljana.ijs.si/) | Academic | C++/Python | Numerical RG framework |

**rgpy Features:**
- RG techniques with ML emphasis
- Critical exponent calculation
- Standard renormalization tools

**Use Case for Repo:**
- Multi-scale stability management
- Coarse-graining: Combine micro-tasks into block spins
- Identify "relevant" (structural bottleneck) vs "irrelevant" (noise) parameters

---

***REMOVED******REMOVED*** Part 2: Workforce Resilience Engineering Libraries

***REMOVED******REMOVED******REMOVED*** 2.1 Safety Layer: Process Safety & Sterile Cockpit

**No specific libraries needed** - Implement as business logic using existing FHIR schemas and state machines.

**Implementation Pattern:**
```python
***REMOVED*** Engineering Control - Hard Stop
if provider.lmp_score > CRITICAL_THRESHOLD:
    slot.status = "busy-unavailable"  ***REMOVED*** Phantom appointment

***REMOVED*** Sterile Cockpit - Signal Suppression
if block.service_type == "HighAcuity":
    message_queue.suppress(priority_below="Emergency")
```

---

***REMOVED******REMOVED******REMOVED*** 2.2 Capacity Layer: Advanced Queuing Theory

***REMOVED******REMOVED******REMOVED******REMOVED*** Primary Library: pyworkforce

| Library | Install | Features |
|---------|---------|----------|
| [pyworkforce](https://github.com/rodrigo-arenas/pyworkforce) | `pip install pyworkforce` | Erlang C, Multi-Erlang, Scheduling |

**Key Classes:**
- `ErlangC`: Basic staffing calculation with abandonment
- `MultiErlangC`: Parameter grid search
- `MinAbsDifference`: Shift optimization
- `MinRequiredResources`: Cost-weighted scheduling

**Code Example:**
```python
from pyworkforce.queuing import ErlangC

erlang = ErlangC(
    transactions=100,      ***REMOVED*** λ: Arrival rate
    asa=20/60,            ***REMOVED*** Target answer time (min)
    aht=3,                ***REMOVED*** μ⁻¹: Avg handle time (min)
    interval=30,          ***REMOVED*** Planning interval
    shrinkage=0.3         ***REMOVED*** Staff unavailability
)

result = erlang.required_positions(
    service_level=0.8,
    max_occupancy=0.85
)
***REMOVED*** Returns: positions, service_level, occupancy, waiting_probability
```

**Erlang X (Abandonment Model):**
- pyworkforce implements basic abandonment via shrinkage
- For full Erlang X with blocking, see [CCmath tools](https://www.ccmath.com/erlangc-vs-erlangx/)

**Use Case for Repo:** Specialist coverage optimization, clinic staffing

---

***REMOVED******REMOVED******REMOVED*** 2.3 Physiology Layer: Thermodynamics & Materials Science

***REMOVED******REMOVED******REMOVED******REMOVED*** Larson-Miller Parameter (LMP)

**No Python library exists** - Implement formula directly:

```python
import numpy as np

def larson_miller_parameter(temperature_kelvin: float, time_hours: float, C: float = 20) -> float:
    """
    Calculate Larson-Miller Parameter for creep/fatigue prediction.

    LMP = T * (C + log10(t))

    For scheduling context:
    - T → Clinical Intensity (normalized)
    - t → Shift Duration (hours)
    """
    return temperature_kelvin * (C + np.log10(time_hours))

def max_shift_duration(clinical_intensity: float, lmp_limit: float, C: float = 20) -> float:
    """
    Given intensity and LMP limit, calculate maximum safe shift duration.

    t_max = 10^((LMP_limit / T) - C)
    """
    return 10 ** ((lmp_limit / clinical_intensity) - C)
```

**Reference:** [Larson-Miller Relation](https://en.wikipedia.org/wiki/Larson–Miller_relation)

***REMOVED******REMOVED******REMOVED******REMOVED*** Biomathematical Fatigue Models

| Model | Type | Availability |
|-------|------|--------------|
| SAFTE-FAST | Commercial | Fatigue Science (proprietary) |
| FAID | Commercial | InterDynamics (proprietary) |
| Three-Process Model | Academic | Public domain, implement manually |

**Simplified Fatigue Implementation:**
```python
def biomathematical_fatigue(work_history_14d: list[dict]) -> float:
    """
    Simplified BFM based on cumulative work-rest imbalance.

    BFM = Σ(work_hours × intensity) - Σ(rest_hours × recovery_rate)
    """
    fatigue_score = 0
    for day in work_history_14d:
        fatigue_score += day['work_hours'] * day['intensity']
        fatigue_score -= day['rest_hours'] * RECOVERY_RATE
    return max(0, fatigue_score)
```

**Use Case for Repo:** Provider availability constraints, burnout prevention

---

***REMOVED******REMOVED******REMOVED*** 2.4 Stability Layer: SPC & Resilience

***REMOVED******REMOVED******REMOVED******REMOVED*** Primary Library: pyspc

| Library | Install | Features |
|---------|---------|----------|
| [pyspc](https://github.com/carlosqsilva/pyspc) | `pip install pyspc` | Control charts, Western Electric rules |

**Supported Rules:**
- `RULE_1_BEYOND_3SIGMA`: Catastrophic surge
- `RULE_7_ON_ONE_SIDE` / `RULE_8_ON_ONE_SIDE`: Process drift
- WECO rules (commented in source, easy to enable)

**Code Example:**
```python
from pyspc import spc, xbar_rbar, rules

***REMOVED*** Monitor workload metrics
workload_data = get_documentation_time_series()
chart = spc(workload_data) + xbar_rbar() + rules()

***REMOVED*** Check for out-of-control signals
if chart.has_violations():
    trigger_operating_mode_change()
```

**Alternative:** [WE_Rules](https://github.com/bman511/WE_Rules) - Pure numpy/statistics implementation

***REMOVED******REMOVED******REMOVED******REMOVED*** Process Capability (Cp/Cpk)

| Library | Install | Features |
|---------|---------|----------|
| [manufacturing](https://pypi.org/project/manufacturing/) | `pip install manufacturing` | Cp/Cpk, control charts |

**Code Example:**
```python
from manufacturing import ppk_plot, control_chart

***REMOVED*** Schedule quality metrics
ppk_plot(
    data=shift_coverage_data,
    upper_control_limit=1.2,  ***REMOVED*** 120% staffing
    lower_control_limit=0.8   ***REMOVED*** 80% staffing
)
```

**Use Case for Repo:** Schedule quality monitoring, Six Sigma compliance

***REMOVED******REMOVED******REMOVED******REMOVED*** Clinical Danger Rating (Fire Index Analogy)

| Library | Install | Features |
|---------|---------|----------|
| [cffdrs_py](https://github.com/cffdrs/cffdrs_py) | `pip install cffdrs` | FWI, FBP systems |

**Adaptation for Clinical Context:**
```python
def clinical_danger_rating(
    occupancy: float,      ***REMOVED*** Ignition potential
    viral_rate: float,     ***REMOVED*** Spread rate
    acuity: float,         ***REMOVED*** Burning index
    staff_rest: float      ***REMOVED*** Fuel moisture (inverse)
) -> str:
    """
    CDR analogous to Canadian Fire Weather Index.
    """
    composite = (occupancy * 0.3 + viral_rate * 0.2 +
                 acuity * 0.3 + (1 - staff_rest) * 0.2)

    if composite < 0.3: return "LOW"
    elif composite < 0.5: return "MODERATE"
    elif composite < 0.7: return "HIGH"
    else: return "EXTREME"
```

---

***REMOVED******REMOVED******REMOVED*** 2.5 Social Layer: Epidemiology & Fairness

***REMOVED******REMOVED******REMOVED******REMOVED*** Network Diffusion: ndlib

| Library | Install | Features |
|---------|---------|----------|
| [ndlib](https://github.com/GiulioRossetti/ndlib) | `pip install ndlib` | SI, SIS, SEIR, opinion dynamics |

**Key Features:**
- Built on NetworkX
- Supports dynamic networks
- Visual interface available
- Extensible model framework

**Code Example:**
```python
import networkx as nx
import ndlib.models.epidemics as ep
from ndlib.models.ModelConfig import Configuration

***REMOVED*** Build social network of providers
G = build_provider_network()

***REMOVED*** Configure burnout contagion model
model = ep.SISModel(G)
config = Configuration()
config.add_model_parameter('beta', 0.05)  ***REMOVED*** Infection rate
config.add_model_parameter('lambda', 0.01)  ***REMOVED*** Recovery rate
model.set_initial_status(config)

***REMOVED*** Simulate spread
iterations = model.iteration_bunch(50)

***REMOVED*** Identify high-risk hubs for intervention
```

**Use Case for Repo:** Burnout contagion modeling, team composition optimization

***REMOVED******REMOVED******REMOVED******REMOVED*** Anomaly Detection (STA/LTA from Seismology)

| Library | Install | Features |
|---------|---------|----------|
| [obspy](https://docs.obspy.org/) | `pip install obspy` | STA/LTA trigger, AR-AIC picker |

**STA/LTA Concept:**
- **STA (Short-Term Average):** Detects rapid changes
- **LTA (Long-Term Average):** Establishes baseline
- **Trigger:** When STA/LTA ratio exceeds threshold

**Code Example:**
```python
from obspy.signal.trigger import recursive_sta_lta, trigger_onset

***REMOVED*** Apply to workload time series
workload_trace = get_hourly_workload()
cft = recursive_sta_lta(workload_trace, nsta=5, nlta=50)

***REMOVED*** Detect anomalies
triggers = trigger_onset(cft, thr_on=3.5, thr_off=0.5)
```

**Use Case for Repo:** Precursor signal detection for capacity surges

***REMOVED******REMOVED******REMOVED******REMOVED*** Gini Coefficient (Equity)

| Library | Install | Features |
|---------|---------|----------|
| [oliviaguest/gini](https://github.com/oliviaguest/gini) | GitHub | Fast numpy implementation |
| [IneqPy](https://pypi.org/project/IneqPy/) | `pip install IneqPy` | Gini, Atkinson, Theil |
| [QuantEcon](https://quantecon.org/quantecon-py/) | `pip install quantecon` | `qe.gini_coefficient` |

**Code Example:**
```python
import ineqpy

***REMOVED*** Calculate workload inequality
gini = ineqpy.gini(
    data=provider_df,
    income='intensity_adjusted_hours',
    weights='fte'
)

***REMOVED*** Optimize: Minimize Gini over rolling window
```

**Use Case for Repo:** Roster fairness optimization

---

***REMOVED******REMOVED*** Part 3: Already Available in Repository

The following libraries are already in `requirements.txt`:

| Library | Version | Current Use | Extended Use |
|---------|---------|-------------|--------------|
| `networkx` | ≥3.0 | Hub vulnerability analysis | Constraint graphs, social networks |
| `ortools` | ≥9.8 | CP-SAT scheduling | VCG solver integration |
| `numpy` | 2.3.5 | General | LMP, Gini, matrix ops |
| `scipy` | (via numpy) | Available | Force density solver |
| `pymoo` | ≥0.6.0 | Multi-objective | Pareto optimization |
| `pyqubo` | ≥1.4.0 | QUBO formulation | Combinatorial auctions |
| `pandas` | 2.3.3 | Data processing | Time series analysis |
| `plotly` | ≥5.18.0 | Visualization | Control charts |

---

***REMOVED******REMOVED*** Part 4: Recommended Library Additions

***REMOVED******REMOVED******REMOVED*** Priority 1 (Add Immediately)

```txt
***REMOVED*** Statistical Process Control
pyspc>=0.4                    ***REMOVED*** Western Electric rules, control charts

***REMOVED*** Process Capability / Six Sigma
manufacturing>=0.1.0          ***REMOVED*** Cp/Cpk metrics

***REMOVED*** Epidemiology / Network Diffusion
ndlib>=5.1.0                  ***REMOVED*** Burnout contagion modeling

***REMOVED*** Artificial Immune Systems
aisp>=1.0.0                   ***REMOVED*** RNSA, Clonal Selection for anomaly detection
```

***REMOVED******REMOVED******REMOVED*** Priority 2 (Add for Advanced Features)

```txt
***REMOVED*** Workforce Queuing Theory
pyworkforce>=0.5.1            ***REMOVED*** Erlang C staffing optimization

***REMOVED*** Time Series Anomaly Detection
obspy>=1.4.2                  ***REMOVED*** STA/LTA trigger detection

***REMOVED*** Inequality Metrics
IneqPy>=0.1.0                 ***REMOVED*** Gini, Atkinson, Theil indices
```

***REMOVED******REMOVED******REMOVED*** Priority 3 (Reference/Optional)

```txt
***REMOVED*** Fire Danger Index (reference implementation)
cffdrs>=0.1.0                 ***REMOVED*** Canadian Fire Weather Index

***REMOVED*** Renormalization Group
***REMOVED*** rgpy - install from GitHub if needed
```

---

***REMOVED******REMOVED*** Part 5: Implementation Roadmap

***REMOVED******REMOVED******REMOVED*** Phase 1: Foundation (Immediate)
1. Add P1 libraries to `requirements.txt`
2. Implement Gini coefficient in equity constraints
3. Add SPC monitoring to existing metrics

***REMOVED******REMOVED******REMOVED*** Phase 2: Immune System (Short-term)
1. Train RNSA detectors on valid schedule corpus
2. Implement clonal selection for deadlock resolution
3. Add "digital antibody" library of schedule patches

***REMOVED******REMOVED******REMOVED*** Phase 3: Physics Layer (Medium-term)
1. Implement pebble game for rigidity analysis
2. Add force density solver for equilibrium schedules
3. Integrate with existing constraint system

***REMOVED******REMOVED******REMOVED*** Phase 4: Economic Layer (Long-term)
1. Implement Karma mechanism for swap bidding
2. Add VCG auction for high-value slot allocation
3. Integrate with existing swap management system

---

***REMOVED******REMOVED*** Sources

***REMOVED******REMOVED******REMOVED*** VCG/Mechanism Design
- [ZhuangDingyi/VCG-Auction-Mechanism](https://github.com/ZhuangDingyi/VCG-Auction-Mechanism)
- [QuantEcon Multiple Good Allocation](https://python.quantecon.org/house_auction.html)

***REMOVED******REMOVED******REMOVED*** Karma Systems
- [Fair Money – Karma Economies](https://arxiv.org/html/2407.05132)
- [Self-Contained Karma Economy](https://link.springer.com/article/10.1007/s13235-023-00503-0)

***REMOVED******REMOVED******REMOVED*** Artificial Immune Systems
- [AISP Documentation](https://ais-package.github.io/docs/intro/)
- [AISP GitHub](https://github.com/AIS-Package/aisp)

***REMOVED******REMOVED******REMOVED*** Tensegrity/Rigidity
- [TRAMbio](https://link.springer.com/article/10.1186/s12859-025-06300-3)
- [Pebble-Game](https://github.com/CharlesLiu7/Pebble-Game)
- [TsgFEM](https://github.com/Muhao-Chen/Tensegrity_Finite_Element_Method_TsgFEM)

***REMOVED******REMOVED******REMOVED*** SPC/Quality
- [pyspc](https://github.com/carlosqsilva/pyspc)
- [manufacturing (PyPI)](https://pypi.org/project/manufacturing/)

***REMOVED******REMOVED******REMOVED*** Epidemiology
- [NDlib Documentation](https://ndlib.readthedocs.io/)
- [NDlib Paper](https://arxiv.org/pdf/1801.05854)

***REMOVED******REMOVED******REMOVED*** Workforce/Queuing
- [pyworkforce](https://github.com/rodrigo-arenas/pyworkforce)
- [pyworkforce Docs](https://pyworkforce.readthedocs.io/)

***REMOVED******REMOVED******REMOVED*** Seismology/Anomaly Detection
- [ObsPy Trigger Tutorial](https://docs.obspy.org/tutorial/code_snippets/trigger_tutorial.html)

***REMOVED******REMOVED******REMOVED*** Fire Index
- [cffdrs_py](https://github.com/cffdrs/cffdrs_py)

***REMOVED******REMOVED******REMOVED*** Materials Science
- [Larson-Miller Relation](https://en.wikipedia.org/wiki/Larson–Miller_relation)

***REMOVED******REMOVED******REMOVED*** Inequality Metrics
- [IneqPy](https://pypi.org/project/IneqPy/)
- [oliviaguest/gini](https://github.com/oliviaguest/gini)
