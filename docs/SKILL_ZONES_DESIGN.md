# Skill-Based Zone Self-Sufficiency Design

## Problem Statement

The current `is_self_sufficient()` implementation only checks headcount, creating a critical blind spot in zone health assessment. This leads to what we call the **"Warm Body Fallacy"**.

### The Warm Body Fallacy: A Concrete Example

Consider Zone A (OB/GYN coverage):
- **Current Assessment**: Zone A has 3 faculty assigned (minimum requirement: 2)
- **System Status**: GREEN (self-sufficient)
- **Reality**: None of the 3 faculty are credentialed for OB supervision
- **Actual Status**: Zone A cannot function for OB cases

**The Risk**: The system reports healthy status while lacking critical capabilities. Headcount alone does not guarantee operational capability.

## Current Implementation Analysis

### Existing Code

The current self-sufficiency check in `blast_radius.py` (lines 201-203):

```python
def is_self_sufficient(self) -> bool:
    return self.get_total_available() >= self.minimum_coverage
```

This implementation only verifies that the total number of available faculty meets or exceeds the minimum coverage requirement. It makes no assessment of whether those faculty members can actually perform the required functions.

### What's Currently Tracked

`ZoneFacultyAssignment` data class tracks:
- `faculty_id` - Unique identifier
- `name` - Faculty member's name
- `role` - Assignment role (primary, backup, etc.)
- `available` - Availability status

### What's Missing

- **Skill/credential information** - No tracking of what each faculty member can actually do
- **Critical skill requirements** - No definition of what skills a zone needs to operate
- **Skill gap analysis** - No way to identify when required capabilities are missing

## Related Existing Code

The system already has components that track skill-related information, but they're not integrated with zone self-sufficiency:

### Hub Analysis Module

**File**: `hub_analysis.py`

1. **Tracks `unique_services` per faculty**
   - Already maintains information about what services/procedures each faculty can provide
   - This data exists but isn't used in zone health calculations

2. **Has `generate_cross_training_recommendations()`**
   - Identifies single points of failure (skills provided by only one person)
   - Suggests cross-training priorities
   - Currently operates independently of zone status

**The Gap**: These components exist in isolation. We need to integrate skill tracking with zone self-sufficiency to create a comprehensive health assessment.

## Proposed Solution

### 5a. Data Model Changes

Enhance existing data models to track skills and requirements:

```python
@dataclass
class SchedulingZone:
    # ... existing fields ...

    # NEW: Critical skills required for zone operation
    critical_skills: dict[str, int] = field(default_factory=dict)
    # Key: skill identifier (e.g., "ob_supervision")
    # Value: minimum number of providers required
    # Example: {"ob_supervision": 1, "icu_procedures": 2, "trauma": 1}

@dataclass
class ZoneFacultyAssignment:
    # ... existing fields ...

    # NEW: Skills this faculty member can provide
    skills: list[str] = field(default_factory=list)
    # List of skill identifiers this person is credentialed/qualified to perform
    # Example: ["ob_supervision", "clinic_supervision", "code_team_leader"]
```

**Design Rationale**:
- Use `dict[str, int]` for critical_skills to capture both the skill name and minimum count
- Use `list[str]` for faculty skills to support multiple qualifications per person
- Default to empty collections for backward compatibility

### 5b. Enhanced Self-Sufficiency Check

Replace the simple headcount check with a comprehensive capability assessment:

```python
def is_self_sufficient(self) -> bool:
    """Check if zone can operate without borrowing resources.

    A zone is self-sufficient when:
    1. Total available headcount meets minimum coverage
    2. All critical skills have sufficient qualified providers

    Returns:
        True if zone can operate independently, False otherwise
    """
    # Check total headcount (existing logic)
    if self.get_total_available() < self.minimum_coverage:
        return False

    # Check critical skills coverage (NEW)
    available_faculty = self._get_all_available_faculty()
    for skill, min_required in self.critical_skills.items():
        providers = sum(1 for f in available_faculty if skill in f.skills)
        if providers < min_required:
            return False

    return True

def _get_all_available_faculty(self) -> list[ZoneFacultyAssignment]:
    """Get all available faculty across all roles.

    Returns:
        List of available faculty assignments
    """
    available = []
    for assignments in [self.primary, self.backup, self.on_call]:
        available.extend(f for f in assignments if f.available)
    return available
```

### 5c. Enhanced Status Calculation

Integrate skill gap detection into zone status determination:

```python
def calculate_status(self) -> ZoneStatus:
    """Determine zone operational status based on capacity and skills.

    Status levels:
    - GREEN: Meets headcount AND all critical skills covered
    - YELLOW: Meets headcount BUT some skill gaps exist
    - ORANGE: Below headcount OR critical skill completely missing
    - RED: Severe headcount deficit AND/OR multiple critical skill gaps

    Returns:
        Current zone status
    """
    # ... existing capacity checks ...

    # Check skill gaps (NEW)
    skill_gaps = self._check_skill_gaps()

    if not skill_gaps:
        # No skill gaps, use traditional headcount-based status
        return self._calculate_headcount_status()

    # Analyze skill gap severity
    complete_gaps = [gap for gap in skill_gaps
                     if gap["available"] == 0]
    partial_gaps = [gap for gap in skill_gaps
                    if 0 < gap["available"] < gap["required"]]

    if complete_gaps:
        # Complete absence of critical skill = RED
        return ZoneStatus.RED
    elif len(partial_gaps) >= 2:
        # Multiple partial gaps = ORANGE
        return ZoneStatus.ORANGE
    elif partial_gaps:
        # Single partial gap = YELLOW
        return ZoneStatus.YELLOW
    else:
        return ZoneStatus.GREEN

def _check_skill_gaps(self) -> list[dict]:
    """Identify gaps between required and available skills.

    Returns:
        List of skill gap dictionaries with keys:
        - skill: skill identifier
        - required: minimum providers needed
        - available: current providers available
        - missing: deficit (required - available)
    """
    available_faculty = self._get_all_available_faculty()
    gaps = []

    for skill, required in self.critical_skills.items():
        available = sum(1 for f in available_faculty if skill in f.skills)
        if available < required:
            gaps.append({
                "skill": skill,
                "required": required,
                "available": available,
                "missing": required - available
            })

    return gaps
```

## Integration with Hub Analysis

The `HubAnalyzer` already identifies single points of failure and cross-training opportunities. We can leverage this for skill-based zone management:

### Workflow

1. **Identify Critical Skills**
   - Use `HubAnalyzer.generate_cross_training_recommendations()` to find single-provider skills
   - Any skill provided by only one person in a zone is a critical risk
   - These skills should be added to zone `critical_skills` configuration

2. **Priority Calculation**
   - Cross-training priority = impact on zone self-sufficiency
   - Highest priority: Skills that would cause immediate zone failure if lost
   - Medium priority: Skills that would downgrade zone status
   - Low priority: Skills with adequate backup coverage

3. **Feedback Loop**
   - Zone skill gaps inform cross-training recommendations
   - Cross-training completion updates faculty skill lists
   - Zone status automatically improves as skills are developed

### Integration Points

```python
# In hub_analysis.py
def generate_zone_skill_recommendations(
    self,
    zone: SchedulingZone
) -> list[CrossTrainingRecommendation]:
    """Generate cross-training recommendations for a specific zone.

    Prioritizes skills that:
    1. Are marked as critical for the zone
    2. Have insufficient providers
    3. Would improve zone self-sufficiency

    Args:
        zone: The scheduling zone to analyze

    Returns:
        Prioritized list of cross-training recommendations
    """
    skill_gaps = zone._check_skill_gaps()
    recommendations = []

    for gap in skill_gaps:
        # Find potential trainees (faculty in zone without this skill)
        available_faculty = zone._get_all_available_faculty()
        candidates = [f for f in available_faculty
                     if gap["skill"] not in f.skills]

        # Find qualified trainers
        trainers = [f for f in available_faculty
                   if gap["skill"] in f.skills]

        recommendations.append(
            CrossTrainingRecommendation(
                skill=gap["skill"],
                priority="HIGH" if gap["available"] == 0 else "MEDIUM",
                current_providers=trainers,
                suggested_trainees=candidates[:2],  # Top 2 candidates
                impact=f"Would improve {zone.name} from {gap['available']} "
                       f"to {gap['available'] + 2} providers"
            )
        )

    return recommendations
```

## Zone Health Report Enhancement

Expand health reporting to include skill coverage metrics:

```python
@dataclass
class ZoneHealthReport:
    # ... existing fields ...
    zone_name: str
    status: ZoneStatus
    total_available: int
    minimum_coverage: int
    capacity_rate: float

    # NEW FIELDS
    skill_gaps: list[dict]
    # List of skill deficits, format:
    # [{"skill": "ob_supervision", "required": 1, "available": 0, "missing": 1}]

    skill_coverage_rate: float
    # Percentage of critical skills adequately covered (0.0 - 1.0)
    # Formula: (skills_with_adequate_coverage / total_critical_skills)

    skill_details: dict[str, dict]
    # Detailed skill coverage info:
    # {
    #     "ob_supervision": {
    #         "required": 1,
    #         "available": 0,
    #         "providers": [],
    #         "status": "CRITICAL"
    #     }
    # }

def generate_health_report(self) -> ZoneHealthReport:
    """Generate comprehensive health report including skill coverage."""
    skill_gaps = self._check_skill_gaps()
    skill_details = self._get_skill_details()

    # Calculate skill coverage rate
    total_skills = len(self.critical_skills)
    covered_skills = total_skills - len(skill_gaps)
    skill_coverage_rate = covered_skills / total_skills if total_skills > 0 else 1.0

    return ZoneHealthReport(
        zone_name=self.name,
        status=self.calculate_status(),
        total_available=self.get_total_available(),
        minimum_coverage=self.minimum_coverage,
        capacity_rate=self.get_total_available() / self.minimum_coverage,
        skill_gaps=skill_gaps,
        skill_coverage_rate=skill_coverage_rate,
        skill_details=skill_details
    )

def _get_skill_details(self) -> dict[str, dict]:
    """Get detailed information about each critical skill."""
    available_faculty = self._get_all_available_faculty()
    details = {}

    for skill, required in self.critical_skills.items():
        providers = [f for f in available_faculty if skill in f.skills]
        available = len(providers)

        if available == 0:
            status = "CRITICAL"
        elif available < required:
            status = "INSUFFICIENT"
        elif available == required:
            status = "ADEQUATE"
        else:
            status = "GOOD"

        details[skill] = {
            "required": required,
            "available": available,
            "providers": [f.name for f in providers],
            "status": status
        }

    return details
```

## Migration Plan

### Phase 1: Data Model Enhancement (Backward Compatible)
**Timeline**: Sprint 1

**Actions**:
- Add `critical_skills` field to `SchedulingZone` with `field(default_factory=dict)`
- Add `skills` field to `ZoneFacultyAssignment` with `field(default_factory=list)`
- Add `_check_skill_gaps()` helper method
- Add `_get_skill_details()` helper method
- **No behavioral changes** - new fields default to empty, old logic still applies

**Validation**:
- All existing tests pass
- New zones created with empty skill requirements
- Existing zones load without errors

### Phase 2: Configuration Population
**Timeline**: Sprint 2

**Actions**:
- Create admin UI for defining zone critical skills
- Develop skill catalog/taxonomy (standardized skill names)
- Populate `critical_skills` for existing zones via admin interface
- Document skill definitions and requirements

**Validation**:
- Admins can add/edit/remove critical skills per zone
- Skill requirements persist correctly
- Skill catalog is comprehensive and unambiguous

### Phase 3: Faculty Skill Tracking
**Timeline**: Sprint 3

**Actions**:
- Create admin UI for managing faculty skills
- Import existing credential/certification data
- Populate `skills` for existing faculty
- Implement skill verification workflow

**Validation**:
- Faculty skills can be added/edited/removed
- Skills align with defined catalog
- Skill data persists correctly

### Phase 4: Skill-Based Self-Sufficiency
**Timeline**: Sprint 4

**Actions**:
- Enable skill checks in `is_self_sufficient()`
- Update `calculate_status()` to use skill gaps
- Deploy enhanced `ZoneHealthReport`
- Update dashboards to show skill coverage

**Validation**:
- Zones with skill gaps show correct status
- Health reports display skill details
- False positives (Warm Body Fallacy cases) eliminated
- Cross-training recommendations align with zone needs

### Rollback Strategy

Each phase can be rolled back independently:
- **Phase 4**: Disable skill checks via feature flag
- **Phase 3**: Clear faculty skills (fall back to headcount only)
- **Phase 2**: Clear zone critical skills (fall back to headcount only)
- **Phase 1**: Not needed (backward compatible)

## Configuration Examples

### Inpatient Zone
```python
critical_skills = {
    "icu_attending": 1,           # At least 1 ICU-qualified attending
    "procedure_supervision": 1,    # At least 1 procedure supervisor
    "code_team_leader": 1,         # At least 1 code team leader
}

# Example faculty in this zone:
faculty = [
    ZoneFacultyAssignment(
        faculty_id="F001",
        name="Dr. Smith",
        role="primary",
        available=True,
        skills=["icu_attending", "code_team_leader"]
    ),
    ZoneFacultyAssignment(
        faculty_id="F002",
        name="Dr. Jones",
        role="backup",
        available=True,
        skills=["procedure_supervision", "icu_attending"]
    )
]
# Status: GREEN (all skills covered)
```

### Outpatient Zone
```python
critical_skills = {
    "clinic_supervision": 2,      # At least 2 clinic supervisors
    "precepting": 2,              # At least 2 faculty who can precept
}

# Example scenario with skill gap:
faculty = [
    ZoneFacultyAssignment(
        faculty_id="F010",
        name="Dr. Wilson",
        role="primary",
        available=True,
        skills=["clinic_supervision", "precepting"]
    ),
    ZoneFacultyAssignment(
        faculty_id="F011",
        name="Dr. Taylor",
        role="primary",
        available=True,
        skills=["precepting"]  # Missing clinic_supervision
    )
]
# Status: ORANGE (headcount OK, but clinic_supervision gap)
```

### Education Zone
```python
critical_skills = {
    "simulation_instructor": 1,    # At least 1 sim instructor
    "didactics_faculty": 1,        # At least 1 didactics-qualified faculty
    "curriculum_development": 1,   # At least 1 curriculum developer
}

# High-functioning zone example:
faculty = [
    ZoneFacultyAssignment(
        faculty_id="F020",
        name="Dr. Martinez",
        role="primary",
        available=True,
        skills=["simulation_instructor", "didactics_faculty", "curriculum_development"]
    ),
    ZoneFacultyAssignment(
        faculty_id="F021",
        name="Dr. Brown",
        role="backup",
        available=True,
        skills=["simulation_instructor", "didactics_faculty"]
    )
]
# Status: GREEN (all skills well-covered)
```

### Emergency Department Zone
```python
critical_skills = {
    "trauma_team_leader": 1,       # At least 1 trauma leader
    "pediatric_resuscitation": 1,  # At least 1 PALS-qualified
    "ultrasound_supervision": 1,   # At least 1 ultrasound supervisor
    "toxicology_consult": 1,       # At least 1 tox specialist
}

# Demonstration of the "Warm Body Fallacy":
faculty = [
    ZoneFacultyAssignment(faculty_id="F030", name="Dr. Green",
                         role="primary", available=True,
                         skills=["pediatric_resuscitation"]),
    ZoneFacultyAssignment(faculty_id="F031", name="Dr. White",
                         role="primary", available=True,
                         skills=["ultrasound_supervision"]),
    ZoneFacultyAssignment(faculty_id="F032", name="Dr. Black",
                         role="backup", available=True,
                         skills=[])  # No critical skills
]
# OLD LOGIC: GREEN (3 faculty, minimum 2)
# NEW LOGIC: RED (missing trauma_team_leader and toxicology_consult)
```

## Testing Strategy

### Unit Tests: Skill-Based Self-Sufficiency

```python
def test_is_self_sufficient_with_skill_gaps():
    """Zone with adequate headcount but skill gaps is NOT self-sufficient."""
    zone = SchedulingZone(
        name="Test Zone",
        minimum_coverage=2,
        critical_skills={"ob_supervision": 1}
    )
    zone.primary = [
        ZoneFacultyAssignment(
            faculty_id="F1", name="Dr. A", role="primary",
            available=True, skills=[]  # No OB skill
        ),
        ZoneFacultyAssignment(
            faculty_id="F2", name="Dr. B", role="primary",
            available=True, skills=[]  # No OB skill
        )
    ]

    assert not zone.is_self_sufficient()

def test_is_self_sufficient_with_skills_covered():
    """Zone with adequate headcount and skills IS self-sufficient."""
    zone = SchedulingZone(
        name="Test Zone",
        minimum_coverage=2,
        critical_skills={"ob_supervision": 1}
    )
    zone.primary = [
        ZoneFacultyAssignment(
            faculty_id="F1", name="Dr. A", role="primary",
            available=True, skills=["ob_supervision"]
        ),
        ZoneFacultyAssignment(
            faculty_id="F2", name="Dr. B", role="primary",
            available=True, skills=[]
        )
    ]

    assert zone.is_self_sufficient()

def test_is_self_sufficient_insufficient_headcount():
    """Zone fails on headcount regardless of skills."""
    zone = SchedulingZone(
        name="Test Zone",
        minimum_coverage=2,
        critical_skills={"ob_supervision": 1}
    )
    zone.primary = [
        ZoneFacultyAssignment(
            faculty_id="F1", name="Dr. A", role="primary",
            available=True, skills=["ob_supervision"]
        )
    ]

    assert not zone.is_self_sufficient()
```

### Unit Tests: Skill-Based Status Calculation

```python
def test_calculate_status_complete_skill_gap():
    """Complete absence of critical skill yields RED status."""
    zone = SchedulingZone(
        name="Test Zone",
        minimum_coverage=2,
        critical_skills={"trauma": 1}
    )
    zone.primary = [
        ZoneFacultyAssignment(
            faculty_id="F1", name="Dr. A", role="primary",
            available=True, skills=[]
        ),
        ZoneFacultyAssignment(
            faculty_id="F2", name="Dr. B", role="primary",
            available=True, skills=[]
        )
    ]

    assert zone.calculate_status() == ZoneStatus.RED

def test_calculate_status_partial_skill_gap():
    """Partial skill coverage yields YELLOW or ORANGE."""
    zone = SchedulingZone(
        name="Test Zone",
        minimum_coverage=2,
        critical_skills={"icu": 2}  # Need 2, have 1
    )
    zone.primary = [
        ZoneFacultyAssignment(
            faculty_id="F1", name="Dr. A", role="primary",
            available=True, skills=["icu"]
        ),
        ZoneFacultyAssignment(
            faculty_id="F2", name="Dr. B", role="primary",
            available=True, skills=[]
        )
    ]

    assert zone.calculate_status() in [ZoneStatus.YELLOW, ZoneStatus.ORANGE]
```

### Integration Tests: Hub Analyzer

```python
def test_hub_analyzer_integration():
    """Hub analyzer recommendations align with zone skill gaps."""
    # Setup zone with skill gap
    zone = SchedulingZone(
        name="Test Zone",
        minimum_coverage=2,
        critical_skills={"ultrasound": 1}
    )
    zone.primary = [
        ZoneFacultyAssignment(
            faculty_id="F1", name="Dr. A", role="primary",
            available=True, skills=[]
        ),
        ZoneFacultyAssignment(
            faculty_id="F2", name="Dr. B", role="primary",
            available=True, skills=[]
        )
    ]

    # Generate recommendations
    analyzer = HubAnalyzer()
    recommendations = analyzer.generate_zone_skill_recommendations(zone)

    # Verify recommendation targets the gap
    assert len(recommendations) == 1
    assert recommendations[0].skill == "ultrasound"
    assert recommendations[0].priority == "HIGH"
```

### Regression Tests: Backward Compatibility

```python
def test_backward_compatibility_no_critical_skills():
    """Zones without critical skills use traditional headcount logic."""
    zone = SchedulingZone(
        name="Test Zone",
        minimum_coverage=2,
        critical_skills={}  # No critical skills defined
    )
    zone.primary = [
        ZoneFacultyAssignment(
            faculty_id="F1", name="Dr. A", role="primary",
            available=True, skills=[]
        ),
        ZoneFacultyAssignment(
            faculty_id="F2", name="Dr. B", role="primary",
            available=True, skills=[]
        )
    ]

    # Should be self-sufficient based on headcount alone
    assert zone.is_self_sufficient()
    assert zone.calculate_status() == ZoneStatus.GREEN

def test_backward_compatibility_no_faculty_skills():
    """Faculty without skills tracked use traditional headcount logic."""
    zone = SchedulingZone(
        name="Test Zone",
        minimum_coverage=2,
        critical_skills={"ob": 1}
    )
    zone.primary = [
        ZoneFacultyAssignment(
            faculty_id="F1", name="Dr. A", role="primary",
            available=True
            # skills field not set (defaults to empty list)
        ),
        ZoneFacultyAssignment(
            faculty_id="F2", name="Dr. B", role="primary",
            available=True
            # skills field not set
        )
    ]

    # During migration, should gracefully handle missing skill data
    assert not zone.is_self_sufficient()  # Skill gap detected
```

### Performance Tests

```python
def test_performance_large_zone():
    """Skill checking performs adequately with large faculty pools."""
    import time

    zone = SchedulingZone(
        name="Large Zone",
        minimum_coverage=10,
        critical_skills={f"skill_{i}": 1 for i in range(20)}  # 20 skills
    )

    # Add 100 faculty members
    for i in range(100):
        zone.primary.append(
            ZoneFacultyAssignment(
                faculty_id=f"F{i}",
                name=f"Dr. {i}",
                role="primary",
                available=True,
                skills=[f"skill_{i % 20}"]  # Distribute skills
            )
        )

    start = time.time()
    result = zone.is_self_sufficient()
    duration = time.time() - start

    assert duration < 0.1  # Should complete in < 100ms
    assert result is True
```

## Success Metrics

### Primary Objective: Eliminate False Positives

**Metric**: False GREEN rate
- **Current**: Unknown (not tracked)
- **Target**: 0% false GREEN status when critical skills missing
- **Measurement**: Audit zone status against actual operational capability

**Success Criterion**: No zone reports GREEN status when it lacks any critical skill.

### Secondary Objective: Improve Cross-Training Targeting

**Metric**: Cross-training effectiveness
- **Current**: Recommendations based on general single-provider analysis
- **Target**: 100% of HIGH priority recommendations address actual zone gaps
- **Measurement**: Track correlation between recommendations and zone skill deficits

**Success Criterion**: All HIGH priority cross-training recommendations target skills that would improve zone self-sufficiency if acquired.

### Tertiary Objective: Accurate Capability Reporting

**Metric**: Zone health report accuracy
- **Current**: Reports only headcount-based status
- **Target**: Reports reflect both headcount and skill coverage
- **Measurement**: Compare reported status against manual capability assessment

**Success Criterion**: Zone health reports accurately reflect operational capability, including specific skill gaps and their severity.

### Adoption Metrics

**Metric**: Configuration completeness
- **Phase 2 Target**: 100% of zones have critical skills defined
- **Phase 3 Target**: 100% of active faculty have skills populated
- **Measurement**: Count zones/faculty with non-empty skill data

**Success Criterion**: Complete skill data coverage across all zones and faculty within 1 month of Phase 3 completion.

### System Reliability

**Metric**: Status calculation performance
- **Target**: < 100ms for skill-based self-sufficiency check
- **Target**: < 500ms for complete health report generation
- **Measurement**: Performance monitoring of new methods

**Success Criterion**: No performance degradation in zone status calculations or report generation.

---

## Appendix: Skill Taxonomy Examples

To ensure consistency, define a standardized skill catalog:

### Clinical Skills
- `icu_attending` - ICU attending physician
- `ob_supervision` - OB/GYN supervision and delivery
- `trauma_team_leader` - Trauma team leadership
- `pediatric_resuscitation` - PALS-level pediatric care
- `procedure_supervision` - Procedural supervision (general)
- `code_team_leader` - Code blue team leadership
- `ultrasound_supervision` - Point-of-care ultrasound
- `toxicology_consult` - Toxicology consultation

### Supervision Skills
- `clinic_supervision` - Outpatient clinic supervision
- `ed_supervision` - Emergency department supervision
- `precepting` - Student/resident precepting

### Education Skills
- `simulation_instructor` - Simulation center instruction
- `didactics_faculty` - Classroom teaching
- `curriculum_development` - Curriculum design
- `assessment_development` - Assessment and evaluation

### Administrative Skills
- `medical_director` - Medical director responsibilities
- `quality_improvement` - QI project leadership
- `peer_review` - Peer review participation

This taxonomy should be maintained in a configuration file and updated through a formal governance process.
