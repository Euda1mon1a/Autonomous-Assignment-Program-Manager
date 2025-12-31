# MCP Resilience Tools Documentation

**Mission**: G2_RECON SEARCH_PARTY reconnaissance of cross-industry resilience framework
**Status**: COMPLETE | **Generated**: 2025-12-30

---

## Quick Navigation

### For Your Role

**I'm a Manager/Administrator**
→ Start with: `RESILIENCE_TOOLS_SUMMARY.md`
→ Then read: "System Health Assessment" section
→ Action: Set up monitoring dashboards per "Production Monitoring" section

**I'm a Developer/Architect**
→ Start with: `mcp-tools-resilience.md`
→ Then read: "Tier 1-5 Tool Registry" section
→ Action: Review `/backend/app/resilience/service.py` for orchestration

**I'm an AI Assistant/Claude Code**
→ Start with: `RESILIENCE_TOOLS_SUMMARY.md` (quick overview)
→ Then: `quick-reference.md` (fast tool lookup)
→ Action: Use MCP tools for system analysis

**I'm in an Emergency**
→ Go directly to: "Emergency Response Workflow" in any document
→ Follow: 6-step DETECT → ASSESS → ACTIVATE → MONITOR → RECOVER → COMMUNICATE
→ Call: Relevant tool from emergency tool call sequences

---

## Documentation Files

### Primary Reference (Comprehensive)

**File**: `mcp-tools-resilience.md` (1,367 lines | 44 KB)

**Contents**:
- Executive overview with SEARCH_PARTY analysis
- MCP server architecture (tool locations, file structure)
- Complete inventory of all 82 tools organized by tier
- Detailed documentation for each tool with parameters
- Cross-disciplinary reference guide (11 domains)
- Emergency procedures with step-by-step workflows
- Comprehensive metric documentation with thresholds
- Integration checklist for developers
- Audit verification (no stealth analyses)

**Best For**: Technical reference, architecture decisions, detailed tool behavior

**Time to Read**: 45 minutes (full), 15 minutes (skimming key sections)

---

### Executive Summary (Overview)

**File**: `RESILIENCE_TOOLS_SUMMARY.md` (426 lines | 15 KB)

**Contents**:
- Quick facts (82 tools, 55+ modules, 100+ tests)
- Five-tier system overview with key tools
- Cross-disciplinary integration table (11 domains)
- System health assessment (5 defense levels)
- Emergency response workflow diagram
- Key metrics reference organized by category
- Production monitoring requirements
- Completeness verification using SEARCH_PARTY lenses

**Best For**: Executive briefing, quick reference, decision-making, onboarding

**Time to Read**: 10 minutes

---

### Mission Report (Investigation)

**File**: `MISSION_REPORT.md` (600+ lines)

**Contents**:
- Complete mission briefing and objectives
- Six-phase execution methodology
- Tool inventory with tier breakdown
- Stealth analysis audit results (NONE found)
- All SEARCH_PARTY lens findings
- Statistics and metrics
- Key recommendations for operations/devs/AI
- Appendices with reference data

**Best For**: Understanding how the system was analyzed, audit trail, verification

**Time to Read**: 25 minutes

---

### Quick Reference (Lookup)

**File**: `quick-reference.md` (350+ lines | 12 KB)

**Contents**:
- Categorized tool listing (82 tools with one-line descriptions)
- Quick usage patterns with code examples
- Tool response types reference
- Error codes and recovery procedures
- Performance expectations by category
- Recommended workflows (emergency, compliance, deployment)
- Tool dependencies

**Best For**: Fast lookup during development, emergency response, example code

**Time to Read**: 5 minutes (per lookup)

---

## Key Sections Across All Documents

### Understanding the Five Tiers

All documents explain the tier structure:

- **Tier 1 (Critical)**: 11 tools - Real-time health, crisis activation
- **Tier 2 (Strategic)**: 10 tools - Advanced analysis, planning
- **Tier 3 (Behavioral)**: 8 tools - Pattern prediction, stress analysis
- **Tier 4 (Epidemiological)**: 6 tools - Burnout spread, contagion
- **Tier 5 (Exotic Frontier)**: 47 tools - Advanced physics, frontier science

### Understanding Utilization Levels

All documents define the 5-level escalation:

```
GREEN     YELLOW    ORANGE    RED       BLACK
(<70%)    (70-80%)  (80-85%)  (85-95%)  (>95%)
Healthy   Advisory  Caution   Warning   Critical
```

### Understanding Defense Levels

All documents detail the 5-defense escalation:

```
PREVENTION → CONTROL → SAFETY SYSTEMS → CONTAINMENT → EMERGENCY
Normal         Monitor    Automate        Isolate       Fallback
```

### Understanding Metrics

Each document explains:
- **Utilization**: System capacity usage
- **Contingency**: Failure impact (N-1, N-2)
- **Homeostasis**: Feedback loop health (allostatic load)
- **Blast Radius**: Cross-zone impact
- **Early Warning**: Precursor detection (STA/LTA, fire index)
- **Epidemiology**: Burnout spread (Rt, SIR)
- **Fatigue**: Exhaustion level (Samn-Perelli, sleep debt)
- **Recovery**: Schedule fragility (recovery distance)

---

## How to Use These Documents Together

### Scenario 1: Emergency Response

1. **Alert received**: Utilization → RED
2. **Quick ref**: Check `quick-reference.md` → Emergency Response section
3. **Actions**: Follow 6-step workflow (DETECT → ASSESS → ACTIVATE...)
4. **Details**: If need full context, refer to `mcp-tools-resilience.md` "Emergency Procedures"

**Time**: 5-15 minutes depending on complexity

---

### Scenario 2: Architect Designing New Feature

1. **Understand framework**: Read `RESILIENCE_TOOLS_SUMMARY.md` tiers overview
2. **Identify gaps**: Check `mcp-tools-resilience.md` Tier 1-5 inventories
3. **Check existing implementations**: Review `/backend/app/resilience/` file listing
4. **Plan integration**: Reference `MISSION_REPORT.md` integration checklist
5. **Implement**: Follow CLAUDE.md (project guidelines)

**Time**: 60-120 minutes depending on feature scope

---

### Scenario 3: Production Monitoring Setup

1. **Requirements**: Read `RESILIENCE_TOOLS_SUMMARY.md` "Production Monitoring"
2. **Metrics**: Check same section "Key Metrics Reference"
3. **Alerts**: Review "Alert Thresholds" table
4. **Tool calls**: Look up specific tools in `quick-reference.md`
5. **Automation**: Code examples in `quick-reference.md` "Quick Usage Patterns"

**Time**: 30 minutes

---

### Scenario 4: AI Assistant Analysis

1. **Context**: Skim `RESILIENCE_TOOLS_SUMMARY.md` (5 min)
2. **Tool discovery**: Use `quick-reference.md` for lookup (as needed)
3. **Detail**: Read specific tool section in `mcp-tools-resilience.md` (when needed)
4. **Call tool**: Use MCP directly with parameters from documentation
5. **Interpret**: Use metric thresholds to understand results

**Time**: Real-time during tool use

---

## Key Statistics

```
Total MCP Tools:           82
├─ Tier 1 (Critical):      11 tools
├─ Tier 2 (Strategic):     10 tools
├─ Tier 3 (Behavioral):     8 tools
├─ Tier 4 (Epidemiology):   6 tools
└─ Tier 5 (Exotic):        47 tools

Backend Modules:           55+
API Endpoints:             40+
Test Suites:               100+
Cross-Disciplinary Domains: 11
Documentation Files:       4 (primary docs)
                          15+ (total in session)
```

---

## Domains Covered

| # | Domain | Tools | Key Metric |
|---|--------|-------|-----------|
| 1 | Queueing Theory | 3 | 80% utilization threshold |
| 2 | Epidemiology | 4 | Rt reproduction number |
| 3 | Manufacturing | 3 | SPC Western Electric rules |
| 4 | Seismology | 2 | STA/LTA ratio >2.5 |
| 5 | Forestry | 1 | Fire Weather Index |
| 6 | Materials Science | 2 | Larson-Miller <0.70 |
| 7 | Aviation | 7 | Samn-Perelli <5 |
| 8 | Finance | 4 | VaR 95%, CVaR |
| 9 | Physics | 10 | Entropy, phases |
| 10 | Graph Theory | 3 | Hub centrality >0.80 |
| 11 | Ecology | 2 | Keystone species |

---

## Where Are the Tools?

### MCP Server (Tool Registration)

```
/mcp-server/src/scheduler_mcp/
├── server.py ..................... 82 tools registered
├── resilience_integration.py ...... Tier 1 tools
├── composite_resilience_tools.py .. Unified Index, Recovery Dist
├── circuit_breaker_tools.py ....... Fail-fast isolation
├── early_warning_integration.py ... Seismic, SPC, Fire Index
├── frms_integration.py ............ Aviation fatigue models
├── var_risk_tools.py ............. Value-at-Risk modeling
├── thermodynamics_tools.py ........ Entropy, phase transitions
├── hopfield_attractor_tools.py .... Energy landscapes
├── time_crystal_tools.py ......... Anti-churn scheduling
└── immune_system_tools.py ........ Immunological patterns
```

### Backend Implementation

```
/backend/app/resilience/
├── service.py ..................... Central orchestration
├── utilization.py ................ 80% threshold
├── contingency.py ................ N-1/N-2 analysis
├── defense_in_depth.py ........... 5-level escalation
├── static_stability.py ........... Fallback schedules
├── sacrifice_hierarchy.py ........ Load shedding triage
├── homeostasis.py ............... Feedback loops
├── blast_radius.py .............. Zone isolation
├── le_chatelier.py .............. Equilibrium shifts
├── burnout_epidemiology.py ....... SIR model
├── spc_monitoring.py ............ Western Electric
├── seismic_detection.py ......... STA/LTA detection
├── burnout_fire_index.py ........ CFFDRS model
├── erlang_coverage.py ........... Telecom queuing
├── process_capability.py ........ Six Sigma metrics
├── creep_fatigue.py ............ Larson-Miller
├── recovery_distance.py ........ Schedule fragility
├── unified_critical_index.py ... Cross-domain risk
├── frms/ (7 modules) ........... Aviation fatigue
├── circuit_breaker/ (3 modules) . Fail-fast patterns
├── thermodynamics/ (3 modules) .. Entropy, phases
└── 15+ additional modules ....... Exotic frameworks
```

### API Routes

```
/backend/app/api/routes/
├── resilience.py ................ 40+ public endpoints
└── exotic_resilience.py ......... Exotic frontier endpoints
```

---

## Next Steps

### If You're a Manager

1. Read: `RESILIENCE_TOOLS_SUMMARY.md`
2. Review: "Production Monitoring" section
3. Action: Brief your team on:
   - 5 defense levels
   - Alert thresholds
   - Emergency response procedure
4. Delegate: Have architect set up monitoring dashboard

---

### If You're an Architect

1. Read: `mcp-tools-resilience.md`
2. Study: Backend module layout (section: "MCP Server Architecture")
3. Review: `/backend/app/resilience/service.py` (orchestration)
4. Plan: Which tools to expose in your frontend

---

### If You're a Developer

1. Read: `mcp-tools-resilience.md` (Tier 1-2 section)
2. Study: `/backend/app/resilience/utilization.py` (example implementation)
3. Review: `/backend/tests/test_resilience.py` (testing pattern)
4. Implement: Your feature following same pattern

---

### If You're an AI Assistant

1. Read: `RESILIENCE_TOOLS_SUMMARY.md` (5 min overview)
2. Bookmark: `quick-reference.md` (tool lookup)
3. Save: `mcp-tools-resilience.md` (detailed reference)
4. Use: MCP tools as questions arise
5. Follow: Emergency procedures when needed

---

## Completeness Verification

**All 10 SEARCH_PARTY Lenses Analyzed**:

- ✓ PERCEPTION: All 82 tools visible
- ✓ INVESTIGATION: Complete analysis coverage
- ✓ ARCANA: 11 domains integrated
- ✓ HISTORY: Full evolution documented
- ✓ INSIGHT: AI-assisted resilience operational
- ✓ RELIGION: All metrics accessible
- ✓ NATURE: Graduated complexity spectrum
- ✓ MEDICINE: System health comprehensive
- ✓ SURVIVAL: Emergency procedures ready
- ✓ STEALTH: ZERO undocumented analyses

**Conclusion**: System is FULLY TRANSPARENT with complete documentation.

---

## Support & References

### Project Guidelines

**File**: `/backend/CLAUDE.md` (Section: Resilience Framework)

**Contains**:
- Code style requirements
- Testing requirements
- Database migration procedures
- Git workflow
- AI rules of engagement

### Architecture Documentation

**Location**: `/docs/architecture/`

**Key Files**:
- `cross-disciplinary-resilience.md` - Framework overview
- `EXOTIC_FRONTIER_CONCEPTS.md` - Frontier science modules
- `TIME_CRYSTAL_ANTI_CHURN.md` - Anti-churn scheduling
- `SOLVER_ALGORITHM.md` - Constraint-based generation

### Research Papers

**Location**: `/docs/research/`

**Key Files**:
- `epidemiology-for-workforce-resilience.md`
- `materials-science-workforce-resilience.md`
- `exotic-control-theory-for-scheduling.md`
- `thermodynamic_resilience_foundations.md`

---

## Document Relationships

```
START
  │
  ├─→ (Quick Overview)
  │   └─ RESILIENCE_TOOLS_SUMMARY.md
  │      ├─→ (Emergency)
  │      │   └─ Emergency Response Workflow section
  │      └─→ (Production)
  │          └─ Production Monitoring section
  │
  ├─→ (Detailed Reference)
  │   └─ mcp-tools-resilience.md
  │      ├─→ (Specific Tool)
  │      │   └─ Tier X Tool Registry section
  │      ├─→ (Emergency Procedure)
  │      │   └─ Emergency Procedures section
  │      └─→ (Metrics)
  │          └─ Metric Documentation section
  │
  ├─→ (Fast Lookup)
  │   └─ quick-reference.md
  │      ├─→ (Tool by Name)
  │      │   └─ Tool Categories section
  │      └─→ (Code Example)
  │          └─ Quick Usage Patterns section
  │
  └─→ (Investigation Results)
      └─ MISSION_REPORT.md
         ├─→ (Audit Trail)
         │   └─ Stealth Analysis Audit section
         └─→ (Statistics)
             └─ Mission Statistics section
```

---

## Final Checklist

Before using this documentation:

- [ ] I understand the 5-tier tool structure
- [ ] I know the 5 defense levels (GREEN→BLACK)
- [ ] I can identify key metrics (utilization, contingency, Rt, fatigue)
- [ ] I know the 6-step emergency procedure
- [ ] I can find specific tools in quick-reference.md
- [ ] I know where backend modules are located
- [ ] I understand this system is 100% transparent
- [ ] I have bookmarked the documents for my role

---

**Documentation Status**: COMPLETE
**Last Updated**: 2025-12-30
**Verification**: Full SEARCH_PARTY audit ✓
**Accessibility**: Complete transparency ✓

---

**Ready to use. Questions? See documentation above for your role.**
