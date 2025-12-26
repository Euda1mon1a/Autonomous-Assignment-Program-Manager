***REMOVED*** Prompt Templates - Meta-Prompting Library

> **Purpose:** Standardized, reusable prompt templates for common PAI (Personal AI Infrastructure) tasks
> **Location:** `.claude/PromptTemplates/`
> **Last Updated:** 2025-12-26

---

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Template Syntax](***REMOVED***template-syntax)
3. [When to Use Templates](***REMOVED***when-to-use-templates)
4. [Template Composition Patterns](***REMOVED***template-composition-patterns)
5. [Available Templates](***REMOVED***available-templates)
6. [Creating New Templates](***REMOVED***creating-new-templates)
7. [Best Practices](***REMOVED***best-practices)

---

***REMOVED******REMOVED*** Overview

***REMOVED******REMOVED******REMOVED*** What is Meta-Prompting?

Meta-prompting is the practice of using **structured templates** to generate consistent, high-quality prompts for AI agents. Instead of writing ad-hoc prompts each time, you instantiate a template with specific parameters.

**Benefits:**
- **Consistency**: Same structure for similar tasks
- **Quality**: Built-in best practices and completeness checks
- **Efficiency**: Faster than writing from scratch
- **Maintainability**: Update template once, affects all uses
- **Composability**: Combine templates for complex workflows

***REMOVED******REMOVED******REMOVED*** Use Cases

| Template | Use Case | Typical User |
|----------|----------|--------------|
| `RESEARCH_POLICY.md` | Investigate ACGME rules, institutional policies | Program Director, Coordinator |
| `SCHEDULE_GENERATION.md` | Create monthly/block schedules | Scheduler, Coordinator |
| `INCIDENT_REVIEW.md` | Analyze schedule failures, coverage gaps | Chief Resident, PD |
| `CONSTRAINT_ANALYSIS.md` | Debug conflicting requirements | Scheduler, Developer |
| `SWAP_REQUEST.md` | Process resident swap requests | Faculty, Coordinator |

---

***REMOVED******REMOVED*** Template Syntax

***REMOVED******REMOVED******REMOVED*** Variable Placeholders

Use `{{variable_name}}` for required parameters:

```
Research {{policy_name}} covering {{time_period}}.
```

**Instantiation:**
```
Research ACGME 2023 Common Program Requirements covering July 2023 - June 2024.
```

***REMOVED******REMOVED******REMOVED*** Conditional Sections

Use `[IF condition]...[ENDIF]` for optional content:

```
[IF urgent]
⚠️ **URGENT**: This requires immediate attention.
[ENDIF]

Analyze {{issue}}.
```

**Instantiation (urgent=true):**
```
⚠️ **URGENT**: This requires immediate attention.

Analyze double-booking on 2024-01-15.
```

**Instantiation (urgent=false):**
```
Analyze double-booking on 2024-01-15.
```

***REMOVED******REMOVED******REMOVED*** Loops/Iteration

Use `[FOR item IN list]...[ENDFOR]` for repeating sections:

```
Check the following constraints:
[FOR constraint IN constraints]
- {{constraint.name}}: {{constraint.description}}
[ENDFOR]
```

**Instantiation:**
```
Check the following constraints:
- Max 80 hours/week: ACGME work hour limit
- 1-in-7 days off: Mandatory rest day
- Supervision ratio: 1:2 for PGY-1
```

***REMOVED******REMOVED******REMOVED*** Nested Structures

Combine conditionals and loops:

```
[FOR resident IN residents]
**{{resident.name}}** ({{resident.level}})
[IF resident.on_leave]
  Status: On leave until {{resident.return_date}}
[ENDIF]
[ENDFOR]
```

***REMOVED******REMOVED******REMOVED*** Default Values

Use `{{variable_name|default_value}}` for optional parameters:

```
Priority: {{priority|medium}}
Deadline: {{deadline|none specified}}
```

---

***REMOVED******REMOVED*** When to Use Templates

***REMOVED******REMOVED******REMOVED*** ✅ Use Templates When:

1. **Recurring Tasks**: You perform this task regularly (weekly schedule generation)
2. **Standardized Output**: The output format needs consistency (incident reports)
3. **Complex Structure**: The prompt has many required elements (policy research)
4. **Team Collaboration**: Multiple people perform the same task (swap processing)
5. **Audit Trail**: You need reproducible, documented reasoning
6. **Quality Assurance**: Built-in validation or safety checks

***REMOVED******REMOVED******REMOVED*** ❌ Don't Use Templates When:

1. **One-Off Questions**: Simple, unique queries ("What's the weather?")
2. **Exploratory Work**: Open-ended research with unknown structure
3. **Rapid Iteration**: Still experimenting with prompt structure
4. **Highly Context-Specific**: No generalization value

***REMOVED******REMOVED******REMOVED*** Example Decision Tree

```
Is this task recurring or one-time?
├─ One-time
│  └─ Is the structure complex with many required elements?
│     ├─ Yes → Consider creating a new template
│     └─ No → Use direct prompt
└─ Recurring
   └─ Use existing template (or create one if none exists)
```

---

***REMOVED******REMOVED*** Template Composition Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: Sequential Composition

Execute templates in sequence, passing outputs forward:

```bash
***REMOVED*** Step 1: Research policy
Output1 = RESEARCH_POLICY(policy="ACGME 2023 CPR")

***REMOVED*** Step 2: Generate schedule using research findings
Output2 = SCHEDULE_GENERATION(
  constraints=Output1.key_findings,
  date_range="2024-01-01 to 2024-01-31"
)

***REMOVED*** Step 3: Validate schedule
Output3 = CONSTRAINT_ANALYSIS(
  schedule=Output2,
  rules=Output1.compliance_requirements
)
```

***REMOVED******REMOVED******REMOVED*** Pattern 2: Parallel Composition

Run multiple templates concurrently, then synthesize:

```bash
***REMOVED*** Parallel execution
[ParallelStart]
  Output_A = RESEARCH_POLICY(policy="Night Float Guidelines")
  Output_B = RESEARCH_POLICY(policy="Call Duty Limits")
  Output_C = RESEARCH_POLICY(policy="Vacation Policies")
[ParallelEnd]

***REMOVED*** Synthesis
FinalOutput = SCHEDULE_GENERATION(
  constraints=[Output_A, Output_B, Output_C]
)
```

***REMOVED******REMOVED******REMOVED*** Pattern 3: Conditional Branching

Choose template based on input conditions:

```bash
IF swap_request.type == "emergency":
  Process using SWAP_REQUEST(priority="urgent")
ELIF swap_request.involves_call:
  Process using SWAP_REQUEST(safety_level="high")
ELSE:
  Process using SWAP_REQUEST(priority="standard")
ENDIF
```

***REMOVED******REMOVED******REMOVED*** Pattern 4: Nested Templates

Embed one template inside another:

```markdown
<!-- INCIDENT_REVIEW.md (outer) -->
***REMOVED******REMOVED*** Root Cause Analysis

[EMBED CONSTRAINT_ANALYSIS(
  constraints=incident.violated_rules,
  context=incident.timeline
)]

***REMOVED******REMOVED*** Prevention Measures

[EMBED SCHEDULE_GENERATION(
  constraints=incident.lessons_learned,
  mode="preview_only"
)]
```

***REMOVED******REMOVED******REMOVED*** Pattern 5: Template Inheritance

Create specialized templates from generic base:

```
BASE: RESEARCH_POLICY.md
  ├─ RESEARCH_ACGME_RULE.md (adds regulatory framing)
  ├─ RESEARCH_INSTITUTIONAL_POLICY.md (adds local context)
  └─ RESEARCH_CLINICAL_GUIDELINE.md (adds medical evidence)
```

---

***REMOVED******REMOVED*** Available Templates

***REMOVED******REMOVED******REMOVED*** Core Templates

| Template | Complexity | Typical Duration | Output Format |
|----------|------------|------------------|---------------|
| `RESEARCH_POLICY.md` | Medium | 5-15 min | Structured summary |
| `SCHEDULE_GENERATION.md` | High | 10-30 min | Schedule + rationale |
| `INCIDENT_REVIEW.md` | Medium | 10-20 min | Post-mortem report |
| `CONSTRAINT_ANALYSIS.md` | Medium | 5-15 min | Constraint matrix |
| `SWAP_REQUEST.md` | Low | 2-5 min | Approval/denial + reasoning |

***REMOVED******REMOVED******REMOVED*** Template Dependencies

```
RESEARCH_POLICY (independent)
    ↓
SCHEDULE_GENERATION (may use research output)
    ↓
CONSTRAINT_ANALYSIS (analyzes generated schedule)
    ↓
INCIDENT_REVIEW (uses analysis for root cause)

SWAP_REQUEST (independent, but may trigger CONSTRAINT_ANALYSIS)
```

---

***REMOVED******REMOVED*** Creating New Templates

***REMOVED******REMOVED******REMOVED*** Template Structure

Every template should have:

1. **Header Block**: Purpose, inputs, outputs, prerequisites
2. **Variable Section**: List all `{{placeholders}}` with descriptions
3. **Instructions Section**: Step-by-step execution guide
4. **Output Format Section**: Expected structure of results
5. **Examples Section**: At least 2 instantiation examples
6. **Validation Checklist**: Quality gates before submission

***REMOVED******REMOVED******REMOVED*** Template Creation Workflow

```bash
***REMOVED*** 1. Identify need
"I've done this task 3+ times with similar structure"

***REMOVED*** 2. Extract commonalities
cat previous_prompts/*.md | analyze_common_structure

***REMOVED*** 3. Draft template
cp TEMPLATE_SKELETON.md NEW_TEMPLATE.md

***REMOVED*** 4. Add variables
***REMOVED*** Replace specific values with {{placeholders}}

***REMOVED*** 5. Test instantiation
***REMOVED*** Try 3 different scenarios to verify generality

***REMOVED*** 6. Document
***REMOVED*** Add to README.md Available Templates section

***REMOVED*** 7. Commit
git add .claude/PromptTemplates/NEW_TEMPLATE.md
git commit -m "feat: Add NEW_TEMPLATE prompt template"
```

***REMOVED******REMOVED******REMOVED*** Template Skeleton

```markdown
***REMOVED*** {{TEMPLATE_NAME}} - Prompt Template

> **Purpose:** [One sentence describing what this template does]
> **Complexity:** [Low/Medium/High]
> **Typical Duration:** [Estimated time to complete]
> **Prerequisites:** [Required context, data, or prior templates]

---

***REMOVED******REMOVED*** Input Parameters

***REMOVED******REMOVED******REMOVED*** Required

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `{{param1}}` | String | [Description] | `"example"` |
| `{{param2}}` | Date | [Description] | `2024-01-01` |

***REMOVED******REMOVED******REMOVED*** Optional

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `{{param3}}` | Boolean | `false` | [Description] |

---

***REMOVED******REMOVED*** Template

[TEMPLATE CONTENT GOES HERE]

---

***REMOVED******REMOVED*** Output Format

[EXPECTED OUTPUT STRUCTURE]

---

***REMOVED******REMOVED*** Examples

***REMOVED******REMOVED******REMOVED*** Example 1: [Scenario Name]

**Instantiation:**
[Filled template]

**Output:**
[Expected result]

---

***REMOVED******REMOVED*** Validation Checklist

- [ ] All required parameters provided
- [ ] Output format matches specification
- [ ] [Domain-specific checks]
```

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** 1. Variable Naming

**Good:**
- `{{resident_name}}` (specific, clear)
- `{{constraint_type}}` (unambiguous)
- `{{start_date}}` (formatted consistently)

**Bad:**
- `{{name}}` (too generic)
- `{{x}}` (not descriptive)
- `{{date}}` (ambiguous - start? end?)

***REMOVED******REMOVED******REMOVED*** 2. Documentation

- Always include at least 2 examples (simple + complex)
- Document edge cases in comments
- Link to related templates
- Specify expected input formats

***REMOVED******REMOVED******REMOVED*** 3. Error Handling

```markdown
***REMOVED******REMOVED*** Pre-Execution Checks

[IF NOT {{required_param}}]
❌ ERROR: Missing required parameter `{{required_param}}`
STOP: Cannot proceed without this value.
[ENDIF]

[IF {{date_range}} NOT VALID]
⚠️ WARNING: Date range appears invalid.
Proceeding with interpretation: {{interpreted_range}}
[ENDIF]
```

***REMOVED******REMOVED******REMOVED*** 4. Version Control

- Include version number and last updated date
- Document breaking changes in template header
- Use semantic versioning for major templates

***REMOVED******REMOVED******REMOVED*** 5. Testing

Before committing a new template:

```bash
***REMOVED*** Test with minimal valid input
***REMOVED*** Test with full optional parameters
***REMOVED*** Test with edge cases (empty lists, far-future dates, etc.)
***REMOVED*** Test with invalid input (should fail gracefully)
```

***REMOVED******REMOVED******REMOVED*** 6. Composition Guidelines

When combining templates:
- Validate intermediate outputs before passing to next template
- Document the composition pattern used
- Consider creating a "workflow template" for common sequences

---

***REMOVED******REMOVED*** Maintenance

***REMOVED******REMOVED******REMOVED*** Regular Reviews

- **Quarterly**: Review usage metrics (which templates are used most?)
- **Bi-annually**: Update examples with current data
- **After major incidents**: Check if new template patterns are needed

***REMOVED******REMOVED******REMOVED*** Deprecation Process

1. Mark template as `[DEPRECATED]` in header
2. Provide migration path to replacement
3. Keep deprecated template for 6 months
4. Archive to `.claude/PromptTemplates/archive/`

---

***REMOVED******REMOVED*** Integration with PAI

***REMOVED******REMOVED******REMOVED*** Hooks Integration

Templates can be invoked from `.claude/Hooks/`:

```yaml
***REMOVED*** .claude/Hooks/on_swap_request.yaml
trigger: swap_request_received
action:
  template: .claude/PromptTemplates/SWAP_REQUEST.md
  params:
    requester: ${event.requester_id}
    target_date: ${event.date}
```

***REMOVED******REMOVED******REMOVED*** Agent Integration

Agents (in `.claude/Agents/`) can use templates as sub-tasks:

```python
***REMOVED*** .claude/Agents/scheduler_agent.py
def handle_policy_question(policy_name: str):
    template = load_template("RESEARCH_POLICY.md")
    prompt = template.instantiate(
        policy_name=policy_name,
        search_terms=generate_search_terms(policy_name)
    )
    return execute_prompt(prompt)
```

***REMOVED******REMOVED******REMOVED*** History Logging

All template instantiations are logged to `.claude/History/PromptTemplates/`:

```
.claude/History/PromptTemplates/
├── 2024-01-15_RESEARCH_POLICY_acgme_2023.md
├── 2024-01-16_SCHEDULE_GENERATION_jan_2024.md
└── 2024-01-20_INCIDENT_REVIEW_double_booking.md
```

---

***REMOVED******REMOVED*** Resources

- **Template Gallery**: See all templates in this directory
- **Composition Cookbook**: `docs/guides/TEMPLATE_COMPOSITION_PATTERNS.md`
- **PAI Overview**: `.claude/INFRASTRUCTURE_OVERVIEW.md`
- **Agent Integration**: `.claude/Agents/README.md`

---

***REMOVED******REMOVED*** Quick Reference

***REMOVED******REMOVED******REMOVED*** Common Template Invocations

```bash
***REMOVED*** Research ACGME policy
Use RESEARCH_POLICY with policy_name="ACGME 2023 CPR"

***REMOVED*** Generate January schedule
Use SCHEDULE_GENERATION with date_range="2024-01-01 to 2024-01-31"

***REMOVED*** Review incident
Use INCIDENT_REVIEW with incident_id="INC-2024-001"

***REMOVED*** Analyze constraint conflict
Use CONSTRAINT_ANALYSIS with constraints=["80hr rule", "call coverage"]

***REMOVED*** Process swap
Use SWAP_REQUEST with requester="FAC-01", target_date="2024-02-14"
```

---

**Remember:** Templates are tools, not straightjackets. Adapt them when needed, but maintain the core structure for consistency.
