# Design: K2.5 Swarm MCP Integration

## Overview

Add MCP tools to spawn Kimi K2.5 Agent Swarm tasks for parallel execution, with results returned as drafts for review before commit.

## Architecture

```
Claude Code (AAPM Orchestrator)
    │
    ├── mcp__k2_swarm__spawn_task
    │       │
    │       ▼
    │   Moonshot API (K2.5 Agent Swarm)
    │       │
    │       ▼
    │   100 sub-agents (parallel)
    │       │
    │       ▼
    │   Draft result (files, patches, analysis)
    │
    ├── mcp__k2_swarm__get_result
    │       │
    │       ▼
    │   Poll for completion, retrieve output
    │
    └── Review → Approve → Apply
```

## MCP Tools

### 1. `k2_swarm_spawn_task`

Spawn a K2.5 swarm task asynchronously.

**Request:**
```python
class K2SwarmSpawnRequest(BaseModel):
    task: str = Field(..., description="Task description for swarm")
    mode: Literal["agent", "agent_swarm"] = Field(
        default="agent_swarm",
        description="K2.5 mode (agent=single, agent_swarm=100 agents)"
    )
    context_files: list[str] = Field(
        default_factory=list,
        description="File paths to include as context"
    )
    max_steps: int = Field(
        default=100,
        description="Max steps per agent (swarm mode)"
    )
    output_format: Literal["patches", "files", "analysis"] = Field(
        default="patches",
        description="How to return results"
    )
```

**Response:**
```python
class K2SwarmSpawnResponse(BaseModel):
    success: bool
    task_id: str  # Moonshot task ID for polling
    message: str
    estimated_completion: datetime | None
```

### 2. `k2_swarm_get_result`

Poll for task completion and retrieve results.

**Request:**
```python
class K2SwarmResultRequest(BaseModel):
    task_id: str = Field(..., description="Task ID from spawn")
    wait: bool = Field(
        default=False,
        description="Block until completion (max 5 min)"
    )
```

**Response:**
```python
class K2SwarmResultResponse(BaseModel):
    success: bool
    status: Literal["pending", "running", "completed", "failed"]
    progress: float  # 0.0-1.0
    result: K2SwarmOutput | None
    error: str | None

class K2SwarmOutput(BaseModel):
    patches: list[FilePatch] | None  # Unified diff format
    files: dict[str, str] | None     # filepath → content
    analysis: str | None              # Text analysis
    tool_calls: int                   # Total tool calls made
    agents_used: int                  # Sub-agents spawned
    execution_time_seconds: float
```

### 3. `k2_swarm_apply_patches`

Apply approved patches from swarm output.

**Request:**
```python
class K2SwarmApplyRequest(BaseModel):
    task_id: str
    patch_indices: list[int] | None = Field(
        default=None,
        description="Specific patches to apply (None=all)"
    )
    dry_run: bool = Field(
        default=True,
        description="Preview changes without applying"
    )
```

## Implementation

### New Files

```
mcp-server/src/scheduler_mcp/
├── k2_swarm/
│   ├── __init__.py
│   ├── client.py          # MoonshotAPIClient
│   ├── models.py          # Pydantic schemas
│   ├── spawn_tool.py      # spawn_task tool
│   ├── result_tool.py     # get_result tool
│   └── apply_tool.py      # apply_patches tool
```

### Moonshot API Client

```python
class MoonshotAPIClient:
    """Client for Moonshot K2.5 API."""

    def __init__(self):
        self.api_key = os.environ.get("MOONSHOT_API_KEY")
        self.base_url = "https://api.moonshot.cn/v1"

    async def create_chat_completion(
        self,
        messages: list[dict],
        model: str = "kimi-k2.5",
        mode: str = "agent_swarm",
        max_tokens: int = 32000,
    ) -> dict:
        """Create K2.5 completion with swarm mode."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "mode": mode,  # agent_swarm enables 100-agent parallelism
                    "max_tokens": max_tokens,
                },
                timeout=300.0,  # 5 min for swarm execution
            )
            response.raise_for_status()
            return response.json()
```

### Environment Variables

```bash
# Required for K2.5 integration
MOONSHOT_API_KEY=sk-...          # From platform.moonshot.ai
K2_SWARM_ENABLED=true            # Feature flag
K2_SWARM_MAX_CONTEXT_SIZE=100000 # Max chars for context files
```

## Use Cases

### 1. Bulk Type Annotations

```python
# From Claude Code
result = await mcp.k2_swarm_spawn_task(
    task="Add type annotations to all functions in backend/app/services/",
    context_files=["backend/app/services/*.py"],
    output_format="patches"
)

# Wait for completion
output = await mcp.k2_swarm_get_result(task_id=result.task_id, wait=True)

# Review patches
for i, patch in enumerate(output.result.patches):
    print(f"=== Patch {i}: {patch.filepath} ===")
    print(patch.diff)

# Apply selected patches
await mcp.k2_swarm_apply_patches(
    task_id=result.task_id,
    patch_indices=[0, 2, 5],  # Skip patch 1, 3, 4
    dry_run=False
)
```

### 2. Codebase Exploration

```python
result = await mcp.k2_swarm_spawn_task(
    task="Analyze all API endpoints and create a dependency graph",
    context_files=["backend/app/api/routes/*.py"],
    output_format="analysis"
)
```

### 3. Test Generation

```python
result = await mcp.k2_swarm_spawn_task(
    task="Generate pytest tests for backend/app/services/swap_*.py",
    context_files=[
        "backend/app/services/swap_*.py",
        "backend/tests/conftest.py"
    ],
    output_format="files"
)
```

## Verification

1. **Unit tests:** Mock Moonshot API, test tool flow
2. **Integration test:** Real API call with simple task
3. **Manual test:**
   - Spawn bulk annotation task
   - Poll for completion
   - Review patches
   - Apply subset

## Dependencies

- `httpx` (already in mcp-server)
- Moonshot API account with swarm access

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| API rate limits | Implement backoff, queue tasks |
| Context too large | Chunk files, summarize first |
| Swarm timeout | 5 min max wait, async polling |
| Bad patches | Dry-run default, selective apply |
| Cost overrun | Token budget per task |

## Commit Strategy

1. Add `k2_swarm/` module with client + models
2. Add spawn/result/apply tools
3. Register in server.py with armory conditional loading
4. Add tests
5. Document in README
