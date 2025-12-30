***REMOVED*** Scheduling Assistant Prompts

System prompts and prompt management for the local LLM scheduling assistant.

***REMOVED******REMOVED*** Overview

This module provides carefully crafted prompts optimized for 7B parameter local LLMs (Mistral-7B, Llama-2-7B, Llama-3-8B) to power a medical residency scheduling assistant. The prompts emphasize:

- **ACGME compliance awareness** - Enforcing regulatory requirements
- **Explicit tool usage** - Guiding models to use MCP tools rather than guess
- **RAG context integration** - Injecting retrieved schedule data
- **Professional medical/military tone** - Appropriate for DoD healthcare
- **HIPAA awareness** - Avoiding unnecessary PII exposure

***REMOVED******REMOVED*** Quick Start

```python
from app.prompts import get_default_prompt_manager

***REMOVED*** Initialize prompt manager
pm = get_default_prompt_manager()

***REMOVED*** Build a prompt for a swap request
prompt = pm.build_prompt(
    query="Can I swap my Friday call shift?",
    context="Dr. Smith is assigned to inpatient call on Friday, Jan 19...",
    task_type="swap"
)

***REMOVED*** Send prompt to LLM
response = llm.generate(prompt)
```

***REMOVED******REMOVED*** Prompt Types

***REMOVED******REMOVED******REMOVED*** 1. Base System Prompt

`SCHEDULING_ASSISTANT_SYSTEM_PROMPT` - The foundation prompt that defines:
- Assistant role and capabilities
- ACGME compliance rules (80-hour, 1-in-7, supervision ratios)
- Tool usage instructions
- Response guidelines (concise, professional, HIPAA-aware)
- What the assistant should NOT do

Use this as the system message for all conversations.

***REMOVED******REMOVED******REMOVED*** 2. Task-Specific Prompts

Additional instructions for specific tasks:

- **`SWAP_ANALYSIS_PROMPT`** - Analyzing swap requests and finding candidates
- **`COMPLIANCE_CHECK_PROMPT`** - Validating ACGME compliance
- **`SCHEDULE_EXPLANATION_PROMPT`** - Explaining schedule assignments
- **`COVERAGE_ANALYSIS_PROMPT`** - Identifying coverage gaps

These are combined with the base prompt when handling specific tasks.

***REMOVED******REMOVED******REMOVED*** 3. Error Handling Prompts

Pre-formatted responses for common error scenarios:

- `no_swap_candidates` - When no swap matches are found
- `acgme_violation` - When a request would violate ACGME rules
- `tool_failure` - When MCP tools fail
- `insufficient_context` - When not enough info is provided
- `permission_denied` - When user lacks access rights
- `ambiguous_request` - When request is unclear

***REMOVED******REMOVED*** Using the PromptManager

The `PromptManager` class provides a high-level interface for building prompts:

***REMOVED******REMOVED******REMOVED*** Basic Usage

```python
from app.prompts import PromptManager

pm = PromptManager(version="v1")

***REMOVED*** Build a prompt with RAG context
prompt = pm.build_prompt(
    query="Am I over hours this week?",
    context="Your hours: Mon 12h, Tue 14h, Wed 16h, Thu 12h, Fri 10h",
    task_type="compliance"
)
```

***REMOVED******REMOVED******REMOVED*** Building Tool Response Prompts

After calling MCP tools, guide the LLM to synthesize results:

```python
***REMOVED*** User asked: "Can I swap Friday?"
***REMOVED*** You called: analyze_swap_candidates()
***REMOVED*** Tool returned: {"candidates": [...]}

response_prompt = pm.build_tool_response(
    original_query="Can I swap my Friday call shift?",
    tool_results='{"candidates": [{"name": "Dr. Jones", "compatible": true}]}',
    task_type="swap"
)
```

***REMOVED******REMOVED******REMOVED*** Getting Error Prompts

```python
***REMOVED*** No swap candidates found
error_msg = pm.get_error_prompt(
    "no_swap_candidates",
    shift_type="call",
    date="Jan 19"
)

***REMOVED*** ACGME violation detected
error_msg = pm.get_error_prompt(
    "acgme_violation",
    rule_name="80-Hour Rule",
    current_value="72 hours",
    projected_value="88 hours",
    limit="80 hours",
    alternative_suggestion="Consider swapping a different shift to stay under limit"
)
```

***REMOVED******REMOVED******REMOVED*** Few-Shot Examples

Provide examples to guide the model:

```python
***REMOVED*** Get a specific example
example = pm.get_few_shot_example("swap_request")
print(example["query"])       ***REMOVED*** "Can I swap my Friday call shift with someone?"
print(example["tool_call"])   ***REMOVED*** "analyze_swap_candidates(...)"

***REMOVED*** Include examples in the prompt
prompt = pm.build_prompt(
    query="Can I swap Friday?",
    context=rag_context,
    task_type="swap",
    include_examples=True  ***REMOVED*** Adds relevant few-shot examples
)
```

***REMOVED******REMOVED******REMOVED*** Custom Task Prompts

Add your own task-specific prompts:

```python
pm.add_custom_task_prompt(
    "vacation_request",
    """You are analyzing a vacation request. Your task is to:
    1. Check ACGME impact on work hours
    2. Verify minimum coverage is maintained
    3. Suggest optimal dates if requested dates are problematic
    """
)

prompt = pm.build_prompt(
    query="Can I take vacation Jan 15-20?",
    task_type="vacation_request"
)
```

***REMOVED******REMOVED******REMOVED*** Prompt Versioning

Support for A/B testing and prompt iteration:

```python
***REMOVED*** Create different versions
pm_v1 = PromptManager(version="v1")
pm_v2 = PromptManager(version="v2")  ***REMOVED*** Future: load different prompt variants

***REMOVED*** Switch versions
pm.set_version("v2")
current = pm.get_version()  ***REMOVED*** "v2"
```

***REMOVED******REMOVED*** RAG Context Injection

***REMOVED******REMOVED******REMOVED*** Manual Context Building

```python
from app.prompts import build_rag_prompt

prompt = build_rag_prompt(
    query="Am I over hours?",
    context="Your schedule this week: Mon-Fri clinic (8h/day), Sat call (24h)",
    system_prompt=SCHEDULING_ASSISTANT_SYSTEM_PROMPT,
    task_prompt=COMPLIANCE_CHECK_PROMPT
)
```

***REMOVED******REMOVED******REMOVED*** Formatting Schedule Data

Convert schedule dictionaries to readable context:

```python
from app.prompts import format_schedule_data_for_context

schedule_data = {
    "person": "Dr. Smith (PGY-2)",
    "assignments": [
        {"date": "2024-01-15", "rotation": "Clinic", "shift_type": "AM"},
        {"date": "2024-01-16", "rotation": "Inpatient", "shift_type": "Day"},
    ],
    "hours_summary": {
        "This week": "48 hours",
        "4-week average": "72 hours"
    },
    "compliance_status": "COMPLIANT"
}

context = format_schedule_data_for_context(schedule_data)
***REMOVED*** Returns:
***REMOVED*** Person: Dr. Smith (PGY-2)
***REMOVED***
***REMOVED*** Assignments:
***REMOVED***   - 2024-01-15: Clinic AM
***REMOVED***   - 2024-01-16: Inpatient Day
***REMOVED***
***REMOVED*** Work Hours Summary:
***REMOVED***   This week: 48 hours
***REMOVED***   4-week average: 72 hours
***REMOVED***
***REMOVED*** Compliance Status: COMPLIANT
```

***REMOVED******REMOVED*** Integration with LLM Service

Example integration with the LLM service:

```python
from app.prompts import get_default_prompt_manager
from app.services.llm_service import LLMService

async def handle_user_query(query: str, user_id: str):
    """Handle a user query with prompt management."""

    ***REMOVED*** 1. Retrieve relevant context via RAG
    rag_context = await retrieve_schedule_context(query, user_id)

    ***REMOVED*** 2. Determine task type
    task_type = classify_query(query)  ***REMOVED*** "swap", "compliance", etc.

    ***REMOVED*** 3. Build prompt
    pm = get_default_prompt_manager()
    prompt = pm.build_prompt(
        query=query,
        context=rag_context,
        task_type=task_type,
        include_examples=True
    )

    ***REMOVED*** 4. Generate response
    llm = LLMService()
    response = await llm.generate(prompt)

    return response
```

***REMOVED******REMOVED*** Prompt Design Principles

These prompts follow best practices for small LLMs:

1. **Explicit > Implicit**: Tell the model exactly what to do, don't rely on inference
2. **Structure matters**: Use markdown headers, bullet points, clear sections
3. **Tool usage front and center**: Repeatedly emphasize using tools vs. guessing
4. **ACGME rules as facts**: List rules explicitly rather than expecting the model to "know" them
5. **Few-shot when helpful**: Provide examples for complex or ambiguous tasks
6. **Error handling**: Give clear templates for common failure modes
7. **Professional tone**: Model appropriate medical/military communication

***REMOVED******REMOVED*** Testing Prompts

Test prompts with different models:

```bash
***REMOVED*** Run prompt tests
cd backend
pytest tests/prompts/test_scheduling_assistant_prompts.py -v

***REMOVED*** Test with specific model
MODEL=mistral-7b pytest tests/prompts/ -v
```

***REMOVED******REMOVED*** Customization

***REMOVED******REMOVED******REMOVED*** Modifying Prompts

When updating prompts:

1. Edit the prompt constants in `scheduling_assistant.py`
2. Test with your target LLM (Mistral-7B or Llama)
3. Validate that ACGME rules are still enforced
4. Check that tool usage instructions are clear
5. Update version number if making breaking changes

***REMOVED******REMOVED******REMOVED*** Adding New Task Types

```python
***REMOVED*** 1. Define the prompt
NEW_TASK_PROMPT = """You are analyzing a [task]. Your task is to:
1. [Step 1]
2. [Step 2]
...
"""

***REMOVED*** 2. Add to PromptManager.__init__ or use add_custom_task_prompt()
pm.add_custom_task_prompt("new_task", NEW_TASK_PROMPT)

***REMOVED*** 3. Add few-shot examples if helpful
FEW_SHOT_EXAMPLES["new_task_example"] = {
    "query": "Example query",
    "reasoning": "Why this approach",
    "tool_call": "tool_name(args)",
    "response_template": "Response format"
}
```

***REMOVED******REMOVED*** Performance Notes

- **Mistral-7B-Instruct**: Works well with structured prompts, good tool usage
- **Llama-2-7B-Chat**: May need more explicit examples, test tool calling carefully
- **Llama-3-8B-Instruct**: Strong instruction following, handles complex prompts well

All prompts have been tested to stay under 2048 token context windows (typical for 7B models).

***REMOVED******REMOVED*** See Also

- `docs/planning/local-llm-docker-integration-plan.md` - Integration architecture
- `backend/app/services/llm_service.py` - LLM service implementation
- `backend/app/services/rag_service.py` - RAG context retrieval
- `mcp-server/` - MCP tools for schedule operations
