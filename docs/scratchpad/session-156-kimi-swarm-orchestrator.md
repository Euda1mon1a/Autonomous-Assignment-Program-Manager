# Session 156 - Kimi K2.5 Swarm Orchestrator

**Date:** 2026-02-01
**Focus:** Refine Kimi K2.5 mypy swarm with orchestrator-triggering prompts

---

## Key Discovery

Kimi K2.5's swarm orchestrator is triggered by **prompt structure**, not API parameters.

From [Moonshot docs](https://www.kimi.com/blog/kimi-k2-5.html):
> "The constraints you specify in the prompt become the blueprint for how Kimi instantiates and assigns sub-agents."

---

## Script Improvements

File: `scripts/kimi_mypy_swarm.py`

### New Flags
| Flag | Description |
|------|-------------|
| `--swarm` | Enable swarm mode (batch files, trigger orchestrator) |
| `--batch-size N` | Files per batch in swarm mode (default: 10) |
| `--repair` | Enable Generate-Check-Repair loop |
| `--max-repair N` | Max repair attempts per file (default: 2) |

### New Functions
- `build_swarm_prompt()` - Orchestrator-triggering batch prompt
- `parse_swarm_response()` - Parse batch FILE|LINE|CODE output
- `run_swarm_batch()` - Single API call for multiple files
- `fix_file_with_repair()` - Generate-Check-Repair loop
- `validate_indentation()` - Reject fixes with wrong indent
- `update_error_stats()` - Track success by error type

---

## Test Results

### Swarm Mode (20 files, batch of 20)
```
📊 Success rate: 11/20 (55%)

📈 Success by error type:
  [assignment]: 100% (7/7)
  [valid-type]: 100% (2/2)
  [return-value]: 100% (1/1)
```

### Key Findings
1. **Simple errors** (assignment, valid-type): 100% success
2. **Complex errors** (arg-type, attr-defined): Correctly skipped
3. **Error count**: 4,972 mypy errors (unchanged - fixes reverted for safety)

---

## Prompt Engineering Insights

### What Triggers Swarm Decomposition
- Domain-specific tasks → specialist sub-agents
- Explicit scale ("50 files", "8 error types") → parallelization
- Independent subtasks → concurrent processing

### Effective Prompt Structure
```
## MISSION
Fix mypy errors across {N} files.

## ERROR CATEGORIES (specialize by type)
- [assignment]: 100 errors across 50 files
- [valid-type]: 20 errors across 10 files

## PARALLELIZATION STRATEGY
Process by category. Apply same fix pattern to all matching errors.

## OUTPUT FORMAT
FILE_PATH|LINE|FIXED_CODE
```

---

## Commits (PR #800 - Merged)

| Hash | Message |
|------|---------|
| `3d110390` | feat(swarm): add swarm mode with orchestrator-triggering prompts |
| `0d4461a3` | docs: session 156 - kimi swarm orchestrator improvements |
| `3031fcd1` | fix(swarm): address Codex P2 feedback |

### Codex Fixes Applied
- **P2-1:** Actually insert typing imports (Any, Optional, Callable)
- **P2-2:** Fix dry-run repair loop to use temp file for validation

### Mypy Fixes Applied
| Commit | Change |
|--------|--------|
| `4b1bceda` | fix(types): apply Kimi swarm mypy fixes (22 errors reduced) |

- 31 files fixed, 17 skipped, 2 syntax errors rejected
- Error count: **4209 → 4187** (-22)

---

## Next Steps

1. Run swarm on `assignment` errors only (safe pattern)
2. Add post-fix mypy verification before accepting
3. Consider sed/awk for simplest patterns (`= None` → `| None = None`)

---

## Sources

- [Kimi K2.5 Technical Report](https://www.kimi.com/blog/kimi-k2-5.html)
- [Automated Type Annotation Research (arxiv)](https://arxiv.org/html/2508.00422v1) - 88.6% with Generate-Check-Repair
- [Dev.to Guide](https://dev.to/czmilo/kimi-k25-in-2026-the-ultimate-guide-to-open-source-visual-agentic-intelligence-18od)
