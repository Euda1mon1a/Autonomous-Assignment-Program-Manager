# Leadership Discussion Guide: Edge Cases & Policy Decisions

**Purpose:** Pre-deployment discussion topics for PD, APD, and Clinic OIC
**Context:** The scheduler is technically ready. These are the *human* edge cases that need policy decisions before go-live.

---

## Your Stated Preferences (Baseline)

1. **Auto-approve faculty swaps** if no external party impact - log with gaming flags
2. **PD/APD/OIC can force swaps** for coverage needs (e.g., family emergency)
3. **Log everything** and factor forced swaps into fairness calculations

---

## Part 1: Defining "External Party Impact"

Before auto-approving swaps, we need a clear definition of what counts as "affecting external parties."

### Discussion Questions:

| Scenario | External Impact? | Suggested Policy |
|----------|------------------|------------------|
| Faculty A and B swap weeks, both are clinic weeks | No | Auto-approve |
| Faculty swaps FROM clinic week TO admin week | **Maybe** - patients may be scheduled | Depends on timing (see below) |
| Faculty swaps INTO a week with resident supervision duties | **Yes** - resident needs compatible faculty | Check supervision requirements |
| Faculty swaps week where MSA already opened slots | **Yes** - slots may have patients | Require MSA confirmation or time window |
| Faculty swaps during resident evaluation period | **Maybe** - affects who does the eval | Policy decision needed |

### Recommended Thresholds:

**Auto-approve if ALL true:**
- [ ] Both parties consented (in system)
- [ ] Same "weight" of week (clinic↔clinic, admin↔admin)
- [ ] >14 days before effective date (MSAs haven't opened slots yet)
- [ ] No residents assigned who require specific faculty supervision
- [ ] Neither week is during a scheduled evaluation period

**Flag for review if ANY true:**
- [ ] <14 days before effective date (slots may be opened)
- [ ] Involves supervision mismatch (e.g., OB faculty swapping with FM-only faculty)
- [ ] Faculty has swapped >3 times this quarter (gaming detection)
- [ ] Swap creates coverage gap in specialty area

**Question for PD:** What's your cutoff? 14 days? 7 days? Should MSA confirmation be required after slots are opened?

---

## Part 2: Forced Swaps (Coverage Mode)

When PD/APD/OIC needs to pull someone from admin to cover clinic due to emergency.

### Scenarios to Discuss:

#### Scenario A: Simple Coverage Pull
```
Dr. Smith (Clinic) has family emergency, can't come in
Dr. Jones (Admin) is available and qualified
OIC reassigns Dr. Jones to clinic
```

**Questions:**
1. Does Dr. Jones get "credit" for the disruption? (Logged as "forced into clinic" for fairness tracking)
2. Does Dr. Smith get "debit"? (Logged as "caused coverage gap")
3. If Dr. Smith's emergency was legitimate, should it affect their fairness score at all?

**Suggested Policy:**
- Log forced swaps separately from voluntary swaps
- Track "disruption absorbed" as positive fairness credit
- Track "disruption caused" but weight by reason (emergency = 0 penalty, pattern of emergencies = flag for discussion)

#### Scenario B: No One Available
```
Dr. Smith (Clinic) has emergency
All other faculty on admin/leave/at conference
```

**Questions:**
1. Can residents run clinic without faculty? (ACGME supervision rules)
2. Do you cancel clinic? Who decides?
3. Is there a "reservist" call list (retired faculty, locums)?

**Need from OIC:** What's the escalation path when coverage is impossible?

#### Scenario C: Cascade Effect
```
Dr. Smith's emergency → Dr. Jones pulled from admin
But Dr. Jones was doing chart reviews for ACGME compliance
Now ACGME deadline may be missed
```

**Question for PD:** Priority ranking when you can't have both:
- [ ] Patient care always #1
- [ ] ACGME compliance
- [ ] Administrative duties
- [ ] Faculty wellbeing (not burning out the same people)

---

## Part 3: Gaming Detection

What patterns indicate someone is gaming the system vs. legitimate needs?

### Red Flags to Discuss:

| Pattern | Possible Gaming | Possible Legitimate | How to Handle |
|---------|-----------------|---------------------|---------------|
| Blocks ALL holiday weeks | Yes | Childcare during school breaks | Max blocked weeks policy |
| Swaps away from every Friday clinic | Yes | Recurring commitment (board position) | Require documentation for patterns |
| Always swaps with same person | Possible collusion | Compatible schedules | Flag but allow |
| Requests swap <48 hours before | Irresponsible | True emergency | Require reason code |
| High swap count (>6/quarter) | Possible | Life circumstances | Flag for check-in, not auto-deny |

### Suggested Gaming Thresholds:

**Auto-flag for human review:**
- >4 swaps in a single quarter
- >2 blocked weeks adjacent to holidays
- Swap requested <72 hours before effective date
- Same two people swapping >3 times per year

**Question for PD:**
- Should gaming flags be visible to the faculty member? ("You've blocked 3 holiday-adjacent weeks, which is above average")
- Or private to leadership only?

---

## Part 4: Biggest Morale Killers

Based on residency scheduling literature and common patterns:

### 1. **Perception of Unfairness** (Even When Mathematically Fair)

**The Problem:**
- Faculty see Dr. X always has Thanksgiving off
- System shows Dr. X worked Memorial Day + July 4th to earn it
- But *perception* is "Dr. X gets holidays"

**Mitigation Options:**
- [ ] Public fairness dashboard (everyone sees everyone's scores)
- [ ] Quarterly "state of fairness" report from PD
- [ ] Let people see *why* assignments were made ("explain_json" exists in system)

**Question for PD:** How transparent do you want to be? Full public transparency or "trust the system"?

### 2. **Last-Minute Changes Without Warning**

**The Problem:**
- Faculty planned around their schedule
- Schedule changes 3 days before
- Life plans disrupted, spouse angry, childcare scrambled

**Mitigation Options:**
- [ ] Hard freeze at X days out (no changes without OIC override)
- [ ] Mandatory notification + acknowledgment for any change
- [ ] "Disruption compensation" - get first pick next quarter if disrupted this quarter

**Question for PD:** What's your freeze window? 14 days? 7 days? Or just "best effort"?

### 3. **The "Martyrs" and "Evaders"**

**The Problem:**
- Some faculty always say yes, absorb extra burden
- Others always have excuses, shed burden
- Martyrs burn out, evaders coast

**System Already Tracks:**
- "Burden absorbed" score (who picks up slack)
- "Burden shed" score (who causes reassignments)
- Can identify MARTYR and EVADER patterns

**Mitigation Options:**
- [ ] Auto-protect martyrs (block them from accepting more swaps when overloaded)
- [ ] Auto-scrutinize evaders (require PD approval for their swap requests)
- [ ] Quarterly check-in with identified martyrs (are they okay?)

**Question for PD:** Should the system auto-protect martyrs, or is that paternalistic?

### 4. **New Faculty vs. Senior Faculty**

**The Problem:**
- New faculty don't know the "good" weeks vs. "bad" weeks
- Senior faculty already claimed holiday-adjacent blocks
- New faculty feels stuck with leftovers

**Mitigation Options:**
- [ ] Protected first-year: new faculty get median assignment quality, not leftovers
- [ ] Seniority weight: senior faculty get small preference boost
- [ ] No seniority: strict fairness regardless of tenure

**Question for PD:** What's the culture you want? Seniority privileges or strict equality?

### 5. **External Commitments Collision**

**The Problem:**
- Dr. X has a military drill weekend (non-negotiable)
- Dr. Y has CME conference they paid for
- Dr. Z is on a national board that meets quarterly
- All three need the same week off

**Current System:** Treats all absences equally

**Mitigation Options:**
- [ ] Priority ranking: Military > pre-paid CME > recurring board > preference
- [ ] First-come-first-served: whoever submitted first wins
- [ ] Negotiated: PD mediates conflicts manually

**Question for PD:** Is there a priority order for external commitment types?

### 6. **The "Invisible Workload" Problem**

**The Problem:**
- Clinic week ≠ clinic week
- Wednesday PM clinic with 20 complex patients ≠ Friday AM clinic with 8 simple f/u
- System treats them as equal "half-day blocks"

**Current System:** No weighting by patient complexity or volume

**Future Option:** Could integrate with MHS Genesis for slot counts, but manual for now

**Question for OIC:** Should we weight clinic sessions by expected difficulty? Or is a half-day a half-day?

---

## Part 5: Hard Decisions That Will Happen

These situations WILL occur. Better to have a policy than improvise.

### Decision 1: "I Can't, But I Won't Say Why"

**Scenario:** Faculty declines swap/assignment, won't give reason (could be health, personal crisis, just doesn't want to)

**Options:**
- A) Accept it, no questions (privacy respected, but opens gaming)
- B) Require reason for pattern (3rd decline = must talk to PD)
- C) Require reason always (invasive, but transparent)

**Recommendation:** Option B - trust but verify patterns

### Decision 2: Two Emergencies, One Slot

**Scenario:** Dr. A's kid is sick, Dr. B's parent is dying. Both need the same day off. No other coverage.

**Options:**
- A) First to call in wins
- B) PD makes judgment call on severity
- C) Both get the day, clinic runs short-staffed

**Recommendation:** PD judgment call, logged with rationale

### Decision 3: The Chronic Problem

**Scenario:** Faculty has pattern of last-minute call-outs (>4/quarter). May be burnout, health issue, or reliability problem.

**Options:**
- A) Formal performance conversation
- B) Reduce their clinic load preemptively (protect patients)
- C) Refer to wellness resources, no schedule changes
- D) Combination

**Recommendation:** Wellness check-in first, then performance if pattern continues

### Decision 4: The Schedule Complainer

**Scenario:** Faculty constantly complains schedule is unfair, despite metrics showing fairness.

**Options:**
- A) Show them the data (transparency)
- B) Acknowledge feelings, don't argue data
- C) Investigate if their perception reveals blind spot in metrics

**Recommendation:** Show the data ONCE. If complaints continue, investigate their specific concern - they may see something the algorithm misses.

### Decision 5: Resident vs. Faculty Conflict

**Scenario:** Resident complains faculty supervisor is always unavailable during their shared clinic time (faculty doing admin in their office).

**This is serious:** ACGME supervision requirements

**Options:**
- A) Address with faculty directly
- B) Reassign resident to different faculty
- C) Both

**Recommendation:** Address immediately - this is a compliance issue, not just morale

---

## Part 6: What the System WILL Track (For Your Awareness)

The following metrics will be visible to admins/leadership:

| Metric | Purpose | Privacy Level |
|--------|---------|---------------|
| Swap count per faculty | Gaming detection | Admin only |
| Burden absorbed score | Martyr identification | Admin only |
| Burden shed score | Evader identification | Admin only |
| Blocked weeks count | Fairness | Admin only |
| Holiday distribution | Fairness | Can be public |
| Overall workload (Gini coefficient) | System fairness | Should be public |
| Last-minute changes caused | Reliability | Admin only |
| Coverage gap incidents | Operational health | OIC + Admin |

**Question for PD:** Which metrics should be visible to all faculty vs. leadership only?

---

## Summary: Decisions Needed Before Go-Live

### Must Decide:

1. **Auto-approve threshold:** How many days out can swaps auto-approve? (Suggested: 14 days)
2. **External impact definition:** What counts as affecting external parties?
3. **Gaming thresholds:** How many swaps/blocked weeks trigger review?
4. **Transparency level:** Public fairness dashboard or trust-the-system?
5. **Freeze window:** When do schedules become immutable without OIC override?
6. **Forced swap credit:** How do we compensate faculty who absorb disruptions?
7. **Priority ranking:** Military vs. CME vs. board vs. preference

### Should Discuss:

8. Seniority privileges: Yes or strict equality?
9. Martyr auto-protection: Should system block overloaded faculty from accepting more?
10. Wellness escalation: At what pattern does scheduling data trigger wellness check-in?

### Nice to Align On:

11. Clinic weighting: Is a half-day a half-day, or should we weight by difficulty?
12. New faculty protection: Guarantee median quality assignments for first year?
13. Complainer protocol: How do we handle perception vs. reality disputes?

---

## Appendix: Swap Auto-Approval Logic (Technical Reference)

```
IF swap_request.days_until_effective > THRESHOLD_DAYS
   AND both_parties_consented = TRUE
   AND week_type_match(from_week, to_week) = TRUE  # clinic↔clinic, admin↔admin
   AND no_supervision_mismatch(from_week, to_week) = TRUE
   AND slots_not_opened_in_ehr(from_week, to_week) = TRUE
   AND faculty_swap_count_this_quarter < MAX_AUTO_SWAPS
THEN
   AUTO_APPROVE
   LOG(swap, reason="auto_approved", flags=[])
ELSE
   QUEUE_FOR_REVIEW
   LOG(swap, reason="needs_review", flags=[triggered_conditions])
```

**Configurable Parameters:**
- `THRESHOLD_DAYS`: 14 (suggested)
- `MAX_AUTO_SWAPS`: 4 per quarter (suggested)
- `REQUIRE_REASON_AFTER`: 3 declines (suggested)

---

*Document prepared for leadership discussion*
*System: Residency Scheduler v1.0*
