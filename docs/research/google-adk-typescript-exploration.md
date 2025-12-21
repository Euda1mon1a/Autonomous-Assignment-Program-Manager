# Google Agent Development Kit (ADK) for TypeScript - Exploration

> **Date:** 2025-12-20
> **Status:** Exploration / Research
> **Relevance:** High - Complements existing MCP Agent Server

---

## Executive Summary

Google launched the Agent Development Kit (ADK) for TypeScript on December 17, 2025, providing JavaScript and TypeScript developers with a code-first approach to building autonomous AI agents. This document explores how Google ADK relates to our Residency Scheduler project and identifies potential integration opportunities.

**Key Finding:** Our existing MCP Agent Server architecture is highly compatible with Google ADK. The `sample_llm()` method in `mcp-server/src/scheduler_mcp/agent_server.py` is already designed as an abstraction point for LLM providers, making Gemini integration straightforward.

---

## What is Google ADK?

Google's Agent Development Kit is an open-source framework for building, evaluating, and deploying AI agents with:

- **Code-First Approach**: Define agent logic, tools, and orchestration directly in TypeScript
- **Modular Components**: Agents, Instructions, and Tools as testable units
- **Type Safety**: End-to-end TypeScript across agent backend and frontend
- **Model-Agnostic Design**: Optimized for Gemini but compatible with other LLMs
- **Enterprise-Ready Evaluation**: Automated metrics, test sets, and production deployment

### Core Components

```typescript
// Example ADK Agent Structure
import { Agent, FunctionTool } from '@google/adk';
import { z } from 'zod';

const scheduleAnalysisTool = new FunctionTool({
  name: 'analyze_schedule',
  description: 'Analyzes a schedule for compliance issues and coverage gaps',
  parameters: z.object({
    scheduleId: z.string().describe('The schedule ID to analyze'),
    checkCompliance: z.boolean().describe('Whether to check ACGME compliance')
  }),
  execute: async ({ scheduleId, checkCompliance }) => {
    // Call our existing backend API
    const response = await fetch(`/api/schedules/${scheduleId}/analyze`);
    return response.json();
  }
});

export const rootAgent = new Agent({
  name: 'ScheduleAssistant',
  model: 'gemini-2.5-flash',
  description: 'AI assistant for medical residency scheduling',
  instruction: `You are a scheduling assistant for a medical residency program.
    Your goal is to help optimize schedules while ensuring ACGME compliance.`,
  tools: [scheduleAnalysisTool]
});
```

---

## How ADK Relates to Our Repository

### Current Architecture

Our repository already has a sophisticated agent infrastructure:

| Component | Location | Status |
|-----------|----------|--------|
| MCP Agent Server | `/mcp-server/src/scheduler_mcp/agent_server.py` | Production-ready |
| 16 MCP Tools | `/mcp-server/src/scheduler_mcp/tools.py` | Implemented |
| Resilience Integration | `/mcp-server/src/scheduler_mcp/resilience_integration.py` | 13 tools |
| TypeScript Frontend | `/frontend/src/` | ~200 TypeScript files |
| n8n Workflows | `/n8n/workflows/` | 6 ChatOps workflows |

### LLM Abstraction Point

The existing `sample_llm()` method in `agent_server.py:221-270` is designed for LLM provider abstraction:

```python
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
    """
    # TODO: Replace with actual MCP sampling call
    # Currently simulated - ready for Gemini integration
```

This is the **perfect integration point** for Google ADK or Gemini API.

---

## Integration Opportunities

### Option 1: TypeScript Agent Layer (Recommended)

Create a new TypeScript-based agent layer using Google ADK that:
- Sits alongside the existing Python MCP server
- Handles frontend-initiated agent interactions
- Leverages the same backend API endpoints
- Uses Gemini models via ADK

**Proposed Structure:**
```
/agent-ts/                    # New TypeScript agent module
├── src/
│   ├── agents/
│   │   ├── schedule-agent.ts
│   │   ├── compliance-agent.ts
│   │   └── swap-agent.ts
│   ├── tools/
│   │   ├── schedule-tools.ts
│   │   ├── resilience-tools.ts
│   │   └── swap-tools.ts
│   └── index.ts
├── package.json
├── tsconfig.json
└── tests/
    └── agents.test.ts
```

### Option 2: Hybrid Python/TypeScript

Enhance the existing Python MCP server with Gemini support while adding TypeScript ADK for frontend-specific agents:

```python
# In agent_server.py - Add Gemini provider
from google.generativeai import GenerativeModel

async def sample_llm(self, prompt: str, context: dict, ...):
    if self.llm_provider.startswith('gemini'):
        model = GenerativeModel(self.llm_provider)
        response = await model.generate_content_async(prompt)
        return response.text
    elif self.llm_provider.startswith('claude'):
        # Existing Claude implementation
        pass
```

### Option 3: ADK Evaluation Framework Only

Use Google ADK's evaluation capabilities without full agent migration:
- Tool trajectory testing
- Response match scoring
- Safety evaluation
- Regression testing for agent behavior

---

## Feature Comparison

| Feature | Our MCP Server | Google ADK TypeScript |
|---------|----------------|----------------------|
| Language | Python | TypeScript |
| Agent Loops | Goal decomposition | Multi-agent orchestration |
| Tool Definition | FastMCP decorators | FunctionTool + Zod |
| LLM Support | Claude (placeholder) | Gemini (native) |
| Type Safety | Pydantic | TypeScript + Zod |
| Evaluation | Manual testing | Automated metrics |
| Deployment | MCP protocol | Cloud Run / GKE |
| Human-in-Loop | Approval workflows | Built-in support |

---

## ADK Evaluation Capabilities

One of ADK's strongest features is systematic agent evaluation:

### Automated Metrics

1. **Tool Trajectory Evaluation**
   - Compares actual tool calls vs expected sequence
   - Match modes: EXACT, IN_ORDER, ANY_ORDER
   - Critical for validating scheduling workflows

2. **Response Match Score**
   - Uses ROUGE metric for NLP comparison
   - Default: 80% accuracy threshold
   - Useful for compliance explanations

3. **Semantic Equivalence**
   - LLM-as-judge evaluation
   - Tolerates formatting differences
   - Validates reasoning quality

4. **Safety Evaluation**
   - Vertex AI General AI Eval SDK
   - Detects harmful content
   - Essential for medical domain

### Testing Integration

```typescript
// Example evaluation test
import { evaluate } from '@google/adk';

describe('Schedule Analysis Agent', () => {
  it('should detect ACGME violations', async () => {
    const result = await evaluate({
      agent: scheduleAgent,
      input: 'Check schedule for compliance issues',
      expectedToolCalls: [
        { name: 'get_schedule', args: { id: 'current' } },
        { name: 'validate_acgme', args: { checkAll: true } }
      ],
      expectedResponseContains: ['80-hour rule', 'supervision ratio']
    });

    expect(result.toolTrajectoryScore).toBeGreaterThan(0.9);
    expect(result.responseMatchScore).toBeGreaterThan(0.8);
  });
});
```

---

## Proposed Implementation Roadmap

### Phase 1: Research & Proof of Concept
- [ ] Set up ADK development environment
- [ ] Create basic schedule analysis agent
- [ ] Integrate with existing backend API
- [ ] Compare performance with MCP agent

### Phase 2: Tool Migration
- [ ] Port high-priority MCP tools to ADK format
- [ ] Implement Zod schemas matching Pydantic models
- [ ] Create tool registry for both systems

### Phase 3: Evaluation Framework
- [ ] Define test cases for scheduling workflows
- [ ] Implement trajectory evaluation
- [ ] Add safety checks for medical data
- [ ] Set up CI/CD evaluation pipeline

### Phase 4: Production Integration
- [ ] Deploy ADK agents to Cloud Run
- [ ] Configure Vertex AI for enterprise
- [ ] Integrate with frontend React hooks
- [ ] Add monitoring and observability

---

## Environment Variables Required

```bash
# Google ADK / Gemini
GOOGLE_GENAI_API_KEY=<api-key>        # For Gemini API
VERTEX_AI_PROJECT_ID=<project-id>      # For Vertex AI
VERTEX_AI_LOCATION=us-central1         # Vertex AI region

# Existing (keep for Claude fallback)
ANTHROPIC_API_KEY=<api-key>
```

---

## Technical Considerations

### Advantages of ADK Integration

1. **Native TypeScript**: Matches our frontend stack
2. **Type Safety**: End-to-end typing with Zod validation
3. **Gemini 3 Models**: Access to latest Google AI capabilities
4. **Evaluation Built-in**: Production-ready testing framework
5. **Vertex AI Path**: Enterprise deployment on Google Cloud

### Challenges

1. **Dual Agent Systems**: Managing both MCP and ADK
2. **Python/TypeScript Bridge**: Coordination between backends
3. **Migration Effort**: Porting existing tools
4. **Testing Overhead**: Maintaining two evaluation systems

### Recommendation

**Start with Option 1 (TypeScript Agent Layer)** for new frontend-driven agent features while keeping the Python MCP server for MCP protocol compliance. This provides:
- Best of both worlds
- Incremental adoption
- No disruption to existing functionality
- Path to full TypeScript if desired

---

## Related Documentation

- [MCP Agent Implementation Summary](/mcp-server/AGENT_IMPLEMENTATION_SUMMARY.md)
- [Resilience MCP Integration](/mcp-server/RESILIENCE_MCP_INTEGRATION.md)
- [Architecture Overview](/docs/architecture/overview.md)
- [Frontend Architecture](/docs/architecture/frontend.md)

## External Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [TypeScript Quickstart](https://google.github.io/adk-docs/get-started/typescript/)
- [ADK Evaluation Criteria](https://google.github.io/adk-docs/evaluate/criteria/)
- [ADK GitHub Repository](https://github.com/google/adk-js)
- [ADK Samples](https://github.com/google/adk-samples)
- [Google Developers Blog Announcement](https://developers.googleblog.com/introducing-agent-development-kit-for-typescript-build-ai-agents-with-the-power-of-a-code-first-approach/)

---

## Conclusion

Google ADK for TypeScript represents a significant opportunity for this project. Our existing architecture—with its abstracted LLM sampling, comprehensive tool library, and TypeScript frontend—is well-positioned for ADK integration. The evaluation framework alone justifies exploration, as it addresses a critical gap in testing autonomous agent behavior.

The recommended approach is to create a parallel TypeScript agent module using ADK while maintaining the Python MCP server for backward compatibility. This enables incremental adoption and provides immediate access to Gemini models and ADK's evaluation capabilities.
