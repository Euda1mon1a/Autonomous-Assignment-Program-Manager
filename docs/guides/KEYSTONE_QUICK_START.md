# Keystone Analysis Quick Start Guide

## What is Keystone Analysis?

Identifies critical resources (faculty, residents, services) whose removal causes **disproportionate** schedule collapse, like removing a keystone species from an ecosystem.

**Key Difference from Hub Analysis:**
- **Hub**: High volume, many connections (risk: overload)
- **Keystone**: Low volume, critical impact (risk: irreplaceable)

## Quick Usage

```python
from app.resilience import KeystoneAnalyzer

# 1. Initialize
analyzer = KeystoneAnalyzer(keystone_threshold=0.6)

# 2. Identify keystones
keystones = analyzer.identify_keystone_resources(
    faculty=faculty_list,
    residents=resident_list,
    assignments=current_assignments,
    services=service_capability_map,
    rotations=rotation_metadata,
)

# 3. Simulate cascade for critical keystone
cascade = analyzer.simulate_removal_cascade(
    entity_id=keystones[0].entity_id,
    faculty=faculty_list,
    residents=resident_list,
    assignments=current_assignments,
    services=service_capability_map,
    rotations=rotation_metadata,
)

# 4. Create succession plan
plan = analyzer.recommend_succession_plan(
    keystone=keystones[0],
    all_entities=faculty_list + resident_list,
    services=service_capability_map,
)

# 5. Get summary
summary = analyzer.get_keystone_summary()
print(f"Found {summary['total_keystones']} keystones")
print(f"Single points of failure: {summary['single_points_of_failure']}")
```

## Key Metrics

### Keystoneness Score (0.0-1.0)
- **>0.8**: Extreme keystone (immediate succession planning)
- **0.6-0.8**: High keystone (prioritize cross-training)
- **0.4-0.6**: Moderate keystone (monitor)
- **<0.4**: Not a keystone

### Functional Redundancy (0.0-1.0)
- **<0.2**: Critical - no viable backup
- **0.2-0.5**: Limited - some alternatives
- **0.5-0.8**: Moderate - replaceable
- **>0.8**: High - many backups

### Risk Levels
1. **CATASTROPHIC**: System collapse likely (>50% coverage loss)
2. **CRITICAL**: Major disruption, no backup
3. **HIGH**: Significant impact, limited backup
4. **MODERATE**: Noticeable impact, backup exists
5. **LOW**: Minimal impact, easy replacement

## Interpreting Results

### Example Keystone Resource
```python
KeystoneResource(
    entity_name="Dr. Smith (Neonatologist)",
    keystoneness_score=0.85,        # High impact/low abundance
    functional_redundancy=0.1,      # No viable backup
    unique_capabilities=["NICU"],   # Only one who can do this
    risk_level=CRITICAL,            # High risk
    is_keystone=True,               # Confirmed keystone
    is_single_point_of_failure=True # No backup
)
```

**Interpretation:**
- Dr. Smith is a keystone (0.85 score, low redundancy)
- Sole provider for NICU (unique capability)
- If removed: CRITICAL impact
- **Action:** Urgent succession planning

### Example Cascade
```python
CascadeAnalysis(
    cascade_depth=3,           # 3-level propagation
    coverage_loss=0.35,        # 35% of assignments lost
    recovery_time_days=30,     # 1 month to recover
    is_catastrophic=False,     # <50% threshold
    total_affected=12          # 12 entities impacted
)
```

**Interpretation:**
- Removal triggers 3-level cascade
- 35% coverage loss (significant but not catastrophic)
- 30-day recovery (moderate)
- **Action:** Cross-train backup immediately

## Files Created

1. **`backend/app/resilience/keystone_analysis.py`** - Core engine
2. **`backend/app/resilience/keystone_visualization.py`** - Graphs/charts
3. **`backend/tests/resilience/test_keystone_analysis.py`** - Tests
4. **`backend/app/resilience/keystone_example.py`** - Demo

## Integration with Existing Framework

### Complements Existing Modules
- **Contingency Analysis**: Adds ecological cascade perspective
- **Hub Analysis**: Identifies different critical resources
- **Defense in Depth**: Keystone risk → defense level
- **Static Stability**: Succession plans → fallback schedules

### MCP Tool Ready
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

## Real-World Example

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

## Next Steps

1. **Run analysis on current schedule**
2. **Review top 5 keystones**
3. **Prioritize succession plans by risk level**
4. **Implement cross-training for CRITICAL keystones**
5. **Monitor keystoneness over time**

## Documentation

- Full details: `KEYSTONE_IMPLEMENTATION_SUMMARY.md`
- Usage example: `backend/app/resilience/keystone_example.py`
- Tests: `backend/tests/resilience/test_keystone_analysis.py`
- API docs: Docstrings in `keystone_analysis.py`
