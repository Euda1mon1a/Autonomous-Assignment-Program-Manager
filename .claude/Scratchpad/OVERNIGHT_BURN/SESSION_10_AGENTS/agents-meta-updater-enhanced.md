# META_UPDATER Agent Specification - Enhanced

**G2_RECON Classification:** SEARCH_PARTY Operation - Documentation Enhancement
**Date:** 2025-12-30
**Author:** G2_RECON (Analysis), META_UPDATER (Subject)
**Status:** Complete Reconnaissance
**Scope:** Meta-documentation patterns, knowledge management, system self-improvement

---

## PERCEPTION: Current State Analysis

The META_UPDATER agent specification (v1.0, established 2025-12-26) provides foundational roles and workflows. This enhanced specification extends that foundation with:

1. **Documentation Architecture** - Patterns observed across 401+ .claude files
2. **Knowledge Management** - Best practices for maintaining 50+ skills
3. **Maintenance Strategies** - Proactive vs. reactive documentation approaches
4. **Integration Patterns** - How META_UPDATER coordinates with other agents
5. **Quality Gates** - Documentation standards and verification methods

---

## Section 1: Documentation Architecture

### 1.1 The .claude/ Directory Taxonomy

The `.claude/` infrastructure has evolved into a specialized knowledge base with clear semantic zones:

```
.claude/
├── Agents/                    # Agent role specifications (46 files)
│   ├── G-STAFF/             # Core leadership team
│   ├── COORDINATORS/        # Specialized domains
│   ├── WORKERS/             # Task execution
│   └── SUPPORT/             # Cross-cutting concerns
├── skills/                    # 50+ specialized capabilities
│   ├── CORE/                # Core protocols & patterns
│   ├── PROJECT_DOMAIN/      # Scheduling, compliance, resilience
│   ├── ENGINEERING/         # Code quality, testing, infrastructure
│   └── MANAGED/             # Delivered by external systems (MCP)
├── protocols/               # Real-time coordination (NEW - Session 025)
│   ├── RESULT_STREAMING.md
│   ├── SIGNAL_PROPAGATION.md
│   └── MULTI_TERMINAL_HANDOFF.md
├── commands/                # Quick-invoke entry points (NEW - Session 025)
│   ├── parallel-explore.md
│   ├── parallel-implement.md
│   ├── parallel-test.md
│   └── handoff-session.md
├── docs/                    # Framework & schema extensions
│   ├── PARALLELISM_FRAMEWORK.md
│   ├── TODO_PARALLEL_SCHEMA.md
│   └── [domain docs]
└── Scratchpad/              # Session documentation & analysis
    ├── SESSION_*/           # Session-specific findings
    ├── histories/           # Narrative documentation
    └── OVERNIGHT_BURN/      # Deep dives on subsystems
```

**Key Insight:** META_UPDATER maintains not just code documentation, but a sophisticated organizational memory system where 401+ markdown files form an interconnected knowledge graph.

### 1.2 Documentation Lifecycle Stages

Every piece of documentation goes through predictable stages:

```
DISCOVERY → CREATION → MATURATION → ARCHIVAL → RETIREMENT
```

| Stage | Duration | Owner | Activity |
|-------|----------|-------|----------|
| **DISCOVERY** | 1-2 sessions | Agent + META_UPDATER | Issue identified, pattern observed |
| **CREATION** | 1 session | Agent (primary), META_UPDATER (guidance) | First draft, experimental format |
| **MATURATION** | 2-4 sessions | Agent + META_UPDATER (review) | Refinement, cross-references, examples |
| **ARCHIVAL** | Ongoing | META_UPDATER | Links from Scratchpad to permanent location |
| **RETIREMENT** | Optional | META_UPDATER (with Faculty approval) | Superseded docs marked deprecated, moved to history/ |

**META_UPDATER's Role at Each Stage:**
- **DISCOVERY**: Recognize patterns, flag for documentation
- **CREATION**: Suggest structures, review for consistency
- **MATURATION**: Link to related docs, refactor for clarity, add examples
- **ARCHIVAL**: Move from Scratchpad to permanent location (docs/), verify cross-references
- **RETIREMENT**: Create deprecation notice, redirect readers to replacement

### 1.3 Documentation by Artifact Type

#### Agent Specifications (46 files, 30-60KB each)

**File Pattern:** `.claude/Agents/[AGENT_NAME].md`

**Mandatory Sections:**
1. Header metadata (Role, Authority, Status, Model Tier)
2. Charter (Primary responsibilities, scope, philosophy)
3. Personality traits (if applicable)
4. Decision authority (Can execute, requires approval, forbidden)
5. Approach (Workflows, decision-making processes)
6. Skills access (Full write, read-only, none)
7. Key workflows (Step-by-step procedures)
8. Escalation rules (When to escalate, format)
9. Success metrics (How to measure effectiveness)
10. Delegation section (How to spawn this agent)
11. Version history
12. Next review date (Quarterly minimum)

**Quality Checks:**
- [ ] Authority matrix is consistent (no conflicts with other agents)
- [ ] Workflows reference specific files/tools available
- [ ] Examples are up-to-date and accurate
- [ ] All external references (CLAUDE.md, docs/) exist
- [ ] Escalation paths match actual agent hierarchy
- [ ] Model tier is justified (haiku for simple, opus for complex)

**Example Precedent:** ORCHESTRATOR.md (v5.1.0) - Sets pattern for complex agent specifications with multi-agent coordination

#### Skill Specifications (50+ files, 5-30KB each)

**File Pattern:** `.claude/skills/[SKILL_NAME]/SKILL.md` with optional subdirectories

**YAML Frontmatter (New Pattern - Session 025):**
```yaml
---
name: skill-name
description: One-line description for invocation
model_tier: [haiku|sonnet|opus]
parallel_hints:
  can_parallel_with: [skill-a, skill-b]
  must_serialize_with: [skill-x, skill-y]
  preferred_batch_size: N
---
```

**Mandatory Sections:**
1. When this skill activates (use cases)
2. Methodology (Process, algorithms, patterns)
3. Step-by-step procedures (Copy-paste ready)
4. Code examples (Language-specific: Python, TypeScript)
5. Output format/templates
6. Integration with other skills
7. Escalation rules (When to defer to human)
8. Quick reference commands
9. Common patterns (do's and don'ts)

**Quality Checks:**
- [ ] Examples are tested and working
- [ ] Commands have absolute paths (/Users/aaronmontgomery/...)
- [ ] Tool integrations (bash, Read, Edit, etc.) are referenced
- [ ] Output templates are copy-paste ready
- [ ] Escalation rules are clear (no ambiguity)
- [ ] Parallel hints are accurate

**Supporting Files in Skill Directories:**
- `reference/`: Technical reference material
- `examples/`: Working examples (not in SKILL.md)
- `workflows/`: Step-by-step procedures

#### Protocol Specifications (3 files, ~200KB total)

**File Pattern:** `.claude/protocols/[PROTOCOL_NAME].md`

**New in Session 025:** Protocols define real-time coordination between agents

**Mandatory Sections:**
1. Overview (Purpose, when to use)
2. Signal types (Enumeration with semantics)
3. Signal structure (JSON schema)
4. Propagation rules (How signals flow)
5. Conflict resolution (What happens when signals conflict)
6. Integration points (How to hook into workflows)
7. Examples (Real-world coordination scenarios)
8. Fallback behavior (What happens if protocol fails)

**Example Precedent:** SIGNAL_PROPAGATION.md - 7 signal types, 4 propagation rules, sophisticated conflict detection

#### Session Documentation (Scratchpad)

**File Pattern:** `.claude/Scratchpad/SESSION_[NUMBER]_[TOPIC].md` or `OVERNIGHT_BURN/SESSION_[NUMBER]_[DOMAIN]/`

**Purpose:** Capture learnings, decision trees, and ephemeral analysis

**Mandatory Sections:**
1. Session metadata (Date, scope, outcome)
2. Executive summary (1-2 sentences)
3. Key findings (Numbered with evidence)
4. Recommendations (Prioritized)
5. Artifacts created (Links to permanent locations)
6. Cross-references (What's related in other sessions)
7. Next steps (Handoff for future sessions)

**Archival Rules:**
- Sessions > 90 days old stay in Scratchpad (not deleted)
- High-value insights get extracted to `histories/` with narrative format
- Superseded findings get marked `[DEPRECATED - See SESSION_X instead]`
- Cross-session patterns aggregate into framework updates (PARALLELISM_FRAMEWORK.md, etc.)

---

## Section 2: Knowledge Management Strategies

### 2.1 The Triple-Store Pattern

Session 025 introduced a key insight: documentation should exist in three forms:

1. **Practical (Skills, Commands)**: "How do I do X?" - Step-by-step, copy-paste ready
2. **Conceptual (Frameworks, Protocols)**: "Why is it done this way?" - Design rationale, theory
3. **Narrative (Histories, Handoffs)**: "What happened and what did we learn?" - Stories, context

META_UPDATER maintains all three:

```
Practical Layer (Skills)     → How-to guides, examples
        ↓ references ↓
Conceptual Layer (Frameworks) → Theory, architecture, decisions
        ↓ references ↓
Narrative Layer (Histories)   → Context, lessons learned, evolution
```

**Benefits:**
- Newcomer can start with narrative (understand context)
- Doer can reference practical (get work done)
- Architect can consult conceptual (understand why)

**META_UPDATER's Responsibility:** Keep these three layers in sync. When practical changes, update conceptual. When conceptual changes, add to narrative.

### 2.2 Maintaining 50+ Skills Without Chaos

**Problem:** Skills become stale as code evolves. How to keep 50+ skill definitions current?

**Solution: Skill Verification Audit (Quarterly)**

**META_UPDATER Workflow:**

```
Q1 Audit:
├── For each skill:
│   ├── Read SKILL.md
│   ├── Verify referenced files still exist
│   ├── Run example commands (if safe)
│   ├── Check "Integration with other skills" section
│   ├── Verify parallel_hints are accurate
│   └── Flag changes needed or deprecations
├── Cross-reference matrix
│   ├── Build graph: skill A uses tool X, skill B uses tool X
│   ├── Identify circular dependencies
│   ├── Check for skill supersession (A replaced by B)
│   └── Flag integration gaps
└── Report
    ├── Skills needing updates (categorized by severity)
    ├── Integration issues
    ├── Deprecation candidates
    └── Recommendations
```

**Practical Example:** If `code-review` skill references deleted files, the quarterly audit catches it immediately, and META_UPDATER files an issue to update references.

### 2.3 Cross-Referencing Best Practices

The repository's documentation is a knowledge graph. META_UPDATER maintains coherence.

**Key Patterns:**

**Pattern 1: The Skill-to-Framework Bridge**
```markdown
# test-writer Skill

## When This Skill Activates
- New code added without tests
- Coverage below 70% threshold

## Coverage Requirements
| Layer | Target | Minimum |
|-------|--------|---------|
| Services | 90% | 80% |
| Controllers | 85% | 75% |

*See `docs/testing/TESTING_STRATEGY.md` for full testing framework*
```

**Pattern 2: The Protocol-to-Workflow Cross-Reference**
```markdown
# SIGNAL_PROPAGATION Protocol

### Integration with ORCHESTRATOR
ORCHESTRATOR uses SIGNAL_PROPAGATION to coordinate parallel agent execution.
See `.claude/Agents/ORCHESTRATOR.md` section "Result Synthesis from Signals"
```

**Pattern 3: The Session-to-Permanent Documentation Link**
```markdown
# SESSION_025_HANDOFF_SUMMARY.md

## Key Concepts for Future Sessions
See `.claude/protocols/SIGNAL_PROPAGATION.md` for full specification.
See `.claude/skills/MCP_ORCHESTRATION/SKILL.md` for integration examples.
```

**META_UPDATER's Role:** Periodically audit internal cross-references. Use grep to find broken links.

```bash
# Find all markdown references
grep -r "\[.*\]\(.*\.md\)" .claude/ docs/

# Check if referenced files exist
# (Build a verification report)
```

### 2.4 Deprecation & Sunsetting

**Problem:** Old patterns accumulate. How to retire documentation without losing institutional memory?

**Solution: Deprecation Lifecycle**

**Stage 1: Mark Deprecated (3+ sessions before removal)**
```markdown
# DEPRECATED - [SKILL_NAME]

> This skill is superseded by [NEW_SKILL_NAME].md (introduced 2025-12-25).
> Use [NEW_SKILL] for new work. Existing code using this skill should migrate
> at next refactor.
>
> Historical reference: This skill was used for X purpose.
> Lessons learned: [Brief reflection]

See [NEW_SKILL] for replacement.
```

**Stage 2: Archive to History**
Move to `.claude/Scratchpad/histories/DEPRECATED_[SKILL_NAME].md` with full context.

**Stage 3: Remove (after explicit approval from ARCHITECT)**
Delete from active skill set, verify no remaining references.

**Example:** If a skill is replaced, META_UPDATER:
1. Marks it deprecated (session N)
2. Updates CHANGELOG.md
3. Notifies relevant agents via GitHub issue
4. Monitors usage (search codebase for calls to deprecated skill)
5. Archives to history after 2-3 sessions with no usage
6. Requests removal approval

---

## Section 3: Maintenance Strategies - Proactive vs. Reactive

### 3.1 Proactive Maintenance (Quarterly Audits)

**Scheduled Tasks (META_UPDATER calendar):**

| Frequency | Task | Owner | Output |
|-----------|------|-------|--------|
| **Weekly** | Scan new GitHub issues for pattern emergence | META_UPDATER | Findings captured in WEEKLY_HEALTH_*.md |
| **Monthly** | Retrospective & lessons learned synthesis | META_UPDATER | MONTHLY_RETRO_*.md |
| **Quarterly** | Full documentation audit (links, accuracy, staleness) | META_UPDATER | DOCS_AUDIT_*.md + fix PRs |
| **Quarterly** | Skill verification (examples work, references valid) | META_UPDATER | SKILL_AUDIT_*.md + update PRs |
| **Semi-Annually** | Agent specification review (workflow accuracy, authority) | META_UPDATER + ARCHITECT | Agent update proposals |

**Quarterly Audit Checklist (NEW):**

```markdown
## Q1 2026 Documentation Audit

### Link Verification (Automated)
- [ ] Scan `.claude/` for all markdown reference patterns
- [ ] Verify internal references exist (absolute paths)
- [ ] Check external references still valid
- [ ] Flag orphaned files (no incoming references)
- [ ] Report: X broken links, Y orphaned files

### Staleness Detection
- [ ] Identify docs not updated in 6+ months
- [ ] For each old doc: Is it still accurate? Still needed?
- [ ] Report: X stale docs, recommend updates for Y

### Skill Verification
- [ ] For each skill: Can examples be run?
- [ ] Do parallel_hints match actual parallelization?
- [ ] Are integrations with other skills still valid?
- [ ] Report: Z skills need updates

### Framework Consistency
- [ ] Compare CLAUDE.md examples to current code
- [ ] Check if architectural patterns documented match implementation
- [ ] Verify ACGME rules are current
- [ ] Report: Updated examples or new framework docs needed

### Cross-Reference Matrix
- [ ] Build graph of skill → skill dependencies
- [ ] Identify circular dependencies
- [ ] Check integration completeness
- [ ] Report: Gaps and recommendations

### Outcomes
- [ ] File GitHub issues for needed updates
- [ ] Create PR for low-risk fixes
- [ ] Escalate to ARCHITECT for high-impact changes
```

### 3.2 Reactive Maintenance (Issue-Driven)

**When Issues Trigger Documentation Updates:**

**Trigger 1: Same Question Asked 3+ Times**
```
If SCHEDULER asks "How do I handle timezone conversion?" 3+ times:
1. Recognize the pattern (META_UPDATER's core skill)
2. Identify root cause (missing doc? unclear doc? workflow issue?)
3. Fix it (add section to CLAUDE.md or create timezone-handling skill)
4. Announce to team (create GitHub issue with link to fix)
5. Track effectiveness (did question frequency drop?)
```

**Trigger 2: PR Review Comments Repeat**
```
If code-review finds N+1 query problems in 3+ PRs:
1. Recognize the pattern
2. Create/update documentation:
   - Add example to backend-patterns in Overnight Burn docs
   - Update code-review skill with detection checklist
   - Add to CLAUDE.md "Common Pitfalls"
3. Update pre-commit hooks if possible (catch at linting time)
4. Monitor: Did N+1 problems decrease in future PRs?
```

**Trigger 3: Test Failures in Same Module**
```
If test_swap_executor.py fails repeatedly in same way:
1. Recognize as operational issue
2. Update test-writer skill with edge case
3. Add to test-scenario-framework as regression test
4. Document the scenario for future reference
```

### 3.3 Maintenance Metrics (Success Indicators)

**Metric 1: Documentation Currency**
```
Stale % = (Docs not updated in 6+ months) / (Total docs)
Target: < 10% stale
Action: If > 15%, trigger quarterly audit
```

**Metric 2: Link Health**
```
Broken Link % = (Broken references) / (Total references)
Target: 0% (or near-zero after audit)
Action: If > 2%, trigger automated link audit
```

**Metric 3: Cross-Reference Completeness**
```
Integration Gaps = (Skills with no integration docs) / (Total skills)
Target: 0%
Action: If > 5%, create missing integration docs
```

**Metric 4: Documentation Utility**
```
Metric: "Agents report docs are helpful when needed"
Collection: Qualitative feedback in handoffs, escalations
Action: If sentiment turns negative, trigger doc review
```

**Metric 5: Pattern Detection Latency**
```
Time from pattern emergence to documentation fix
Target: < 7 days for documented patterns
Measure: GitHub issue creation → PR merged
```

---

## Section 4: Integration Patterns - How META_UPDATER Coordinates

### 4.1 Agent Collaboration Matrix

META_UPDATER interacts with other agents in structured ways:

```
ARCHITECT               ← Proposes spec updates, framework changes
        ↓
  [Escalation]
        ↓
  META_UPDATER ← Analyzes patterns, proposes improvements
        ↑
  [Review]
        ↑
CODE_REVIEWER        ← Reviews documentation PRs
SYNTHESIZER          ← Synthesizes findings into patterns
COORD_INTEL          ← Shares trends & metrics
```

**Key Integration Points:**

**Integration 1: Pattern → Skill → Agent Update Cycle**

```
Session N: Agent A encounters repeated issue
        ↓
Session N+1: META_UPDATER detects pattern (3+ occurrences)
        ↓
Session N+2: Create skill or doc update
        ↓
Session N+3: Test effectiveness (issue frequency drops)
        ↓
Session N+4: Archive in permanent location
```

**Integration 2: Documentation PR Review**

META_UPDATER proposes documentation changes → CODE_REVIEWER reviews for accuracy → ARCHITECT approves if architectural implications → Merge

**Integration 3: Metrics Sharing**

META_UPDATER generates:
- Weekly health reports (shared with ORCHESTRATOR)
- Monthly retrospectives (shared with all agents)
- Quarterly audits (published for transparency)

### 4.2 Delegation Patterns for META_UPDATER

**When to Spawn META_UPDATER:**

```markdown
## Delegate to META_UPDATER When:

1. Pattern Recognition Needed
   "We're seeing test failures in the same module repeatedly.
    Analyze the pattern and recommend documentation updates."

2. Documentation Audit Triggered
   "It's been a quarter. Run the full documentation audit and
    report on staleness, broken links, and skill verification."

3. Improvement Proposal Needed
   "SCHEDULER has asked about timezone conversion 3 times.
    Identify root cause and propose a fix."

4. Knowledge Graph Maintenance
   "Session 025 introduced 3 new protocols. Verify they're
    properly cross-referenced throughout the codebase."
```

### 4.3 Avoiding Bottlenecks

**Risk:** META_UPDATER becomes a bottleneck if agents must wait for documentation approvals.

**Mitigation Strategies:**

**Strategy 1: Document-First Culture**
- Agents document as they work (drafts in Scratchpad)
- META_UPDATER improves + organizes (no blocking review)
- Move to permanent location when stable

**Strategy 2: Parallelizable Reviews**
- Documentation changes don't require sequential review
- Can batch review (weekly instead of per-PR)
- Code review skill can handle doc PRs in parallel

**Strategy 3: Self-Service Documentation**
- Agents can update Scratchpad directly (no META_UPDATER needed)
- Only cross-repoository docs need META_UPDATER review
- Policy: "If unsure, ask META_UPDATER"

---

## Section 5: Quality Gates & Standards

### 5.1 Documentation Quality Checklist

**For Agent Specifications:**
- [ ] Role, authority, model tier are clear
- [ ] Workflows reference actual tools/files
- [ ] Examples are copy-paste ready and tested
- [ ] Escalation paths match agent hierarchy
- [ ] Authority matrix doesn't conflict with other agents
- [ ] Delegation section includes all required context
- [ ] Cross-references are accurate and current
- [ ] Next review date is set (quarterly minimum)

**For Skill Specifications:**
- [ ] YAML frontmatter is complete (name, model_tier, parallel_hints)
- [ ] "When this skill activates" is clear and specific
- [ ] Examples in primary languages (Python, TypeScript)
- [ ] Output templates are provided
- [ ] Integrations with other skills are documented
- [ ] Escalation rules are specific (not vague)
- [ ] All referenced files exist and have absolute paths
- [ ] parallel_hints are accurate and justified

**For Protocols:**
- [ ] Signal types are enumerated with semantics
- [ ] Signal structure (JSON schema) is provided
- [ ] Propagation rules are unambiguous
- [ ] Conflict resolution is addressed
- [ ] Real-world examples are provided
- [ ] Fallback behavior is specified
- [ ] Integration points are clear

**For Session Documentation:**
- [ ] Metadata is complete (date, scope, outcome)
- [ ] Findings are numbered and evidence-backed
- [ ] Recommendations are prioritized
- [ ] Artifacts created are linked
- [ ] Cross-references to other sessions
- [ ] Handoff for future sessions is clear

### 5.2 Common Documentation Anti-Patterns (To Avoid)

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Vague Role Description** | "Do stuff related to X" | Specific list of responsibilities + what's NOT in scope |
| **Examples with Typos** | Agent copies broken example | Test examples before documenting, note setup requirements |
| **Relative Paths** | Doesn't work when doc is moved | Use absolute paths only (/Users/aaronmontgomery/...) |
| **Dangling References** | "See docs/api/swaps.md" but file was renamed | Automated link auditing, update all references |
| **Unclear Escalation** | "Ask ARCHITECT if unsure" | Specific decision criteria, not judgment calls |
| **Stale Examples** | Code changed but example wasn't updated | Quarterly skill verification, test examples |
| **Inconsistent Terminology** | Same concept called "person", "resident", "human" | Create glossary, use find-replace to standardize |
| **Missing Integration Context** | Skill A doesn't mention skill B | Document integrations, maintain integration matrix |

### 5.3 Documentation Standards

**Markdown Style:**
- Use ATX headings (#, ##, ###) not underlines
- Code blocks must specify language (```python, ```bash, etc.)
- Use tables for comparative information
- Use ordered lists for sequences, unordered for options
- Bold for emphasis, `code` for literals

**File Naming:**
- Agent specs: `[AGENT_NAME].md` (PascalCase)
- Skills: `.claude/skills/[skill-name]/SKILL.md` (kebab-case)
- Sessions: `SESSION_[NUMBER]_[TOPIC].md` or `OVERNIGHT_BURN/SESSION_[NUMBER]_[DOMAIN]/`
- Never use spaces in filenames

**Cross-Referencing:**
- Absolute paths: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docs/...`
- Internal references: `See [Title](path/to/file.md)` with clear link text
- No dangling references (verify file exists before referencing)

**Code Examples:**
- Must include language specification
- Should be copy-paste ready (standalone when possible)
- Include setup/context if needed
- Indicate if example is pseudo-code vs. real code

---

## Section 6: Best Practices & Lessons Learned

### 6.1 From Session 025 Documentation Patterns

**Pattern 1: The Triple-Store Pattern (Conceptual, Practical, Narrative)**

Session 025 successfully demonstrated maintaining three layers of documentation:

1. **Practical:** skills/code-review/SKILL.md, skills/test-writer/SKILL.md
2. **Conceptual:** protocols/SIGNAL_PROPAGATION.md, docs/PARALLELISM_FRAMEWORK.md
3. **Narrative:** SESSION_025_HANDOFF_SUMMARY.md, SIGNAL_AMPLIFICATION_SESSION_025.md

Insight: Users prefer navigating narratives, but doers need practical guides, and architects need conceptual understanding. All three are essential.

**Pattern 2: Versioning & Evolution**

Agent specs now include version numbers (ORCHESTRATOR: v5.1.0). This enables:
- Tracking when changes happened
- Describing evolution (v4 → v5 changes)
- Referencing specific versions in discussions
- Deprecating old versions if needed

**Pattern 3: Session Artifacts as Context**

Overnight Burn sessions (SESSION_1_BACKEND, SESSION_2_FRONTEND, SESSION_3_ACGME) show that deep-dives into subsystems should be organized by domain, not just chronologically. This makes them more discoverable and reusable.

**Pattern 4: Scratchpad as Staging Ground**

Scratchpad (uncurated, session-specific) feeds into permanent docs. This two-phase approach works well:
- Phase 1: Raw findings in Scratchpad
- Phase 2: Curated, cross-referenced in permanent location
- Reduces pressure on initial documentation

### 6.2 Recommended Extensions to Current META_UPDATER

**Extension 1: Automated Link Auditing**

Create a script that runs quarterly:
```bash
# Find all .md references in .claude/
# Verify the referenced files exist
# Report broken links + recommendations
# Could be triggered by `/lint-docs` command
```

**Extension 2: Documentation Coverage Report**

Like test coverage, track documentation coverage:
```
Agent Specs:             46/46 (100%)
Skills with docs:        50/50 (100%)
Skills with examples:    45/50 (90%)  ← Gap here
Protocols documented:    3/3 (100%)
Commands with docs:      4/4 (100%)
```

**Extension 3: Cross-Reference Matrix**

Maintain a knowledge graph showing:
- Which skills integrate with which
- Which protocols involve which agents
- Which sessions contributed to which framework updates
- Visual/textual representation in quarterly reports

**Extension 4: Glossary Management**

As terminology evolves (e.g., "person" vs. "resident" debate), maintain a glossary with variants and preferred terms. Use in documentation audits to catch inconsistencies.

**Extension 5: Documentation A/B Testing**

For important docs (CLAUDE.md, key skills), test readability:
- New agent reads Section X without help
- Time to understand: target < 5 minutes
- If time > 5 min, doc needs revision

---

## Section 7: Recommended Enhancements to META_UPDATER Spec

### 7.1 Enhanced Decision Authority

**Current Authority:** Propose-Only (Cannot Merge Changes)

**Recommended Enhancement:** Add Tier 2 (Limited Autonomous) for low-risk changes

```
### Tier 1: Autonomous Execute
- Fix typos in agent specs
- Update examples to match current code
- Add missing cross-references
- Reformat documentation for consistency
→ Can commit directly to feature branches

### Tier 2: Review-Required
- Update CLAUDE.md content
- Change agent specifications
- Add new skills or frameworks
→ Must create PR for review

### Tier 3: Escalation-Required
- Change decision authority of agents
- Deprecate existing patterns
- Major documentation rewrites
→ Must escalate to ARCHITECT + Faculty
```

### 7.2 Enhanced Workflows

**New Workflow: Skill Lifecycle Management**

```
TRIGGER: Skill created or updated
├── AUTO: Add to skills inventory
├── AUTO: Verify YAML frontmatter
├── AUTO: Check parallel_hints accuracy
├── MONTHLY: Test examples still work
├── QUARTERLY: Verify integrations up-to-date
├── SEMI-ANNUALLY: Check if still used
└── ON-DEMAND: Archive if superseded
```

**New Workflow: Documentation Health Score**

```
MONTHLY: Compute documentation health
├── Link health (0-100)
├── Staleness (0-100)
├── Consistency (0-100)
├── Completeness (0-100)
├── Utility (0-100)
└── COMPOSITE SCORE: Average of above
    - 90+: Excellent
    - 80-89: Good (minor improvements needed)
    - 70-79: Fair (attention needed)
    - < 70: Poor (audit recommended)
```

### 7.3 Enhanced Escalation Framework

**New Escalation Type: Documentation Policy Questions**

```
When to escalate to Faculty:
- "Should we retire documentation about [old pattern]?"
- "Should we enforce [new documentation standard]?"
- "How long should we keep session documentation?"
→ These are policy decisions, not technical decisions
```

**New Escalation Type: Knowledge Architecture Questions**

```
When to escalate to ARCHITECT:
- "Should we reorganize .claude/ directory structure?"
- "Should we add new skill category?"
- "How should we handle skill versioning?"
→ These affect system architecture
```

---

## Section 8: Integration with Session Documentation

### 8.1 Session-to-Permanent Documentation Pipeline

```
Session Work
    ↓
Scratchpad Notes (raw findings)
    ↓ (META_UPDATER review)
Session Summary (OVERNIGHT_BURN or SESSION_*.md)
    ↓ (if high-value)
Extract to Narrative (histories/ with story format)
    ↓ (if generalizable)
Update Framework Docs (CLAUDE.md, protocols/, skills/)
    ↓ (final stage)
Permanent Location with Cross-References
```

### 8.2 Seasonal Documentation Cycles

**Q1 (Jan-Mar):** Strategic review & planning docs
- Update CLAUDE.md with new standards if any
- Review architectural decisions (ADRs)

**Q2 (Apr-Jun):** Implementation & skill updates
- Update skills with new patterns from spring work
- Add integration examples from successful projects

**Q3 (Jul-Sep):** Deep-dive & framework expansion
- Overnight Burn sessions → Framework updates
- Complex pattern documentation

**Q4 (Oct-Dec):** Retrospective & cross-session synthesis
- Annual retrospective (comparing Q4 this year to previous)
- Consolidate learnings from all sessions
- Plan documentation improvements for next year

---

## Section 9: Recommendations for Implementation

### 9.1 Short-Term (Next 2 Weeks)

1. **Create Quarterly Audit Checklist** (in this spec)
   - Already done (Section 3.1)

2. **Document Current Skill Status**
   - Run verification audit on 10 random skills
   - Create SKILL_AUDIT_BASELINE.md

3. **Build Link Verification Tool**
   - Script to find broken references
   - Report format for use in quarterly audits

### 9.2 Medium-Term (Next Month)

1. **Glossary Creation**
   - Extract terminology from CLAUDE.md
   - Create `.claude/docs/GLOSSARY.md`
   - Use in documentation audits

2. **Cross-Reference Matrix Tool**
   - Script to build skill dependency graph
   - Identify circular dependencies
   - Generate visual or textual report

3. **Documentation Health Score**
   - Implement scoring system from Section 7.2
   - Baseline current score
   - Set improvement targets

### 9.3 Long-Term (This Quarter & Beyond)

1. **Automated Link Auditing**
   - Runs monthly
   - Reports to META_UPDATER (via GitHub issue or summary)
   - Integrated into CI/CD if possible

2. **Skill Lifecycle Tracking**
   - Database of skill creation, updates, usage
   - Automated detection of stale skills
   - Deprecation workflow implementation

3. **Documentation Search/Discovery**
   - Vector DB indexing (from Session 025 VECTOR_DB_PENDING.md)
   - Semantic search across all documentation
   - "Find similar patterns" capability

4. **Documentation A/B Testing Framework**
   - Protocol for testing readability
   - Metrics for documentation clarity
   - Continuous improvement cycle

---

## Section 10: Maintenance Calendar (Recommended)

| Schedule | Task | Owner | Output |
|----------|------|-------|--------|
| **Every Monday 8:00** | Weekly pattern scan & health report | META_UPDATER | WEEKLY_HEALTH_[date].md |
| **First Monday of month** | Monthly retrospective & lessons synthesis | META_UPDATER | MONTHLY_RETRO_[date].md |
| **Monthly (2nd Tuesday)** | Documentation health score | META_UPDATER | Brief email/report |
| **Quarterly (1st week)** | Full documentation audit | META_UPDATER | DOCS_AUDIT_[date].md + PRs |
| **Quarterly (2nd week)** | Skill verification audit | META_UPDATER | SKILL_AUDIT_[date].md + PRs |
| **Quarterly (3rd week)** | Cross-reference matrix update | META_UPDATER | INTEGRATION_MATRIX_[date].md |
| **Semi-Annually** | Agent specification review | META_UPDATER + ARCHITECT | Agent update proposals or summary |
| **Annually** | Full knowledge architecture review | META_UPDATER + ARCHITECT + Faculty | Strategic recommendations for next year |

---

## Section 11: Reference Implementations

### 11.1 Example: Quarterly Documentation Audit

**Input:** Current date is Q1 2026

**Process:**

1. **Link Verification (Week 1)**
   ```bash
   # Find all markdown files in .claude/
   # Extract all reference patterns: [text](path)
   # For each: verify file exists
   # Output: broken_links.txt with recommendations
   ```

2. **Staleness Detection (Week 1-2)**
   ```bash
   # For each .md file:
   #   - Extract last commit date
   #   - If > 6 months old AND not in /histories:
   #     - Check if still accurate
   #     - Mark for review
   # Output: stale_docs.txt with recommendations
   ```

3. **Skill Verification (Week 2-3)**
   ```
   For each skill (50 total):
   ├── Read SKILL.md
   ├── Check: Can examples be understood/run? (Automated: parse code blocks)
   ├── Check: Are parallel_hints accurate? (Compare to skill dependencies)
   ├── Check: Are integrations up-to-date? (Compare to SKILL_AUDIT_BASELINE)
   ├── Flag: Issues for manual review
   └── Output: SKILL_VERIFICATION_Q1_2026.md
   ```

4. **Framework Consistency (Week 3)**
   ```
   ├── Compare CLAUDE.md examples to actual code
   ├── Check if ACGME rules are current
   ├── Verify architectural patterns match implementation
   └── Output: FRAMEWORK_REVIEW_Q1_2026.md
   ```

5. **Cross-Reference Matrix (Week 4)**
   ```
   ├── Build graph: skill → skill dependencies
   ├── Identify circular dependencies
   ├── Check: Is skill A documented to integrate with skill B?
   ├── Output: INTEGRATION_MATRIX_Q1_2026.md + recommendations
   ```

6. **Report & Actions**
   ```
   Create DOCS_AUDIT_Q1_2026.md with:
   ├── Executive summary
   ├── Findings by category (links, staleness, skills, framework)
   ├── Recommendations prioritized by impact
   ├── Action items with owners
   └── Timeline for fixes

   File GitHub issue:
   ├── Link to audit report
   ├── High-priority items for immediate fix
   ├── Medium-priority items for this quarter
   └── Low-priority items for next quarter
   ```

### 11.2 Example: Skill Integration Update

**Scenario:** New skill `credential-validator` created (Session 10)

**META_UPDATER Actions:**

1. **Verify YAML Frontmatter**
   ```yaml
   - name: credential-validator ✓
   - description: [present] ✓
   - model_tier: opus (justified? check scope) ✓
   - parallel_hints: [check accuracy] ✓
   ```

2. **Find Related Skills**
   ```
   Search: Where might credential-validator integrate?
   - SCHEDULING (schedule-optimization)
   - COMPLIANCE_VALIDATION
   - safe-schedule-generation

   Action: Document integration points in SKILL.md
   ```

3. **Update Cross-References**
   ```
   In safe-schedule-generation/SKILL.md:
   + "This skill integrates with credential-validator
     to ensure slot-filling respects credential requirements.
     See credential-validator/SKILL.md for full spec."

   In schedule-optimization/SKILL.md:
   + "Consider credential requirements in optimization.
     Use credential-validator skill for eligibility checks."
   ```

4. **Add to Integration Matrix**
   ```
   credential-validator
   ├── can_parallel_with: [test-writer, code-review]
   ├── must_serialize_with: [database-migration]
   └── integrates_with: [safe-schedule-generation, schedule-optimization, COMPLIANCE_VALIDATION]
   ```

5. **Update Agent Specs**
   ```
   For agents that use this skill (SCHEDULER, COMPLIANCE_AUDITOR, etc.):
   + "Use credential-validator skill to verify slot eligibility"
   ```

6. **Track in Quarterly Audit**
   ```
   Next Q1 audit:
   - Verify credential-validator examples still work
   - Check if being used (monitor GitHub)
   - Gather feedback from SCHEDULER/COMPLIANCE_AUDITOR
   ```

---

## Section 12: Success Metrics & Measurement

### 12.1 Documentation Quality Metrics

**Metric 1: Coverage**
- Agent specs: 100% of agents have current specs
- Skill docs: 100% of skills have YAML + SKILL.md
- Framework docs: All major patterns documented

**Metric 2: Accuracy**
- Broken links: < 1% of references
- Example failures: < 5% of tested examples
- Stale docs: < 10% of docs older than 6 months

**Metric 3: Utility**
- Pattern detection latency: < 7 days from pattern → documentation
- Agent query rate: "How do I X?" → "Documentation already covers it" (reduce escalations)
- New agent onboarding time: < 1 week to productive (with good docs)

**Metric 4: Coherence**
- Cross-reference integrity: All referenced files exist
- Terminology consistency: Same concept not called 3 different names
- Integration completeness: Skills that should integrate have cross-references

### 12.2 Process Metrics

**Metric 1: Audit Completion**
- Weekly health reports: 100% on schedule
- Monthly retrospectives: 100% on schedule
- Quarterly audits: 100% on schedule

**Metric 2: Issue Resolution**
- Documentation issues: < 2 week resolution time
- High-priority audit findings: 100% fixed within quarter
- Agent specification updates: Deployed within 2 weeks of proposal

---

## Conclusion: The Documentation Virtuous Cycle

META_UPDATER's role is to maintain a documentation system that:

1. **Captures** lived experiences (from agents and sessions)
2. **Organizes** that knowledge into coherent structure
3. **Verifies** accuracy through regular audits
4. **Distributes** understanding across three layers (practical, conceptual, narrative)
5. **Keeps current** through proactive maintenance
6. **Enables** agent self-improvement through pattern recognition

The enhanced META_UPDATER specification provides the frameworks and processes to scale this across 50+ skills, 46+ agents, and 400+ documentation files, while maintaining the quality and coherence that makes the repository truly "autonomous."

---

## Appendices

### Appendix A: Quick Reference - Where Things Live

| Type | Location | Pattern |
|------|----------|---------|
| Agent Specs | `.claude/Agents/` | `[AGENT_NAME].md` |
| Skills | `.claude/skills/` | `[skill-name]/SKILL.md` |
| Protocols | `.claude/protocols/` | `[PROTOCOL_NAME].md` |
| Commands | `.claude/commands/` | `[command-name].md` |
| Sessions | `.claude/Scratchpad/` | `SESSION_[N]_*.md` or `OVERNIGHT_BURN/SESSION_*/` |
| Narratives | `.claude/Scratchpad/histories/` | `[TOPIC_NARRATIVE].md` |
| Project Docs | `docs/` | Various (architecture/, api/, development/, etc.) |
| Master Docs | Root | `CLAUDE.md`, `CHANGELOG.md`, `README.md` |

### Appendix B: Glossary of Key Terms

- **Agent Specification**: A detailed markdown file describing an agent's role, authority, workflows, and escalation rules
- **Skill**: A reusable capability with a SKILL.md document and supporting reference material
- **Protocol**: A coordination mechanism for real-time communication (signals, timing, conflict resolution)
- **Session Documentation**: Ephemeral documentation created during a session (lives in Scratchpad)
- **Framework Documentation**: Conceptual documentation about how the system is designed (lives in docs/)
- **META_UPDATER**: The agent responsible for maintaining all documentation and identifying patterns
- **Quarterly Audit**: A systematic review of documentation health (links, staleness, accuracy)
- **Triple-Store Pattern**: Maintaining documentation in three forms (practical, conceptual, narrative)

### Appendix C: References to Key Documents

Related documentation in this repository:

- `.claude/Agents/META_UPDATER.md` - Original specification (v1.0)
- `.claude/Scratchpad/SESSION_025_HANDOFF_SUMMARY.md` - Context on Session 025 signal amplification
- `CLAUDE.md` - Project guidelines and conventions
- `docs/architecture/PARALLELISM_FRAMEWORK.md` - Framework for understanding parallelization
- `.claude/skills/code-review/SKILL.md` - Example of well-documented skill
- `.claude/Agents/ORCHESTRATOR.md` - Example of complex agent specification
- `.claude/protocols/SIGNAL_PROPAGATION.md` - Example of protocol documentation

---

**Document Metadata:**
- **Created:** 2025-12-30
- **Author:** G2_RECON (SEARCH_PARTY operation)
- **Classification:** Documentation Enhancement - META_UPDATER Specification
- **Status:** Complete - Ready for META_UPDATER review and potential adoption
- **Scope:** Extends v1.0 META_UPDATER spec with patterns, processes, and best practices
- **Next Review:** 2026-03-30 (Quarterly)

