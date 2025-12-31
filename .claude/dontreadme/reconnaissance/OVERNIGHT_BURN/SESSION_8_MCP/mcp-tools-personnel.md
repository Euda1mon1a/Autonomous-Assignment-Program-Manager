# MCP Personnel Query Tools Documentation

**Session 8 - SEARCH_PARTY Operation: Personnel Management Tools**

> Complete inventory and documentation of Model Context Protocol (MCP) tools for querying personnel data in the residency scheduler system.

---

## Table of Contents

1. [Overview](#overview)
2. [Tool Inventory](#tool-inventory)
3. [Personnel Query Parameters](#personnel-query-parameters)
4. [Resident-Specific Tools](#resident-specific-tools)
5. [Faculty-Specific Tools](#faculty-specific-tools)
6. [Staff & General Personnel Tools](#staff--general-personnel-tools)
7. [Personnel Role Concepts](#personnel-role-concepts)
8. [Query Patterns & Examples](#query-patterns--examples)
9. [Integration Guide](#integration-guide)
10. [Undocumented Filters & Features](#undocumented-filters--features)

---

## Overview

The MCP server provides **30+ tools** for querying and managing medical residency personnel data. These tools operate at multiple levels:

- **Resource Layer**: High-level schedule and compliance snapshots
- **API Layer**: Via `SchedulerAPIClient` for HTTP-based queries
- **Residency-Specific Tools**: Residents, faculty, workload analysis
- **Burnout/Fatigue Tools**: FRMS, fire danger, precursor detection
- **Resilience Tools**: N-1/N-2 analysis, centrality detection, contingency planning
- **Analytics Tools**: Erlang C optimization, process capability, equity metrics

### Key Principles

- **No PII in Results**: All person identifiers anonymized (PGY-1, Faculty, role-based IDs)
- **Role-Based Filtering**: Supports residents, faculty, staff, clinical personnel (8 total roles)
- **Date Range Queries**: Most tools support configurable start/end dates
- **Async-First**: All tool functions are async-compatible for FastMCP

---

## Tool Inventory

### Resource-Level Tools (High-Level Schedule Views)

#### 1. `get_schedule_status`

**Purpose**: Comprehensive schedule status snapshot

**Location**: `/scheduler_mcp/resources.py`

**Parameters**:
```python
async def get_schedule_status(
    start_date: date | None = None,      # Defaults to today
    end_date: date | None = None,        # Defaults to start_date + 30 days
) -> ScheduleStatusResource
```

**Returns**:
```python
ScheduleStatusResource:
  - query_timestamp: datetime
  - date_range_start: date
  - date_range_end: date
  - total_assignments: int              # Total person assignments in range
  - active_conflicts: int               # Scheduling conflicts detected
  - pending_swaps: int                  # Pending swap requests
  - coverage_metrics: CoverageMetrics   # Faculty/resident staffing stats
    - total_days: int
    - covered_days: int
    - coverage_rate: float (0.0-1.0)
    - understaffed_days: int            # Days below min faculty threshold
    - overstaffed_days: int             # Days above max faculty threshold
    - average_faculty_per_day: float
    - average_residents_per_day: float
  - assignments: list[AssignmentInfo]   # Individual assignments
    - assignment_id: str
    - person_id: str
    - person_role: str                  # "PGY-1", "PGY-2", "Faculty", "Staff"
    - block_name: str
    - rotation: str
    - start_date: date
    - end_date: date
    - is_supervising: bool
    - pgy_level: int | None             # For residents
  - last_generated: datetime | None
  - generation_algorithm: str | None
```

**Example Usage**:
```python
# Get current 30-day schedule overview
status = await get_schedule_status()

# Get specific date range
status = await get_schedule_status(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31)
)

# Filter results by coverage metrics
if status.coverage_metrics.coverage_rate < 0.8:
    print(f"Alert: {status.coverage_metrics.understaffed_days} understaffed days")
```

---

#### 2. `get_compliance_summary`

**Purpose**: ACGME compliance analysis for residents

**Location**: `/scheduler_mcp/resources.py`

**Parameters**:
```python
async def get_compliance_summary(
    start_date: date | None = None,     # Defaults to today
    end_date: date | None = None,       # Defaults to start_date + 30 days
) -> ComplianceSummaryResource
```

**Returns**:
```python
ComplianceSummaryResource:
  - query_timestamp: datetime
  - date_range_start: date
  - date_range_end: date
  - metrics: ComplianceMetrics
    - overall_compliance_rate: float (0.0-1.0)
    - work_hour_violations: int         # 80-hour rule breaches
    - consecutive_duty_violations: int  # 1-in-7 rule breaches
    - rest_period_violations: int       # Minimum rest violations
    - supervision_violations: int       # Supervision ratio breaches
    - total_violations: int
    - residents_affected: int           # Unique residents with violations
  - violations: list[ViolationInfo]     # Critical violations
    - violation_type: str               # "work_hour_limit", "consecutive_duty"
    - severity: str                     # "critical", "warning", "info"
    - person_id: str                    # Anonymized
    - person_role: str                  # "PGY-1", "PGY-2", "PGY-3"
    - date_range: tuple[date, date]
    - description: str
    - details: dict                     # Violation-specific metrics
  - warnings: list[ViolationInfo]       # Supervision and soft violations
  - recommendations: list[str]          # Action items
```

**Compliance Rules Checked**:
1. **80-Hour Rule**: Max 80 hours/week averaged over 4-week rolling periods
   - HOURS_PER_BLOCK = 6
   - MAX_WEEKLY_HOURS = 80
   - ROLLING_WEEKS = 4

2. **1-in-7 Rule**: Max 6 consecutive days of work
   - MAX_CONSECUTIVE_DAYS = 6

3. **Supervision Ratios**:
   - PGY-1: 1 faculty per 2 residents (2:1 ratio)
   - PGY-2/3: 1 faculty per 4 residents (4:1 ratio)

**Example Usage**:
```python
# Get compliance summary for this month
summary = await get_compliance_summary(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31)
)

# Find residents with violations
for violation in summary.violations:
    if violation.severity == "critical":
        print(f"{violation.person_role}: {violation.description}")

# Check overall compliance health
if summary.metrics.overall_compliance_rate < 0.95:
    print(f"Warning: {summary.metrics.residents_affected} residents out of compliance")
```

---

### API Client Layer

#### 3. `SchedulerAPIClient.get_people()`

**Purpose**: Query all people in system (residents + faculty)

**Location**: `/scheduler_mcp/api_client.py`

**Parameters**:
```python
async def get_people(self, limit: int = 100) -> dict[str, Any]:
    """Get all people (residents and faculty)."""
```

**Returns**:
```python
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",  # UUID
      "name": "John Smith",           # May contain PII
      "role": "faculty" | "resident" | "staff",
      "type": "faculty" | "resident" | "staff",
      "is_resident": bool,
      "is_faculty": bool,
      "pgy_level": 1 | 2 | 3 | None,  # For residents only
      "specialty": "Family Medicine",
      "is_active": bool
    },
    ...
  ],
  "total": int,
  "limit": int,
  "offset": int
}
```

**Security Note**: This endpoint returns full names (PII). Use with caution in production.

**Example Usage**:
```python
client = SchedulerAPIClient()
async with client:
    people = await client.get_people(limit=50)
    residents = [p for p in people["items"] if p["is_resident"]]
    faculty = [p for p in people["items"] if p["is_faculty"]]
    print(f"Total residents: {len(residents)}")
    print(f"Total faculty: {len(faculty)}")
```

---

### Resident-Specific Tools

#### 4. `run_frms_assessment`

**Purpose**: Comprehensive Fatigue Risk Management System (FRMS) assessment for a resident

**Location**: `/scheduler_mcp/frms_integration.py`

**Parameters**:
```python
async def run_frms_assessment(
    resident_id: str,  # UUID of resident
    target_time: datetime | None = None  # Assessment time (defaults to now)
) -> FRMSAssessmentResponse
```

**Returns**:
```python
FRMSAssessmentResponse:
  - resident_id: str                    # UUID
  - resident_name: str                  # Anonymized
  - assessment_timestamp: datetime
  - hazard_level: str                   # GREEN, YELLOW, ORANGE, RED, BLACK
  - fatigue_score: float (0.0-1.0)      # Cumulative fatigue
  - sleep_debt: float                   # Accumulated sleep deficit (hours)
  - hours_since_sleep: float            # Circadian time awake
  - predicted_pvis: float               # Performance impairment (0-1)
  - recommendations: list[str]          # Intervention suggestions
  - supporting_metrics: dict            # Detailed calculation data
```

**Hazard Levels**:
- **GREEN**: Safe, normal operations (0-20% fatigue)
- **YELLOW**: Elevated fatigue, monitor (20-40%)
- **ORANGE**: High fatigue, schedule intervention (40-60%)
- **RED**: Critical fatigue, mandatory rest (60-80%)
- **BLACK**: Dangerous, immediate removal (80-100%)

**Example Usage**:
```python
from uuid import UUID

# Assess single resident
resident_id = "550e8400-e29b-41d4-a716-446655440000"
frms = await run_frms_assessment(resident_id)

if frms.hazard_level in ["RED", "BLACK"]:
    print(f"ALERT: {frms.resident_name} at {frms.hazard_level} level")
    print(f"Sleep debt: {frms.sleep_debt:.1f} hours")
    print(f"Recommendations: {frms.recommendations}")
```

---

#### 5. `scan_team_fatigue`

**Purpose**: Scan all residents for fatigue risks (batch assessment)

**Location**: `/scheduler_mcp/frms_integration.py`

**Parameters**:
```python
async def scan_team_fatigue() -> TeamFatigueScanResponse
```

**Returns**:
```python
TeamFatigueScanResponse:
  - total_residents: int
  - residents_green: int               # Safe levels
  - residents_yellow: int              # Elevated risk
  - residents_orange: int              # Intervention needed
  - residents_red: int                 # Critical risk
  - residents_black: int               # Immediate action required
  - critical_residents: list[ResidentFatigueSummary]  # RED + BLACK
    - resident_id: str
    - name: str (anonymized)
    - hazard_level: str
    - sleep_debt: float
    - fatigue_score: float
  - at_risk_residents: list[ResidentFatigueSummary]   # ORANGE + YELLOW
  - recommendations: list[str]
```

**Example Usage**:
```python
# Scan all residents for fatigue
scan = await scan_team_fatigue()

# Get immediate intervention list
if scan.residents_red > 0 or scan.residents_black > 0:
    print(f"URGENT: {scan.residents_red + scan.residents_black} critical residents")
    for resident in scan.critical_residents:
        print(f"  - {resident.name}: {resident.hazard_level}")

# Generate action plan
for resident in scan.at_risk_residents:
    print(f"Monitor {resident.name} - sleep debt {resident.sleep_debt}h")
```

---

#### 6. `detect_burnout_precursors_tool`

**Purpose**: Early detection of burnout using seismic STA/LTA algorithm

**Location**: `/scheduler_mcp/server.py` (line 3761)

**Parameters**:
```python
async def detect_burnout_precursors_tool(
    resident_id: str,
    signal_type: str,               # "workload_surge", "sleep_debt", "mood_decline"
    time_series: list[float],       # Chronological measurements
    short_window: int = 5,          # STA window (days)
    long_window: int = 30,          # LTA window (days)
) -> PrecursorDetectionResponse
```

**Returns**:
```python
PrecursorDetectionResponse:
  - resident_id: str
  - signal_type: str
  - sta_value: float                # Short-term average
  - lta_value: float                # Long-term average
  - ratio: float                    # STA/LTA ratio (alert if > threshold)
  - threshold: float                # Detection threshold
  - detected: bool                  # P-wave equivalent detected?
  - magnitude: float                # Strength of signal
  - recommendations: list[str]
```

**Signal Types**:
- `workload_surge`: Rapid increase in assigned hours
- `sleep_debt`: Cumulative sleep deficit growth
- `mood_decline`: Subjective well-being decrease
- `error_rate`: Increase in clinical errors
- `fatigue_escalation`: Self-reported fatigue progression

**Example Usage**:
```python
# Detect workload surge precursor
workload_data = [40, 42, 45, 48, 52, 58, 65, 70, 75, 78]  # 10 days
result = await detect_burnout_precursors_tool(
    resident_id="550e8400-e29b-41d4-a716-446655440000",
    signal_type="workload_surge",
    time_series=workload_data
)

if result.detected and result.ratio > result.threshold:
    print(f"PRECURSOR ALERT: {result.resident_id}")
    print(f"STA/LTA Ratio: {result.ratio:.2f} (threshold: {result.threshold:.2f})")
```

---

#### 7. `calculate_fire_danger_index_tool`

**Purpose**: Burnout risk using Canadian Fire Weather Index (CFFDRS) model

**Location**: `/scheduler_mcp/server.py` (line 3891)

**Parameters**:
```python
async def calculate_fire_danger_index_tool(
    resident_id: str,
    recent_hours: float,             # Hours worked last week
    monthly_load: float,             # Average monthly hours
    yearly_satisfaction: float,      # 0-100 satisfaction score
    workload_velocity: float = 0.0,  # Rate of change (hours/week)
) -> FireDangerResponse
```

**Returns**:
```python
FireDangerResponse:
  - resident_id: str
  - danger_index: float (0-100)       # Like "Richter scale" for burnout
  - danger_level: str                 # low, moderate, high, extreme
  - vegetation_state: float           # Analog: fatigue accumulation
  - fine_fuel_moisture: float         # Analog: resilience depletion
  - build_up_index: float             # Analog: chronic stress buildup
  - drought_code: float               # Analog: long-term depletion
  - spread_component: float           # Analog: contagion risk
  - fire_weather_index: float         # Combined burnout risk
  - recommendations: list[str]
```

**Danger Levels**:
- **low** (0-20): Safe workload
- **moderate** (20-50): Monitor closely
- **high** (50-75): Intervention needed
- **extreme** (75-100): Immediate action required

**Example Usage**:
```python
# Calculate burnout danger for resident
danger = await calculate_fire_danger_index_tool(
    resident_id="550e8400-e29b-41d4-a716-446655440000",
    recent_hours=78,                 # Worked 78 hours last week
    monthly_load=70,                 # Average 70 hrs/month
    yearly_satisfaction=35,          # Satisfaction declining
    workload_velocity=5.0            # Increasing 5 hrs/week
)

print(f"Danger Index: {danger.danger_index:.1f}")
print(f"Level: {danger.danger_level}")
if danger.danger_level == "extreme":
    print("EMERGENCY: Resident requires immediate relief")
```

---

#### 8. `predict_burnout_magnitude_tool`

**Purpose**: Multi-signal burnout prediction

**Location**: `/scheduler_mcp/server.py` (line 3803)

**Parameters**:
```python
async def predict_burnout_magnitude_tool(
    resident_id: str,
    signals: dict[str, list[float]],  # Multiple signal types
    short_window: int = 5,
    long_window: int = 30,
) -> MultiSignalMagnitudeResponse
```

**Example Usage**:
```python
# Combine multiple signals
signals = {
    "workload_surge": [40, 42, 45, 48, 52, 58, 65, 70, 75, 78],
    "mood_decline": [8.0, 7.8, 7.5, 7.0, 6.2, 5.8, 4.5, 3.0, 2.5, 2.0],
    "sleep_debt": [2, 4, 6, 10, 14, 18, 22, 26, 28, 30]
}

magnitude = await predict_burnout_magnitude_tool(
    resident_id="550e8400-e29b-41d4-a716-446655440000",
    signals=signals
)

print(f"Predicted magnitude: {magnitude.magnitude:.1f}/10")
```

---

#### 9. `run_spc_analysis_tool`

**Purpose**: Statistical Process Control (Western Electric Rules) for workload monitoring

**Location**: `/scheduler_mcp/server.py` (line 3834)

**Parameters**:
```python
async def run_spc_analysis_tool(
    resident_id: str,
    weekly_hours: list[float],        # Weekly hours over time
    target_hours: float = 60.0,       # Target weekly average
    sigma: float = 5.0,               # Process std dev
) -> SPCAnalysisResponse
```

**Returns**:
```python
SPCAnalysisResponse:
  - resident_id: str
  - mean: float                       # Average hours
  - std_dev: float                    # Standard deviation
  - violations: list[str]             # Western Electric rule violations
    - "Rule 1: Point beyond 3σ"
    - "Rule 2: 9+ points on same side"
    - "Rule 3: 6+ increasing points"
    - "Rule 4: 14+ alternating points"
    - etc.
  - control_chart_data: dict          # For visualization
  - recommendations: list[str]
```

**Example Usage**:
```python
# Monitor resident workload over 12 weeks
weekly = [55, 58, 60, 62, 61, 65, 70, 75, 78, 82, 85, 88]
spc = await run_spc_analysis_tool(
    resident_id="550e8400-e29b-41d4-a716-446655440000",
    weekly_hours=weekly,
    target_hours=60.0
)

if spc.violations:
    print(f"SPC Violations detected:")
    for violation in spc.violations:
        print(f"  - {violation}")
```

---

#### 10. `assess_schedule_fatigue_risk`

**Purpose**: Evaluate proposed schedule for fatigue impact

**Location**: `/scheduler_mcp/frms_integration.py`

**Parameters**:
```python
async def assess_schedule_fatigue_risk(
    resident_id: str,
    proposed_shifts: list[dict],      # List of shift data
) -> ScheduleFatigueRiskResponse
```

**Example Usage**:
```python
proposed = [
    {"date": "2025-01-06", "shift_type": "inpatient", "hours": 12},
    {"date": "2025-01-07", "shift_type": "clinic", "hours": 8},
    {"date": "2025-01-08", "shift_type": "call_night", "hours": 16},
]

risk = await assess_schedule_fatigue_risk(
    resident_id="550e8400-e29b-41d4-a716-446655440000",
    proposed_shifts=proposed
)

if risk.fatigue_level == "red":
    print(f"ALERT: Proposed schedule will cause {risk.fatigue_level} fatigue")
```

---

### Faculty-Specific Tools

#### 11. `analyze_hub_centrality`

**Purpose**: Identify faculty single points of failure via network analysis

**Location**: `/scheduler_mcp/resilience_integration.py`

**Parameters**:
```python
async def analyze_hub_centrality() -> HubAnalysisResponse
```

**Returns**:
```python
HubAnalysisResponse:
  - hub_faculty: list[FacultyHubInfo]
    - faculty_id: str
    - faculty_name: str (anonymized)
    - centrality_score: float         # Network importance (0-1)
    - blocks_critical: int            # Blocks they're critical for
    - supervision_coverage: float     # % of residents they supervise
    - replacement_difficulty: int     # Difficulty if removed (1-10)
  - total_faculty_analyzed: int
  - critical_faculty_count: int       # Centrality > 0.7
  - hub_factor: float                 # System-wide concentration risk
  - recommendations: list[str]
```

**Example Usage**:
```python
# Identify faculty bottlenecks
hubs = await analyze_hub_centrality()

print(f"Critical hub faculty: {hubs.critical_faculty_count}")
for faculty in hubs.hub_faculty:
    if faculty.centrality_score > 0.7:
        print(f"  - {faculty.faculty_name}: centrality {faculty.centrality_score:.2f}")
        print(f"    Blocks: {faculty.blocks_critical}, Difficulty: {faculty.replacement_difficulty}/10")
```

---

#### 12. `calculate_shapley_values`

**Purpose**: Determine fair workload contribution using cooperative game theory

**Location**: `/scheduler_mcp/server.py` (line 1659)

**Parameters**:
```python
async def calculate_shapley_values(
    faculty_ids: list[str]  # Faculty member UUIDs
) -> dict[str, Any]
```

**Returns**:
```python
{
  "faculty_count": int,
  "shapley_values": {
    "faculty-id-1": {
      "shapley_value": float,         # Fair contribution (0-1)
      "equity_ratio": float,          # Expected vs actual
      "contribution_percentile": int  # Percentile among peers
    },
    ...
  },
  "equity_metrics": {
    "gini_coefficient": float,        # Inequality (0=equal, 1=concentrated)
    "variance": float,                # Workload spread
    "fairness_index": float           # Overall equity (0-1)
  }
}
```

**Example Usage**:
```python
faculty_ids = [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002",
]

shapley = await calculate_shapley_values(faculty_ids)

for fid, metrics in shapley["shapley_values"].items():
    print(f"{fid}: Shapley={metrics['shapley_value']:.3f}, Equity Ratio={metrics['equity_ratio']:.2f}")

print(f"Gini Coefficient: {shapley['equity_metrics']['gini_coefficient']:.3f}")
```

---

### Staff & General Personnel Tools

#### 13. `run_contingency_analysis_tool`

**Purpose**: Simulate personnel absence scenarios (faculty, resident, mass absence)

**Location**: `/scheduler_mcp/server.py` (line 644)

**Parameters**:
```python
async def run_contingency_analysis_tool(
    scenario: str,                    # faculty_absence, resident_absence, emergency_coverage, mass_absence
    affected_person_ids: list[str],   # UUIDs of affected personnel
    start_date: str,                  # YYYY-MM-DD
    end_date: str,                    # YYYY-MM-DD
    auto_resolve: bool = False        # Auto-apply recommendations?
) -> ContingencyAnalysisResult
```

**Returns**:
```python
ContingencyAnalysisResult:
  - scenario: str
  - affected_count: int               # Personnel affected
  - start_date: str
  - end_date: str
  - impact_analysis: {
      "affected_blocks": int,
      "affected_residents": int,
      "coverage_gap": float (0-1),    # Fraction of assignments impacted
      "critical_gaps": list[str]
    }
  - resolution_strategies: list[{
      "strategy": str,
      "description": str,
      "affected_people": list[str],   # Personnel involved in fix
      "implementation_effort": str    # low, medium, high
    }],
  - recommendations: list[str]
```

**Scenario Types**:
- `faculty_absence`: One faculty member unavailable
- `resident_absence`: One resident unavailable
- `mass_absence`: Multiple personnel unavailable (flu, emergency)
- `emergency_coverage`: Unexpected coverage demand

**Example Usage**:
```python
# Analyze impact of faculty absence
analysis = await run_contingency_analysis_tool(
    scenario="faculty_absence",
    affected_person_ids=["550e8400-e29b-41d4-a716-446655440000"],
    start_date="2025-01-15",
    end_date="2025-01-17"
)

print(f"Coverage gap: {analysis.impact_analysis['coverage_gap']:.1%}")
print(f"Critical gaps: {analysis.impact_analysis['critical_gaps']}")
for strategy in analysis.resolution_strategies:
    print(f"  - {strategy['strategy']}: {strategy['description']}")
```

---

#### 14. `get_behavioral_patterns`

**Purpose**: Analyze preference trails left by personnel making schedule decisions

**Location**: `/scheduler_mcp/resilience_integration.py`

**Parameters**:
```python
async def get_behavioral_patterns(
    include_suggestions: bool = False
) -> BehavioralPatternsResponse
```

**Returns**:
```python
BehavioralPatternsResponse:
  - patterns: list[dict]              # Behavioral trends
    - pattern_type: str               # e.g., "faculty_clustering", "resident_avoidance"
    - frequency: int                  # How often observed
    - affected_personnel: list[str]   # Personnel IDs involved
    - impact: str                     # "neutral", "positive", "negative"
  - faculty_suggestions: list[dict]   # If include_suggestions=True
    - faculty_id: str
    - patterns_observed: int
    - suggested_assignments: list[str]
  - contributing_faculty: int         # Faculty with patterns
  - recommendations: list[str]
```

**Example Usage**:
```python
patterns = await get_behavioral_patterns(include_suggestions=True)

for pattern in patterns.patterns:
    print(f"Pattern: {pattern['pattern_type']}")
    print(f"  Frequency: {pattern['frequency']}")
    print(f"  Impact: {pattern['impact']}")
```

---

### Advanced Resilience Tools

#### 15. `get_unified_critical_index`

**Purpose**: Combined resilience metric for faculty (centrality + N-1 vulnerability + burnout risk)

**Location**: `/scheduler_mcp/composite_resilience_tools.py`

**Parameters**:
```python
async def get_unified_critical_index(
    include_details: bool = False,    # Include individual faculty assessments?
    top_n: int = 20                   # Top N critical faculty to return
) -> UnifiedCriticalIndexResponse
```

**Returns**:
```python
UnifiedCriticalIndexResponse:
  - universal_critical_count: int     # Faculty with critical index > threshold
  - average_critical_index: float     # System-wide metric
  - critical_vulnerability_spots: int # N-1 single points of failure
  - super_spreader_count: int         # Burnout contagion risk
  - top_critical_faculty: list[FacultyUnifiedIndex]
    - faculty_id: str
    - faculty_name: str (anonymized)
    - unified_critical_index: float (0-1)
    - risk_pattern: str               # central_hub, super_spreader, burned_out
    - recommendation: str
  - recommendations: list[str]
```

**Risk Patterns**:
- `central_hub`: High network centrality (N-1 vulnerable)
- `super_spreader`: High burnout contagion risk
- `burned_out`: High personal fatigue risk
- `cascading_failure`: Multiple risk factors
- `recovery_blocked`: Cannot recover if pulled

**Example Usage**:
```python
critical = await get_unified_critical_index(include_details=True, top_n=10)

print(f"Critical faculty: {critical.universal_critical_count}")
print(f"Super-spreaders: {critical.super_spreader_count}")
print(f"N-1 vulnerabilities: {critical.critical_vulnerability_spots}")

for faculty in critical.top_critical_faculty:
    print(f"\n{faculty.faculty_name}")
    print(f"  Risk Type: {faculty.risk_pattern}")
    print(f"  Index: {faculty.unified_critical_index:.3f}")
    print(f"  Action: {faculty.recommendation}")
```

---

#### 16. `check_utilization_threshold`

**Purpose**: Check 80% utilization threshold (queuing theory)

**Location**: `/scheduler_mcp/server.py` (line 879)

**Parameters**:
```python
async def check_utilization_threshold(
    available_faculty: int,
    required_blocks: int,
    blocks_per_faculty_per_day: float = 2.0,
    days_in_period: int = 1,
) -> UtilizationResponse
```

**Returns**:
```python
UtilizationResponse:
  - utilization_percent: float        # % capacity used
  - threshold_percent: float = 80.0   # Critical threshold
  - is_critical: bool                 # Above threshold?
  - safety_margin: float              # % remaining capacity
  - status: str                       # "GREEN", "YELLOW", "RED"
  - wait_time_prediction: float       # Expected wait time (minutes)
  - cascade_risk: str                 # none, low, medium, high, critical
  - recommendations: list[str]
```

**Status Levels**:
- **GREEN** (0-70%): Safe operations
- **YELLOW** (70-80%): Monitor closely
- **RED** (>80%): Cascade failure risk

**Example Usage**:
```python
utilization = await check_utilization_threshold(
    available_faculty=12,
    required_blocks=200,  # Morning + afternoon blocks per day
    blocks_per_faculty_per_day=2.0,
    days_in_period=30
)

print(f"Utilization: {utilization.utilization_percent:.1%}")
print(f"Status: {utilization.status}")
if utilization.is_critical:
    print(f"ALERT: System at cascade failure risk")
    print(f"Cascade risk level: {utilization.cascade_risk}")
```

---

## Personnel Query Parameters

### Standard Parameter Patterns

#### Date Range Parameters
```python
start_date: str | date          # YYYY-MM-DD or date object
end_date: str | date            # YYYY-MM-DD or date object
```

#### Person Identifier Parameters
```python
person_id: str                  # UUID or string ID
person_ids: list[str]           # Multiple UUIDs
resident_id: str                # UUID of resident
faculty_id: str                 # UUID of faculty

# Role filtering
person_role: str                # "resident", "faculty", "staff"
pgy_level: int                  # 1, 2, or 3 for residents only
```

#### Filtering & Pagination
```python
limit: int = 100                # Max results to return
offset: int = 0                 # Pagination offset
include_details: bool = False   # Detailed vs summary results
filter_by_type: str             # "all", "active", "inactive"
```

#### Numeric Bounds
```python
max_candidates: int = 10        # Max swap matches, centrality results, etc
top_n: int = 20                 # Top N rankings
threshold: float = 0.7          # Centrality, risk, etc cutoff
```

---

## Personnel Role Concepts

### Core Roles

**ROLE_CONTEXT** (from `domain_context.py`):

```python
"pgy_levels": {
    "PGY-1": "Post-Graduate Year 1 (first-year resident/intern)",
    "PGY-2": "Post-Graduate Year 2 (second-year resident)",
    "PGY-3": "Post-Graduate Year 3 (third-year resident)",
}

"staff_roles": {
    "Clinical Staff": "Support clinical operations",
    "RN": "Registered Nurse",
    "LPN": "Licensed Practical Nurse",
    "MSA": "Medical Support Assistant",
}

"faculty_roles": {
    "Attending": "Senior faculty physician",
    "Preceptor": "Teaching faculty",
    "Clinical Educator": "Faculty focused on education",
}
```

### Person Model Attributes
```python
Person:
  - id: str (UUID)
  - name: str                     # Full name (PII)
  - type: str                     # "resident", "faculty", "staff"
  - is_resident: bool
  - is_faculty: bool
  - pgy_level: int | None         # Only for residents
  - specialty: str                # e.g., "Family Medicine"
  - is_active: bool               # Active in program?
  - created_at: datetime
  - updated_at: datetime
```

---

## Query Patterns & Examples

### Pattern 1: Get All Personnel Data

```python
# High-level: Get schedule status with all personnel
status = await get_schedule_status(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31)
)

# Analyze assignments
for assignment in status.assignments:
    print(f"{assignment.person_role}: {assignment.rotation}")

# Get complete person records
client = SchedulerAPIClient()
async with client:
    people = await client.get_people(limit=100)
```

---

### Pattern 2: Resident Fatigue Monitoring

```python
# Scan all residents
team_scan = await scan_team_fatigue()

# Get critical residents
critical = team_scan.critical_residents  # RED + BLACK

# Detailed assessment for each
for resident in critical:
    frms = await run_frms_assessment(resident.resident_id)
    print(f"{resident.name}: {frms.hazard_level}")
    print(f"  Sleep debt: {frms.sleep_debt:.1f}h")
    print(f"  Recommendations: {frms.recommendations}")
```

---

### Pattern 3: Faculty Risk Analysis

```python
# Get unified critical index for faculty
critical_index = await get_unified_critical_index(
    include_details=True,
    top_n=5
)

# Analyze N-1 vulnerabilities
for faculty in critical_index.top_critical_faculty:
    if faculty.risk_pattern == "central_hub":
        print(f"ALERT: {faculty.faculty_name} is critical hub")
        print(f"  Actions: {faculty.recommendation}")

# Check hub centrality in detail
hubs = await analyze_hub_centrality()
```

---

### Pattern 4: Contingency Planning

```python
# Simulate faculty absence
analysis = await run_contingency_analysis_tool(
    scenario="faculty_absence",
    affected_person_ids=["550e8400-e29b-41d4-a716-446655440000"],
    start_date="2025-01-15",
    end_date="2025-01-17"
)

# Review impact
print(f"Coverage gap: {analysis.impact_analysis['coverage_gap']:.1%}")

# Consider resolution strategies
for strategy in analysis.resolution_strategies:
    print(f"\nStrategy: {strategy['strategy']}")
    print(f"  Impact: {strategy['description']}")
    print(f"  Affected: {strategy['affected_people']}")
    print(f"  Effort: {strategy['implementation_effort']}")
```

---

### Pattern 5: ACGME Compliance Checking

```python
# Get compliance summary
summary = await get_compliance_summary(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31)
)

# Check metrics
print(f"Compliance rate: {summary.metrics.overall_compliance_rate:.1%}")
print(f"Residents affected: {summary.metrics.residents_affected}")

# Review violations by type
for violation in summary.violations:
    if violation.violation_type == "work_hour_limit":
        print(f"{violation.person_role}: Exceeded 80-hour limit")
        hours = violation.details.get("average_weekly_hours", 0)
        print(f"  Average: {hours:.1f}/week (limit: 80)")

# Act on recommendations
for rec in summary.recommendations:
    print(f"Action: {rec}")
```

---

### Pattern 6: Workload Equity Analysis

```python
# Calculate fair contribution via Shapley values
faculty_ids = ["fac-1", "fac-2", "fac-3"]
shapley = await calculate_shapley_values(faculty_ids)

# Check for inequity
gini = shapley["equity_metrics"]["gini_coefficient"]
if gini > 0.3:  # Moderate inequality threshold
    print(f"WARNING: Unequal distribution (Gini={gini:.3f})")

# Detail per-faculty contribution
for fid, metrics in shapley["shapley_values"].items():
    ratio = metrics["equity_ratio"]
    if ratio > 1.2:  # Overloaded
        print(f"{fid}: OVERLOADED (expected vs actual: {ratio:.2f}x)")
```

---

## Integration Guide

### FastMCP Server Registration

All tools are auto-registered via `@mcp.tool()` decorator:

```python
# From server.py

@mcp.tool()
async def detect_burnout_precursors_tool(resident_id: str, signal_type: str, ...):
    """Tool docstring becomes help text"""
    request = PrecursorDetectionRequest(...)
    return await detect_burnout_precursors(request)

# FastMCP automatically exposes as:
# - Claude can call via "detect_burnout_precursors_tool"
# - Tool receives parameters from Claude
# - Returns response matching return type annotation
```

### Using with SchedulerAPIClient

```python
# Setup
client = SchedulerAPIClient(config=APIConfig(
    base_url="http://localhost:8000",
    username="mcp_user",
    password="secure_password"
))

async with client:
    # Query personnel
    people = await client.get_people(limit=50)

    # Get schedule
    assignments = await client.get_assignments(
        start_date="2025-01-01",
        end_date="2025-01-31"
    )

    # Run analysis
    analysis = await client.run_contingency_analysis(
        scenario="faculty_absence",
        affected_ids=["550e8400-e29b-41d4-a716-446655440000"],
        start_date="2025-01-15",
        end_date="2025-01-17"
    )
```

### Direct Database Access (Fallback)

```python
# If API unavailable, tools use direct DB access
from app.db.session import SessionLocal
from app.models.person import Person
from sqlalchemy import select

db = SessionLocal()
try:
    # Query residents
    residents = db.query(Person).filter(
        Person.type == "resident",
        Person.is_active == True
    ).all()

    # Filter by PGY level
    pgy1 = [r for r in residents if r.pgy_level == 1]
finally:
    db.close()
```

---

## Undocumented Filters & Features

### Hidden Query Parameters

#### 1. Role-Based Anonymization

Tools automatically anonymize person identifiers:
```python
# Internal: "Dr. John Smith" with ID "550e8400..."
# Returned: "Faculty-001" or "PGY-1-003"

_anonymize_id("550e8400-e29b-41d4-a716-446655440000", "Faculty")
# Returns: "Faculty-001" (consistent, deterministic)
```

**Usage**: All external APIs return anonymized IDs by default.

---

#### 2. Time-Series Window Defaults

Many tools have hidden defaults for time windows:
```python
# STA/LTA windows (seismic precursor detection)
short_window: int = 5    # Default: 5 days
long_window: int = 30    # Default: 30 days

# If not provided, computes over available data
# If data < 30 days, uses all available points
```

---

#### 3. Cascading Contingency Analysis

`run_contingency_analysis_tool` with `auto_resolve=True`:
```python
# Not exposed in signature, but available internally
# Automatically applies first resolution strategy if enabled
# Useful for emergency scenarios

analysis = await run_contingency_analysis_tool(
    scenario="mass_absence",
    affected_person_ids=["id1", "id2", "id3"],
    start_date="2025-01-15",
    end_date="2025-01-20",
    auto_resolve=True  # Applies recommendations automatically
)
```

---

#### 4. Database Fallback Behavior

All tools have dual-mode operation:
```
┌─────────────────────────────────┐
│ MCP Tool Request                 │
├─────────────────────────────────┤
│ Primary: Via SchedulerAPIClient  │
│   (HTTP to FastAPI backend)      │
├─────────────────────────────────┤
│ Fallback: Direct DB access       │
│   (if API unavailable)           │
├─────────────────────────────────┤
│ Last Resort: Synthetic data      │
│   (for testing, demo)            │
└─────────────────────────────────┘
```

---

#### 5. Caching Behavior

Some tools cache results:
```python
# get_schedule_status caches for 5 minutes
# Reduces repeated database queries

# Clear cache by using different date ranges
status1 = await get_schedule_status(start_date=date1, end_date=date2)
# Uses cache

status2 = await get_schedule_status(start_date=date1, end_date=date3)
# Cache miss (different end_date)
```

---

#### 6. Silent Fallback Modes

Tools gracefully degrade when data unavailable:
```python
# If resident_id invalid/not found
run_frms_assessment("invalid-uuid") returns {
    "resident_id": "invalid-uuid",
    "resident_name": "Resident-xxxx",  # Synthetic
    "hazard_level": "GREEN",            # Default
    "sleep_debt": 0.0,
    "recommendations": ["Unable to assess - using defaults"]
}

# Uses fallback hazard calculation rather than error
```

---

#### 7. Undocumented Metric Calculations

Internal algorithms not exposed in docs:

**Centrality Score** (`analyze_hub_centrality`):
```python
centrality = (
    (blocks_critical / total_blocks) * 0.4 +
    (residents_supervised / total_residents) * 0.3 +
    (swing_shifts / total_shifts) * 0.3
)

# 0.0 = not critical
# 0.5 = moderately critical
# 0.7+ = critical hub (alert threshold)
```

**Fire Danger Index** (`calculate_fire_danger_index_tool`):
```python
# Adapted from Canadian Fire Weather Index
# Combines:
# - Fine Fuel Moisture Code (fatigue)
# - Duff Moisture Code (chronic stress)
# - Drought Code (long-term depletion)
# - Initial Spread Index (contagion)
# - Build Up Index (accumulation)
# - Fire Weather Index (combined)

# Result: 0-100 scale (like Richter scale)
```

---

### Stealth Filters

#### Filter by Supervision Type
```python
# Internal: assignment.role field
# "supervising" vs "supervised"

# Not exposed in API, but searchable:
assignments = [a for a in status.assignments if a.is_supervising]
# Returns faculty in supervising role
```

---

#### Filter by Rotation Type
```python
# Internal rotation categories:
rotation_types = {
    "inpatient": Family Medicine inpatient rotation,
    "clinic": Outpatient clinic,
    "call": Overnight call coverage,
    "fmit": Family Medicine Inpatient Team (week-long block),
    "conference": Educational conference/didactic,
    "admin": Administrative/teaching,
}

# Filter by searching assignment.rotation field
clinic_assignments = [a for a in status.assignments if "clinic" in a.rotation.lower()]
```

---

#### Filter by Compliance Violation Type
```python
violation_types = {
    "work_hour_limit": 80-hour rule breach,
    "consecutive_duty": 1-in-7 rule breach,
    "rest_period": Inadequate rest days,
    "supervision_ratio": Faculty-to-resident ratio breach,
}

# Filter by severity
critical = [v for v in summary.violations if v.severity == "critical"]
warnings = [v for v in summary.violations if v.severity == "warning"]
```

---

## Appendix: Tool Inventory Table

| Tool | Primary Use | Parameter | Returns |
|------|-------------|-----------|---------|
| `get_schedule_status` | Schedule snapshot | date range | ScheduleStatusResource |
| `get_compliance_summary` | ACGME compliance | date range | ComplianceSummaryResource |
| `run_frms_assessment` | Resident fatigue | resident_id | FRMSAssessmentResponse |
| `scan_team_fatigue` | All residents fatigue | none | TeamFatigueScanResponse |
| `detect_burnout_precursors_tool` | Early warning signals | resident_id, signal_type | PrecursorDetectionResponse |
| `calculate_fire_danger_index_tool` | Burnout risk (CFFDRS) | resident_id, metrics | FireDangerResponse |
| `predict_burnout_magnitude_tool` | Multi-signal prediction | resident_id, signals | MultiSignalMagnitudeResponse |
| `run_spc_analysis_tool` | Workload monitoring (SPC) | resident_id, weekly_hours | SPCAnalysisResponse |
| `analyze_hub_centrality` | Faculty single points of failure | none | HubAnalysisResponse |
| `calculate_shapley_values` | Workload equity | faculty_ids | Dict with Shapley values |
| `run_contingency_analysis_tool` | Absence scenarios | scenario, person_ids, dates | ContingencyAnalysisResult |
| `get_behavioral_patterns` | Personnel preference trails | include_suggestions | BehavioralPatternsResponse |
| `get_unified_critical_index` | Combined faculty risk | include_details, top_n | UnifiedCriticalIndexResponse |
| `check_utilization_threshold` | 80% queuing theory check | faculty_count, block_count | UtilizationResponse |
| `assess_schedule_fatigue_risk` | Proposed schedule impact | resident_id, shifts | ScheduleFatigueRiskResponse |
| `get_people` (API client) | All personnel | limit | Dict with people list |

---

## Summary

**SEARCH_PARTY Operation Findings:**

- **PERCEPTION**: 15+ personnel query tools across 4 integration layers
- **INVESTIGATION**: Full parameter documentation with examples provided
- **ARCANA**: 3 PGY levels, 5+ role types, deep domain integration
- **HISTORY**: Tools evolved from basic queries to cross-disciplinary analytics
- **INSIGHT**: Burnout detection via seismology, fire weather, game theory
- **RELIGION**: Yes - all documented, plus 7 stealth filters discovered
- **NATURE**: Highly flexible - date ranges, IDs, metrics, thresholds
- **MEDICINE**: FRMS, ACGME compliance, supervision ratios fully integrated
- **SURVIVAL**: Emergency contingency and N-1/N-2 resilience tools present
- **STEALTH**: Anonymization, fallback modes, cascading analysis, caching

---

**Document Generated**: Session 8, SEARCH_PARTY Operation
**Coverage**: Personnel domain complete
**Next Phase**: Integration examples and workflow optimization

