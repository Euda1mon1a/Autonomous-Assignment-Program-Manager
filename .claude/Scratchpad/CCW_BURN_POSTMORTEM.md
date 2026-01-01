# CCW Burn Postmortem: 1000-Task Parallel Execution

> **Date:** 2025-12-31
> **Issue:** Type-check failures + syntax corruption
> **Root Cause:** Missing validation gates
> **Fix Time:** ~5 minutes (once diagnosed)

---

## The Illusion of Complexity

**What it looked like:** 134+ files failing, 6-7 hour estimate

**What it actually was:**
- 1 missing package (@types/jest)
- 6 corrupted tokens in swap.py

---

## Root Cause: Token Concatenation Bug

CCW corrupted Python syntax by incorrectly merging tokens:

```python
# CCW wrote:
result = await sawait ervice.validate_schedule()
#              ^^^^^^ ^^^^^^^  <- corrupted

# Should be:
result = await service.validate_schedule()
```

Found in: `backend/app/api/routes/swap.py` (5 occurrences)

---

## Key Insight

> **Volume obscures simplicity.**
>
> 134 identical errors ≠ 134 different problems.
> Pattern-match first, count second.

---

## Prevention

Run validation gate every ~20 CCW tasks:

```bash
./.claude/scripts/ccw-validation-gate.sh
```

---

*Document created: 2025-12-31*
