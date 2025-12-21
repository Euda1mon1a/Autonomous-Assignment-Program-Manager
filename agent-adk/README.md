***REMOVED*** Agent ADK - Google Agent Development Kit for Residency Scheduler

TypeScript-based AI agents using Google's Agent Development Kit (ADK) with Gemini models.

***REMOVED******REMOVED*** Quick Start

```bash
***REMOVED*** Install dependencies
npm install

***REMOVED*** Set up environment
cp .env.example .env
***REMOVED*** Edit .env with your GOOGLE_GENAI_API_KEY

***REMOVED*** Run the web UI
npm run dev

***REMOVED*** Or run CLI mode
npm run cli
```

***REMOVED******REMOVED*** Features

- **ScheduleAssistant Agent**: Main agent for schedule queries and management
- **ComplianceChecker Agent**: Specialized ACGME compliance analysis
- **Evaluation Framework**: Automated testing for agent behavior
- **Multi-Model Support**: Gemini (default), Claude, and GPT options

***REMOVED******REMOVED*** Project Structure

```
agent-adk/
├── src/
│   ├── agents/           ***REMOVED*** ADK agent definitions
│   │   ├── index.ts      ***REMOVED*** Root agent export
│   │   └── schedule-agent.ts
│   ├── tools/            ***REMOVED*** Function tools for agents
│   │   └── schedule-tools.ts
│   └── evaluation/       ***REMOVED*** Test criteria and cases
│       ├── criteria.ts
│       └── test-cases.ts
├── tests/
│   └── agent.eval.test.ts
├── package.json
└── tsconfig.json
```

***REMOVED******REMOVED*** Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start ADK web UI at localhost:8000 |
| `npm run cli` | Run agent in CLI mode |
| `npm run build` | Compile TypeScript |
| `npm test` | Run all tests |
| `npm run test:eval` | Run evaluation tests only |

***REMOVED******REMOVED*** Tools Available to Agents

| Tool | Description |
|------|-------------|
| `get_schedule` | Retrieve schedule data |
| `validate_acgme_compliance` | Check ACGME rule compliance |
| `find_swap_matches` | Find compatible swap partners |
| `check_utilization` | Monitor 80% threshold |
| `run_contingency_analysis` | N-1/N-2 analysis |

***REMOVED******REMOVED*** Evaluation

Run agent evaluation tests:

```bash
npm run test:eval
```

Test categories:
- **ACGME**: Compliance checking behavior
- **Swap**: Partner matching and validation
- **Resilience**: System health monitoring
- **Safety**: PII protection and escalation

***REMOVED******REMOVED*** Model Configuration

Default: `gemini-2.5-flash`

Set `ADK_MODEL` environment variable to change:
- `gemini-2.5-flash` - Fast, cost-effective
- `gemini-2.5-pro` - Better reasoning
- `gemini-3-pro` - Latest capabilities

***REMOVED******REMOVED*** Integration with MCP

This ADK module complements the existing Python MCP server:

```
┌─────────────────┐     ┌─────────────────┐
│   ADK Agents    │     │   MCP Server    │
│   (TypeScript)  │     │   (Python)      │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │ Backend API │
              │  (FastAPI)  │
              └─────────────┘
```

Both systems call the same backend API endpoints.
