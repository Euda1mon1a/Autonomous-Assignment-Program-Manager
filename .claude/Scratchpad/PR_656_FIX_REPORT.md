# PR #656 Required Changes

## 1. HIERARCHY.md Updates (BLOCKING)

### Chain of Command Section (Replace lines 92-116)

**Current text to replace:**
```
## Chain of Command

```
ORCHESTRATOR (opus) ─── Supreme Commander
    │
    ├── ARCHITECT (opus) ─── Deputy for Systems
    │   ├── COORD_PLATFORM (sonnet) → DBA, BACKEND_ENGINEER, API_DEVELOPER
    │   ├── COORD_QUALITY (sonnet) → QA_TESTER, CODE_REVIEWER
    │   ├── COORD_ENGINE (sonnet) → SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST
    │   └── COORD_TOOLING (sonnet) → TOOLSMITH, TOOL_QA, TOOL_REVIEWER
    │
    └── SYNTHESIZER (opus) ─── Deputy for Operations
        ├── COORD_OPS (sonnet) → RELEASE_MANAGER, META_UPDATER, KNOWLEDGE_CURATOR, CI_LIAISON
        ├── COORD_RESILIENCE (sonnet) → RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, SECURITY_AUDITOR
        ├── COORD_FRONTEND (sonnet) → FRONTEND_ENGINEER, UX_SPECIALIST
        └── COORD_INTEL (sonnet) → (intel specialists)

    G-Staff (Advisory, sonnet) ─── Advisors to ORCHESTRATOR
        G-1 PERSONNEL, G-2 RECON, G-3 OPERATIONS, G-4 CONTEXT, G-5 PLANNING, G-6 SIGNAL

    Special Staff (Advisory, sonnet) ─── Domain Experts
        FORCE_MANAGER, DEVCOM_RESEARCH, MEDCOM

    IG (DELEGATION_AUDITOR) ─── Independent Oversight (sonnet)
    PAO (HISTORIAN) ─── Historical Record (sonnet)
```
```

**New text:**
```
## Chain of Command

```
ORCHESTRATOR (opus) ─── Supreme Commander
    │
    ├── ARCHITECT (opus) ─── Deputy for Systems
    │   ├── COORD_PLATFORM (sonnet) → DBA, BACKEND_ENGINEER, API_DEVELOPER
    │   ├── COORD_QUALITY (sonnet) → QA_TESTER, CODE_REVIEWER
    │   ├── COORD_ENGINE (sonnet) → SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST
    │   ├── COORD_TOOLING (sonnet) → TOOLSMITH, TOOL_QA, TOOL_REVIEWER
    │   └── G6_SIGNAL (sonnet) ─── Direct Support (Signal/Data)
    │
    └── SYNTHESIZER (opus) ─── Deputy for Operations
        ├── COORD_OPS (sonnet) → RELEASE_MANAGER, META_UPDATER, KNOWLEDGE_CURATOR, CI_LIAISON
        ├── COORD_RESILIENCE (sonnet) → RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, SECURITY_AUDITOR
        ├── COORD_FRONTEND (sonnet) → FRONTEND_ENGINEER, UX_SPECIALIST
        ├── COORD_INTEL (sonnet) → (intel specialists)
        ├── G1_PERSONNEL (sonnet) ─── Direct Support (Roster/Personnel)
        ├── G3_OPERATIONS (sonnet) ─── Direct Support (Operations)
        └── G4_CONTEXT_MANAGER (sonnet) ─── Direct Support (Context/Logistics)

    G-Staff General Support (Advisory, sonnet) ─── Attachable to Either Deputy
        G-2 RECON, G-5 PLANNING

    Special Staff (Advisory, sonnet) ─── Domain Experts
        FORCE_MANAGER, DEVCOM_RESEARCH, MEDCOM

    IG (DELEGATION_AUDITOR) ─── Independent Oversight (sonnet)
    PAO (HISTORIAN) ─── Historical Record (sonnet)
```
```

### G-Staff Intel Routing Section (Replace lines 162-179)

**Current text to replace:**
```
## G-Staff Intel Routing

G-Staff agents are advisory. Their intel SHOULD route through Deputies for strategic interpretation, but CAN go direct to ORCHESTRATOR for urgent matters.

| G-Staff | Primary Route | Strategic Interpretation |
|---------|---------------|-------------------------|
| G-1 PERSONNEL | → ORCHESTRATOR | Via FORCE_MANAGER (team assembly) |
| G-2 RECON | → ORCHESTRATOR | Via ARCHITECT (systems) or SYNTHESIZER (ops) |
| G-3 OPERATIONS | → ORCHESTRATOR | Via SYNTHESIZER (operational conflicts) |
| G-4 CONTEXT | → ORCHESTRATOR | Direct (context management) |
| G-5 PLANNING | → ORCHESTRATOR | Via ARCHITECT (strategic planning) |
| G-6 SIGNAL | → ORCHESTRATOR | Via SYNTHESIZER (data/metrics) |

**Routing Guidance:**
- **Urgent/Time-Critical**: Direct to ORCHESTRATOR
- **Strategic/Interpretive**: Route through appropriate Deputy
- **Cross-Domain**: Both Deputies may be consulted
```

**New text:**
```
## G-Staff Intel Routing

G-Staff agents are organized into three groups based on reporting relationships:

### Direct Support to Deputies

These G-Staff members report directly to their respective Deputy and provide domain-specific support:

| G-Staff | Reports To | Role |
|---------|------------|------|
| G1_PERSONNEL | SYNTHESIZER | Personnel/roster management, utilization analysis |
| G3_OPERATIONS | SYNTHESIZER | Operational coordination, workflow execution |
| G4_CONTEXT_MANAGER | SYNTHESIZER | Context logistics, RAG management, memory persistence |
| G6_SIGNAL | ARCHITECT | Data aggregation, metrics collection, observability |

**Routing:** Direct to their Deputy for all matters. Deputy escalates to ORCHESTRATOR if needed.

### General Support (Attachable)

These G-Staff members can be attached to either Deputy based on mission requirements:

| G-Staff | Primary Attachment | Secondary Attachment | Role |
|---------|-------------------|---------------------|------|
| G2_RECON | ARCHITECT (systems recon) | SYNTHESIZER (ops recon) | Intelligence gathering, reconnaissance |
| G5_PLANNING | ARCHITECT (strategic planning) | SYNTHESIZER (operational planning) | Strategy development, execution planning |

**Routing:** Through Deputy they're attached to for current mission. ORCHESTRATOR assigns attachment based on task domain.

### Routing Guidance

- **Direct Support agents**: Always route through assigned Deputy
- **General Support agents**: Route through Deputy they're attached to for current mission
- **Urgent/Time-Critical**: Can go direct to ORCHESTRATOR with Deputy notification
- **Cross-Domain**: ORCHESTRATOR coordinates both Deputies
```

## 2. Identity Card Validation (RECOMMENDED)

### Option A: Pre-commit Hook (Automated)

Create file: `.git/hooks/pre-commit-identity-validation`

```bash
#!/bin/bash
# Identity card validation pre-commit hook
# Validates that agent identity cards match their parent specs

AGENTS_DIR=".claude/Agents"
FAILURES=0

echo "Validating agent identity cards..."

# Function to extract "Reports To" from agent spec
get_reports_to() {
    local file=$1
    grep "^> \*\*Reports To:\*\*" "$file" | sed 's/^> \*\*Reports To:\*\* //' | sed 's/ .*//'
}

# Check all G-Staff agents
for agent in G1_PERSONNEL G2_RECON G3_OPERATIONS G4_CONTEXT_MANAGER G5_PLANNING G6_SIGNAL; do
    spec_file="$AGENTS_DIR/${agent}.md"

    if [ ! -f "$spec_file" ]; then
        echo "ERROR: Missing spec for $agent"
        FAILURES=$((FAILURES + 1))
        continue
    fi

    reports_to=$(get_reports_to "$spec_file")

    # Validate against expected reporting structure
    case $agent in
        G1_PERSONNEL|G3_OPERATIONS|G4_CONTEXT_MANAGER)
            if [ "$reports_to" != "SYNTHESIZER" ]; then
                echo "ERROR: $agent reports to '$reports_to', expected 'SYNTHESIZER'"
                FAILURES=$((FAILURES + 1))
            fi
            ;;
        G6_SIGNAL)
            if [ "$reports_to" != "ARCHITECT" ]; then
                echo "ERROR: $agent reports to '$reports_to', expected 'ARCHITECT'"
                FAILURES=$((FAILURES + 1))
            fi
            ;;
        G2_RECON|G5_PLANNING)
            if [ "$reports_to" != "ORCHESTRATOR" ]; then
                echo "ERROR: $agent reports to '$reports_to', expected 'ORCHESTRATOR' (General Support)"
                FAILURES=$((FAILURES + 1))
            fi
            ;;
    esac
done

if [ $FAILURES -gt 0 ]; then
    echo ""
    echo "Identity card validation failed with $FAILURES error(s)"
    echo "Please update agent specs to match HIERARCHY.md"
    exit 1
fi

echo "Identity card validation passed!"
exit 0
```

### Option B: Manual Validation Script (On-demand)

Create file: `scripts/validate-identity-cards.sh`

```bash
#!/bin/bash
# Manual identity card validation script
# Run: ./scripts/validate-identity-cards.sh

AGENTS_DIR=".claude/Agents"
HIERARCHY_FILE=".claude/Governance/HIERARCHY.md"

echo "=== Agent Identity Card Validation ==="
echo ""
echo "Checking against: $HIERARCHY_FILE"
echo ""

# Function to extract "Reports To" from agent spec
get_reports_to() {
    local file=$1
    grep "^> \*\*Reports To:\*\*" "$file" | sed 's/^> \*\*Reports To:\*\* //' | sed 's/ .*//'
}

# Function to check if standing orders section exists
check_standing_orders() {
    local file=$1
    if grep -q "## Standing Orders" "$file"; then
        echo "✓"
    else
        echo "✗"
    fi
}

# Function to check if escalation section exists
check_escalation() {
    local file=$1
    if grep -q "## Escalation" "$file" || grep -q "## Escalate" "$file"; then
        echo "✓"
    else
        echo "✗"
    fi
}

echo "| Agent | Reports To | Expected | Match | Standing Orders | Escalation |"
echo "|-------|-----------|----------|-------|----------------|------------|"

FAILURES=0

for agent in G1_PERSONNEL G2_RECON G3_OPERATIONS G4_CONTEXT_MANAGER G5_PLANNING G6_SIGNAL; do
    spec_file="$AGENTS_DIR/${agent}.md"

    if [ ! -f "$spec_file" ]; then
        echo "| $agent | MISSING | - | ✗ | - | - |"
        FAILURES=$((FAILURES + 1))
        continue
    fi

    reports_to=$(get_reports_to "$spec_file")
    standing_orders=$(check_standing_orders "$spec_file")
    escalation=$(check_escalation "$spec_file")

    # Determine expected reporting
    case $agent in
        G1_PERSONNEL|G3_OPERATIONS|G4_CONTEXT_MANAGER)
            expected="SYNTHESIZER"
            ;;
        G6_SIGNAL)
            expected="ARCHITECT"
            ;;
        G2_RECON|G5_PLANNING)
            expected="ORCHESTRATOR"
            ;;
    esac

    if [ "$reports_to" = "$expected" ]; then
        match="✓"
    else
        match="✗"
        FAILURES=$((FAILURES + 1))
    fi

    echo "| $agent | $reports_to | $expected | $match | $standing_orders | $escalation |"
done

echo ""
if [ $FAILURES -gt 0 ]; then
    echo "❌ Validation failed with $FAILURES error(s)"
    exit 1
else
    echo "✅ All identity cards valid!"
    exit 0
fi
```

## 3. Party Skill Decision Guide (RECOMMENDED)

Add new section to `.claude/Governance/HIERARCHY.md` after line 194 (after Script Ownership section):

```markdown
## Party Skill Decision Matrix

PAI includes 7 parallel party deployment skills for specialized mass reconnaissance and validation. Each is owned by a specific G-Staff agent and optimized for different intelligence gathering missions.

### Available Party Skills

| Skill | Owner | Probes | Timeout | Use Case |
|-------|-------|--------|---------|----------|
| `/search-party` | G2_RECON | 120 (12 G-2s × 10 probes) | 120s | Comprehensive codebase reconnaissance |
| `/plan-party` | G5_PLANNING | 10 strategy probes | 90s | Multi-perspective implementation planning |
| `/qa-party` | COORD_QUALITY | 8+ validation agents | 180s | Parallel test/lint/health validation |
| `/roster-party` | G1_PERSONNEL | Personnel probes | 60s | Team composition and capability analysis |
| `/ops-party` | G3_OPERATIONS | Pre-execution probes | 90s | Pre-execution validation and readiness |
| `/context-party` | G4_CONTEXT_MANAGER | Historical context probes | 60s | Session history and precedent mining |
| `/signal-party` | G6_SIGNAL | Metrics collection probes | 120s | System-wide metrics aggregation |

### Decision Tree

```
START: Complex task received
    │
    ├─ Need codebase intel?
    │   └─ YES → /search-party (G2_RECON)
    │       └─ Need implementation strategy?
    │           └─ YES → /plan-party (G5_PLANNING)
    │               └─ Ready to execute?
    │                   └─ YES → /ops-party (G3_OPERATIONS)
    │                       └─ After execution → /qa-party (COORD_QUALITY)
    │
    ├─ Need team assessment?
    │   └─ YES → /roster-party (G1_PERSONNEL)
    │
    ├─ Need historical context?
    │   └─ YES → /context-party (G4_CONTEXT_MANAGER)
    │
    └─ Need system metrics?
        └─ YES → /signal-party (G6_SIGNAL)
```

### Common Workflows

**Full Intelligence → Execution Pipeline:**
```
1. /search-party    (G2: Recon the terrain)
2. /plan-party      (G5: Develop strategy)
3. /ops-party       (G3: Pre-flight checks)
4. [Execute]
5. /qa-party        (QA: Validate results)
```

**Quick Tactical Assessment:**
```
1. /search-party backend/specific/path/
2. [Direct execution - no planning party needed]
3. /qa-party
```

**Team Capability Review:**
```
1. /roster-party     (G1: Current capabilities)
2. /context-party    (G4: Historical decisions on team structure)
```

**System Health Check:**
```
1. /signal-party     (G6: Collect all metrics)
2. /qa-party         (QA: Validate systems)
```

### When NOT to Use Party Skills

Skip party deployment for:
- Simple, single-file changes with known impact
- Emergency P0 fixes (time-critical)
- Trivial tasks (typo fixes, README updates)
- Tasks with clear, obvious approach

**Rule of Thumb:** If task complexity < 5/10 and single domain, execute directly.

### Economics: Zero Marginal Wall-Clock Cost

**Critical Understanding:** Parallel agents with same timeout cost nothing extra in wall-clock time.

```
Sequential (BAD):        Parallel (GOOD):
10 probes × 30s each     10 probes × 30s in parallel
Total: 300s              Total: 30s (10× faster)
```

**Implication:** Always deploy full party. No cost savings from partial deployment.

### IDE Crash Prevention

**CRITICAL:** Never have ORCHESTRATOR spawn multiple agents directly.

**CORRECT Pattern:**
```
ORCHESTRATOR → spawns 1 Party Commander (G2_RECON, G5_PLANNING, etc.)
                    ↓
              Commander deploys party internally
              (manages parallelism, synthesizes results)
```

**WRONG Pattern (causes IDE crash):**
```
ORCHESTRATOR → spawns 12 agents directly → IDE SEIZURE/CRASH
```

The Party Commander agent absorbs parallelism complexity. ORCHESTRATOR only spawns 1 coordinator.
```

## 4. Armory Notation Updates (RECOMMENDED)

Search for Armory agent references and add notation:

```bash
grep -r "INCIDENT_COMMANDER\|CRASH_RECOVERY" .claude/Agents/*.md | grep -v ".md:>" | cut -d: -f1 | sort -u
```

For each file found, add "(Armory - production activation)" where these agents are mentioned.

## 5. Update Individual Agent Specs (BLOCKING)

The following agent spec files need their "Reports To" field updated:

### G1_PERSONNEL.md
**Current (line 8):** `> **Reports To:** ORCHESTRATOR (G-Staff)`
**New:** `> **Reports To:** SYNTHESIZER (Direct Support)`

### G3_OPERATIONS.md
**Current (line 8):** `> **Reports To:** ORCHESTRATOR (G-Staff)`
**New:** `> **Reports To:** SYNTHESIZER (Direct Support)`

### G4_CONTEXT_MANAGER.md
**Current (line 8):** `> **Reports To:** ORCHESTRATOR (G-Staff)`
**New:** `> **Reports To:** SYNTHESIZER (Direct Support)`

### G6_SIGNAL.md
**Current (line 8):** `> **Reports To:** ORCHESTRATOR (G-Staff)`
**New:** `> **Reports To:** ARCHITECT (Direct Support)`

### G2_RECON.md and G5_PLANNING.md
**Current (line 8):** `> **Reports To:** ORCHESTRATOR (G-Staff)`
**New:** `> **Reports To:** ORCHESTRATOR (General Support - attachable)`

---

## Implementation Checklist

- [ ] Update HIERARCHY.md Chain of Command diagram (lines 92-116)
- [ ] Update HIERARCHY.md G-Staff Intel Routing section (lines 162-179)
- [ ] Add Party Skill Decision Matrix to HIERARCHY.md (after line 194)
- [ ] Update G1_PERSONNEL.md "Reports To" field (line 8) → SYNTHESIZER
- [ ] Update G3_OPERATIONS.md "Reports To" field (line 8) → SYNTHESIZER
- [ ] Update G4_CONTEXT_MANAGER.md "Reports To" field (line 8) → SYNTHESIZER
- [ ] Update G6_SIGNAL.md "Reports To" field (line 8) → ARCHITECT
- [ ] Update G2_RECON.md "Reports To" field (line 8) → ORCHESTRATOR (General Support)
- [ ] Update G5_PLANNING.md "Reports To" field (line 8) → ORCHESTRATOR (General Support)
- [ ] Create validation script: `scripts/validate-identity-cards.sh`
- [ ] Search for Armory agent references and add notation
- [ ] Run validation script to verify all changes
- [ ] Commit with message: "fix: Update G-Staff reporting structure per PR #656 review"
