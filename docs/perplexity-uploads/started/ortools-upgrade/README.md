# OR-Tools CP-SAT 9.8 → 9.12 Migration Upload

Upload folder for analyzing the OR-Tools upgrade path from 9.8 to 9.12.

## Usage

1. Upload all files from this folder to Perplexity Computer
2. Paste the contents of `PROMPT.md` as the session prompt

## File Manifest

| Upload Path | Original Source Path | Size |
|-------------|---------------------|------|
| `solver/solvers.py` | `backend/app/scheduling/solvers.py` | 96K |
| `solver/activity_solver.py` | `backend/app/scheduling/activity_solver.py` | 156K |
| `solver/fair_call_optimizer.py` | `backend/app/scheduling/fair_call_optimizer.py` | ~40K |
| `solver/solver_streaming.py` | `backend/app/scheduling/solver_streaming.py` | ~8K |
| `solver/constraints_config.py` | `backend/app/scheduling/constraints/config.py` | 22K |
| `constraints/call_equity.py` | `backend/app/scheduling/constraints/call_equity.py` | ~20K |

## Sections

| # | Section | Focus |
|---|---------|-------|
| 1 | Changelog Deep Dive | Version-by-version breaking changes (9.8→9.12) |
| 2 | API Compatibility Scan | Every API call checked against 9.12 docs |
| 3 | Hint System Evolution | Two-phase solver hint preservation fixes |
| 4 | Behavioral Changes | Search strategy, LP relaxation, symmetry, determinism |
| 5 | New Features | What 9.9-9.12 features could improve our solver |
| 6 | Migration Checklist | Ordered steps with risk assessment |

## Notes

- No PII: all source code
- Currently pinned to `ortools>=9.8,<9.9` in requirements
- Known 9.8 bug: hint preservation broken (workaround: repair_hint=True)
