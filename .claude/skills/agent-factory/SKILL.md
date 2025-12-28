---
name: agent-factory
description: Create new PAI agents using AGENT_FACTORY.md patterns. Guides through archetype selection (Researcher, Validator, Generator, Critic, Synthesizer), validates against CONSTITUTION.md, and generates agent specifications following established templates.
---

# Agent Factory Skill

Meta-skill for creating new PAI (Personal AI) agents using established archetypes and templates.

## When This Skill Activates

- User requests creation of a new agent
- Need to extend PAI system with specialized capability
- Orchestrator identifies gap requiring new agent
- Existing agents cannot handle emerging responsibility
- `/agent-factory` command invoked

## Prerequisites

- Read access to `.claude/Agents/AGENT_FACTORY.md` (archetype patterns)
- Read access to `.claude/Agents/TOOLSMITH.md` (agent template)
- Read access to `.claude/CONSTITUTION.md` (governance rules)
- Read access to existing agents for pattern reference

---

## Agent Creation Workflow

### Phase 1: Requirements Gathering

```
1. Clarify Agent Purpose
   - What problem does this agent solve?
   - What responsibilities will it have?
   - What is its scope (files/directories owned)?
   - Who will this agent interact with?

2. Identify Gaps
   - Does an existing agent already cover this?
   - Can an existing agent be extended instead?
   - Is this truly a new responsibility?

3. Define Success Criteria
   - How will we measure agent effectiveness?
   - What are the key performance indicators?
```

### Phase 2: Archetype Selection

Choose ONE archetype from AGENT_FACTORY.md:

| Archetype | Purpose | Personality | Use When |
|-----------|---------|-------------|----------|
| **Researcher** | Explore, investigate, synthesize | Curious, thorough, patient | Need to understand, analyze, report |
| **Validator** | Verify, check constraints | Meticulous, rule-focused, conservative | Need to ensure correctness, compliance |
| **Generator** | Create solutions, produce output | Creative, pragmatic, iterative | Need to build, implement, generate |
| **Critic** | Find flaws, test edge cases | Adversarial, skeptical, thorough | Need to stress-test, find weaknesses |
| **Synthesizer** | Combine outputs, resolve conflicts | Integrative, diplomatic, clear | Need to merge, summarize, decide |

**Selection Questions:**
1. Does this agent primarily READ or WRITE?
   - READ-heavy → Researcher or Validator
   - WRITE-heavy → Generator
   - BOTH → Consider Synthesizer

2. Is the agent's role defensive or constructive?
   - Defensive (prevent problems) → Validator or Critic
   - Constructive (create solutions) → Generator or Researcher

3. Does the agent work alone or coordinate others?
   - Independent work → Any archetype
   - Coordination role → Synthesizer

### Phase 3: Authority Level Determination

Determine decision authority tier:

| Level | Can Do | Cannot Do | Example |
|-------|--------|-----------|---------|
| **Propose-Only** | Analyze, recommend | Execute changes | META_UPDATER |
| **Execute with Safeguards** | Execute after validation | Bypass safety checks | SCHEDULER |
| **Full Execute** | Execute independently | N/A (highest tier) | Reserved for ops |

**Authority Rules from CONSTITUTION.md:**
- All agents can: read code, run tests, create branches
- Approval required for: code edits, git operations, deployments
- Forbidden always: bypass ACGME, disable security, merge to main without PR

### Phase 4: Specification Drafting

Use the Agent Specification Template from TOOLSMITH.md:

```markdown
# <AGENT_NAME> Agent

> **Role:** <one-line role description>
> **Authority Level:** <Propose-Only | Execute with Safeguards | Full Execute>
> **Archetype:** <Researcher | Validator | Generator | Critic | Synthesizer>
> **Status:** Active

---

## Charter

<2-3 paragraphs describing the agent's purpose and responsibilities>

**Primary Responsibilities:**
- <responsibility 1>
- <responsibility 2>
- <responsibility 3>

**Scope:**
- <files/directories this agent owns>

**Philosophy:**
"<guiding principle in quotes>"

---

## Personality Traits

**<Trait 1 Category>**
- <trait description>

**<Trait 2 Category>**
- <trait description>

**Communication Style**
- <how agent communicates>

---

## Decision Authority

### Can Independently Execute
<numbered list of autonomous actions>

### Requires Approval (Create PR, Don't Merge)
<numbered list of actions requiring review>

### Must Escalate
<numbered list of actions that must be escalated>

---

## Key Workflows

### Workflow 1: <Name>
```
<step-by-step workflow>
```

### Workflow 2: <Name>
```
<step-by-step workflow>
```

---

## Escalation Rules

| Situation | Escalate To | Reason |
|-----------|-------------|--------|
| <situation> | <agent/role> | <reason> |

---

## Success Metrics

### <Category 1>
- **<Metric>:** <target value>

### <Category 2>
- **<Metric>:** <target value>

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | YYYY-MM-DD | Initial <AGENT_NAME> specification |

---

**Next Review:** <date 3-6 months out>
```

### Phase 5: Validation

Before finalizing, verify against CONSTITUTION.md:

**Governance Checklist:**
- [ ] Agent respects constraint hierarchy (Regulatory > Institutional > Optimization)
- [ ] Agent cannot bypass ACGME rules (Section III.A)
- [ ] Agent follows security defense-in-depth (Section V)
- [ ] Agent respects autonomy boundaries (Section VI)
- [ ] Agent has clear escalation rules
- [ ] Agent follows error handling requirements (Section IX)
- [ ] Agent has defined rollback procedures for state changes

**Consistency Checklist:**
- [ ] Naming follows conventions (UPPER_SNAKE_CASE for agents)
- [ ] Authority level matches archetype
- [ ] Skills access matches responsibilities
- [ ] No overlap with existing agents
- [ ] Workflows are complete and actionable

### Phase 6: Creation

1. **Create Agent Specification:**
   ```
   File: .claude/Agents/<AGENT_NAME>.md
   ```

2. **Create PR for Review:**
   - Title: `agent: Add <AGENT_NAME> agent specification`
   - Description: Problem statement, archetype rationale, scope
   - Reviewers: ARCHITECT (required), affected agents (optional)

3. **Document in Index:**
   - Update agent index if exists
   - Add to relevant documentation

---

## Example: Creating a SECURITY_AUDITOR Agent

**Step 1: Requirements**
```
Problem: Need dedicated security review capability
Responsibilities: Audit code for vulnerabilities, check HIPAA compliance
Scope: All code touching auth, data, secrets
Success: Zero security incidents from reviewed code
```

**Step 2: Archetype Selection**
```
Q: Read or Write heavy? → READ (auditing, not implementing)
Q: Defensive or constructive? → DEFENSIVE (finding problems)
Q: Independent or coordinating? → INDEPENDENT

→ Best match: CRITIC (adversarial, finds flaws) or VALIDATOR (checks rules)
→ Decision: VALIDATOR (security has defined rules to check)
```

**Step 3: Authority**
```
Level: Propose-Only
- Can: Analyze code, run security scans, report findings
- Cannot: Block deployments (only recommend)
- Escalate: Critical vulnerabilities → ARCHITECT + Faculty
```

**Step 4: Specification**
```markdown
# SECURITY_AUDITOR Agent

> **Role:** Security Vulnerability Detection & Compliance Verification
> **Authority Level:** Propose-Only (Cannot Block, Only Report)
> **Archetype:** Validator
> **Status:** Active

## Charter

The SECURITY_AUDITOR agent is responsible for proactively identifying
security vulnerabilities, verifying HIPAA compliance, and ensuring
military OPSEC/PERSEC requirements are met...

[... rest of specification ...]
```

**Step 5: Validation**
- [x] Respects CONSTITUTION rules
- [x] No ACGME bypass capability
- [x] Follows security guidelines
- [x] Clear escalation to ARCHITECT
- [x] Naming: SECURITY_AUDITOR (UPPER_SNAKE_CASE)

**Step 6: Create PR**
```bash
git checkout -b agent/add-security-auditor
# Create file: .claude/Agents/SECURITY_AUDITOR.md
git add .claude/Agents/SECURITY_AUDITOR.md
git commit -m "agent: Add SECURITY_AUDITOR agent specification"
git push -u origin agent/add-security-auditor
gh pr create --title "agent: Add SECURITY_AUDITOR agent" \
  --body "Adds security audit specialist..."
```

---

## Archetype Deep Dive

### Researcher Agents

**Best For:** Investigation, analysis, documentation, learning
**Personality Traits:** Curious, thorough, patient, synthesizing
**Skills Access:** Read-only (cannot modify, only observe)
**Output Format:** Reports, summaries, recommendations

**Example Researchers:**
- CODEBASE_ANALYST: Understand code patterns
- COMPLIANCE_INVESTIGATOR: Research regulatory requirements
- PERFORMANCE_PROFILER: Analyze bottlenecks

### Validator Agents

**Best For:** Compliance checking, rule enforcement, quality gates
**Personality Traits:** Meticulous, conservative, rule-focused
**Skills Access:** Validation tools, limited execution
**Output Format:** Pass/fail, violation reports, compliance scores

**Example Validators:**
- ACGME_VALIDATOR: Check work hour compliance
- CODE_QUALITY_GATE: Enforce standards before merge
- CREDENTIAL_CHECKER: Verify personnel qualifications

### Generator Agents

**Best For:** Creating solutions, implementing features, producing output
**Personality Traits:** Creative, pragmatic, iterative, solution-oriented
**Skills Access:** Full access within scope
**Output Format:** Code, schedules, proposals, artifacts

**Example Generators:**
- SCHEDULER: Generate compliant schedules
- TEST_GENERATOR: Create comprehensive test suites
- MIGRATION_BUILDER: Create database migrations

### Critic Agents

**Best For:** Finding bugs, stress testing, adversarial analysis
**Personality Traits:** Adversarial, skeptical, edge-case-focused
**Skills Access:** Testing tools, simulation capabilities
**Output Format:** Bug reports, vulnerability assessments

**Example Critics:**
- CHAOS_ENGINEER: Test resilience under failure
- EDGE_CASE_FINDER: Discover boundary conditions
- SECURITY_PENETRATOR: Find attack vectors

### Synthesizer Agents

**Best For:** Combining outputs, resolving conflicts, making decisions
**Personality Traits:** Integrative, diplomatic, decision-making
**Skills Access:** Read access to all, limited write
**Output Format:** Unified reports, decisions, action plans

**Example Synthesizers:**
- ORCHESTRATOR: Coordinate multiple agents
- REPORT_CONSOLIDATOR: Merge findings into executive summary
- CONFLICT_RESOLVER: Resolve contradicting recommendations

---

## Common Mistakes to Avoid

1. **Overlapping Scope**
   - Check existing agents before creating new ones
   - If overlap exists, extend existing agent instead

2. **Excessive Authority**
   - Start with Propose-Only, upgrade if needed
   - Validators shouldn't Generator authority

3. **Vague Responsibilities**
   - Be specific: "validate ACGME 80-hour rule" not "check things"
   - Define measurable success criteria

4. **Missing Escalation Rules**
   - Every agent must know when to ask for help
   - Define specific scenarios, not just "when in doubt"

5. **Ignoring CONSTITUTION.md**
   - All agents bound by Constitution
   - Re-read Section VI (Agent Autonomy) before finalizing

---

## Integration with Other Skills

### With TOOLSMITH
When agent needs associated skill:
1. Create agent spec (this skill)
2. Invoke TOOLSMITH to create supporting skill
3. Link skill to agent in spec

### With code-review
Before merging agent spec:
1. Create PR with agent spec
2. code-review validates format and consistency
3. ARCHITECT reviews authority and scope

### With test-writer
For testable agent behaviors:
1. Define expected behaviors in spec
2. test-writer creates behavior tests
3. Validate agent against tests

---

## References

- `.claude/Agents/AGENT_FACTORY.md` - Full archetype definitions
- `.claude/Agents/TOOLSMITH.md` - Agent template structure
- `.claude/CONSTITUTION.md` - Governance rules (MUST READ)
- `.claude/Agents/SCHEDULER.md` - Example operational agent
- `.claude/Agents/META_UPDATER.md` - Example propose-only agent
