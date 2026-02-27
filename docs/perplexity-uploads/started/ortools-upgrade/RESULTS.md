# OR-Tools CP-SAT 9.8 → 9.12 Migration Analysis

**System:** Military Residency Scheduling System  
**Model Profile:** ~12 residents, ~8 faculty, 28-day blocks, 25+ soft constraints, ~4,000 binary variables  
**Current Pin:** `ortools>=9.8,<9.9`  
**Target Pin:** `ortools>=9.12,<9.13`  
**Date:** February 26, 2026  

---

## Table of Contents

1. [Changelog Deep Dive](#1-changelog-deep-dive)
2. [API Compatibility Scan](#2-api-compatibility-scan)
3. [Hint System Evolution](#3-hint-system-evolution)
4. [Solver Behavioral Changes](#4-solver-behavioral-changes)
5. [New Features for Scheduling](#5-new-features-for-scheduling)
6. [Migration Checklist](#6-migration-checklist)

---

## 1. Changelog Deep Dive

### v9.9 — March 7, 2024

**Release:** [GitHub v9.9](https://github.com/google/or-tools/releases/tag/v9.9) | [Discussion #4119](https://github.com/google/or-tools/discussions/4119)

#### Breaking Changes (Python-Specific)

- **PEP 8 Rename (MAJOR):** The entire CP-SAT Python API was rewritten to be PEP 8-compliant, replacing all CamelCase method names with snake_case equivalents ([GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)). For example, `model.NewBoolVar()` becomes `model.new_bool_var()`, `solver.Solve()` becomes `solver.solve()`, and `solver.ObjectiveValue()` becomes the property `solver.objective_value`. The old CamelCase names remain as deprecated shims that forward to the snake_case implementations via a `_add_pre_pep8_methods()` compatibility layer ([Issue #4143](https://github.com/google/or-tools/issues/4143)).
- **pybind11 Backend:** The Python binding layer was switched from SWIG to pybind11 ([Discussion #3992](https://github.com/google/or-tools/discussions/3992)). This is transparent to most user code but affects anyone importing `swig_helper` directly.
- **`SolveWithSolutionCallback()` deprecated:** Replaced by `solver.solve(model, solution_callback=callback)` ([GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)).
- **`SearchForAllSolutions()` deprecated:** Replaced by `solver.solve(model, callback, enumerate_all_solutions=True)` ([GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)).

#### Deprecations

- All CamelCase method names on `CpModel` and `CpSolver` are deprecated in favor of snake_case equivalents. Deprecation warnings are **silent by default** and only fire when `cp_model.enable_warnings = True` ([OR-Tools API docs](https://or-tools.github.io/docs/pdoc/ortools/sat/python/cp_model.html)).
- `Proto()` method is deprecated; use the `proto` property (no parentheses) instead ([Discussion #3992](https://github.com/google/or-tools/discussions/3992)).
- `ObjectiveValue()`, `BestObjectiveBound()`, `NumBranches()`, `NumConflicts()`, `WallTime()` are now properties (no parentheses) ([GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)).

#### New Features

- **`~` operator for literal negation:** Both C++ and Python now support `~var` as an alternative to `var.Not()` for negating Boolean literals ([GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)).
- **`py.typed` marker files:** Enable type checking on the OR-Tools Python package, though initial annotations had issues with strict type checkers ([Issue #4120](https://github.com/google/or-tools/issues/4120)).
- **Math Opt:** Added C++ and Python support via CMake build, included in the Python wheel package ([GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)).

#### Bug Fixes Relevant to CP-SAT

- Improvements to `no_overlap_2d` algorithms (performance/correctness, no API changes) ([GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)).
- Linear propagator code cleanup and optimization ([GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)).

#### Dependency Versions (v9.9)

| Dependency | Version |
|------------|----------|
| abseil-cpp | 20240116.1 |
| Protobuf | v25.3 |
| SCIP | v810 |
| pybind11 | v2.11.1 |
| googletest | 1.14.0 |
| re2 | 2024-02-01 |

Source: [GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)

#### Known Issues

- Windows wheel exceeded PyPI's 108MB file size limit ([GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)).
- Ubuntu 20.04 builds failed due to C++20 header inclusion ([GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)).
- Type annotation issues with strict type checkers (`Call to untyped function "CpModel"`, `Non-overlapping container check`) ([Issue #4120](https://github.com/google/or-tools/issues/4120)).

#### Context

v9.9 was announced as the **last minor release in the 9.x series** before a planned 10.0 major release. The team planned only bugfix releases on the 9.9 branch. `MPSolver` was deprecated starting v9.9 ([Discussion #3992](https://github.com/google/or-tools/discussions/3992)). The routing library was slated for a complete breaking rewrite in 10.0 (pybind11-based).

---

### v9.10 — May 8, 2024

**Release:** [GitHub v9.10](https://github.com/google/or-tools/releases/tag/v9.10) | [Discussion #4232](https://github.com/google/or-tools/discussions/4232)

> Summary from the OR-Tools team: "This is **mostly a CP-SAT bugfix release**." ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10))

#### Breaking Changes (Python-Specific)

- **`new_linear_propagation` default flipped from `false` to `true`:** This is the most impactful behavioral change in 9.10. The new linear propagation code uses a Bellman-Ford-Tarjan adaptation to propagate constraints in a smarter order. This may cause changes in solve times and solution paths for any model with linear constraints ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)). Revert with `solver.parameters.new_linear_propagation = False`.
- **`NewFixedSizedIntervalVar` renamed to `NewFixedSizeIntervalVar`** ("Sized" → "Size" in the CamelCase alias). If using the old name, it will raise `AttributeError` in 9.10+ ([cp_model.py v9.10 diff](https://raw.githubusercontent.com/google/or-tools/v9.10/ortools/sat/python/cp_model.py)). The snake_case name `new_fixed_size_interval_var` is unchanged.
- **Pseudo-cost implementation changed** to be closer to the literature, affecting branching heuristics and potentially altering solver behavior/performance ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)).

#### Deprecations

- No new deprecations beyond those introduced in v9.9.

#### New Features

- **Best bound callback:** A new `solver.best_bound_callback` attribute allows real-time reaction to improvements in the best proven bound ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)):
  ```python
  solver.best_bound_callback = lambda bound: print(f"New best bound: {bound}")
  ```
- **Improved Python typing:** NumPy integer types are now explicitly supported as variable coefficients, bounds, and hint values. `isinstance(x, numbers.Integral)` checks replaced with `isinstance(x, IntegralTypes)` ([cp_model.py v9.10](https://raw.githubusercontent.com/google/or-tools/v9.10/ortools/sat/python/cp_model.py)).
- **New solver parameters:** `shared_tree_open_leaves_per_worker` (default 2.0), `shared_tree_worker_min_restarts_per_subtree` (default 32), `use_lns` (default true), `max_lin_max_size_for_expansion` (default 0) ([sat_parameters.proto v9.10](https://raw.githubusercontent.com/google/or-tools/v9.10/ortools/sat/sat_parameters.proto)).

#### Bug Fixes Relevant to CP-SAT

- **Hint preservation during presolve (partial fix):** Hints set via `model.add_hint()` are now better preserved through the presolve phase. However, this fix was incomplete — complete feasible hints could still become infeasible during model preloading ([Issue #4373](https://github.com/google/or-tools/issues/4373)).
- **Fix crash in `no_overlap_2d` LNS** ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)).
- **Objective setting bug fix:** `vars` and `coeffs` were appended in the wrong order for some `IntVar` objectives in v9.9 — fixed in v9.10 ([cp_model.py v9.10](https://raw.githubusercontent.com/google/or-tools/v9.10/ortools/sat/python/cp_model.py)).
- **Interval variable construction:** Removed redundant internal linear constraint `start + size == end` (was unnecessary and inflated model) ([cp_model.py v9.10](https://raw.githubusercontent.com/google/or-tools/v9.10/ortools/sat/python/cp_model.py)).
- **Merged linear and difference propagators** into a single component ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)).

#### Dependency Versions (v9.10)

| Dependency | Version |
|------------|----------|
| ZLIB | 1.3.1 |
| abseil-cpp | 20240116.2 |
| Protobuf | **v26.1** (breaking for Java) |
| Re2 | 2024-04-01 |
| HiGHS | v1.7.0 |
| SCIP | v900 |
| Gurobi | Added support for Gurobi 11 |

Source: [GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)

#### Known Issues (v9.10)

| Issue | Details |
|-------|---------|
| Windows crashes | Multiple crash reports (#4224–#4227). Fix: ensure Visual Studio is fully updated. ([Issue #4225](https://github.com/google/or-tools/issues/4225)) |
| Java protobuf incompatibility | Protobuf v26.1 is incompatible with Protobuf 3.x Java users |
| Hint preservation incomplete | Hint feasible at presolve start but infeasible at model preloading ([Issue #4373](https://github.com/google/or-tools/issues/4373)) |

---

### v9.11 — September 13, 2024

**Release:** [GitHub v9.11](https://github.com/google/or-tools/releases/tag/v9.11)

#### Breaking Changes (Python-Specific)

- **`num_search_workers` deprecated:** Use `num_workers` instead. `num_search_workers` still works if `num_workers` is 0, but users should migrate ([GitHub v9.11 release](https://github.com/google/or-tools/releases/tag/v9.11)).
- **Callback bug (documented known issue):** CP-SAT callbacks in Python, Java, and .NET can slow down search performance significantly — search may continue until the time limit even after the problem is closed ([GitHub v9.11 release](https://github.com/google/or-tools/releases/tag/v9.11)). Workaround: call `self.stop_search()` explicitly inside `on_solution_callback()`.

#### Deprecations

- `num_search_workers` → `num_workers` ([GitHub v9.11 release](https://github.com/google/or-tools/releases/tag/v9.11)).

#### New Features

- **`no_overlap_2d` improvements:** New parameters `use_linear3_for_no_overlap_2d_precedences` (default true), `no_overlap_2d_boolean_relations_limit` (default 10), `maximum_regions_to_split_in_disconnected_no_overlap_2d` (default 0) ([sat_parameters.proto stable](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto)).
- **LNS tuning parameters:** `lns_initial_difficulty` (default 0.5) and `lns_initial_deterministic_limit` (default 0.1) ([sat_parameters.proto stable](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto)).
- **Debug hint parameter:** `debug_crash_if_presolve_breaks_hint` (tag 306, default false) — crashes if presolve corrupts a feasible hint ([sat_parameters.proto stable](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto)).
- **Platform support:** Added Almalinux 9, Rockylinux 9, Ubuntu 24.04 LTS ([GitHub v9.11 release](https://github.com/google/or-tools/releases/tag/v9.11)).

#### Bug Fixes Relevant to CP-SAT

- Continued improvements to hint preservation (partial) ([Stack Overflow: hint completeness](https://stackoverflow.com/questions/79350475/or-tools-cp-sat-hint-completeness-is-lost-after-presolve)).
- Improved `no_overlap_2d` propagation and linear propagation ([GitHub v9.11 release](https://github.com/google/or-tools/releases/tag/v9.11)).

#### Dependency Versions (v9.11)

| Dependency | Version |
|------------|----------|
| abseil-cpp | 20240722.0 |
| HiGHS | 1.7.2 |
| googletest | v1.15.2 |
| Gurobi | 11.0.3 support added |
| Java | Requires maven 3.6+ |

Source: [GitHub v9.11 release](https://github.com/google/or-tools/releases/tag/v9.11)

#### Known Regressions

- **Memory regression (3-4x):** Multiple users reported significantly higher RAM usage vs. v9.10. A large model used ~15 GB in v9.10 but ~54 GB in v9.11 ([Issue #4406](https://github.com/google/or-tools/issues/4406)).
- **Callback bug:** Confirmed by maintainer — solver continues to time limit even after problem is closed ([Issue #4376](https://github.com/google/or-tools/issues/4376)).
- **Performance regression with hints:** Models with `num_search_workers: 12` and `hint_conflict_limit: 75000` that ran fine in v9.10 ran out of 32 GB RAM in v9.11 ([Google Groups discussion](https://groups.google.com/g/or-tools-discuss/c/FO8-jCNVjPQ)).

---

### v9.12 — February 17, 2025

**Release:** [GitHub v9.12](https://github.com/google/or-tools/releases/tag/v9.12) | [Discussion #4544](https://github.com/google/or-tools/discussions/4544)

#### Breaking Changes (Python-Specific)

- **LinearExpr layer moved to C++/pybind11:** The `LinearExpr` class and subclasses (`_Sum`, `_ProductCst`, `_SumArray`, `_WeightedSum`, `_NotBooleanVariable`, `BoundedLinearExpression`) were removed from `cp_model.py` and replaced with compiled helpers from `cp_model_helper` (pybind11 C++ extension) ([Fossies diff 9.11→9.12](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/python/cp_model.py-diff.html)). Code that subclasses `LinearExpr` directly, uses `isinstance(var, cp_model.LinearExpr)`, or accesses internal attributes of `BoundedLinearExpression` may break.
- **`swig_helper` removed:** `ortools/sat/python/swig_helper.cc` removed entirely. Any code importing `from ortools.sat.python import swig_helper` will fail ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).
- **`add_automaton()` parameter renamed:** `transition_variables` → `transition_expressions` (now accepts 1-variable affine expressions) ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).
- **`add_element()` parameter renamed:** `variables` → `expressions` (now accepts affine expressions for index, expressions, and target) ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).
- **`shared_tree_max_nodes_per_worker` default changed:** 100,000 → 10,000 (10x reduction), affecting parallel search dynamics ([sat_parameters.proto diff](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/sat_parameters.proto-diff.html)).
- **`use_lb_relax_lns` default changed:** `false` → `true` — LB-relax LNS now active by default ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).
- **IntVar class hierarchy changed:** `IntVar` no longer inherits from Python `LinearExpr`; it now inherits from `cmh.BaseIntVar` (C++ base class). Public method names are unchanged ([Fossies diff](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/python/cp_model.py-diff.html)).

#### Deprecations

- CamelCase shims from v9.9 remain. No new deprecations announced.
- This is the **last release supporting Python 3.8** — Python 3.8 drops in 9.13 ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).

#### New Features

- **Hint system fully rewritten:** Complete rewrite of hint transformation during presolve. Feasible and complete hints now survive presolve correctly. New internal files `solution_crush.cc` and `combine_solutions.cc` implement the revised mechanism ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).
- **`RandomHalfBranching`:** New search branching strategy added to the portfolio ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).
- **Experimental symmetry parameters:** `use_symmetry_in_lp` (default false), `keep_symmetry_in_presolve` (default false), `symmetry_detection_deterministic_time_limit` (default 1.0) ([sat_parameters.proto diff](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/sat_parameters.proto-diff.html)).
- **`evaluate_linear_expr()` and `evaluate_boolean_expression()`:** New top-level utility functions for evaluating expressions against a solution response ([Fossies diff](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/python/cp_model.py-diff.html)).
- **Python 3.13 support:** New wheel packages for Python 3.13, plus `musllinux` wheels for Alpine ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).
- **Cumulative constraint improvements:** Better propagation algorithms and new cuts for scheduling ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).
- **20+ new solver parameters** including LNS tuning, routing cuts, symmetry, inprocessing, and shared tree controls ([sat_parameters.proto diff](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/sat_parameters.proto-diff.html)).
- **C API added:** New `ortools/sat/c_api/` directory with C language bindings for CP-SAT ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).
- **Go and Julia bindings:** Go bindings moved to `ortools/sat/go/cpmodel/`; initial Julia bindings added ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).

#### Dependency Versions (v9.12)

| Dependency | Version |
|------------|----------|
| Protobuf | 29.3 |
| HiGHS | 1.9.0 |
| SCIP | v920 |
| abseil-cpp | 20240722.0 (unchanged) |
| Clp | 1.17.10 |
| Cbc | 2.10.12 |

Source: [GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)

#### Bug Fixes Relevant to CP-SAT

- **Hint preservation fully fixed:** The longstanding regression where hints were lost during presolve (reported since v9.8, partially fixed in v9.10/v9.11) is now resolved ([Stack Overflow: hint completeness](https://stackoverflow.com/questions/79350475/or-tools-cp-sat-hint-completeness-is-lost-after-presolve)).
- **"Tens of fixes" from fuzzing:** Improved robustness for edge cases ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).
- **Feasibility jump speedup:** Faster first-solution heuristic ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).

---

## 2. API Compatibility Scan

The following table maps every OR-Tools API call found in the codebase to its v9.12 status and required migration action.

### Legend

| Status | Meaning |
|--------|---------|
| **OK** | Unchanged; works identically in 9.12 |
| **DEPRECATED** | CamelCase shim still works but is deprecated; snake_case preferred |
| **REMOVED** | No longer exists in 9.12 |
| **CHANGED** | Signature or behavior changed |

### API Compatibility Table

| API Call | File(s) | Line(s) | 9.12 Status | Migration Action |
|----------|---------|---------|-------------|------------------|
| **`CpModel()` constructor** | solvers.py | 833 | OK | No change needed |
| | activity_solver.py | 735 | OK | No change needed |
| | fair_call_optimizer.py | 103 | OK | No change needed |
| **`NewBoolVar`** | solvers.py | 870, 886, 906, 920, 956, 990, 991, 996, 997 | DEPRECATED | Rename to `new_bool_var` |
| | activity_solver.py | 946, 2075, 2102, 2174, 2185, 2269 | DEPRECATED | Rename to `new_bool_var` |
| | fair_call_optimizer.py | 130 | DEPRECATED | Rename to `new_bool_var` |
| | call_equity.py | 1304, 1305, 1312 | DEPRECATED | Rename to `new_bool_var` |
| **`NewIntVar`** | solvers.py | 1173, 1357 | DEPRECATED | Rename to `new_int_var` |
| | activity_solver.py | 1395, 1405, 1473, 1481, 1559, 1569, 1649, 1660, 1663, 1669, 1726, 1727, 1731, 1757, 1797, 1875, 1906, 2000, 2062, 2079, 2159, 2325, 2331 | DEPRECATED | Rename to `new_int_var` |
| | fair_call_optimizer.py | 136, 145, 152, 157 | DEPRECATED | Rename to `new_int_var` |
| | call_equity.py | 126, 321, 528 | DEPRECATED | Rename to `new_int_var` |
| **`Add`** | solvers.py | 888, 889, 922, 1084, 1099, 1119, 1121, 1123, 1125, 1144, 1170, 1178, 1228, 1237, 1242, 1245, 1304, 1330, 1361 | DEPRECATED | Rename to `add` |
| | activity_solver.py | 1043, 1390, 1400, 1410, 1413, 1467, 1478, 1486, 1564, 1574, 1654, 1667, 1668, 1672, 1729, 1730, 1732, 1762, 1802, 1880, 1911, 2005, 2067, 2084, 2178, 2183, 2189, 2322, 2330 | DEPRECATED | Rename to `add` |
| | fair_call_optimizer.py | 165, 177, 184, 198, 202, 204, 207, 214, 258, 262 | DEPRECATED | Rename to `add` |
| | call_equity.py | 134, 331, 538 | DEPRECATED | Rename to `add` |
| **`AddMaxEquality`** | activity_solver.py | 2078, 2177, 2188, 2272, 2336 | DEPRECATED | Rename to `add_max_equality` |
| | call_equity.py | 1308, 1309 | DEPRECATED | Rename to `add_max_equality` |
| **`AddMultiplicationEquality`** | call_equity.py | 1313 | DEPRECATED | Rename to `add_multiplication_equality` |
| **`OnlyEnforceIf`** | solvers.py | 888, 889 | DEPRECATED | Rename to `only_enforce_if` |
| **`.Not()`** | solvers.py | 890, 923 | OK | Still works; `~var` is the modern alternative |
| **`Maximize`** | solvers.py | 1377 | DEPRECATED | Rename to `maximize` |
| | activity_solver.py | 2588 | DEPRECATED | Rename to `maximize` |
| **`Minimize`** | fair_call_optimizer.py | 228, 262 | DEPRECATED | Rename to `minimize` |
| **`Proto()`** | solvers.py | 1382, 1527 | DEPRECATED | Use `model.proto` property (remove parentheses) |
| **`CpSolver()` constructor** | solvers.py | 1452 | OK | No change needed |
| | activity_solver.py | 2593 | OK | No change needed |
| | fair_call_optimizer.py | 230, 264, 377 | OK | No change needed |
| **`Solve()`** | solvers.py | 1475, 1477 | DEPRECATED | Rename to `solve()` |
| | activity_solver.py | 2597 | DEPRECATED | Rename to `solve()` |
| | fair_call_optimizer.py | 234, 268, 379 | DEPRECATED | Rename to `solve()` |
| | solver_streaming.py | 26, 115 | DEPRECATED | Rename to `solve()` |
| **`Value()`** | solvers.py | 1602, 1621, 1638, 1669, 1671, 1675, 1677 | DEPRECATED | Rename to `value()` |
| | activity_solver.py | 2743, 2775, 2788, 2789, 2799, 2808, 2816, 2823, 2830, 2838, 2844, 2850, 2856 | DEPRECATED | Rename to `value()` |
| | fair_call_optimizer.py | 238, 291, 306, 380, 392, 407 | DEPRECATED | Rename to `value()` |
| | solver_streaming.py | 234 | DEPRECATED | Rename to `value()` |
| **`ObjectiveValue()`** | solvers.py | 634, 1488, 1705 | DEPRECATED | Use `solver.objective_value` property (remove parens) |
| | fair_call_optimizer.py | 272, 418, 427 | DEPRECATED | Use `solver.objective_value` property (remove parens) |
| | solver_streaming.py | 187 | DEPRECATED | Use `solver.objective_value` property (remove parens) |
| **`BestObjectiveBound()`** | solvers.py | 635, 1493 | DEPRECATED | Use `solver.best_objective_bound` property (remove parens) |
| | solver_streaming.py | 188 | DEPRECATED | Use `solver.best_objective_bound` property (remove parens) |
| **`StatusName()`** | solvers.py | 1484, 1517 | DEPRECATED | Rename to `status_name()` |
| | activity_solver.py | 2600 | DEPRECATED | Rename to `status_name()` |
| | fair_call_optimizer.py | 237, 271 | DEPRECATED | Rename to `status_name()` |
| **`NumBranches()`** | solvers.py | 1721 | DEPRECATED | Use `solver.num_branches` property (remove parens) |
| **`NumConflicts()`** | solvers.py | 1722 | DEPRECATED | Use `solver.num_conflicts` property (remove parens) |
| **`WallTime()`** | fair_call_optimizer.py | 239, 273 | DEPRECATED | Use `solver.wall_time` property (remove parens) |
| **`CpSolverSolutionCallback`** | solvers.py | 620 | OK | Class name unchanged |
| | solver_streaming.py | 159 | OK | Class name unchanged |
| **`on_solution_callback`** | solvers.py | 628 | OK | Already using snake_case |
| | solver_streaming.py | 166 | OK | Already using snake_case |
| **`cp_model.OPTIMAL / FEASIBLE / INFEASIBLE`** | solvers.py | 1489, 1494, 1497, 1498, 1502, 1518, 1704 | OK | Unchanged |
| | activity_solver.py | 2603, 2863 | OK | Unchanged |
| | fair_call_optimizer.py | 238, 272, 361, 387, 411, 478, 480, 482 | OK | Unchanged |
| **`max_time_in_seconds`** | solvers.py | 1453 | OK | Unchanged |
| | activity_solver.py | 2594 | OK | Unchanged |
| | fair_call_optimizer.py | 231, 265, 378 | OK | Unchanged |
| **`num_search_workers`** | solvers.py | 1454 | DEPRECATED | Replace with `num_workers` |
| | activity_solver.py | 2595 | DEPRECATED | Replace with `num_workers` |
| **`log_search_progress`** | fair_call_optimizer.py | 232, 266 | OK | Unchanged |

### Call Site Counts by File

The following table summarizes the number of deprecated API call sites per file:

| File | Deprecated Call Sites | OK Call Sites | Total |
|------|----------------------|---------------|-------|
| `solvers.py` | ~55 | ~15 | ~70 |
| `activity_solver.py` | ~65 | ~5 | ~70 |
| `fair_call_optimizer.py` | ~28 | ~10 | ~38 |
| `call_equity.py` | ~12 | 0 | ~12 |
| `solver_streaming.py` | ~7 | ~3 | ~10 |
| **Total** | **~167** | **~33** | **~200** |

### CamelCase → snake_case Quick-Reference

For the rename task, here is the complete sed substitution list for this codebase:

```bash
# CpModel methods
sed -i 's/\.NewBoolVar(/.new_bool_var(/g' *.py
sed -i 's/\.NewIntVar(/.new_int_var(/g' *.py
sed -i 's/\.Add(/.add(/g' *.py
sed -i 's/\.AddMaxEquality(/.add_max_equality(/g' *.py
sed -i 's/\.AddMultiplicationEquality(/.add_multiplication_equality(/g' *.py
sed -i 's/\.OnlyEnforceIf(/.only_enforce_if(/g' *.py
sed -i 's/\.Maximize(/.maximize(/g' *.py
sed -i 's/\.Minimize(/.minimize(/g' *.py

# CpSolver methods
sed -i 's/\.Solve(/.solve(/g' *.py
sed -i 's/\.Value(/.value(/g' *.py
sed -i 's/\.StatusName(/.status_name(/g' *.py

# CpSolver properties (remove parentheses)
sed -i 's/\.ObjectiveValue()/.objective_value/g' *.py
sed -i 's/\.BestObjectiveBound()/.best_objective_bound/g' *.py
sed -i 's/\.NumBranches()/.num_branches/g' *.py
sed -i 's/\.NumConflicts()/.num_conflicts/g' *.py
sed -i 's/\.WallTime()/.wall_time/g' *.py

# CpModel property
sed -i 's/\.Proto()/.proto/g' *.py

# Solver parameter
sed -i 's/num_search_workers/num_workers/g' *.py
```

> **Caution:** The `sed` for `.Add(` is aggressive — verify it doesn't match non-OR-Tools `.Add(` calls. The `.Solve(` substitution may also match other solver libraries. Review diffs carefully after applying.

### Summary

**19 of 25 unique API calls are DEPRECATED** (CamelCase shims). All shims still work in 9.12 — no hard breakage. **0 calls are REMOVED.** 6 API calls (`CpModel()`, `CpSolver()`, `.Not()`, `CpSolverSolutionCallback`, `on_solution_callback`, `cp_model.OPTIMAL/FEASIBLE/INFEASIBLE`, `max_time_in_seconds`, `log_search_progress`) are fully OK with no changes needed.

The deprecated calls span ~200 call sites across 5 files. Since all CamelCase shims are retained in v9.12, there is **zero hard breakage** on upgrade ([OR-Tools API docs](https://or-tools.github.io/docs/pdoc/ortools/sat/python/cp_model.html)). The rename to snake_case is recommended but not blocking.

---

## 3. Hint System Evolution

### 3.1 Bug Timeline

The CP-SAT hint system has undergone significant changes from v9.8 to v9.12, centered on a longstanding regression where hints set via `model.add_hint()` were lost or corrupted during the presolve phase.

| Version | Date | Hint Preservation Status | Key Event |
|---------|------|--------------------------|-----------|
| **v9.7** | Aug 2023 | Working (baseline) | Hints survive presolve correctly |
| **v9.8** | Nov 2023 | **Regression introduced** | Performance degradation with hints; "Reduce memory footprint for large model" change interacts poorly with hints ([Issue #4166](https://github.com/google/or-tools/issues/4166)) |
| **v9.9** | Mar 2024 | **Completeness lost after presolve** | Complete, feasible hints become incomplete/infeasible after presolve. `AddHint` renamed to `add_hint` as part of PEP8 rewrite. No semantic fix. ([Stack Overflow](https://stackoverflow.com/questions/79350475/or-tools-cp-sat-hint-completeness-is-lost-after-presolve)) |
| **v9.10** | May 2024 | **Partial fix** | "Preserve hints during presolve" — first dedicated fix. Hint preserved through CP presolve but still broken during model preloading stage ([Issue #4373](https://github.com/google/or-tools/issues/4373)) |
| **v9.11** | Sep 2024 | **Further improvements** | Additional hint preservation work; issues still reproducible. Laurent Perron: "It has been much improved in 9.11" ([Stack Overflow](https://stackoverflow.com/questions/79350475/or-tools-cp-sat-hint-completeness-is-lost-after-presolve)) |
| **v9.12** | Feb 2025 | **Full rewrite — fixed** | "Rewrote the hint transformation during presolve. Feasible and complete hints should now be preserved after presolve." New `solution_crush.cc` implements revised mechanism. ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)) |

### 3.2 What Changed in Each Version

| Version | Hint API Change | Presolve Behavior | Solver Log |
|---------|----------------|-------------------|------------|
| v9.8 | `AddHint()` only | Hints may be lost during presolve | `The solution hint is incomplete: N out of M non fixed variables hinted.` |
| v9.9 | Renamed to `add_hint()`; CamelCase shim kept | Same regression as v9.8 | Same as v9.8 |
| v9.10 | No API change | Hints better preserved through CP presolve; still broken at preloading | `The solution hint is complete and is feasible.` → then `complete, but infeasible!` at preloading |
| v9.11 | No API change | Further improvements; incomplete hints now handled better | `The solution hint is incomplete: 374 out of 6974 non fixed variables hinted.` — but solution found easily |
| v9.12 | No API change | **Fully rewritten.** Complete hints survive presolve. | `#1 1.51s best:891360 next:[526660,891359] complete_hint` — hint used immediately |

### 3.3 Parameters That Affect Hints

| Parameter | Proto Tag | Default | Purpose | Version Notes |
|-----------|-----------|---------|---------|---------------|
| `repair_hint` | 167 | `false` | When true, actively repairs infeasible hints via neighborhood search rather than simple FIXED_SEARCH ([sat_parameters.proto](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto)) | Available since v9.8; edge case with late exit reported post-v9.12 ([Issue #4743](https://github.com/google/or-tools/issues/4743)) |
| `hint_conflict_limit` | 153 | `10` | Max conflicts during hint exploitation phase before switching to regular search ([sat_parameters.proto](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto)) | Default of 10 is very conservative; increase for complex hints |
| `fix_variables_to_their_hinted_value` | 192 | `false` | Fixes hinted variables to their values (hint becomes hard constraint). Recommended for hint feasibility verification. ([sat_parameters.proto](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto)) | Unchanged across versions |
| `keep_all_feasible_solutions_in_presolve` | 173 | `false` | Disables presolve reductions that remove feasible solutions. Prevents hint infeasibility at a performance cost. ([sat_parameters.proto](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto)) | May no longer be needed in v9.12 |
| `max_presolve_iterations` | 138 | `3` | Max presolve iterations. Reducing this limits hint transformation risk. ([sat_parameters.proto](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto)) | Default unchanged; current workaround sets to 3 (already the default) |
| `debug_crash_if_presolve_breaks_hint` | 306 | `false` | **New in v9.12.** Crashes solver if presolve corrupts a feasible hint. Useful during testing only. ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)) | Testing/CI use only |

### 3.4 Impact on This Codebase

The scheduling system uses hints for two-phase solving, but **no `AddHint` / `add_hint` calls appear in the uploaded solver files** — they are likely in a higher-level orchestration layer that passes hint data into the model before invoking the solver.

The current workaround (`repair_hint=True` + `max_presolve_iterations=3`) was implemented to mitigate the v9.8 hint preservation regression. Since `max_presolve_iterations` defaults to 3 anyway, the effective workaround is primarily `repair_hint=True`.

**With v9.12:** The root cause — hint corruption during presolve — is fixed by the complete rewrite of hint transformation logic ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)). The workaround should be re-tested and likely removed.

### 3.5 Recommended Code Diff

```python
# ============================================================
# BEFORE (9.8 workaround — hint setup area in orchestration layer)
# ============================================================
solver.parameters.repair_hint = True
solver.parameters.max_presolve_iterations = 3
# Additional workarounds for hint preservation:
# solver.parameters.keep_all_feasible_solutions_in_presolve = True  # if needed

# ============================================================
# AFTER (9.12 — workarounds can be removed)
# ============================================================
# Hint preservation is now handled correctly by the solver.
# The presolve hint transformation was fully rewritten in v9.12.
# Remove repair_hint workaround; test with default presolve.

# Optionally enable debug parameter during testing:
solver.parameters.debug_crash_if_presolve_breaks_hint = True  # testing only

# solver.parameters.repair_hint = True               # REMOVE — no longer needed
# solver.parameters.max_presolve_iterations = 3       # REMOVE — use default (3)
# solver.parameters.keep_all_feasible_solutions_in_presolve = True  # REMOVE if present
```

### 3.6 Best Practices for v9.12

1. **Always call `clear_hints()` before re-hinting** to avoid accumulating stale or duplicate hint entries. There is no uniqueness check — calling `add_hint(x, 1)` twice adds two entries ([CP-SAT Primer](https://d-krupke.github.io/cpsat-primer/06_coding_patterns.html)).

2. **Provide complete hints for best performance.** A hint covering all variables and satisfying all constraints is treated fundamentally differently from a partial hint. The solver log will show `complete_hint` when the hint is used directly as the first solution ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).

3. **Use `fix_variables_to_their_hinted_value` for debugging** hint feasibility:
   ```python
   solver.parameters.fix_variables_to_their_hinted_value = True
   status = solver.solve(model)
   if status == cp_model.INFEASIBLE:
       print("Hints are conflicting or infeasible!")
   ```
   This is more reliable than `debug_crash_on_bad_hint` which depends on race conditions in multi-worker mode ([Issue #4166](https://github.com/google/or-tools/issues/4166)).

4. **Enable `debug_crash_if_presolve_breaks_hint` in CI/testing** to catch any remaining presolve issues:
   ```python
   solver.parameters.debug_crash_if_presolve_breaks_hint = True  # CI only
   ```

5. **Monitor hint usage in logs** by enabling `solver.parameters.log_search_progress = True` and looking for `complete_hint`, `[hint]`, or `fixed_bools:N/M` in the output ([CP-SAT Primer](https://d-krupke.github.io/cpsat-primer/05_parameters.html)).

---

## 4. Solver Behavioral Changes

### 4.1 Search Strategy Changes

| Change | Version | Details | Impact on This Codebase |
|--------|---------|---------|------------------------|
| Pseudo-cost implementation changed | v9.10 | Changed to match literature, affecting branching order and variable selection heuristics ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)) | Solution paths may differ; the same model may find different feasible solutions first. Scheduling objectives may reach different intermediate states. |
| Linear + difference propagator merged | v9.10 | Two formerly separate propagators unified into one ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)) | Internal architectural change; may affect propagation order for linear/difference constraints (common in scheduling). |
| `RandomHalfBranching` added to portfolio | v9.12 | New search branching strategy included in the automatic portfolio. Can be excluded via `ignore_subsolvers` if needed. ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)) | Additional worker strategy; may find solutions in different order. |
| Improved `lb_tree_search` | v9.10 | Enhancements to the lower bound tree search worker ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)) | May improve lower bound convergence for the scheduling objective. |
| Improved core-based search | v9.10 | Improvements to UNSAT core-based optimization ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)) | Beneficial for problems with many soft constraints (this codebase has 25+). |

**Impact Summary:** Solution paths may differ from v9.8 even with identical inputs. The same model may find different feasible solutions first, and the sequence of improving solutions during search may change. Objective values at timeout may differ.

### 4.2 LP Relaxation Changes

| Change | Version | Old Default | New Default | Details |
|--------|---------|-------------|-------------|---------|
| `new_linear_propagation` | v9.10 | `false` | **`true`** | New code treats all linear constraints at once and uses Bellman-Ford-Tarjan to propagate constraints in a smarter order and detect propagation cycles earlier ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)) |

**Impact for this scheduling system:** Linear constraints are pervasive in this codebase — every `model.Add(expr ≤ bound)` call creates a linear constraint. With ~4,000 binary variables and 25+ soft constraints, this change is likely to affect solve behavior. The new propagator may improve performance on well-structured linear models or degrade it on models where the old propagator's ordering happened to be favorable.

**Mitigation:** If performance degrades after upgrade, revert to old behavior:
```python
solver.parameters.new_linear_propagation = False
```
Note that the old propagator is being phased out and may be removed in a future version ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)).

### 4.3 Symmetry Handling

| Parameter | Version | Default | Description |
|-----------|---------|---------|-------------|
| `use_symmetry_in_lp` | v9.12 | `false` | Folds orbit variables in the LP relaxation ([sat_parameters.proto diff](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/sat_parameters.proto-diff.html)) |
| `keep_symmetry_in_presolve` | v9.12 | `false` | Computes symmetry once and preserves it through presolve ([sat_parameters.proto diff](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/sat_parameters.proto-diff.html)) |
| `symmetry_detection_deterministic_time_limit` | v9.12 | `1.0` | Time budget for symmetry detection ([sat_parameters.proto diff](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/sat_parameters.proto-diff.html)) |

**Not enabled by default.** Could be beneficial for this scheduling problem where residents may be partially symmetric (e.g., same seniority level, similar constraints). Enabling `use_symmetry_in_lp` and `keep_symmetry_in_presolve` is worth testing to see if it reduces solve time by exploiting resident interchangeability.

**Example: Enabling symmetry for resident scheduling:**

```python
# Experimental — test with and without on representative instances
solver.parameters.use_symmetry_in_lp = True
solver.parameters.keep_symmetry_in_presolve = True
solver.parameters.symmetry_detection_deterministic_time_limit = 2.0  # increase budget for larger models
```

**When symmetry helps:** If residents A and B have identical constraint profiles (same seniority, same eligible rotations, same availability), the solver can detect this symmetry and reduce the effective search space. With 12 residents, there may be 2-3 groups of interchangeable residents.

### 4.4 Determinism

- **Same `num_workers` + same model = deterministic:** This property is unchanged across all versions ([CP-SAT Primer](https://d-krupke.github.io/cpsat-primer/05_parameters.html)).
- **Behavioral changes from new defaults mean results may differ from v9.8** even with the same inputs. The pseudo-cost change, the `new_linear_propagation` default flip, and the `use_lb_relax_lns` default flip all alter the solver's internal decision-making.
- **Parameters to control for reproducibility:** To match v9.8 behavior as closely as possible:
  ```python
  solver.parameters.new_linear_propagation = False  # revert v9.10 default change
  solver.parameters.use_lb_relax_lns = False         # revert v9.12 default change
  ```

### 4.5 Default Value Changes (CRITICAL)

| Parameter | Version Changed | Old Default | New Default | Impact |
|-----------|----------------|-------------|-------------|--------|
| `new_linear_propagation` | v9.10 | `false` | **`true`** | May change solve times significantly. Uses Bellman-Ford-Tarjan propagation for all linear constraints. ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)) |
| `use_lb_relax_lns` | v9.12 | `false` | **`true`** | LB-relax LNS worker now active by default. May improve lower bound convergence but changes search dynamics. Only used when at least `lb_relax_num_workers_threshold` (default 16) workers are active. ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)) |
| `shared_tree_max_nodes_per_worker` | v9.12 | `100000` | **`10000`** | 10x reduction. Shared tree uses smaller subtrees, increasing load-balancing overhead but improving worker coordination. ([sat_parameters.proto diff](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/sat_parameters.proto-diff.html)) |

**Note for this codebase:** The `use_lb_relax_lns` change only activates when 16+ workers are running. With `num_search_workers` likely set to 8-12 for this system, this change may have no effect unless the system is configured for higher parallelism. The `new_linear_propagation` change is the most impactful and should be tested first.

### 4.6 Known Regressions

| Regression | Version | Description | Mitigation |
|------------|---------|-------------|------------|
| **Memory regression (3-4x)** | v9.11 | Some models use significantly more RAM. A large model used ~15 GB in v9.10 but ~54 GB in v9.11. ([Issue #4406](https://github.com/google/or-tools/issues/4406)) | Reduce `num_workers` to lower memory footprint; test with production-size instances before deploying. |
| **Callback bug** | v9.11 | Search continues to time limit even after problem is closed when using Python callbacks. Confirmed by maintainer. ([Issue #4376](https://github.com/google/or-tools/issues/4376)) | Call `self.stop_search()` explicitly inside `on_solution_callback()`. |
| **Hint + memory** | v9.11 | Models with `hint_conflict_limit: 75000` and `num_search_workers: 12` that ran fine in v9.10 exhausted 32 GB RAM in v9.11. ([Google Groups](https://groups.google.com/g/or-tools-discuss/c/FO8-jCNVjPQ)) | Reduce `hint_conflict_limit` or test on v9.12 where hint handling was rewritten. |

**Impact on this codebase:**

- The `SolverProgressCallback` (solvers.py:620) and `_StreamingCallback` (solver_streaming.py:159) both use `ObjectiveValue()` inside `on_solution_callback`. Due to the v9.11 callback bug, these callbacks may cause the solver to run to the full time limit even after finding an optimal solution. **Verify that `stop_search()` is called explicitly** when the desired solution quality is reached.

- Recommended callback pattern for v9.12:

```python
# BEFORE (v9.8 pattern — may trigger callback bug in v9.11+):
class SolverProgressCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._solution_count = 0

    def on_solution_callback(self):
        self._solution_count += 1
        obj = self.ObjectiveValue()  # deprecated CamelCase
        bound = self.BestObjectiveBound()  # deprecated CamelCase
        print(f"Solution {self._solution_count}: obj={obj}, bound={bound}")
        # BUG: No stop_search() call — solver may continue to time limit

# AFTER (v9.12 pattern — explicit stop + snake_case):
class SolverProgressCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self, target_gap=0.01):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._solution_count = 0
        self._target_gap = target_gap

    def on_solution_callback(self):
        self._solution_count += 1
        obj = self.objective_value      # property (no parens)
        bound = self.best_objective_bound  # property (no parens)
        print(f"Solution {self._solution_count}: obj={obj}, bound={bound}")

        # Explicitly stop when gap is small enough
        if bound > 0 and abs(obj - bound) / abs(bound) < self._target_gap:
            self.stop_search()  # CRITICAL for v9.11+ callback bug
```

- With ~4,000 binary variables and ~12 residents, the memory regression may not be as severe as with larger models, but it should still be validated with production-size instances.

---

## 5. New Features for Scheduling

### 5.1 Best Bound Callback (v9.10)

The new `solver.best_bound_callback` attribute fires whenever the proven bound improves, independent of solution callbacks which fire on new feasible solutions ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)).

**Relevance to this codebase:** The two-phase solving pattern in `fair_call_optimizer.py` uses phase 1 for initial feasibility and phase 2 for optimization. The best bound callback could replace phase 1 early termination logic by stopping search when the proven bound reaches a threshold:

```python
solver = cp_model.CpSolver()

def bound_callback(bound: float) -> None:
    """Stop search when proven bound reaches phase 1 threshold."""
    if bound >= phase_1_threshold:
        solver.stop_search()

solver.best_bound_callback = bound_callback
status = solver.solve(model)
```

This is cleaner than polling inside a solution callback and triggers on bound improvement rather than solution improvement ([CP-SAT Primer](https://d-krupke.github.io/cpsat-primer/05_parameters.html)).

**Extended example for two-phase solving:**

```python
# Phase 1: Quick feasibility — stop when bound proves objective can't improve much
def phase1_bound_callback(bound: float) -> None:
    """Stop when proven bound exceeds the phase 1 feasibility threshold."""
    if bound >= phase_1_target:
        print(f"Phase 1 complete: proven bound {bound} >= target {phase_1_target}")
        solver.stop_search()

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_workers = 8
solver.best_bound_callback = phase1_bound_callback
status = solver.solve(model)

# Phase 2: Full optimization with time limit
solver.best_bound_callback = None  # clear phase 1 callback
solver.parameters.max_time_in_seconds = 120.0
status = solver.solve(model)
```

This pattern avoids the need to check objective values inside `on_solution_callback` for early termination and provides a cleaner separation of concerns between solution monitoring and bound monitoring.

### 5.2 `~` Operator for Negation (v9.9)

The `~` operator provides a cleaner syntax for negating Boolean literals, replacing the `.Not()` method ([GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)):

```python
# BEFORE (solvers.py lines 890, 923):
model.Add(x > 0).OnlyEnforceIf(b.Not())

# AFTER:
model.add(x > 0).only_enforce_if(~b)
```

Functionally identical; `~var` is syntactic sugar for `var.negated()` which is the same as `var.Not()`.

### 5.3 Hint System Improvements (v9.12)

- **Complete hints** now show as `complete_hint` in the solver log, confirming the hint was used directly as the first solution ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).
- **`debug_crash_if_presolve_breaks_hint`** (new in v9.12) enables crash-on-failure during testing to catch any remaining hint corruption ([sat_parameters.proto diff](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/sat_parameters.proto-diff.html)).
- **`repair_hint` workaround can be removed** since the root cause (hint corruption during presolve) is fixed by the rewrite of hint transformation logic ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)).

### 5.4 LNS Tuning Parameters (v9.12)

Two new parameters control Large Neighborhood Search initialization ([sat_parameters.proto stable](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto)):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `lns_initial_difficulty` | `0.5` | Controls initial neighborhood size. Lower values create smaller neighborhoods (faster but less diverse). |
| `lns_initial_deterministic_limit` | `0.1` | Time budget per LNS iteration in deterministic time units. |

**For this scheduling system:** If LNS is slow on early iterations (observable via `log_search_progress`), try reducing `lns_initial_difficulty` to 0.3 for faster early convergence, or increasing to 0.7 for more diverse exploration.

### 5.5 Cumulative Constraint Improvements (v9.12)

Better propagation algorithms and new cuts for the cumulative constraint ([GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)). This is relevant if the scheduling system uses `add_cumulative()` for room or resource capacity constraints. The improvements are internal — no API changes, just better performance and tighter bounds.

### 5.6 `evaluate_linear_expr` / `evaluate_boolean_expression` (v9.12)

New top-level utility functions for evaluating expressions against a solution response without needing a solver instance ([Fossies diff](https://fossies.org/diffs/or-tools/9.11_vs_9.12/ortools/sat/python/cp_model.py-diff.html)):

```python
from ortools.sat.python.cp_model import evaluate_linear_expr, evaluate_boolean_expression

# Evaluate a linear expression against a raw response proto
value = evaluate_linear_expr(2 * x + y, response_proto)
is_true = evaluate_boolean_expression(b, response_proto)
```

**For this codebase:** Could simplify solution extraction code in `solvers.py` and `activity_solver.py` where many `solver.Value()` calls are used. Particularly useful if solution responses are stored and re-evaluated later without a live solver instance.

```python
from ortools.sat.python.cp_model import evaluate_linear_expr, evaluate_boolean_expression

# Example: Evaluate schedule assignments from a stored response
def extract_schedule_from_response(model, response, residents, blocks, assignments):
    """Extract schedule data from a stored CpSolverResponse without a solver instance."""
    schedule = {}
    for r in residents:
        for b in blocks:
            var = assignments[r, b]
            if evaluate_boolean_expression(var, response):
                schedule[(r, b)] = True
    return schedule

# Example: Evaluate a weighted objective expression
total_penalty = evaluate_linear_expr(penalty_expr, response)
print(f"Total schedule penalty: {total_penalty}")
```

This decouples solution extraction from the solver lifecycle, which is useful for post-processing, logging, and testing.

### 5.7 Solver Parameter: `num_workers` (preferred over `num_search_workers`)

The `num_search_workers` parameter is deprecated in favor of `num_workers` ([GitHub v9.11 release](https://github.com/google/or-tools/releases/tag/v9.11)):

```python
# BEFORE (solvers.py:1454, activity_solver.py:2595):
solver.parameters.num_search_workers = 8

# AFTER:
solver.parameters.num_workers = 8
```

`num_search_workers` still works if `num_workers` is 0, but `num_workers` is the canonical name going forward. The two parameters control the same underlying behavior — total number of parallel workers.

---

## 6. Migration Checklist

### Migration Checklist: OR-Tools CP-SAT 9.8 → 9.12

#### Phase 1: Critical (Before Merge)

- [ ] **HIGH** — Update version pin from `ortools>=9.8,<9.9` to `ortools>=9.12,<9.13`  
  **Files:** `requirements.txt` / `pyproject.toml`  
  **Risk:** All downstream changes flow from this. Test thoroughly in staging before production.  
  **Source:** [GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)

- [ ] **HIGH** — Test hint preservation — remove `repair_hint=True` and `max_presolve_iterations` workarounds, verify hints survive presolve  
  **Files:** Hint configuration code (orchestration layer)  
  **Risk:** The v9.8 hint regression is the original motivation for the workaround. v9.12 rewrites hint transformation entirely. Test by enabling `debug_crash_if_presolve_breaks_hint=True` during validation, then remove the workaround if hints pass.  
  **Source:** [GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12), [Stack Overflow](https://stackoverflow.com/questions/79350475/or-tools-cp-sat-hint-completeness-is-lost-after-presolve)

- [ ] **HIGH** — Verify callback behavior — `SolverProgressCallback` and `_StreamingCallback` may run to time limit due to v9.11 callback bug; add explicit `stop_search()` calls  
  **Files:** `solvers.py:628`, `solver_streaming.py:166`  
  **Risk:** Without `stop_search()`, callbacks may cause the solver to continue searching past the point where the problem is closed, wasting compute time.  
  **Source:** [Issue #4376](https://github.com/google/or-tools/issues/4376), [GitHub v9.11 release](https://github.com/google/or-tools/releases/tag/v9.11)

#### Phase 2: Medium Priority (First Sprint)

- [ ] **MEDIUM** — Run performance benchmark — `new_linear_propagation` default change + pseudo-cost change may affect solve times  
  **Files:** All solver files (`solvers.py`, `activity_solver.py`, `fair_call_optimizer.py`, `solver_streaming.py`)  
  **Risk:** Solve times may increase or decrease. Compare 9.8 vs. 9.12 on representative scheduling instances. If performance degrades, set `solver.parameters.new_linear_propagation = False` as a fallback.  
  **Source:** [GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)

- [ ] **MEDIUM** — Replace `num_search_workers` with `num_workers`  
  **Files:** `solvers.py:1454`, `activity_solver.py:2595`  
  **Risk:** Low — both parameters work, but `num_search_workers` is deprecated.  
  **Source:** [GitHub v9.11 release](https://github.com/google/or-tools/releases/tag/v9.11)

- [ ] **MEDIUM** — Test memory usage — v9.11+ may use more RAM; validate with production-size instances  
  **Files:** Infrastructure / deployment configuration  
  **Risk:** 3-4x memory increase reported for some models. With ~4,000 binary variables this system is relatively small, but validate before deploying.  
  **Source:** [Issue #4406](https://github.com/google/or-tools/issues/4406), [Google Groups](https://groups.google.com/g/or-tools-discuss/c/FO8-jCNVjPQ)

#### Phase 3: Low Priority (Tech Debt)

- [ ] **LOW** — Rename CamelCase API calls to snake_case — all files (~200+ call sites). Shims work so this is not blocking.  
  **Files:** `solvers.py`, `activity_solver.py`, `fair_call_optimizer.py`, `call_equity.py`, `solver_streaming.py`  
  **Risk:** None — purely cosmetic. CamelCase shims have no announced removal date. Can be done incrementally or via a sed script.  
  **Source:** [GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9), [Issue #4143](https://github.com/google/or-tools/issues/4143)

- [ ] **LOW** — Replace `.Not()` with `~` operator  
  **Files:** `solvers.py:890, 923`  
  **Risk:** None — functionally identical.  
  **Source:** [GitHub v9.9 release](https://github.com/google/or-tools/releases/tag/v9.9)

- [ ] **LOW** — Convert `ObjectiveValue()` / `BestObjectiveBound()` / `NumBranches()` / `NumConflicts()` / `WallTime()` to properties (remove parentheses)  
  **Files:** `solvers.py:634, 635, 1488, 1493, 1705, 1721, 1722`, `fair_call_optimizer.py:239, 272, 273, 418, 427`, `solver_streaming.py:187, 188`  
  **Risk:** None via shim. However, if anyone stores `solver.ObjectiveValue` (without parens) as a bound method reference, behavior would change in v9.12 (returns float directly as a property). This edge case is unlikely.  
  **Source:** [OR-Tools API docs](https://or-tools.github.io/docs/pdoc/ortools/sat/python/cp_model.html)

- [ ] **LOW** — Replace `Proto()` with `.proto` property  
  **Files:** `solvers.py:1382, 1527`  
  **Risk:** None — `Proto()` shim forwards to `proto` property.  
  **Source:** [Discussion #3992](https://github.com/google/or-tools/discussions/3992)

- [ ] **LOW** — Adopt `best_bound_callback` for two-phase solver early termination  
  **Files:** `fair_call_optimizer.py`  
  **Risk:** None — additive feature. Could simplify phase 1 early termination logic.  
  **Source:** [GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10), [CP-SAT Primer](https://d-krupke.github.io/cpsat-primer/05_parameters.html)

- [ ] **LOW** — Enable `debug_crash_if_presolve_breaks_hint=True` during CI/testing  
  **Files:** Solver configuration (CI test harness)  
  **Risk:** None in CI — crashes are caught by test runner. Should NOT be enabled in production.  
  **Source:** [GitHub v9.12 release](https://github.com/google/or-tools/releases/tag/v9.12)

---

### Rollback Plan

If regressions are found after upgrading to v9.12, the following fallback options are available:

#### Option A: Pin to v9.11 as Intermediate Step

```
ortools>=9.11,<9.12
```

v9.11 includes hint improvements without the `LinearExpr` C++ rewrite. This is a safer intermediate target if v9.12-specific issues are encountered. However, be aware of the [callback bug](https://github.com/google/or-tools/issues/4376) and [memory regression](https://github.com/google/or-tools/issues/4406) in v9.11.

#### Option B: Revert New Linear Propagation

If performance degrades on the scheduling model:
```python
solver.parameters.new_linear_propagation = False  # revert to v9.9 propagator
```
This reverts the most impactful behavioral change from v9.10 without downgrading the package ([GitHub v9.10 release](https://github.com/google/or-tools/releases/tag/v9.10)).

#### Option C: Revert LB-Relax LNS

If search dynamics change unfavorably with higher worker counts:
```python
solver.parameters.use_lb_relax_lns = False  # revert to v9.11 default
```

#### Option D: Address Memory Issues

If v9.11+ memory regression affects this system:
- Reduce `num_workers` (e.g., from 12 to 8) to lower per-worker memory overhead
- Reduce `hint_conflict_limit` if using large values
- Test v9.10 as an intermediate: `ortools>=9.10,<9.11` ([Issue #4406](https://github.com/google/or-tools/issues/4406))

#### Option E: Full Rollback

```
ortools>=9.8,<9.9  # original pin
```

Restore original workarounds (`repair_hint=True`, `max_presolve_iterations=3`). This is the safest fallback but forfeits all improvements.

---

### Version-by-Version Risk Summary

If a phased migration is preferred, here is the risk profile for each intermediate version:

| Target Version | Risk Level | Key Benefit | Key Risk | Recommended? |
|---------------|-----------|-------------|----------|-------------|
| v9.9 | LOW | PEP8 rename; `~` operator | No hint fix; type annotation issues | Skippable |
| v9.10 | MEDIUM | `best_bound_callback`; partial hint fix; new linear propagation | `new_linear_propagation` default flip may change solve times; Windows crashes | Viable intermediate |
| v9.11 | MEDIUM-HIGH | Hint improvements; `num_workers` preferred | Memory regression (3-4x); callback bug; hints still partially broken | Not recommended as target |
| **v9.12** | **MEDIUM** | **Full hint fix; LinearExpr performance; cumulative improvements; Python 3.13** | LinearExpr rewrite (internal); `use_lb_relax_lns` default change; `swig_helper` removed | **Recommended target** |

The recommended migration path is **v9.8 → v9.12 directly**, with v9.10 as a fallback if v9.12-specific issues are found. Skipping v9.11 avoids the memory regression and callback bug while getting the full hint system rewrite.

---

### Performance Testing Protocol

Before deploying v9.12 to production, run the following benchmark protocol:

1. **Baseline:** Run 5 representative scheduling instances on v9.8 with current workarounds. Record solve time, objective value at timeout, memory usage, and hint utilization (check solver log for `complete_hint` or `[hint]`).

2. **Upgrade (default settings):** Run the same 5 instances on v9.12 with no parameter changes other than removing hint workarounds. Compare solve time, objective, and memory.

3. **Upgrade (reverted propagation):** If step 2 shows regression, re-run with:
   ```python
   solver.parameters.new_linear_propagation = False
   solver.parameters.use_lb_relax_lns = False
   ```
   This isolates the impact of default value changes.

4. **Hint validation:** For each instance, verify that hints survive presolve by enabling:
   ```python
   solver.parameters.debug_crash_if_presolve_breaks_hint = True
   ```
   Run once per instance to confirm no hint corruption.

5. **Memory profiling:** Monitor peak RSS during solve. Compare v9.8 vs v9.12 for the largest scheduling instance.

---

*Analysis compiled February 26, 2026. Covers OR-Tools CP-SAT v9.8 through v9.12. All source links verified against [GitHub releases](https://github.com/google/or-tools/releases) and [official documentation](https://developers.google.com/optimization/support/release_notes).*
