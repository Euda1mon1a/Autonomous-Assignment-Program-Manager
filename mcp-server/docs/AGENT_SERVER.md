***REMOVED*** MCP Agent Server

**Implementation of the November 2025 MCP Specification - Agentic Pattern**

***REMOVED******REMOVED*** Overview

The MCP Agent Server extends the base Model Context Protocol with agentic capabilities, allowing the server to autonomously:

- Decompose complex goals into executable subtasks
- Use LLM sampling for reasoning and decision-making
- Execute multi-step workflows with context propagation
- Support human-in-the-loop approval workflows

***REMOVED******REMOVED*** Architecture

***REMOVED******REMOVED******REMOVED*** Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentMCPServer                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────┐      ┌────────────────┐               │
│  │ Goal           │      │ LLM Sampling   │               │
│  │ Decomposition  │──────│ Integration    │               │
│  └────────────────┘      └────────────────┘               │
│         │                        │                         │
│         ▼                        ▼                         │
│  ┌────────────────┐      ┌────────────────┐               │
│  │ Task           │      │ Context        │               │
│  │ Execution      │◄─────│ Propagation    │               │
│  └────────────────┘      └────────────────┘               │
│         │                                                  │
│         ▼                                                  │
│  ┌────────────────────────────────────────┐               │
│  │   Human-in-the-Loop Approval           │               │
│  └────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED******REMOVED*** Agentic Workflow Pattern

1. **Goal Definition**: High-level objective is specified
2. **Decomposition**: Goal is broken into ordered subtasks
3. **Execution**: Tasks run sequentially, respecting dependencies
4. **Context Propagation**: Each task's output feeds the next
5. **LLM Reasoning**: Tasks requiring intelligence use sampling
6. **Human Approval**: Critical decisions can require human sign-off

***REMOVED******REMOVED*** Agentic Tools

***REMOVED******REMOVED******REMOVED*** 1. analyze_and_fix_schedule

**Purpose**: Autonomous schedule analysis and repair

**Workflow**:
```
Goal: Fix schedule issue
  ├─ Task 1: Identify problem (LLM) ✓
  ├─ Task 2: Find root causes (LLM) ✓
  │    └─ Depends on: Task 1
  ├─ Task 3: Generate solutions (LLM) ✓
  │    └─ Depends on: Task 2
  ├─ Task 4: Evaluate solutions (LLM) ✓
  │    └─ Depends on: Task 3
  └─ Task 5: Apply fixes (Human approval) ⏸
       └─ Depends on: Task 4
```

**Example**:
```python
result = await agent.analyze_and_fix_schedule(
    schedule_id="sched-2025-01",
    issue_description="Coverage gap on 2025-01-15 PM shift",
    auto_apply=False  ***REMOVED*** Require approval
)

***REMOVED*** Result includes:
***REMOVED*** - Detailed analysis with root causes
***REMOVED*** - Multiple fix options with scores
***REMOVED*** - Execution log showing reasoning
***REMOVED*** - Applied fixes (if auto_apply=True)
```

**Use Cases**:
- Coverage gaps from unexpected absences
- Compliance violations detected by monitoring
- Workload imbalances reported by faculty
- Schedule optimization opportunities

***REMOVED******REMOVED******REMOVED*** 2. optimize_coverage

**Purpose**: Multi-criteria coverage optimization

**Workflow**:
```
Goal: Optimize coverage for date range
  ├─ Task 1: Analyze gaps ✓
  ├─ Task 2: Generate options (LLM) ✓
  │    └─ Depends on: Task 1
  ├─ Task 3: Score options (LLM) ✓
  │    └─ Depends on: Task 2
  └─ Task 4: Recommend best (LLM) ✓
       └─ Depends on: Task 3
```

**Example**:
```python
result = await agent.optimize_coverage(
    start_date=date(2025, 2, 1),
    end_date=date(2025, 2, 28),
    optimization_goal="maximize_coverage_minimize_cost",
    constraints={
        "max_overtime_hours": 20,
        "maintain_acgme_compliance": True,
    }
)

***REMOVED*** Result includes:
***REMOVED*** - Current coverage analysis
***REMOVED*** - Multiple optimization strategies
***REMOVED*** - Scored options (coverage, cost, workload, etc.)
***REMOVED*** - Recommended approach with reasoning
```

**Optimization Strategies**:
- Activate backup faculty pool
- Redistribute existing assignments
- Extend selected faculty hours (with limits)
- Request external coverage
- Adjust service levels temporarily

***REMOVED******REMOVED******REMOVED*** 3. resolve_conflict

**Purpose**: Stakeholder-aware conflict resolution

**Workflow**:
```
Goal: Resolve scheduling conflict
  ├─ Task 1: Identify stakeholders (LLM) ✓
  ├─ Task 2: Generate resolutions (LLM) ✓
  │    └─ Depends on: Task 1
  ├─ Task 3: Evaluate trade-offs (LLM) ✓
  │    └─ Depends on: Task 2
  └─ Task 4: Propose resolution (Human approval) ⏸
       └─ Depends on: Task 3
```

**Example**:
```python
result = await agent.resolve_conflict(
    conflict_description=(
        "Dr. Smith and Dr. Martinez both requested "
        "2025-01-20 off. Only one can be granted."
    ),
    constraints={
        "must_maintain_supervision_ratio": True,
        "acgme_compliant": True,
    },
    require_approval=True
)

***REMOVED*** Result includes:
***REMOVED*** - Stakeholder identification
***REMOVED*** - Multiple resolution strategies
***REMOVED*** - Fairness scoring (0.0-1.0)
***REMOVED*** - Trade-off analysis for each stakeholder
***REMOVED*** - Recommended resolution with reasoning
***REMOVED*** - Approval workflow status
```

**Resolution Strategies**:
- Mutual swaps (win-win)
- Priority-based allocation
- Split the difference approaches
- Escalation to leadership
- Alternative compensation

***REMOVED******REMOVED*** LLM Sampling

***REMOVED******REMOVED******REMOVED*** How It Works

The agent server uses MCP's sampling capability to call an LLM for reasoning:

```python
async def sample_llm(
    prompt: str,
    context: dict,
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> str:
    """
    Make LLM sampling call for reasoning.

    In production, this uses the MCP sampling protocol
    to call the configured LLM provider.
    """
    ***REMOVED*** Build full prompt with context
    full_prompt = build_prompt(prompt, context)

    ***REMOVED*** MCP sampling call
    response = await mcp.sample(
        provider=self.llm_provider,
        prompt=full_prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )

    return response.text
```

***REMOVED******REMOVED******REMOVED*** When LLM Sampling is Used

**Analysis Tasks**:
- Root cause identification
- Pattern recognition
- Trend analysis

**Generation Tasks**:
- Creating solution options
- Suggesting alternatives
- Brainstorming approaches

**Evaluation Tasks**:
- Scoring and ranking options
- Trade-off analysis
- Risk assessment

**Reasoning Tasks**:
- Multi-criteria decision making
- Fairness evaluation
- Stakeholder impact analysis

***REMOVED******REMOVED*** Goal and Task Management

***REMOVED******REMOVED******REMOVED*** Task Model

```python
@dataclass
class Task:
    """A subtask in an agentic workflow."""

    id: UUID
    name: str
    description: str
    status: TaskStatus  ***REMOVED*** PENDING, IN_PROGRESS, COMPLETED, FAILED
    priority: TaskPriority  ***REMOVED*** CRITICAL, HIGH, MEDIUM, LOW
    dependencies: list[UUID]  ***REMOVED*** Tasks that must complete first
    requires_llm: bool  ***REMOVED*** Needs LLM reasoning
    requires_human: bool  ***REMOVED*** Needs human approval
    context: dict  ***REMOVED*** Execution context
    result: Any  ***REMOVED*** Task output
```

***REMOVED******REMOVED******REMOVED*** Dependency Resolution

Tasks are executed in topological order respecting dependencies:

```python
def _order_tasks_by_dependencies(tasks: list[Task]) -> list[Task]:
    """
    Topologically sort tasks by dependencies.

    Ensures each task runs only after its dependencies complete.
    """
    ***REMOVED*** Implementation uses graph traversal
    return ordered_tasks
```

***REMOVED******REMOVED******REMOVED*** Context Propagation

Each task's output is added to the execution context for downstream tasks:

```python
context = {"schedule_id": "sched-001"}

***REMOVED*** Task 1 executes
result_1, context = await execute_subtask(task_1, context)
***REMOVED*** context now includes: {"identify_problem": result_1, ...}

***REMOVED*** Task 2 can use Task 1's output
result_2, context = await execute_subtask(task_2, context)
***REMOVED*** context now includes both results
```

***REMOVED******REMOVED*** Human-in-the-Loop

***REMOVED******REMOVED******REMOVED*** Approval Workflow

Tasks can be flagged as requiring human approval:

```python
task = Task(
    name="apply_fixes",
    description="Apply recommended schedule changes",
    requires_human=True,  ***REMOVED*** Needs approval
    priority=TaskPriority.CRITICAL
)
```

When such a task is reached:
1. Workflow pauses
2. Goal marked as `awaiting_approval`
3. Result includes approval information
4. Execution log shows pause point

***REMOVED******REMOVED******REMOVED*** Approval Integration

```python
***REMOVED*** Create conflict resolution
result = await agent.resolve_conflict(
    conflict_description="...",
    require_approval=True  ***REMOVED*** Enable approval workflow
)

if result.awaiting_approval:
    ***REMOVED*** Show proposed resolution to human
    print(f"Proposed: {result.resolutions_proposed[0].description}")
    print(f"Requires approval from: {result.approval_from}")

    ***REMOVED*** Human reviews and approves (via UI/API)
    ***REMOVED*** Then agent can continue execution
```

***REMOVED******REMOVED*** Integration with Existing MCP Server

***REMOVED******REMOVED******REMOVED*** Registration Pattern

```python
from scheduler_mcp.agent_server import AgentMCPServer
from scheduler_mcp.server import mcp  ***REMOVED*** FastMCP instance

***REMOVED*** Initialize agent server
agent = AgentMCPServer(llm_provider="claude-3-5-sonnet-20241022")

***REMOVED*** Register agentic tools with FastMCP
@mcp.tool()
async def analyze_and_fix_schedule_agent(
    schedule_id: str | None = None,
    issue_description: str = "",
    auto_apply: bool = False,
) -> dict:
    """Agentic schedule analysis and repair."""
    result = await agent.analyze_and_fix_schedule(
        schedule_id=schedule_id,
        issue_description=issue_description,
        auto_apply=auto_apply,
    )
    return result.model_dump()
```

***REMOVED******REMOVED******REMOVED*** Service Integration

The agent server integrates with backend services:

```python
***REMOVED*** Backend service integration points
from app.resilience.service import ResilienceService
from app.services.swap_executor import SwapExecutor
from app.scheduling.acgme_validator import ACGMEValidator

class AgentMCPServer:
    def __init__(self, db_session=None):
        self.resilience_service = ResilienceService(db_session)
        self.swap_executor = SwapExecutor()
        self.validator = ACGMEValidator()

    async def _execute_standard_task(self, task: Task, context: dict):
        """Call actual backend services."""
        if task.name == "analyze_gaps":
            ***REMOVED*** Call resilience service
            health = self.resilience_service.check_health(...)
            return health

        elif task.name == "apply_fixes":
            ***REMOVED*** Call swap executor
            result = await self.swap_executor.execute_swap(...)
            return result
```

***REMOVED******REMOVED*** Error Handling and Recovery

***REMOVED******REMOVED******REMOVED*** Task Failure Handling

```python
try:
    result, context = await execute_subtask(task, context)
except Exception as e:
    task.status = TaskStatus.FAILED
    task.error = str(e)

    ***REMOVED*** Log failure
    execution_log.append(f"✗ {task.name} failed: {e}")

    ***REMOVED*** Mark goal as failed
    goal.success = False

    ***REMOVED*** Stop execution
    break
```

***REMOVED******REMOVED******REMOVED*** Retry Logic

For transient failures:

```python
MAX_RETRIES = 3
retry_count = 0

while retry_count < MAX_RETRIES:
    try:
        result = await execute_subtask(task, context)
        break
    except TransientError as e:
        retry_count += 1
        await asyncio.sleep(2 ** retry_count)  ***REMOVED*** Exponential backoff
```

***REMOVED******REMOVED*** Monitoring and Observability

***REMOVED******REMOVED******REMOVED*** Goal Tracking

```python
***REMOVED*** Get all active goals
active_goals = agent.get_active_goals()

***REMOVED*** Get recently completed goals
completed = agent.get_completed_goals(limit=10)

***REMOVED*** Get detailed status
status = agent.get_goal_status(goal_id)
```

***REMOVED******REMOVED******REMOVED*** Execution Logging

Every agentic tool returns an execution log:

```python
result = await agent.analyze_and_fix_schedule(...)

for entry in result.execution_log:
    print(entry)

***REMOVED*** Output:
***REMOVED*** ✓ identify_problem: Analyze schedule - Completed
***REMOVED*** ✓ find_root_causes: Determine root causes - Completed
***REMOVED*** ✓ generate_solutions: Generate fix options - Completed
***REMOVED*** ✓ evaluate_solutions: Score solutions - Completed
***REMOVED*** ⏸ Awaiting human approval before proceeding
```

***REMOVED******REMOVED******REMOVED*** Event Hooks

```python
***REMOVED*** Register event handlers (future enhancement)
agent.on_goal_started = lambda goal: logger.info(f"Goal started: {goal.id}")
agent.on_task_completed = lambda task: metrics.increment("tasks_completed")
agent.on_llm_call = lambda prompt: audit_log.record(prompt)
```

***REMOVED******REMOVED*** Performance Considerations

***REMOVED******REMOVED******REMOVED*** LLM Call Optimization

- **Batching**: Group similar LLM calls when possible
- **Caching**: Cache LLM responses for identical prompts
- **Streaming**: Use streaming for long-running analyses
- **Parallel Execution**: Run independent tasks concurrently

***REMOVED******REMOVED******REMOVED*** Cost Management

```python
***REMOVED*** Track LLM usage
total_tokens_used = 0
total_cost = 0.0

async def sample_llm_with_tracking(prompt, context):
    response = await sample_llm(prompt, context)

    ***REMOVED*** Track usage
    tokens = count_tokens(prompt) + count_tokens(response)
    total_tokens_used += tokens
    total_cost += calculate_cost(tokens, model)

    return response
```

***REMOVED******REMOVED*** Testing

***REMOVED******REMOVED******REMOVED*** Unit Testing

```python
import pytest
from scheduler_mcp.agent_server import AgentMCPServer

@pytest.mark.asyncio
async def test_goal_decomposition():
    """Test goal decomposition into tasks."""
    agent = AgentMCPServer()

    tasks = await agent.decompose_goal(
        "Analyze and fix schedule issue",
        {"schedule_id": "test-001"}
    )

    assert len(tasks) > 0
    assert any(t.requires_llm for t in tasks)
    assert all(isinstance(t.id, UUID) for t in tasks)

@pytest.mark.asyncio
async def test_task_execution():
    """Test task execution with context propagation."""
    agent = AgentMCPServer()

    task = Task(
        name="test_task",
        description="Test task",
        requires_llm=False
    )

    context = {"input": "test"}
    result, updated_context = await agent.execute_subtask(task, context)

    assert task.status == TaskStatus.COMPLETED
    assert "test_task" in updated_context
```

***REMOVED******REMOVED******REMOVED*** Integration Testing

```python
@pytest.mark.asyncio
async def test_analyze_and_fix_workflow():
    """Test complete analyze and fix workflow."""
    agent = AgentMCPServer()

    result = await agent.analyze_and_fix_schedule(
        issue_description="Test coverage gap",
        auto_apply=False
    )

    assert result.status in ["analyzed", "fully_fixed"]
    assert len(result.analysis.issues_found) > 0
    assert len(result.recommended_fixes) > 0
    assert len(result.execution_log) > 0
```

***REMOVED******REMOVED*** Future Enhancements

***REMOVED******REMOVED******REMOVED*** Planned Features

1. **Multi-Agent Collaboration**
   - Multiple agents working together
   - Agent specialization (coverage, compliance, optimization)
   - Consensus-based decision making

2. **Learning and Adaptation**
   - Track success rates of different strategies
   - Adapt decision-making based on outcomes
   - Personalized recommendations per facility

3. **Advanced Reasoning**
   - Chain-of-thought prompting
   - Tree-of-thought exploration
   - Self-verification loops

4. **Proactive Monitoring**
   - Continuous background analysis
   - Predictive issue detection
   - Automatic preventive actions

***REMOVED******REMOVED*** References

- **MCP Specification**: November 2025 update (agentic pattern)
- **Backend Integration**: `/backend/app/resilience/service.py`
- **Existing Tools**: `/mcp-server/src/scheduler_mcp/tools.py`
- **FastMCP Docs**: https://github.com/jlowin/fastmcp

***REMOVED******REMOVED*** License

Same as main project (see root LICENSE file)
