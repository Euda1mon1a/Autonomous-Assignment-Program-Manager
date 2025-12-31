***REMOVED*** Prompt Template Library - Master Index

> **Version:** 1.0
> **Last Updated:** 2025-12-31
> **Purpose:** Comprehensive prompt templates for all 47 agents and 10 probes

---

***REMOVED******REMOVED*** Quick Navigation

***REMOVED******REMOVED******REMOVED*** G-Staff Agents (6)
- [G1 Personnel](agents/G1_PERSONNEL_PROMPTS.md) - Recruitment, credentials, retention
- [G2 Recon](agents/G2_RECON_PROMPTS.md) - Intelligence, monitoring, threat detection
- [G3 Operations](agents/G3_OPERATIONS_PROMPTS.md) - Schedule execution, conflict resolution
- [G5 Planning](agents/G5_PLANNING_PROMPTS.md) - Schedule generation, optimization
- [G6 Signal](agents/G6_SIGNAL_PROMPTS.md) - Communication, notifications, alerts
- [Orchestrator](agents/ORCHESTRATOR_PROMPTS.md) - Multi-agent coordination

***REMOVED******REMOVED******REMOVED*** Development Agents (5)
- [Backend Engineer](agents/BACKEND_ENGINEER_PROMPTS.md) - API/service layer development
- [Frontend Engineer](agents/FRONTEND_ENGINEER_PROMPTS.md) - React/Next.js UI development
- [API Developer](agents/API_DEVELOPER_PROMPTS.md) - RESTful API design & documentation
- [Database Specialist](agents/DATABASE_SPECIALIST_PROMPTS.md) - Schema design, optimization
- [Test Engineer](agents/TEST_ENGINEER_PROMPTS.md) - Testing strategy, automation

***REMOVED******REMOVED******REMOVED*** Specialist Agents (5)
- [Security Auditor](agents/SECURITY_AUDITOR_PROMPTS.md) - Security assessment, vulnerability detection
- [ACGME Validator](agents/ACGME_VALIDATOR_PROMPTS.md) - Compliance validation, rule enforcement
- [Resilience Engineer](agents/RESILIENCE_ENGINEER_PROMPTS.md) - Failure analysis, contingency planning
- [Scheduler](agents/SCHEDULER_PROMPTS.md) - Schedule optimization, workload balancing
- [Swap Coordinator](agents/SWAP_COORDINATOR_PROMPTS.md) - Swap processing, matching, execution

***REMOVED******REMOVED******REMOVED*** Intelligence Probes (10)
- [Perception](probes/PERCEPTION_PROBE_PROMPTS.md) - Pattern detection, data profiling
- [Investigation](probes/INVESTIGATION_PROBE_PROMPTS.md) - Root cause analysis, evidence gathering
- [Arcana](probes/ARCANA_PROBE_PROMPTS.md) - Complex system analysis, constraint mechanics
- [History](probes/HISTORY_PROBE_PROMPTS.md) - Historical analysis, trend detection
- [Insight](probes/INSIGHT_PROBE_PROMPTS.md) - Personnel analysis, motivations
- [Religion](probes/RELIGION_PROBE_PROMPTS.md) - Policy analysis, institutional knowledge
- [Nature](probes/NATURE_PROBE_PROMPTS.md) - System ecology, natural patterns
- [Medicine](probes/MEDICINE_PROBE_PROMPTS.md) - Health diagnosis, problem detection
- [Survival](probes/SURVIVAL_PROBE_PROMPTS.md) - Crisis planning, resource management
- [Stealth](probes/STEALTH_PROBE_PROMPTS.md) - Covert analysis, vulnerability detection

---

***REMOVED******REMOVED*** Template Categories

***REMOVED******REMOVED******REMOVED*** Standard Templates (Present in all agent prompts)

Every agent prompt includes these 12 standard templates:

1. **Mission Briefing** - Initialize agent with mission parameters
2. **Primary Function** - Agent's main responsibility template
3. **Status Report** - Reporting on current state and metrics
4. **Escalation** - Escalate issues to decision-makers
5. **Handoff** - Transfer state to another agent
6. **Delegation** - Delegate tasks to other agents
7. **Error Handling** - Handle failures gracefully
8. **Additional** - Agent-specific templates (varies)

***REMOVED******REMOVED******REMOVED*** Probe-Specific Templates

Probes use D&D-inspired ability check templates:
- DC (Difficulty Class) based outcomes
- Success tiers with increasing information
- Confidence levels for findings
- Specialization-based analysis

---

***REMOVED******REMOVED*** Variable Naming Convention

All template variables follow this format:

```
${CATEGORY_SPECIFIC_NAME}

Examples:
  ${MISSION_OBJECTIVE}
  ${PERSON_ID}
  ${COVERAGE_PERCENT}
  ${COMPLIANCE_STATUS}
```

**Categories:**
- `MISSION_*` - Mission parameters
- `PERSON_*` - Personnel-related
- `SCHEDULE_*` - Schedule-related
- `COVERAGE_*` - Coverage metrics
- `COMPLIANCE_*` - ACGME compliance
- `RESOURCE_*` - Resources
- `TIME_*` - Time-related
- `STATUS_*` - Status information
- `RESULT_*` - Outcome/results

---

***REMOVED******REMOVED*** Template Usage Workflow

***REMOVED******REMOVED******REMOVED*** 1. **Select Template**
Choose the appropriate template for the current task from the agent's prompt file.

***REMOVED******REMOVED******REMOVED*** 2. **Initialize Variables**
Replace all `${VARIABLE}` placeholders with actual values:
```
${MISSION_OBJECTIVE} → "Generate schedule for Q1"
${PERSONNEL_COUNT} → 45
${COVERAGE_TARGET} → 95
```

***REMOVED******REMOVED******REMOVED*** 3. **Execute Mission**
Use the initialized template to guide the agent's actions.

***REMOVED******REMOVED******REMOVED*** 4. **Report Results**
Use the Status Report template to communicate outcomes.

***REMOVED******REMOVED******REMOVED*** 5. **Archive**
Store completed templates for audit trail.

---

***REMOVED******REMOVED*** Agent Template Summary

| Agent | Templates | Primary Use |
|-------|-----------|------------|
| G1 Personnel | 12 | Recruitment, credentials, retention |
| G2 Recon | 12 | Intelligence gathering, threat detection |
| G3 Operations | 12 | Schedule execution, conflict resolution |
| G5 Planning | 12 | Schedule generation, optimization |
| G6 Signal | 12 | Communication, notifications |
| Orchestrator | 12 | Multi-agent coordination |
| Backend Eng | 12 | API/service layer development |
| Frontend Eng | 12 | UI component development |
| API Dev | 8 | API design, documentation |
| DB Specialist | 7 | Schema design, optimization |
| Test Engineer | 12 | Test strategy, automation |
| Security Auditor | 8 | Security assessment |
| ACGME Validator | 8 | Compliance validation |
| Resilience Eng | 8 | Failure analysis, contingency |
| Scheduler | 8 | Schedule optimization |
| Swap Coordinator | 12 | Swap processing |

---

***REMOVED******REMOVED*** Key Features

***REMOVED******REMOVED******REMOVED*** Consistency
All templates follow the same structure:
- Clear objective statement
- Required parameters
- Step-by-step process
- Output format specification
- Success criteria

***REMOVED******REMOVED******REMOVED*** Extensibility
New templates can be added by:
1. Creating new template file
2. Following naming convention
3. Including all standard sections
4. Adding to this index

***REMOVED******REMOVED******REMOVED*** Traceability
Every template includes:
- Version number
- Last update date
- Agent/probe identifier
- Archive reference

***REMOVED******REMOVED******REMOVED*** Validation
Templates are validated for:
- Complete variable coverage
- Process completeness
- Output format correctness
- ACGME compliance (where applicable)

---

***REMOVED******REMOVED*** Performance Metrics

***REMOVED******REMOVED******REMOVED*** Template Effectiveness
- Measured by mission completion rate
- Tracked by audit trail
- Reported in agent status reports

***REMOVED******REMOVED******REMOVED*** Variables Used Per Template
- Average: 15-20 variables
- Range: 8-50 variables
- Critical: Those affecting compliance

***REMOVED******REMOVED******REMOVED*** Execution Time Targets
- Agent initialization: < 1 minute
- Template parameter setting: < 2 minutes
- Mission execution: Variable (by template type)

---

***REMOVED******REMOVED*** Best Practices

1. **Always initialize ALL variables** before executing
2. **Use consistent date/time formatting** across templates
3. **Log all escalations** for audit trail
4. **Archive completed templates** immediately after use
5. **Validate ACGME compliance** before marking tasks complete
6. **Document any deviations** from standard templates
7. **Track metrics** for continuous improvement

---

***REMOVED******REMOVED*** Future Enhancements

***REMOVED******REMOVED******REMOVED*** Planned Additions
- Template automation (auto-fill common variables)
- Conditional templates (if/then based on state)
- Machine-readable template definitions (YAML)
- Template composition library

***REMOVED******REMOVED******REMOVED*** In Development
- Template performance profiling
- Variable dependency mapping
- Cross-template consistency checking

---

***REMOVED******REMOVED*** Document Organization

```
.claude/prompts/
├── PROMPT_TEMPLATE_INDEX.md (this file)
├── infrastructure/
│   ├── TEMPLATE_VARIABLES.md
│   ├── TEMPLATE_COMPOSITION.md
│   ├── TEMPLATE_VALIDATION.md
│   ├── TEMPLATE_VERSIONING.md
│   ├── TEMPLATE_TESTING.md
│   ├── TEMPLATE_PERFORMANCE.md
│   └── TEMPLATE_USAGE_GUIDE.md
├── agents/
│   ├── G1_PERSONNEL_PROMPTS.md
│   ├── G2_RECON_PROMPTS.md
│   ├── ... (6 G-Staff)
│   ├── BACKEND_ENGINEER_PROMPTS.md
│   ├── ... (5 Development)
│   ├── SECURITY_AUDITOR_PROMPTS.md
│   ├── ... (5 Specialist)
└── probes/
    ├── PERCEPTION_PROBE_PROMPTS.md
    ├── ... (10 Probes)
```

---

***REMOVED******REMOVED*** Support & Maintenance

***REMOVED******REMOVED******REMOVED*** Issues?
1. Check TEMPLATE_USAGE_GUIDE.md for solutions
2. Verify all variables are initialized
3. Review TEMPLATE_VALIDATION.md
4. Check agent status report for errors

***REMOVED******REMOVED******REMOVED*** Contributing?
1. Follow variable naming convention
2. Include all 12 standard templates
3. Add entry to this index
4. Update version in index

***REMOVED******REMOVED******REMOVED*** Contact
For template library issues:
- Check documentation files
- Review recent commits
- Escalate to development lead

---

*This index should be updated whenever new templates are added.*
*Last Update: 2025-12-31*
