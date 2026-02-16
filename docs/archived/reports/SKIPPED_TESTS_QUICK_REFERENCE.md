# Skipped Tests Quick Reference

**96 total skip decorators across 11 files**

## At a Glance

```
HIGH PRIORITY - Fix Immediately (42 tests)
├─ DEBT-016 Placeholders (38 tests) - Services implemented, tests need fixtures
│  ├─ test_fmit_scheduler_service.py (14)
│  ├─ test_call_assignment_service.py (16)
│  └─ test_schedule_routes.py (12)
├─ Test Isolation Issue (1 test) - Concurrent contingency analysis
└─ Anti-churn fixtures (2 tests) - Need mock Assignment with dates

MEDIUM PRIORITY - Defer (8 tests)
└─ test_kalman_workload_bridge.py (8) - Feature not yet implemented

KEEP SKIPPED - Conditional CI (44 tests)
├─ Missing ndlib (30 tests) - Optional burnout epidemiology
├─ Vector DB/pgvector (9 tests) - PostgreSQL only
├─ Quantum solver (3 tests) - PyQUBO/dwave optional
├─ NetworkX (1 test) - Optional graph analysis
└─ MCP server (1 test) - Optional integration
```

## Quick Links

| File | Tests | Issue | Fix |
|------|-------|-------|-----|
| `test_fmit_scheduler_service.py` | 14 | DEBT-016: needs fixtures | Uncomment import, create fixtures, remove skip |
| `test_call_assignment_service.py` | 16 | DEBT-016: needs fixtures | Same as above |
| `test_schedule_routes.py` | 12 | DEBT-016: needs auth fixtures | Create auth fixture, sample data, remove skip |
| `test_resilience_load.py` | 1 | SQLAlchemy object lifecycle | Fix test isolation, unskip |
| `test_anti_churn.py` | 2 | Needs mock Assignment objects | Create mock fixtures, remove skip |
| `test_kalman_workload_bridge.py` | 8 | Not implemented | Defer - feature in progress |
| `test_contagion_model.py` | 30 | ndlib missing | Keep skipped - optional |
| `test_rag_service.py` | 9 | pgvector missing | Keep skipped - environment |
| `test_quantum_solver.py` | 3 | Quantum deps | Keep skipped - optional |
| `test_resilience_hub_analysis.py` | 1 | NetworkX missing | Keep skipped - optional |
| `test_orchestration_e2e.py` | 1 | MCP server | Keep skipped - optional |

## DEBT-016 Unskip Checklist

For `test_fmit_scheduler_service.py`, `test_call_assignment_service.py`:

```
[ ] Uncomment service import (line ~28)
[ ] Create fixtures using conftest.py patterns
[ ] Replace pass statements with assertions
[ ] Remove @pytest.mark.skip decorators
[ ] Run: pytest tests/services/test_*.py -v
[ ] All green? Commit!
```

For `test_schedule_routes.py`:

```
[ ] Create auth_headers fixture (token generation)
[ ] Create sample_rotation_template fixture
[ ] Create sample_persons fixture
[ ] Create sample_blocks fixture
[ ] Replace pass statements with assertions
[ ] Remove @pytest.mark.skip decorators
[ ] Run: pytest tests/test_schedule_routes.py -v
[ ] All green? Commit!
```

## CI Configuration

```bash
# Main test suite (skip optional deps)
pytest tests/ --ignore=tests/unit/test_contagion_model.py ...

# With optional deps (requires pip install ndlib networkx scikit-learn)
pytest tests/

# Integration only (requires Docker)
pytest tests/integration/
```

## Risk Summary

| Category | Tests | Risk | Action |
|----------|-------|------|--------|
| No test coverage | 42 | HIGH | Unskip immediately |
| Known bug blocked | 1 | CRITICAL | Fix + unskip |
| Incomplete fixtures | 2 | MEDIUM | Implement + unskip |
| Missing optional deps | 35 | LOW | Keep skipped |
| Not implemented | 8 | MEDIUM | Defer |

## Legend

- **DEBT-016**: Scheduled test debt (services exist, fixtures don't)
- **@pytest.mark.skip**: Hard skip (test won't run)
- **@pytest.mark.skipif()**: Conditional skip (runs if condition met)
- **SQLAlchemy object lifecycle**: Test isolation issue (detached sessions)
- **pgvector**: PostgreSQL vector extension (not in SQLite)
- **ndlib/PyQUBO/dwave**: Optional advanced feature dependencies

---

See `SKIPPED_TESTS_MANIFEST.md` for full analysis and implementation details.
