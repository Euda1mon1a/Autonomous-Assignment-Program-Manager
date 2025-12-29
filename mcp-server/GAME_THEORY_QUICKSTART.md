# Game Theory Tools - Quick Start

## 🎯 What It Does

Detects **Nash equilibrium** stability in schedules - predicts who will request swaps and why.

## 🚀 Quick Usage

### 1. Check if Schedule is Stable
```python
result = await analyze_nash_stability_tool(
    start_date="2025-01-01",
    end_date="2025-03-31"
)

# Result: UNSTABLE - 30% of players want to deviate
# Expect 12 swap requests from dissatisfied faculty
```

### 2. Investigate Specific Person
```python
analysis = await find_deviation_incentives_tool(
    person_id="faculty-id-here",
    start_date="2025-01-01",
    end_date="2025-03-31"
)

# Result: Current utility 0.62, best alternative 0.80
# Recommendation: Swap clinic days with Dr. Jones (+0.18 utility)
```

### 3. Find Coordination Failures
```python
failures = await detect_coordination_failures_tool(
    start_date="2025-01-01",
    end_date="2025-03-31"
)

# Result: 3 three-way swaps blocked by protocol barrier
# Total potential gain: +0.28 utility if coordination succeeded
```

## 📊 Game Theory Concepts

**Nash Equilibrium:** State where no one can improve by changing alone
- ✅ STABLE: No one wants to deviate → schedule is stable
- ⚠️ UNSTABLE: People want to swap → expect requests

**Pareto Improvement:** Win-win-win changes where everyone benefits
- Coordination failures prevent these from happening
- "Money left on the table"

**Utility Function:** Measures satisfaction [0.0, 1.0]
```
Utility = 0.4 × Workload Fairness
        + 0.3 × Preference Match
        + 0.2 × Convenience
        + 0.1 × Continuity
```

## 📁 Files

- **Implementation:** `src/scheduler_mcp/tools/game_theory_tools.py`
- **Registration:** `src/scheduler_mcp/server.py` (lines 1729+)
- **Documentation:** `docs/GAME_THEORY_TOOLS.md`
- **Examples:** `examples/game_theory_example.py`

## 🔗 Integration

**Complements:**
- Shapley Fairness (fair workload)
- Swap Candidates (compatible partners)
- Resilience Framework (N-1/N-2 analysis)

**Workflow:**
1. Generate schedule
2. Check Nash stability (this tool)
3. If unstable: facilitate predicted swaps proactively
4. If stable: monitor for changes

## ✨ Key Features

- Predicts swap requests before they happen
- Explains WHY people are dissatisfied (utility breakdown)
- Detects "money left on table" (coordination failures)
- Game theory interpretation of results
- Graceful degradation if backend unavailable

**Status:** ✅ Production-ready
