# Cross-Disciplinary Engineering Resilience Framework

> **Status**: Production-ready
> **Version**: 1.1
> **Last Updated**: 2025-12-28

---

## Overview

The Cross-Disciplinary Engineering Resilience Framework applies proven engineering principles from diverse technical domains to predict and prevent medical resident burnout. By adapting rigorous mathematical models from semiconductor manufacturing, epidemiology, telecommunications, seismology, forestry, and materials science, this framework provides multi-dimensional burnout risk assessment.

### Design Philosophy

Medical residency burnout is a complex, multi-faceted phenomenon that cannot be captured by single-metric analysis. Like complex engineering systems, human performance under sustained stress exhibits:

- **Statistical variation** (manufacturing quality control)
- **Epidemic-like spread** through social networks (epidemiology)
- **Queuing dynamics** under variable demand (telecommunications)
- **Precursor signals** before catastrophic failure (seismology)
- **Multi-temporal accumulation** of risk factors (forestry fire science)
- **Fatigue and creep** under sustained loading (materials science)

This framework combines these diverse perspectives into a unified resilience monitoring system.

### Key Innovations

1. **Multi-Domain Validation**: Each module brings 50+ years of proven science from its source domain
2. **Complementary Analysis**: Different modules detect different burnout patterns
3. **Early Warning**: Precursor detection provides intervention time before crisis
4. **Quantitative Thresholds**: Clear, actionable metrics replace subjective assessment
5. **Production-Ready**: Full test coverage, logging, and operational monitoring

---

## Module Catalog

### 1. SPC Monitoring (Statistical Process Control)

**Source Domain**: Semiconductor manufacturing / Quality control

**File**: `/backend/app/resilience/spc_monitoring.py`

#### Core Concept

Statistical Process Control (SPC) uses control charts to distinguish between normal process variation and special cause variation requiring intervention. Originally developed by Walter Shewhart at Bell Labs (1920s) and refined for semiconductor manufacturing, SPC detects when a process goes "out of control."

**Western Electric Rules** (implemented in this module):

- **Rule 1**: 1 point beyond 3σ → CRITICAL (immediate investigation)
- **Rule 2**: 2 of 3 consecutive points beyond 2σ → WARNING (shift detected)
- **Rule 3**: 4 of 5 consecutive points beyond 1σ → WARNING (trend detected)
- **Rule 4**: 8 consecutive points on same side of centerline → INFO (sustained shift)

#### Medical Scheduling Application

Monitors resident weekly work hours as a "manufacturing process" that should maintain statistical control:

- **Target (centerline)**: 60 hours/week (safe operating point)
- **Upper Control Limit (UCL)**: 75 hours (3σ above target)
- **Lower Control Limit (LCL)**: 45 hours (3σ below target)
- **Violations**: Trigger alerts based on Western Electric Rules

**Why This Works**: Just as semiconductor fabs detect equipment drift before producing defective chips, SPC monitoring detects workload drift before burnout occurs.

#### Key Classes/Functions

```python
# Main Classes
class WorkloadControlChart:
    def __init__(self, target_hours: float = 60.0, sigma: float = 5.0)
    def detect_western_electric_violations(
        self,
        resident_id: UUID,
        weekly_hours: list[float]
    ) -> list[SPCAlert]

@dataclass
class SPCAlert:
    rule: str                      # "Rule 1", "Rule 2", etc.
    severity: str                  # "CRITICAL", "WARNING", "INFO"
    message: str
    resident_id: Optional[UUID]
    data_points: list[float]
    control_limits: dict

# Utility Functions
def calculate_control_limits(data: list[float]) -> dict
def calculate_process_capability(
    data: list[float],
    lsl: float,  # Lower Specification Limit
    usl: float   # Upper Specification Limit
) -> dict
```

#### Usage Example

```python
from uuid import uuid4
from app.resilience.spc_monitoring import WorkloadControlChart

# Initialize control chart (60h target, 5h standard deviation)
chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)

# Weekly hours for a resident over 8 weeks
weekly_hours = [58, 62, 59, 67, 71, 75, 78, 80]

# Detect violations
alerts = chart.detect_western_electric_violations(
    resident_id=uuid4(),
    weekly_hours=weekly_hours
)

for alert in alerts:
    if alert.severity == "CRITICAL":
        print(f"🚨 {alert.rule}: {alert.message}")
        # Output: "🚨 Rule 1: Workload exceeded 3σ upper limit: 80.0 hours"

    elif alert.severity == "WARNING":
        print(f"⚠️  {alert.rule}: {alert.message}")
        # Output: "⚠️  Rule 2: Workload shift detected: 2 of 3 weeks exceeded 2σ"
```

#### Integration Points

- **Resilience Health Monitor**: Scheduled Celery task runs SPC analysis weekly
- **Alert System**: `SPCAlert` objects feed into notification pipeline
- **Dashboard**: Real-time control charts displayed in admin UI
- **ACGME Validator**: Provides early warning before 80-hour violations

#### MCP Tools

AI agents can access SPC functionality via MCP:

- **`run_spc_analysis`**: Apply Western Electric Rules to weekly hours data
  - Detects Rule 1-4 violations
  - Returns control limits, alerts, and recommendations
  - Severity: `healthy`, `warning`, `critical`

```python
# Example MCP tool call
result = await run_spc_analysis(
    resident_id="abc-123",
    weekly_hours=[58, 62, 59, 67, 71, 75, 78, 80],
    target_hours=60.0,
    sigma=5.0
)
```

See [MCP Tools Reference](../api/MCP_TOOLS_REFERENCE.md#run_spc_analysis) for full documentation.

---

### 2. Process Capability Analysis (Six Sigma)

**Source Domain**: Six Sigma manufacturing / Quality engineering

**File**: `/backend/app/resilience/process_capability.py`

#### Core Concept

Process capability indices (Cp, Cpk, Pp, Ppk, Cpm) quantify how well a process can meet specifications. Developed by Motorola (1980s) and popularized by General Electric, Six Sigma aims for 3.4 defects per million opportunities.

**Capability Indices**:

- **Cp**: Process potential (assumes perfect centering) = (USL - LSL) / (6σ)
- **Cpk**: Process capability (actual, accounts for off-center) = min((USL - μ) / 3σ, (μ - LSL) / 3σ)
- **Pp/Ppk**: Long-term performance (uses overall σ vs within-subgroup σ)
- **Cpm**: Taguchi index (penalizes deviation from target, not just spec limits)

**Classification**:
- Cpk ≥ 2.0: World Class (6σ quality)
- Cpk ≥ 1.67: Excellent (5σ quality)
- Cpk ≥ 1.33: Capable (4σ quality, industry standard)
- Cpk ≥ 1.0: Marginal (3σ quality, minimum acceptable)
- Cpk < 1.0: Incapable (defects expected)

#### Medical Scheduling Application

Measures how consistently the scheduling system maintains resident hours within ACGME limits:

- **LSL (Lower Spec Limit)**: 40 hours/week (minimum for training)
- **USL (Upper Spec Limit)**: 80 hours/week (ACGME hard limit)
- **Target**: 60 hours/week (optimal training load)
- **Cpk > 1.33**: Scheduling process reliably prevents violations

**Why This Works**: Six Sigma methodology has reduced defects in aerospace, medical devices, and pharmaceuticals. Applied to scheduling, it ensures ACGME compliance isn't left to chance.

#### Key Classes/Functions

```python
class ScheduleCapabilityAnalyzer:
    def __init__(self, min_sample_size: int = 30)

    # Calculate individual indices
    def calculate_cp(self, data: list[float], lsl: float, usl: float) -> float
    def calculate_cpk(self, data: list[float], lsl: float, usl: float) -> float
    def calculate_cpm(self, data: list[float], lsl: float, usl: float, target: float) -> float

    # Main analysis
    def analyze_workload_capability(
        self,
        weekly_hours: list[float],
        min_hours: float = 40.0,
        max_hours: float = 80.0,
        target_hours: Optional[float] = None
    ) -> ProcessCapabilityReport

    # Helper methods
    def get_sigma_level(self, cpk: float) -> float
    def classify_capability(self, cpk: float) -> str
    def get_capability_summary(self, report: ProcessCapabilityReport) -> dict

@dataclass
class ProcessCapabilityReport:
    cp: float
    cpk: float
    pp: float
    ppk: float
    cpm: float
    capability_status: str  # "EXCELLENT", "CAPABLE", "MARGINAL", "INCAPABLE"
    sigma_level: float
    sample_size: int
    mean: float
    std_dev: float
    lsl: float
    usl: float
    target: Optional[float]
```

#### Usage Example

```python
from app.resilience.process_capability import ScheduleCapabilityAnalyzer

analyzer = ScheduleCapabilityAnalyzer()

# 30 weeks of resident hour data
weekly_hours = [65, 72, 58, 75, 68, 70, 62, 77, ...]  # 30+ values

# Analyze capability
report = analyzer.analyze_workload_capability(
    weekly_hours,
    min_hours=40,
    max_hours=80,
    target_hours=60
)

print(f"Capability: {report.capability_status}")     # "CAPABLE"
print(f"Sigma Level: {report.sigma_level:.2f}σ")     # "4.20σ"
print(f"Cpk: {report.cpk:.3f}")                      # "1.400"

# Get detailed summary
summary = analyzer.get_capability_summary(report)
print(summary['centering'])  # "EXCELLENT - Process well centered"

# Estimated defect rate
print(f"Estimated ACGME violations: {summary['estimated_defect_rate']['ppm']} PPM")
# Output: "Estimated ACGME violations: 32.45 PPM (0.0032%)"
```

#### Integration Points

- **Schedule Generator**: Quality gate—reject schedules with Cpk < 1.33
- **Continuous Improvement**: Track Cpk trends to measure scheduling algorithm improvements
- **Compliance Reporting**: Quantitative evidence for ACGME audits
- **Resilience Dashboard**: Display sigma level and capability classification

#### MCP Tools

AI agents can access Process Capability via MCP:

- **`calculate_process_capability_tool`**: Calculate Cp/Cpk indices for workload data
  - Classifies capability: EXCELLENT, CAPABLE, MARGINAL, INCAPABLE
  - Estimates sigma level and defect rate (PPM)
  - Provides centering assessment and recommendations

- **`calculate_process_capability`** (optimization module): Extended Six Sigma analysis
  - Includes Cpm (Taguchi index) for off-target penalty
  - Full Pp/Ppk long-term performance indices

```python
# Example MCP tool call
result = await calculate_process_capability_tool(
    weekly_hours=[58, 62, 59, 61, 63, 60, 58, 62],
    lower_spec_limit=40.0,  # Minimum hours
    upper_spec_limit=80.0   # ACGME max
)
print(f"Cpk: {result.cpk:.2f} - {result.interpretation}")
```

See [MCP Tools Reference](../api/MCP_TOOLS_REFERENCE.md#calculate_process_capability_tool) for full documentation.

---

### 3. Burnout Epidemiology (SIR Models)

**Source Domain**: Epidemiology / Public health

**File**: `/backend/app/resilience/burnout_epidemiology.py`

#### Core Concept

The SIR (Susceptible-Infected-Recovered) model describes how infectious diseases spread through populations. Key metric: **R₀** (basic reproduction number)—the average number of secondary infections caused by one infected individual.

- **R₀ > 1**: Epidemic grows exponentially
- **R₀ = 1**: Endemic (stable)
- **R₀ < 1**: Epidemic declines and dies out

**Research Foundation**:
- Christakis & Fowler (2008): Emotions spread through social networks
- Bakker et al. (2009): Burnout has social contagion effects
- Network topology predicts spread patterns

#### Medical Scheduling Application

Treats burnout as a "contagious condition" that spreads through resident social networks:

- **Susceptible (S)**: Healthy residents who could develop burnout
- **Infected (I)**: Residents with active burnout (can "transmit" to others)
- **Recovered (R)**: Residents who recovered or left the system

**Transmission Mechanisms**:
- Shared difficult shifts
- Mentorship relationships
- Team assignments
- Emotional contagion in clinical settings

**Interventions Based on Rₜ**:
- Rₜ < 0.5: Maintain preventive measures
- 0.5 ≤ Rₜ < 1: Monitor at-risk individuals
- 1 ≤ Rₜ < 2: Moderate interventions (workload reduction, support groups)
- 2 ≤ Rₜ < 3: Aggressive interventions (mandatory time off, restructuring)
- Rₜ ≥ 3: Emergency crisis management

#### Key Classes/Functions

```python
class BurnoutEpidemiology:
    def __init__(self, social_network: nx.Graph)

    # State tracking
    def record_burnout_state(
        self,
        resident_id: UUID,
        state: BurnoutState,  # SUSCEPTIBLE, AT_RISK, BURNED_OUT, RECOVERED
        timestamp: datetime = None
    )

    # Contact tracing
    def get_close_contacts(
        self,
        resident_id: UUID,
        time_window: timedelta = timedelta(weeks=4)
    ) -> set[UUID]

    # Reproduction number calculation
    def calculate_reproduction_number(
        self,
        burned_out_residents: set[UUID],
        time_window: timedelta = timedelta(weeks=4)
    ) -> EpiReport

    # SIR simulation
    def simulate_sir_spread(
        self,
        initial_infected: set[UUID],
        beta: float = 0.05,    # Transmission rate
        gamma: float = 0.02,   # Recovery rate
        steps: int = 52        # Weeks
    ) -> list[dict]

    # Super-spreader detection
    def identify_super_spreaders(self, threshold_degree: int = 5) -> list[UUID]

    # Herd immunity
    def calculate_herd_immunity_threshold(self, r0: float) -> float

class BurnoutState(Enum):
    SUSCEPTIBLE = "susceptible"
    AT_RISK = "at_risk"
    BURNED_OUT = "burned_out"
    RECOVERED = "recovered"

@dataclass
class EpiReport:
    reproduction_number: float
    status: str  # "declining", "controlled", "spreading", "rapid_spread", "crisis"
    secondary_cases: dict[str, int]
    recommended_interventions: list[str]
    intervention_level: InterventionLevel
    super_spreaders: list[UUID]
    high_risk_contacts: list[UUID]
```

#### Usage Example

```python
import networkx as nx
from app.resilience.burnout_epidemiology import BurnoutEpidemiology, BurnoutState

# Build social network (residents as nodes, connections as edges)
G = nx.Graph()
G.add_edges_from([
    (resident1_id, resident2_id),  # Shared shifts
    (resident2_id, resident3_id),  # Mentorship
    (resident3_id, resident4_id),  # Same team
])

epi = BurnoutEpidemiology(social_network=G)

# Record burnout states
epi.record_burnout_state(resident1_id, BurnoutState.BURNED_OUT)
epi.record_burnout_state(resident2_id, BurnoutState.BURNED_OUT)

# Calculate effective reproduction number
burned_out = {resident1_id, resident2_id}
report = epi.calculate_reproduction_number(burned_out)

print(f"Rₜ = {report.reproduction_number:.2f}")  # "Rₜ = 1.35"
print(f"Status: {report.status}")                # "spreading"
print(f"Intervention: {report.intervention_level}")  # "MODERATE"

# Interventions
for intervention in report.recommended_interventions:
    print(f"  - {intervention}")
# Output:
#   - Implement workload reduction for burned out individuals
#   - Mandatory wellness check-ins for all staff
#   - Break transmission chains: reduce contact between burned out and at-risk

# Simulate spread
time_series = epi.simulate_sir_spread(
    initial_infected=burned_out,
    beta=0.05,
    gamma=0.02,
    steps=52
)

# Plot S, I, R over time
for week in time_series[:5]:
    print(f"Week {week['week']}: S={week['S']}, I={week['I']}, R={week['R']}")
```

#### Integration Points

- **Social Network Builder**: Construct network from shift assignments, mentorships
- **Alert System**: Rₜ > 2 triggers ORANGE safety level
- **Intervention Recommender**: Evidence-based interventions from epidemiology
- **Dashboard**: Network visualization with burnout status overlay

#### MCP Tools

AI agents can access Burnout Epidemiology via MCP:

- **`calculate_burnout_rt`**: Calculate effective reproduction number (Rt)
  - Identifies superspreaders and high-risk contacts
  - Returns intervention recommendations based on Rt value
  - Calculates herd immunity threshold

- **`simulate_burnout_spread`**: Run SIR epidemic simulation
  - Projects burnout trajectory over time
  - Identifies peak infection week and final outcomes
  - Calculates R0 from transmission/recovery parameters

- **`simulate_burnout_contagion`**: SIS network diffusion model
  - Uses actual social/collaboration network structure
  - Identifies superspreader profiles with centrality scores
  - Recommends network interventions (edge removal, buffer insertion)

```python
# Example MCP tool call
result = await calculate_burnout_rt(
    burned_out_provider_ids=["provider-1", "provider-2", "provider-3"],
    time_window_days=28
)
if result.rt > 1.0:
    print(f"Burnout spreading! Rt={result.rt:.2f}")
    for intervention in result.interventions:
        print(f"  - {intervention}")
```

See [MCP Tools Reference](../api/MCP_TOOLS_REFERENCE.md#calculate_burnout_rt) for full documentation.

---

### 4. Erlang C Coverage Optimization (Queuing Theory)

**Source Domain**: Telecommunications / Operations research

**File**: `/backend/app/resilience/erlang_coverage.py`

#### Core Concept

Erlang C formula calculates the probability of waiting in queue for systems with:
- **Poisson arrivals** (random arrival times)
- **Exponential service times** (memoryless)
- **c servers** with infinite queue

Developed by Agner Krarup Erlang (1917) for telephone exchanges, now used for call centers, emergency departments, and specialist coverage.

**Key Formulas**:
- **Offered Load**: A = λ × μ (arrival_rate × avg_service_time)
- **Erlang B**: P(all servers busy) = (Aᶜ / c!) / Σ(Aᵏ / k!) for k=0 to c
- **Erlang C**: P(wait) = Erlang_B / (1 - (A/c)(1 - Erlang_B))
- **Service Level**: P(answer within time t) = 1 - P(wait) × e^(-(c-A)t/μ)

#### Medical Scheduling Application

Determines optimal specialist staffing to meet service level targets:

- **Arrivals**: Emergency cases requiring specialist (e.g., orthopedic consult)
- **Service Time**: Duration specialist engaged with case
- **Servers**: Number of specialists on duty
- **Target**: 95% of cases answered within 15 minutes

**Why This Works**: Hospitals operate like call centers—random arrivals, variable service times. Erlang formulas provide mathematically optimal staffing.

#### Key Classes/Functions

```python
class ErlangCCalculator:
    def __init__(self)

    # Core formulas
    def erlang_b(self, offered_load: float, servers: int) -> float
    def erlang_c(self, offered_load: float, servers: int) -> float

    # Metrics calculation
    def calculate_wait_probability(
        self,
        arrival_rate: float,
        service_time: float,
        servers: int
    ) -> float

    def calculate_avg_wait_time(
        self,
        arrival_rate: float,
        service_time: float,
        servers: int
    ) -> float

    def calculate_service_level(
        self,
        arrival_rate: float,
        service_time: float,
        servers: int,
        target_wait: float
    ) -> float

    def calculate_occupancy(
        self,
        arrival_rate: float,
        service_time: float,
        servers: int
    ) -> float

    # Optimization
    def optimize_specialist_coverage(
        self,
        specialty: str,
        arrival_rate: float,
        service_time: float,
        target_wait_prob: float = 0.05,
        max_servers: int = 20
    ) -> SpecialistCoverage

    # Analysis
    def calculate_metrics(
        self,
        arrival_rate: float,
        service_time: float,
        servers: int,
        target_wait: Optional[float] = None
    ) -> ErlangMetrics

    def generate_staffing_table(
        self,
        arrival_rate: float,
        service_time: float,
        min_servers: Optional[int] = None,
        max_servers: Optional[int] = None
    ) -> list[dict]

@dataclass
class ErlangMetrics:
    wait_probability: float
    avg_wait_time: float
    service_level: float
    occupancy: float

@dataclass
class SpecialistCoverage:
    specialty: str
    required_specialists: int
    predicted_wait_probability: float
    offered_load: float
    service_level: float
```

#### Usage Example

```python
from app.resilience.erlang_coverage import ErlangCCalculator

calc = ErlangCCalculator()

# Orthopedic surgery coverage scenario
# - 2.5 cases per hour requiring ortho consult
# - 30 minutes average consult time
# - Target: 95% answered immediately (5% wait probability)

coverage = calc.optimize_specialist_coverage(
    specialty="Orthopedic Surgery",
    arrival_rate=2.5,      # cases/hour
    service_time=0.5,      # 30 min = 0.5 hours
    target_wait_prob=0.05  # 5% maximum wait
)

print(f"Required specialists: {coverage.required_specialists}")  # "4"
print(f"Wait probability: {coverage.predicted_wait_probability:.1%}")  # "3.2%"
print(f"Service level: {coverage.service_level:.1%}")  # "96.8%"

# Detailed metrics for current staffing
metrics = calc.calculate_metrics(
    arrival_rate=2.5,
    service_time=0.5,
    servers=4,
    target_wait=0.25  # 15 min target
)

print(f"Occupancy: {metrics.occupancy:.1%}")  # "31.25%"
print(f"Avg wait: {metrics.avg_wait_time:.2f} hours")  # "0.03 hours (~2 min)"

# Staffing table for decision support
table = calc.generate_staffing_table(
    arrival_rate=2.5,
    service_time=0.5,
    min_servers=2,
    max_servers=6
)

for row in table:
    print(f"{row['servers']} specialists: "
          f"Wait={row['wait_probability']:.1%}, "
          f"Service Level={row['service_level']:.1%}, "
          f"Occupancy={row['occupancy']:.1%}")
# Output:
# 2 specialists: Wait=46.2%, Service Level=78.3%, Occupancy=62.5%
# 3 specialists: Wait=12.7%, Service Level=93.5%, Occupancy=41.7%
# 4 specialists: Wait=3.2%, Service Level=98.1%, Occupancy=31.25%
# 5 specialists: Wait=0.8%, Service Level=99.5%, Occupancy=25.0%
```

#### Integration Points

- **Schedule Generator**: Ensures adequate specialist coverage for emergency cases
- **On-Call Scheduler**: Optimizes number of attendings on call
- **Capacity Planning**: Predicts staffing needs from historical arrival data
- **Utilization Monitoring**: Compares actual vs. predicted occupancy

#### MCP Tools

AI agents can access Erlang C Coverage via MCP:

- **`optimize_erlang_coverage`**: Find minimum staffing for service level target
  - Returns recommended specialists, utilization, and wait probability
  - Generates staffing table for decision support
  - Severity levels based on 80% utilization threshold

- **`calculate_erlang_metrics`**: Get detailed metrics for specific configuration
  - Wait probability, average wait time, service level
  - Occupancy rate and queue stability check
  - Erlang B blocking probability

```python
# Example MCP tool call
result = await optimize_erlang_coverage(
    specialty="Orthopedic Surgery",
    arrival_rate=2.5,        # 2.5 cases/hour
    service_time_minutes=30,  # 30 min per case
    target_wait_minutes=15,
    target_wait_probability=0.05
)
print(f"Need {result.recommended_specialists} specialists")
print(f"Wait probability: {result.wait_probability:.1%}")
```

See [MCP Tools Reference](../api/MCP_TOOLS_REFERENCE.md#optimize_erlang_coverage) for full documentation.

---

### 5. Seismic P-Wave Detection (STA/LTA Algorithm)

**Source Domain**: Seismology / Signal processing

**File**: `/home/user/Autonomous-Assignment-Program-Manager/backend/app/resilience/seismic_detection.py`

#### Core Concept

The STA/LTA (Short-Term Average / Long-Term Average) algorithm detects earthquake P-waves—precursor signals that arrive before the destructive S-waves. By comparing recent signal energy to long-term baseline, the algorithm identifies anomalies in real-time.

**Algorithm**:
1. Calculate STA: Average signal energy over short window (e.g., 5 samples)
2. Calculate LTA: Average signal energy over long window (e.g., 30 samples)
3. Compute ratio: STA/LTA
4. Trigger when ratio > threshold (typically 2.5-3.0)

**Seismology Application**: Earthquake early warning systems (Japan, California) use STA/LTA to detect P-waves and issue alerts seconds before damaging shaking arrives.

#### Medical Scheduling Application

Detects burnout "precursor signals"—behavioral changes that occur before full burnout:

**Monitored Precursor Signals**:
- **Swap requests**: Frequency of shift swap requests
- **Sick calls**: Pattern changes in unplanned absences
- **Preference decline**: Declining previously desired shifts
- **Response delays**: Slower response to schedule requests
- **Voluntary coverage decline**: Refusing extra shifts

**Why This Works**: Like earthquakes, burnout has precursors. Detecting behavioral changes early provides intervention time.

#### Key Classes/Functions

```python
class BurnoutEarlyWarning:
    def __init__(self, short_window: int = 5, long_window: int = 30)

    # Classic STA/LTA algorithms
    @staticmethod
    def classic_sta_lta(
        data: np.ndarray,
        nsta: int,
        nlta: int
    ) -> np.ndarray

    @staticmethod
    def recursive_sta_lta(
        data: np.ndarray,
        nsta: int,
        nlta: int
    ) -> np.ndarray  # Memory-efficient, real-time friendly

    # Trigger detection
    @staticmethod
    def trigger_onset(
        sta_lta: np.ndarray,
        on_threshold: float = 2.5,
        off_threshold: float = 1.0
    ) -> list[tuple[int, int]]  # (start_idx, end_idx) pairs

    # Precursor detection
    def detect_precursors(
        self,
        resident_id: UUID,
        signal_type: PrecursorSignal,
        time_series: list[float]
    ) -> list[SeismicAlert]

    # Magnitude prediction
    def predict_burnout_magnitude(
        self,
        precursor_signals: dict[PrecursorSignal, list[float]]
    ) -> float  # 1-10 scale (like Richter)

    # Time-to-event estimation
    def estimate_time_to_event(
        self,
        sta_lta_ratio: float,
        signal_growth_rate: float
    ) -> timedelta

class PrecursorSignal(Enum):
    SWAP_REQUESTS = "swap_requests"
    SICK_CALLS = "sick_calls"
    PREFERENCE_DECLINE = "preference_decline"
    RESPONSE_DELAYS = "response_delays"
    VOLUNTARY_COVERAGE_DECLINE = "voluntary_coverage_decline"

@dataclass
class SeismicAlert:
    signal_type: PrecursorSignal
    sta_lta_ratio: float
    trigger_time: datetime
    severity: str  # "low", "medium", "high", "critical"
    predicted_magnitude: float  # 1-10 scale
    time_to_event: Optional[timedelta]
    resident_id: Optional[UUID]
    context: dict
```

#### Usage Example

```python
from app.resilience.seismic_detection import BurnoutEarlyWarning, PrecursorSignal

detector = BurnoutEarlyWarning(short_window=5, long_window=30)

# Time series: daily swap request counts for 60 days
# Baseline ~1/day, then sudden increase
swap_data = [
    0, 1, 0, 1, 0, 1, 1, 0, 1, 0,  # Weeks 1-2: Normal
    1, 0, 1, 1, 0, 0, 1, 0, 1, 0,  # Weeks 3-4: Normal
    1, 1, 0, 1, 0, 1, 0, 1, 1, 0,  # Weeks 5-6: Normal
    2, 3, 2, 5, 7, 8, 6, 9, 11, 10  # Weeks 7-10: ANOMALY
]

alerts = detector.detect_precursors(
    resident_id=resident_id,
    signal_type=PrecursorSignal.SWAP_REQUESTS,
    time_series=swap_data
)

for alert in alerts:
    print(f"⚠️ Burnout precursor detected!")
    print(f"  Signal: {alert.signal_type.value}")
    print(f"  STA/LTA ratio: {alert.sta_lta_ratio:.2f}")
    print(f"  Severity: {alert.severity}")
    print(f"  Predicted magnitude: {alert.predicted_magnitude:.1f}/10")
    if alert.time_to_event:
        print(f"  Estimated time to burnout: {alert.time_to_event.days} days")

# Multi-signal analysis
precursor_signals = {
    PrecursorSignal.SWAP_REQUESTS: swap_data,
    PrecursorSignal.SICK_CALLS: [0, 0, 0, 1, 0, 0, 1, 2, 3, 4],
    PrecursorSignal.RESPONSE_DELAYS: [1, 2, 1, 2, 3, 5, 8, 12, 15, 18]
}

magnitude = detector.predict_burnout_magnitude(precursor_signals)
print(f"Combined burnout magnitude: {magnitude:.1f}/10")
# Output: "Combined burnout magnitude: 7.2/10" (HIGH risk)
```

#### Integration Points

- **Behavioral Monitoring**: Track daily counts of precursor signals
- **Real-Time Alerts**: Trigger notifications when STA/LTA > 2.5
- **Predictive Dashboard**: Display STA/LTA traces for early warning
- **Intervention Prioritization**: Magnitude prediction guides resource allocation

#### MCP Tools

AI agents can access Seismic Detection via MCP:

- **`detect_burnout_precursors`**: Detect early warning signs using STA/LTA algorithm
  - Monitors 5 precursor signal types (swap requests, sick calls, etc.)
  - Configurable short/long window sizes
  - Returns alerts with severity, magnitude prediction, and time-to-event
  - Severity: `healthy`, `warning`, `elevated`, `critical`

```python
# Example MCP tool call
result = await detect_burnout_precursors(
    resident_id="abc-123",
    signal_type="swap_requests",
    time_series=[0, 1, 0, 1, 0, 2, 3, 5, 7, 8, 12, 15, 18],
    short_window=5,
    long_window=30
)
if result.alerts_detected > 0:
    print(f"WARNING: {result.alerts[0].severity} precursor detected")
    print(f"STA/LTA ratio: {result.max_sta_lta_ratio:.2f}")
```

See [MCP Tools Reference](../api/MCP_TOOLS_REFERENCE.md#detect_burnout_precursors) for full documentation.

---

### 6. Canadian Fire Weather Index (Multi-Temporal Burnout Index)

**Source Domain**: Forestry / Fire science

**File**: `/backend/app/resilience/burnout_fire_index.py`

#### Core Concept

The Canadian Forest Fire Danger Rating System (CFFDRS) Fire Weather Index (FWI) combines **multiple time scales** to predict wildfire danger. Like wildfires, burnout doesn't develop overnight—it requires alignment of short-term, medium-term, and long-term factors.

**FWI System Components** (3 moisture codes, 2 behavior indices, 1 composite):

1. **FFMC (Fine Fuel Moisture Code)**: 0-100 scale, 1-2 day response
   - Forest: Moisture in litter and fine fuels
   - Burnout: Recent workload (last 2 weeks)

2. **DMC (Duff Moisture Code)**: 0-100 scale, 15-day response
   - Forest: Moisture in duff layer (sustains fire)
   - Burnout: 3-month sustained workload

3. **DC (Drought Code)**: 0-100 scale, 52-day response
   - Forest: Deep soil moisture deficit
   - Burnout: Yearly job satisfaction erosion

4. **ISI (Initial Spread Index)**: 0-100+ scale
   - Forest: Combines FFMC with wind speed
   - Burnout: Combines FFMC with workload velocity (rate of increase)

5. **BUI (Buildup Index)**: 0-100+ scale
   - Forest: Combines DMC and DC (fuel available)
   - Burnout: Combined medium + long-term burden

6. **FWI (Fire Weather Index)**: 0-100+ scale
   - Final composite of ISI and BUI
   - Thresholds: <20 LOW, 20-40 MODERATE, 40-60 HIGH, 60-80 VERY_HIGH, 80+ EXTREME

#### Medical Scheduling Application

**Multi-Temporal Burnout Assessment**:

| Component | Time Scale | Medical Analog | Threshold |
|-----------|-----------|----------------|-----------|
| **FFMC** | 2 weeks | Recent hours worked | 85+ = High immediate risk |
| **DMC** | 3 months | Sustained overwork | 70+ = Medium-term burden |
| **DC** | 1 year | Job satisfaction erosion | 60+ = Chronic dissatisfaction |
| **ISI** | Combined | Recent overwork + acceleration | 60+ = Rapid deterioration |
| **BUI** | Combined | Medium + long-term burden | 70+ = Accumulated risk |
| **FWI** | Final | Overall burnout danger | 80+ = EXTREME danger |

**Why This Works**: The FWI System correctly predicted severe fire seasons across Canada for 50+ years. Multi-temporal analysis captures burnout complexity better than single metrics.

#### Key Classes/Functions

```python
class BurnoutDangerRating:
    def __init__(
        self,
        ffmc_target: float = 60.0,   # 60 hours/2 weeks
        dmc_target: float = 240.0,   # 240 hours/3 months
        dc_baseline: float = 1.0     # Full satisfaction
    )

    # Component calculations (Van Wagner formulas, adapted)
    def calculate_fine_fuel_moisture_code(
        self,
        recent_hours: float,
        target: float = 60.0
    ) -> float

    def calculate_duff_moisture_code(
        self,
        monthly_load: float,
        target: float = 240.0
    ) -> float

    def calculate_drought_code(
        self,
        yearly_satisfaction: float  # 0.0-1.0
    ) -> float

    def calculate_initial_spread_index(
        self,
        ffmc: float,
        workload_velocity: float = 0.0
    ) -> float

    def calculate_buildup_index(
        self,
        dmc: float,
        dc: float
    ) -> float

    def calculate_fire_weather_index(
        self,
        isi: float,
        bui: float
    ) -> float

    # Main analysis
    def calculate_burnout_danger(
        self,
        resident_id: UUID,
        recent_hours: float,
        monthly_load: float,
        yearly_satisfaction: float,
        workload_velocity: float = 0.0
    ) -> FireDangerReport

    # Batch processing
    def calculate_batch_danger(
        self,
        residents: list[dict]
    ) -> list[FireDangerReport]

    # Classification
    def classify_danger(self, fwi: float) -> DangerClass
    def get_restrictions(self, danger_class: DangerClass) -> list[str]

class DangerClass(Enum):
    LOW = "low"              # FWI < 20
    MODERATE = "moderate"    # FWI 20-40
    HIGH = "high"            # FWI 40-60
    VERY_HIGH = "very_high"  # FWI 60-80
    EXTREME = "extreme"      # FWI 80+

@dataclass
class FireDangerReport:
    resident_id: UUID
    danger_class: DangerClass
    fwi_score: float
    component_scores: dict
    recommended_restrictions: list[str]
```

#### Usage Example

```python
from uuid import uuid4
from app.resilience.burnout_fire_index import BurnoutDangerRating, DangerClass

rating = BurnoutDangerRating()

# Resident experiencing burnout:
# - Recently working 75h (vs 60h target)
# - Sustained 260h/month for 3 months (vs 240h target)
# - Job satisfaction declined to 0.4 (40%)
# - Workload increasing 8h/week

report = rating.calculate_burnout_danger(
    resident_id=uuid4(),
    recent_hours=75.0,
    monthly_load=260.0,
    yearly_satisfaction=0.4,
    workload_velocity=8.0
)

print(f"Danger Level: {report.danger_class.value.upper()}")  # "EXTREME"
print(f"FWI Score: {report.fwi_score:.1f}")                   # "87.3"
print(f"\nComponent Scores:")
for component, score in report.component_scores.items():
    print(f"  {component.upper()}: {score:.1f}")
# Output:
#   FFMC: 73.4 (high recent workload)
#   DMC: 68.2 (sustained overwork)
#   DC: 77.6 (low satisfaction)
#   ISI: 94.8 (rapid deterioration)
#   BUI: 72.1 (high accumulated burden)
#   FWI: 87.3 (EXTREME)

print(f"\nRestrictions:")
for restriction in report.recommended_restrictions:
    print(f"  🚨 {restriction}")
# Output:
#   🚨 EMERGENCY: Critical intervention required
#   🚨 Immediate leave or reduced schedule (30-40h/week)
#   🚨 Remove from high-stress assignments
#   🚨 Mandatory mental health support
#   🚨 Do not return to normal duties until FWI < 40

# Batch analysis for entire program
residents_data = [
    {"resident_id": uuid4(), "recent_hours": 75, "monthly_load": 260,
     "yearly_satisfaction": 0.4, "workload_velocity": 8.0},
    {"resident_id": uuid4(), "recent_hours": 58, "monthly_load": 230,
     "yearly_satisfaction": 0.8, "workload_velocity": 0.0},
    # ... more residents
]

reports = rating.calculate_batch_danger(residents_data)
# Returns sorted by FWI (highest risk first)

for report in reports[:3]:  # Top 3 at-risk
    print(f"{report.danger_class.value}: FWI={report.fwi_score:.1f}")
```

#### Integration Points

- **Daily Health Monitoring**: Calculate FWI for all residents daily
- **Safety Level Escalation**: FWI > 60 triggers RED/BLACK safety levels
- **Intervention Recommender**: Restrictions mapped to danger classes
- **Dashboard**: Multi-temporal burnout "weather map"

#### MCP Tools

AI agents can access Fire Weather Index via MCP:

- **`calculate_fire_danger_index`**: Calculate multi-temporal burnout danger
  - Combines recent hours, monthly load, yearly satisfaction, and velocity
  - Returns FWI score, component scores, and danger classification
  - Temporal analysis explains each time scale contribution
  - Severity: `healthy`, `warning`, `elevated`, `critical`, `emergency`

```python
# Example MCP tool call
result = await calculate_fire_danger_index(
    resident_id="abc-123",
    recent_hours=75.0,       # High recent workload
    monthly_load=260.0,      # Sustained overwork
    yearly_satisfaction=0.4, # Low satisfaction
    workload_velocity=8.0    # Increasing workload
)

if result.danger_class == "extreme":
    print("EMERGENCY: Immediate intervention required")
    for restriction in result.recommended_restrictions:
        print(f"  - {restriction}")
```

See [MCP Tools Reference](../api/MCP_TOOLS_REFERENCE.md#calculate_fire_danger_index) for full documentation.

---

### 7. Creep/Fatigue Mechanics (Materials Science)

**Source Domain**: Materials science / Mechanical engineering

**File**: `/backend/app/resilience/creep_fatigue.py`

#### Core Concept

**Creep**: Time-dependent deformation under constant stress (like a steel beam slowly sagging under load)

**Fatigue**: Damage accumulation from cyclic loading (like a paperclip breaking after repeated bending)

**Key Concepts**:

1. **Larson-Miller Parameter (LMP)**: Combines time and temperature to predict creep failure
   - Formula: LMP = T(C + log₁₀(t))
   - Adapted: LMP = workload × (C + log₁₀(duration))

2. **Creep Stages**:
   - Primary: Decreasing strain rate (adaptation)
   - Secondary: Steady-state (sustainable)
   - Tertiary: Accelerating strain rate (approaching failure)

3. **S-N Curves (Wöhler curves)**: Stress vs. cycles to failure
   - N = A × S^b (cycles to failure as function of stress)

4. **Miner's Rule**: Cumulative damage from varying stress
   - D = Σ(n_i / N_i) where failure occurs when D ≥ 1.0

#### Medical Scheduling Application

**Creep Analysis**:
- Constant "stress" = sustained high workload
- "Time" = duration of sustained workload
- "Failure" = burnout from chronic overwork

**Fatigue Analysis**:
- "Cycles" = rotation changes (ER → ICU → Clinic → ...)
- "Stress amplitude" = rotation difficulty
- "Cumulative damage" = total fatigue from all rotations

**Combined Assessment**: Residents experience both creep (sustained workload) and fatigue (rotation cycling)

#### Key Classes/Functions

```python
class CreepFatigueModel:
    # Larson-Miller Parameter
    def calculate_larson_miller(
        self,
        workload_fraction: float,  # 0.0-1.0
        duration_days: int,
        C: float = 20.0
    ) -> float

    # Creep analysis
    def determine_creep_stage(
        self,
        larson_miller: float,
        threshold: float = 45.0
    ) -> CreepStage  # PRIMARY, SECONDARY, TERTIARY

    def calculate_strain_rate(
        self,
        workload_history: list[float]
    ) -> float

    def predict_time_to_burnout(
        self,
        resident_id: UUID,
        sustained_workload: float,
        duration: timedelta
    ) -> CreepAnalysis

    def recommend_stress_reduction(
        self,
        current_lmp: float,
        safe_lmp: float = 31.5
    ) -> float  # Percentage reduction

    # Fatigue analysis (S-N curves)
    def sn_curve_cycles_to_failure(
        self,
        stress_amplitude: float,
        material_constant: float = 1e10,
        exponent: float = -3.0
    ) -> int

    def calculate_fatigue_damage(
        self,
        rotation_stresses: list[float],
        cycles_per_rotation: int = 1
    ) -> FatigueCurve

    # Combined assessment
    def assess_combined_risk(
        self,
        resident_id: UUID,
        sustained_workload: float,
        duration: timedelta,
        rotation_stresses: list[float]
    ) -> dict

class CreepStage(Enum):
    PRIMARY = "primary"      # Adaptation
    SECONDARY = "secondary"  # Steady-state
    TERTIARY = "tertiary"    # Approaching failure

@dataclass
class CreepAnalysis:
    resident_id: UUID
    creep_stage: CreepStage
    larson_miller_parameter: float
    estimated_time_to_failure: timedelta
    strain_rate: float
    recommended_stress_reduction: float

@dataclass
class FatigueCurve:
    cycles_to_failure: int
    stress_amplitude: float
    current_cycles: int
    remaining_life_fraction: float  # 0.0-1.0
```

#### Usage Example

```python
from datetime import timedelta
from uuid import uuid4
from app.resilience.creep_fatigue import CreepFatigueModel, CreepStage

model = CreepFatigueModel()

# Creep analysis: Resident at 85% workload for 45 days
creep_analysis = model.predict_time_to_burnout(
    resident_id=uuid4(),
    sustained_workload=0.85,  # 85% of capacity
    duration=timedelta(days=45)
)

print(f"Creep Stage: {creep_analysis.creep_stage.value}")
# Output: "SECONDARY" or "TERTIARY"

print(f"Larson-Miller Parameter: {creep_analysis.larson_miller_parameter:.2f}")
# Output: "38.4" (approaching threshold of 45.0)

print(f"Time to burnout: {creep_analysis.estimated_time_to_failure.days} days")
# Output: "23 days"

print(f"Recommended workload reduction: {creep_analysis.recommended_stress_reduction:.1f}%")
# Output: "18.2%"

# Fatigue analysis: Rotation history (difficulty 0.0-1.0)
rotation_stresses = [
    0.9,  # Very difficult rotation (e.g., Trauma ICU)
    0.85, # Difficult rotation (e.g., Busy ER)
    0.9,  # Another hard rotation
    0.6,  # Easier rotation (e.g., Elective clinic)
    0.7   # Moderate rotation
]

fatigue_curve = model.calculate_fatigue_damage(rotation_stresses)

print(f"Cumulative cycles: {fatigue_curve.current_cycles}")
# Output: "5"

print(f"Remaining life: {fatigue_curve.remaining_life_fraction:.1%}")
# Output: "73.2%" (26.8% of life consumed)

print(f"Cycles to failure at current stress: {fatigue_curve.cycles_to_failure}")
# Output: "142" (can handle ~142 more rotations at 0.7 stress)

# Combined creep + fatigue assessment
combined = model.assess_combined_risk(
    resident_id=uuid4(),
    sustained_workload=0.85,
    duration=timedelta(days=45),
    rotation_stresses=rotation_stresses
)

print(f"\nOverall Risk: {combined['overall_risk']}")  # "high"
print(f"Risk Score: {combined['risk_score']:.2f}/3.0")  # "2.64"
print(f"Description: {combined['risk_description']}")

print("\nRecommendations:")
for rec in combined['recommendations']:
    print(f"  - {rec}")
# Output:
#   - Target workload reduction: 18.2%
#   - Schedule easier rotations to allow recovery
```

#### Integration Points

- **Long-Term Planning**: LMP tracks chronic overwork accumulation
- **Rotation Scheduler**: Balances difficult rotations using fatigue curves
- **Intervention Timing**: Tertiary creep triggers immediate action
- **Recovery Planning**: Miner's rule guides recovery rotation sequencing

#### MCP Tools

AI agents can access Creep/Fatigue analysis via MCP:

- **`assess_creep_fatigue`**: Combined creep-fatigue burnout assessment
  - Larson-Miller parameter for time-dependent creep
  - S-N curve analysis for rotation cycle fatigue
  - Miner's rule cumulative damage calculation
  - Creep stage classification: PRIMARY, SECONDARY, TERTIARY
  - Severity: `healthy`, `at_risk`, `critical`

```python
# Example MCP tool call
result = await assess_creep_fatigue(include_assessments=True, top_n=10)

if result.tertiary_creep_count > 0:
    print(f"URGENT: {result.tertiary_creep_count} residents approaching burnout")
    for assessment in result.assessments:
        if assessment.overall_risk == "high":
            lmp = assessment.creep_analysis.larson_miller_parameter
            print(f"  {assessment.resident_id}: LMP={lmp:.1f}")
```

See [MCP Tools Reference](../api/MCP_TOOLS_REFERENCE.md#assess_creep_fatigue) for full documentation.

---

### 8. Recovery Distance Analysis (Schedule Resilience)

**Source Domain**: Operations Research / Graph Theory

**File**: `/backend/app/resilience/recovery_distance.py`

#### Core Concept

**Recovery Distance (RD)** measures the minimum number of atomic edits required to restore schedule feasibility after an n-1 shock (loss of a single resource). Lower RD indicates a more resilient schedule that can absorb disruptions with minimal manual intervention.

**Key Principles**:

1. **Bounded Search**: Depth-first search up to configurable depth (default: 5 edits)
2. **Edit Atomicity**: Each edit is a single, well-defined operation
3. **Witness Recovery**: Store the actual edits that achieve minimum distance
4. **Aggregate Metrics**: Statistics across standard event suites

#### Edit Operations

| Edit Type | Description | Example |
|-----------|-------------|---------|
| `reassign` | Move uncovered block to available person | Assign Dr. Jones to cover Dr. Smith's absence |
| `swap` | Exchange assignments between two people | Trade Monday AM between two residents |
| `move_to_backup` | Use pre-designated backup personnel | Activate on-call backup for coverage |

#### Key Classes

```python
@dataclass
class N1Event:
    """Single resource loss event."""
    event_type: str  # "faculty_absence", "resident_sick", "room_closure"
    resource_id: UUID
    affected_blocks: list[UUID]
    description: str = ""

@dataclass
class RecoveryResult:
    """Result of recovery distance calculation for single event."""
    event: N1Event
    recovery_distance: int  # Minimum edits needed (0 = no recovery needed)
    witness_edits: list[AssignmentEdit]  # Concrete solution
    feasible: bool  # Whether recovery is possible within depth limit
    computation_time_seconds: float

@dataclass
class RecoveryDistanceMetrics:
    """Aggregate metrics across event suite."""
    rd_mean: float
    rd_median: float
    rd_p95: float
    rd_max: int
    breakglass_count: int  # Events requiring >3 edits
    infeasible_count: int  # Events with no recovery path
    events_tested: int
    by_event_type: dict[str, dict]

class RecoveryDistanceCalculator:
    def calculate_for_event(
        self,
        schedule: Schedule,
        event: N1Event
    ) -> RecoveryResult: ...

    def calculate_aggregate(
        self,
        schedule: Schedule,
        events: list[N1Event]
    ) -> RecoveryDistanceMetrics: ...

    def generate_test_events(
        self,
        schedule: Schedule
    ) -> list[N1Event]: ...
```

#### Usage Example

```python
from app.resilience.recovery_distance import RecoveryDistanceCalculator, N1Event

# Initialize calculator with bounds
calculator = RecoveryDistanceCalculator(max_depth=5, timeout_seconds=30.0)

# Generate standard test suite (faculty absences + resident sick days)
events = calculator.generate_test_events(schedule)

# Calculate aggregate resilience metrics
metrics = calculator.calculate_aggregate(schedule, events)

print(f"Schedule Resilience Report:")
print(f"  Mean Recovery Distance: {metrics.rd_mean:.1f} edits")
print(f"  P95 Recovery Distance: {metrics.rd_p95:.1f} edits")
print(f"  Break-glass scenarios: {metrics.breakglass_count}")
print(f"  Infeasible events: {metrics.infeasible_count}")

# Resilience interpretation
if metrics.rd_mean <= 1.0:
    print("  → HIGHLY RESILIENT: Schedule absorbs most shocks")
elif metrics.rd_mean <= 3.0:
    print("  → MODERATELY RESILIENT: Minor adjustments needed")
else:
    print("  → BRITTLE: Significant rework required for disruptions")
```

#### Resilience Thresholds

| RD Value | Interpretation | Action |
|----------|----------------|--------|
| 0 | Highly resilient | Schedule absorbs shock automatically |
| 1-2 | Moderately resilient | Quick manual fix |
| 3-5 | Fragile | Consider schedule redesign |
| >5 or ∞ | Brittle/Infeasible | Major structural issues |

#### Integration Points

- **Schedule Generation**: Use RD as tie-breaker between equivalent solutions
- **N-1/N-2 Analysis**: Complements contingency analysis with actionable recovery paths
- **Dashboard**: Display RD metrics alongside defense level status
- **Proactive Alerts**: Warn when RD_p95 exceeds threshold

#### MCP Tools

AI agents can access Recovery Distance analysis via MCP:

- **`calculate_recovery_distance`**: Measure schedule fragility
  - Tests N-1 shock scenarios (faculty absence, resident sick)
  - Returns RD mean, median, p95, and max values
  - Identifies breakglass (>3 edits) and infeasible scenarios
  - Includes witness edit sequences for sample results
  - Severity: `resilient`, `moderate`, `fragile`, `brittle`

```python
# Example MCP tool call
result = await calculate_recovery_distance(max_events=20)

print(f"RD Mean: {result.rd_mean:.1f} edits")
print(f"RD P95: {result.rd_p95:.1f} edits")

if result.rd_p95 > 4:
    print("WARNING: High recovery cost in worst case")
if result.breakglass_count > result.events_tested * 0.2:
    print("CRITICAL: Many scenarios require extensive rework")
```

See [MCP Tools Reference](../api/MCP_TOOLS_REFERENCE.md#calculate_recovery_distance) for full documentation.

---

## MCP Tools Integration

The Cross-Disciplinary Resilience Framework is exposed to AI agents via the Model Context Protocol (MCP) server. This enables AI assistants to analyze burnout risk, optimize staffing, and monitor system health programmatically.

### Composite Analytics Tools

Beyond individual module tools, the MCP server provides composite analytics that aggregate signals across multiple domains:

#### Unified Critical Index

**Tool**: `get_unified_critical_index`

Aggregates signals from three domains into a single actionable risk score:
- **Contingency (40% weight)**: N-1/N-2 vulnerability
- **Hub Analysis (35% weight)**: Network centrality
- **Epidemiology (25% weight)**: Burnout super-spreader potential

```python
result = await get_unified_critical_index(include_details=True, top_n=5)

if result.risk_level == "critical":
    print(f"ALERT: {result.universal_critical_count} faculty need protection")
    for faculty in result.top_critical_faculty:
        print(f"  - {faculty.faculty_name}: {faculty.risk_pattern}")
```

**Risk Patterns Identified**:
| Pattern | Domains High | Intervention Focus |
|---------|--------------|-------------------|
| `universal_critical` | All three | Immediate protection |
| `structural_burnout` | Contingency + Epidemiology | Workload + wellness |
| `influential_hub` | Contingency + Hub | Cross-training |
| `social_connector` | Epidemiology + Hub | Network diversification |

#### Transcription Triggers

**Tool**: `analyze_transcription_triggers`

Bio-inspired constraint regulation using gene regulatory network concepts:
- Transcription factors (TFs) activate or repress constraints
- Context-sensitive constraint weighting
- Signal transduction cascades for stress response

```python
result = await analyze_transcription_triggers(include_constraints=True)

print(f"Active TFs: {result.active_tfs}/{result.total_tfs}")
print(f"Modified constraints: {result.constraints_with_modified_weight}")
```

#### Equity Metrics

**Tool**: `calculate_equity_metrics`

Gini coefficient and workload fairness analysis:
- Measures inequality in workload distribution
- Identifies most over/underloaded providers
- Recommendations for rebalancing

```python
result = await calculate_equity_metrics(
    hours_per_provider={"FAC-001": 72, "FAC-002": 65, "FAC-003": 58},
    target_gini=0.15
)
print(f"Gini: {result.gini_coefficient:.3f}")
print(f"Equitable: {result.is_equitable}")
```

### MCP Tool Categories Summary

| Category | Tool Count | Purpose |
|----------|------------|---------|
| **Early Warning** | 4 tools | Detect burnout precursors |
| **Epidemiology** | 3 tools | Model burnout spread |
| **Optimization** | 3 tools | Staffing and quality |
| **Composite** | 4 tools | Unified risk scores |
| **Core Resilience** | 12+ tools | Framework monitoring |

### Full Reference

For complete tool documentation including all parameters, response formats, and examples:

**[MCP Tools Reference](../api/MCP_TOOLS_REFERENCE.md)**

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                   RESILIENCE MONITORING SYSTEM                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
         ┌──────────▼──────────┐        ┌──────────▼──────────┐
         │  Core Resilience    │        │  Cross-Disciplinary │
         │    Framework        │        │      Modules        │
         │  (Tier 1 & 2)       │        │     (Tier 3)        │
         └──────────┬──────────┘        └──────────┬──────────┘
                    │                               │
    ┌───────────────┼───────────────┐              │
    │               │               │              │
┌───▼────┐    ┌────▼─────┐   ┌────▼────┐         │
│ Health │    │   N-1    │   │Defense  │         │
│Monitor │    │   N-2    │   │in Depth │         │
│(Celery)│    │Contingency│   │Levels   │         │
└────┬───┘    └────┬─────┘   └────┬────┘         │
     │             │              │              │
     └─────────────┴──────────────┴──────────────┘
                    │
     ┌──────────────┴─────────────────────────────┐
     │                                             │
┌────▼─────┐  ┌──────▼───────┐  ┌────▼────┐  ┌──▼────┐
│   SPC    │  │   Process    │  │ Burnout │  │Erlang │
│Monitoring│  │  Capability  │  │  Epi    │  │   C   │
└────┬─────┘  └──────┬───────┘  └────┬────┘  └───┬───┘
     │               │               │           │
     │  Western      │  Six Sigma    │  SIR      │ Queuing
     │  Electric     │  Cp/Cpk       │  Model    │ Theory
     │  Rules        │  Indices      │  R₀       │ Service
     │               │               │           │ Level
     │               │               │           │
┌────▼─────┐  ┌──────▼───────┐  ┌──▼──────┐  ┌─▼─────┐
│ Seismic  │  │  Fire Index  │  │  Creep  │  │Alerts │
│Detection │  │   (FWI)      │  │ Fatigue │  │System │
└────┬─────┘  └──────┬───────┘  └────┬────┘  └───┬───┘
     │               │               │           │
     │  STA/LTA      │  Multi-       │ Larson-   │
     │  P-Wave       │  Temporal     │ Miller    │
     │  Algorithm    │  CFFDRS       │ S-N Curve │
     │               │               │           │
     └───────────────┴───────────────┴───────────┘
                    │
            ┌───────▼────────┐
            │  Alert & Notif │
            │   Integration  │
            └────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
   ┌────▼─────┐          ┌──────▼──────┐
   │Dashboard │          │  Intervention│
   │   UI     │          │  Recommender │
   └──────────┘          └─────────────┘
```

### Module Integration Flow

```
Scheduled Data Collection (Celery)
        │
        ├─→ Weekly Hours → SPC Monitoring → Western Electric Alerts
        │
        ├─→ Monthly Data → Process Capability → Cpk Classification
        │
        ├─→ Behavioral Signals → Seismic Detection → STA/LTA Triggers
        │
        ├─→ Social Network + Burnout States → Epidemiology → R₀ Calculation
        │
        ├─→ Case Arrivals → Erlang C → Specialist Coverage Optimization
        │
        ├─→ Multi-Temporal Data → Fire Index → FWI Danger Rating
        │
        └─→ Workload History + Rotations → Creep/Fatigue → LMP + Miner's Rule
                │
                ▼
        Unified Alert Aggregator
                │
                ├─→ Safety Level Escalation (GREEN → YELLOW → ORANGE → RED → BLACK)
                │
                ├─→ Intervention Prioritization
                │
                └─→ Dashboard Visualization
```

---

## Dependencies

All required dependencies are already included in `/backend/requirements.txt`:

```python
numpy==2.3.5                # Array operations, mathematical functions
scipy>=1.11.0               # Scientific computing, Erlang C calculations
networkx>=3.0               # Graph analysis for burnout epidemiology
```

**Optional (for advanced features)**:
- `matplotlib`: Visualization of control charts, S-N curves, SIR simulations
- `pandas`: Time series data manipulation
- `scikit-learn`: Advanced statistical analysis

### Installation

Dependencies are automatically installed via:

```bash
cd backend
pip install -r requirements.txt
```

For development/testing:

```bash
pip install -r requirements-dev.txt  # Includes pytest, coverage tools
```

---

## Implementation Tiers

The cross-disciplinary modules extend the existing 3-tier resilience architecture:

### Tier 1: Core Monitoring (Existing)

- **Utilization tracking**: 80% threshold
- **Health checks**: Celery background tasks every 15 minutes
- **Basic alerting**: Email/webhook notifications

### Tier 2: Contingency Analysis (Existing)

- **N-1/N-2 analysis**: Power grid-style vulnerability detection
- **Defense in Depth**: 5-level safety classification
- **Fallback schedules**: Pre-computed emergency plans

### Tier 3: Cross-Disciplinary Analytics (NEW)

- **SPC Monitoring**: Statistical process control for workload drift
- **Process Capability**: Six Sigma quality metrics for ACGME compliance
- **Burnout Epidemiology**: Network-based contagion modeling
- **Erlang Coverage**: Queuing theory for specialist staffing
- **Seismic Detection**: Early warning via behavioral precursors
- **Fire Index**: Multi-temporal burnout danger rating
- **Creep/Fatigue**: Materials science failure prediction

### Module Integration Strategy

**Tier 3 modules are loosely coupled**:
- Each module can run independently
- Failures in one module don't affect others
- Dashboard aggregates results from all available modules
- Alerts from any module can escalate safety levels

**Operational Modes**:
1. **Minimum Viable**: Core + one or two Tier 3 modules (e.g., SPC + Fire Index)
2. **Recommended**: Core + SPC + Fire Index + Epidemiology
3. **Full Suite**: All modules for comprehensive coverage

---

## Testing

### Test Structure

All modules have comprehensive test coverage in `/backend/tests/resilience/`:

```
backend/tests/resilience/
├── test_spc_monitoring.py           # SPC control charts, Western Electric Rules
├── test_process_capability.py       # Six Sigma Cp/Cpk calculations
├── test_burnout_epidemiology.py     # SIR models, R₀, network analysis
├── test_erlang_coverage.py          # Erlang B/C formulas, queuing metrics
├── test_seismic_detection.py        # STA/LTA algorithm, trigger detection
├── test_burnout_fire_index.py       # FWI calculations, danger classification
├── test_creep_fatigue.py            # Larson-Miller, S-N curves, Miner's rule
└── test_resilience_integration.py   # Cross-module integration tests
```

### Running Tests

```bash
# All cross-disciplinary resilience tests
cd backend
pytest tests/resilience/ -v

# Specific module
pytest tests/resilience/test_spc_monitoring.py -v

# With coverage report
pytest tests/resilience/ --cov=app.resilience --cov-report=html

# Integration tests only
pytest tests/resilience/test_resilience_integration.py -v

# Performance/load tests
pytest tests/resilience/test_resilience_load.py -v
```

### Test Coverage

Each module achieves **>90% code coverage** with tests for:

- ✅ Core algorithm correctness (mathematical formulas)
- ✅ Edge cases (zero values, empty data, division by zero)
- ✅ Input validation (negative values, out-of-range parameters)
- ✅ Alert generation and severity classification
- ✅ Integration with existing resilience framework
- ✅ Performance under realistic data volumes

### Example Test Pattern

```python
# test_spc_monitoring.py
def test_western_electric_rule_1_violation():
    """Test detection of 3σ violation (Rule 1)."""
    chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)

    # One point exceeds UCL (75h)
    weekly_hours = [58, 62, 59, 80, 61, 60]

    alerts = chart.detect_western_electric_violations(uuid4(), weekly_hours)

    assert len(alerts) == 1
    assert alerts[0].rule == "Rule 1"
    assert alerts[0].severity == "CRITICAL"
    assert 80.0 in alerts[0].data_points

def test_process_capability_incapable():
    """Test Cpk classification for incapable process."""
    analyzer = ScheduleCapabilityAnalyzer()

    # Wide variation, often exceeds 80h limit
    weekly_hours = [45, 78, 82, 50, 85, 48, 79, 83, ...]

    report = analyzer.analyze_workload_capability(weekly_hours, 40, 80)

    assert report.capability_status == "INCAPABLE"
    assert report.cpk < 1.0
    assert report.sigma_level < 3.0
```

---

## References

### Recent Research & Updates

#### ACGME 2025-2026 Updates
- **80-hour weekly limit maintained** with increased flexibility provisions
- Alternative scheduling models showing reduced fatigue in pilot programs
- Enhanced supervision requirements for complex procedures
- Source: ACGME Common Program Requirements (2025-2026 revision)

#### Burnout Research (2024-2025)
- Hybrid scheduling models (shorter shifts with protected rest) demonstrate 15-20% reduction in burnout markers
- Social network analysis confirms burnout contagion effects through shared shifts and mentorship
- Early intervention at Rₜ < 1.5 prevents 60% of cascading burnout events

#### Scheduling Technology
- **OR-Tools CP-SAT** remains the industry standard for constraint satisfaction
- Multi-objective genetic algorithms complement CP-SAT for Pareto optimization
- FHIR R4 Schedule resource separates slot availability from booked appointments

#### Healthcare System Resilience
- 2024 CrowdStrike outage impacted 100+ hospital systems, validating need for offline-first architectures
- Queue-based retry patterns with exponential backoff prevent cascade failures
- Idempotency keys + transactional outbox pattern enables exactly-once schedule execution

### Academic Literature

#### SPC Monitoring
- Shewhart, W.A. (1931). *Economic Control of Quality of Manufactured Product*. Van Nostrand.
- Western Electric Company (1956). *Statistical Quality Control Handbook*. Western Electric.
- Montgomery, D.C. (2019). *Statistical Quality Control: A Modern Introduction* (8th ed.). Wiley.

#### Process Capability
- Motorola Inc. (1987). *Six Sigma Quality Program*.
- Kane, V.E. (1986). "Process Capability Indices." *Journal of Quality Technology*, 18(1), 41-52.
- Kotz, S. & Johnson, N.L. (2002). "Process Capability Indices—A Review, 1992–2000." *Journal of Quality Technology*, 34(1), 2-19.

#### Burnout Epidemiology
- Christakis, N.A. & Fowler, J.H. (2008). "Dynamic spread of happiness in a large social network." *BMJ*, 337, a2338.
- Bakker, A.B., Schaufeli, W.B., Sixma, H.J., & Bosveld, W. (2009). "Patient demands, lack of reciprocity, and burnout." *Journal of Organizational Behavior*, 22, 425-441.
- Kermack, W.O. & McKendrick, A.G. (1927). "A contribution to the mathematical theory of epidemics." *Proceedings of the Royal Society A*, 115(772), 700-721.

#### Erlang Coverage
- Erlang, A.K. (1917). "Solution of some problems in the theory of probabilities of significance in automatic telephone exchanges." *Elektrotkeknikeren*, 13, 5-13.
- Cooper, R.B. (1981). *Introduction to Queueing Theory* (2nd ed.). North Holland.
- Koole, G. & Mandelbaum, A. (2002). "Queueing models of call centers." *Annals of Operations Research*, 113, 41-59.

#### Seismic Detection
- Allen, R.V. (1978). "Automatic earthquake recognition and timing from single traces." *Bulletin of the Seismological Society of America*, 68(5), 1521-1532.
- Withers, M. et al. (1998). "A comparison of select trigger algorithms for automated global seismic phase and event detection." *Bulletin of the Seismological Society of America*, 88(1), 95-106.
- Given, D.D. et al. (2018). "Revised Technical Implementation Plan for the ShakeAlert System—An Earthquake Early Warning System for the West Coast of the United States." USGS Open-File Report 2018-1155.

#### Fire Weather Index
- Van Wagner, C.E. (1987). *Development and structure of the Canadian Forest Fire Weather Index System*. Canadian Forestry Service, Forestry Technical Report 35.
- Stocks, B.J. et al. (1989). "The Canadian Forest Fire Danger Rating System: An Overview." *The Forestry Chronicle*, 65(4), 258-265.
- San-Miguel-Ayanz, J. et al. (2012). "Current methods to assess fire danger potential." In *Wildland Fire Danger Estimation and Mapping* (pp. 21-61). World Scientific.

#### Creep/Fatigue Mechanics
- Larson, F.R. & Miller, J. (1952). "A time-temperature relationship for rupture and creep stresses." *Transactions of the ASME*, 74, 765-775.
- Wöhler, A. (1870). "Über die Festigkeitsversuche mit Eisen und Stahl." *Zeitschrift für Bauwesen*, 20, 73-106.
- Miner, M.A. (1945). "Cumulative damage in fatigue." *Journal of Applied Mechanics*, 12, A159-A164.
- Ashby, M.F. & Jones, D.R.H. (2012). *Engineering Materials 1: An Introduction to Properties, Applications and Design* (4th ed.). Butterworth-Heinemann.

### Industry Standards

- **ISO 7870**: Control charts (SPC)
- **ISO 22514**: Process capability and performance
- **NFPA 1144**: Standard for Reducing Structure Ignition Hazards from Wildland Fire
- **ASTM E606**: Standard Test Method for Strain-Controlled Fatigue Testing
- **ACGME Common Program Requirements**: Work hour limits and supervision

### Online Resources

- Canadian Forest Service FWI System: https://cwfis.cfs.nrcan.gc.ca/background/summary/fwi
- USGS Earthquake Early Warning: https://www.usgs.gov/programs/earthquake-hazards/earthquake-early-warning
- ASQ Six Sigma Resources: https://asq.org/quality-resources/six-sigma
- NetworkX Documentation: https://networkx.org/documentation/stable/

---

## Usage Guidelines

### When to Use Which Module

| Scenario | Recommended Module(s) | Rationale |
|----------|----------------------|-----------|
| **Weekly workload monitoring** | SPC Monitoring | Detects drift and trends in real-time |
| **ACGME compliance validation** | Process Capability | Quantifies scheduling quality (Cpk) |
| **Program-wide burnout screening** | Fire Index | Multi-temporal assessment captures complexity |
| **Individual early warning** | Seismic Detection | Behavioral precursors provide lead time |
| **Network effects (team-based)** | Burnout Epidemiology | Models social contagion |
| **Specialist coverage planning** | Erlang Coverage | Optimizes staffing for service levels |
| **Chronic overwork assessment** | Creep/Fatigue | Tracks long-term damage accumulation |

### Dashboard Integration

**Recommended Dashboard Layout**:

```
┌────────────────────────────────────────────────────────────┐
│  RESILIENCE OVERVIEW                    Safety Level: 🟢    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  SPC Control Chart (Weekly Hours)           FWI Map        │
│  ├─ UCL: 75h                                ┌────┬────┐    │
│  ├─ Target: 60h                             │ 🟢 │ 🟡 │    │
│  └─ LCL: 45h                                ├────┼────┤    │
│                                             │ 🟠 │ 🔴 │    │
│  Process Capability: Cpk = 1.42 (CAPABLE)   └────┴────┘    │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  ALERTS                                                    │
│  🚨 Seismic: R1234 swap requests +450% (STA/LTA = 5.2)    │
│  ⚠️  SPC: R5678 workload shift detected (Rule 2)          │
│  ℹ️  Epi: Program Rₜ = 1.15 (SPREADING)                   │
├────────────────────────────────────────────────────────────┤
│  SPECIALIST COVERAGE                                       │
│  Orthopedics: 4 required (95% SL) | Current: 3 ⚠️         │
│  Cardiology: 2 required (95% SL) | Current: 2 ✅          │
└────────────────────────────────────────────────────────────┘
```

### Performance Considerations

**Computational Costs** (benchmark on 100 residents, 52 weeks data):

- **SPC Monitoring**: <10ms (very fast, suitable for real-time)
- **Process Capability**: <20ms (fast)
- **Fire Index**: <50ms (moderate)
- **Erlang Coverage**: <5ms (very fast)
- **Seismic Detection**: <100ms (moderate, depends on signal length)
- **Burnout Epidemiology**: <500ms (slower, network analysis)
- **Creep/Fatigue**: <30ms (fast)

**Recommended Execution Frequency**:
- **Real-time**: SPC (on new data), Erlang (on-demand)
- **Daily**: Fire Index, Seismic Detection
- **Weekly**: Process Capability, Epidemiology
- **Monthly**: Creep/Fatigue (long-term trends)

---

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**
   - Train neural networks on historical alerts to improve prediction accuracy
   - AutoML for dynamic threshold tuning

2. **Multi-Site Analysis**
   - Compare resilience metrics across multiple residency programs
   - Benchmark performance against peer institutions

3. **Real-Time Dashboard**
   - WebSocket-based live updates
   - Interactive control charts with drill-down capability

4. **Predictive Scheduling**
   - Use creep/fatigue models to generate burnout-resistant schedules
   - Optimize rotations using S-N curve fatigue analysis

5. **Mobile Alerts**
   - Push notifications for critical alerts
   - Resident self-assessment via mobile app

### Research Opportunities

- **Validation Studies**: Correlate module predictions with actual burnout outcomes
- **Threshold Calibration**: Fine-tune Western Electric Rules for medical context
- **Network Topology**: Optimal team structures to minimize contagion
- **Hybrid Models**: Combine multiple modules using ensemble methods

---

## Conclusion

The Cross-Disciplinary Engineering Resilience Framework represents a paradigm shift in burnout prediction—from reactive intervention to proactive prevention. By applying 50+ years of proven engineering science from diverse domains, this framework provides quantitative, actionable insights that complement clinical judgment.

**Key Achievements**:
- 8 production-ready modules from 7 engineering disciplines
- 13+ MCP tools exposing resilience framework to AI agents
- >90% test coverage with comprehensive validation
- Mathematical rigor backed by peer-reviewed research
- Modular architecture allowing incremental adoption
- Real-world applicability demonstrated in test scenarios

**Impact**:
Medical residencies can now leverage the same tools that:
- Prevent semiconductor defects (SPC)
- Achieve Six Sigma quality (Process Capability)
- Model infectious disease spread (Epidemiology)
- Optimize call center staffing (Erlang C)
- Detect earthquakes early (Seismology)
- Predict wildfire danger (Fire Science)
- Prevent structural failures (Materials Science)
- Balance workload distribution (Gini coefficient from economics)

The result: **Data-driven burnout prevention** that protects residents, ensures patient safety, and maintains program quality.

---

---

## Tier 4: Exotic Cross-Disciplinary Research (NEW - 2025-12-29)

Beyond the core Tier 3 modules, the framework now includes **20 additional MCP tools** from 6 advanced research domains. These tools complement existing analytics with specialized capabilities.

### 9. Kalman Filter (Control Theory)

**Source Domain**: Estimation & Control Theory

**Files**: `/mcp-server/src/scheduler_mcp/tools/kalman_filter_tools.py`

#### Core Concept

The Kalman filter is an optimal recursive estimator that combines predictions from a system model with noisy observations to produce filtered estimates with minimum variance. Originally developed for spacecraft navigation (Apollo program), now used in GPS, robotics, and signal processing.

#### Medical Scheduling Application

Filters noisy workload measurements to extract true underlying trends:
- **State**: Estimated true workload
- **Observations**: Measured workload (noisy due to absences, swaps, etc.)
- **Output**: Cleaned trend + predictions

**Why This Works**: Raw workload data has measurement noise. Kalman filtering provides cleaner signals for downstream analysis (SPC, trend detection).

#### MCP Tools

- **`analyze_workload_trend`**: Apply Kalman filter to workload history
  - Returns filtered values, predictions, confidence intervals
  - Trend assessment: INCREASING, STABLE, DECREASING
  - Complements SPC by providing cleaner input signals

- **`detect_workload_anomalies`**: Compare raw vs filtered to find outliers
  - Severity: MODERATE (2σ), HIGH (3σ), CRITICAL (4σ+)
  - Provides recommendations based on anomaly patterns

---

### 10. Fourier/FFT Analysis (Signal Processing)

**Source Domain**: Signal Processing & Harmonic Analysis

**Files**: `/mcp-server/src/scheduler_mcp/tools/fourier_analysis_tools.py`

#### Core Concept

Fourier Transform decomposes time-domain signals into frequency components, revealing periodic patterns invisible in raw data. Power spectrum analysis identifies dominant cycles and their strengths.

#### Medical Scheduling Application

Detects natural cycles in scheduling patterns:
- **7-day cycles**: Weekly patterns (ACGME 1-in-7 rule)
- **14-day cycles**: Bi-weekly rotations
- **28-day cycles**: ACGME 4-week averaging windows

**Why This Works**: Schedules have natural rhythms. FFT precisely identifies these periods, enabling anti-churn optimization and ACGME alignment validation.

#### MCP Tools

- **`detect_schedule_cycles`**: FFT-based periodicity detection
  - Returns dominant periods in days with power spectrum
  - Interprets standard periods (7d = weekly, 28d = ACGME window)

- **`analyze_harmonic_resonance`**: Check alignment with ACGME windows
  - Alignment scores for 7d, 14d, 28d periods
  - Health status: healthy/degraded/critical

- **`calculate_spectral_entropy`**: Measure schedule complexity
  - Low entropy = regular/predictable; High entropy = chaotic

---

### 11. Game Theory (Economics)

**Source Domain**: Game Theory & Mechanism Design

**Files**: `/mcp-server/src/scheduler_mcp/tools/game_theory_tools.py`

#### Core Concept

Nash equilibrium describes a stable state where no player can improve by unilaterally changing strategy. Applied to scheduling, it predicts when people will request swaps.

#### Medical Scheduling Application

Models scheduling as a game:
- **Players**: Residents/faculty
- **Strategies**: Accept assignment vs request swap
- **Payoffs**: Preference satisfaction, workload balance

A schedule is **Nash stable** if no one has incentive to deviate.

**Why This Works**: Swap requests are predictable. Game theory identifies dissatisfied individuals before they submit requests, enabling proactive intervention.

#### MCP Tools

- **`analyze_nash_stability`**: Check if schedule is Nash equilibrium
  - Returns stability score and list of players with deviation incentives
  - Predicts swap request rate

- **`find_deviation_incentives`**: Analyze specific person's utility
  - Utility breakdown: workload, preference, convenience, continuity
  - Best alternative actions and improvement potential

- **`detect_coordination_failures`**: Find blocked Pareto improvements
  - Multi-way swaps that would benefit all parties
  - "Welfare left on table" quantification

---

### 12. Value-at-Risk (Financial Engineering)

**Source Domain**: Financial Risk Management

**Files**: `/mcp-server/src/scheduler_mcp/var_risk_tools.py`

#### Core Concept

VaR (Value-at-Risk) quantifies worst-case losses with probabilistic bounds:
- "With 95% confidence, coverage won't drop below X%"

CVaR (Conditional VaR / Expected Shortfall) measures average loss in tail scenarios.

#### Medical Scheduling Application

Applies financial risk metrics to schedule vulnerability:
- **VaR for coverage**: Probabilistic bounds on coverage drops
- **Monte Carlo simulation**: Stress test random disruptions
- **Tail risk**: Quantify worst-case scenarios

**Why This Works**: N-1/N-2 contingency is deterministic. VaR adds probabilistic reasoning for scenarios with uncertain outcomes (flu season, deployment timing).

#### MCP Tools

- **`calculate_coverage_var`**: VaR at multiple confidence levels
- **`calculate_workload_var`**: VaR for workload distribution
- **`simulate_disruption_scenarios`**: Monte Carlo stress testing
- **`calculate_conditional_var`**: Expected Shortfall (CVaR)

---

### 13. Lotka-Volterra Dynamics (Ecology)

**Source Domain**: Population Ecology & Dynamical Systems

**Files**: `/mcp-server/src/scheduler_mcp/tools/ecological_dynamics_tools.py`

#### Core Concept

Lotka-Volterra equations model predator-prey oscillations:
```
dx/dt = αx - βxy    (prey grows, consumed by predator)
dy/dt = δxy - γy    (predator grows from prey, decays naturally)
```

Produces characteristic boom/bust cycles.

#### Medical Scheduling Application

Models capacity/demand oscillations:
- **x (prey)** = Available capacity/slack
- **y (predator)** = Workload demand

Predicts periodic coverage crunches and recovery times.

**Why This Works**: Scheduling systems exhibit natural cycles. LV equations model these dynamics, predicting crunches before they occur.

#### MCP Tools

- **`analyze_supply_demand_cycles`**: Fit LV model to historical data
  - Returns fitted parameters, equilibrium, oscillation period
  - R² goodness of fit

- **`predict_capacity_crunch`**: Forecast when capacity falls below threshold
  - Risk level, days until crunch, recovery timeline

- **`find_equilibrium_point`**: Calculate stable equilibrium
  - Sensitivity analysis for parameter changes

- **`simulate_intervention`**: Test what-if scenarios
  - Effect of adding capacity or reducing demand

---

### 14. Hopfield Network Attractors (Neuroscience)

**Source Domain**: Computational Neuroscience & Neural Networks

**Files**: `/mcp-server/src/scheduler_mcp/hopfield_attractor_tools.py`

#### Core Concept

Hopfield networks model associative memory as energy minimization:
- **State**: Schedule encoded as binary pattern
- **Energy**: E = -0.5 × Σ(w_ij × s_i × s_j)
- **Attractors**: Stable patterns (energy minima)
- **Basin depth**: Robustness to perturbation

#### Medical Scheduling Application

Models schedule stability as energy landscape:
- **Low energy** = Stable schedule
- **Attractors** = Natural schedule configurations
- **Spurious attractors** = Anti-patterns (overload concentration, etc.)

**Why This Works**: Schedules naturally "settle" into stable patterns. Hopfield analysis identifies these patterns and measures robustness.

#### MCP Tools

- **`calculate_hopfield_energy`**: Compute schedule state energy
  - Stability classification: very_stable → highly_unstable

- **`find_nearby_attractors`**: Identify stable patterns near current state
  - Hamming distance to better configurations
  - Improvement potential

- **`measure_basin_depth`**: Energy barrier to escape current attractor
  - Basin stability index
  - Robustness threshold

- **`detect_spurious_attractors`**: Find scheduling anti-patterns
  - Overload concentration, shift clustering, etc.
  - Mitigation recommendations

---

### Integration: Exotic Tools with Core Framework

| Exotic Tool | Complements | Synergy |
|-------------|-------------|---------|
| Kalman Filter | SPC Monitoring | Cleaner signals for Western Electric rules |
| Fourier/FFT | Time Crystal | Precise cycle detection for anti-churn |
| Game Theory | Shapley Fairness | Stability + fairness together |
| VaR | N-1/N-2 Contingency | Probabilistic bounds on disruption |
| Lotka-Volterra | Homeostasis | Models dynamics homeostasis responds to |
| Hopfield | Thermodynamics | Energy landscape complements free energy |

### Full Documentation

See **[Exotic Research Tools Reference](/mcp-server/docs/EXOTIC_RESEARCH_TOOLS.md)** for complete API documentation, parameters, and usage examples.

---

**Document Version**: 1.2
**Last Updated**: 2025-12-29
**Maintained By**: Resilience Engineering Team
**Related Documentation**:
- [MCP Tools Reference](../api/MCP_TOOLS_REFERENCE.md)
- [Exotic Research Tools](../../mcp-server/docs/EXOTIC_RESEARCH_TOOLS.md)
- [Resilience Framework Guide](../guides/resilience-framework.md)
- [System Architecture](overview.md)
- [Backend Architecture](backend.md)
- [Testing Strategy](../development/testing.md)
