# AGENT_FACTORY - Dynamic Multi-Agent Composition

> **Purpose:** Dynamic agent creation, composition, and orchestration patterns
> **Version:** 1.0.0
> **Last Updated:** 2025-12-26
> **Status:** Active
> **Model Tier:** opus

---

## I. OVERVIEW

The AGENT_FACTORY provides a framework for dynamically creating, composing, and orchestrating multiple AI agents to solve complex problems through parallel execution and result synthesis.

**Core Capabilities:**
- **Agent Templates**: Pre-defined personality + expertise archetypes
- **Dynamic Spawning**: Create temporary agents with focused tasks
- **Parallel Execution**: Run multiple agents simultaneously
- **Result Synthesis**: Combine outputs using intelligent merge strategies
- **Lifecycle Management**: Spawn, execute, merge, terminate

**Philosophy:** "Many specialized experts working in parallel produce better outcomes than a single generalist working sequentially."

---

## II. AGENT COMPOSITION MODEL

### A. Agent Template Structure

```yaml
agent_template:
  # Identity
  name: string                    # e.g., "schedule_validator_01"
  archetype: string              # e.g., "Validator", "Generator", "Critic"

  # Personality Configuration
  personality:
    - thorough                   # Checks all edge cases
    - analytical                 # Data-driven decisions
    - conservative              # Prefers safe, proven approaches
    - creative                  # Proposes novel solutions
    - adversarial              # Actively seeks problems

  # Expertise & Scope
  expertise: string              # e.g., "scheduling", "resilience", "security"
  domain_knowledge:
    - ACGME_compliance          # Regulatory expertise
    - constraint_programming    # Technical expertise
    - medical_workflow         # Domain expertise

  # Approach & Methods
  approach: string               # e.g., "constraint-propagation", "adversarial-testing"
  methodologies:
    - systematic_exploration    # Methodical approach
    - defensive_depth          # Security-focused
    - rapid_iteration          # Fast feedback cycles

  # Access Control
  skills_access:
    - SCHEDULING                # Full access skills
    - COMPLIANCE_VALIDATION
  tools_access:
    - generate_schedule         # MCP tools
    - validate_acgme
  read_only_skills:
    - code-review               # Read-only access
    - test-writer

  # Behavioral Parameters
  risk_tolerance: low | medium | high
  autonomy_level: supervised | semi-autonomous | autonomous

  # Task Configuration
  max_duration: "30m"            # Timeout for agent execution
  context_limit: 100000          # Token budget
  output_format: "structured"    # or "narrative", "code", "analysis"

  # Coordination
  merge_strategy: "consensus" | "union" | "priority" | "synthesis"
  conflict_resolution: "escalate" | "majority" | "expert_priority"
```

### B. Template Instantiation

```python
# Python pseudocode for agent creation
def create_agent(template: AgentTemplate, task: Task) -> Agent:
    """Instantiate an agent from a template with a specific task."""

    agent = Agent(
        id=generate_unique_id(),
        name=f"{template.archetype}_{task.domain}_{uuid.short()}",
        template=template,
        task=task,
        created_at=datetime.now(),
        context=build_context(template, task)
    )

    # Load personality traits
    agent.set_personality(template.personality)

    # Grant access to skills and tools
    agent.grant_skills(template.skills_access)
    agent.grant_tools(template.tools_access)

    # Set behavioral parameters
    agent.set_risk_tolerance(template.risk_tolerance)
    agent.set_autonomy_level(template.autonomy_level)

    # Configure task-specific parameters
    agent.set_timeout(template.max_duration)
    agent.set_output_format(template.output_format)

    return agent
```

---

## III. NAMED AGENT ARCHETYPES

### Archetype 1: Researcher

**Purpose:** Explore, investigate, synthesize findings (read-only)

```yaml
researcher_template:
  archetype: Researcher
  personality: [curious, thorough, synthesizing, patient]
  expertise: varies_by_domain
  approach: systematic_exploration

  skills_access: []  # No write access
  read_only_skills: [all_skills]  # Read-only access to all
  tools_access: [read_only_tools]

  risk_tolerance: low
  autonomy_level: autonomous

  typical_tasks:
    - "Analyze codebase for performance bottlenecks"
    - "Investigate root cause of scheduling conflict"
    - "Survey constraint implementation patterns"
    - "Map dependencies between modules"

  output_format: structured_report

  success_criteria:
    - Comprehensive coverage (explores all relevant areas)
    - Identifies patterns and trends
    - Provides actionable insights
    - Cites evidence for conclusions
```

**Example Usage:**
```markdown
**Task:** "Research why schedule generation slowed down this week"

**Spawn 3 Researchers in Parallel:**
- Researcher_1: Investigate solver performance metrics
- Researcher_2: Analyze database query logs
- Researcher_3: Review recent code changes

**Merge Strategy:** Synthesis (combine findings into coherent narrative)

**Expected Output:**
- Root cause: Database index missing after migration
- Contributing factors: Increased data volume, inefficient query
- Evidence: Query time increased 10x, specific slow queries identified
- Recommendation: Add index, optimize query
```

---

### Archetype 2: Validator

**Purpose:** Verify correctness, check constraints, ensure compliance

```yaml
validator_template:
  archetype: Validator
  personality: [thorough, meticulous, conservative, rule-focused]
  expertise: varies_by_domain
  approach: exhaustive_verification

  skills_access:
    - COMPLIANCE_VALIDATION
    - acgme-compliance
  tools_access:
    - validate_acgme
    - check_constraints

  risk_tolerance: low
  autonomy_level: supervised

  typical_tasks:
    - "Validate generated schedule for ACGME compliance"
    - "Check swap request for constraint violations"
    - "Verify N-1 contingency coverage"
    - "Audit credential requirements for all assignments"

  output_format: structured

  validation_levels:
    - tier_1: regulatory_compliance    # MUST PASS
    - tier_2: institutional_policy     # SHOULD PASS
    - tier_3: optimization_preferences # NICE TO PASS

  success_criteria:
    - Zero false negatives (catch all violations)
    - Low false positives (< 5%)
    - Clear violation reports (actionable)
    - Performance (< 3s for full schedule)
```

**Example Usage:**
```markdown
**Task:** "Validate proposed swap for ACGME compliance"

**Spawn 3 Validators in Parallel:**
- Validator_1: Check 80-hour rule (4-week rolling window)
- Validator_2: Check 1-in-7 day off requirement
- Validator_3: Check supervision ratios

**Merge Strategy:** Union (all violations from all validators)

**Expected Output:**
- Tier 1 violations: 0 (ACGME compliant)
- Tier 2 warnings: 1 (PGY1-02 approaches 75-hour soft limit)
- Recommendation: Approve swap with advisory
```

---

### Archetype 3: Generator

**Purpose:** Create solutions, propose implementations, generate code/schedules

```yaml
generator_template:
  archetype: Generator
  personality: [creative, solution-oriented, pragmatic, iterative]
  expertise: varies_by_domain
  approach: constraint-satisfying_generation

  skills_access:
    - SCHEDULING
    - schedule-optimization
    - code-generation
  tools_access:
    - generate_schedule
    - optimize_assignments

  risk_tolerance: medium
  autonomy_level: semi-autonomous

  typical_tasks:
    - "Generate Block 10 schedule"
    - "Create 5 alternative swap proposals"
    - "Propose optimization strategies"
    - "Implement constraint logic"

  output_format: code | schedule | proposal

  generation_strategy:
    - Start with feasible solution (hard constraints)
    - Iteratively improve (soft constraints)
    - Generate alternatives (diversity)
    - Rank by quality metrics

  success_criteria:
    - Satisfies all hard constraints
    - Optimizes soft constraints (> 60% satisfaction)
    - Generates multiple options (3-5 alternatives)
    - Explainable (documents rationale)
```

**Example Usage:**
```markdown
**Task:** "Generate 3 alternative schedules for Block 10"

**Spawn 3 Generators in Parallel:**
- Generator_1: Optimize for fairness (minimize call variance)
- Generator_2: Optimize for preferences (maximize satisfaction)
- Generator_3: Optimize for continuity (minimize rotation changes)

**Merge Strategy:** Competitive (present all 3, let faculty choose)

**Expected Output:**
- Schedule_1: Fairness score 0.95, preference score 0.65
- Schedule_2: Fairness score 0.80, preference score 0.85
- Schedule_3: Fairness score 0.88, preference score 0.75
- Recommendation: Schedule_2 (best overall balance)
```

---

### Archetype 4: Critic

**Purpose:** Find flaws, test edge cases, adversarial analysis

```yaml
critic_template:
  archetype: Critic
  personality: [adversarial, skeptical, thorough, edge-case-focused]
  expertise: varies_by_domain
  approach: adversarial_testing

  skills_access:
    - systematic-debugger
    - test-scenario-framework
  tools_access:
    - stress_test
    - edge_case_generator

  risk_tolerance: high  # Tests risky scenarios
  autonomy_level: autonomous

  typical_tasks:
    - "Find edge cases that break schedule generation"
    - "Stress-test N-1 contingency"
    - "Identify security vulnerabilities"
    - "Challenge assumptions in implementation"

  output_format: bug_report | vulnerability_report

  adversarial_strategies:
    - Boundary testing (min/max values)
    - Concurrent operations (race conditions)
    - Failure injection (what if X fails?)
    - Assumption violation (what if rule Y doesn't hold?)

  success_criteria:
    - Discovers edge cases (bugs before production)
    - Clear reproduction steps
    - Severity classification (P0-P4)
    - Suggested fixes (not just complaints)
```

**Example Usage:**
```markdown
**Task:** "Stress-test N-1 contingency for all critical roles"

**Spawn 5 Critics in Parallel:**
- Critic_1: Test N-1 failure for Chief Resident
- Critic_2: Test N-1 failure for Senior Faculty
- Critic_3: Test N-2 failure (Chief + Senior)
- Critic_4: Test concurrent failures (cascading)
- Critic_5: Test failure during peak utilization

**Merge Strategy:** Union (all bugs from all critics)

**Expected Output:**
- Critical bugs: 2 (cascade failure, peak utilization failure)
- Medium bugs: 3 (suboptimal coverage, slow recovery)
- Low priority: 5 (cosmetic, non-critical)
- Recommendations: Fix critical bugs before production
```

---

### Archetype 5: Synthesizer

**Purpose:** Combine multiple agent outputs, resolve conflicts, create unified view

```yaml
synthesizer_template:
  archetype: Synthesizer
  personality: [integrative, diplomatic, clear-communicating, decision-making]
  expertise: meta_analysis
  approach: multi-perspective_integration

  skills_access: []  # Doesn't execute, only synthesizes
  read_only_skills: [all_skills]
  tools_access: []

  risk_tolerance: low
  autonomy_level: autonomous

  typical_tasks:
    - "Synthesize findings from 5 researchers"
    - "Resolve conflicting recommendations"
    - "Create executive summary from detailed reports"
    - "Combine partial solutions into complete solution"

  output_format: narrative | executive_summary

  synthesis_strategies:
    - Identify common themes across reports
    - Highlight unique insights from each agent
    - Resolve contradictions with evidence
    - Prioritize recommendations by impact
    - Create coherent narrative flow

  success_criteria:
    - Preserves key insights from all agents
    - Resolves conflicts with rationale
    - Actionable (clear next steps)
    - Concise (1-2 pages max for executive summary)
```

**Example Usage:**
```markdown
**Task:** "Synthesize root cause analysis from multiple agents"

**Input:** Reports from 5 parallel investigators

**Synthesis Process:**
1. Extract key findings from each report
2. Identify patterns (3 agents mentioned database)
3. Resolve conflicts (Agent_1 says CPU, Agent_2 says memory)
4. Build causal chain (database slow → CPU high → timeout)
5. Prioritize recommendations (fix database first)

**Expected Output:**
- Executive Summary (1 page)
- Root Cause: Database index missing
- Contributing Factors: High CPU, memory pressure
- Recommendations (prioritized):
  1. Add index (immediate, high impact)
  2. Increase memory (short-term, medium impact)
  3. Optimize queries (long-term, high impact)
```

---

## IV. DYNAMIC AGENT SPAWNING

### A. Spawning Patterns

#### Pattern 1: Homogeneous Parallel (Same Task, Different Data)

```python
# Spawn 5 parallel stress-test analysts
def spawn_homogeneous_agents(
    template: str,
    count: int,
    task_generator: Callable[[int], Task]
) -> list[Agent]:
    """Spawn multiple agents with same template but different tasks."""

    agents = []
    for i in range(count):
        task = task_generator(i)
        agent = create_agent(
            template=get_template(template),
            task=task
        )
        agents.append(agent)

    return agents

# Example: Test N-1 failure for each critical role
residents = ["Alice", "Bob", "Carol", "Dave", "Eve"]
critics = spawn_homogeneous_agents(
    template="critic",
    count=5,
    task_generator=lambda i: Task(
        type="n1_failure_test",
        target=residents[i],
        duration="15m"
    )
)
```

#### Pattern 2: Heterogeneous Parallel (Different Templates, Related Tasks)

```python
def spawn_heterogeneous_agents(
    tasks: list[tuple[str, Task]]
) -> list[Agent]:
    """Spawn agents with different templates for complementary tasks."""

    agents = []
    for template_name, task in tasks:
        agent = create_agent(
            template=get_template(template_name),
            task=task
        )
        agents.append(agent)

    return agents

# Example: Multi-perspective analysis
agents = spawn_heterogeneous_agents([
    ("researcher", Task("investigate_slowdown", domain="solver")),
    ("researcher", Task("investigate_slowdown", domain="database")),
    ("critic", Task("stress_test", scenario="high_load")),
    ("validator", Task("check_compliance", scope="current_schedule"))
])
```

#### Pattern 3: Pipeline (Sequential with Handoffs)

```python
def spawn_pipeline(stages: list[tuple[str, Task]]) -> Pipeline:
    """Create sequential pipeline with handoffs between stages."""

    pipeline = Pipeline()

    for i, (template_name, task) in enumerate(stages):
        agent = create_agent(
            template=get_template(template_name),
            task=task
        )

        # Configure input from previous stage
        if i > 0:
            agent.set_input_source(pipeline.stages[i-1].output)

        pipeline.add_stage(agent)

    return pipeline

# Example: Design → Implement → Test
pipeline = spawn_pipeline([
    ("researcher", Task("design_validation_logic")),
    ("generator", Task("implement_validation_logic")),
    ("validator", Task("test_validation_logic")),
    ("critic", Task("adversarial_test_validation_logic"))
])
```

### B. Task Distribution Strategies

#### Strategy 1: Divide by Component

```python
# Audit all scheduling code
components = [
    "schedule_service.py",
    "swap_service.py",
    "acgme_validator.py",
    "scheduling_engine.py",
    "constraint_propagation.py"
]

agents = [
    create_agent("critic", Task("audit_component", file=component))
    for component in components
]
```

#### Strategy 2: Divide by Perspective

```python
# Evaluate feature proposal from multiple angles
perspectives = [
    ("architecture", "ARCHITECT"),
    ("resilience", "RESILIENCE_ENGINEER"),
    ("testing", "QA_TESTER"),
    ("security", "SECURITY_AUDITOR")
]

agents = [
    create_agent("researcher", Task(f"evaluate_feature_{domain}", perspective=domain))
    for domain, role in perspectives
]
```

#### Strategy 3: Divide by Scenario

```python
# Test swap validation under different conditions
scenarios = [
    "normal_conditions",
    "high_utilization",
    "near_80hr_limit",
    "cascading_swaps",
    "last_minute_swap"
]

agents = [
    create_agent("validator", Task("test_swap_validation", scenario=scenario))
    for scenario in scenarios
]
```

---

## V. MERGE STRATEGIES

### Strategy 1: Consensus (Majority Vote)

**Use When:** Need agreement across multiple agents

```python
def merge_consensus(results: list[AgentResult]) -> MergedResult:
    """Combine results using majority vote."""

    findings = defaultdict(int)

    # Count votes for each finding
    for result in results:
        for finding in result.findings:
            findings[finding] += 1

    # Keep findings supported by majority
    threshold = len(results) / 2
    consensus = [
        finding for finding, count in findings.items()
        if count > threshold
    ]

    return MergedResult(
        strategy="consensus",
        findings=consensus,
        agreement_rate=calculate_agreement(results)
    )
```

**Example:**
```markdown
5 agents analyze code, 3 say "performance issue in query", 2 say "no issue"
→ Consensus: "performance issue in query" (60% agreement)
```

---

### Strategy 2: Union (Combine All Findings)

**Use When:** Want comprehensive coverage, false positives acceptable

```python
def merge_union(results: list[AgentResult]) -> MergedResult:
    """Combine all findings from all agents."""

    all_findings = []

    for result in results:
        all_findings.extend(result.findings)

    # Deduplicate
    unique_findings = deduplicate(all_findings)

    return MergedResult(
        strategy="union",
        findings=unique_findings,
        source_count=len(results)
    )
```

**Example:**
```markdown
3 validators find different violations:
- Validator_1: 80-hour violation for PGY1-01
- Validator_2: 1-in-7 violation for PGY2-03
- Validator_3: Supervision ratio violation in Peds

→ Union: All 3 violations reported (comprehensive)
```

---

### Strategy 3: Priority (Weighted by Expertise)

**Use When:** Agents have different expertise levels

```python
def merge_priority(
    results: list[AgentResult],
    weights: dict[str, float]
) -> MergedResult:
    """Prioritize findings based on agent expertise."""

    weighted_findings = []

    for result in results:
        agent_weight = weights.get(result.agent_id, 1.0)

        for finding in result.findings:
            weighted_findings.append({
                "finding": finding,
                "weight": agent_weight,
                "source": result.agent_id
            })

    # Sort by weight, keep top findings
    sorted_findings = sorted(
        weighted_findings,
        key=lambda x: x["weight"],
        reverse=True
    )

    return MergedResult(
        strategy="priority",
        findings=[f["finding"] for f in sorted_findings[:10]],
        weights_applied=True
    )
```

**Example:**
```markdown
Weights: ARCHITECT=2.0, SCHEDULER=1.5, QA_TESTER=1.0

Findings:
- ARCHITECT: "Architectural flaw in swap logic" (weight 2.0)
- SCHEDULER: "Inefficient algorithm" (weight 1.5)
- QA_TESTER: "Missing test case" (weight 1.0)

→ Priority: Architectural flaw addressed first
```

---

### Strategy 4: Synthesis (Meta-Agent Creates Coherent Narrative)

**Use When:** Need integrated understanding, not just list of findings

```python
def merge_synthesis(results: list[AgentResult]) -> MergedResult:
    """Use synthesizer agent to create coherent output."""

    # Spawn synthesizer agent
    synthesizer = create_agent(
        template="synthesizer",
        task=Task("synthesize_findings", input=results)
    )

    # Synthesizer analyzes all results and creates narrative
    synthesis = synthesizer.execute()

    return MergedResult(
        strategy="synthesis",
        narrative=synthesis.narrative,
        key_findings=synthesis.key_findings,
        recommendations=synthesis.recommendations,
        agent_count=len(results)
    )
```

**Example:**
```markdown
Input: 5 detailed investigation reports (50 pages total)

Synthesizer Output:
- Executive Summary (1 page)
- Root Cause: Database index missing after migration
- Contributing Factors:
  1. Increased data volume (Researcher_1)
  2. Inefficient query (Researcher_2)
  3. High CPU contention (Researcher_3)
- Recommendations (prioritized):
  1. Add index (immediate, high impact)
  2. Optimize query (short-term, medium impact)
  3. Scale database (long-term, high impact)
```

---

## VI. AGENT LIFECYCLE

### Phase 1: Creation

```python
def create_agent(template: str, task: Task) -> Agent:
    """Create and initialize agent."""

    # 1. Load template
    template_config = load_template(template)

    # 2. Instantiate agent
    agent = Agent(
        id=generate_id(),
        template=template_config,
        task=task
    )

    # 3. Grant permissions
    agent.grant_skills(template_config.skills_access)
    agent.grant_tools(template_config.tools_access)

    # 4. Set behavioral parameters
    agent.set_personality(template_config.personality)
    agent.set_risk_tolerance(template_config.risk_tolerance)

    # 5. Allocate resources
    agent.set_timeout(template_config.max_duration)
    agent.set_context_limit(template_config.context_limit)

    # 6. Log creation
    log_agent_created(agent)

    return agent
```

---

### Phase 2: Execution

```python
def execute_agents_parallel(agents: list[Agent]) -> list[AgentResult]:
    """Execute multiple agents in parallel with resource limits."""

    results = []

    with ThreadPoolExecutor(max_workers=len(agents)) as executor:
        futures = {
            executor.submit(execute_agent, agent): agent
            for agent in agents
        }

        for future in as_completed(futures):
            agent = futures[future]

            try:
                result = future.result(timeout=agent.max_duration)
                results.append(result)
                log_agent_completed(agent, result)

            except TimeoutError:
                log_agent_timeout(agent)
                results.append(AgentResult.timeout(agent))

            except Exception as e:
                log_agent_error(agent, e)
                results.append(AgentResult.error(agent, e))

    return results

def execute_agent(agent: Agent) -> AgentResult:
    """Execute single agent with monitoring."""

    # 1. Validate prerequisites
    if not agent.can_execute():
        raise AgentError("Prerequisites not met")

    # 2. Build context
    context = build_agent_context(agent)

    # 3. Execute task
    start_time = time.time()
    output = agent.run(context)
    duration = time.time() - start_time

    # 4. Validate output
    validate_agent_output(output, agent.output_format)

    # 5. Create result
    return AgentResult(
        agent_id=agent.id,
        status="success",
        output=output,
        duration=duration,
        metrics=agent.get_metrics()
    )
```

---

### Phase 3: Merge

```python
def merge_results(
    results: list[AgentResult],
    strategy: str = "synthesis"
) -> MergedResult:
    """Merge results using specified strategy."""

    # Filter out failed results
    successful = [r for r in results if r.status == "success"]

    if len(successful) == 0:
        return MergedResult.all_failed(results)

    # Select merge strategy
    if strategy == "consensus":
        return merge_consensus(successful)
    elif strategy == "union":
        return merge_union(successful)
    elif strategy == "priority":
        return merge_priority(successful, weights=get_agent_weights())
    elif strategy == "synthesis":
        return merge_synthesis(successful)
    else:
        raise ValueError(f"Unknown merge strategy: {strategy}")
```

---

### Phase 4: Termination

```python
def terminate_agents(agents: list[Agent]) -> None:
    """Clean up agent resources."""

    for agent in agents:
        # 1. Save results
        save_agent_results(agent)

        # 2. Release resources
        agent.release_skills()
        agent.release_tools()
        agent.clear_context()

        # 3. Log termination
        log_agent_terminated(agent)

        # 4. Archive for audit
        archive_agent_session(agent)
```

---

## VII. COMPOSITION EXAMPLES

### Example 1: Schedule Generation (Researcher → Generator → Validator)

**Scenario:** Generate new Block 10 schedule

```python
# Phase 1: Research constraints
researcher = create_agent("researcher", Task(
    type="analyze_constraints",
    scope="block_10",
    output="constraint_list"
))
constraints = researcher.execute()

# Phase 2: Generate schedule (3 alternatives)
generators = [
    create_agent("generator", Task(
        type="generate_schedule",
        constraints=constraints,
        optimization_goal=goal
    ))
    for goal in ["fairness", "preferences", "continuity"]
]
schedules = execute_agents_parallel(generators)

# Phase 3: Validate all schedules
validators = [
    create_agent("validator", Task(
        type="validate_schedule",
        schedule=schedule,
        tier=1  # ACGME only
    ))
    for schedule in schedules
]
validations = execute_agents_parallel(validators)

# Phase 4: Synthesize recommendation
synthesizer = create_agent("synthesizer", Task(
    type="recommend_schedule",
    schedules=schedules,
    validations=validations
))
recommendation = synthesizer.execute()
```

**Output:**
```markdown
## Block 10 Schedule Recommendation

**Schedules Generated:** 3
- Schedule_1 (fairness-optimized): 0.95 fairness, 0.65 preference
- Schedule_2 (preference-optimized): 0.80 fairness, 0.85 preference
- Schedule_3 (continuity-optimized): 0.88 fairness, 0.75 preference

**Validation Results:** All ACGME compliant

**Recommendation:** Schedule_2 (preference-optimized)
- Rationale: Best balance of fairness and satisfaction
- Trade-off: Slightly lower fairness (still > 0.8)
- Approval: Recommended for faculty review
```

---

### Example 2: Swap Validation (3× Validator + Synthesizer)

**Scenario:** Validate complex multi-party swap

```python
# Spawn 3 validators with different foci
validators = spawn_heterogeneous_agents([
    ("validator", Task("validate_acgme", swap=swap_request)),
    ("validator", Task("validate_credentials", swap=swap_request)),
    ("validator", Task("validate_coverage", swap=swap_request))
])

# Execute in parallel
results = execute_agents_parallel(validators)

# Merge using UNION (all violations matter)
merged = merge_results(results, strategy="union")

# If violations found, synthesize report
if merged.has_violations():
    synthesizer = create_agent("synthesizer", Task(
        type="explain_violations",
        validations=results
    ))
    report = synthesizer.execute()
else:
    report = "All validations passed, swap approved"
```

**Output:**
```markdown
## Swap Validation Report

**Status:** REJECTED

**Violations:**
1. ACGME Tier 1 (CRITICAL):
   - PGY1-02 would exceed 80-hour limit (projected: 84 hours)
   - Violation source: Validator_1 (ACGME check)

2. Coverage Warning:
   - Peds clinic coverage drops below minimum (2 → 1 resident)
   - Violation source: Validator_3 (coverage check)

**Recommendation:** Reject swap, suggest alternative:
- Find different partner for PGY1-02 (under 75 hours)
- OR delay swap by 1 week (after PGY1-02's call weekend)
```

---

### Example 3: Resilience Analysis (5× Critic + Synthesizer)

**Scenario:** Test N-1 contingency for all critical roles

```python
# Identify critical roles
critical_roles = [
    "Chief_Resident",
    "Senior_Faculty",
    "Procedures_Lead",
    "Night_Float_Coord",
    "Peds_Supervisor"
]

# Spawn critics to test each N-1 failure
critics = [
    create_agent("critic", Task(
        type="n1_failure_simulation",
        role=role,
        duration="7_days"
    ))
    for role in critical_roles
]

# Execute stress tests in parallel
results = execute_agents_parallel(critics)

# Synthesize into resilience report
synthesizer = create_agent("synthesizer", Task(
    type="resilience_report",
    simulations=results,
    threshold="tier_2"  # Must pass N-1
))
report = synthesizer.execute()
```

**Output:**
```markdown
## N-1 Contingency Analysis

**Simulations Run:** 5
**Threshold:** Tier 2 (system must function with 1 unavailable)

**Results:**

✅ PASS: Chief_Resident (backup chain works)
✅ PASS: Senior_Faculty (coverage redistributed)
✅ PASS: Procedures_Lead (qualified alternatives exist)
❌ FAIL: Night_Float_Coord (no qualified backup)
⚠️  WARNING: Peds_Supervisor (backup exists but stressed)

**Critical Finding:**
Night Float Coordinator has no qualified backup. If unavailable:
- Night coverage drops below minimum
- Requires emergency faculty activation
- Violates Tier 2 resilience requirement

**Recommendations:**
1. URGENT: Cross-train 2 residents for Night Float Coord
2. HIGH: Add qualified backup to Peds Supervisor role
3. MEDIUM: Document escalation procedures for N-1 failures
```

---

### Example 4: Feature Implementation (ARCHITECT + SCHEDULER + QA_TESTER)

**Scenario:** Implement swap auto-cancellation feature

```python
# Phase 1: Design (parallel architecture + test design)
designers = spawn_heterogeneous_agents([
    ("researcher", Task("design_swap_autocancellation", role="ARCHITECT")),
    ("researcher", Task("design_test_cases", role="QA_TESTER"))
])
designs = execute_agents_parallel(designers)

# Phase 2: Implementation (sequential, needs design)
generator = create_agent("generator", Task(
    type="implement_feature",
    design=designs[0],  # ARCHITECT design
    constraints=designs[1]  # Test cases
))
implementation = generator.execute()

# Phase 3: Testing (parallel unit + integration)
testers = spawn_heterogeneous_agents([
    ("validator", Task("run_unit_tests", code=implementation)),
    ("critic", Task("adversarial_test", code=implementation))
])
test_results = execute_agents_parallel(testers)

# Phase 4: Synthesis (decision: merge or iterate)
synthesizer = create_agent("synthesizer", Task(
    type="review_feature",
    implementation=implementation,
    tests=test_results
))
review = synthesizer.execute()
```

**Output:**
```markdown
## Feature Review: Swap Auto-Cancellation

**Design Quality:** ✅ Excellent (ARCHITECT approved)
**Implementation:** ✅ Complete, follows design
**Unit Tests:** ✅ All pass (18/18)
**Adversarial Tests:** ⚠️  2 edge cases found

**Edge Cases:**
1. Race condition: Concurrent swaps + cancellation
2. Cascade: Cancelling swap A triggers cancellation of swap B

**Recommendation:** Fix edge cases before merge
**Estimated Time:** 1-2 hours
**Approval:** Hold pending fixes
```

---

### Example 5: Incident Response (Parallel Investigation)

**Scenario:** Schedule generation failing

```python
# Immediate parallel investigation
investigators = spawn_heterogeneous_agents([
    ("researcher", Task("check_solver_logs")),
    ("researcher", Task("check_database_health")),
    ("researcher", Task("check_recent_code_changes")),
    ("critic", Task("reproduce_in_test_environment"))
])

# Execute all in parallel (time-critical)
results = execute_agents_parallel(investigators)

# Synthesize root cause
synthesizer = create_agent("synthesizer", Task(
    type="root_cause_analysis",
    investigations=results,
    severity="P1"
))
root_cause = synthesizer.execute()

# If root cause found, spawn fixer
if root_cause.confirmed:
    generator = create_agent("generator", Task(
        type="implement_fix",
        root_cause=root_cause
    ))
    fix = generator.execute()

    # Validate fix
    validator = create_agent("validator", Task(
        type="verify_fix",
        fix=fix,
        original_issue=root_cause
    ))
    verification = validator.execute()
```

**Output:**
```markdown
## Incident Response: Schedule Generation Failure

**Severity:** P1 (Production down)
**Investigation Time:** 12 minutes (parallel)
**Root Cause:** Database index missing after migration

**Evidence:**
- Solver logs: Timeout after 30min (normally 5min)
- Database health: Query on `assignments` table taking 45s
- Recent changes: Migration 0042 dropped index accidentally
- Reproduction: Confirmed in test environment

**Fix Implemented:**
- Add missing index on `assignments(person_id, block_id)`
- Migration: 0043_restore_missing_index.py

**Verification:**
✅ Query time: 45s → 0.2s
✅ Schedule generation: Success in 4min
✅ All tests pass

**Status:** RESOLVED
**Total Time:** 45 minutes (investigation + fix + verification)
```

---

## VIII. BEST PRACTICES

### 1. When to Use Multi-Agent Composition

**✅ Use Multi-Agent When:**
- Task has independent subtasks (parallelizable)
- Multiple expertise domains required
- Time-sensitive (parallelism saves time)
- Need diverse perspectives (avoid blind spots)
- Task is complex (divide and conquer)

**❌ Don't Use Multi-Agent When:**
- Task is simple (overhead > value)
- Task is highly sequential (no parallelism)
- Agents would overlap/conflict
- Single agent sufficient

---

### 2. Agent Selection Guidelines

**Match Agent to Task:**
- **Research/Investigate:** Researcher
- **Verify/Validate:** Validator
- **Create/Generate:** Generator
- **Test/Challenge:** Critic
- **Integrate/Summarize:** Synthesizer

**Consider Personality:**
- Conservative task → Conservative agent
- Creative task → Creative agent
- Adversarial task → Adversarial agent

---

### 3. Merge Strategy Selection

| Strategy | When to Use | Trade-offs |
|----------|-------------|------------|
| **Consensus** | Need agreement, majority vote | May lose minority insights |
| **Union** | Comprehensive coverage critical | May include false positives |
| **Priority** | Agents have different expertise | Requires accurate weighting |
| **Synthesis** | Need coherent narrative | Slower, requires meta-agent |

---

### 4. Resource Management

**Limits:**
- Max 10 parallel agents (avoid resource exhaustion)
- Max 30min per agent (timeout if stuck)
- Max 100k tokens context per agent (avoid bloat)

**Monitoring:**
- Track agent execution time
- Monitor memory usage
- Log all agent actions for audit

---

### 5. Error Handling

**Agent Failures:**
- If 1 agent fails: Continue with others, note partial results
- If >50% fail: Abort, investigate systemic issue
- Always log failures for debugging

**Timeout Handling:**
- Graceful termination (save partial results)
- Log timeout for analysis
- Consider increasing timeout or simplifying task

---

## IX. INTEGRATION WITH EXISTING AGENTS

### Using Named Agents as Templates

```python
# SCHEDULER agent can spawn sub-agents
def generate_schedule_with_agents():
    # 1. Research constraints (Researcher)
    researcher = create_agent_from_existing(
        base="SCHEDULER",
        archetype="researcher",
        task="analyze_constraints"
    )

    # 2. Generate alternatives (Generator)
    generators = [
        create_agent_from_existing(
            base="SCHEDULER",
            archetype="generator",
            task=f"generate_schedule_{goal}"
        )
        for goal in ["fairness", "preferences"]
    ]

    # 3. Validate (Validator)
    validator = create_agent_from_existing(
        base="SCHEDULER",
        archetype="validator",
        task="validate_acgme"
    )
```

---

## X. VERSIONING & EVOLUTION

### Template Versioning

```yaml
agent_template:
  name: "validator"
  version: "2.1.0"
  changelog:
    - version: "2.1.0"
      date: "2025-12-26"
      changes: "Added credential validation"
    - version: "2.0.0"
      date: "2025-11-15"
      changes: "Major refactor - multi-tier validation"
```

### Template Evolution

**When to Update Template:**
1. New capability added (skill, tool)
2. Personality adjustment based on experience
3. Performance improvement (faster, more accurate)
4. Bug fix (incorrect behavior)

**Process:**
1. Document change in changelog
2. Increment version (major.minor.patch)
3. Test new template
4. Update all agent factories using template

---

## XI. MONITORING & METRICS

### Agent Performance Metrics

```python
class AgentMetrics:
    agent_id: str
    template: str
    task_type: str

    # Execution
    duration: float  # seconds
    timeout: bool
    error: Optional[str]

    # Quality
    output_quality: float  # 0-1
    constraint_violations: int
    false_positives: int
    false_negatives: int

    # Resources
    tokens_used: int
    tools_called: int
    skills_accessed: int

    # Coordination
    agents_spawned: int
    merge_strategy: str
    synthesis_quality: float  # 0-1
```

### Success Criteria

**Individual Agent:**
- Task completion: > 90%
- Timeout rate: < 5%
- Error rate: < 10%
- Output quality: > 0.8

**Multi-Agent Orchestration:**
- Parallelization efficiency: > 50%
- Merge quality: > 0.85
- Conflict resolution: < 5% escalation
- Total time: < 2× single-agent time (parallelism benefit)

---

## XII. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-26 | Initial AGENT_FACTORY specification |

---

**Next Review:** 2026-03-26 (Quarterly - evolves with agent usage patterns)
