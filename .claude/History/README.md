# History System - Residency Scheduler PAI

> **Purpose:** Permanent audit trail for schedule operations, compliance decisions, and incidents
> **Retention:** Varies by type (see below)
> **Integration:** Feeds MetaUpdater for continuous improvement

---

## Overview

The History system provides a permanent, searchable record of all significant operations performed by the Residency Scheduler AI system. Unlike logs (which are transient and technical), History entries are:

- **Human-readable**: Written in markdown with clear context
- **Decision-focused**: Document *why* decisions were made, not just *what* happened
- **Audit-compliant**: Sufficient detail for ACGME audits and compliance reviews
- **Pattern-detectable**: Enable MetaUpdater to identify recurring issues and optimization opportunities
- **Searchable**: Structured format enables grep/search for rapid investigation

**Key Principle:** History is the institutional memory of the scheduling system. If an operation might need to be explained 6 months from now (to faculty, auditors, or future developers), it belongs in History.

---

## Directory Structure

```
.claude/History/
├── README.md                          # This file
├── scheduling/                        # Schedule generation records
│   ├── TEMPLATE.md                    # Template for new entries
│   ├── 2025-07-15_block10_gen001.md   # Example: Block 10 generation
│   └── 2025-09-01_academic_year.md    # Example: Full year generation
├── swaps/                             # Swap execution records
│   ├── TEMPLATE.md                    # Template for new entries
│   ├── 2025-08-03_swap_s12345.md      # Example: One-to-one swap
│   └── 2025-08-10_chain_c67890.md     # Example: Chain swap
├── compliance/                        # ACGME compliance audits
│   ├── 2025-07-31_monthly_audit.md    # Example: Monthly compliance review
│   └── 2025-08-15_violation_v001.md   # Example: Violation remediation
├── resilience/                        # Resilience health assessments
│   ├── 2025-07-20_n1_analysis.md      # Example: N-1 contingency test
│   └── 2025-08-01_health_check.md     # Example: Monthly health assessment
└── incidents/                         # Production incidents and postmortems
    ├── TEMPLATE.md                    # Template for new entries
    └── 2025-08-05_solver_timeout.md   # Example: Solver performance incident
```

---

## Naming Convention

All History entries follow this format:

```
YYYY-MM-DD_<type>_<identifier>.md
```

**Components:**
- `YYYY-MM-DD`: Date of operation (ISO 8601)
- `<type>`: Short descriptor (e.g., `block10`, `swap`, `audit`, `incident`)
- `<identifier>`: Unique ID (e.g., generation ID, swap ID, incident number)

**Examples:**
```
2025-07-15_block10_gen001.md          # Block 10 schedule generation
2025-08-03_swap_s12345.md              # Swap request S12345
2025-08-15_violation_pgy201.md         # ACGME violation for PGY2-01
2025-09-01_n1_fac_pd.md                # N-1 test: Program Director unavailable
2025-10-12_incident_inc042.md          # Production incident #042
```

---

## Retention Policy

| Category | Retention Period | Rationale |
|----------|------------------|-----------|
| **Scheduling** | 1 academic year | Historical schedules needed for pattern analysis and resident reviews |
| **Swaps** | 1 academic year | Swap history informs fairness metrics and preference learning |
| **Compliance** | **Forever** | ACGME audits may request historical compliance data (6-10 year lookback) |
| **Resilience** | 2 years | Trend analysis requires multi-year baseline |
| **Incidents** | **Forever** | Incident patterns inform long-term system improvements |

**Archive Process:**
- After retention period expires, move to `.claude/History/archive/`
- Compress old entries: `tar -czf archive_2024.tar.gz 2024-*.md`
- Never delete compliance or incident records

**Pruning Schedule:**
- Automated: First day of new academic year (July 1st)
- Manual review: Before archiving, check for ongoing investigations

---

## Querying History

### Common Search Patterns

**Find all schedule generations in July 2025:**
```bash
ls .claude/History/scheduling/2025-07-*.md
```

**Find all ACGME violations:**
```bash
grep -r "ACGME.*VIOLATED" .claude/History/compliance/
```

**Find all swaps involving a specific resident:**
```bash
grep -r "PGY2-01" .claude/History/swaps/ -l
```

**Find all solver timeouts:**
```bash
grep -r "timeout" .claude/History/scheduling/ -A 5
```

**Find all high-severity incidents:**
```bash
grep -r "Severity:.*CRITICAL" .claude/History/incidents/
```

**Find decisions made under N-1 contingency:**
```bash
grep -r "N-1.*ACTIVE" .claude/History/scheduling/
```

### Advanced Queries

**Timeline analysis (all operations on a specific date):**
```bash
find .claude/History/ -name "2025-08-15*.md" -exec echo "=== {} ===" \; -exec cat {} \;
```

**Pattern detection (recurring constraint conflicts):**
```bash
grep -r "Conflict:" .claude/History/scheduling/ | \
  cut -d: -f3 | sort | uniq -c | sort -rn | head -10
```

**MetaUpdater input (all rationale decisions for learning):**
```bash
grep -r "Rationale:" .claude/History/ -A 3
```

**Compliance audit report (all violations in date range):**
```bash
grep -r "ACGME.*VIOLATED" .claude/History/compliance/ | \
  grep "2025-07\|2025-08\|2025-09"
```

---

## Integration with MetaUpdater

The MetaUpdater agent periodically scans History entries to:

1. **Identify Recurring Patterns**
   - Same constraint conflict appearing 3+ times → Suggest constraint revision
   - Same swap type rejected repeatedly → Update auto-matcher logic
   - Same incident type recurring → Propose architectural fix

2. **Extract Decision Rationale**
   - Why was soft constraint X relaxed in generation Y?
   - Why was swap approved despite coverage impact?
   - Why was N-1 contingency activated?

3. **Measure Performance Trends**
   - Solver time increasing over time? → Investigate constraint complexity
   - Swap rejection rate increasing? → Review validation logic
   - Resilience scores declining? → Trigger preventive action

4. **Generate Improvement Proposals**
   - "Scheduling History shows 5 instances of 'clinic day conflicts'. Propose: Add hard constraint preventing clinic day overlap."
   - "Swap History shows 80% rejection rate for PGY-1 → PGY-3 swaps. Propose: Auto-filter incompatible swaps in UI."

**MetaUpdater Scan Schedule:**
- **Daily:** Incident review (new incidents flagged immediately)
- **Weekly:** Scheduling pattern analysis
- **Monthly:** Comprehensive cross-category review
- **Quarterly:** Meta-analysis for Constitution amendments

---

## Entry Guidelines

### What Belongs in History

**Include:**
- All schedule generation operations (successful or failed)
- All swap executions (approved, rejected, or rolled back)
- All ACGME compliance audits (scheduled or triggered)
- All resilience health assessments (monthly or emergency)
- All production incidents (any severity)
- All manual overrides or exceptions
- All constraint relaxations with justification

**Exclude:**
- Routine health checks (unless anomaly detected)
- Read-only queries (view operations)
- Test/development operations (use Scratchpad instead)
- Transient errors that auto-recover

### Writing Style

**Audience:** Future you, faculty administrators, ACGME auditors, and debugging engineers

**Tone:** Professional, factual, and concise

**Structure:**
- **Summary first**: One-sentence description at top
- **Context**: Why was this operation needed?
- **Decision rationale**: Why this approach vs. alternatives?
- **Outcome**: What happened? Did it succeed?
- **Impact**: Who/what was affected?
- **Follow-up**: Any actions needed?

**Example - Good Entry:**
```markdown
# Schedule Generation - Block 10 (July-August 2025)

**Summary:** Generated 2-month schedule for 12 residents with 3 leave requests and 1 TDY absence.

## Context
Annual schedule generation for Block 10 (academic year start). PGY-1 cohort includes 4 new residents requiring supervised clinic assignments.

## Rationale
- Relaxed "preferred clinic day" constraint (Soft-3) for PGY1-03 due to conflict with required orientation.
- Applied N-1 contingency: FAC-PD scheduled for TDY Aug 10-20, pre-assigned backup supervisor.

## Outcome
✅ Schedule generated in 4m 32s
✅ ACGME compliance: 0 violations
✅ Coverage: 100% (all 122 blocks assigned)
✅ Fairness: Call distribution variance 0.8σ (target: < 1σ)

## Impact
- 12 residents notified via email
- Dashboard updated
- Calendar integrations synced
```

**Example - Bad Entry:**
```markdown
# thing

ran solver. worked. done.
```

---

## Template Usage

Each subdirectory contains a `TEMPLATE.md` file:

1. **Copy template** to new file following naming convention
2. **Fill in all sections** (don't skip any)
3. **Replace placeholders** with actual data
4. **Review for completeness** before saving
5. **Commit to git** (History is version-controlled)

**Quick create script:**
```bash
# Usage: create_history_entry.sh scheduling "block10_gen001"
#!/bin/bash
category=$1  # scheduling, swaps, compliance, resilience, incidents
identifier=$2
date=$(date +%Y-%m-%d)
filename="${date}_${identifier}.md"

cp .claude/History/${category}/TEMPLATE.md \
   .claude/History/${category}/${filename}

echo "Created: .claude/History/${category}/${filename}"
echo "Edit this file to document the operation."
```

---

## Relationship to Other PAI Components

### History vs. Logs

| Aspect | History | Logs |
|--------|---------|------|
| **Audience** | Humans (future review) | Machines (debugging) |
| **Format** | Markdown (structured prose) | JSON (structured data) |
| **Retention** | Years (selective) | Days to weeks (comprehensive) |
| **Purpose** | Decision audit trail | Technical diagnostics |
| **Searchability** | grep, pattern matching | Log aggregation tools |

**Example:** Solver timeout

- **Log:** `{"timestamp": "2025-08-05T14:32:01Z", "level": "ERROR", "message": "Solver timeout after 1800s", "solver": "CPSAT", "constraints": 1247}`
- **History:** "Solver timeout during Block 11 generation. Root cause: Over-constrained problem (1247 constraints for 60 blocks). Mitigation: Relaxed Soft-2 continuity constraints, regeneration succeeded in 8m 12s."

### History vs. Scratchpad

| Aspect | History | Scratchpad |
|--------|---------|------------|
| **Permanence** | Permanent (committed to git) | Temporary (7-day auto-cleanup) |
| **Scope** | Production operations only | Development, experiments, drafts |
| **Review** | Formal review before commit | Informal, working notes |
| **Promotion** | N/A | Scratchpad → History when finalized |

**Use Scratchpad for:**
- Debugging notes during incident investigation
- Draft constraint designs before implementation
- Experimental solver configurations
- Brainstorming session notes

**Promote to History when:**
- Incident investigation complete (create postmortem)
- Experiment proves successful (document rationale)
- Decision finalized (record for future reference)

---

## Security and Privacy

**OPSEC/PERSEC Considerations:**

History entries may reference residents and faculty. Follow these rules:

1. **Use role-based identifiers:** `PGY2-01`, `FAC-PD`, not real names
2. **Sanitize before sharing:** Never share History files outside secure systems
3. **Redact sensitive details:** TDY destinations, deployment info, medical conditions
4. **Classify appropriately:** History files are **FOR OFFICIAL USE ONLY (FOUO)**

**Audit Trail Integrity:**

- History files are **append-only** (never edit after commit)
- Use git commits to track all changes
- GPG-sign commits for tamper detection (optional but recommended)
- Periodic checksums for long-term retention files

**Example git workflow:**
```bash
# Create new History entry
vim .claude/History/scheduling/2025-08-15_block11_gen002.md

# Add to git (never use git add .)
git add .claude/History/scheduling/2025-08-15_block11_gen002.md

# Commit with descriptive message
git commit -m "history: Document Block 11 schedule generation (gen002)"

# Optional: Sign commit
git commit -S -m "history: Document Block 11 schedule generation (gen002)"
```

---

## Quality Checklist

Before committing a History entry, verify:

- [ ] **Filename** follows `YYYY-MM-DD_<type>_<id>.md` convention
- [ ] **Summary** is clear and concise (one sentence)
- [ ] **Context** explains why operation was needed
- [ ] **Rationale** documents decision-making process
- [ ] **Outcome** includes metrics and validation results
- [ ] **Impact** identifies affected parties
- [ ] **OPSEC** no real names, sensitive details redacted
- [ ] **Completeness** all template sections filled
- [ ] **Accuracy** data matches actual operation results
- [ ] **Searchability** includes relevant keywords for future grep

---

## Troubleshooting

### "Too many History files, performance is slow"

**Solution:** Archive old files
```bash
cd .claude/History/scheduling
tar -czf archive_2024.tar.gz 2024-*.md
mkdir -p ../archive
mv archive_2024.tar.gz ../archive/
rm 2024-*.md  # Only after confirming archive is valid!
```

### "Can't find History entry I know exists"

**Solution:** Search across all categories
```bash
grep -r "keyword" .claude/History/ --include="*.md"
```

### "History entry has wrong information"

**Solution:** Never edit History directly. Instead, create **addendum** entry
```markdown
# Addendum: 2025-08-15_block11_gen002

**Original Entry:** 2025-08-15_block11_gen002.md

**Correction:**
Original entry stated "0 ACGME violations". Post-generation audit revealed 1 supervision ratio violation for PGY1-02 on Aug 18 PM.

**Resolution:**
- Violation corrected via swap (PGY2-01 reassigned)
- Updated supervision tracking logic to catch ratio violations pre-commit
- See: 2025-08-16_violation_pgy102.md
```

---

## Examples in Production

See these History entries for reference:

- **Scheduling:** `.claude/History/scheduling/2025-07-15_block10_gen001.md`
- **Swaps:** `.claude/History/swaps/2025-08-03_swap_s12345.md`
- **Compliance:** `.claude/History/compliance/2025-07-31_monthly_audit.md`
- **Resilience:** `.claude/History/resilience/2025-07-20_n1_analysis.md`
- **Incidents:** `.claude/History/incidents/2025-08-05_solver_timeout.md`

---

## Related Documentation

- **CONSTITUTION.md:** Foundational rules for all AI operations
- **Scratchpad/README.md:** Temporary working files system
- **docs/PERSONAL_INFRASTRUCTURE.md:** Complete PAI architecture overview
- **docs/architecture/SOLVER_ALGORITHM.md:** Scheduling engine technical details

---

**Version:** 1.0.0
**Last Updated:** 2025-12-26
**Maintained By:** SCHEDULER, RESILIENCE_ENGINEER, and ORCHESTRATOR agents
