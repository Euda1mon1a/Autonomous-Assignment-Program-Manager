---
name: recall
description: Search episodic task history for lessons learned from prior agent work. Surfaces past failures and successes relevant to your current task.
model_tier: haiku
parallel_hints:
  can_parallel_with: [preflight, constraint-state]
  must_serialize_with: []
  preferred_batch_size: 1
context_hints:
  max_file_context: 0
  compression_level: 2
  requires_git_context: false
  requires_db_context: false
---

# /recall — Episodic Task Memory

Search the task history learning system for lessons from prior agent work.

## When to Use

- Before starting a task involving files that caused prior failures
- When working in a domain area (scheduling, constraints, HDA) where past lessons exist
- To check if a similar task was attempted before and what happened
- After a failure, to log the lesson for future agents

## Usage

```
/recall "scheduling engine changes"
/recall "HalfDayAssignment is_deleted"
/recall "constraint archetype violations"
```

## Behavior

1. Call `query_similar_tasks_tool` with the user's query
2. Format results as actionable warnings grouped by outcome
3. Highlight failure lessons prominently — these prevent repeat mistakes

## Output Format

```
Lessons from task history (N results):

FAILURES:
  1. "Add is_deleted filter to HDA query" (2026-03-12)
     Lesson: HalfDayAssignment has no is_deleted column.
     Tags: scheduling, hda, schema
     Files: engine.py

SUCCESSES:
  2. "Add block_half filter to HDA query" (2026-03-08)
     Duration: 450ms
     Tags: scheduling, hda
     Files: engine.py, sync_preload_service.py
```

## Instructions

When the user runs `/recall <query>`:

1. Call the MCP tool `query_similar_tasks_tool` with the provided query text:
   - Set `top_k` to 10 for comprehensive results
   - Leave `success_filter` as None to get both successes and failures
   - Set `min_similarity` to 0.4 for broader recall

2. If results are returned, format them as shown above:
   - Group by FAILURES first (most actionable), then SUCCESSES
   - Include the `notes` field prominently — this is the lesson
   - Show `tags`, `files_touched`, `created_at`, and `duration_ms` when available
   - Show similarity score in parentheses for transparency

3. If no results are found, say:
   "No similar tasks found in history. After completing your current task, consider logging it with `log_task_tool` to help future agents."

4. If the MCP tool call fails (server down, etc.), say:
   "Task history service unavailable. Proceed with caution — no prior lessons could be checked."
