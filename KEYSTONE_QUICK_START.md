***REMOVED*** Keystone Analysis Quick Start Guide

***REMOVED******REMOVED*** What is Keystone Analysis?

Identifies critical resources (faculty, residents, services) whose removal causes **disproportionate** schedule collapse, like removing a keystone species from an ecosystem.

**Key Difference from Hub Analysis:**
- **Hub**: High volume, many connections (risk: overload)
- **Keystone**: Low volume, critical impact (risk: irreplaceable)

***REMOVED******REMOVED*** Quick Usage

```python
from app.resilience import KeystoneAnalyzer

***REMOVED*** 1. Initialize
analyzer = KeystoneAnalyzer(keystone_threshold=0.6)

***REMOVED*** 2. Identify keystones
keystones = analyzer.identify_keystone_resources(
    faculty=faculty_list,
    residents=resident_list,
    assignments=current_assignments,
    services=service_capability_map,
    rotations=rotation_metadata,
)

***REMOVED*** 3. Simulate cascade for critical keystone
cascade = analyzer.simulate_removal_cascade(
    entity_id=keystones[0].entity_id,
    faculty=faculty_list,
    residents=resident_list,
    assignments=current_assignments,
    services=service_capability_map,
    rotations=rotation_metadata,
)

***REMOVED*** 4. Create succession plan
plan = analyzer.recommend_succession_plan(
    keystone=keystones[0],
    all_entities=faculty_list + resident_list,
    services=service_capability_map,
)

***REMOVED*** 5. Get summary
summary = analyzer.get_keystone_summary()
print(f"Found {summary['total_keystones']} keystones")
print(f"Single points of failure: {summary['single_points_of_failure']}")
```

***REMOVED******REMOVED*** Key Metrics

***REMOVED******REMOVED******REMOVED*** Keystoneness Score (0.0-1.0)
- **>0.8**: Extreme keystone (immediate succession planning)
- **0.6-0.8**: High keystone (prioritize cross-training)
- **0.4-0.6**: Moderate keystone (monitor)
- **<0.4**: Not a keystone

***REMOVED******REMOVED******REMOVED*** Functional Redundancy (0.0-1.0)
- **<0.2**: Critical - no viable backup
- **0.2-0.5**: Limited - some alternatives
- **0.5-0.8**: Moderate - replaceable
- **>0.8**: High - many backups

***REMOVED******REMOVED******REMOVED*** Risk Levels
1. **CATASTROPHIC**: System collapse likely (>50% coverage loss)
2. **CRITICAL**: Major disruption, no backup
3. **HIGH**: Significant impact, limited backup
4. **MODERATE**: Noticeable impact, backup exists
5. **LOW**: Minimal impact, easy replacement

***REMOVED******REMOVED*** Interpreting Results

***REMOVED******REMOVED******REMOVED*** Example Keystone Resource
```python
KeystoneResource(
    entity_name="Dr. Smith (Neonatologist)",
    keystoneness_score=0.85,        ***REMOVED*** High impact/low abundance
    functional_redundancy=0.1,      ***REMOVED*** No viable backup
    unique_capabilities=["NICU"],   ***REMOVED*** Only one who can do this
    risk_level=CRITICAL,            ***REMOVED*** High risk
    is_keystone=True,               ***REMOVED*** Confirmed keystone
    is_single_point_of_failure=True ***REMOVED*** No backup
)
```

**Interpretation:**
- Dr. Smith is a keystone (0.85 score, low redundancy)
- Sole provider for NICU (unique capability)
- If removed: CRITICAL impact
- **Action:** Urgent succession planning

***REMOVED******REMOVED******REMOVED*** Example Cascade
```python
CascadeAnalysis(
    cascade_depth=3,           ***REMOVED*** 3-level propagation
    coverage_loss=0.35,        ***REMOVED*** 35% of assignments lost
    recovery_time_days=30,     ***REMOVED*** 1 month to recover
    is_catastrophic=False,     ***REMOVED*** <50% threshold
    total_affected=12          ***REMOVED*** 12 entities impacted
)
```

**Interpretation:**
- Removal triggers 3-level cascade
- 35% coverage loss (significant but not catastrophic)
- 30-day recovery (moderate)
- **Action:** Cross-train backup immediately

***REMOVED******REMOVED*** Files Created

1. **`backend/app/resilience/keystone_analysis.py`** - Core engine
2. **`backend/app/resilience/keystone_visualization.py`** - Graphs/charts
3. **`backend/tests/resilience/test_keystone_analysis.py`** - Tests
4. **`backend/app/resilience/keystone_example.py`** - Demo

***REMOVED******REMOVED*** Integration with Existing Framework

***REMOVED******REMOVED******REMOVED*** Complements Existing Modules
- **Contingency Analysis**: Adds ecological cascade perspective
- **Hub Analysis**: Identifies different critical resources
- **Defense in Depth**: Keystone risk → defense level
- **Static Stability**: Succession plans → fallback schedules

***REMOVED******REMOVED******REMOVED*** MCP Tool Ready
```json
{
  "tool": "identify_keystone_resources",
  "params": {
    "schedule_id": "uuid",
    "threshold": 0.6,
    "generate_succession_plans": true
  }
}
```

***REMOVED******REMOVED*** Real-World Example

**Military Medical Residency:**
- 1 Neonatologist (MAJ Smith) for 500-bed hospital
- Handles all high-risk deliveries
- If deployed: NICU rotation cannot run
- **Result**: ACGME violation

**Keystone Analysis Output:**
- Keystoneness: 0.92 (CRITICAL)
- Redundancy: 0.0 (no backup)
- Cascade: 3 levels, 35% coverage loss
- **Succession Plan**: Train CPT Jones (6 months, 200 hours)

***REMOVED******REMOVED*** Next Steps

1. **Run analysis on current schedule**
2. **Review top 5 keystones**
3. **Prioritize succession plans by risk level**
4. **Implement cross-training for CRITICAL keystones**
5. **Monitor keystoneness over time**

***REMOVED******REMOVED*** Documentation

- Full details: `KEYSTONE_IMPLEMENTATION_SUMMARY.md`
- Usage example: `backend/app/resilience/keystone_example.py`
- Tests: `backend/tests/resilience/test_keystone_analysis.py`
- API docs: Docstrings in `keystone_analysis.py`
