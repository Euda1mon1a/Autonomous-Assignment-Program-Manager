# Hopfield Network Attractor Analysis Tools

## Overview

The Hopfield Network Attractor tools apply neuroscience-inspired energy landscape analysis to schedule stability. These tools model schedule states as attractors in an energy landscape, providing insights into schedule robustness and identifying potential anti-patterns.

## Scientific Foundation

**Hopfield Networks** are recurrent neural networks with symmetric weights that model associative memory. They naturally minimize an energy function:

```
E = -0.5 * Σ(w_ij * s_i * s_j)
```

Where:
- `s_i, s_j` are binary state variables (assignment present/absent)
- `w_ij` are learned weights encoding stable scheduling patterns
- Lower energy = more stable configuration

### Key Concepts

1. **Attractors**: Stable states (energy minima) that the system naturally evolves toward
2. **Basin of Attraction**: Region from which initial states converge to the same attractor
3. **Basin Depth**: Energy barrier to escape the basin (measures stability)
4. **Spurious Attractors**: Unintended stable states (scheduling anti-patterns)

## Available Tools

### 1. `calculate_hopfield_energy_tool`

**Purpose**: Compute Hopfield energy of the current schedule state

**Parameters**:
- `start_date` (str, optional): Start date (YYYY-MM-DD)
- `end_date` (str, optional): End date (YYYY-MM-DD)
- `schedule_id` (str, optional): Specific schedule to analyze

**Returns**: `HopfieldEnergyResponse`
- `total_energy`: Total Hopfield energy
- `normalized_energy`: Energy normalized to [-1, 1]
- `stability_score`: 0 (unstable) to 1 (very stable)
- `is_local_minimum`: Whether at a local energy minimum
- `distance_to_minimum`: Estimated changes needed to reach stability

**Example Usage**:
```python
result = await calculate_hopfield_energy_tool(
    start_date="2025-01-01",
    end_date="2025-01-31"
)

if result.stability_level == "unstable":
    print(f"WARNING: Schedule energy = {result.metrics.total_energy:.2f}")
    print(f"Need {result.metrics.distance_to_minimum} changes for stability")
```

**Interpretation**:
- **Negative Energy**: Schedule matches learned stable patterns (good)
- **Energy Near Zero**: Transitional state
- **Positive Energy**: Conflicts with learned patterns (unstable)

---

### 2. `find_nearby_attractors_tool`

**Purpose**: Identify stable attractors near the current schedule state

**Parameters**:
- `max_distance` (int, default=10): Maximum Hamming distance to search (1-50)
- `start_date` (str, optional): Analysis start date
- `end_date` (str, optional): Analysis end date

**Returns**: `NearbyAttractorsResponse`
- `attractors_found`: Number of attractors identified
- `attractors`: List of `AttractorInfo` objects
  - `attractor_type`: global_minimum, local_minimum, spurious, metastable
  - `energy_level`: Energy at the attractor
  - `basin_depth`: Stability measure
  - `hamming_distance`: Distance from current state
- `global_minimum_identified`: Whether global optimum was found

**Example Usage**:
```python
result = await find_nearby_attractors_tool(max_distance=5)

for attractor in result.attractors:
    if attractor.attractor_type == "global_minimum":
        print(f"Global optimum: {attractor.hamming_distance} changes away")
        print(f"Energy improvement: {attractor.energy_level:.2f}")
```

**Use Cases**:
1. **Schedule Optimization**: Find global minimum for best configuration
2. **Alternative Schedules**: Discover different stable patterns
3. **Robustness Assessment**: Check current basin depth
4. **Constraint Debugging**: Identify why schedule won't improve

---

### 3. `measure_basin_depth_tool`

**Purpose**: Measure stability of the basin of attraction

**Parameters**:
- `attractor_id` (str, optional): Specific attractor to analyze
- `num_perturbations` (int, default=100): Perturbations to test (10-1000)

**Returns**: `BasinDepthResponse`
- `min_escape_energy`: Minimum barrier to escape basin
- `avg_escape_energy`: Average barrier across all paths
- `basin_stability_index`: 0 (shallow) to 1 (deep)
- `is_robust`: Whether schedule tolerates perturbations
- `robustness_threshold`: Number of simultaneous changes tolerated

**Example Usage**:
```python
result = await measure_basin_depth_tool(num_perturbations=200)

if result.metrics.basin_stability_index > 0.8:
    print(f"Highly stable (index = {result.metrics.basin_stability_index:.2f})")
    print(f"Tolerates {result.robustness_threshold} simultaneous changes")
else:
    print(f"WARNING: Fragile schedule")
    print(f"Min escape barrier: {result.metrics.min_escape_energy:.2f}")
```

**Why This Matters**:
- **Deep Basin**: Robust to swaps, absences, N-1 failures
- **Shallow Basin**: Small changes trigger cascade to different attractor
- **Critical for Resilience**: N-1/N-2 failures shouldn't escape basin

---

### 4. `detect_spurious_attractors_tool`

**Purpose**: Detect unintended stable patterns (scheduling anti-patterns)

**Parameters**:
- `search_radius` (int, default=20): Hamming distance to search (5-50)
- `min_basin_size` (int, default=10): Minimum basin size to report

**Returns**: `SpuriousAttractorsResponse`
- `spurious_attractors_found`: Number detected
- `spurious_attractors`: List of `SpuriousAttractorInfo` objects
  - `anti_pattern_type`: overload_concentration, clustering_violation, etc.
  - `description`: Human-readable anti-pattern description
  - `risk_level`: low, medium, high, critical
  - `mitigation_strategy`: Recommended fix
- `total_basin_coverage`: Fraction of state space that is spurious
- `is_current_state_spurious`: Whether current schedule is an anti-pattern

**Example Usage**:
```python
result = await detect_spurious_attractors_tool(search_radius=25)

if result.is_current_state_spurious:
    print("ALERT: Current schedule is in spurious attractor!")

for spurious in result.spurious_attractors:
    if spurious.risk_level == "critical":
        print(f"Anti-pattern: {spurious.description}")
        print(f"Mitigation: {spurious.mitigation_strategy}")

if result.total_basin_coverage > 0.2:
    print(f"WARNING: {result.total_basin_coverage:.0%} of state space is spurious")
```

**Common Anti-Patterns Detected**:
1. **Overload Concentration**: 80% of call shifts on 3 senior faculty
2. **Shift Clustering**: Same person consecutive night shifts
3. **Underutilization**: Junior faculty minimal rotations
4. **Boundary Gaming**: Schedule exactly at ACGME limits
5. **Rotation Monotony**: Always same rotation type

---

## Integration with Resilience Framework

Hopfield tools complement existing resilience metrics:

| Hopfield Metric | Resilience Framework Equivalent |
|-----------------|--------------------------------|
| Basin Depth | N-1/N-2 Contingency depth |
| Energy Level | Defense in Depth tier |
| Basin Escape Distance | Recovery Distance |
| Spurious Attractors | Constraint Anti-Patterns |

### Combined Analysis Pattern

```python
# 1. Check thermodynamic entropy
entropy = await calculate_schedule_entropy_tool()

# 2. Check Hopfield energy
energy = await calculate_hopfield_energy_tool()

# Combined interpretation:
if entropy.normalized_entropy > 0.7 and energy.normalized_energy < -0.5:
    print("✓ OPTIMAL: High diversity + Stable patterns")
elif entropy.normalized_entropy < 0.4 and energy.normalized_energy < -0.5:
    print("⚠ RISKY: Low diversity but stable (concentrated risk)")
elif entropy.normalized_entropy > 0.7 and energy.normalized_energy > 0:
    print("✗ BAD: High diversity but unstable (chaotic)")
else:
    print("� SUBOPTIMAL: Review schedule configuration")

# 3. Check basin depth for N-1 robustness
basin = await measure_basin_depth_tool(num_perturbations=500)
if basin.robustness_threshold < n_minus_1_target:
    print(f"✗ FAIL N-1: Only tolerates {basin.robustness_threshold} failures")

# 4. Scan for anti-patterns
spurious = await detect_spurious_attractors_tool(search_radius=30)
if spurious.spurious_attractors_found > 0:
    print(f"⚠ WARNING: {spurious.spurious_attractors_found} anti-patterns detected")
```

## Neuroscience Interpretation

Hopfield networks model **associative memory** - the schedule "remembers" stable patterns learned from historical data. Just as neurons settle into stable firing patterns representing memories:

- **Stable Schedules** = Energy minima (attractors)
- **Schedule Changes** = State evolution in energy landscape
- **Learning from History** = Weight matrix encoding past patterns
- **Anti-Patterns** = Spurious attractors (unintended memories)

## Implementation Notes

### Current Status (Phase 1 - Placeholder)

All four tools currently return **mock/placeholder data** with realistic values and proper response structures. This allows:
1. Tool discovery and testing
2. Integration with AI assistants
3. Response schema validation
4. Documentation and examples

### Future Implementation (Phase 2 - Production)

Full implementation will include:
1. **Schedule Encoding**: Convert assignments to binary state vector
2. **Weight Matrix Learning**: Train from historical schedule data
3. **Energy Calculation**: Implement actual Hopfield energy function
4. **Gradient Descent**: Find local minima in energy landscape
5. **Basin Analysis**: Monte Carlo perturbation testing
6. **Pattern Classification**: ML-based spurious attractor detection

### Dependencies

- `numpy`: Matrix operations for weight matrix and energy calculations
- `scipy`: Optimization for gradient descent and basin analysis
- `scikit-learn` (optional): Pattern classification for spurious detection

## References

1. Hopfield, J.J. (1982). "Neural networks and physical systems with emergent collective computational abilities"
2. Amit, D.J. (1989). "Modeling Brain Function: The World of Attractor Neural Networks"
3. Hertz, J., Krogh, A., Palmer, R.G. (1991). "Introduction to the Theory of Neural Computation"
4. Maass, W., Bishop, C.M. (1998). "Pulsed Neural Networks" (on attractor dynamics)

## See Also

- **Thermodynamics Tools**: Complementary entropy and phase transition analysis
- **Resilience Framework**: N-1/N-2 contingency and defense in depth
- **Time Crystal Tools**: Anti-churn and schedule stability metrics
- **Cross-Disciplinary Resilience**: Full resilience framework documentation
