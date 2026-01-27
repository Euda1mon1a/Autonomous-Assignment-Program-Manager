# Software Concepts for Medical Professionals

> **Purpose:** Explain software engineering concepts using medical analogies for domain experts who aren't software engineers.
> **Created:** 2026-01-27 (Session blind spot assessment)
> **Audience:** Medical professionals, program coordinators, and AI assistants working with clinician-developers

---

## Quick Reference Table

| Software Concept | Medical Equivalent | Key Insight |
|------------------|-------------------|-------------|
| Async/Sync | ED attending / Surgeon | Multitask vs. blocking |
| Exception swallowing | Ignoring critical labs | Errors disappear into logs |
| Transaction boundaries | All-or-nothing surgery | Partial completion = corruption |
| Unit vs integration tests | In vitro vs in vivo | Isolated vs whole-organism |
| CP-SAT constraints | Physics, not biology | No tolerance, no adaptation |

---

## 1. Async vs Sync Operations

### Synchronous (Blocking)

**Medical analogy: Surgeon in the OR**

The surgeon makes an incision and must wait for it to complete before placing the next suture. They cannot leave mid-procedure to check on another patient. The surgeon is *blocked* on each step.

```
Cut → wait → suture → wait → close → wait → done
```

**In software:** A sync function must complete before the next line runs. The program waits.

### Asynchronous (Non-blocking)

**Medical analogy: Attending on the floor**

The attending orders labs for Patient A, then immediately sees Patient B while waiting for A's results. When results come back, they get notified and return to A. They're never *waiting* - always doing something.

```
Order labs A → see patient B → labs A ready → return to A → order imaging B → ...
```

**In software:** An async function can start, yield control while waiting for I/O, and resume when data arrives.

### When Each is Appropriate

| Context | Correct Choice | Why |
|---------|----------------|-----|
| API handling web requests | **Async** | Don't block other users |
| CPU-intensive computation | **Sync** | No I/O to wait for |
| Database queries in API | **Async** | Network I/O involved |
| Solver doing math | **Sync** | Pure computation |

**Key insight:** The scheduling engine uses sync intentionally because it's like surgery - CPU-bound work where blocking is expected. The API layer uses async because it's like an ED - must handle many concurrent requests.

---

## 2. Exception Handling

### Exception Swallowing (Bad Pattern)

**Medical analogy: Ignoring critical lab values**

```python
except Exception as e:
    logger.error(f"Something failed: {e}")
    # continues execution
```

This is like a lab system that flags a critical potassium of 6.8, but the alert just gets logged to a file nobody checks. The patient continues through the system, and you don't find out until they code.

**The trap:** In medicine, you're trained to compensate. In software, there's no compensation unless you explicitly code it. The error just disappears into a log file.

### Good Exception Handling

**Option A: Fail loudly (crash)**
```python
except Exception as e:
    logger.error(f"Critical failure: {e}")
    raise  # Stop everything, make someone notice
```

Like calling a code - everyone stops and addresses the problem.

**Option B: Explicit recovery**
```python
except DatabaseError as e:
    logger.warning(f"DB failed, using fallback: {e}")
    return fallback_value  # Intentional, documented degradation
```

Like switching to a backup protocol when primary treatment fails - intentional and documented.

---

## 3. Database Transactions

### Transaction Boundaries

**Medical analogy: Multi-step surgical procedure**

Imagine a surgery:
1. Incision made ✓
2. Organ removed ✓
3. Power outage — procedure stops
4. ...organ is out but nothing is closed

In databases, a "transaction" is a promise: **all steps complete, or none do**. Like saying "either the whole surgery happens, or the patient wakes up as if we never started."

### Partial Commits (Bad Pattern)

```python
commit()  # Saves step A to database (permanent)
... some code ...
commit()  # Saves step B to database (permanent)
... some code that fails ...
commit()  # Never reached - step C not saved
```

**Result:** A is saved, B is saved, C is not. You have a partial schedule — some assignments written, some not. This is worse than having no schedule at all.

### Atomic Transactions (Good Pattern)

```python
try:
    # Do steps A, B, C (no commits yet)
    step_a()
    step_b()
    step_c()
    commit()  # All three saved together
except:
    rollback()  # None of them saved
```

**Key insight:** In biology, partial completion is often fine - a half-synthesized protein gets degraded and recycled. In databases, partial completion is corruption. You can't "degrade and recycle" half-written data.

---

## 4. Testing Levels

### Unit Tests

**Medical analogy: In vitro testing**

Testing a drug on isolated cells in a petri dish.
- Fast, cheap, reproducible
- Tests one thing in isolation
- Can't detect organism-level interactions

### Integration Tests

**Medical analogy: In vivo testing**

Testing a drug in a living organism.
- Slower, more complex
- Tests how components interact
- Catches systemic issues

### End-to-End Tests

**Medical analogy: Clinical trials**

Testing in real patients with real conditions.
- Slowest, most expensive
- Tests the whole system
- Catches real-world edge cases

### The Gap

You can have:
- Unit tests passing (enzyme works in tube) ✓
- Integration tests missing (never tested in cell)
- Discovery: enzyme doesn't work in vivo

**Key insight:** "Try it and see" (operational testing) works but isn't automated. Integration tests automate "try it and see" so you don't have to do it manually every time.

---

## 5. Constraint Solvers (CP-SAT)

### Biological Systems vs. Solvers

| Biological Systems | CP-SAT Solver |
|--------------------|---------------|
| Tolerance/homeostasis | Binary: satisfies or fails |
| Graceful degradation | No partial credit |
| Adaptation over time | Static model per run |
| Feedback loops | No feedback (one-shot) |

**The trap:** Your intuition says "if I relax this constraint a little, the system will adapt." CP-SAT says "constraint violated = INFEASIBLE, full stop."

### Hard vs. Soft Constraints

**Hard constraint:** Physically or logically impossible to violate.
- Medical: Can't be in two ORs simultaneously
- Software: `if violated: FAIL`

**Soft constraint:** Desirable but not mandatory.
- Medical: Prefer attending supervision, but senior resident can cover
- Software: `if violated: penalty_score += 10`

### Key Insight

The solver is **dumb math that happens very fast**. It has no:
- Common sense
- Domain knowledge
- Ability to "figure it out"

Every behavior must be explicitly encoded. If you think "the solver should be smart enough to..." - it isn't.

---

## 6. The Meta-Lesson

### Software ≠ Biology

| Biological Systems | Software Systems |
|-------------------|------------------|
| Self-healing | Stays broken until fixed |
| Homeostasis | No automatic rebalancing |
| Immune response | No automatic threat response |
| Adaptation | Static until redeployed |
| Redundancy via diversity | Redundancy via explicit copies |

**Key insight:** When code breaks, it stays broken. There's no immune system, no homeostasis, no adaptation. The exotic resilience concepts being built (transcription factors, homeostasis monitors, etc.) are attempts to add these biological properties to software - but until integrated, the system is more fragile than biological intuition suggests.

---

## References

- [BEST_PRACTICES_AND_GOTCHAS.md](BEST_PRACTICES_AND_GOTCHAS.md) - Technical gotchas
- [CPSAT_MENTAL_MODEL.md](../scheduling/CPSAT_MENTAL_MODEL.md) - Solver deep-dive
- Plan file: `.claude/plans/deep-foraging-starfish.md` - Original blind spot assessment

---

*Created during blind spot assessment session. Medical analogies developed for a physician learning software development through "vibecoding."*
