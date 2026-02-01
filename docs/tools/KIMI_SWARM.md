# Kimi K2.5 Swarm Orchestrator

> **Status:** Experimental | **Last Updated:** 2026-02-01
>
> This tool is under active development. Kimi K2.5's swarm capabilities significantly exceed our current utilization. Further prompt engineering and integration work is needed to unlock its full potential.

---

## Overview

Kimi K2.5 can self-direct an **agent swarm of up to 100 sub-agents**, executing parallel workflows across **up to 1,500 coordinated tool calls**. This reduces execution time by up to 4.5x compared to single-agent approaches.

**Key Insight:** The swarm orchestrator is triggered by **prompt structure**, not API parameters. The constraints you specify in the prompt become the blueprint for how Kimi instantiates and assigns sub-agents.

---

## Current Implementation

Script: `scripts/kimi_mypy_swarm.py`

### CLI Flags

| Flag | Description |
|------|-------------|
| `--swarm` | Enable swarm mode (batch files together) |
| `--batch-size N` | Files per batch (default: 10) |
| `--repair` | Enable Generate-Check-Repair loop |
| `--max-repair N` | Max repair attempts (default: 2) |
| `--apply` | Apply fixes (default: dry-run) |

### Current Use Case

Fixing mypy type annotation errors in bulk:

```bash
# Dry run on 20 files with simple errors
python scripts/kimi_mypy_swarm.py --swarm --limit 20 --max-errors 3

# Apply fixes
python scripts/kimi_mypy_swarm.py --swarm --limit 20 --max-errors 3 --apply
```

---

## Prompt Engineering for Swarm Activation

### What Triggers Swarm Decomposition

1. **Domain-specific tasks** → Specialist sub-agents created
2. **Explicit scale signals** ("50 files", "100 items") → Parallelization
3. **Independent subtasks** → Concurrent processing
4. **Category grouping** → Specialized handlers per category

### Effective Prompt Structure

```
## MISSION
[Clear objective with quantified scope]

## CATEGORIES (specialize by type)
- [Category A]: N items across M files
- [Category B]: N items across M files

## PARALLELIZATION STRATEGY
[Explicit instruction to process categories independently]

## OUTPUT FORMAT
[Structured, aggregatable format]

## EXECUTE
[Clear action instruction]
```

### Example: Mypy Swarm Prompt

```
## MISSION
Fix mypy type annotation errors across 50 Python files.
Total errors: 75

## ERROR CATEGORIES (specialize by type)
- [assignment]: 40 errors across 30 files
- [valid-type]: 20 errors across 15 files
- [return-value]: 15 errors across 10 files

## FIX PATTERNS BY CATEGORY
- [assignment]: Add `| None` to parameter types with None defaults
- [valid-type]: Replace `any` with `Any` from typing
- [return-value]: Update return type to match actual returns

## OUTPUT FORMAT
FILE_PATH|LINE|FIXED_CODE
FILE_PATH|LINE|SKIP|reason

## EXECUTE
Process all files in parallel by error category.
```

---

## Current Performance

### Tested Results (Session 156)

| Error Type | Success Rate | Notes |
|------------|--------------|-------|
| `[assignment]` | 100% | Simple pattern: add `\| None` |
| `[valid-type]` | 100% | Simple: `any` → `Any` |
| `[return-value]` | 100% | Type annotation updates |
| `[arg-type]` | 0% (skipped) | Requires logic changes |
| `[attr-defined]` | 0% (skipped) | Requires class changes |

### Limitations Observed

1. **Complex errors** - Correctly skips, but doesn't attempt
2. **Logic changes** - Sometimes modifies behavior, not just types
3. **Large files** - Risk of unintended changes
4. **Context loss** - Batching too many files loses context

---

## Untapped Capabilities

Based on Kimi K2.5 documentation, we are **significantly underutilizing** the swarm:

### What We're Using
- Single-turn batch prompts
- ~10-20 files per batch
- Simple fix patterns only
- Text-only output

### What's Available (Not Yet Leveraged)

| Capability | Kimi K2.5 Spec | Our Usage |
|------------|----------------|-----------|
| Sub-agents | Up to 100 | ~5-10 implicit |
| Tool calls | Up to 1,500 | 0 (text only) |
| Parallelism | 4.5x speedup | Unknown |
| Multi-turn | Supported | Single-turn |
| Vision | Supported | Not used |
| Code execution | Supported | Not used |

### Potential Improvements

1. **Multi-turn orchestration** - Let Kimi iterate on failures
2. **Tool integration** - Give Kimi access to run mypy directly
3. **Larger batches** - Push toward 100 files per call
4. **Complex patterns** - Teach via few-shot for harder errors
5. **Agent specialization prompts** - Explicitly define sub-agent roles

---

## API Configuration

### Endpoint
```
https://api.moonshot.ai/v1/chat/completions
```

### Model
```
kimi-k2-turbo-preview
```

### Recommended Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `temperature` | 0.6 | Per Moonshot docs for turbo |
| `top_p` | 0.95 | Standard for code |
| `max_tokens` | 16384 | Large for batch output |
| `timeout` | 300s | Allow time for swarm |

### API Key Storage
```bash
# Stored in macOS Keychain
security find-generic-password -a "moltbot" -s "moonshot-ai-api-key" -w
```

---

## Research References

- [Kimi K2.5 Technical Report](https://www.kimi.com/blog/kimi-k2-5.html) - Official capabilities
- [HuggingFace Model Card](https://huggingface.co/moonshotai/Kimi-K2.5) - Parameters
- [Automated Type Annotation (arxiv)](https://arxiv.org/html/2508.00422v1) - Generate-Check-Repair achieves 88.6%
- [Dev.to Guide](https://dev.to/czmilo/kimi-k25-in-2026-the-ultimate-guide-to-open-source-visual-agentic-intelligence-18od) - Practical patterns

---

## Roadmap

### Phase 1: Current (Session 156)
- [x] Basic swarm prompt structure
- [x] Batch file processing
- [x] Error type statistics
- [x] Simple fix patterns working

### Phase 2: Refinement
- [ ] Multi-turn repair loop via API
- [ ] Post-fix mypy verification
- [ ] Larger batch sizes (50+ files)
- [ ] More error type patterns

### Phase 3: Full Integration
- [ ] Tool use (let Kimi run mypy)
- [ ] Self-directed repair cycles
- [ ] Complex error handling
- [ ] Integration with CI/CD

---

## Contributing

To improve the swarm:

1. Test new prompt structures in `scripts/kimi_mypy_swarm.py`
2. Document what triggers effective decomposition
3. Track success rates by error type
4. Share findings in session scratchpads

The goal is to unlock Kimi's full 100-agent, 1,500-tool-call capability for our codebase maintenance tasks.
