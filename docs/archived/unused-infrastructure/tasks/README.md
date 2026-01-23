# Agent Task Queue

This directory contains task documents for autonomous execution by agentic browsers (Comet/Atlas).

## Directory Structure

```
/docs/tasks/
├── active/          # Tasks awaiting execution
├── in-progress/     # Tasks currently being executed
├── completed/       # Finished tasks (with results)
└── templates/       # Task document templates
```

## How It Works

1. **Claude creates** a task document in `/active/` when it needs information
2. **User triggers** Comet or Atlas to pick up the task
3. **Agent executes** the task (research, consultation, etc.)
4. **Agent writes** results back to the document
5. **Document moves** to `/completed/`
6. **Claude reads** results in subsequent session

## Agent Selection

| Agent | Best For |
|-------|----------|
| **Comet** | Parallel research, bulk tasks, speed-critical |
| **Atlas** | Oracle queries, preference-sensitive, nuanced tasks |

## Templates

- `consultation.md` - Consulting an LLM advisor
- `oracle-query.md` - ChatGPT personal oracle queries
- `research.md` - Web research tasks

## Task Lifecycle

```
pending → in_progress → completed
```

See [Expert Consultation Protocol](/docs/architecture/expert-consultation-protocol.md) for full documentation.
