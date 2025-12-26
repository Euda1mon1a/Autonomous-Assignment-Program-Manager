# Academic Year Block Structure

> **Reference Documentation** for the Residency Scheduler block system

---

## Overview

The academic year (AY) runs **July 1 through June 30** and is divided into **14 blocks** (Block 0 + Blocks 1-13). Each calendar day contains **AM and PM scheduling blocks**, yielding **730 total blocks** per academic year (365 days x 2).

---

## Block Types

### Block 0: Orientation
- **Duration**: 2 days (Tuesday-Wednesday)
- **Purpose**: New resident orientation, onboarding activities
- **Flexibility**: Absorbs calendar irregularities and leap year adjustments

### Blocks 1-12: Standard Rotation Blocks
- **Duration**: 28 days each
- **Pattern**: Thursday through Wednesday (Thu→Wed)
- **Total**: 336 days (12 blocks x 28 days)

### Block 13: Final Block
- **Duration**: 27 days
- **Pattern**: Thursday through Tuesday (ends on June 30)
- **Purpose**: Academic year cutoff alignment

---

## AY 2025-2026 Block Schedule

| Block | Start Date | End Date | Days | Notes |
|-------|------------|----------|------|-------|
| **0** | Tue, Jul 1, 2025 | Wed, Jul 2, 2025 | 2 | Orientation |
| **1** | Thu, Jul 3, 2025 | Wed, Jul 30, 2025 | 28 | Standard |
| **2** | Thu, Jul 31, 2025 | Wed, Aug 27, 2025 | 28 | Standard |
| **3** | Thu, Aug 28, 2025 | Wed, Sep 24, 2025 | 28 | Standard |
| **4** | Thu, Sep 25, 2025 | Wed, Oct 22, 2025 | 28 | Standard |
| **5** | Thu, Oct 23, 2025 | Wed, Nov 19, 2025 | 28 | Standard |
| **6** | Thu, Nov 20, 2025 | Wed, Dec 17, 2025 | 28 | Standard |
| **7** | Thu, Dec 18, 2025 | Wed, Jan 14, 2026 | 28 | Standard |
| **8** | Thu, Jan 15, 2026 | Wed, Feb 11, 2026 | 28 | Standard |
| **9** | Thu, Feb 12, 2026 | Wed, Mar 11, 2026 | 28 | Standard |
| **10** | Thu, Mar 12, 2026 | Wed, Apr 8, 2026 | 28 | Standard |
| **11** | Thu, Apr 9, 2026 | Wed, May 6, 2026 | 28 | Standard |
| **12** | Thu, May 7, 2026 | Wed, Jun 3, 2026 | 28 | Standard |
| **13** | Thu, Jun 4, 2026 | Tue, Jun 30, 2026 | 27 | AY Cutoff |

**Total**: 365 days / 730 scheduling blocks

---

## Daily Block Structure

Each calendar day contains two scheduling blocks:

| Block | Time Period | Typical Use |
|-------|-------------|-------------|
| AM | Morning session | Clinic, procedures, inpatient |
| PM | Afternoon session | Clinic, conferences, call handoff |

---

## Leap Year Handling

- **Block 0** provides flexibility to absorb the extra day in leap years
- Standard blocks (1-12) maintain consistent 28-day duration
- Block 13 adjusts as needed to align with June 30 cutoff

---

## Key Invariants

1. Academic year always ends June 30
2. Blocks 1-12 are always 28 days (Thu→Wed)
3. Block boundaries never split a Thu→Wed week mid-cycle
4. Total scheduling blocks per AY = 730 (non-leap) or 732 (leap year)

---

## Related Documentation

- [Solver Algorithm](SOLVER_ALGORITHM.md) - How blocks are assigned
- [Cross-Disciplinary Resilience](cross-disciplinary-resilience.md) - Coverage requirements per block
