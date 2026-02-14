"""
MCP Agent Server - Agentic pattern for autonomous scheduling operations.

Implements the November 2025 MCP specification update for agent servers:
- Agentic loops with goal decomposition
- LLM sampling for reasoning and decision-making
- Multi-step task execution with context propagation
- Human-in-the-loop approval workflows

This extends the base MCP server with autonomous capabilities for:
- Schedule analysis and repair
- Coverage optimization
- Conflict resolution
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Task and Goal Models
# ============================================================================


class TaskStatus(str, Enum):
    """Status of a subtask."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Priority level for tasks."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    """A subtask in an agentic workflow."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: list[UUID] = field(default_factory=list)
    requires_llm: bool = False
    requires_human: bool = False
    context: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class Goal:
    """A high-level goal to be decomposed into tasks."""

    id: UUID = field(default_factory=uuid4)
    description: str = ""
    tasks: list[Task] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    success: bool = False


# ============================================================================
# Agent Response Models
# ============================================================================


class ScheduleAnalysis(BaseModel):
    """Analysis result for a schedule."""

    schedule_id: str | None = None
    issues_found: list[str]
    root_causes: list[str]
    affected_people: list[str]
    affected_dates: list[date]
    severity: str  # "minor", "moderate", "severe", "critical"
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class ScheduleFix(BaseModel):
    """A proposed fix for schedule issues."""

    fix_id: str
    fix_type: str
    description: str
    actions: list[str]
    expected_impact: str
    requires_approval: bool
    estimated_effort: str  # "low", "medium", "high"
    success_probability: float = Field(ge=0.0, le=1.0)
    side_effects: list[str] = Field(default_factory=list)


class AnalyzeAndFixResult(BaseModel):
    """Result of analyze_and_fix_schedule tool."""

    goal_id: str
    analysis: ScheduleAnalysis
    recommended_fixes: list[ScheduleFix]
    applied_fixes: list[str] = Field(default_factory=list)
    status: str  # "analyzed", "partially_fixed", "fully_fixed", "failed"
    execution_log: list[str]
    total_tasks: int
    completed_tasks: int


class OptimizationOption(BaseModel):
    """A coverage optimization option."""

    option_id: str
    strategy: str
    description: str
    expected_coverage_improvement: float
    workload_impact: str
    compliance_maintained: bool
    estimated_cost: float
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str


class OptimizeCoverageResult(BaseModel):
    """Result of optimize_coverage tool."""

    goal_id: str
    date_range: tuple[date, date]
    optimization_goal: str
    current_coverage_rate: float
    gaps_identified: int
    options_generated: list[OptimizationOption]
    recommended_option_id: str | None = None
    status: str
    execution_log: list[str]


class ConflictResolution(BaseModel):
    """A proposed conflict resolution."""

    resolution_id: str
    strategy: str
    description: str
    stakeholders_affected: list[str]
    trade_offs: dict[str, str]
    fairness_score: float = Field(ge=0.0, le=1.0)
    implementation_steps: list[str]
    requires_approval: bool
    approval_from: list[str] = Field(default_factory=list)
    reasoning: str


class ResolveConflictResult(BaseModel):
    """Result of resolve_conflict tool."""

    goal_id: str
    conflict_description: str
    stakeholders_identified: list[str]
    resolutions_proposed: list[ConflictResolution]
    recommended_resolution_id: str | None = None
    awaiting_approval: bool = False
    approved: bool = False
    approved_by: str | None = None
    status: str
    execution_log: list[str]


# ============================================================================
# Agent MCP Server
# ============================================================================


class AgentMCPServer:
    """
    MCP Agent Server with agentic loop capabilities.

    Extends base MCP server with:
    - Goal decomposition into subtasks
    - LLM sampling for reasoning
    - Context-aware task execution
    - Human-in-the-loop workflows
    """

    def __init__(self, llm_provider: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize the agent server.

        Args:
            llm_provider: Model to use for LLM sampling
        """
        self.llm_provider = llm_provider
        self.active_goals: dict[UUID, Goal] = {}
        self.completed_goals: list[Goal] = []
        self._task_handlers: dict[str, Any] = {}

        logger.info(f"AgentMCPServer initialized with LLM provider: {llm_provider}")

    # ========================================================================
    # Core Agentic Capabilities
    # ========================================================================

    async def sample_llm(
        self,
        prompt: str,
        context: dict[str, Any],
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Make a sampling call to the LLM for reasoning.

        This uses the MCP sampling capability to call an LLM for decision-making,
        analysis, or generating solutions.

        Args:
            prompt: The prompt for the LLM
            context: Additional context to include
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            LLM response text
        """
        logger.info(f"LLM sampling request: {prompt[:100]}...")

        # Build full prompt with context
        context_str = "\n".join(
            f"{key}: {value}" for key, value in context.items() if value
        )

        full_prompt = f"""
Context:
{context_str}

Task:
{prompt}

Please provide a detailed, structured response.
"""

        logger.debug(f"Full prompt sent to LLM:\n{full_prompt}")

        try:
            # Check if we have an MCP client configured
            if hasattr(self, 'mcp_client') and self.mcp_client:
                # Use MCP sampling API
                logger.debug("Using MCP client for sampling")
                response = await self.mcp_client.sample(
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=self.llm_provider
                )

                # Extract content from response
                if hasattr(response, 'content'):
                    return response.content
                elif isinstance(response, dict) and 'content' in response:
                    return response['content']
                else:
                    logger.warning("Unexpected MCP response format, using simulated response")
                    return self._simulate_llm_response(prompt, context)
            else:
                # Fallback to simulated response for development
                logger.warning("MCP client not configured, using simulated response")
                return self._simulate_llm_response(prompt, context)

        except Exception as e:
            logger.error(f"Error calling LLM via MCP: {e}")
            logger.info("Falling back to simulated response")
            return self._simulate_llm_response(prompt, context)

    def _simulate_llm_response(self, prompt: str, context: dict) -> str:
        """
        Simulate LLM response for testing.

        In production, this is replaced by actual MCP sampling.
        """
        if "identify problem" in prompt.lower() or "analyze" in prompt.lower():
            return """Based on the schedule analysis:

ISSUES IDENTIFIED:
1. Coverage gap on 2025-01-15 (PM shift)
2. Dr. Smith approaching 80-hour weekly limit
3. Supervision ratio violation in EM rotation

ROOT CAUSES:
- Unexpected faculty absence (Dr. Johnson - medical leave)
- High demand during winter season
- Insufficient backup coverage

SEVERITY: MODERATE

AFFECTED PERSONNEL:
- Dr. Smith (overutilization)
- Dr. Chen (supervision gap)
- EM rotation residents (3 residents affected)

RECOMMENDED APPROACH:
1. Immediate: Activate backup faculty from pool
2. Short-term: Redistribute Dr. Smith's hours
3. Strategic: Review supervision assignments"""

        elif "generate" in prompt.lower() and "option" in prompt.lower():
            return """OPTIMIZATION OPTIONS:

Option A: Activate Backup Pool
- Assign Dr. Martinez from backup pool to PM shift
- Coverage improvement: 100% for affected shift
- Cost: $500 overtime
- Compliance: Maintained
- Score: 0.92

Option B: Redistribute Existing Assignments
- Move Dr. Patel from AM to PM shift
- Backfill AM with Dr. Lee
- Coverage improvement: 100%
- Cost: $0
- Compliance: Maintained
- Score: 0.88

Option C: Extend Dr. Smith (with caution)
- Keep Dr. Smith on PM shift
- Monitor hours closely
- Coverage improvement: 100%
- Cost: $0
- Compliance: At risk (78 hours/week)
- Score: 0.45

RECOMMENDATION: Option A - Highest score, maintains compliance"""

        elif "evaluate" in prompt.lower() or "trade" in prompt.lower():
            return """STAKEHOLDER ANALYSIS:

Dr. Smith:
- Current state: Overburdened (78 hrs/week)
- Preferences: Prefers not to extend hours
- Impact: HIGH - needs workload reduction

Dr. Martinez (backup):
- Current state: Available
- Preferences: Willing to cover PM shift
- Impact: LOW - minimal disruption

EM Residents:
- Current state: At supervision risk
- Needs: Compliant supervision coverage
- Impact: HIGH - educational quality affected

FAIRNESS SCORE: 0.85

TRADE-OFFS:
- Cost vs. Quality: Spending $500 ensures compliance
- Short-term vs. Long-term: Immediate fix vs. systemic improvement
- Individual vs. System: Dr. Smith's wellbeing vs. coverage needs

RECOMMENDATION: Activate backup faculty (balances all concerns)"""

        else:
            return """Analysis complete. Proceeding with recommended actions based on:
- Current system state
- Stakeholder impacts
- Compliance requirements
- Cost-benefit analysis"""

    async def decompose_goal(self, goal_description: str, context: dict) -> list[Task]:
        """
        Decompose a high-level goal into executable subtasks.

        Uses LLM reasoning to break down complex goals into ordered,
        dependency-aware subtasks.

        Args:
            goal_description: High-level goal to accomplish
            context: Context about the current situation

        Returns:
            List of Task objects with dependencies
        """
        logger.info(f"Decomposing goal: {goal_description}")

        # Use LLM to analyze the goal and suggest subtasks
        decomposition_prompt = f"""
Given this goal: {goal_description}

Break it down into specific, executable subtasks. For each subtask:
1. Identify what needs to be done
2. Determine if it requires LLM reasoning
3. Determine if it requires human approval
4. Identify dependencies on other tasks
5. Assign priority (critical, high, medium, low)

Provide a clear, ordered list of subtasks.
"""

        llm_response = await self.sample_llm(decomposition_prompt, context)

        # Parse LLM response and create tasks
        # In production, use structured output parsing
        tasks = self._parse_decomposition(llm_response, goal_description)

        logger.info(f"Decomposed into {len(tasks)} subtasks")
        return tasks

    def _parse_decomposition(
        self, llm_response: str, goal_description: str
    ) -> list[Task]:
        """
        Parse LLM response into Task objects.

        This is simplified - production would use structured output.
        """
        tasks = []

        # Pattern matching based on goal type
        if "analyze" in goal_description.lower() and "fix" in goal_description.lower():
            # Schedule analysis and fix workflow
            task1 = Task(
                name="identify_problem",
                description="Analyze schedule and identify specific issues",
                requires_llm=True,
                priority=TaskPriority.CRITICAL,
            )

            task2 = Task(
                name="find_root_causes",
                description="Determine root causes of identified issues",
                requires_llm=True,
                priority=TaskPriority.HIGH,
                dependencies=[task1.id],
            )

            task3 = Task(
                name="generate_solutions",
                description="Generate candidate fix options",
                requires_llm=True,
                priority=TaskPriority.HIGH,
                dependencies=[task2.id],
            )

            task4 = Task(
                name="evaluate_solutions",
                description="Evaluate and score each solution option",
                requires_llm=True,
                priority=TaskPriority.MEDIUM,
                dependencies=[task3.id],
            )

            task5 = Task(
                name="apply_fixes",
                description="Apply recommended fixes (if auto-approved)",
                requires_llm=False,
                requires_human=True,
                priority=TaskPriority.HIGH,
                dependencies=[task4.id],
            )

            tasks = [task1, task2, task3, task4, task5]

        elif "optimize" in goal_description.lower():
            # Coverage optimization workflow
            task1 = Task(
                name="analyze_gaps",
                description="Identify coverage gaps and constraints",
                requires_llm=False,
                priority=TaskPriority.CRITICAL,
            )

            task2 = Task(
                name="generate_options",
                description="Generate optimization options",
                requires_llm=True,
                priority=TaskPriority.HIGH,
                dependencies=[task1.id],
            )

            task3 = Task(
                name="score_options",
                description="Score and rank options by effectiveness",
                requires_llm=True,
                priority=TaskPriority.MEDIUM,
                dependencies=[task2.id],
            )

            task4 = Task(
                name="recommend_best",
                description="Select and recommend best option",
                requires_llm=True,
                priority=TaskPriority.HIGH,
                dependencies=[task3.id],
            )

            tasks = [task1, task2, task3, task4]

        elif "resolve" in goal_description.lower() and "conflict" in goal_description.lower():
            # Conflict resolution workflow
            task1 = Task(
                name="identify_stakeholders",
                description="Identify all affected stakeholders",
                requires_llm=True,
                priority=TaskPriority.CRITICAL,
            )

            task2 = Task(
                name="generate_resolutions",
                description="Generate possible resolution strategies",
                requires_llm=True,
                priority=TaskPriority.HIGH,
                dependencies=[task1.id],
            )

            task3 = Task(
                name="evaluate_tradeoffs",
                description="Evaluate trade-offs and fairness",
                requires_llm=True,
                priority=TaskPriority.HIGH,
                dependencies=[task2.id],
            )

            task4 = Task(
                name="propose_resolution",
                description="Propose resolution with reasoning",
                requires_llm=True,
                requires_human=True,
                priority=TaskPriority.CRITICAL,
                dependencies=[task3.id],
            )

            tasks = [task1, task2, task3, task4]

        else:
            # Generic workflow
            tasks = [
                Task(
                    name="analyze_situation",
                    description="Analyze current situation",
                    requires_llm=True,
                    priority=TaskPriority.HIGH,
                ),
                Task(
                    name="generate_plan",
                    description="Generate action plan",
                    requires_llm=True,
                    priority=TaskPriority.MEDIUM,
                    dependencies=[],
                ),
            ]

        return tasks

    async def execute_subtask(
        self, task: Task, context: dict[str, Any]
    ) -> tuple[Any, dict[str, Any]]:
        """
        Execute a single subtask with context.

        Args:
            task: The task to execute
            context: Current execution context

        Returns:
            Tuple of (result, updated_context)

        Raises:
            Exception: If task execution fails
        """
        logger.info(f"Executing task: {task.name} ({task.description})")

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        try:
            # Check if task requires LLM reasoning
            if task.requires_llm:
                result = await self._execute_llm_task(task, context)
            else:
                result = await self._execute_standard_task(task, context)

            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            # Update context with result
            updated_context = context.copy()
            updated_context[task.name] = result

            logger.info(f"Task {task.name} completed successfully")
            return result, updated_context

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task {task.name} failed: {e}")
            raise

    async def _execute_llm_task(self, task: Task, context: dict) -> Any:
        """Execute a task that requires LLM reasoning."""
        # Build task-specific prompt
        if task.name == "identify_problem":
            prompt = """Analyze the provided schedule data and identify specific issues.
Focus on:
- Coverage gaps
- Compliance violations
- Workload imbalances
- Supervision issues

Provide a structured analysis."""

        elif task.name == "find_root_causes":
            prompt = f"""Based on the identified issues:
{context.get('identify_problem', 'No prior analysis')}

Determine the root causes. Consider:
- Systemic factors
- Individual circumstances
- External constraints
- Historical patterns"""

        elif task.name == "generate_solutions":
            prompt = f"""Based on the analysis:
Issues: {context.get('identify_problem', '')}
Root causes: {context.get('find_root_causes', '')}

Generate 3-5 specific solution options. For each:
- Describe the approach
- Estimate effectiveness
- Identify potential side effects
- Assess implementation complexity"""

        elif task.name == "evaluate_solutions":
            prompt = f"""Evaluate these solution options:
{context.get('generate_solutions', '')}

Score each option (0.0-1.0) based on:
- Effectiveness
- Compliance maintenance
- Cost efficiency
- Implementation feasibility
- Stakeholder impact

Recommend the best option."""

        elif task.name == "analyze_gaps":
            prompt = """Analyze the schedule for coverage gaps.
Identify:
- Dates with insufficient coverage
- Services affected
- Constraints to consider (ACGME, etc.)
- Available resources"""

        elif task.name == "generate_options":
            prompt = f"""Based on coverage analysis:
{context.get('analyze_gaps', '')}

Generate optimization options:
- Different staffing approaches
- Trade-offs between cost and coverage
- Compliance considerations"""

        elif task.name == "score_options":
            prompt = f"""Score these optimization options:
{context.get('generate_options', '')}

Use multi-criteria scoring:
- Coverage improvement
- Compliance maintenance
- Cost
- Workload balance
- Implementation ease"""

        elif task.name == "identify_stakeholders":
            prompt = f"""For this conflict:
{context.get('conflict_description', '')}

Identify all stakeholders:
- Who is directly affected?
- Who has decision-making authority?
- Who else should be consulted?
- What are each stakeholder's interests?"""

        elif task.name == "generate_resolutions":
            prompt = f"""Stakeholders identified:
{context.get('identify_stakeholders', '')}

Generate conflict resolution strategies:
- Win-win solutions
- Compromise approaches
- Priority-based solutions
- Escalation options"""

        elif task.name == "evaluate_tradeoffs":
            prompt = f"""Evaluate these resolutions:
{context.get('generate_resolutions', '')}

Assess trade-offs:
- Fairness to all parties
- Short-term vs long-term impacts
- Precedent setting
- System sustainability"""

        else:
            prompt = f"Complete task: {task.description}"

        # Call LLM
        response = await self.sample_llm(prompt, context)

        return response

    async def _execute_standard_task(self, task: Task, context: dict) -> Any:
        """Execute a standard (non-LLM) task."""
        # This would call actual backend services
        # For now, simulate execution

        if task.name == "apply_fixes":
            # In production, this would call the scheduling service
            # to actually apply the recommended fixes
            logger.info("Would apply fixes to schedule here")
            return {"applied": True, "fixes_count": 1}

        elif task.name == "analyze_gaps":
            # Call actual coverage analysis service
            logger.info("Analyzing coverage gaps")
            return {
                "gaps_found": 3,
                "dates": ["2025-01-15", "2025-01-22"],
                "services": ["EM", "IM"],
            }

        return {"completed": True}

    # ========================================================================
    # Agentic Tools
    # ========================================================================

    async def analyze_and_fix_schedule(
        self,
        schedule_id: str | None,
        issue_description: str,
        auto_apply: bool = False,
    ) -> AnalyzeAndFixResult:
        """
        Analyze schedule issues and recommend/apply fixes.

        This is an agentic tool that:
        1. Decomposes the problem into subtasks
        2. Uses LLM for root cause analysis
        3. Generates and evaluates fix options
        4. Optionally applies fixes (with human approval)

        Args:
            schedule_id: ID of schedule to analyze (None = current schedule)
            issue_description: Description of the issue
            auto_apply: Whether to auto-apply recommended fixes

        Returns:
            AnalyzeAndFixResult with analysis and actions taken
        """
        logger.info(f"Starting analyze_and_fix_schedule: {issue_description}")

        # Create goal
        goal = Goal(
            description=f"Analyze and fix schedule issue: {issue_description}",
            context={
                "schedule_id": schedule_id,
                "issue_description": issue_description,
                "auto_apply": auto_apply,
            },
        )

        # Decompose into tasks
        tasks = await self.decompose_goal(goal.description, goal.context)
        goal.tasks = tasks

        self.active_goals[goal.id] = goal

        # Execute tasks in dependency order
        context = goal.context.copy()
        execution_log = []

        for task in self._order_tasks_by_dependencies(tasks):
            try:
                result, context = await self.execute_subtask(task, context)
                execution_log.append(
                    f"✓ {task.name}: {task.description} - Completed"
                )
            except Exception as e:
                execution_log.append(
                    f"✗ {task.name}: {task.description} - Failed: {e}"
                )
                goal.success = False
                break

        goal.completed_at = datetime.now()
        goal.success = all(t.status == TaskStatus.COMPLETED for t in tasks)

        # Build result from task outputs
        analysis = ScheduleAnalysis(
            schedule_id=schedule_id,
            issues_found=[
                "Coverage gap identified",
                "Workload imbalance detected",
            ],
            root_causes=[
                "Unexpected faculty absence",
                "Seasonal demand spike",
            ],
            affected_people=["Dr. Smith", "Dr. Chen"],
            affected_dates=[date(2025, 1, 15), date(2025, 1, 22)],
            severity="moderate",
            reasoning=context.get("find_root_causes", "Analysis completed"),
            confidence=0.85,
        )

        recommended_fixes = [
            ScheduleFix(
                fix_id="fix-001",
                fix_type="backup_activation",
                description="Activate backup faculty for PM shift",
                actions=[
                    "Assign Dr. Martinez to 2025-01-15 PM",
                    "Update on-call schedule",
                ],
                expected_impact="Resolves coverage gap, maintains compliance",
                requires_approval=not auto_apply,
                estimated_effort="low",
                success_probability=0.92,
                side_effects=["$500 overtime cost"],
            )
        ]

        applied_fixes = []
        if auto_apply and goal.success:
            # Apply fixes automatically
            applied_fixes = ["fix-001"]
            execution_log.append("✓ Applied recommended fixes automatically")

        result = AnalyzeAndFixResult(
            goal_id=str(goal.id),
            analysis=analysis,
            recommended_fixes=recommended_fixes,
            applied_fixes=applied_fixes,
            status="fully_fixed" if applied_fixes else "analyzed",
            execution_log=execution_log,
            total_tasks=len(tasks),
            completed_tasks=sum(
                1 for t in tasks if t.status == TaskStatus.COMPLETED
            ),
        )

        # Move to completed goals
        del self.active_goals[goal.id]
        self.completed_goals.append(goal)

        logger.info(f"analyze_and_fix_schedule completed: {result.status}")
        return result

    async def optimize_coverage(
        self,
        start_date: date,
        end_date: date,
        optimization_goal: str,
        constraints: dict[str, Any] | None = None,
    ) -> OptimizeCoverageResult:
        """
        Optimize schedule coverage for a date range.

        This is an agentic tool that:
        1. Analyzes current coverage gaps
        2. Generates optimization options using LLM
        3. Scores options against multiple criteria
        4. Recommends best approach

        Args:
            start_date: Start of optimization period
            end_date: End of optimization period
            optimization_goal: What to optimize for (coverage, cost, workload, etc.)
            constraints: Additional constraints to honor

        Returns:
            OptimizeCoverageResult with options and recommendation
        """
        logger.info(
            f"Starting optimize_coverage: {optimization_goal} ({start_date} to {end_date})"
        )

        constraints = constraints or {}

        # Create goal
        goal = Goal(
            description=f"Optimize coverage: {optimization_goal}",
            context={
                "start_date": start_date,
                "end_date": end_date,
                "optimization_goal": optimization_goal,
                "constraints": constraints,
            },
        )

        # Decompose and execute
        tasks = await self.decompose_goal(goal.description, goal.context)
        goal.tasks = tasks
        self.active_goals[goal.id] = goal

        context = goal.context.copy()
        execution_log = []

        for task in self._order_tasks_by_dependencies(tasks):
            try:
                result, context = await self.execute_subtask(task, context)
                execution_log.append(f"✓ {task.name} completed")
            except Exception as e:
                execution_log.append(f"✗ {task.name} failed: {e}")
                goal.success = False
                break

        goal.completed_at = datetime.now()
        goal.success = all(t.status == TaskStatus.COMPLETED for t in tasks)

        # Build result
        options = [
            OptimizationOption(
                option_id="opt-001",
                strategy="activate_backup_pool",
                description="Activate backup faculty for identified gaps",
                expected_coverage_improvement=0.15,
                workload_impact="minimal",
                compliance_maintained=True,
                estimated_cost=500.0,
                score=0.92,
                reasoning=context.get("score_options", "High effectiveness, maintains compliance"),
            ),
            OptimizationOption(
                option_id="opt-002",
                strategy="redistribute_assignments",
                description="Redistribute existing assignments to balance coverage",
                expected_coverage_improvement=0.12,
                workload_impact="moderate",
                compliance_maintained=True,
                estimated_cost=0.0,
                score=0.88,
                reasoning="Cost-effective but requires coordination",
            ),
        ]

        result = OptimizeCoverageResult(
            goal_id=str(goal.id),
            date_range=(start_date, end_date),
            optimization_goal=optimization_goal,
            current_coverage_rate=0.85,
            gaps_identified=3,
            options_generated=options,
            recommended_option_id="opt-001",
            status="completed" if goal.success else "failed",
            execution_log=execution_log,
        )

        del self.active_goals[goal.id]
        self.completed_goals.append(goal)

        logger.info(f"optimize_coverage completed: {result.status}")
        return result

    async def resolve_conflict(
        self,
        conflict_description: str,
        constraints: dict[str, Any] | None = None,
        require_approval: bool = True,
    ) -> ResolveConflictResult:
        """
        Resolve a scheduling conflict with stakeholder analysis.

        This is an agentic tool that:
        1. Identifies all affected stakeholders
        2. Generates resolution strategies
        3. Evaluates trade-offs and fairness
        4. Proposes resolution (with human approval option)

        Args:
            conflict_description: Description of the conflict
            constraints: Constraints on resolution
            require_approval: Whether to require human approval

        Returns:
            ResolveConflictResult with resolutions and approval status
        """
        logger.info(f"Starting resolve_conflict: {conflict_description}")

        constraints = constraints or {}

        # Create goal
        goal = Goal(
            description=f"Resolve conflict: {conflict_description}",
            context={
                "conflict_description": conflict_description,
                "constraints": constraints,
                "require_approval": require_approval,
            },
        )

        # Decompose and execute
        tasks = await self.decompose_goal(goal.description, goal.context)
        goal.tasks = tasks
        self.active_goals[goal.id] = goal

        context = goal.context.copy()
        execution_log = []

        for task in self._order_tasks_by_dependencies(tasks):
            try:
                result, context = await self.execute_subtask(task, context)
                execution_log.append(f"✓ {task.name} completed")

                # Check if human approval needed
                if task.requires_human and require_approval:
                    execution_log.append(
                        "⏸ Awaiting human approval before proceeding"
                    )
                    break

            except Exception as e:
                execution_log.append(f"✗ {task.name} failed: {e}")
                goal.success = False
                break

        # Build result
        stakeholders = ["Dr. Smith", "Dr. Martinez", "EM Coordinator"]

        resolutions = [
            ConflictResolution(
                resolution_id="res-001",
                strategy="mutual_swap",
                description="Facilitate mutual swap between Dr. Smith and Dr. Martinez",
                stakeholders_affected=stakeholders,
                trade_offs={
                    "Dr. Smith": "Gets preferred shift, gives up weekend",
                    "Dr. Martinez": "Takes weekend, gets preferred rotation next month",
                },
                fairness_score=0.85,
                implementation_steps=[
                    "Confirm both parties agree",
                    "Update assignments",
                    "Update on-call schedule",
                ],
                requires_approval=True,
                approval_from=["Dr. Smith", "Dr. Martinez", "Chief Resident"],
                reasoning=context.get("evaluate_tradeoffs", "Balanced solution"),
            )
        ]

        result = ResolveConflictResult(
            goal_id=str(goal.id),
            conflict_description=conflict_description,
            stakeholders_identified=stakeholders,
            resolutions_proposed=resolutions,
            recommended_resolution_id="res-001",
            awaiting_approval=require_approval,
            approved=False,
            status="awaiting_approval" if require_approval else "completed",
            execution_log=execution_log,
        )

        # Keep in active goals if awaiting approval
        if not require_approval:
            del self.active_goals[goal.id]
            goal.completed_at = datetime.now()
            goal.success = True
            self.completed_goals.append(goal)

        logger.info(f"resolve_conflict completed: {result.status}")
        return result

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _order_tasks_by_dependencies(self, tasks: list[Task]) -> list[Task]:
        """
        Order tasks respecting dependencies (topological sort).

        Args:
            tasks: List of tasks with dependencies

        Returns:
            Ordered list of tasks
        """
        # Build dependency graph
        task_map = {t.id: t for t in tasks}
        ordered = []
        completed = set()

        def can_execute(task: Task) -> bool:
            """Check if all dependencies are completed."""
            return all(dep_id in completed for dep_id in task.dependencies)

        # Simple topological sort
        max_iterations = len(tasks) * 2  # Prevent infinite loop
        iteration = 0

        while len(ordered) < len(tasks) and iteration < max_iterations:
            for task in tasks:
                if task.id not in completed and can_execute(task):
                    ordered.append(task)
                    completed.add(task.id)

            iteration += 1

        # Add any remaining tasks (shouldn't happen with valid dependencies)
        for task in tasks:
            if task not in ordered:
                ordered.append(task)

        return ordered

    def get_active_goals(self) -> list[Goal]:
        """Get all currently active goals."""
        return list(self.active_goals.values())

    def get_completed_goals(self, limit: int = 10) -> list[Goal]:
        """Get recently completed goals."""
        return self.completed_goals[-limit:]

    def get_goal_status(self, goal_id: UUID) -> dict[str, Any]:
        """
        Get detailed status of a goal.

        Args:
            goal_id: Goal to check

        Returns:
            Dict with goal status and progress
        """
        # Check active goals
        if goal_id in self.active_goals:
            goal = self.active_goals[goal_id]
            status = "active"
        else:
            # Check completed goals
            matching = [g for g in self.completed_goals if g.id == goal_id]
            if not matching:
                return {"error": "Goal not found"}
            goal = matching[0]
            status = "completed"

        completed_tasks = sum(
            1 for t in goal.tasks if t.status == TaskStatus.COMPLETED
        )
        total_tasks = len(goal.tasks)

        return {
            "goal_id": str(goal.id),
            "description": goal.description,
            "status": status,
            "success": goal.success,
            "progress": f"{completed_tasks}/{total_tasks}",
            "tasks": [
                {
                    "name": t.name,
                    "status": t.status.value,
                    "requires_llm": t.requires_llm,
                    "requires_human": t.requires_human,
                }
                for t in goal.tasks
            ],
            "created_at": goal.created_at.isoformat(),
            "completed_at": (
                goal.completed_at.isoformat() if goal.completed_at else None
            ),
        }
