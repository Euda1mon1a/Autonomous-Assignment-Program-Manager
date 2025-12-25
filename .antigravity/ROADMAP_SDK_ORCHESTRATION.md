# SDK Orchestration Roadmap: From Comet to Production

> **Created:** 2025-12-25
> **Goal:** Replace browser-based Signal Transduction with resilient SDK orchestration
> **Timeline:** Phases, not dates (you decide pacing)

---

## Executive Summary

### Where We Were
```
┌─────────────────────────────────────────────────────────────────┐
│                    COMET BROWSER AGENT                          │
│                                                                 │
│   [Tab 1]   [Tab 2]   [Tab 3]  ...  [Tab 10]                   │
│   Claude    Claude    Claude        Claude                      │
│    Web       Web       Web           Web                        │
│                                                                 │
│   • DOM scraping for responses                                  │
│   • Click automation for actions                                │
│   • ~10GB RAM for browser                                       │
│   • Tab crashes, session timeouts                               │
│   • Fragile selectors break on UI changes                       │
└─────────────────────────────────────────────────────────────────┘
```

### Where We're Going
```
┌─────────────────────────────────────────────────────────────────┐
│                   OPUS 4.5 ORCHESTRATOR                         │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              Claude Agent SDK (Python)                  │   │
│   │                                                         │   │
│   │   Lane 1    Lane 2    Lane 3   ...   Lane 8            │   │
│   │   ┌─────┐  ┌─────┐  ┌─────┐        ┌─────┐            │   │
│   │   │Async│  │Async│  │Async│        │Async│            │   │
│   │   │Client│ │Client│ │Client│       │Client│           │   │
│   │   └─────┘  └─────┘  └─────┘        └─────┘            │   │
│   │                                                         │   │
│   │   • Structured JSON responses                           │   │
│   │   • PreToolUse/PostToolUse hooks                        │   │
│   │   • ~500MB RAM total                                    │   │
│   │   • Built-in retries, session management                │   │
│   │   • Type-safe, testable, observable                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              Observability Layer                        │   │
│   │   Prometheus │ Structured Logs │ Health Checks          │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Current State (You Are Here)

### What Exists

```
.antigravity/
├── settings.json              # Orchestrator config (conceptual)
├── autopilot-instructions.md  # Agent behavior rules
├── guardrails.md              # Operations requiring approval
├── recovery.md                # Failure handling
├── FUTURE_B_MANAGER_VIEW.md   # Multi-agent plans
└── logs/                      # Session logs

.claude/
├── skills/                    # 20+ domain skills
│   ├── acgme-compliance/
│   ├── safe-schedule-generation/
│   ├── security-audit/
│   └── ...
├── hooks/                     # Pre/post execution hooks
│   ├── session-start.sh
│   ├── pre-bash-validate.sh
│   └── stop-verify.sh
├── commands/                  # Slash commands
└── settings.json              # Claude Code permissions

docs/sessions/
└── SESSION_13_PROTOCOL.md     # Signal Transduction documentation
```

### What Works (Comet-Based)
- [x] 8-lane parallel execution
- [x] Domain territory isolation
- [x] Dual-nucleus (Synthesis + DNA Repair)
- [x] HANDOFF protocol for cross-domain
- [x] 8 PRs/hour throughput demonstrated

### Pain Points
- [ ] Browser memory overhead (~10GB)
- [ ] DOM scraping fragility
- [ ] Tab crash recovery manual
- [ ] No structured response format
- [ ] Session timeout handling weak
- [ ] No programmatic hooks

---

## Phase 1: Minimal Viable Orchestrator

**Goal:** Single Claude Code agent controlled via SDK

### Deliverables

```
.antigravity/
└── orchestrator/
    ├── __init__.py
    ├── minimal.py          # Phase 1: Single agent
    └── requirements.txt
```

### Implementation

```python
# .antigravity/orchestrator/minimal.py
"""
Phase 1: Minimal Viable Orchestrator
Single Claude Code agent via SDK - prove the pattern works.
"""
import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import AsyncIterator

# Note: Install with `pip install claude-agent-sdk`
from claude_agent_sdk import query, ClaudeAgentOptions


@dataclass
class TaskResult:
    """Result from a single agent task."""
    task_id: str
    success: bool
    output: str
    duration_seconds: float
    error: str | None = None


class MinimalOrchestrator:
    """
    Phase 1: Prove SDK control works.

    This replaces: Open Chrome → Navigate to claude.ai → Type prompt → Scrape response
    With: Python function call → Structured response
    """

    def __init__(self, working_dir: Path | None = None):
        self.working_dir = working_dir or Path.cwd()
        self.log_file = self.working_dir / ".antigravity/logs/orchestrator.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _log(self, level: str, message: str):
        """Structured logging."""
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [{level}] {message}\n"
        self.log_file.open("a").write(entry)
        print(entry.strip())

    def _load_skills(self) -> str:
        """Load skills from .claude/skills/ as system prompt."""
        skills_dir = self.working_dir / ".claude/skills"
        if not skills_dir.exists():
            return ""

        skill_content = []
        for skill_file in skills_dir.glob("*/SKILL.md"):
            skill_name = skill_file.parent.name
            content = skill_file.read_text()
            skill_content.append(f"## Skill: {skill_name}\n{content}")

        return "\n\n---\n\n".join(skill_content)

    async def run_task(
        self,
        task_id: str,
        prompt: str,
        allowed_tools: list[str] | None = None
    ) -> TaskResult:
        """
        Execute a single task via Claude Agent SDK.

        This is the core primitive that replaces browser automation.
        """
        start_time = datetime.now()
        self._log("INFO", f"Starting task {task_id}: {prompt[:80]}...")

        # Default tools if not specified
        if allowed_tools is None:
            allowed_tools = ["Read", "Edit", "Bash", "Glob", "Grep"]

        # Build options
        options = ClaudeAgentOptions(
            allowed_tools=allowed_tools,
            working_directory=str(self.working_dir),
            append_system_prompt=self._load_skills()
        )

        try:
            # Execute via SDK - this replaces all browser automation
            output_parts = []
            async for message in query(prompt, options=options):
                output_parts.append(str(message))
                self._log("DEBUG", f"Agent: {str(message)[:100]}")

            output = "\n".join(output_parts)
            duration = (datetime.now() - start_time).total_seconds()

            self._log("INFO", f"Completed task {task_id} in {duration:.1f}s")

            return TaskResult(
                task_id=task_id,
                success=True,
                output=output,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self._log("ERROR", f"Task {task_id} failed: {e}")

            return TaskResult(
                task_id=task_id,
                success=False,
                output="",
                duration_seconds=duration,
                error=str(e)
            )


async def main():
    """Test the minimal orchestrator."""
    orchestrator = MinimalOrchestrator()

    # Test task: something simple to prove it works
    result = await orchestrator.run_task(
        task_id="TEST-001",
        prompt="List the files in backend/app/services/ and summarize what each service does.",
        allowed_tools=["Read", "Glob", "Grep"]
    )

    print(f"\n{'='*60}")
    print(f"Task: {result.task_id}")
    print(f"Success: {result.success}")
    print(f"Duration: {result.duration_seconds:.1f}s")
    if result.error:
        print(f"Error: {result.error}")
    print(f"Output:\n{result.output[:500]}...")


if __name__ == "__main__":
    asyncio.run(main())
```

### Validation Criteria
- [ ] `pip install claude-agent-sdk` succeeds
- [ ] `python -m antigravity.orchestrator.minimal` completes a task
- [ ] Logs written to `.antigravity/logs/orchestrator.log`
- [ ] Skills loaded from `.claude/skills/`
- [ ] Response is structured (not DOM scrape)

### Dependencies
```
# .antigravity/orchestrator/requirements.txt
claude-agent-sdk>=0.1.0
```

---

## Phase 2: Multi-Lane Parallelism (Kinase Loop)

**Goal:** 8 parallel agents with domain isolation

### Deliverables

```
.antigravity/
└── orchestrator/
    ├── __init__.py
    ├── minimal.py           # Phase 1
    ├── kinase.py            # Phase 2: Multi-lane
    ├── domains.py           # Domain definitions
    └── requirements.txt
```

### Implementation

```python
# .antigravity/orchestrator/domains.py
"""
Domain definitions for territory isolation.
Maps your PARALLEL_ORCHESTRATION_PROMPT.md to code.
"""
from enum import Enum
from dataclasses import dataclass


class Domain(Enum):
    """Exclusive territory domains from Signal Transduction."""
    CORE = "core"    # models, schemas, db, alembic
    API = "api"      # api routes, services, core config
    SCHED = "sched"  # scheduling engine
    FE = "fe"        # frontend
    TEST = "test"    # tests, docs


@dataclass
class DomainConfig:
    """Configuration for a domain territory."""
    name: Domain
    allowed_paths: list[str]
    forbidden_paths: list[str]
    commit_prefix: str
    allowed_tools: list[str]


# Territory map from your documentation
DOMAIN_CONFIGS = {
    Domain.CORE: DomainConfig(
        name=Domain.CORE,
        allowed_paths=[
            "backend/app/models/**",
            "backend/app/schemas/**",
            "backend/app/db/**",
            "backend/alembic/**"
        ],
        forbidden_paths=[
            "backend/app/api/**",
            "backend/app/services/**",
            "backend/app/scheduling/**",
            "frontend/**"
        ],
        commit_prefix="core:",
        allowed_tools=["Read", "Edit", "Bash", "Glob", "Grep"]
    ),
    Domain.API: DomainConfig(
        name=Domain.API,
        allowed_paths=[
            "backend/app/api/**",
            "backend/app/services/**",
            "backend/app/core/**"
        ],
        forbidden_paths=[
            "backend/app/models/**",
            "backend/app/schemas/**",
            "backend/app/scheduling/**",
            "frontend/**"
        ],
        commit_prefix="api:",
        allowed_tools=["Read", "Edit", "Bash", "Glob", "Grep"]
    ),
    Domain.SCHED: DomainConfig(
        name=Domain.SCHED,
        allowed_paths=["backend/app/scheduling/**"],
        forbidden_paths=[
            "backend/app/models/**",
            "backend/app/api/**",
            "frontend/**"
        ],
        commit_prefix="sched:",
        allowed_tools=["Read", "Edit", "Bash", "Glob", "Grep"]
    ),
    Domain.FE: DomainConfig(
        name=Domain.FE,
        allowed_paths=[
            "frontend/src/**",
            "frontend/public/**"
        ],
        forbidden_paths=[
            "backend/**",
            "frontend/__tests__/**"
        ],
        commit_prefix="fe:",
        allowed_tools=["Read", "Edit", "Bash", "Glob", "Grep"]
    ),
    Domain.TEST: DomainConfig(
        name=Domain.TEST,
        allowed_paths=[
            "backend/tests/**",
            "frontend/__tests__/**",
            "docs/**"
        ],
        forbidden_paths=[
            "backend/app/**",
            "frontend/src/**"
        ],
        commit_prefix="test:",
        allowed_tools=["Read", "Edit", "Bash", "Glob", "Grep"]
    )
}
```

```python
# .antigravity/orchestrator/kinase.py
"""
Phase 2: 8-Lane Kinase Loop
Parallel agent execution with domain isolation.
"""
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Awaitable

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher

from .minimal import MinimalOrchestrator, TaskResult
from .domains import Domain, DomainConfig, DOMAIN_CONFIGS


class LaneState(Enum):
    """State machine for each lane."""
    IDLE = "idle"
    CLAIMED = "claimed"
    ACTIVE = "active"
    PR_OPEN = "pr_open"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Lane:
    """Single processing lane."""
    id: int
    state: LaneState = LaneState.IDLE
    current_task: str | None = None
    domain: Domain | None = None
    started_at: datetime | None = None
    result: TaskResult | None = None


@dataclass
class Task:
    """Task to be processed by a lane."""
    id: str
    prompt: str
    domain: Domain
    task_type: str  # REFACTOR, TEST, TOOL
    dependencies: list[str] = field(default_factory=list)
    priority: int = 1


class KinaseLoop:
    """
    8-Lane parallel processing inspired by enzyme kinase cascades.

    Replaces: 8 browser tabs managed by Comet
    With: 8 async SDK clients with proper isolation
    """

    def __init__(self, num_lanes: int = 8):
        self.lanes = [Lane(id=i) for i in range(num_lanes)]
        self.task_queue: list[Task] = []
        self.completed: dict[str, TaskResult] = {}
        self._lock = asyncio.Lock()
        self._orchestrator = MinimalOrchestrator()

    def _get_affinity_lanes(self, task_type: str) -> list[int]:
        """
        Affinity-based lane assignment.
        From your pseudocode in SESSION_13_PROTOCOL.md
        """
        affinity_map = {
            "REFACTOR": [0, 1, 2, 3, 4],  # Lanes 1-5
            "TEST": [5, 6],                # Lanes 6-7
            "TOOL": [7]                    # Lane 8
        }
        return affinity_map.get(task_type, list(range(8)))

    async def claim_lane(self, task: Task) -> Lane | None:
        """
        Attempt to claim an idle lane for a task.
        Returns None if backpressure (all lanes busy).
        """
        async with self._lock:
            preferred_lanes = self._get_affinity_lanes(task.task_type)

            # Try preferred lanes first
            for lane_id in preferred_lanes:
                if self.lanes[lane_id].state == LaneState.IDLE:
                    self.lanes[lane_id].state = LaneState.CLAIMED
                    self.lanes[lane_id].current_task = task.id
                    self.lanes[lane_id].domain = task.domain
                    return self.lanes[lane_id]

            # Fall back to any idle lane
            for lane in self.lanes:
                if lane.state == LaneState.IDLE:
                    lane.state = LaneState.CLAIMED
                    lane.current_task = task.id
                    lane.domain = task.domain
                    return lane

            return None  # Backpressure

    def _create_domain_guardrail(self, domain: Domain) -> Callable:
        """
        Create a hook that enforces domain boundaries.
        Replaces: Manual file watching in Comet
        With: Programmatic PreToolUse hook
        """
        config = DOMAIN_CONFIGS[domain]

        async def guardrail_hook(input_data: dict, tool_use_id: str, context: dict):
            tool_name = input_data.get("tool_name", "")
            tool_input = input_data.get("tool_input", {})

            # Check Edit/Write operations
            if tool_name in ["Edit", "Write"]:
                file_path = tool_input.get("file_path", "")

                # Check forbidden paths
                for forbidden in config.forbidden_paths:
                    pattern = forbidden.replace("**", "").rstrip("/")
                    if pattern in file_path:
                        return {
                            "hookSpecificOutput": {
                                "permissionDecision": "deny",
                                "permissionDecisionReason": (
                                    f"Domain {domain.value} cannot edit {file_path}. "
                                    f"Create a HANDOFF request instead."
                                )
                            }
                        }

            return {"hookSpecificOutput": {"permissionDecision": "allow"}}

        return guardrail_hook

    async def run_in_lane(self, lane: Lane, task: Task) -> TaskResult:
        """
        Execute task in a specific lane with domain isolation.
        """
        lane.state = LaneState.ACTIVE
        lane.started_at = datetime.now()

        config = DOMAIN_CONFIGS[task.domain]

        # Build domain-specific system prompt
        domain_prompt = f"""
# Domain: {task.domain.value.upper()}

## Your Exclusive Territory
{chr(10).join(f'- {p}' for p in config.allowed_paths)}

## OFF LIMITS (create HANDOFF if needed)
{chr(10).join(f'- {p}' for p in config.forbidden_paths)}

## Commit Prefix
Use: `{config.commit_prefix} <message>`

## Rules
1. ONLY edit files in YOUR domain
2. If you need cross-domain changes, output:
   ```
   HANDOFF_REQUEST:
   - To: <target_domain>
   - File: <path>
   - Change: <description>
   - Blocking: Yes/No
   ```
3. Run tests before completing
"""

        options = ClaudeAgentOptions(
            allowed_tools=config.allowed_tools,
            working_directory=str(self._orchestrator.working_dir),
            append_system_prompt=domain_prompt + "\n\n" + self._orchestrator._load_skills(),
            hooks={
                "PreToolUse": [
                    HookMatcher(
                        matcher="Edit|Write",
                        hooks=[self._create_domain_guardrail(task.domain)]
                    )
                ]
            }
        )

        try:
            output_parts = []
            async with ClaudeSDKClient(options=options) as client:
                await client.query(task.prompt)
                async for message in client.receive_response():
                    output_parts.append(str(message))

            result = TaskResult(
                task_id=task.id,
                success=True,
                output="\n".join(output_parts),
                duration_seconds=(datetime.now() - lane.started_at).total_seconds()
            )

        except Exception as e:
            result = TaskResult(
                task_id=task.id,
                success=False,
                output="",
                duration_seconds=(datetime.now() - lane.started_at).total_seconds(),
                error=str(e)
            )

        lane.state = LaneState.COMPLETED
        lane.result = result
        self.completed[task.id] = result

        return result

    async def run_parallel(self, tasks: list[Task]) -> dict[str, TaskResult]:
        """
        Execute multiple tasks in parallel across lanes.

        Respects:
        - Domain isolation
        - Task dependencies
        - Lane affinity
        - Backpressure (queuing when full)
        """
        # Separate by dependencies
        ready = [t for t in tasks if not t.dependencies]
        pending = [t for t in tasks if t.dependencies]

        results = {}

        # Process ready tasks in parallel
        async def process_task(task: Task):
            lane = await self.claim_lane(task)
            while lane is None:
                await asyncio.sleep(2)  # Backpressure wait
                lane = await self.claim_lane(task)

            result = await self.run_in_lane(lane, task)

            # Release lane
            async with self._lock:
                lane.state = LaneState.IDLE
                lane.current_task = None
                lane.domain = None

            return result

        # Run ready tasks
        ready_results = await asyncio.gather(
            *[process_task(t) for t in ready],
            return_exceptions=True
        )

        for task, result in zip(ready, ready_results):
            if isinstance(result, Exception):
                results[task.id] = TaskResult(
                    task_id=task.id,
                    success=False,
                    output="",
                    duration_seconds=0,
                    error=str(result)
                )
            else:
                results[task.id] = result

        # Process pending tasks (dependencies resolved)
        for task in pending:
            deps_met = all(
                task_id in results and results[task_id].success
                for task_id in task.dependencies
            )

            if deps_met:
                result = await process_task(task)
                results[task.id] = result
            else:
                results[task.id] = TaskResult(
                    task_id=task.id,
                    success=False,
                    output="",
                    duration_seconds=0,
                    error="Dependencies not met"
                )

        return results

    def get_status(self) -> dict:
        """Get current lane status (for monitoring)."""
        return {
            "lanes": [
                {
                    "id": lane.id,
                    "state": lane.state.value,
                    "task": lane.current_task,
                    "domain": lane.domain.value if lane.domain else None
                }
                for lane in self.lanes
            ],
            "queue_depth": len(self.task_queue),
            "completed": len(self.completed)
        }


async def demo():
    """Demo the kinase loop with parallel tasks."""
    kinase = KinaseLoop(num_lanes=8)

    tasks = [
        Task(
            id="A01",
            prompt="Review the PeopleService in backend/app/services/people.py",
            domain=Domain.API,
            task_type="REFACTOR"
        ),
        Task(
            id="A02",
            prompt="Review the ScheduleService in backend/app/services/schedule.py",
            domain=Domain.API,
            task_type="REFACTOR"
        ),
        Task(
            id="B01",
            prompt="Check test coverage for backend/tests/services/",
            domain=Domain.TEST,
            task_type="TEST",
            dependencies=["A01"]
        ),
    ]

    print("Starting parallel execution...")
    print(f"Status: {kinase.get_status()}")

    results = await kinase.run_parallel(tasks)

    print("\nResults:")
    for task_id, result in results.items():
        status = "✅" if result.success else "❌"
        print(f"  {status} {task_id}: {result.duration_seconds:.1f}s")


if __name__ == "__main__":
    asyncio.run(demo())
```

### Validation Criteria
- [ ] 8 lanes can run concurrently
- [ ] Domain guardrails block cross-territory edits
- [ ] Affinity routing works (REFACTOR → lanes 1-5)
- [ ] Backpressure queues tasks when lanes full
- [ ] Dependencies respected

---

## Phase 3: Dual-Nucleus Architecture

**Goal:** Synthesis (code gen) + DNA Repair (adversarial review)

### Deliverables

```
.antigravity/
└── orchestrator/
    ├── __init__.py
    ├── minimal.py           # Phase 1
    ├── kinase.py            # Phase 2
    ├── domains.py
    ├── nucleus.py           # Phase 3: Dual nucleus
    └── prompts/
        ├── synthesis.md     # PROMPT A
        └── adversarial.md   # PROMPT B
```

### Implementation

```python
# .antigravity/orchestrator/nucleus.py
"""
Phase 3: Dual-Nucleus Architecture
Synthesis (code generation) + DNA Repair (adversarial review)
"""
import asyncio
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

from .kinase import KinaseLoop, Task
from .domains import Domain


class ReviewSeverity(Enum):
    """Severity levels for review findings."""
    CRITICAL = "critical"  # Must fix before merge
    HIGH = "high"          # Should fix before merge
    MEDIUM = "medium"      # Consider fixing
    LOW = "low"            # Nice to have


@dataclass
class ReviewFinding:
    """Single finding from DNA Repair review."""
    severity: ReviewSeverity
    title: str
    location: str
    issue: str
    fix: str


@dataclass
class ReviewResult:
    """Complete review from DNA Repair nucleus."""
    approved: bool
    findings: list[ReviewFinding]
    summary: str


class DualNucleus:
    """
    Dual-nucleus pattern from Signal Transduction:

    1. Synthesis Nucleus (PROMPT A): Generate/refactor code
    2. DNA Repair Nucleus (PROMPT B): Adversarial security review

    Replaces: Claude Code tabs + ChatGPT Codex in separate browser
    With: Two SDK clients with specialized prompts
    """

    def __init__(self, working_dir: Path | None = None):
        self.working_dir = working_dir or Path.cwd()
        self.prompts_dir = self.working_dir / ".antigravity/orchestrator/prompts"

    def _load_prompt(self, name: str) -> str:
        """Load prompt from file."""
        prompt_file = self.prompts_dir / f"{name}.md"
        if prompt_file.exists():
            return prompt_file.read_text()
        return ""

    async def synthesis(
        self,
        task: str,
        domain: Domain,
        allowed_tools: list[str] | None = None
    ) -> str:
        """
        Synthesis Nucleus (PROMPT A): Code generation.

        This is the "Architect Mode" from your protocol.
        """
        if allowed_tools is None:
            allowed_tools = ["Read", "Edit", "Bash", "Glob", "Grep"]

        synthesis_prompt = self._load_prompt("synthesis")

        options = ClaudeAgentOptions(
            allowed_tools=allowed_tools,
            working_directory=str(self.working_dir),
            append_system_prompt=synthesis_prompt
        )

        output_parts = []
        async with ClaudeSDKClient(options=options) as client:
            await client.query(task)
            async for message in client.receive_response():
                output_parts.append(str(message))

        return "\n".join(output_parts)

    async def dna_repair(
        self,
        code_output: str,
        context: str = ""
    ) -> ReviewResult:
        """
        DNA Repair Nucleus (PROMPT B): Adversarial review.

        This replaces ChatGPT Codex doing security audits.
        Now it's another Claude instance with adversarial prompt.
        """
        adversarial_prompt = self._load_prompt("adversarial")

        # Read-only tools for review
        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Glob"],
            working_directory=str(self.working_dir),
            append_system_prompt=adversarial_prompt
        )

        review_task = f"""
# Code Review Request

## Context
{context}

## Code to Review
```
{code_output[:10000]}  # Truncate for context limits
```

## Your Task
1. Check for IDOR vulnerabilities
2. Check for N+1 query problems
3. Check for logic gaps
4. Check for security issues
5. Verify ACGME compliance (if applicable)

Output your findings in this format:
```
FINDING: [CRITICAL|HIGH|MEDIUM|LOW]
Title: <title>
Location: <file:line>
Issue: <description>
Fix: <recommendation>
```

End with:
```
VERDICT: [APPROVED|CHANGES_REQUESTED|BLOCKED]
SUMMARY: <one paragraph summary>
```
"""

        output_parts = []
        async with ClaudeSDKClient(options=options) as client:
            await client.query(review_task)
            async for message in client.receive_response():
                output_parts.append(str(message))

        review_output = "\n".join(output_parts)

        # Parse findings (simplified - real impl would be more robust)
        findings = []
        approved = "VERDICT: APPROVED" in review_output or "APPROVED" in review_output

        return ReviewResult(
            approved=approved,
            findings=findings,
            summary=review_output
        )

    async def synthesize_and_review(
        self,
        task: str,
        domain: Domain,
        require_approval: bool = True
    ) -> dict:
        """
        Full dual-nucleus cycle:
        1. Synthesis generates code
        2. DNA Repair reviews it
        3. If not approved and require_approval, synthesis must fix
        """
        # Phase 1: Synthesis
        synthesis_output = await self.synthesis(task, domain)

        # Phase 2: DNA Repair
        review = await self.dna_repair(
            synthesis_output,
            context=f"Task: {task}\nDomain: {domain.value}"
        )

        # Phase 3: Fix if needed
        if not review.approved and require_approval:
            fix_task = f"""
The following code review found issues that must be addressed:

## Original Task
{task}

## Review Findings
{review.summary}

## Your Task
Fix the issues identified in the review. Do not introduce new issues.
"""
            # Re-run synthesis with fix request
            fixed_output = await self.synthesis(fix_task, domain)

            # Re-review
            final_review = await self.dna_repair(
                fixed_output,
                context=f"Fix attempt for: {task}"
            )

            return {
                "synthesis": fixed_output,
                "review": final_review,
                "iterations": 2,
                "approved": final_review.approved
            }

        return {
            "synthesis": synthesis_output,
            "review": review,
            "iterations": 1,
            "approved": review.approved
        }


class SignalTransducer:
    """
    Complete Signal Transduction: Kinase + Dual Nucleus.

    This is the full orchestrator that replaces Comet.
    """

    def __init__(self, num_lanes: int = 8):
        self.kinase = KinaseLoop(num_lanes=num_lanes)
        self.nucleus = DualNucleus()

    async def transduce(self, tasks: list[Task]) -> dict:
        """
        Run full signal transduction cascade.

        For each task:
        1. Claim lane (kinase)
        2. Synthesis (nucleus)
        3. DNA Repair (nucleus)
        4. Release lane (kinase)
        """
        results = {}

        async def process_with_review(task: Task):
            # Run synthesis in lane
            lane = await self.kinase.claim_lane(task)
            while lane is None:
                await asyncio.sleep(2)
                lane = await self.kinase.claim_lane(task)

            try:
                result = await self.nucleus.synthesize_and_review(
                    task.prompt,
                    task.domain,
                    require_approval=True
                )
                return (task.id, result)
            finally:
                # Release lane
                async with self.kinase._lock:
                    lane.state = lane.state.IDLE

        # Process all tasks
        task_results = await asyncio.gather(
            *[process_with_review(t) for t in tasks],
            return_exceptions=True
        )

        for item in task_results:
            if isinstance(item, Exception):
                continue
            task_id, result = item
            results[task_id] = result

        return results
```

### Prompts

```markdown
<!-- .antigravity/orchestrator/prompts/synthesis.md -->
# PROMPT A: SYNTHESIS NUCLEUS - ARCHITECT MODE

## Role
You are a senior software architect performing autonomous repository refactoring.
Your task is to extract business logic from route handlers into dedicated service layers.

## Objectives
1. **Route Thinning**: Remove business logic from FastAPI route handlers
2. **Service Extraction**: Create dedicated service classes with proper dependency injection
3. **Test Generation**: Create comprehensive unit and integration tests
4. **PR Creation**: Commit, push, and create PR with proper documentation

## Patterns to Apply

### Service Layer Pattern
```python
# BEFORE: Fat route
@router.post("/people")
async def create_person(data: PersonCreate, db: Session = Depends(get_db)):
    person = Person(**data.dict())
    db.add(person)
    await db.commit()
    return person

# AFTER: Thin route + service
@router.post("/people")
async def create_person(
    data: PersonCreate,
    service: PeopleService = Depends()
):
    return await service.create_person(data)
```

## Constraints
- NEVER modify core infrastructure (config.py, security.py, session.py)
- NEVER break existing API contracts
- ALWAYS maintain backward compatibility
- ALWAYS run tests before committing
- ALWAYS include type hints and docstrings
```

```markdown
<!-- .antigravity/orchestrator/prompts/adversarial.md -->
# PROMPT B: DNA REPAIR NUCLEUS - ADVERSARIAL REVIEW MODE

## Role
You are a security-focused code reviewer performing adversarial analysis.
Your mission is to find bugs, security vulnerabilities, and logic gaps BEFORE merge.

## Audit Checklist

### 1. IDOR (Insecure Direct Object Reference)
- Does every endpoint verify the user has access to the requested resource?
- Are there organization/tenant boundaries being enforced?

### 2. N+1 Query Detection
- Are there loops that execute database queries?
- Is eager loading used where appropriate?

### 3. Logic Gap Identification
- Missing null checks?
- Unhandled edge cases?
- Race conditions in concurrent operations?

### 4. Security Bug Hunting
- SQL injection via raw queries?
- Command injection in subprocess calls?
- Path traversal in file operations?
- Secrets in code or logs?

### 5. ACGME Compliance (Medical Scheduling)
- Does this change affect the 80-hour work week calculation?
- Does this affect supervision ratio validation?
- Does this affect the 1-in-7 day off requirement?

## Adversarial Mindset
- Assume all input is malicious
- Assume network is hostile
- Assume database can be corrupted
- Assume users will find edge cases
- Assume attackers read the source code
```

### Validation Criteria
- [ ] Synthesis generates code successfully
- [ ] DNA Repair catches intentional bugs in test cases
- [ ] Full cycle completes (synthesis → review → fix → re-review)
- [ ] Prompts loaded from files correctly

---

## Phase 4: Full Signal Transduction

**Goal:** HANDOFF protocol, backpressure, recovery, observability

### Deliverables

```
.antigravity/
└── orchestrator/
    ├── __init__.py
    ├── minimal.py
    ├── kinase.py
    ├── domains.py
    ├── nucleus.py
    ├── handoff.py           # Phase 4: Cross-domain handoffs
    ├── recovery.py          # Phase 4: Failure recovery
    ├── transducer.py        # Phase 4: Full orchestrator
    ├── prompts/
    │   ├── synthesis.md
    │   └── adversarial.md
    └── requirements.txt
```

### Implementation Highlights

```python
# .antigravity/orchestrator/handoff.py
"""
Phase 4: HANDOFF Protocol for cross-domain dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .domains import Domain


class HandoffPriority(Enum):
    BLOCKING = "blocking"      # Source task cannot complete without this
    HIGH = "high"              # Should be done soon
    NORMAL = "normal"          # Can be batched


@dataclass
class Handoff:
    """Cross-domain dependency request."""
    id: str
    from_domain: Domain
    to_domain: Domain
    file_path: str
    change_description: str
    priority: HandoffPriority
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    source_task_id: str | None = None


class HandoffManager:
    """
    Manages cross-domain handoffs.

    When a domain agent needs changes outside its territory,
    it creates a handoff request instead of violating boundaries.
    """

    def __init__(self):
        self.pending: dict[Domain, list[Handoff]] = {d: [] for d in Domain}
        self.completed: list[Handoff] = []

    def create_handoff(
        self,
        from_domain: Domain,
        to_domain: Domain,
        file_path: str,
        change_description: str,
        priority: HandoffPriority = HandoffPriority.NORMAL,
        source_task_id: str | None = None
    ) -> Handoff:
        """Create a new handoff request."""
        handoff = Handoff(
            id=f"HO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{from_domain.value}-{to_domain.value}",
            from_domain=from_domain,
            to_domain=to_domain,
            file_path=file_path,
            change_description=change_description,
            priority=priority,
            source_task_id=source_task_id
        )

        self.pending[to_domain].append(handoff)
        return handoff

    def get_pending(self, domain: Domain) -> list[Handoff]:
        """Get all pending handoffs for a domain."""
        return sorted(
            self.pending[domain],
            key=lambda h: (h.priority.value, h.created_at)
        )

    def get_blocking(self, domain: Domain) -> list[Handoff]:
        """Get blocking handoffs that must be processed."""
        return [
            h for h in self.pending[domain]
            if h.priority == HandoffPriority.BLOCKING
        ]

    def complete_handoff(self, handoff_id: str):
        """Mark a handoff as completed."""
        for domain in Domain:
            for handoff in self.pending[domain]:
                if handoff.id == handoff_id:
                    handoff.completed_at = datetime.now()
                    self.pending[domain].remove(handoff)
                    self.completed.append(handoff)
                    return

    def to_markdown(self, domain: Domain) -> str:
        """Generate HANDOFF file content for a domain."""
        handoffs = self.get_pending(domain)
        if not handoffs:
            return ""

        lines = [f"# Pending Handoffs for {domain.value.upper()}\n"]

        for h in handoffs:
            lines.append(f"## {h.id}")
            lines.append(f"- **From:** {h.from_domain.value}")
            lines.append(f"- **Priority:** {h.priority.value}")
            lines.append(f"- **File:** `{h.file_path}`")
            lines.append(f"- **Change:** {h.change_description}")
            lines.append(f"- **Created:** {h.created_at.isoformat()}")
            lines.append("")

        return "\n".join(lines)
```

```python
# .antigravity/orchestrator/recovery.py
"""
Phase 4: Failure recovery and resilience.
"""
import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Awaitable


class FailureLevel(Enum):
    """Failure severity levels."""
    TRANSIENT = 1   # Retry immediately
    TEMPORARY = 2   # Retry with backoff
    PERSISTENT = 3  # Escalate to human
    FATAL = 4       # Stop everything


@dataclass
class RecoveryAction:
    """Action to take on failure."""
    level: FailureLevel
    retry_count: int = 0
    max_retries: int = 3
    backoff_seconds: float = 2.0
    escalation_message: str | None = None


class RecoveryManager:
    """
    Failure recovery inspired by your recovery.md.

    Handles:
    - Transient failures (network blips) → Immediate retry
    - Temporary failures (rate limits) → Exponential backoff
    - Persistent failures (logic errors) → Escalate
    - Fatal failures (security breach) → Stop
    """

    def __init__(self):
        self.failure_history: list[dict] = []
        self.escalations: list[str] = []

    def classify_failure(self, error: Exception) -> FailureLevel:
        """Classify failure severity based on error type."""
        error_str = str(error).lower()

        if "timeout" in error_str or "connection" in error_str:
            return FailureLevel.TRANSIENT
        elif "rate limit" in error_str or "429" in error_str:
            return FailureLevel.TEMPORARY
        elif "permission" in error_str or "forbidden" in error_str:
            return FailureLevel.PERSISTENT
        elif "security" in error_str or "breach" in error_str:
            return FailureLevel.FATAL
        else:
            return FailureLevel.TEMPORARY

    async def with_recovery(
        self,
        operation: Callable[[], Awaitable],
        task_id: str,
        max_retries: int = 3
    ):
        """
        Execute operation with automatic recovery.
        """
        action = RecoveryAction(
            level=FailureLevel.TRANSIENT,
            max_retries=max_retries
        )

        while action.retry_count <= action.max_retries:
            try:
                return await operation()

            except Exception as e:
                action.level = self.classify_failure(e)
                action.retry_count += 1

                self.failure_history.append({
                    "task_id": task_id,
                    "error": str(e),
                    "level": action.level.name,
                    "retry": action.retry_count,
                    "timestamp": datetime.now().isoformat()
                })

                if action.level == FailureLevel.FATAL:
                    self.escalations.append(
                        f"FATAL: {task_id} - {e}"
                    )
                    raise

                if action.level == FailureLevel.PERSISTENT:
                    if action.retry_count > action.max_retries:
                        self.escalations.append(
                            f"ESCALATION: {task_id} - {e}"
                        )
                        raise

                # Backoff
                wait_time = action.backoff_seconds * (2 ** (action.retry_count - 1))
                await asyncio.sleep(wait_time)

        raise RuntimeError(f"Max retries exceeded for {task_id}")
```

### Validation Criteria
- [ ] Handoffs created when domain boundary violated
- [ ] Blocking handoffs prevent task completion
- [ ] Transient failures retry automatically
- [ ] Persistent failures escalate
- [ ] Recovery history logged

---

## Phase 5: Production Hardening

**Goal:** Monitoring, observability, deployment

### Deliverables

```
.antigravity/
├── orchestrator/
│   ├── ...
│   ├── metrics.py           # Prometheus metrics
│   ├── health.py            # Health checks
│   └── api.py               # HTTP API (optional)
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── grafana/
│   └── dashboards/
│       └── orchestrator.json
└── README.md
```

### Key Additions

```python
# .antigravity/orchestrator/metrics.py
"""
Phase 5: Prometheus metrics for observability.
"""
from prometheus_client import Counter, Histogram, Gauge


# Counters
TASKS_TOTAL = Counter(
    'orchestrator_tasks_total',
    'Total tasks processed',
    ['domain', 'task_type', 'status']
)

HANDOFFS_TOTAL = Counter(
    'orchestrator_handoffs_total',
    'Total handoffs created',
    ['from_domain', 'to_domain', 'priority']
)

REVIEWS_TOTAL = Counter(
    'orchestrator_reviews_total',
    'Total DNA Repair reviews',
    ['approved', 'severity']
)

# Histograms
TASK_DURATION = Histogram(
    'orchestrator_task_duration_seconds',
    'Task execution duration',
    ['domain', 'task_type'],
    buckets=[10, 30, 60, 120, 300, 600]
)

# Gauges
LANES_ACTIVE = Gauge(
    'orchestrator_lanes_active',
    'Currently active lanes'
)

QUEUE_DEPTH = Gauge(
    'orchestrator_queue_depth',
    'Tasks waiting in queue'
)
```

```yaml
# .antigravity/docker/docker-compose.yml
version: '3.8'

services:
  orchestrator:
    build:
      context: ../..
      dockerfile: .antigravity/docker/Dockerfile
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - WORKING_DIR=/workspace
    volumes:
      - ../../:/workspace
    ports:
      - "8080:8080"  # API
      - "9090:9090"  # Metrics

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9091:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - ../grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3001:3000"
```

### Validation Criteria
- [ ] Prometheus metrics exposed on :9090
- [ ] Grafana dashboard shows lane utilization
- [ ] Health endpoint returns status
- [ ] Docker deployment works
- [ ] Logs structured (JSON)

---

## Migration Checklist

### From Comet → SDK

| Step | Comet (Before) | SDK (After) | Done |
|------|----------------|-------------|------|
| Agent start | Open browser tab | `ClaudeSDKClient()` | [ ] |
| Send prompt | Type in UI | `client.query(prompt)` | [ ] |
| Get response | Scrape DOM | `async for msg in client` | [ ] |
| Multiple agents | Multiple tabs | `asyncio.gather()` | [ ] |
| Domain isolation | File watching | `PreToolUse` hooks | [ ] |
| Error recovery | Manual refresh | `RecoveryManager` | [ ] |
| Handoffs | HANDOFF_*.md files | `HandoffManager` | [ ] |
| Status monitoring | Visual inspection | Prometheus metrics | [ ] |

### Feature Parity Matrix

| Feature | Comet | SDK | Phase |
|---------|-------|-----|-------|
| Single task | ✅ | ✅ | 1 |
| 8 parallel lanes | ✅ | ✅ | 2 |
| Domain isolation | ✅ | ✅ | 2 |
| Synthesis prompt | ✅ | ✅ | 3 |
| Adversarial review | ✅ (Codex) | ✅ (Claude) | 3 |
| Handoff protocol | ✅ | ✅ | 4 |
| Backpressure | ✅ | ✅ | 4 |
| Auto-recovery | ❌ | ✅ | 4 |
| Metrics | ❌ | ✅ | 5 |
| Health checks | ❌ | ✅ | 5 |
| Docker deploy | ❌ | ✅ | 5 |

---

## Success Metrics (Your SESSION_13 Benchmarks)

Target: Match or exceed Comet throughput

| Metric | Comet (Baseline) | SDK Target | Phase |
|--------|------------------|------------|-------|
| PRs/hour | 8 | 10+ | 4 |
| Memory usage | ~10GB | <1GB | 1 |
| Startup time | ~30s | <5s | 1 |
| Recovery time | Manual | <30s | 4 |
| Lane utilization | ~70% | >85% | 5 |
| CI pass rate | 97% | >97% | 4 |
| Security findings caught | 5 | 5+ | 3 |

---

## Quick Start Commands

```bash
# Phase 1: Install and test minimal
cd /home/user/Autonomous-Assignment-Program-Manager
pip install claude-agent-sdk
python -c "from claude_agent_sdk import query; print('SDK installed')"

# Create orchestrator directory
mkdir -p .antigravity/orchestrator
touch .antigravity/orchestrator/__init__.py

# Test minimal orchestrator (after creating minimal.py)
python -m .antigravity.orchestrator.minimal

# Phase 2-5: Progressive implementation
# Follow the phase deliverables above
```

---

## Timeline Recommendation

| Phase | Complexity | Prerequisite |
|-------|------------|--------------|
| Phase 1 | Low | SDK access |
| Phase 2 | Medium | Phase 1 working |
| Phase 3 | Medium | Phase 2 working |
| Phase 4 | High | Phase 3 working |
| Phase 5 | Medium | Phase 4 working |

**Suggested approach:** Get Phase 1-2 working, then iterate on Phases 3-5 based on actual usage patterns.

---

*This roadmap transforms your Signal Transduction concept from browser automation into production-grade SDK orchestration.*
