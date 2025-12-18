***REMOVED*** Agent Task Queue

This directory contains task documents for autonomous execution by agentic browsers (Comet/Atlas).

***REMOVED******REMOVED*** Directory Structure

```
/docs/tasks/
├── active/          ***REMOVED*** Tasks awaiting execution
├── in-progress/     ***REMOVED*** Tasks currently being executed
├── completed/       ***REMOVED*** Finished tasks (with results)
└── templates/       ***REMOVED*** Task document templates
```

***REMOVED******REMOVED*** How It Works

1. **Claude creates** a task document in `/active/` when it needs information
2. **User triggers** Comet or Atlas to pick up the task
3. **Agent executes** the task (research, consultation, etc.)
4. **Agent writes** results back to the document
5. **Document moves** to `/completed/`
6. **Claude reads** results in subsequent session

***REMOVED******REMOVED*** Agent Selection

| Agent | Best For |
|-------|----------|
| **Comet** | Parallel research, bulk tasks, speed-critical |
| **Atlas** | Oracle queries, preference-sensitive, nuanced tasks |

***REMOVED******REMOVED*** Templates

- `consultation.md` - Consulting an LLM advisor
- `oracle-query.md` - ChatGPT personal oracle queries
- `research.md` - Web research tasks

***REMOVED******REMOVED*** Task Lifecycle

```
pending → in_progress → completed
```

See [Expert Consultation Protocol](/docs/architecture/expert-consultation-protocol.md) for full documentation.
