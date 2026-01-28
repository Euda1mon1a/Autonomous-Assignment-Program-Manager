# Residency Scheduling Domain Knowledge

> **Authoritative Reference Document**
> Last Updated: 2026-01-09 | Military Family Medicine Residency

This document is the single source of truth for scheduling domain concepts, terminology, and business rules.

---

## Table of Contents

1. [Terminology Glossary](#1-terminology-glossary)
2. [Academic Year & Block Structure](#2-academic-year--block-structure)
3. [Rotations & Templates](#3-rotations--templates)
4. [Activities & Assignments](#4-activities--assignments)
5. [Supervision Requirements](#5-supervision-requirements)
6. [Call Models](#6-call-models)
7. [Protected Time](#7-protected-time)
8. [Time Away Rules](#8-time-away-rules)
9. [ACGME Compliance](#9-acgme-compliance)
10. [Constraint Hierarchy](#10-constraint-hierarchy)

---

## 1. Terminology Glossary

**Authoritative definitions for scheduling terms.**

| Term | Meaning | Example |
|------|---------|---------|
| **Block** | 28-day scheduling period (4 weeks) | "Block 5 starts March 6" |
| **Rotation** | Multi-week assignment to a template | "On FMIT rotation" |
| **Rotation Template** | Reusable blueprint defining rotation requirements | "FMIT Inpatient template" |
| **Rotation Type** | Category/setting for a rotation template (not an Activity) | `clinic`, `outpatient`, `inpatient`, `education` |
| **Activity** | Slot-level activity vocabulary | "FM Clinic is a clinical activity" |
| **Assignment** | Actualized scheduled slot (solver output) | "Dr. Smith assigned FM Clinic Tue AM" |
| **Slot** | Half-day period (AM or PM) | "Wednesday PM slot" |
| **AT** | Attending Time (supervision coverage unit) | "Requires 2 AT for this clinic" |
| **PCAT** | Post Call Attending Time | "Faculty gets PCAT after overnight call" |
| **DO** | Direct Observation | "Scheduled for DO after weekday call" |

### Terms NOT to Use

| Incorrect | Correct | Reason |
|-----------|---------|--------|
| "730 blocks/year" | "14 blocks/year" | AM/PM periods are **slots**, not blocks |
| "Call block" | "Call shift/duty" | Blocks are 28-day periods only |
| "Schedule block" | "Slot" or "Assignment" | Avoid ambiguity |

---

## 2. Academic Year & Block Structure

### Overview

The academic year runs **July 1 to June 30** and is divided into **14 blocks** (Block 0-13).

| Block | Purpose | Duration | Notes |
|-------|---------|----------|-------|
| **Block 0** | Normalization | Variable (short) | Aligns all blocks to Thu-Wed cycle |
| **Blocks 1-12** | Standard | 28 days each | Thursday start, Wednesday end |
| **Block 13** | AY End | Variable | Always ends June 30 |

### Thursday-Wednesday Cycle

All standard blocks (1-12) follow the Thursday-Wednesday pattern:
- **Start:** Thursday
- **End:** Wednesday (4 weeks later)
- **Purpose:** Consistent handoff day, avoids weekend transitions

### Block 0: The Fudge Factor

Block 0 is a short "normalization" period at the start of the academic year:
- **Purpose:** Ensures all subsequent blocks start on Thursday
- **Duration:** Varies by year (depends on what day July 1 falls on)
- **Example:** If July 1 is a Monday, Block 0 = Mon-Wed (3 days), Block 1 starts Thursday

### Half-Day Slots Within Blocks

Each 28-day block contains **56 half-day slots**:
- 28 days x 2 (AM/PM) = 56 slots per block
- Each slot can hold one **activity** or **assignment**

```
Block Structure:
├── Week 1: 14 slots (7 days x 2 AM/PM)
├── Week 2: 14 slots
├── Week 3: 14 slots
└── Week 4: 14 slots
Total: 56 slots per block
```

---

## 3. Rotations & Templates

### What is a Rotation?

A **rotation** is a multi-week clinical or educational experience:
- Residents are assigned to rotations via **BlockAssignments**
- Each rotation follows a **Rotation Template** blueprint
- One rotation per resident per block (enforced by database constraint)

### Rotation Template Components

A **Rotation Template** defines:

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | Display name | "FMIT Inpatient" |
| `rotation_type` | Rotation category/setting | `inpatient`, `outpatient`, `education` |
| `includes_weekend_work` | Weekend scheduling | `true` for FMIT, `false` for clinics |
| `leave_eligible` | Can take leave | `false` for inpatient |
| `weekly_patterns` | 7x2 activity grid | See Weekly Patterns below |
| `activity_requirements` | Half-day distribution targets | "4 FM Clinic, 5 Specialty" |

### Weekly Pattern Grid

Each rotation template has a **7x2 grid** defining activities per slot:

```
         | Sun | Mon | Tue | Wed | Thu | Fri | Sat |
    AM   | OFF | FM  | FM  | FM  | SP  | SP  | OFF |
    PM   | OFF | SP  | SP  | LEC | SP  | FM  | OFF |
```

- **Week-specific patterns:** Some slots vary by week (e.g., Week 4 Wednesday)
- **Protected slots:** Cannot be modified by solver (`is_protected = true`)

### Inpatient vs Outpatient

| Aspect | Inpatient (FMIT, Night Float) | Outpatient (Clinics) |
|--------|-------------------------------|----------------------|
| **Slots/week** | 12/14 scheduled | 10/14 scheduled |
| **Weekend work** | YES | NO |
| **Call eligible** | NO (already providing coverage) | YES |
| **Leave eligible** | NO | YES |
| **Hours/day** | ~12 hours | ~8-10 hours |

**Terminology note:** “Clinic” is a slot‑level Activity that often appears in
outpatient rotations. Use `rotation_type=outpatient` for the rotation category.

---

## 4. Activities & Assignments

### Activity = Vocabulary/Catalog

**Activities** are the building blocks of schedules:
- Stored in `activities` table
- Define what CAN happen in a slot
- Have properties: category, supervision requirement, protected status

| Category | Examples | Counts Toward Clinical Hours |
|----------|----------|------------------------------|
| `clinical` | FM Clinic, Specialty, Inpatient | Yes |
| `educational` | Lecture (LEC), Conference | No |
| `time_off` | Day Off, Recovery | No |
| `administrative` | Admin duties | No |

### Assignment = Scheduled Instance

**Assignments** are the actual scheduled slots:
- Generated by solver based on templates + constraints
- Links: Person + Date/Slot + Activity
- 56 assignments per resident per 28-day block

### Four-Layer Stack

```
Assignment (actual schedule)
    ↑
Rotation Template (blueprint)
    ↑
Weekly Pattern (7x2 grid)
    ↑
Activity (vocabulary item)
```

---

## 5. Supervision Requirements

### HARD CONSTRAINT - HIGHEST PRIORITY

**Supervision ratios trump everything** - including faculty clinic/admin time.

### Attending Time (AT) Calculation

| Resident Type | AT Value |
|---------------|----------|
| PGY-1 (Intern) | 0.5 AT |
| PGY-2/3 (Senior) | 0.25 AT |

**Rules:**
1. Sum AT values for all residents in clinic
2. Round UP to nearest whole number
3. That's the minimum faculty required

### Calculation Examples

| Scenario | Calculation | Result |
|----------|-------------|--------|
| 4 PGY-2s | 4 x 0.25 = 1.0 | **1 faculty** |
| 4 PGY-3s + 2 PGY-1s | (4 x 0.25) + (2 x 0.5) = 2.0 | **2 faculty** |
| 3 PGY-2s + 1 PGY-1 | (3 x 0.25) + (1 x 0.5) = 1.25 | **2 faculty** (round up) |

### Procedure Clinics: +1 Faculty Rule

Certain clinics require **immediate availability** for supervision:

| Code | Clinic | +1 Required |
|------|--------|-------------|
| PROC | Procedure Clinic | Yes |
| VAS | Vasectomy Clinic | Yes |
| BTX | Botox Clinic | Yes |
| COLPO | Colposcopy Clinic | Yes |

**Example:** 2 AT required + PROC clinic = **3 faculty minimum**

---

## 6. Call Models

### Resident Call

**Resident call is NOT a rotation.** It's a separate duty that enables Night Float coverage.

| Aspect | Details |
|--------|---------|
| **Purpose** | Cover so NF resident can have required day/night off |
| **Who takes call** | Residents on easy outpatient rotations |
| **When** | Varies - enables NF 1-in-7 compliance |
| **Structure** | TBD - significantly different from faculty call |

> **Note:** Full resident call structure is not yet fully documented. Document current understanding only.

### Faculty Call

Faculty have two call modalities:

#### 1. Overnight Call (Sun-Thu)

- Faculty take overnight call Sunday through Thursday
- Provides attending-level backup for inpatient services
- PCAT and DO automatically assigned after weeknight call

#### 2. Weekend FMIT Attending

- Faculty cover Friday and Saturday nights as FMIT attending
- **FMIT faculty do NOT get PCAT/DO** - they're already covering

### PCAT and DO Assignment Rules

| Scenario | PCAT | DO | Reason |
|----------|------|-----|--------|
| After weeknight call (Sun-Thu) | YES | YES | Recovery/observation time |
| After FMIT weekend duty | NO | NO | Already covering Fri/Sat nights |
| Weekends | N/A | N/A | PCAT/DO not needed on weekends |

---

## 7. Protected Time

### Wednesday Constraints (HARD)

Wednesday has **protected educational time** that the solver CANNOT move:

| Week | Wednesday AM | Wednesday PM | Type |
|------|--------------|--------------|------|
| **1-3** | (flexible) | Lecture | **HARD** |
| **4** | Lecture | Advising | **HARD** |

**Key point:** Week 4 is NOT a "soft exception" - it's a different HARD pattern.

### Protected Slot Definition

Slots with `is_protected = true`:
- Solver **CANNOT** modify
- Equivalent in enforcement to ACGME rules
- Include: Wednesday lectures, required training, institutional meetings

---

## 8. Time Away Rules

### Residents: 28-Day Limit

**Core Rule:** If it's not in a rotation template, it's days away from program.

| Absence Type | Counts Toward 28-Day | Counts as Annual Leave |
|--------------|----------------------|------------------------|
| Vacation | YES | YES |
| Conference | YES | NO |
| Medical leave | YES | NO |
| Sick day | YES | NO |
| Day Off (on rotation) | NO | N/A |

**Consequences:**
- **Limit:** 28 days per academic year
- **Exceeding:** Requires training extension
- **Tracking:** Via `is_away_from_program` field on absences

### Faculty: No Limit

- Faculty do NOT have time-away-from-program tracking
- Absences tracked for **coverage purposes only**
- No 28-day limit applies

### TDY vs Deployment

| Duty Type | Residents | Faculty |
|-----------|-----------|---------|
| **TDY** (Temporary Duty) | YES | YES |
| **Deployment** (Combat/Operational) | **NO** | YES |

**TDY for Residents:**
- Away rotations (location-dependent, may require TDY orders)
- Conferences (always counts toward 28-day limit)
- Military training courses

**TDY and Away-From-Program:**
| TDY Type | Counts Toward 28-Day? |
|----------|----------------------|
| Away rotation (still training) | NO |
| Conference | YES |
| Non-training military duty | YES |

**Deployment:**
- Combat zones, operational theaters
- Only faculty can deploy
- Residents cannot be deployed during training

---

## 9. ACGME Compliance

### Tier 0: Absolute Rules (Cannot Be Violated)

| Rule | Limit | Calculation |
|------|-------|-------------|
| **80-hour rule** | 80 hrs/week | 4-week rolling average |
| **1-in-7 day off** | 1 day/7 days | 4-week average |
| **24+4 shift limit** | 28 hours max | 24 duty + 4 transition |
| **Rest between shifts** | 10 hours min | - |

### PGY-Specific Rules

| PGY Level | Shift Limit | Supervision |
|-----------|-------------|-------------|
| PGY-1 | 16 hours max | Direct supervision required |
| PGY-2+ | 24+4 hours | May have indirect supervision |

### Supervision Ratios (ACGME)

| Setting | Ratio |
|---------|-------|
| PGY-1 clinic | 1:2 (1 faculty per 2 interns) |
| PGY-2/3 clinic | 1:4 (1 faculty per 4 seniors) |
| Inpatient | Per census requirements |

---

## 10. Constraint Hierarchy

### Tier System

| Tier | Name | Examples | Violation |
|------|------|----------|-----------|
| **0** | ACGME Absolute | 80-hour, 1-in-7, supervision | NEVER allowed |
| **1** | Institutional Hard | Protected slots, Wednesday LEC | NEVER allowed |
| **2** | Optimization Soft | Half-day distribution, preferences | Penalty-based |
| **3** | Nice-to-Have | Scheduling aesthetics | Lowest priority |

### Priority Levels (for soft constraints)

| Priority | Type | Meaning |
|----------|------|---------|
| 0-30 | SOFT | Nice to have |
| 31-60 | SOFT | Should satisfy |
| 61-90 | SOFT | Strong preference |
| 91-100 | **HARD** | Must satisfy (institutional requirements) |

**Note:** Priority 91-100 is effectively HARD - these are requirements that cannot be violated.

---

## Appendix A: Database Schema Reference

```
rotation_templates (Rotations)
  ├── weekly_patterns (7x2 grid per week)
  │     └── activity_id → activities
  ├── activity_requirements (soft constraints)
  │     └── activity_id → activities
  └── block_assignments (resident assignments)

activities (Slot-level events)
  - FM Clinic, Specialty, LEC, OFF, etc.
  - is_protected for locked slots

absences (Time away)
  - is_away_from_program for 28-day tracking (residents only)
```

---

## Appendix B: Common Patterns

### Outpatient Rotation Example

```
Rotation: Neurology Elective
Weekend Work: NO
Leave Eligible: YES

Weekly Pattern (Mon-Fri only):
         | Mon | Tue | Wed | Thu | Fri |
    AM   | SP  | SP  | SP  | SP  | SP  |
    PM   | SP  | SP  | LEC | SP  | FM  |

Activity Distribution:
- Specialty: 8 slots
- FM Clinic: 1 slot
- Lecture: 1 slot (protected)
```

### Inpatient Rotation Example

```
Rotation: FMIT Inpatient
Weekend Work: YES
Leave Eligible: NO

Weekly Pattern (7 days):
         | Sun | Mon | Tue | Wed | Thu | Fri | Sat |
    AM   | INP | INP | INP | INP | INP | INP | INP |
    PM   | INP | INP | INP | LEC | INP | INP | INP |

Activity Distribution:
- Inpatient: 13 slots
- Lecture: 1 slot (protected)
```

---

## Document History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-09 | Initial canonical document | Claude Code |

---

*This document supersedes all previous scheduling domain documentation.*
