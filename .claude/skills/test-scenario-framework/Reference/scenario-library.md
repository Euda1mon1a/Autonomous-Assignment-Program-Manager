# Scenario Library

Pre-built test scenarios for medical residency scheduling. 20+ scenarios covering N-1 failures, multi-swap operations, ACGME edge cases, holiday conflicts, and moonlighting.

## Category Index

1. **N-1 Failure Scenarios** (10 scenarios)
2. **Swap Operation Scenarios** (5 scenarios)
3. **ACGME Edge Case Scenarios** (7 scenarios)
4. **Holiday & Vacation Conflict Scenarios** (4 scenarios)
5. **Moonlighting Scenarios** (3 scenarios)
6. **Integration Scenarios** (2 scenarios)

---

## N-1 Failure Scenarios

### N1-001: Simple Single Resident Unavailable

**Scenario ID:** `n1-simple-unavailable-001`

**Description:** Test basic N-1 contingency when single resident becomes unavailable during regular rotation.

**Setup:**
- 2 PGY-2 residents (R1, R2)
- R2 configured as backup for R1
- R1 assigned to inpatient AM shift on 2024-12-25
- R2 assigned to clinic AM shift on 2024-12-25

**Test Case:**
- Mark R1 unavailable on 2024-12-25 (reason: illness)
- Trigger contingency analysis
- Activate backup assignments

**Expected Outcome:**
- Coverage maintained on 2024-12-25 for inpatient
- R2 reassigned from clinic to inpatient
- ACGME compliance preserved
- Execution time < 5s

---

### N1-002: Holiday Coverage Failure

**Scenario ID:** `n1-holiday-coverage-001`

**Description:** Test N-1 failure during critical holiday coverage when backup pool is limited.

**Setup:**
- 4 residents: R1-PGY2, R2-PGY2, R3-PGY3, R4-PGY1
- Holiday schedule (2024-12-25 Christmas)
- R1 assigned to inpatient 24-hour call
- R2 assigned to ER coverage
- R3 as backup for R1
- R4 scheduled off (ACGME 1-in-7 compliance)

**Test Case:**
- Mark R1 unavailable on 2024-12-25 0600hrs (reason: family emergency)
- Trigger emergency contingency
- Ensure PGY-1 supervision maintained

**Expected Outcome:**
- R3 activated as backup
- PGY-1 (R4) NOT called in (preserve 1-in-7)
- Supervision ratio maintained (1 faculty per 2 residents minimum)
- Coverage gap = 0 hours
- Alert sent to program director

---

### N1-003: Multiple Simultaneous Absences

**Scenario ID:** `n1-multi-absence-001`

**Description:** Stress test N-1 system with multiple simultaneous unplanned absences.

**Setup:**
- 6 residents: R1-R6 (mix of PGY levels)
- Full day schedule with multiple rotations
- Backup chains defined (R3→R1, R4→R2, R5→R3, R6→R4)

**Test Case:**
- Mark R1 unavailable (illness)
- Mark R2 unavailable (car accident)
- Trigger cascade contingency analysis
- Activate backup chains

**Expected Outcome:**
- R3 covers R1's assignments
- R4 covers R2's assignments
- R5 and R6 backfill R3 and R4
- No coverage gaps
- Total assignments modified ≤ 12
- ACGME 80-hour rule maintained for all residents
- Execution time < 10s

---

### N1-004: Backup Chain Cascade

**Scenario ID:** `n1-backup-chain-cascade-001`

**Description:** Test deep backup chain activation (3+ levels deep).

**Setup:**
- 8 residents with 4-level backup chain
- R1 → R3 → R5 → R7
- R2 → R4 → R6 → R8
- All residents near 70 hours/week (approaching limit)

**Test Case:**
- Mark R1 unavailable (week-long TDY)
- Trigger backup: R3 covers R1
- Trigger secondary backup: R5 covers R3's original assignments
- Trigger tertiary backup: R7 covers R5's original assignments

**Expected Outcome:**
- All 3 backup levels activated successfully
- No resident exceeds 80 hours/week
- Backup chain integrity maintained
- Optimization: Minimize total reassignments
- Expected reassignments: 15-20 (with tolerance ±5)

---

### N1-005: Weekend Coverage Gap

**Scenario ID:** `n1-weekend-coverage-001`

**Description:** Test N-1 failure during weekend when backup pool is reduced.

**Setup:**
- Weekend schedule (Saturday 2024-12-28)
- Minimal staff (4 residents on duty, 6 off for 1-in-7 compliance)
- R1 on call, R2 on inpatient, R3 on procedures, R4 on ER

**Test Case:**
- Mark R1 unavailable 2 hours into call shift
- Limited backup pool (only R2 and R3 available, R4 cannot be pulled)
- Trigger weekend contingency protocol

**Expected Outcome:**
- Coverage maintained via backup activation
- 1-in-7 rule NOT violated (off-duty residents remain off)
- May require extended hours for R2 or R3 (within 24-hour duty limit)
- Program director notified of weekend coverage stress
- Red flag raised if utilization > 85%

---

### N1-006: Night Float Replacement

**Scenario ID:** `n1-night-float-001`

**Description:** Test N-1 contingency for night float coverage (critical overnight supervision).

**Setup:**
- Night float schedule (2024-12-20 to 2024-12-26, 7 consecutive nights)
- R1 assigned to all 7 nights (within 6-night limit if starting Sunday)
- R2 designated backup for nights 1-3
- R3 designated backup for nights 4-7

**Test Case:**
- Mark R1 unavailable on night 3 (2024-12-22 at 2200hrs)
- Trigger emergency night float replacement

**Expected Outcome:**
- R2 activated for night 3 (within their backup window)
- Night float continuity maintained
- No > 6 consecutive nights for any single resident
- Handoff protocol executed (R1→R2)
- No gap in overnight supervision

---

### N1-007: TDY/Deployment Coverage

**Scenario ID:** `n1-tdy-deployment-001`

**Description:** Test extended absence due to military TDY/deployment (multi-week coverage).

**Setup:**
- R1 assigned to full month of clinic days (20 half-days)
- R2 as primary backup (can cover 10 half-days)
- R3 as secondary backup (can cover 10 half-days)
- All residents have baseline ~60 hours/week

**Test Case:**
- Mark R1 unavailable for 4 weeks (2024-12-01 to 2024-12-28)
- Reason: military deployment
- Trigger long-term contingency planning

**Expected Outcome:**
- R2 and R3 split coverage (10 days each)
- No single resident exceeds 75 hours/week average
- Utilization remains < 80% for all residents
- Long-term coverage plan documented
- Monthly compliance check shows no violations

---

### N1-008: Post-Call Relief Failure

**Scenario ID:** `n1-post-call-relief-001`

**Description:** Test N-1 when post-call relief resident becomes unavailable (ACGME requires 8+ hours off after 24-hour call).

**Setup:**
- R1 on 24-hour call (2024-12-25 0700hrs to 2024-12-26 0700hrs)
- R2 scheduled to relieve R1 at 0700hrs on 2024-12-26
- R3 as backup for R2

**Test Case:**
- Mark R2 unavailable at 0600hrs on 2024-12-26 (car trouble, cannot arrive)
- R1 approaching 24-hour duty limit
- Trigger emergency post-call relief

**Expected Outcome:**
- R3 activated to relieve R1 by 0700hrs
- R1 gets minimum 8 hours off (ACGME compliance)
- No duty period > 24 hours (+4 hour transition max)
- Relief coverage starts within 30 minutes of scheduled time
- Critical alert sent to program director

---

### N1-009: Supervision Ratio Violation Risk

**Scenario ID:** `n1-supervision-ratio-001`

**Description:** Test N-1 when faculty absence would violate supervision ratios.

**Setup:**
- 4 PGY-1 residents on inpatient rotation
- 2 faculty supervisors (F1, F2)
- Ratio requirement: 1 faculty per 2 PGY-1s (2:1)
- F2 as backup supervisor

**Test Case:**
- Mark F1 unavailable during inpatient shift
- Automatic check: would ratio become 1:4 (violation)?
- Trigger faculty backup protocol

**Expected Outcome:**
- F2 activated as backup supervisor
- Supervision ratio maintained at 1:2 (F2 supervises 2, remaining 2 residents reassigned or second faculty called)
- If F2 unavailable, reduce PGY-1 count on service (move to less critical rotations)
- No PGY-1 works without adequate supervision
- ACGME supervision compliance = 100%

---

### N1-010: Cascade Failure Prevention

**Scenario ID:** `n1-cascade-failure-prevention-001`

**Description:** Test system's ability to prevent cascade failures when backup activation would create new gaps.

**Setup:**
- 5 residents at 75 hours/week (near limit)
- Linear backup chain: R1 → R2 → R3 → R4 → R5
- All residents have critical assignments

**Test Case:**
- Mark R1 unavailable
- System attempts to activate R2 as backup
- Check: Would R2 activation create gap in R2's original assignments?
- Check: Would R2 exceed 80 hours if covering R1?

**Expected Outcome:**
- System detects cascade risk BEFORE executing backup
- Alternative solution: Split R1's assignments across R2 and R3 (load balancing)
- No new coverage gaps created
- No resident exceeds 80 hours/week
- Optimization: Minimize disruption (fewest reassignments)
- Expected reassignments: 4-8

---

## Swap Operation Scenarios

### SWAP-001: Simple One-to-One Swap

**Scenario ID:** `swap-one-to-one-simple-001`

**Description:** Test basic one-to-one swap between two residents with compatible schedules.

**Setup:**
- R1 assigned to clinic AM on 2024-12-15
- R2 assigned to inpatient AM on 2024-12-15
- Both PGY-2, both at 50 hours/week, both qualified for both rotations

**Test Case:**
- R1 requests swap with R2 for 2024-12-15
- Validate compatibility (ACGME compliance, qualifications)
- Execute swap

**Expected Outcome:**
- Swap approved and executed
- R1 now on inpatient AM, R2 now on clinic AM
- ACGME compliance maintained
- Swap recorded in audit log
- Both residents notified
- Execution time < 3s

---

### SWAP-002: Multi-Swap Chain

**Scenario ID:** `swap-multi-chain-001`

**Description:** Test chain of swaps (R1→R2→R3) executed in sequence.

**Setup:**
- R1 assigned to call on 2024-12-20
- R2 assigned to clinic on 2024-12-20
- R3 assigned to procedures on 2024-12-20

**Test Case:**
- R1 requests swap with R2 (R1 wants clinic)
- R2 requests swap with R3 (R2 wants procedures)
- Execute swap chain: R1→clinic, R2→procedures, R3→call

**Expected Outcome:**
- All 3 swaps approved
- Final state: R1=clinic, R2=procedures, R3=call
- ACGME compliance maintained throughout chain
- No intermediate violations
- Total execution time < 10s

---

### SWAP-003: Swap Rejected - ACGME Violation

**Scenario ID:** `swap-rejection-acgme-001`

**Description:** Test swap rejection when it would violate ACGME rules.

**Setup:**
- R1 at 78 hours/week, assigned to 4-hour clinic shift on 2024-12-18
- R2 at 60 hours/week, assigned to 12-hour call shift on 2024-12-18

**Test Case:**
- R1 requests swap with R2 (wants call shift)
- System validates: R1 would go to 86 hours/week (violation!)
- Reject swap

**Expected Outcome:**
- Swap REJECTED
- Rejection reason: "Would violate 80-hour rule for R1"
- R1 notified with clear explanation
- No database changes made
- Alternative suggestions provided (if available)

---

### SWAP-004: Absorb Shift (Give Away)

**Scenario ID:** `swap-absorb-001`

**Description:** Test "absorb" swap where one resident gives away shift without taking another.

**Setup:**
- R1 assigned to clinic PM on 2024-12-10
- R2 has no assignment on 2024-12-10 PM
- R1 wants to give away shift (personal conflict)

**Test Case:**
- R1 requests "absorb" swap with R2
- R2 accepts (takes shift without giving one back)
- Validate coverage maintained

**Expected Outcome:**
- Swap approved
- R1 now unassigned on 2024-12-10 PM
- R2 now assigned to clinic PM
- Coverage gap = 0
- R1 total hours decreased
- R2 total hours increased (within limits)

---

### SWAP-005: Auto-Match Swap Candidate

**Scenario ID:** `swap-auto-match-001`

**Description:** Test automatic matching of compatible swap candidates.

**Setup:**
- R1 wants to swap call shift on 2024-12-15
- 5 other residents with varying availability and schedules
- R3 is most compatible (similar shift, compatible qualifications, within hours limit)

**Test Case:**
- R1 initiates swap request without specifying partner
- System runs auto-match algorithm
- System suggests R3 as best match

**Expected Outcome:**
- Auto-match identifies R3 as top candidate
- Match score > 85%
- Compatibility reasons listed (schedule fit, qualification match, ACGME compliance)
- R1 can accept or reject suggested match
- If accepted, swap executes normally

---

## ACGME Edge Case Scenarios

### ACGME-001: Exact 80-Hour Boundary

**Scenario ID:** `acgme-80hour-exact-001`

**Description:** Test scheduling when resident is at exactly 80 hours/week (boundary condition).

**Setup:**
- R1 currently at exactly 80.0 hours for rolling 4-week period
- Attempting to assign 4-hour clinic shift on next available day

**Test Case:**
- Attempt to create new assignment for R1 (4 hours)
- System calculates: would result in 80.0 + 4.0 = 84.0 hours (violation)
- Reject assignment

**Expected Outcome:**
- Assignment REJECTED
- Rejection reason: "Would exceed 80-hour limit"
- Current hours: 80.0, Proposed: +4.0, Total: 84.0
- Alternative coverage suggestions provided
- No partial assignment created

---

### ACGME-002: 1-in-7 Strict Boundary

**Scenario ID:** `acgme-one-in-seven-strict-001`

**Description:** Test 1-in-7 rule at exact 7-day boundary.

**Setup:**
- R1 has worked 6 consecutive days (2024-12-01 to 2024-12-06)
- Day 7 (2024-12-07) available

**Test Case:**
- Attempt to assign R1 to shift on 2024-12-07
- Check: Would violate 1-in-7 rule (7 consecutive days)
- Reject assignment

**Expected Outcome:**
- Assignment REJECTED
- Rejection reason: "Would violate 1-in-7 rule"
- R1 must have 2024-12-07 completely off (24 hours)
- Next eligible assignment: 2024-12-08
- Alternative resident assigned to 2024-12-07

---

### ACGME-003: Post-Call 8-Hour Minimum

**Scenario ID:** `acgme-post-call-8hour-001`

**Description:** Test enforcement of 8-hour minimum rest after 24-hour call.

**Setup:**
- R1 on 24-hour call ending 2024-12-15 at 0700hrs
- Attempting to assign clinic shift starting 2024-12-15 at 1300hrs (6 hours later)

**Test Case:**
- Attempt to create assignment starting < 8 hours after call ends
- System validates post-call rest requirement
- Reject assignment

**Expected Outcome:**
- Assignment REJECTED
- Rejection reason: "Insufficient post-call rest (6 hours < 8 hours required)"
- Earliest next assignment: 2024-12-15 at 1500hrs (8 hours post-call)
- Clinic coverage reassigned to different resident

---

### ACGME-004: Duty Period 24-Hour Limit

**Scenario ID:** `acgme-duty-period-24hour-001`

**Description:** Test enforcement of 24-hour maximum duty period.

**Setup:**
- R1 on shift starting 2024-12-10 at 0600hrs
- Attempting to extend shift to 2024-12-11 at 0800hrs (26 hours total)

**Test Case:**
- Attempt to create continuous assignment > 24 hours
- No strategic napping exception granted
- Reject assignment

**Expected Outcome:**
- Assignment REJECTED
- Rejection reason: "Duty period would exceed 24 hours"
- Maximum allowed: 24 hours (or 28 with strategic napping exception)
- Relief coverage required by 2024-12-11 at 0600hrs
- Automatic handoff scheduled

---

### ACGME-005: Night Float 6-Night Maximum

**Scenario ID:** `acgme-night-float-6night-001`

**Description:** Test enforcement of maximum 6 consecutive night shifts.

**Setup:**
- R1 assigned to nights Sunday-Friday (6 consecutive nights)
- Attempting to assign Saturday night (would be 7th consecutive)

**Test Case:**
- Attempt to assign 7th consecutive night shift
- Validate night float limits
- Reject assignment

**Expected Outcome:**
- Assignment REJECTED
- Rejection reason: "Would exceed 6 consecutive night shifts"
- R1 must have Saturday night off
- Different resident assigned to Saturday night
- R1 can resume nights after ≥ 24 hours off

---

### ACGME-006: Supervision Ratio PGY-1

**Scenario ID:** `acgme-supervision-pgy1-001`

**Description:** Test PGY-1 supervision ratio (max 2 PGY-1s per 1 faculty).

**Setup:**
- Inpatient rotation with 1 faculty on duty
- 2 PGY-1 residents already assigned
- Attempting to assign 3rd PGY-1

**Test Case:**
- Attempt to assign 3rd PGY-1 to rotation
- Validate supervision ratio (would be 3:1, violation of 2:1)
- Reject assignment

**Expected Outcome:**
- Assignment REJECTED
- Rejection reason: "Would violate PGY-1 supervision ratio (3:1 > 2:1 max)"
- Options: Add second faculty, or assign PGY-2/3 instead
- Current ratio: 2:1 (compliant)
- Proposed ratio: 3:1 (violation)

---

### ACGME-007: 4-Week Rolling Average

**Scenario ID:** `acgme-rolling-average-001`

**Description:** Test 80-hour limit calculated as rolling 4-week average.

**Setup:**
- R1 hours for last 4 weeks: 78, 76, 82, 77 hours
- Average: (78+76+82+77)/4 = 78.25 hours (compliant)
- Week 2 drops off, Week 5 starting (new rolling window)

**Test Case:**
- Week 5: Attempting to assign 85 hours
- New average: (76+82+77+85)/4 = 80.0 hours (at limit)
- Validate rolling average calculation

**Expected Outcome:**
- If Week 5 = 85 hours: Average = 80.0 (COMPLIANT, exactly at limit)
- If Week 5 = 86 hours: Average = 80.25 (VIOLATION)
- System correctly calculates rolling 4-week window
- Warning issued at 78+ hour average
- Violation flagged at 80+ hour average

---

## Holiday & Vacation Conflict Scenarios

### HOLIDAY-001: Christmas Coverage Overlap

**Scenario ID:** `holiday-christmas-overlap-001`

**Description:** Test Christmas coverage when multiple residents request time off.

**Setup:**
- 8 residents total
- 4 residents requested Christmas off (2024-12-24 to 2024-12-26)
- Minimum coverage: 3 residents on duty each day
- Fair distribution: No resident covers more than 1 major holiday

**Test Case:**
- Process leave requests
- Generate Christmas coverage schedule
- Ensure fair distribution and minimum coverage

**Expected Outcome:**
- 3-4 residents assigned to each day
- No resident works both Christmas Eve and Christmas Day (if possible)
- Residents who work Christmas get New Year's off (fair rotation)
- ACGME compliance maintained
- Coverage gap = 0
- Holiday rotation equity maintained

---

### HOLIDAY-002: Thanksgiving Week Shortage

**Scenario ID:** `holiday-thanksgiving-shortage-001`

**Description:** Test coverage during Thanksgiving week with reduced staff availability.

**Setup:**
- Thanksgiving week (2024-11-25 to 2024-11-29)
- 6 of 10 residents requested time off
- Minimum coverage: 4 residents needed per day

**Test Case:**
- Deny some leave requests (insufficient coverage)
- Generate coverage schedule with available residents
- Ensure fair distribution of holiday burden

**Expected Outcome:**
- 2 leave requests denied (to maintain minimum coverage)
- Denied requests: Junior residents (seniority-based)
- Residents working Thanksgiving get compensatory time off
- Coverage maintained at 4 residents minimum
- No single resident works entire week
- ACGME 1-in-7 maintained (at least 1 day off in 7)

---

### HOLIDAY-003: New Year's Vacation Conflict

**Scenario ID:** `holiday-newyear-conflict-001`

**Description:** Test New Year's coverage when residents want extended vacation (Dec 30 - Jan 2).

**Setup:**
- 12 residents
- 8 residents requested Dec 30 - Jan 2 off
- Minimum coverage: 5 residents needed (busy ER season)

**Test Case:**
- Process conflicting leave requests
- Prioritize based on: 1) seniority, 2) holiday equity, 3) recent time off
- Generate New Year's coverage

**Expected Outcome:**
- 5 residents assigned to work (8-5 = 3 denied)
- Denied requests notified with rationale
- Residents working New Year's get priority for next holiday
- Coverage: 5 residents per day (minimum met)
- Alternative: Offer partial approval (e.g., Dec 30-31 approved, Jan 1-2 denied)

---

### HOLIDAY-004: Last-Minute Leave Cancellation

**Scenario ID:** `holiday-last-minute-cancel-001`

**Description:** Test emergency coverage when approved leave is cancelled due to staffing crisis.

**Setup:**
- R1 has approved leave for 2024-12-20 to 2024-12-22
- R2 and R3 both call in sick on 2024-12-19
- Coverage drops below minimum (crisis level)

**Test Case:**
- Attempt to cancel R1's approved leave
- Trigger emergency coverage protocol
- Notify R1 and request voluntary coverage

**Expected Outcome:**
- Emergency alert sent to R1 (voluntary basis first)
- If R1 declines, escalate to mandatory coverage policy
- Compensatory time off granted (equal time off later)
- Crisis documented in program records
- ACGME notified if mandatory coverage invoked
- Alternative: Call in faculty to cover temporarily

---

## Moonlighting Scenarios

### MOONLIGHT-001: External Moonlighting Hours

**Scenario ID:** `moonlight-external-hours-001`

**Description:** Test ACGME compliance when resident moonlights at external facility.

**Setup:**
- R1 (PGY-3) at 70 hours/week in residency program
- R1 moonlights at external ER (12 hours/week)
- Combined total: 82 hours/week (VIOLATION)

**Test Case:**
- R1 reports moonlighting hours
- System calculates combined total
- Flag ACGME violation

**Expected Outcome:**
- Violation flagged: "Combined duty hours 82 > 80 hour limit"
- R1 notified to reduce moonlighting or program hours
- Options: 1) Reduce moonlighting to 10 hours, 2) Reduce program hours to 68
- Violation must be corrected within 1 week
- Program director notified
- Monthly tracking of combined hours

---

### MOONLIGHT-002: Internal Moonlighting

**Scenario ID:** `moonlight-internal-hours-001`

**Description:** Test internal moonlighting (within same hospital system) compliance.

**Setup:**
- R2 (PGY-2) at 65 hours/week in program
- R2 picks up extra call shifts in same hospital (internal moonlighting)
- Extra shifts: 10 hours/week
- Combined: 75 hours/week (COMPLIANT)

**Test Case:**
- R2 signs up for internal moonlighting shifts
- System validates combined hours
- Approve moonlighting

**Expected Outcome:**
- Moonlighting APPROVED (75 hours < 80 hour limit)
- Combined hours tracked automatically
- Warning if approaching 78 hours (95% of limit)
- R2 can moonlight up to 15 hours/week while staying compliant
- Automatic alerts if combined hours would exceed limit

---

### MOONLIGHT-003: Moonlighting Conflict with Scheduled Duty

**Scenario ID:** `moonlight-schedule-conflict-001`

**Description:** Test conflict detection when moonlighting overlaps with scheduled program duty.

**Setup:**
- R3 assigned to clinic on 2024-12-12 from 0800-1200
- R3 attempts to sign up for moonlighting shift on 2024-12-12 from 1000-1800

**Test Case:**
- R3 submits moonlighting request
- System detects time conflict
- Reject moonlighting request

**Expected Outcome:**
- Moonlighting request REJECTED
- Rejection reason: "Conflicts with scheduled clinic duty (0800-1200)"
- R3 notified of conflict
- No double-booking allowed
- Alternative moonlighting times suggested (after 1200)
- Program duty takes priority over moonlighting

---

## Integration Scenarios

### INT-001: Full Month Schedule Generation

**Scenario ID:** `integration-full-month-001`

**Description:** End-to-end test of generating complete month schedule with all constraints.

**Setup:**
- 12 residents (4 PGY-1, 4 PGY-2, 4 PGY-3)
- 3 faculty
- 6 rotation types (inpatient, clinic, procedures, call, ER, night float)
- Full month: 2024-12-01 to 2024-12-31 (31 days, 62 blocks)

**Test Case:**
- Generate complete monthly schedule
- Enforce all ACGME rules
- Balance workload across residents
- Minimize coverage gaps
- Optimize for resident preferences (if provided)

**Expected Outcome:**
- Schedule generated successfully
- ACGME compliance: 100%
- Coverage completeness: > 95%
- Workload balance: Std dev of weekly hours < 10
- Execution time: < 60s
- No critical alerts
- Validation checks: All passed

---

### INT-002: Concurrent Multi-Swap with N-1 Failure

**Scenario ID:** `integration-concurrent-swap-n1-001`

**Description:** Stress test system with concurrent operations (swaps + N-1 failure) to test race conditions and consistency.

**Setup:**
- 8 residents with various assignments
- Baseline schedule ACGME compliant

**Test Case:**
- **Concurrent Operation 1:** R1 requests swap with R2 for 2024-12-20
- **Concurrent Operation 2:** R3 requests swap with R4 for 2024-12-21
- **Concurrent Operation 3:** Mark R5 unavailable on 2024-12-20 (N-1 trigger)
- Execute all 3 operations simultaneously
- Test for race conditions and data consistency

**Expected Outcome:**
- All operations complete without deadlock
- Final state is consistent (no double-bookings, no orphaned assignments)
- ACGME compliance maintained throughout
- Transaction isolation prevents race conditions
- Execution order may vary, but final state is deterministic
- All operations logged with timestamps
- No data corruption

---

## Using Scenarios

### Run Single Scenario

```bash
# Run specific scenario by ID
pytest -m scenario -k "n1-simple-unavailable-001"

# Run with verbose output
pytest -m scenario -k "n1-simple-unavailable-001" -v

# Capture artifacts for debugging
pytest -m scenario -k "n1-simple-unavailable-001" --capture-artifacts
```

### Run Category of Scenarios

```bash
# Run all N-1 scenarios
pytest -m scenario -k "n1-"

# Run all swap scenarios
pytest -m scenario -k "swap-"

# Run all ACGME edge cases
pytest -m scenario -k "acgme-"

# Run all holiday scenarios
pytest -m scenario -k "holiday-"

# Run all moonlighting scenarios
pytest -m scenario -k "moonlight-"

# Run integration scenarios
pytest -m scenario -k "integration-"
```

### Run All Scenarios

```bash
# Run full regression suite
pytest -m scenario

# Run with coverage report
pytest -m scenario --cov=app --cov-report=html

# Run in parallel (faster)
pytest -m scenario -n auto
```

### Generate Scenario Report

```bash
# Generate HTML report
pytest -m scenario --html=scenario-report.html --self-contained-html

# Generate JSON results
pytest -m scenario --json-report --json-report-file=results.json

# Generate summary
pytest -m scenario --tb=short --quiet
```

## Scenario Matrix

| Category | Total | Critical | High | Medium |
|----------|-------|----------|------|--------|
| N-1 Failures | 10 | 6 | 3 | 1 |
| Swap Operations | 5 | 1 | 2 | 2 |
| ACGME Edge Cases | 7 | 7 | 0 | 0 |
| Holiday/Vacation | 4 | 2 | 2 | 0 |
| Moonlighting | 3 | 1 | 2 | 0 |
| Integration | 2 | 2 | 0 | 0 |
| **TOTAL** | **31** | **19** | **9** | **3** |

## Coverage Map

### ACGME Rules Covered
- ✅ 80-hour weekly limit (average over 4 weeks)
- ✅ 1-in-7 day off rule
- ✅ 24-hour duty period limit
- ✅ 8-hour post-call rest requirement
- ✅ 6-night maximum for night float
- ✅ PGY-1 supervision ratio (2:1)
- ✅ PGY-2/3 supervision ratio (4:1)
- ✅ Moonlighting hour limits

### Scheduling Operations Covered
- ✅ Assignment creation
- ✅ Assignment modification
- ✅ One-to-one swaps
- ✅ Multi-swap chains
- ✅ Absorb swaps (give away)
- ✅ Auto-match swap candidates
- ✅ N-1 backup activation
- ✅ Cascade backup chains
- ✅ Schedule generation
- ✅ Leave request processing
- ✅ Concurrent operations
- ✅ Emergency coverage

### Edge Cases Covered
- ✅ Exact boundary conditions (80 hours, 7 days, etc.)
- ✅ Holiday coverage conflicts
- ✅ Weekend minimal staffing
- ✅ Night float rotations
- ✅ Post-call scheduling
- ✅ Multi-level backup chains
- ✅ Supervision ratio enforcement
- ✅ Moonlighting integration
- ✅ TDY/deployment coverage
- ✅ Last-minute emergencies
- ✅ Concurrent operation conflicts
- ✅ Data consistency under stress

## Adding New Scenarios

### Scenario Template

Copy and modify this template for new scenarios:

```yaml
scenario:
  name: "Descriptive scenario name"
  id: "category-operation-case-###"
  category: "n1_failure | swap | acgme_edge | holiday | moonlight | integration"
  priority: "critical | high | medium | low"
  tags: ["tag1", "tag2"]

  description: |
    What this scenario tests and why it matters.

  setup:
    persons: [...]
    rotations: [...]
    assignments: [...]
    constraints: {...}

  test_case:
    operation: "operation_name"
    parameters: {...}

  expected_outcome:
    assertions: {...}
    final_state: {...}
```

### Submit New Scenario

1. Create scenario YAML file in `backend/tests/scenarios/{category}/`
2. Add to scenario library reference (this file)
3. Create pytest test in `backend/tests/scenarios/test_{category}_scenarios.py`
4. Run scenario to verify it works
5. Add to CI test suite

## References

- See `Workflows/scenario-definition.md` for detailed scenario specification
- See `Workflows/scenario-execution.md` for execution details
- See `Reference/success-criteria.md` for pass/fail criteria
- See `backend/tests/scenarios/` for scenario YAML files
