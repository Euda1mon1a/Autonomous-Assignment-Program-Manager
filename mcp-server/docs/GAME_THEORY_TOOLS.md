# Game Theory Tools - Nash Equilibrium Analysis

## Overview

The Game Theory tools provide Nash equilibrium analysis for schedule stability, helping identify when schedules are unstable and likely to generate swap requests.

## Core Concepts

### Nash Equilibrium
A schedule is **Nash stable** if no individual player can improve their utility by unilaterally deviating (requesting a swap). If a schedule is NOT Nash stable, expect:
- Swap requests from dissatisfied players
- Schedule instability requiring administrative intervention
- Potential cascade of further swaps

### Utility Function
Player utility is calculated from four weighted components:
- **Workload Fairness** (40%): Based on Gini coefficient of hours distribution
- **Preference Satisfaction** (30%): Match to stated preferences (stigmergy trails)
- **Convenience** (20%): Clustering, commute, family obligations
- **Continuity** (10%): Stability compared to previous period

### Coordination Failures
Situations where multiple players could ALL improve through cooperation (Pareto improvement), but coordination fails due to:
- **Information Asymmetry**: Players don't know about opportunity
- **Trust Deficit**: Players don't trust each other
- **Transaction Cost**: Coordination cost exceeds benefit
- **Protocol Barrier**: System doesn't support multi-way swaps
- **Preference Mismatch**: No mutually beneficial swap exists

## Available Tools

### 1. `analyze_nash_stability`

Analyze overall schedule Nash equilibrium status.

**Input:**
```python
{
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "include_person_details": true,
    "deviation_threshold": 0.01
}
```

**Output:**
```python
{
    "stability_status": "UNSTABLE",  # STABLE, UNSTABLE, WEAKLY_STABLE
    "is_nash_equilibrium": false,
    "total_players": 40,
    "players_with_deviations": 12,
    "deviation_rate": 0.30,
    "avg_utility_gain_available": 0.08,
    "max_deviation_incentive": 0.15,
    "deviations": [
        {
            "person_id": "PERSON_abc123",
            "current_utility": 0.65,
            "alternative_utility": 0.80,
            "utility_gain": 0.15,
            "deviation_type": "SWAP",
            "description": "Swap clinic days with Dr. Jones"
        }
    ],
    "game_theoretic_interpretation": "Schedule is NOT Nash stable...",
    "recommendations": [
        "Address top 5 deviation incentives",
        "Consider facilitating mutually beneficial swaps"
    ]
}
```

**Use Case:** Monthly schedule health check to predict swap request volume.

---

### 2. `find_deviation_incentives`

Analyze deviation incentives for a specific person.

**Input:**
```python
{
    "person_id": "faculty-abc-123",
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "include_all_alternatives": false,
    "max_alternatives": 5
}
```

**Output:**
```python
{
    "person_id": "PERSON_abc123",
    "current_utility": 0.62,
    "utility_breakdown": {
        "workload_fairness": 0.55,
        "preference_satisfaction": 0.70,
        "convenience": 0.60,
        "continuity": 0.65
    },
    "best_alternative_utility": 0.80,
    "max_utility_gain": 0.18,
    "has_profitable_deviation": true,
    "deviation_incentives": [
        {
            "deviation_type": "SWAP",
            "utility_gain": 0.18,
            "target_person_id": "PERSON_def456",
            "description": "Swap clinic days with Dr. Jones",
            "confidence": 0.85
        }
    ],
    "strategic_position": "Strong deviation incentive - likely to request swap",
    "barriers_to_deviation": []
}
```

**Use Case:**
- Investigate why specific person is requesting swaps
- Proactively identify dissatisfied faculty before they complain
- Understand utility breakdown for personalized improvements

---

### 3. `detect_coordination_failures`

Find Pareto improvements blocked by coordination barriers.

**Input:**
```python
{
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "min_pareto_gain": 0.05
}
```

**Output:**
```python
{
    "total_failures_detected": 3,
    "total_pareto_gain_available": 0.28,
    "failures": [
        {
            "failure_type": "PROTOCOL_BARRIER",
            "involved_person_ids": ["PERSON_A", "PERSON_B", "PERSON_C"],
            "potential_pareto_gain": 0.15,
            "per_person_gains": {
                "PERSON_A": 0.05,
                "PERSON_B": 0.05,
                "PERSON_C": 0.05
            },
            "coordination_barrier": "System only supports bilateral swaps - three-way swap not possible",
            "solution_path": "Implement multi-way swap protocol or coordinate via admin",
            "confidence": 0.70
        }
    ],
    "system_recommendations": [
        "Implement multi-way swap support",
        "Create swap marketplace to reduce information asymmetry",
        "Add swap recommendation engine"
    ],
    "game_theoretic_insights": "Found 3 coordination failures with total potential gain of 0.28..."
}
```

**Use Case:**
- Identify "money left on the table" - missed win-win-win opportunities
- Justify system improvements (multi-way swaps, swap marketplace)
- Find manual coordination opportunities for administrators

---

## Integration with Existing Tools

### Complements Shapley Fairness
- **Shapley**: Calculates *fair* workload distribution based on marginal contribution
- **Nash Equilibrium**: Predicts *stable* schedule states where players won't deviate
- **Together**: Shapley determines target fairness, Nash detects deviations from that target

### Workflow
1. Generate schedule using solver
2. Calculate Shapley values to validate fairness
3. Analyze Nash stability to predict swap requests
4. Detect coordination failures for system improvements
5. Proactively facilitate beneficial swaps before requests arrive

---

## Game Theory Insights

### Nash Equilibrium Types

**Pure Nash Equilibrium:**
- Every player's strategy is a best response to others' strategies
- No profitable unilateral deviations exist
- Schedule is stable without enforcement

**Weak Nash Equilibrium:**
- Some players are indifferent to deviations (utility ties)
- Stable but fragile - small changes could trigger swaps
- Monitor closely for deterioration

**Not Nash Equilibrium:**
- At least one player has profitable deviation
- Expect swap requests and instability
- Requires rebalancing or swap facilitation

### Pareto Efficiency

**Pareto Optimal:**
- No change can improve one player without harming another
- Doesn't guarantee Nash stability (could still be unstable!)

**Pareto Improvement:**
- Change that improves at least one player without harming any
- Coordination failures prevent these from happening

**Key Insight:** Nash Equilibrium ≠ Pareto Optimal
- Example: Prisoner's Dilemma has Nash equilibrium that's Pareto inefficient
- A schedule can be Nash stable but still have unrealized Pareto gains
- Coordination failures create Pareto inefficiency even at Nash equilibrium

---

## Example Use Cases

### Use Case 1: Monthly Schedule Health Check
```bash
# Check if January schedule is Nash stable
result = await analyze_nash_stability_tool(
    start_date="2025-01-01",
    end_date="2025-01-31"
)

if not result.is_nash_equilibrium:
    print(f"⚠️ Unstable: {result.players_with_deviations} players want to deviate")
    print(f"Expected swap requests: ~{result.deviation_rate * 100:.0f}%")

    # Address top deviations
    for dev in result.deviations[:5]:
        print(f"  - {dev.person_id}: {dev.description} (+{dev.utility_gain:.2f})")
```

### Use Case 2: Investigate Specific Complaint
```bash
# Dr. Smith is unhappy - why?
analysis = await find_deviation_incentives_tool(
    person_id="dr-smith-id",
    start_date="2025-01-01",
    end_date="2025-03-31"
)

print(f"Current satisfaction: {analysis.current_utility:.2f}")
print(f"Problem areas:")
for component, value in analysis.utility_breakdown.items():
    if value < 0.6:
        print(f"  - {component}: {value:.2f} (low)")

print(f"\nBest improvement: {analysis.deviation_incentives[0].description}")
```

### Use Case 3: Justify System Improvements
```bash
# Find coordination failures to justify multi-way swap feature
failures = await detect_coordination_failures_tool(
    start_date="2025-01-01",
    end_date="2025-12-31"
)

protocol_barriers = [f for f in failures.failures if f.failure_type == "PROTOCOL_BARRIER"]
total_gain = sum(f.potential_pareto_gain for f in protocol_barriers)

print(f"Multi-way swap feature would unlock {total_gain:.2f} utility")
print(f"Affecting {len(protocol_barriers)} opportunities")
```

---

## Implementation Notes

### Utility Calculation Details

**Workload Fairness (Gini Coefficient):**
```python
# Perfect equality: Gini = 0 → Fairness = 1.0
# Maximum inequality: Gini = 1 → Fairness = 0.0
fairness = 1.0 - gini_coefficient(workload_hours)
```

**Preference Satisfaction (Stigmergy):**
```python
# Uses PreferenceTrailRecord data
# Normalized trail strength [0, 1] (max strength = 10.0)
preference = average(trail_strengths) / 10.0
```

**Convenience (Clustering):**
```python
# Placeholder - production would analyze:
# - Temporal clustering (consecutive days)
# - Commute implications
# - Family obligations
# - Circadian rhythm
convenience = 0.6  # Moderate default
```

**Continuity (Stability):**
```python
# Overlap with previous period
overlap = len(current_ids & previous_ids)
continuity = overlap / len(previous_ids)
```

### Custom Utility Weights
```python
# Default: (0.4, 0.3, 0.2, 0.1)
result = await analyze_nash_stability_tool(
    start_date="2025-01-01",
    end_date="2025-03-31",
    utility_weights={
        "workload": 0.5,      # Emphasize workload fairness
        "preference": 0.3,
        "convenience": 0.1,
        "continuity": 0.1
    }
)
```

---

## Future Enhancements

### Planned
1. **Mixed Strategy Nash**: Support probabilistic strategies (accept/reject with probability)
2. **Repeated Game Analysis**: Model long-term cooperation incentives (Folk Theorem)
3. **Mechanism Design**: Suggest swap protocols that incentivize truth-telling
4. **Coalition Formation**: Detect stable coalitions for multi-way swaps

### Research Opportunities
- **Algorithmic Game Theory**: Compute Nash equilibria efficiently for large games
- **Learning in Games**: Model how players learn optimal strategies over time
- **Network Games**: Analyze swap networks and social influence
- **Auction Theory**: Design VCG mechanisms for fair swap allocation

---

## References

### Game Theory
- **Nash Equilibrium**: John Nash (1950) - Non-cooperative games
- **Pareto Efficiency**: Vilfredo Pareto (1896) - Welfare economics
- **Coordination Games**: Schelling (1960) - Focal points
- **Folk Theorem**: Friedman (1971) - Repeated games cooperation

### Related Tools
- **Shapley Fairness**: `calculate_shapley_workload_tool` - Fair workload distribution
- **Swap Candidates**: `analyze_swap_candidates_tool` - Find compatible swaps
- **Preference Trails**: PreferenceTrailRecord model - Stigmergic preference learning

### Implementation
- **Source**: `/mcp-server/src/scheduler_mcp/tools/game_theory_tools.py`
- **Integration**: `/mcp-server/src/scheduler_mcp/server.py` (lines 1729+)
- **Models**: Pydantic request/response schemas with full validation

---

**Last Updated:** 2025-12-29
**Version:** 1.0.0
**Status:** Production-ready
