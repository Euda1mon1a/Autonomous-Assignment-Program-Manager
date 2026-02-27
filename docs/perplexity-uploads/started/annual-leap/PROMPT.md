# RESEARCH PROMPT: Block-to-Annual Scheduling Leap
# For: Perplexity Computer (Deep Research + Code Analysis)
# System: Military Family Medicine Residency CP-SAT Scheduler (AAPM)
# Stack: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 15 + OR-Tools CP-SAT 9.8
# Scale: ~12 residents, ~8 faculty, 13 blocks/year (~28 days each), ~4,032 binary vars/block

---

## CONTEXT

This system currently generates schedules **one block at a time** — 13 independent solver runs per academic year. Each block has amnesia: call equity resets, leave spanning block boundaries is invisible, the 1-in-7 rest rule breaks at transitions, and no annual view exists.

The goal is to transform this from **13 independent block schedulers** into a **coherent annual program manager** that tracks longitudinal state across blocks.

### What Exists Today
- CP-SAT solver generates one block's schedule at a time (~28 days, 56 half-day slots)
- `block_assignments` table stores rotation assignments per block per resident
- `call_assignments` table stores call duty assignments with dates
- `absences` table stores leave/absence records
- `person_academic_year` model exists but migration hasn't been applied
- `longitudinal_validator.py` service exists but only validates within a single block
- Per-block ACGME validation works (80-hour rule, 1-in-7, supervision ratios)
- Annual workbook export infrastructure exists but no YTD summary sheet

### What's Missing (The Five Components)
1. **`person_academic_years` migration** — Track PGY level per academic year to prevent July 1 graduation from corrupting historical ACGME data
2. **Faculty call equity YTD hydration** — Inject year-to-date call history into the solver so Block 10 knows about Blocks 1-9
3. **Cross-block leave continuity** — Validate absences spanning block boundaries, sync to preloads
4. **Cross-block 1-in-7 boundary validation** — Sliding window that crosses block boundaries for ACGME rest compliance
5. **Annual workbook YTD_SUMMARY sheet** — Cross-block aggregation in the Excel export

### Uploaded Files
- `models/` — SQLAlchemy ORM models (person, person_academic_year, block_assignment, absence, call_assignment)
- `scheduling/` — ACGME compliance engine
- `constraints/` — CP-SAT constraint definitions (call_equity, acgme, base, config, equity, manager)
- `services/` — Longitudinal validator, export service, half-day import service
- `routes/` — Block assignment admin routes
- `docs/` — Architecture documents (Faculty Fix Roadmap, Excel Stateful Roundtrip Roadmap, Annual Workbook Architecture)

### Prior Research Available (Completed Perplexity Sessions)
Six parallel research sessions have already completed. Their findings are summarized below as constraints and inputs for THIS session. Do not re-research topics already covered — build on them.

**1. Full-Stack Audit (completed):**
- CP-SAT weight sweep: 2,100 configs tested; current weights (1000/10/5) are in optimal range
- **KEY FINDING:** EQUITY_PENALTY_WEIGHT=35 gives ~10pp improvement in P(equity ≤ 7) — directly relevant to Section 3
- **KEY FINDING:** Rec 4 says upgrade equity penalty from range to MAD using `add_abs_equality` — this is the formulation the annual equity system should use
- **KEY FINDING:** ACGME audit found MIN_REST_BETWEEN_SHIFTS=8 is incomplete — missing the binding 14-hour post-24hr-call Core requirement (ACGME §6.21.a). The cross-block 1-in-7 validator in Section 1 must also enforce this rule at boundaries.

**2. OR-Tools 9.8→9.12 Migration Analysis (completed):**
- **KEY FINDING:** v9.12 hint system fully rewritten — complete hints now survive presolve. This means warm-starting Block N+1 with Block N's schedule as a hint is now viable. Section 3 should assume hint-based warm-start is available.
- **KEY FINDING:** `add_abs_equality` is the recommended approach for MAD (Mean Absolute Deviation) equity formulation in CP-SAT
- **KEY FINDING:** `best_bound_callback` (new in v9.10) enables real-time monitoring of equity convergence
- PEP 8 rename: all CamelCase methods deprecated in favor of snake_case (relevant for code patterns)

**3. Exotic Research — Physics-Based Scheduling (completed):**
- **KEY FINDING:** Burstiness parameter B measures temporal equity — how unevenly assignments are distributed over time. B > 0.3 indicates bursty (crunch-then-rest) patterns. This is a complementary metric to longitudinal call count equity. Section 3 should consider burstiness as a second equity dimension.
- **KEY FINDING:** ACO (Ant Colony Optimization) warm-start from stigmergy.py can generate complete hints for CP-SAT, achieving 30-70% faster time-to-first-incumbent. This pairs with the v9.12 hint fix to enable cross-block warm-starting.
- **KEY FINDING:** CMA-ES bilevel weight optimization (outer loop: CMA-ES proposes 25-dim weight vectors; inner loop: CP-SAT solves with those weights) can improve schedule quality 5-20%. When equity weight changes for longitudinal tracking, the weight landscape shifts and should be re-swept.

**4. PostgreSQL 15 Tuning Analysis (completed):**
- **KEY FINDING:** The YTD hydration query for call equity maps to existing query pattern #5: `CallAssignment by person_id with date range, ORDER BY date` — covered by `idx_call_assignments_person_date`. The 3-column index `(person_id, date, call_type)` is recommended for the full YTD query.
- **KEY FINDING:** PG tuning recommends pushing equity aggregation to SQL (`GROUP BY person_id` with `func.count().filter()`) instead of fetching raw rows — 98% less data transfer. The YTD hydration query should use this pattern.
- **KEY FINDING:** `MERGE` statement (PG15) can replace 4 upsert patterns including HalfDayAssignment, reducing round trips by 50%. Relevant for leave-to-preload sync in Section 4.
- **KEY FINDING:** `half_day_assignments(person_id, date, time_of_day)` unique index is the P0 recommendation — highest-impact single index. Must exist before implementing leave continuity sync.

**5. Competitive Intel (completed):**
- Market has 13,762 ACGME programs and 167,083 active trainees
- No competitor does true cross-block optimization — this IS the competitive moat
- QGenda and Amion both handle annual views but not solver-integrated longitudinal equity

**6. Section 508 Accessibility Audit (completed):**
- Not directly relevant to this session but the annual workbook export should consider accessible Excel patterns (proper table headers, alt text for conditional formatting)

---

## SECTION 1: Longitudinal ACGME Validation Patterns
**Goal:** Research how other medical scheduling systems handle cross-block/cross-rotation ACGME compliance.

### Prior Research Constraints
- Our audit found MIN_REST_BETWEEN_SHIFTS=8 is incomplete — missing the binding 14-hour post-24hr-call requirement (ACGME §6.21.a). The cross-block validator must also enforce this at boundaries.
- No competitor does true cross-block solver-integrated validation — we'd be first. Focus on what ACGME actually requires, not what competitors do.

### Research Questions
1. What is the correct interpretation of the ACGME Common Program Requirements (Section VI) for the 1-in-7 rest rule at rotation transitions? Does the 7-day window reset, carry over, or use a sliding window?
2. How should the 80-hour weekly average be computed when a resident transitions between blocks with different duty patterns? Is this a 4-week rolling average or per-rotation average?
3. What are the ACGME site visit audit patterns — do surveyors look at per-rotation compliance or longitudinal compliance across the academic year? What specific reports do they request?
4. ACGME §6.21.a requires a 14-hour maximum shift after a 24-hour call period. How does this interact with block boundaries — if a 24hr call ends at 7am on the last day of Block 9, what constraints apply to the first day of Block 10?
5. Research "protected time" carryover — if a resident's protected time is disrupted at a block boundary, how should that be tracked for ACGME compliance?

### Analysis of Uploaded Code
- Read `scheduling/acgme_compliance_engine.py` — find the current 1-in-7 implementation and identify the boundary gap
- Read `services/longitudinal_validator.py` — understand what it currently validates and what's missing
- Read `constraints/acgme.py` — find all ACGME rule implementations and identify which need cross-block awareness

### Deliverables
- Summary of ACGME Common Program Requirements Section VI with emphasis on boundary/transition rules
- Recommended sliding window algorithm for cross-block 1-in-7 validation, including the 14-hour post-call rule
- SQL query pattern for "look back N days from block start into previous block's assignments"
- Pseudocode for a `validate_block_boundary(block_n_assignments, block_n1_assignments)` function
- Test case: 6-day consecutive run ending Block 9 Thursday → what must Block 10 enforce?

---

## SECTION 2: Academic Year Rollover Strategies
**Goal:** Research best practices for PGY level tracking and academic year transitions in medical education systems.

### Research Questions
1. How do medical education management systems (MedHub, New Innovations, ACGME WebADS) handle the July 1 PGY advancement?
2. What happens to historical compliance data when a PGY-1 becomes PGY-2? Do the ACGME rules change retroactively for the historical period?
3. How should call count equity reset on July 1? Complete reset, weighted carryover, or exponential decay? (Our exotic research identified burstiness parameter B as a complementary metric — should B also reset?)
4. What is the data model for tracking a person across multiple academic years while preserving historical PGY-specific constraints?
5. How do programs handle mid-year PGY changes (leaves of absence, remediation, early graduation)?

### Analysis of Uploaded Code
- Read `models/person_academic_year.py` — analyze the existing model design, identify missing columns
- Read `models/person.py` — identify where `pgy_level` is currently stored and all code that reads it
- Read `constraints/acgme.py` — find all references to PGY level and assess what needs to become history-aware
- Read `docs/excel-stateful-roundtrip-roadmap.md` Track A — analyze the existing rollover spec

### Deliverables
- Data model recommendation: `person_academic_years` table schema with all needed columns (including call_count_ytd for equity tracking)
- Alembic migration strategy: how to seed from existing `Person.pgy_level` without data loss, including the seed SQL
- API design: REST endpoints for querying person-by-academic-year (GET /api/persons/{id}/academic-years)
- Rollover service spec: what happens on July 1 (advance PGY, handle graduates, reset counters, preserve history)
- Edge case analysis: mid-year transfers, leaves of absence, dual-track residents, preliminary year completions

---

## SECTION 3: Cross-Block Equity Optimization
**Goal:** Research constraint programming techniques for longitudinal equity across independent solver runs.

### Prior Research Constraints (CRITICAL — build on these, don't re-derive)
- **Weight sweep result:** EQUITY_PENALTY_WEIGHT=35 is optimal for single-block. With YTD history injected, the weight landscape shifts — recommend re-sweep strategy.
- **MAD formulation:** The full-stack audit recommends upgrading equity penalty from range to MAD using `add_abs_equality`. This is the formulation to use.
- **Burstiness:** The exotic research provides a burstiness parameter B that measures temporal equity. Longitudinal call COUNT equity (Section 3) + temporal burstiness equity (exotic) form a 2D equity surface.
- **Warm-start:** OR-Tools v9.12 fixes the hint system. ACO warm-start from stigmergy.py generates complete hints achieving 30-70% faster TTFI. Prior block's solution can seed next block's hints.
- **PG query pattern:** YTD hydration should use SQL aggregation: `SELECT person_id, call_type, COUNT(*) FROM call_assignments WHERE date BETWEEN :year_start AND :block_start GROUP BY person_id, call_type`. Index `(person_id, date, call_type)` is recommended.

### Research Questions
1. Given the MAD formulation with `add_abs_equality`, what is the exact CP-SAT code pattern for: `minimize sum(|prior_calls[f] + current_calls[f] - target_mean|)` where `prior_calls[f]` is a constant and `current_calls[f]` is a variable?
2. How do nurse rostering and airline crew scheduling systems handle multi-period equity with rolling horizons?
3. When injecting N faculty × K call_types of history constants into CP-SAT, what is the solver performance impact? Our model has ~4,032 vars — does adding 8×3=24 constants change solve time measurably?
4. Should the equity objective use `prior + current` (additive) or `weighted_prior + current` (decay)? What does the operations research literature recommend for fairness in sequential scheduling?
5. After injecting YTD history, the 25-dim weight landscape from the weight sweep shifts. What is the most efficient re-sweep strategy? (CMA-ES bilevel from exotic research? Focused sweep on just EQUITY_PENALTY_WEIGHT?)

### Analysis of Uploaded Code
- Read `constraints/call_equity.py` — understand the current single-block equity mechanism, find where MAD formulation should replace range
- Read `constraints/base.py` — find `SchedulingContext` and identify where `prior_calls` dict should be added
- Read `constraints/config.py` — find EQUITY_PENALTY_WEIGHT and understand the weight system
- Read `constraints/equity.py` — understand the generic equity constraint pattern
- Read `docs/FACULTY_FIX_ROADMAP.md` Phase 1 — analyze the YTD hydration design (steps 1A-1D)

### Deliverables
- **CP-SAT code pattern:** Complete Python function `inject_ytd_equity(model, context, prior_calls)` using `add_abs_equality` for MAD formulation
- **SQL hydration query:** Exact SQLAlchemy query to populate `prior_calls` dict from `call_assignments` table
- **Mathematical proof:** That `minimize max(prior + current)` converges to longitudinal equity as blocks progress
- **Weight re-sweep strategy:** Recommended approach after YTD injection (focused CMA-ES? grid search on equity weight only?)
- **Warm-start pattern:** How to use Block N's solution as hint for Block N+1 via `model.add_hint()` (leveraging v9.12 fix)
- **Performance benchmark design:** Test plan measuring solver time with 0, 12, 24, 48 history constants

---

## SECTION 4: Leave Continuity Across Block Boundaries
**Goal:** Research absence management patterns for scheduling systems with discrete planning periods.

### Prior Research Constraints
- PG tuning found the P0 index recommendation is `half_day_assignments(person_id, date, time_of_day)` — this must exist before implementing leave-to-preload sync
- PG15 `MERGE` statement can replace the current SELECT-then-INSERT upsert pattern for HalfDayAssignment, reducing round trips by 50%
- The full-stack audit found Excel import has XSS/injection bugs (BUG-01 through BUG-03) — the LV code import pipeline must sanitize inputs

### Research Questions
1. How do enterprise scheduling systems handle leave requests that span planning period boundaries?
2. What is the correct data model for "event-sourced" absences vs. "stamped" absences? Which is more appropriate for a block-based scheduling system?
3. How should preloaded schedule slots (solver-bypassed assignments) be synced when an absence is created/deleted? What are the cascade rules?
4. What integrity constraints should exist between the `absences` table and `block_assignments`/`half_day_assignments`?
5. How should Excel import of "LV" codes create `Absence` records while sanitizing against injection (per full-stack audit findings)?

### Analysis of Uploaded Code
- Read `models/absence.py` — understand the current absence data model
- Read `services/half_day_import_service.py` — find how "LV" codes are (or aren't) handled during import, and note the sanitization gaps
- Read `routes/admin_block_assignments.py` — find the `"absences": [] # TODO` placeholder
- Read `docs/excel-stateful-roundtrip-roadmap.md` Track C — analyze the leave event-sourcing spec

### Deliverables
- **Data model:** absence-to-preload sync integrity rules, including FK constraints and triggers
- **Import pipeline:** How to create `Absence` records from Excel "LV" codes with input sanitization
- **Cross-block validation:** Algorithm for detecting leave that spans Block N → Block N+1, including edge cases (leave starts mid-block, ends mid-next-block)
- **Cascade rules:** Complete state machine for absence lifecycle (create → preloads generated → delete → stale preloads cleaned)
- **MERGE pattern:** PG15 MERGE statement for the HalfDayAssignment upsert during preload sync
- **Event sourcing pattern:** Making `absences` the single source of truth, including migration plan to drop `has_leave`/`leave_days` from `block_assignments`

---

## SECTION 5: Annual Workbook Design Patterns
**Goal:** Research Excel workbook design patterns for multi-period schedule aggregation.

### Prior Research Constraints
- The 508 accessibility audit is complete — the annual workbook should use proper table headers and avoid color-only information encoding
- Competitive intel shows no competitor produces a true cross-block annual workbook — this is a differentiator

### Research Questions
1. How do large scheduling systems present annual/multi-period views in Excel exports?
2. What Excel formula patterns work best for cross-sheet aggregation (SUMIF, SUMPRODUCT, INDIRECT)? Which are most robust when sheets are added/removed?
3. How should a YTD summary sheet be structured for ~50 faculty rows with hide/show logic?
4. What is the formula for "FMIT weeks = total_half_days / 14" and how should it handle partial blocks?
5. How do other military medical facilities present annual scheduling data to ACGME site visitors? What format do surveyors expect?

### Analysis of Uploaded Code
- Read `services/canonical_schedule_export_service.py` — understand the current export infrastructure, find where `_build_ytd_summary_sheet()` should be added
- Read `docs/annual-workbook-architecture.md` — analyze the full 14-sheet workbook spec
- Read `docs/FACULTY_FIX_ROADMAP.md` Phase 3 — analyze the 15-sheet faculty workbook spec with 50-row grid

### Deliverables
- **YTD_SUMMARY sheet specification:** Complete column layout, formula definitions, row structure
- **Cross-sheet SUMIF pattern:** Exact Excel formulas for aggregating FMIT/clinic/AT across 14 block sheets (with proper sheet name references)
- **Faculty row layout:** 50-row grid design with conditional row hiding for inactive faculty
- **FMIT weeks calculation:** Formula handling partial blocks and the 14-half-day-per-week conversion
- **Accessibility compliance:** Proper table headers, alt text patterns, avoiding color-only encoding (per 508 audit)
- **ACGME presentation format:** Recommended layout for site visit documentation

---

## SECTION 6: Synthesis & Implementation Roadmap
**Goal:** Synthesize findings from Sections 1-5 AND all prior research into an actionable implementation plan.

### Cross-Session Integration
This section must integrate findings from ALL completed research sessions:
- Full-stack audit critical items (auth gaps, XSS in import, ACGME §6.21.a gap)
- OR-Tools v9.12 migration (hint system fix enables warm-start, PEP 8 rename needed)
- Exotic research (burstiness as equity dimension, ACO warm-start, CMA-ES re-sweep)
- PG tuning (index prerequisites, MERGE pattern, SQL aggregation pattern)
- Competitive intel (no competitor does cross-block optimization — this is the moat)

### Deliverables
1. **Dependency graph** showing which components must be built first, INCLUDING prerequisites from other research sessions (e.g., PG indexes before leave sync, OR-Tools upgrade before warm-start)
2. **Risk register** for each component (technical risk, data migration risk, July 1 deadline risk)
3. **Testing strategy** for each component:
   - Unit tests (mock data, specific inputs/expected outputs)
   - Integration tests (multi-block scenarios with real query patterns)
   - Regression tests (existing single-block behavior must not break)
   - Performance tests (solver time with YTD history injection)
4. **Migration plan** for `person_academic_years` table:
   - Seed script from existing `Person.pgy_level` with exact SQL
   - Rollback strategy (Alembic downgrade)
   - Zero-downtime deployment approach
5. **Verification checklist:**
   - Generate Block 10 with YTD call history → verify equity across Blocks 1-10
   - Import Excel with LV code spanning block boundary → verify Absence created + preloads correct
   - Create 6-day run ending Block 9 → generate Block 10 → verify 1-in-7 flag at boundary
   - Export annual workbook → verify YTD_SUMMARY formulas compute across all sheets
   - Simulate July 1 graduation → verify PGY-1→PGY-2 transition preserves historical data
   - Run full ACGME compliance check → verify institution-wide (not just per-block) report
   - Warm-start Block 10 with Block 9 hint → verify convergence speedup
   - Run burstiness check across all 10 blocks → verify B < 0.3 for all residents
6. **Execution timeline** with the recommended order:
   ```
   Component 2 (call equity YTD) ← smallest, highest impact, no migration
       ↓
   Component 1 (person_academic_years) ← migration, July 1 deadline
       ↓
   Components 3 + 4 in parallel (leave continuity + 1-in-7 boundary)
       ↓
   Component 5 (YTD_SUMMARY sheet) ← the visible annual dashboard
   ```

---

## OUTPUT FORMAT

For each section, produce:
1. **Research findings** with citations (papers, ACGME documents, product documentation)
2. **Code patterns** — concrete Python/SQL snippets using snake_case (OR-Tools PEP 8 convention) that can be integrated into the codebase
3. **Data model diagrams** — ERD fragments showing table relationships
4. **Test scenarios** — specific test cases with expected inputs/outputs
5. **Risk assessment** — what could go wrong and how to mitigate

**IMPORTANT:** Do not re-derive findings from prior sessions. Reference them as given constraints. Focus research energy on the NEW questions unique to the block-to-annual transformation.

Combine all sections into a single comprehensive report titled:
**"Block-to-Annual Scheduling Transformation: Research & Implementation Guide"**

The report should be directly actionable by a Claude Code agent implementing these changes.
