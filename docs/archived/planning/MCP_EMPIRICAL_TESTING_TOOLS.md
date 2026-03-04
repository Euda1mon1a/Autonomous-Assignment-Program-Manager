# MCP Empirical Testing Tools

> **Goal:** Enable Claude Code to empirically test Python modules head-to-head
> **Purpose:** Determine what works best, what's high-yield, what to cut
> **Status:** IMPLEMENTED - 5 tools ready for use

---

## Implementation Status

| Tool | Status | File |
|------|--------|------|
| `benchmark_solvers_tool` | Implemented | `empirical_tools.py` |
| `benchmark_constraints_tool` | Implemented | `empirical_tools.py` |
| `ablation_study_tool` | Implemented | `empirical_tools.py` |
| `benchmark_resilience_tool` | Implemented | `empirical_tools.py` |
| `module_usage_analysis_tool` | Implemented | `empirical_tools.py` |

---

## The Vision

```
Claude: "Compare greedy vs cp_sat solver on 100 random schedules"
MCP: Returns structured comparison data

Claude: "Which resilience checks catch the most real issues?"
MCP: Returns yield analysis across scenarios

Claude: "What happens if we remove the tensegrity solver?"
MCP: Returns impact analysis - nothing breaks, 50KB less code

Claude: "Run homeostasis vs allostatic load on burnout prediction"
MCP: Returns head-to-head accuracy comparison
```

---

## Core Empirical Testing Tools

### 1. `benchmark_solvers`

**Purpose:** Head-to-head solver comparison with controlled inputs

```python
@mcp.tool()
async def benchmark_solvers_tool(
    solvers: list[str],  # ["greedy", "cp_sat", "pulp", "hybrid"]
    scenario_count: int = 50,
    scenario_type: str = "random",  # random, edge_case, historical
    metrics: list[str] = ["runtime", "violations", "fairness", "coverage"],
    timeout_per_run: int = 60,
) -> SolverBenchmark:
    """
    Benchmark multiple solvers on identical scenarios.

    Returns:
        SolverBenchmark with:
        - scenarios_run: int
        - results_by_solver: dict[solver -> SolverMetrics]
        - winner_by_metric: dict[metric -> solver]
        - statistical_significance: dict[comparison -> p_value]
        - recommendation: str
    """
```

**Output Example:**
```json
{
  "scenarios_run": 50,
  "results_by_solver": {
    "greedy": {"avg_runtime": 0.3, "avg_violations": 2.4, "avg_fairness": 0.82},
    "cp_sat": {"avg_runtime": 12.5, "avg_violations": 0.1, "avg_fairness": 0.94},
    "pulp": {"avg_runtime": 4.2, "avg_violations": 0.8, "avg_fairness": 0.89}
  },
  "winner_by_metric": {
    "runtime": "greedy",
    "violations": "cp_sat",
    "fairness": "cp_sat"
  },
  "recommendation": "cp_sat for quality, greedy for speed. pulp offers no unique advantage."
}
```

---

### 2. `benchmark_constraints`

**Purpose:** Test which constraints catch real issues vs false positives

```python
@mcp.tool()
async def benchmark_constraints_tool(
    constraints: list[str] | None = None,  # None = all
    test_schedules: str = "historical",  # historical, synthetic, edge_cases
    measure: str = "yield",  # yield, false_positive_rate, runtime_cost
) -> ConstraintBenchmark:
    """
    Measure constraint effectiveness.

    Returns:
        ConstraintBenchmark with:
        - constraint_stats: dict[constraint -> {
            triggers: int,
            true_positives: int,
            false_positives: int,
            yield_rate: float,
            avg_runtime_ms: float
        }]
        - high_yield: list[str] (>80% true positive)
        - low_yield: list[str] (<20% true positive)
        - candidates_for_removal: list[str]
    """
```

**Output Example:**
```json
{
  "constraint_stats": {
    "acgme_80_hour": {"triggers": 45, "true_positives": 44, "yield_rate": 0.98},
    "supervision_ratio": {"triggers": 30, "true_positives": 28, "yield_rate": 0.93},
    "template_balance": {"triggers": 120, "true_positives": 15, "yield_rate": 0.12}
  },
  "high_yield": ["acgme_80_hour", "supervision_ratio", "rest_period"],
  "low_yield": ["template_balance", "preference_soft"],
  "candidates_for_removal": ["template_balance"]
}
```

---

### 3. `benchmark_resilience`

**Purpose:** Compare resilience modules for real-world value

```python
@mcp.tool()
async def benchmark_resilience_tool(
    modules: list[str] | None = None,  # None = all
    scenarios: str = "crisis",  # crisis, normal, edge_case
    metrics: list[str] = ["detection_rate", "false_alarm_rate", "lead_time"],
) -> ResilienceBenchmark:
    """
    Compare resilience framework components.

    Returns:
        ResilienceBenchmark with:
        - module_stats: dict[module -> {
            detection_rate: float,
            false_alarm_rate: float,
            avg_lead_time_hours: float,
            runtime_cost_ms: float,
            complexity_lines: int
        }]
        - tier_analysis: dict[tier -> overall_value]
        - high_value: list[str]
        - low_value: list[str]
        - cut_candidates: list[str]
    """
```

**Output Example:**
```json
{
  "module_stats": {
    "n1_contingency": {"detection_rate": 0.95, "false_alarm": 0.05, "lines": 200},
    "n2_contingency": {"detection_rate": 0.60, "false_alarm": 0.30, "lines": 400},
    "homeostasis": {"detection_rate": 0.70, "false_alarm": 0.20, "lines": 1200},
    "stigmergy": {"detection_rate": 0.15, "false_alarm": 0.40, "lines": 800},
    "tensegrity": {"detection_rate": 0.10, "false_alarm": 0.60, "lines": 18000}
  },
  "high_value": ["n1_contingency", "80_percent_threshold", "defense_levels"],
  "low_value": ["stigmergy", "tensegrity", "quantum_solver"],
  "cut_candidates": ["tensegrity", "stigmergy"]
}
```

---

### 4. `ablation_study`

**Purpose:** What breaks if we remove a module?

```python
@mcp.tool()
async def ablation_study_tool(
    module_path: str,  # e.g., "app/scheduling/tensegrity/"
    test_suite: str = "full",  # full, scheduling, resilience
) -> AblationResult:
    """
    Test impact of removing a module.

    Returns:
        AblationResult with:
        - module_size: int (lines of code)
        - dependencies: list[str] (what imports this)
        - dependents: list[str] (what this imports)
        - tests_affected: int
        - tests_would_fail: int
        - functionality_lost: list[str]
        - safe_to_remove: bool
        - removal_impact: str  # "none", "minor", "major", "breaking"
    """
```

**Output Example:**
```json
{
  "module_path": "app/scheduling/tensegrity/",
  "module_size": 18000,
  "dependencies": ["numpy", "scipy"],
  "dependents": ["app/scheduling/engine.py"],
  "tests_affected": 30,
  "tests_would_fail": 2,
  "functionality_lost": ["tensegrity_solver option"],
  "safe_to_remove": true,
  "removal_impact": "minor",
  "recommendation": "Remove - 18K lines for rarely-used solver"
}
```

---

### 5. `scenario_matrix`

**Purpose:** Test module combinations across scenario types

```python
@mcp.tool()
async def scenario_matrix_tool(
    modules: list[str],  # What to compare
    scenarios: list[str],  # What situations
    runs_per_cell: int = 10,
) -> ScenarioMatrix:
    """
    Run matrix of modules x scenarios.

    Returns:
        ScenarioMatrix with:
        - matrix: dict[(module, scenario) -> score]
        - best_for_scenario: dict[scenario -> module]
        - generalist: str (best across all)
        - specialist_recommendations: dict[scenario -> module]
    """
```

**Output Example:**
```json
{
  "matrix": {
    ("greedy", "normal"): 0.85,
    ("greedy", "crisis"): 0.40,
    ("cp_sat", "normal"): 0.92,
    ("cp_sat", "crisis"): 0.88,
    ("hybrid", "normal"): 0.90,
    ("hybrid", "crisis"): 0.91
  },
  "best_for_scenario": {
    "normal": "cp_sat",
    "crisis": "hybrid",
    "understaffed": "greedy"
  },
  "generalist": "hybrid",
  "recommendation": "Use hybrid as default, greedy for emergency speed"
}
```

---

### 6. `module_usage_analysis`

**Purpose:** What code is actually used in production paths?

```python
@mcp.tool()
async def module_usage_analysis_tool(
    entry_points: list[str] = ["schedule_generate", "validate", "swap"],
) -> UsageAnalysis:
    """
    Trace code paths from entry points.

    Returns:
        UsageAnalysis with:
        - reachable_modules: list[str]
        - unreachable_modules: list[str]  # Dead code candidates
        - hot_paths: list[str]  # Frequently executed
        - cold_paths: list[str]  # Rarely executed
        - dead_code_lines: int
        - dead_code_percentage: float
    """
```

**Output Example:**
```json
{
  "reachable_modules": ["engine", "solvers", "constraints", "validator"],
  "unreachable_modules": ["quantum_solver", "tensegrity", "game_theory"],
  "hot_paths": ["engine.solve", "validator.check_acgme"],
  "cold_paths": ["pareto_optimization", "stigmergy_analysis"],
  "dead_code_lines": 25000,
  "dead_code_percentage": 4.0
}
```

---

## Experimental Framework

### 7. `create_experiment`

**Purpose:** Define a controlled experiment

```python
@mcp.tool()
async def create_experiment_tool(
    name: str,
    hypothesis: str,
    control: str,  # Module/config to use as baseline
    treatment: str,  # Module/config to test
    metric: str,  # What to measure
    sample_size: int = 100,
) -> Experiment:
    """
    Create a controlled experiment definition.

    Returns:
        Experiment with:
        - id: str
        - status: "ready"
        - estimated_runtime: float
    """
```

### 8. `run_experiment`

**Purpose:** Execute an experiment

```python
@mcp.tool()
async def run_experiment_tool(
    experiment_id: str,
) -> ExperimentResult:
    """
    Run a defined experiment.

    Returns:
        ExperimentResult with:
        - control_mean: float
        - treatment_mean: float
        - difference: float
        - p_value: float
        - significant: bool
        - confidence_interval: tuple[float, float]
        - recommendation: str
    """
```

---

## Implementation Priority

### Phase 1: Core Comparison (Week 1)

| Tool | Effort | Value | Enables |
|------|--------|-------|---------|
| `benchmark_solvers` | Medium | High | Solver selection |
| `benchmark_constraints` | Medium | High | Constraint pruning |
| `ablation_study` | Low | High | Dead code removal |

### Phase 2: Deep Analysis (Week 2)

| Tool | Effort | Value | Enables |
|------|--------|-------|---------|
| `benchmark_resilience` | Medium | High | Resilience pruning |
| `scenario_matrix` | Medium | Medium | Context-aware selection |
| `module_usage_analysis` | Medium | High | Dead code identification |

### Phase 3: Experimentation (Week 3)

| Tool | Effort | Value | Enables |
|------|--------|-------|---------|
| `create_experiment` | Low | Medium | Structured testing |
| `run_experiment` | Medium | Medium | Statistical rigor |

---

## What This Enables

### Current State
```
Claude: *reads code*
Claude: *guesses* which solver is better
Claude: *hopes* tensegrity is useful
Claude: *manually* compares outputs
```

### With Empirical Tools
```
Claude: benchmark_solvers(["greedy", "cp_sat", "pulp", "hybrid"])
Result: cp_sat wins on quality, greedy on speed, pulp offers nothing unique

Claude: ablation_study("app/scheduling/tensegrity/")
Result: 18K lines, 2 tests fail, safe to remove, minor impact

Claude: benchmark_resilience()
Result: N-1 contingency high yield, stigmergy low yield, cut candidates identified

Claude: Confidently refactor with data backing decisions
```

---

## Data-Driven Decisions

### Questions These Tools Answer

| Question | Tool |
|----------|------|
| Which solver should be default? | `benchmark_solvers` |
| Which constraints are false-positive factories? | `benchmark_constraints` |
| Which resilience features earn their complexity? | `benchmark_resilience` |
| What can we delete without breaking things? | `ablation_study` |
| What's the best module for crisis scenarios? | `scenario_matrix` |
| What code is never executed? | `module_usage_analysis` |
| Is this refactor actually better? | `run_experiment` |

---

## Connection to 10-Year Airgap Goal

These tools help **before** airgap deployment:

1. **Identify dead code** → Remove before freezing
2. **Find high-yield modules** → Keep those
3. **Cut low-yield complexity** → Simpler = more maintainable
4. **Validate solver choice** → Pick the right default
5. **Prune resilience bloat** → Keep what works

**Result:** A leaner, empirically-validated system that a future PD can actually maintain.

---

## Sample Workflow

```markdown
## Cleanup Sprint Using MCP Empirical Tools

### Day 1: Solver Analysis
1. benchmark_solvers(["greedy", "cp_sat", "pulp", "hybrid"])
2. Decision: Remove pulp (no advantage), keep hybrid as default
3. ablation_study("app/scheduling/pulp_solver.py") → Safe to remove

### Day 2: Constraint Analysis
1. benchmark_constraints(test_schedules="historical")
2. Decision: Remove template_balance (12% yield), keep ACGME (98% yield)
3. Refactor constraint loading

### Day 3: Resilience Analysis
1. benchmark_resilience(scenarios="crisis")
2. Decision: Keep N-1, homeostasis. Remove stigmergy, tensegrity.
3. ablation_study("app/resilience/stigmergy/") → Safe
4. ablation_study("app/scheduling/tensegrity/") → Safe

### Day 4: Dead Code Sweep
1. module_usage_analysis(entry_points=["api_main"])
2. Identify 25K lines unreachable
3. Remove quantum_solver, game_theory (unused)

### Day 5: Final Validation
1. run_experiment(control="before", treatment="after", metric="test_pass_rate")
2. Confirm all tests pass
3. Commit cleaned codebase
```

---

*Empirical testing tools for data-driven code refinement - December 2024*
