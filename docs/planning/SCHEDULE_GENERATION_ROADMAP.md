# Schedule Generation Roadmap

> **Created:** 2025-12-23
> **Goal:** Generate production-ready schedules with minimal manual intervention
> **Scope:** Block 10 → AY 25-26 → AY 26-27

---

## Executive Summary

| Timeframe | Goal | Success Metric |
|-----------|------|----------------|
| **Today** | Block 10 generated | <5 manual edits needed |
| **This Week** | Rest of AY 25-26 | Remaining blocks (11-13) complete |
| **This Month** | AY 26-27 Development | Framework ready for next year |

---

## Short Term: Block 10 Generation (Today)

### Objective
Generate Block 10 schedule requiring minimal manual edits by user.

### Critical Path Tasks

| # | Task | Owner | Status |
|---|------|-------|--------|
| 1 | **Fix faculty rotation_template_id** | IDE | Required |
| 2 | Validate FMIT week detection | IDE | Required |
| 3 | Generate Block 10 draft | IDE | Required |
| 4 | Run ACGME compliance validation | IDE | Required |
| 5 | Export for user review | IDE | Required |

### Task Breakdown by Interface

#### Claude Code IDE (Today)

**1. Fix Faculty Assignment Template IDs** (BLOCKER)
```
Location: backend/app/scheduling/engine.py
Issue: Faculty assignments created without rotation_template_id
Impact: Faculty-Inpatient Year View shows all zeros
```

Tasks:
- [ ] Read `backend/app/scheduling/engine.py` - locate faculty assignment logic
- [ ] Identify where resident assignments get `rotation_template_id`
- [ ] Apply same pattern to faculty assignments
- [ ] Write unit test for faculty template assignment
- [ ] Run pytest to verify fix

**2. FMIT Week Boundary Validation**
```
Location: backend/app/services/fmit_scheduler_service.py
Issue: FMIT weeks span Fri-Thurs, must align correctly
```

Tasks:
- [ ] Verify FMIT week detection logic (Fri-Thurs boundaries)
- [ ] Test across block boundaries
- [ ] Ensure post-FMIT Friday recovery blocking

**3. Block 10 Generation**
```
Endpoint: POST /api/schedule/generate
Parameters: block_number=10, academic_year=2025
```

Tasks:
- [ ] Ensure test data is seeded for Block 10
- [ ] Trigger schedule generation
- [ ] Review output for conflicts
- [ ] Run ACGME validation
- [ ] Export to Excel for user review

#### Claude Code Web (Today - Limited)

- [ ] Review this roadmap for clarity
- [ ] Answer questions about constraint priorities
- [ ] Review PR after IDE commits changes
- [ ] Provide feedback on generated schedule logic

---

## Medium Term: AY 25-26 Completion (This Week)

### Objective
Complete schedule generation for remaining blocks (11-13) of academic year 2025-2026.

### Prerequisites (from Today's work)
- Faculty template assignment fix deployed
- FMIT boundaries validated
- Block 10 successfully generated

### Task Breakdown

#### Claude Code IDE (This Week)

**Day 1-2: Constraint Refinement**

| Task | Priority | Effort |
|------|----------|--------|
| Implement FacultyRoleClinicConstraint | High | 2-3h |
| Implement FMITWeekBlockingConstraint | High | 3-4h |
| Add unit tests for new constraints | High | 2h |
| Register constraints in scheduler | Medium | 1h |

**Day 3-4: Batch Generation**

| Task | Priority | Effort |
|------|----------|--------|
| Generate Block 11 | High | 1h |
| Generate Block 12 | High | 1h |
| Generate Block 13 | High | 1h |
| Cross-block conflict detection | High | 2h |
| ACGME compliance validation (all blocks) | High | 1h |

**Day 5: Quality Assurance**

| Task | Priority | Effort |
|------|----------|--------|
| Full AY 25-26 schedule export | High | 1h |
| Fairness metrics calculation | Medium | 2h |
| Manual spot-check validation | User | 2h |
| Fix any identified issues | IDE | Variable |

#### Claude Code Web (This Week - Supporting)

- [ ] Review constraint implementation PRs
- [ ] Clarify constraint priorities with user
- [ ] Document constraint interaction rules
- [ ] Review generated schedule summaries
- [ ] Assist with compliance interpretation

### Deliverables

1. **Block 11-13 Schedules** - Generated and validated
2. **Faculty Role Constraints** - Implemented and tested
3. **FMIT Constraints** - Implemented and tested
4. **Full AY Export** - Excel file for user review
5. **Compliance Report** - ACGME validation results

---

## Long Term: AY 26-27 Development (This Month)

### Objective
Build infrastructure for complete next academic year schedule development.

### Phase 1: Data Preparation (Week 1-2)

#### Claude Code IDE

| Task | Description | Effort |
|------|-------------|--------|
| Academic year rollover script | Create AY 26-27 blocks (730 new blocks) | 4h |
| Personnel updates schema | Track PGY level promotions | 2h |
| Rotation template cloning | Copy AY 25-26 templates to 26-27 | 2h |
| Leave/absence migration | Handle multi-year absences | 3h |
| Database migration | Alembic migration for new year | 2h |

#### Claude Code Web

- [ ] Verify academic calendar dates
- [ ] Review PGY promotion logic
- [ ] Confirm template reuse strategy
- [ ] Document rollover procedure

### Phase 2: Constraint Enhancements (Week 2-3)

#### Claude Code IDE

| Constraint | Phase | Priority | Effort |
|------------|-------|----------|--------|
| Call Equity Tracking | 3.2 | High | 3h |
| Sunday Call Equity | 3.2 | High | 2h |
| Tuesday Call Preference | 3.3 | Medium | 2h |
| SM Faculty Alignment | 4.1 | High | 4h |
| Post-Call Auto-Assignment | 4.2 | High | 3h |

#### Claude Code Web

- [ ] Review constraint specifications
- [ ] Clarify edge cases with user
- [ ] Document constraint interactions
- [ ] Review implementation PRs

### Phase 3: Full Year Generation (Week 3-4)

#### Claude Code IDE

| Task | Description | Effort |
|------|-------------|--------|
| Generate Blocks 1-4 (Q1) | First quarter schedule | 2h |
| Generate Blocks 5-8 (Q2) | Second quarter schedule | 2h |
| Generate Blocks 9-13 (Q3-4) | Remaining blocks | 3h |
| Cross-block optimization | Equity across full year | 4h |
| Full year validation | ACGME compliance check | 2h |

### Phase 4: User Acceptance (Week 4)

#### User Tasks (with Claude Web support)

| Task | Description |
|------|-------------|
| Review generated schedules | Spot-check all 13 blocks |
| Identify manual adjustments | Flag issues for refinement |
| Approve or request changes | Feedback loop with IDE |
| Finalize AY 26-27 schedule | Lock for production use |

---

## Interface Comparison: Web vs IDE

### Claude Code Web - Best For

| Activity | Why Web Works |
|----------|---------------|
| **Status reviews** | Quick read-only check |
| **PR reviews** | Comment on code changes |
| **Documentation** | Review/write markdown |
| **Planning** | Discuss strategy |
| **Clarifications** | Answer questions |
| **Small doc edits** | Suggest changes |

### Claude Code IDE - Required For

| Activity | Why IDE Required |
|----------|------------------|
| **Code implementation** | Multi-file edits |
| **Database migrations** | Alembic commands |
| **Test execution** | pytest, npm test |
| **Schedule generation** | API calls, debugging |
| **Git operations** | Branch, commit, push |
| **Debugging** | Read logs, fix issues |

### Handoff Protocol

```
┌─────────────────────────────────────────────────────────┐
│                   TASK ASSIGNMENT                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Does it require...                                     │
│                                                         │
│  ✓ Code changes across files?        → IDE              │
│  ✓ Running tests/commands?           → IDE              │
│  ✓ Database operations?              → IDE              │
│  ✓ Git commits/pushes?               → IDE              │
│                                                         │
│  ✓ Reading/reviewing code?           → Either           │
│  ✓ Documentation review?             → Either           │
│  ✓ Planning/strategy?                → Either           │
│  ✓ Answering questions?              → Either           │
│                                                         │
│  Default: If you're not sure, use IDE.                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Success Metrics

### Block 10 (Today)
- [ ] Schedule generated without errors
- [ ] ACGME validation passes
- [ ] < 5 manual edits required by user
- [ ] Faculty inpatient view shows correct data

### AY 25-26 (This Week)
- [ ] Blocks 11-13 generated
- [ ] All blocks pass ACGME validation
- [ ] Faculty constraints enforced
- [ ] FMIT blocking working correctly
- [ ] User approves final schedule

### AY 26-27 (This Month)
- [ ] Academic year rollover complete
- [ ] All 13 blocks generated
- [ ] Advanced constraints implemented
- [ ] Full year passes ACGME validation
- [ ] Equity metrics within acceptable range
- [ ] User accepts schedule for deployment

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Faculty template fix breaks residents | High | Test both paths separately |
| FMIT boundary spans block edge | Medium | Add cross-block logic |
| Call equity unfair distribution | Medium | Add balancing soft constraint |
| SM alignment impossible | High | Allow manual override flag |
| AY rollover data loss | Critical | Backup before migration |

---

## Next Actions

### Immediate (Start Now - IDE)
1. Fix faculty `rotation_template_id` in scheduling engine
2. Write test to verify fix
3. Generate Block 10

### After Block 10 Success
1. Implement Phase 2 constraints (FacultyRoleClinic, FMIT)
2. Generate remaining AY 25-26 blocks

### After AY 25-26 Complete
1. Design AY 26-27 rollover procedure
2. Implement advanced constraints
3. Full year generation

---

*This roadmap will be updated as milestones are completed.*
