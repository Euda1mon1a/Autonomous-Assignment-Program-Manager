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

---

## Phase 6: Exotic Pattern Integration (Advanced)

**Goal:** Leverage cross-disciplinary resilience patterns for orchestrator enhancement

### Discovery: The Exotic Resilience Library

The codebase contains a remarkable collection of cross-disciplinary resilience patterns. Each can be mapped to SDK orchestration challenges:

```
backend/app/resilience/
├── unified_critical_index.py   # Master integrator (N-1/Epi/Hub)
├── homeostasis.py              # Biological feedback loops
├── le_chatelier.py             # Chemical equilibrium shifts
├── creep_fatigue.py            # Materials science (Larson-Miller)
├── contagion_model.py          # SIS epidemiology
├── stigmergy.py                # Ant colony optimization
├── seismic_detection.py        # STA/LTA early warning
├── burnout_fire_index.py       # Forestry danger rating
├── transcription_factors.py    # Gene regulatory networks
├── thermodynamics/
│   ├── entropy.py              # Shannon entropy analysis
│   └── phase_transitions.py    # Critical phenomena detection
├── saga/
│   └── orchestrator.py         # Distributed transactions
└── retry/
    └── decorator.py            # Exponential backoff
```

### Integration Map: Exotic Patterns → SDK Orchestration

| Exotic Pattern | Origin Domain | Scheduling Use | **SDK Orchestration Use** |
|----------------|---------------|----------------|---------------------------|
| **Larson-Miller (Creep/Fatigue)** | Materials Science | Burnout prediction | Agent session fatigue tracking |
| **Shannon Entropy** | Information Theory | Schedule disorder | Task distribution balance across lanes |
| **Phase Transitions** | Statistical Physics | Early warning signals | Orchestrator failure prediction |
| **Transcription Factors** | Molecular Biology | Context-sensitive constraints | Dynamic task constraint activation |
| **SIS Contagion** | Epidemiology | Burnout spread | Error propagation modeling |
| **Le Chatelier** | Physical Chemistry | System stress response | Backpressure equilibrium shifts |
| **Homeostasis** | Physiology | Feedback loops | Lane health feedback control |
| **Stigmergy** | Entomology | Preference optimization | Task routing preference trails |
| **STA/LTA Seismic** | Geophysics | Burnout precursors | Orchestrator instability detection |
| **Unified Critical Index** | Novel (Cross-domain) | Faculty risk aggregation | Lane/agent criticality assessment |

### Implementation: Entropy-Based Task Distribution

```python
# .antigravity/orchestrator/entropy_monitor.py
"""
Apply Shannon entropy analysis to task distribution across lanes.

High entropy → Tasks evenly distributed (good)
Low entropy → Tasks concentrated in few lanes (bottleneck risk)
"""
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LaneEntropyMetrics:
    """Entropy analysis of task distribution across lanes."""
    lane_entropy: float           # Shannon entropy of task distribution
    normalized_entropy: float     # 0-1 (1 = perfectly balanced)
    max_lane_load: int           # Highest task count on any lane
    min_lane_load: int           # Lowest task count
    imbalance_ratio: float       # max/min load ratio
    recommendation: str          # Action recommendation


def calculate_lane_entropy(lane_tasks: dict[int, int]) -> LaneEntropyMetrics:
    """
    Calculate Shannon entropy of task distribution.

    Args:
        lane_tasks: Dictionary of lane_id → task_count

    Returns:
        LaneEntropyMetrics with entropy analysis
    """
    total_tasks = sum(lane_tasks.values())
    if total_tasks == 0:
        return LaneEntropyMetrics(
            lane_entropy=0.0,
            normalized_entropy=1.0,
            max_lane_load=0,
            min_lane_load=0,
            imbalance_ratio=1.0,
            recommendation="System idle - no tasks"
        )

    # Calculate probabilities
    probabilities = [count / total_tasks for count in lane_tasks.values() if count > 0]

    # Shannon entropy: H = -Σ p(i) * log2(p(i))
    entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)

    # Maximum entropy for uniform distribution
    max_entropy = math.log2(len(lane_tasks)) if lane_tasks else 1.0

    # Normalized (0-1 scale)
    normalized = entropy / max_entropy if max_entropy > 0 else 1.0

    loads = list(lane_tasks.values())
    max_load = max(loads) if loads else 0
    min_load = min(loads) if loads else 0

    # Generate recommendation
    if normalized > 0.9:
        recommendation = "Excellent - tasks well distributed"
    elif normalized > 0.7:
        recommendation = "Good - minor imbalance"
    elif normalized > 0.5:
        recommendation = "Warning - consider rebalancing"
    else:
        recommendation = "Critical - severe concentration risk"

    return LaneEntropyMetrics(
        lane_entropy=entropy,
        normalized_entropy=normalized,
        max_lane_load=max_load,
        min_lane_load=min_load,
        imbalance_ratio=max_load / min_load if min_load > 0 else float('inf'),
        recommendation=recommendation
    )


class OrchestratorEntropyMonitor:
    """
    Real-time entropy monitoring for lane health.

    Integrates with KinaseLoop to detect task concentration issues
    before they cause cascade failures.
    """

    def __init__(self, num_lanes: int = 8, history_window: int = 50):
        self.num_lanes = num_lanes
        self.history_window = history_window
        self.entropy_history: list[float] = []
        self.timestamp_history: list[datetime] = []

    def update(self, lane_tasks: dict[int, int]) -> LaneEntropyMetrics:
        """Update with current lane task counts."""
        metrics = calculate_lane_entropy(lane_tasks)

        self.entropy_history.append(metrics.normalized_entropy)
        self.timestamp_history.append(datetime.now())

        # Trim history
        if len(self.entropy_history) > self.history_window:
            self.entropy_history.pop(0)
            self.timestamp_history.pop(0)

        return metrics

    def detect_critical_slowing(self) -> bool:
        """
        Detect critical slowing down in entropy dynamics.

        Near phase transitions, entropy changes slow down as system
        explores many configurations. High autocorrelation + low
        rate of change = approaching instability.
        """
        if len(self.entropy_history) < 10:
            return False

        recent = self.entropy_history[-10:]

        # Calculate autocorrelation at lag=1
        mean = sum(recent) / len(recent)
        c0 = sum((v - mean) ** 2 for v in recent)

        if c0 == 0:
            return False

        c1 = sum((recent[i] - mean) * (recent[i+1] - mean)
                 for i in range(len(recent) - 1))
        autocorr = c1 / c0

        # Rate of change
        rate = abs(recent[-1] - recent[0]) / len(recent)

        # Critical slowing: high autocorrelation + low rate
        return autocorr > 0.8 and rate < 0.05
```

### Implementation: Creep-Fatigue for Agent Sessions

```python
# .antigravity/orchestrator/session_fatigue.py
"""
Apply Larson-Miller parameter to track agent session fatigue.

Long sessions with high task load accumulate "creep damage" like
materials under sustained stress. Prevents session exhaustion.
"""
import math
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SessionFatigueMetrics:
    """Fatigue analysis for an agent session."""
    session_id: str
    duration_minutes: float
    task_count: int
    larson_miller_parameter: float  # LMP value
    fatigue_stage: str              # PRIMARY, SECONDARY, TERTIARY
    recommended_action: str


# Constants from materials science (calibrated for agent sessions)
LMP_CONSTANT = 20.0            # Larson-Miller constant
SAFE_LMP = 31.5                # 70% of failure threshold
FAILURE_THRESHOLD = 45.0       # Session should end


def calculate_session_fatigue(
    session_id: str,
    started_at: datetime,
    task_count: int,
    now: datetime | None = None
) -> SessionFatigueMetrics:
    """
    Calculate session fatigue using Larson-Miller parameter.

    LMP = workload_fraction * (base + multiplier * log10(duration))

    Theory:
    - Short high-intensity sessions: acceptable
    - Long high-intensity sessions: fatigue accumulates non-linearly
    - The log10(duration) captures time-temperature analogy from materials
    """
    now = now or datetime.now()
    duration_minutes = (now - started_at).total_seconds() / 60

    # Prevent log(0)
    if duration_minutes < 1:
        duration_minutes = 1

    # Normalize workload (assume 5 tasks/hour is baseline)
    tasks_per_hour = (task_count / duration_minutes) * 60
    workload_fraction = min(1.0, tasks_per_hour / 5.0)

    # Larson-Miller calculation
    base = LMP_CONSTANT / 2.0
    multiplier = LMP_CONSTANT * 1.25
    lmp = workload_fraction * (base + multiplier * math.log10(duration_minutes))

    # Determine fatigue stage
    lmp_ratio = lmp / FAILURE_THRESHOLD

    if lmp_ratio < 0.3:
        stage = "PRIMARY"
        action = "Continue - session healthy"
    elif lmp_ratio < 0.6:
        stage = "SECONDARY"
        action = "Monitor - steady state fatigue"
    elif lmp_ratio < 0.85:
        stage = "TERTIARY"
        action = "Warning - consider session refresh"
    else:
        stage = "FAILURE_IMMINENT"
        action = "CRITICAL - refresh session immediately"

    return SessionFatigueMetrics(
        session_id=session_id,
        duration_minutes=duration_minutes,
        task_count=task_count,
        larson_miller_parameter=lmp,
        fatigue_stage=stage,
        recommended_action=action
    )


class SessionFatigueMonitor:
    """
    Monitor fatigue across all active agent sessions.

    Triggers session refresh before failures occur.
    """

    def __init__(self, sessions: dict[str, datetime] | None = None):
        self.sessions: dict[str, datetime] = sessions or {}
        self.task_counts: dict[str, int] = {}

    def start_session(self, session_id: str):
        """Register a new agent session."""
        self.sessions[session_id] = datetime.now()
        self.task_counts[session_id] = 0

    def record_task(self, session_id: str):
        """Record a task completion for a session."""
        self.task_counts[session_id] = self.task_counts.get(session_id, 0) + 1

    def get_fatigue(self, session_id: str) -> SessionFatigueMetrics | None:
        """Get fatigue metrics for a session."""
        if session_id not in self.sessions:
            return None

        return calculate_session_fatigue(
            session_id=session_id,
            started_at=self.sessions[session_id],
            task_count=self.task_counts.get(session_id, 0)
        )

    def get_sessions_needing_refresh(self) -> list[str]:
        """Get sessions that should be refreshed."""
        needing_refresh = []

        for session_id in self.sessions:
            metrics = self.get_fatigue(session_id)
            if metrics and metrics.fatigue_stage in ("TERTIARY", "FAILURE_IMMINENT"):
                needing_refresh.append(session_id)

        return needing_refresh
```

### Implementation: Transcription Factor Task Constraints

```python
# .antigravity/orchestrator/constraint_regulation.py
"""
Apply gene regulatory network concepts to task constraints.

Constraints are "genes" that can be activated/repressed based on
context "transcription factors". Enables context-sensitive behavior.
"""
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class TFType(Enum):
    """Transcription factor types."""
    ACTIVATOR = "activator"       # Turns on constraints
    REPRESSOR = "repressor"       # Turns off constraints
    DUAL = "dual"                 # Can do both
    MASTER = "master"             # Always active, controls others


class BindingLogic(Enum):
    """How multiple TFs combine."""
    AND = "and"           # All must be active
    OR = "or"             # Any one active
    MAJORITY = "majority" # >50% active
    THRESHOLD = "threshold"  # Sum of strengths > threshold


@dataclass
class TranscriptionFactor:
    """A regulatory factor that controls constraint activation."""
    id: str
    name: str
    tf_type: TFType
    basal_expression: float = 0.0     # Default activity level
    current_expression: float = 0.0   # Current activity
    activation_strength: float = 1.0  # How strongly it activates
    repression_strength: float = 0.5  # How strongly it represses


@dataclass
class RegulatedConstraint:
    """A constraint regulated by transcription factors."""
    id: str
    name: str
    description: str
    activators: list[str] = field(default_factory=list)   # TF IDs that activate
    repressors: list[str] = field(default_factory=list)   # TF IDs that repress
    binding_logic: BindingLogic = BindingLogic.AND
    current_state: float = 1.0  # 0=fully off, 1=fully on


class ConstraintRegulator:
    """
    Regulate task constraints using transcription factor model.

    Use cases for SDK orchestration:
    - Activate strict mode during review phases
    - Repress verbose logging during batch processing
    - Enable cross-domain access during emergencies
    - Enforce serial execution when detecting conflicts
    """

    def __init__(self):
        self.transcription_factors: dict[str, TranscriptionFactor] = {}
        self.constraints: dict[str, RegulatedConstraint] = {}
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initialize default TFs for SDK orchestration."""
        # Master regulators (always active)
        self.transcription_factors["Safety_MR"] = TranscriptionFactor(
            id="Safety_MR",
            name="Safety Master Regulator",
            tf_type=TFType.MASTER,
            basal_expression=1.0,
            current_expression=1.0
        )

        # Context-sensitive TFs
        self.transcription_factors["CrisisMode_TF"] = TranscriptionFactor(
            id="CrisisMode_TF",
            name="Crisis Mode",
            tf_type=TFType.DUAL,
            basal_expression=0.0,
            activation_strength=2.0,
            repression_strength=0.8
        )

        self.transcription_factors["BatchMode_TF"] = TranscriptionFactor(
            id="BatchMode_TF",
            name="Batch Processing Mode",
            tf_type=TFType.REPRESSOR,
            basal_expression=0.0,
            repression_strength=0.7
        )

        self.transcription_factors["ReviewPhase_TF"] = TranscriptionFactor(
            id="ReviewPhase_TF",
            name="Review Phase",
            tf_type=TFType.ACTIVATOR,
            basal_expression=0.0,
            activation_strength=1.5
        )

    def induce_tf(self, tf_id: str, strength: float = 1.0):
        """Induce (activate) a transcription factor."""
        if tf_id in self.transcription_factors:
            tf = self.transcription_factors[tf_id]
            tf.current_expression = min(1.0, tf.basal_expression + strength)

    def suppress_tf(self, tf_id: str, strength: float = 1.0):
        """Suppress (deactivate) a transcription factor."""
        if tf_id in self.transcription_factors:
            tf = self.transcription_factors[tf_id]
            tf.current_expression = max(0.0, tf.current_expression - strength)

    def add_constraint(
        self,
        constraint_id: str,
        name: str,
        description: str,
        activators: list[str] | None = None,
        repressors: list[str] | None = None
    ):
        """Add a regulated constraint."""
        self.constraints[constraint_id] = RegulatedConstraint(
            id=constraint_id,
            name=name,
            description=description,
            activators=activators or [],
            repressors=repressors or []
        )

    def evaluate_constraint(self, constraint_id: str) -> float:
        """
        Evaluate current state of a constraint.

        Returns 0.0-1.0 based on TF activity.
        """
        if constraint_id not in self.constraints:
            return 1.0  # Default: enabled

        constraint = self.constraints[constraint_id]

        # Calculate activation signal
        activation = 0.0
        for tf_id in constraint.activators:
            if tf_id in self.transcription_factors:
                tf = self.transcription_factors[tf_id]
                activation += tf.current_expression * tf.activation_strength

        # Calculate repression signal
        repression = 0.0
        for tf_id in constraint.repressors:
            if tf_id in self.transcription_factors:
                tf = self.transcription_factors[tf_id]
                repression += tf.current_expression * tf.repression_strength

        # Net effect (activation - repression), clamped to 0-1
        constraint.current_state = max(0.0, min(1.0, 0.5 + activation - repression))

        return constraint.current_state

    def is_constraint_active(self, constraint_id: str, threshold: float = 0.5) -> bool:
        """Check if constraint is effectively active."""
        return self.evaluate_constraint(constraint_id) >= threshold
```

### Validation Criteria (Phase 6)
- [ ] Entropy monitor detects task concentration issues
- [ ] Session fatigue triggers before failures
- [ ] Constraint regulator responds to context changes
- [ ] Integration with KinaseLoop working
- [ ] Metrics exposed for all exotic patterns

---

## Phase 7: Potential Explorations

**Goal:** Document advanced concepts for future development

### 7.1 Unified Orchestrator Critical Index (Novel)

Adapt the `UnifiedCriticalIndex` from faculty risk to orchestrator health:

```
┌─────────────────────────────────────────────────────────────────┐
│              UNIFIED ORCHESTRATOR CRITICAL INDEX                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Domain 1: Lane Contingency (N-1/N-2)                          │
│   ├─ Which lanes can fail without cascade?                      │
│   ├─ Single points of failure in domain coverage?              │
│   └─ Maps to: backend/app/resilience/contingency.py            │
│                                                                 │
│   Domain 2: Task Contagion (Epidemiology)                       │
│   ├─ Do failed tasks spread to other lanes?                     │
│   ├─ Which tasks are "super-spreaders" of errors?              │
│   └─ Maps to: backend/app/resilience/contagion_model.py        │
│                                                                 │
│   Domain 3: Lane Hub Analysis (Network)                         │
│   ├─ Which lanes are most interconnected?                       │
│   ├─ What's the handoff dependency graph topology?             │
│   └─ Maps to: backend/app/resilience/hub_analysis.py           │
│                                                                 │
│   CROSS-DOMAIN PATTERNS:                                        │
│   ├─ All 3 high: CRITICAL - orchestrator at risk               │
│   ├─ Contingency + Hub: Structural vulnerability               │
│   ├─ Contagion + Hub: Error amplification risk                 │
│   └─ Single domain: Targeted intervention                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Phase Transition Early Warning

Adapt the `PhaseTransitionDetector` to predict orchestrator failures:

**Signals to monitor:**
1. **Increasing Variance**: Lane completion times becoming erratic
2. **Autocorrelation**: Tasks taking longer after previous slow tasks
3. **Flickering**: Lanes rapidly switching between active/error states
4. **Skewness**: Distribution of task durations becoming asymmetric

**Implementation hook:**
```python
# In Phase 5 metrics.py, add:
from backend.app.resilience.thermodynamics.phase_transitions import PhaseTransitionDetector

class OrchestratorPhaseMonitor:
    def __init__(self):
        self.detector = PhaseTransitionDetector(window_size=50)

    def update(self, metrics: dict[str, float]):
        # Feed orchestrator metrics to detector
        self.detector.update({
            "lane_completion_time": metrics.get("avg_task_duration"),
            "error_rate": metrics.get("error_rate"),
            "queue_depth": metrics.get("queue_depth"),
            "entropy": metrics.get("task_entropy")
        })

    def check_early_warnings(self) -> dict:
        risk = self.detector.detect_critical_phenomena()
        return {
            "severity": risk.overall_severity.value,
            "signals": len(risk.signals),
            "time_to_transition": risk.time_to_transition,
            "recommendations": risk.recommendations
        }
```

### 7.3 Le Chatelier Backpressure Equilibrium

When the system is stressed (queue depth increases), Le Chatelier's principle tells us the system will naturally compensate, but only partially:

```python
# Stress response mapping for orchestrator:
STRESS_RESPONSES = {
    "queue_buildup": {
        "stress_type": "DEMAND_SURGE",
        "natural_compensation": 0.30,  # 30% compensation from backpressure
        "interventions": [
            "spawn_additional_lanes",     # Increase capacity
            "defer_low_priority_tasks",   # Reduce demand
            "accept_new_equilibrium"      # Lower throughput is OK
        ]
    },
    "lane_failure": {
        "stress_type": "CAPACITY_LOSS",
        "natural_compensation": 0.25,  # Remaining lanes absorb ~25%
        "interventions": [
            "cross_domain_coverage",
            "activate_backup_lane",
            "reduce_parallelism"
        ]
    }
}
```

### 7.4 Stigmergy for Task Routing

Ant colony optimization for learning optimal task→lane routing:

```
┌─────────────────────────────────────────────────────────────────┐
│                    STIGMERGY TASK ROUTING                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Task Type: REFACTOR_API                                       │
│   ├─ Lane 1: ████████░░ 0.80 (strong preference)               │
│   ├─ Lane 2: █████░░░░░ 0.50 (moderate)                        │
│   ├─ Lane 3: ██░░░░░░░░ 0.20 (weak)                            │
│   └─ Lane 4: █░░░░░░░░░ 0.10 (avoid)                           │
│                                                                 │
│   Pheromone Rules:                                              │
│   ├─ Success: Deposit pheromone on (task_type, lane)           │
│   ├─ Failure: Evaporate pheromone                              │
│   ├─ Fast completion: Extra pheromone                          │
│   └─ Cross-pollination: Share learning across similar tasks    │
│                                                                 │
│   Over time:                                                    │
│   ├─ Optimal routes emerge from collective experience          │
│   ├─ New task types start with exploration                     │
│   └─ Stale routes decay (adapt to changes)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.5 Saga Pattern for Multi-Lane Transactions

When a task spans multiple domains and requires coordinated commits:

```python
# From backend/app/saga/orchestrator.py - adapt for SDK

class OrchestratorSaga:
    """
    Saga pattern for multi-domain task orchestration.

    When a task requires changes across CORE, API, and TEST domains,
    treat it as a distributed transaction with compensation.
    """

    async def execute_cross_domain_task(self, task: MultiDomainTask):
        completed_steps = []

        try:
            # Step 1: CORE domain changes
            core_result = await self.run_in_domain(Domain.CORE, task.core_prompt)
            completed_steps.append(("CORE", core_result))

            # Step 2: API domain changes
            api_result = await self.run_in_domain(Domain.API, task.api_prompt)
            completed_steps.append(("API", api_result))

            # Step 3: TEST domain changes
            test_result = await self.run_in_domain(Domain.TEST, task.test_prompt)
            completed_steps.append(("TEST", test_result))

            return SagaResult(success=True, steps=completed_steps)

        except Exception as e:
            # Compensation: Revert completed steps in reverse order
            for domain, result in reversed(completed_steps):
                await self.compensate(domain, result)

            return SagaResult(success=False, error=str(e), compensated=True)
```

### 7.6 STA/LTA Seismic Detection for Instability

Short-Term Average / Long-Term Average ratio detects sudden changes:

```python
# Seismic detection for orchestrator instability

def detect_instability(metric_history: list[float], sta_window: int = 5, lta_window: int = 20) -> dict:
    """
    STA/LTA algorithm from seismology.

    When short-term behavior diverges from long-term trend,
    something significant is happening.
    """
    if len(metric_history) < lta_window:
        return {"ratio": 1.0, "alert": False}

    sta = sum(metric_history[-sta_window:]) / sta_window
    lta = sum(metric_history[-lta_window:]) / lta_window

    ratio = sta / lta if lta > 0 else 1.0

    # Thresholds from seismology (calibrate for orchestrator)
    TRIGGER_ON = 2.5   # Start of event
    TRIGGER_OFF = 1.5  # End of event

    return {
        "ratio": ratio,
        "sta": sta,
        "lta": lta,
        "alert": ratio > TRIGGER_ON,
        "interpretation": (
            "INSTABILITY DETECTED" if ratio > TRIGGER_ON
            else "RECOVERING" if ratio > TRIGGER_OFF
            else "STABLE"
        )
    }
```

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                SDK ORCHESTRATOR + EXOTIC PATTERNS               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌───────────────────────────────────────────────────────────┐ │
│   │                    KINASE LOOP (Phase 2)                  │ │
│   │   Lane 1 ─┐                                               │ │
│   │   Lane 2 ─┼─► Entropy Monitor ───► Rebalance             │ │
│   │   ...     │   (Shannon)              Trigger              │ │
│   │   Lane 8 ─┘                                               │ │
│   └───────────────────────────────────────────────────────────┘ │
│                            │                                    │
│                            ▼                                    │
│   ┌───────────────────────────────────────────────────────────┐ │
│   │              SESSION MANAGER (Phase 6)                    │ │
│   │   ┌────────────┐  ┌────────────┐  ┌────────────┐          │ │
│   │   │ Session 1  │  │ Session 2  │  │ Session N  │          │ │
│   │   │ LMP: 28.5  │  │ LMP: 42.1  │  │ LMP: 15.2  │          │ │
│   │   │ PRIMARY    │  │ TERTIARY ⚠ │  │ PRIMARY    │          │ │
│   │   └────────────┘  └────────────┘  └────────────┘          │ │
│   │              Creep/Fatigue Monitor                        │ │
│   └───────────────────────────────────────────────────────────┘ │
│                            │                                    │
│                            ▼                                    │
│   ┌───────────────────────────────────────────────────────────┐ │
│   │            CONSTRAINT REGULATOR (Phase 6)                 │ │
│   │   Transcription Factors:                                  │ │
│   │   ├─ Safety_MR: ████████ 1.0 (always on)                 │ │
│   │   ├─ CrisisMode_TF: ░░░░░░░░ 0.0 (inactive)              │ │
│   │   ├─ BatchMode_TF: ████░░░░ 0.5 (partial)                │ │
│   │   └─ ReviewPhase_TF: ██████░░ 0.75 (active)              │ │
│   └───────────────────────────────────────────────────────────┘ │
│                            │                                    │
│                            ▼                                    │
│   ┌───────────────────────────────────────────────────────────┐ │
│   │              EARLY WARNING SYSTEM (Phase 7)               │ │
│   │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │
│   │   │ Phase Trans │  │  STA/LTA    │  │  Unified    │       │ │
│   │   │  Detector   │  │   Seismic   │  │   Index     │       │ │
│   │   │ Severity: ▲ │  │ Ratio: 1.2  │  │ Risk: 0.45  │       │ │
│   │   └─────────────┘  └─────────────┘  └─────────────┘       │ │
│   └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Priority Ranking for Exploration

| Exploration | Value | Complexity | Recommended |
|-------------|-------|------------|-------------|
| **Entropy Monitor** | High | Low | Phase 6.1 |
| **Session Fatigue** | High | Low | Phase 6.2 |
| **Constraint Regulator** | Medium | Medium | Phase 6.3 |
| **Phase Transition** | High | Medium | Phase 7.1 |
| **STA/LTA Seismic** | Medium | Low | Phase 7.2 |
| **Unified Index** | High | High | Phase 7.3 |
| **Stigmergy Routing** | Medium | High | Phase 7.4 |
| **Saga Transactions** | High | High | Phase 7.5 |

---

## Summary: The Exotic Pattern Library

The codebase contains an extraordinary collection of cross-disciplinary resilience patterns:

### Tier 1: Ready to Integrate (Phase 6)
| Pattern | Implementation | Lines | Readiness |
|---------|----------------|-------|-----------|
| Shannon Entropy | `thermodynamics/entropy.py` | 438 | ✅ Direct |
| Creep/Fatigue | `creep_fatigue.py` | 600+ | ✅ Direct |
| Transcription Factors | `transcription_factors.py` | 1300+ | ✅ Direct |
| Retry/Backoff | `retry/decorator.py` | 468 | ✅ Direct |

### Tier 2: Requires Adaptation (Phase 7)
| Pattern | Implementation | Adaptation Needed |
|---------|----------------|-------------------|
| Unified Critical Index | `unified_critical_index.py` | Faculty→Lane mapping |
| Phase Transitions | `thermodynamics/phase_transitions.py` | Schedule→Orchestrator metrics |
| SIS Contagion | `contagion_model.py` | Burnout→Error propagation |
| Homeostasis | `homeostasis.py` | Setpoints for orchestrator |

### Tier 3: Novel Research (Future)
| Pattern | Source | Novel Application |
|---------|--------|-------------------|
| Stigmergy | `stigmergy.py` | Task routing optimization |
| Le Chatelier | `le_chatelier.py` | Backpressure equilibrium |
| STA/LTA Seismic | `seismic_detection.py` | Instability detection |
| Saga Pattern | `saga/orchestrator.py` | Multi-domain transactions |

---

## Next Steps

1. **Phase 1-2**: Get basic SDK orchestration working
2. **Phase 3**: Add dual-nucleus review cycle
3. **Phase 4**: Implement handoffs and recovery
4. **Phase 5**: Production hardening with metrics
5. **Phase 6**: Integrate exotic patterns (entropy, fatigue, constraints)
6. **Phase 7**: Explore advanced patterns as needed

The exotic pattern library represents months of research into cross-disciplinary resilience. Leveraging it for SDK orchestration creates a uniquely robust system that draws from materials science, information theory, molecular biology, epidemiology, and physics.

---

## Appendix A: Complete Pattern Inventory (54 Modules)

### A.1 Pattern Categories

The resilience library contains **54+ modules** across **14 categories**. This appendix provides complete documentation for SDK orchestration integration.

```
backend/app/resilience/
├── Core Framework (5 modules)
│   ├── service.py                 # Main resilience service
│   ├── metrics.py                 # Prometheus metrics
│   ├── tasks.py                   # Celery background tasks
│   ├── utilization.py             # 80% threshold monitoring
│   └── __init__.py                # Package exports
│
├── Power Grid Patterns (4 modules)
│   ├── contingency.py             # N-1/N-2 analysis
│   ├── defense_in_depth.py        # 5-level safety tiers
│   ├── static_stability.py        # Pre-computed fallbacks
│   └── sacrifice_hierarchy.py     # Triage-based shedding
│
├── Network Analysis (3 modules)
│   ├── hub_analysis.py            # Centrality metrics (betweenness, degree)
│   ├── blast_radius.py            # Zone isolation (AWS-inspired)
│   └── behavioral_network.py      # Shadow org chart / COIN patterns
│
├── Epidemiology (2 modules)
│   ├── burnout_epidemiology.py    # SIR/SEIR burnout spread
│   └── contagion_model.py         # SIS network transmission
│
├── Thermodynamics (3 modules)
│   ├── thermodynamics/entropy.py          # Shannon entropy analysis
│   ├── thermodynamics/phase_transitions.py # Critical phenomena
│   └── thermodynamics/__init__.py
│
├── Materials Science (1 module)
│   └── creep_fatigue.py           # Larson-Miller parameter
│
├── Chemistry (1 module)
│   └── le_chatelier.py            # Equilibrium stress response
│
├── Biology (4 modules)
│   ├── homeostasis.py             # Negative/positive feedback
│   ├── transcription_factors.py   # Gene regulatory networks
│   ├── immune_system.py           # Negative selection / clonal selection
│   └── mtf_types.py               # Multi-transcription factor types
│
├── Psychology/Human Factors (2 modules)
│   ├── cognitive_load.py          # Decision fatigue / Miller's Law
│   └── equity_metrics.py          # Fairness measurement
│
├── Geophysics (1 module)
│   └── seismic_detection.py       # STA/LTA early warning
│
├── Forestry (2 modules)
│   ├── burnout_fire_index.py      # CFFDRS danger rating
│   └── burnout_fire_index_examples.py
│
├── Entomology (1 module)
│   └── stigmergy.py               # Ant colony optimization
│
├── Manufacturing (3 modules)
│   ├── spc_monitoring.py          # Western Electric rules
│   ├── process_capability.py      # Cp/Cpk Six Sigma
│   └── mtf_compliance.py          # MTF regulatory compliance
│
├── Telecommunications (1 module)
│   └── erlang_coverage.py         # Queuing theory
│
├── Fault Tolerance (12 modules)
│   ├── circuit_breaker/breaker.py     # State machine
│   ├── circuit_breaker/states.py      # Open/closed/half-open
│   ├── circuit_breaker/decorators.py  # Function wrappers
│   ├── circuit_breaker/registry.py    # Global registry
│   ├── circuit_breaker/monitoring.py  # Metrics
│   ├── circuit_breaker/__init__.py
│   ├── retry/decorator.py         # Exponential backoff
│   ├── retry/strategies.py        # Retry strategies
│   ├── retry/jitter.py            # Jitter algorithms
│   ├── retry/context.py           # Retry context
│   ├── retry/exceptions.py        # Custom exceptions
│   └── retry/__init__.py
│
├── Distributed Transactions (Saga)
│   └── saga/orchestrator.py       # Compensation patterns
│
├── Simulation Framework (6 modules)
│   ├── simulation/base.py             # SimPy environment
│   ├── simulation/events.py           # Event definitions
│   ├── simulation/metrics.py          # Simulation metrics
│   ├── simulation/n2_scenario.py      # N-2 failure scenarios
│   ├── simulation/cascade_scenario.py # Cascade simulation
│   ├── simulation/compound_stress_scenario.py
│   └── simulation/__init__.py
│
└── Cross-Domain Integrators (2 modules)
    ├── unified_critical_index.py  # N-1 + Epi + Hub fusion
    └── tier3_persistence.py       # Tier 3+ pattern storage
```

### A.2 New Pattern Mappings for SDK Orchestration

These patterns weren't covered in Phase 6-7 but have direct SDK applications:

#### A.2.1 Immune System Pattern → Anomaly Detection

```python
# SDK Application: Detect anomalous agent behavior without explicit rules

from dataclasses import dataclass
from typing import Any

@dataclass
class AgentDetector:
    """
    Negative selection detector for agent behavior.

    Trained on successful agent sessions to detect anomalies:
    - Unusual tool usage patterns
    - Abnormal response lengths
    - Unexpected error rates
    - Out-of-character domain access
    """
    center: list[float]  # Feature vector center
    radius: float        # Detection threshold

    def matches(self, agent_features: list[float]) -> bool:
        """Return True if agent behavior is anomalous."""
        distance = sum((a - b) ** 2 for a, b in zip(agent_features, self.center)) ** 0.5
        return distance > self.radius


class AgentImmuneSystem:
    """
    Self/Non-Self discrimination for agent orchestration.

    Use cases:
    - Detect compromised or misbehaving agents
    - Identify sessions that have "gone off track"
    - Auto-repair with clonal selection (choose best fix)
    """

    def __init__(self, detector_count: int = 50):
        self.detectors: list[AgentDetector] = []
        self.repair_antibodies: dict[str, callable] = {}

    def train_on_successful_sessions(self, session_features: list[list[float]]):
        """Generate detectors that DON'T match good sessions."""
        # Negative selection: any detector matching self is discarded
        pass

    def is_anomalous(self, current_features: list[float]) -> bool:
        """Check if current agent behavior is anomalous."""
        return any(d.matches(current_features) for d in self.detectors)

    def select_repair(self, anomaly_features: list[float]) -> callable:
        """Clonal selection: choose best repair for this anomaly type."""
        # Match antibody with highest affinity
        pass
```

#### A.2.2 Behavioral Network → Agent Power Dynamics

```python
# SDK Application: Detect informal patterns in agent interactions

from enum import Enum

class AgentRole(str, Enum):
    """Emergent roles from agent behavior patterns."""
    NEUTRAL = "neutral"        # Normal behavior
    WORKHORSE = "workhorse"    # Consistently handles most tasks
    SPECIALIST = "specialist"  # Excels in specific domains
    BOTTLENECK = "bottleneck"  # Tasks queue behind this agent
    COLLABORATOR = "collaborator"  # Frequently triggers handoffs
    ISOLATE = "isolate"        # Rarely interacts with others


class AgentBehavioralAnalysis:
    """
    Map the 'shadow org chart' of agent interactions.

    From COIN doctrine: formal assignment != actual influence
    From forensic accounting: activity != contribution

    Use cases:
    - Identify which agents are de facto critical (even if not assigned critical tasks)
    - Detect bottleneck agents that slow the system
    - Find collaboration patterns that emerge organically
    - Protect "workhorse" agents from overload
    """

    def __init__(self):
        self.task_history: dict[str, list[str]] = {}  # agent_id → task_ids
        self.handoff_graph: dict[tuple[str, str], int] = {}  # (from, to) → count
        self.burden_scores: dict[str, float] = {}

    def classify_agent_role(self, agent_id: str) -> AgentRole:
        """Determine agent's emergent behavioral role."""
        pass

    def get_shadow_criticality(self) -> dict[str, float]:
        """
        Calculate actual criticality from behavior (not assignment).

        An agent assigned to low-priority tasks but frequently needed
        for handoffs is actually more critical than assignments suggest.
        """
        pass
```

#### A.2.3 SPC Monitoring → Orchestrator Quality Control

```python
# SDK Application: Western Electric rules for orchestrator metrics

@dataclass
class OrchestratorControlChart:
    """
    Statistical Process Control for SDK orchestration.

    Western Electric Rules applied to orchestrator metrics:
    - Rule 1: 1 point beyond 3σ → CRITICAL (task duration spike)
    - Rule 2: 2/3 points beyond 2σ → WARNING (pattern shift)
    - Rule 3: 4/5 points beyond 1σ → WARNING (trending)
    - Rule 4: 8 consecutive same side → INFO (sustained shift)

    Metrics to monitor:
    - Task completion time
    - Error rate per lane
    - Handoff latency
    - Queue depth
    - Review iteration count
    """
    target: float          # Expected value (centerline)
    sigma: float           # Standard deviation
    history: list[float]   # Recent observations

    def check_rule_1(self) -> bool:
        """1 point beyond 3σ - process out of control."""
        if not self.history:
            return False
        return abs(self.history[-1] - self.target) > 3 * self.sigma

    def check_rule_4(self) -> bool:
        """8 consecutive points on same side - sustained shift."""
        if len(self.history) < 8:
            return False
        recent = self.history[-8:]
        above = all(v > self.target for v in recent)
        below = all(v < self.target for v in recent)
        return above or below

    def get_process_capability(self) -> float:
        """
        Calculate Cpk (process capability index).

        Cpk ≥ 1.33: Process is capable (4σ)
        Cpk ≥ 1.67: Process is highly capable (5σ)
        Cpk < 1.00: Process not capable, needs improvement
        """
        if len(self.history) < 2:
            return 0.0

        import statistics
        mean = statistics.mean(self.history)
        std = statistics.stdev(self.history)

        if std == 0:
            return float('inf')

        # Assuming spec limits at target ± 3σ
        usl = self.target + 3 * self.sigma
        lsl = self.target - 3 * self.sigma

        cpu = (usl - mean) / (3 * std)
        cpl = (mean - lsl) / (3 * std)

        return min(cpu, cpl)
```

#### A.2.4 Cognitive Load → Orchestrator Decision Management

```python
# SDK Application: Prevent decision fatigue in orchestrator

class OrchestratorDecisionManager:
    """
    Manage cognitive load in orchestrator decisions.

    Miller's Law: Working memory ~7±2 items
    Decision fatigue: Quality degrades after repeated decisions

    SDK Applications:
    - Batch similar lane assignments together
    - Provide safe defaults for common decisions
    - Limit cascading decisions in single cycle
    - Monitor decision quality over session
    """

    def __init__(self, max_decisions_per_cycle: int = 7):
        self.max_decisions = max_decisions_per_cycle
        self.decisions_this_cycle: int = 0
        self.safe_defaults: dict[str, any] = {}

    def should_use_default(self, decision_type: str) -> bool:
        """Check if we should use safe default to reduce load."""
        return (
            self.decisions_this_cycle >= self.max_decisions and
            decision_type in self.safe_defaults
        )

    def batch_similar_decisions(self, decisions: list[dict]) -> list[list[dict]]:
        """
        Group similar decisions to reduce context switching.

        Example: All "lane assignment" decisions together,
        then all "retry" decisions, then all "handoff" decisions.
        """
        batches: dict[str, list[dict]] = {}
        for d in decisions:
            dtype = d.get("type", "unknown")
            batches.setdefault(dtype, []).append(d)
        return list(batches.values())
```

### A.3 Simulation Framework for Orchestrator Testing

The `simulation/` subdirectory provides discrete-event simulation (SimPy) for testing orchestrator resilience:

```python
# SDK Application: Simulate orchestrator failure scenarios

from dataclasses import dataclass

@dataclass
class OrchestratorSimConfig:
    """Configuration for orchestrator simulation."""
    seed: int = 42
    duration_hours: int = 24
    lane_count: int = 8
    task_arrival_rate: float = 5.0  # tasks/hour
    lane_failure_probability: float = 0.01  # per hour
    recovery_time_minutes: float = 5.0


class OrchestratorSimulator:
    """
    SimPy-based discrete event simulation for SDK orchestrator.

    Scenarios available:
    1. N-2 Failure: Two lanes fail simultaneously
    2. Cascade: One failure triggers others
    3. Compound Stress: High load + failure
    4. Recovery: Test recovery time under various conditions
    """

    def run_n2_scenario(self, config: OrchestratorSimConfig):
        """Simulate N-2 lane failure."""
        pass

    def run_cascade_scenario(self, config: OrchestratorSimConfig):
        """Simulate cascade failure propagation."""
        pass

    def calculate_mttr(self) -> float:
        """Mean Time To Recovery."""
        pass

    def calculate_availability(self) -> float:
        """System availability percentage."""
        pass
```

---

## Appendix B: Pattern Cross-Reference Matrix

### B.1 Pattern Dependencies

Patterns often work together. This matrix shows which patterns enhance or depend on others:

```
                    │ UCI │ ENT │ HOM │ TF  │ SPC │ C/F │ IMM │ STG │
────────────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
Unified Crit Index  │  -  │  ↑  │  ↑  │     │  ↑  │     │     │     │
Entropy             │  ↓  │  -  │     │     │     │     │     │  ↑  │
Homeostasis         │  ↓  │     │  -  │  ↑  │     │     │     │     │
Transcription Fact  │     │     │  ↓  │  -  │     │     │     │     │
SPC Monitoring      │  ↓  │     │     │     │  -  │  ↑  │     │     │
Creep/Fatigue       │     │     │     │     │  ↓  │  -  │     │     │
Immune System       │     │     │     │     │     │     │  -  │     │
Stigmergy           │     │  ↓  │     │     │     │     │     │  -  │

Legend:
  ↑ = This pattern feeds data TO the column pattern
  ↓ = This pattern receives data FROM the column pattern
  (blank) = No direct dependency
```

### B.2 Recommended Integration Order

Based on dependencies, integrate patterns in this order:

```
Phase 1: Foundation Patterns (No dependencies)
├── Retry/Backoff (standalone)
├── Circuit Breaker (standalone)
└── Entropy Monitoring (standalone)

Phase 2: Feedback Patterns (Depend on Phase 1)
├── Homeostasis (uses Entropy for setpoint detection)
├── SPC Monitoring (uses Entropy for baseline)
└── Creep/Fatigue (uses metrics from Phase 1)

Phase 3: Regulatory Patterns (Depend on Phase 2)
├── Transcription Factors (uses Homeostasis signals)
├── Le Chatelier (uses SPC for stress detection)
└── Cognitive Load (uses fatigue signals)

Phase 4: Detection Patterns (Depend on Phase 2-3)
├── STA/LTA Seismic (uses SPC data streams)
├── Phase Transitions (uses Entropy + SPC)
└── Immune System (uses all baseline data)

Phase 5: Integration Patterns (Depend on all above)
├── Unified Critical Index (aggregates all signals)
├── Behavioral Network (long-term pattern analysis)
└── Stigmergy (emerges from usage patterns)
```

### B.3 Signal Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXOTIC PATTERN SIGNAL FLOW                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   RAW METRICS                                                               │
│   ┌─────────────┬─────────────┬─────────────┬─────────────┐                │
│   │ Task Times  │ Error Rates │ Queue Depth │ Lane States │                │
│   └──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┘                │
│          │             │             │             │                        │
│          ▼             ▼             ▼             ▼                        │
│   ┌─────────────────────────────────────────────────────────┐              │
│   │                  ENTROPY ANALYZER                        │              │
│   │   H = -Σ p(i) log₂ p(i)                                 │              │
│   │   Detects: Distribution imbalance, bottlenecks           │              │
│   └────────────────────────┬────────────────────────────────┘              │
│                            │                                                │
│          ┌─────────────────┼─────────────────┐                             │
│          ▼                 ▼                 ▼                             │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐                       │
│   │ HOMEOSTASIS│    │    SPC     │    │CREEP/FATIGUE│                      │
│   │ Setpoints  │    │ W.E. Rules │    │ Larson-Miller│                     │
│   │ Feedback   │    │ Control    │    │ Session LMP  │                     │
│   └─────┬──────┘    └─────┬──────┘    └──────┬──────┘                      │
│         │                 │                  │                              │
│         └────────┬────────┴────────┬─────────┘                             │
│                  ▼                 ▼                                        │
│         ┌─────────────┐    ┌─────────────┐                                 │
│         │TRANSCRIPTION│    │  STA/LTA    │                                 │
│         │  FACTORS    │    │  SEISMIC    │                                 │
│         │ Constraint  │    │  Detection  │                                 │
│         │ Activation  │    │             │                                 │
│         └──────┬──────┘    └──────┬──────┘                                 │
│                │                  │                                         │
│                └─────────┬────────┘                                         │
│                          ▼                                                  │
│            ┌───────────────────────────┐                                   │
│            │   UNIFIED CRITICAL INDEX  │                                   │
│            │   Aggregates all signals  │                                   │
│            │   Risk = f(N-1, Epi, Hub) │                                   │
│            └─────────────┬─────────────┘                                   │
│                          │                                                  │
│                          ▼                                                  │
│            ┌───────────────────────────┐                                   │
│            │     ACTION DECISIONS      │                                   │
│            ├───────────────────────────┤                                   │
│            │ • Scale lanes             │                                   │
│            │ • Refresh sessions        │                                   │
│            │ • Activate constraints    │                                   │
│            │ • Trigger circuit breaker │                                   │
│            │ • Queue rebalancing       │                                   │
│            └───────────────────────────┘                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix C: Quick Reference Guide

### C.1 Pattern Selection by Problem Type

| Problem | Best Pattern | Fallback | Phase |
|---------|--------------|----------|-------|
| **Lane overload** | Entropy | Utilization | 6 |
| **Session exhaustion** | Creep/Fatigue | Homeostasis | 6 |
| **Error spreading** | Contagion | Circuit Breaker | 7 |
| **Quality degradation** | SPC | Entropy | 7 |
| **Unpredictable failures** | Phase Transitions | STA/LTA | 7 |
| **Complex constraints** | Transcription Factors | - | 6 |
| **Backpressure buildup** | Le Chatelier | Queue monitoring | 7 |
| **Anomaly detection** | Immune System | SPC | 7 |
| **Optimal routing** | Stigmergy | Entropy | 7 |
| **Multi-domain tasks** | Saga | Handoff Manager | 7 |
| **Decision fatigue** | Cognitive Load | Batching | 7 |
| **System criticality** | Unified Index | N-1/N-2 | 7 |

### C.2 One-Line Pattern Summaries

```
ENTROPY:        "How evenly distributed are tasks across lanes?"
CREEP/FATIGUE:  "How tired is this session?"
HOMEOSTASIS:    "Are we deviating from healthy setpoints?"
SPC:            "Are metrics in statistical control?"
PHASE TRANS:    "Are we approaching a tipping point?"
TRANSCRIPTION:  "Which constraints should be active now?"
LE CHATELIER:   "How is the system compensating for stress?"
CONTAGION:      "Are errors spreading between agents?"
IMMUNE:         "Is this behavior anomalous?"
STIGMERGY:      "What routing has worked before?"
STA/LTA:        "Is something sudden happening?"
UNIFIED INDEX:  "What's the overall risk level?"
COGNITIVE:      "Are we making too many decisions?"
BEHAVIORAL:     "What informal patterns have emerged?"
SAGA:           "How do we handle multi-step failures?"
```

### C.3 Implementation Complexity Matrix

| Pattern | Lines | Dependencies | Test Coverage | Ready? |
|---------|-------|--------------|---------------|--------|
| Entropy | ~440 | numpy | High | ✅ |
| Creep/Fatigue | ~600 | numpy | High | ✅ |
| Homeostasis | ~400 | - | High | ✅ |
| Retry/Backoff | ~470 | - | High | ✅ |
| Circuit Breaker | ~800 | asyncio | High | ✅ |
| Transcription | ~1300 | - | Medium | ✅ |
| SPC Monitoring | ~400 | statistics | High | ⚡ |
| Contagion | ~600 | networkx | Medium | ⚡ |
| Phase Transitions | ~500 | scipy | Medium | ⚡ |
| Le Chatelier | ~350 | - | Medium | ⚡ |
| Unified Index | ~900 | networkx | Medium | ⚡ |
| Immune System | ~700 | numpy | Low | 🔬 |
| Stigmergy | ~500 | - | Low | 🔬 |
| Cognitive Load | ~450 | - | Low | 🔬 |
| Behavioral Net | ~600 | - | Low | 🔬 |
| Simulation | ~1500 | simpy | Medium | 🔬 |

Legend: ✅ Ready  ⚡ Needs Adaptation  🔬 Research Phase

---

## Appendix D: Pattern Integration Checklist

### D.1 Before Integrating Any Pattern

- [ ] Read the module docstring completely
- [ ] Understand the domain analogy (biology, physics, etc.)
- [ ] Identify input metrics needed
- [ ] Identify output actions possible
- [ ] Check dependencies (numpy, scipy, networkx, etc.)
- [ ] Review existing tests in `backend/tests/resilience/`

### D.2 Integration Template

```python
# Template for integrating any exotic pattern

from dataclasses import dataclass
from typing import Protocol

class PatternAdapter(Protocol):
    """Standard interface for exotic pattern adapters."""

    def update(self, metrics: dict[str, float]) -> None:
        """Feed new metrics to the pattern analyzer."""
        ...

    def check(self) -> dict:
        """Check pattern state, return recommendations."""
        ...

    def get_prometheus_metrics(self) -> list[tuple[str, float]]:
        """Export metrics for Prometheus."""
        ...


@dataclass
class PatternResult:
    """Standard result from any pattern check."""
    pattern_name: str
    severity: str  # "OK", "WARNING", "CRITICAL"
    message: str
    recommended_action: str | None
    confidence: float  # 0.0 - 1.0
    raw_data: dict
```

### D.3 Testing Integration

```bash
# Run existing resilience tests to ensure no regression
cd backend
pytest tests/resilience/ -v

# Run specific pattern tests
pytest tests/resilience/test_entropy.py -v
pytest tests/resilience/test_homeostasis.py -v
pytest tests/resilience/test_creep_fatigue.py -v
```

---

*This roadmap transforms your Signal Transduction concept from browser automation into production-grade SDK orchestration, enhanced with cross-disciplinary exotic patterns.*
