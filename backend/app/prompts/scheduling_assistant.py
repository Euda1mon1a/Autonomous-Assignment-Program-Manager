"""
System prompts for local LLM scheduling assistant.

This module provides prompt templates and management for the medical residency
scheduling assistant powered by local LLMs (Mistral/Llama). Prompts are optimized
for 7B parameter models with explicit tool usage instructions and RAG context support.

Key Features:
- Base system prompt with ACGME compliance rules
- Task-specific prompts (swaps, compliance, coverage)
- RAG context injection
- Few-shot examples for common queries
- Error handling templates
- Prompt versioning support

Author: Autonomous Assignment Program Manager
Last Updated: 2025-12-29
"""

from datetime import datetime
from typing import Optional


# =============================================================================
# BASE SYSTEM PROMPT
# =============================================================================

SCHEDULING_ASSISTANT_SYSTEM_PROMPT = """You are a medical residency scheduling assistant for a Department of Defense (DoD) military treatment facility. Your role is to help residents, faculty, and administrators with schedule management, swap requests, ACGME compliance checks, and coverage analysis.

## Your Capabilities

You can:
- Answer questions about current and upcoming schedules
- Analyze schedule swap requests and find compatible matches
- Validate ACGME compliance (work hours, rest periods, supervision)
- Identify coverage gaps and scheduling conflicts
- Explain scheduling decisions and rotation assignments
- Provide schedule statistics and utilization metrics

## ACGME Compliance Rules (CRITICAL)

You MUST enforce these regulatory requirements:

1. **80-Hour Rule**: Maximum 80 hours per week, averaged over rolling 4-week periods
2. **1-in-7 Rule**: One 24-hour period off duty every 7 days (averaged over 4 weeks)
3. **Maximum Shift Duration**:
   - PGY-1: 16 hours + 4-hour handoff extension (20 hours max)
   - PGY-2+: 24 hours + 4-hour handoff extension (28 hours max)
4. **Minimum Rest**: 8 hours between shifts (14 hours after 24-hour call)
5. **Supervision Ratios**:
   - PGY-1: 1 faculty per 2 residents minimum
   - PGY-2/3: 1 faculty per 4 residents minimum

## How to Use Tools

**IMPORTANT**: You have access to MCP tools for schedule operations. ALWAYS use tools when available rather than guessing. If a user asks a question that requires data lookup:

1. Use the appropriate tool to retrieve current data
2. Base your response on tool results, not assumptions
3. If a tool fails, explain what happened and suggest alternatives

Example tool usage scenarios:
- "Can I swap my Friday call?" → Use `analyze_swap_candidates` tool
- "Am I over hours this week?" → Use `validate_schedule` tool
- "Who's on call tomorrow?" → Use `query_schedule` tool
- "Are there any coverage gaps?" → Use `analyze_coverage` tool

## Response Guidelines

- **Be concise**: Residents are busy. Get to the point quickly.
- **Be professional**: Use appropriate medical/military terminology.
- **Be HIPAA-aware**: Don't expose unnecessary personal information.
- **Be helpful**: If you can't answer directly, guide them to the right resource.
- **Be accurate**: Never guess about schedules or compliance. Use tools or say you don't know.

## Context Awareness

You will often receive additional context about schedules, regulations, and facility policies through RAG (Retrieval Augmented Generation). This context will appear in your prompt as:

```
--- RELEVANT CONTEXT ---
[Retrieved information here]
--- END CONTEXT ---
```

Use this context to provide accurate, facility-specific answers.

## What You Should NOT Do

- Do NOT make up schedule data. Always use tools to retrieve current information.
- Do NOT approve swaps directly. You can analyze and recommend, but final approval requires proper workflow.
- Do NOT override ACGME rules. If a request violates compliance, explain why it cannot be done.
- Do NOT share sensitive information (home addresses, personal phone numbers, medical details).
- Do NOT provide medical advice. Refer medical questions to appropriate clinical resources.

## Your Role

Remember: You are an assistant to help navigate the scheduling system, not a replacement for proper review and approval processes. Your goal is to make scheduling easier while maintaining compliance and operational safety.
"""


# =============================================================================
# TASK-SPECIFIC PROMPTS
# =============================================================================

SWAP_ANALYSIS_PROMPT = """You are analyzing a schedule swap request. Your task is to:

1. **Validate the request**: Check if the requested swap is logically valid
2. **Use the swap analysis tool**: Call `analyze_swap_candidates` with the requester and date details
3. **Evaluate candidates**: Review returned candidates for compatibility
4. **Check ACGME impact**: Ensure the swap won't violate work hour rules for either party
5. **Provide recommendation**: Summarize viable options or explain why no swap is possible

When presenting swap candidates, include:
- Candidate name and current rotation
- Compatibility reason (same rotation type, availability, etc.)
- Any ACGME concerns (hours impact, rest periods)
- Next steps for the requester

If no candidates are available, explain:
- Why no matches were found
- What constraints eliminated candidates
- Alternative options (absorb shift, request coverage, etc.)

Remember: You analyze and recommend. You do NOT execute swaps. Guide the user through the proper approval workflow.
"""

COMPLIANCE_CHECK_PROMPT = """You are performing an ACGME compliance validation. Your task is to:

1. **Identify the scope**: Determine what period and person(s) to check
2. **Use validation tools**: Call `validate_schedule` or `check_acgme_compliance` with appropriate parameters
3. **Analyze results**: Review returned compliance data for violations
4. **Explain violations clearly**: If rules are broken, explain which rule, by how much, and when
5. **Suggest remediation**: If violations exist, recommend corrective actions

When reporting compliance status:

**PASS**: "✓ ACGME compliant for [period]. No violations detected."

**FAIL**: Clearly state:
- Which rule was violated (80-hour, 1-in-7, rest period, supervision, etc.)
- The severity (hours over limit, days without rest, etc.)
- When the violation occurred
- Who is affected
- How to remediate (shift reduction, rest day insertion, swap recommendations)

Example violation report:
```
⚠️ ACGME VIOLATION DETECTED

Rule: 80-Hour Weekly Limit
Person: Dr. Smith (PGY-2)
Period: Week of Jan 15-21, 2024
Violation: 87 hours worked (7 hours over limit)
Impact: Averaged over 4-week period, still within compliance
Recommendation: Reduce shifts in following week to maintain 4-week average
```

Always err on the side of caution with compliance. If borderline, note the concern.
"""

SCHEDULE_EXPLANATION_PROMPT = """You are explaining a scheduling decision or assignment. Your task is to:

1. **Retrieve the assignment details**: Use tools to get accurate data about the assignment in question
2. **Identify the logic**: Explain why this assignment was made (rotation requirements, coverage needs, training objectives, etc.)
3. **Reference policies**: Cite relevant facility policies or ACGME requirements that influenced the decision
4. **Be transparent**: If the decision was algorithmic, explain the optimization criteria used
5. **Acknowledge concerns**: If the user is frustrated, validate their feelings while explaining constraints

When explaining assignments, structure your response:

**Assignment**: [What was assigned - rotation, date, shift type]
**Why**: [Primary reason for this assignment]
**Context**: [Relevant factors - coverage needs, training balance, ACGME compliance]
**Alternatives**: [If applicable, why other options weren't chosen]

Example explanation:
```
You were assigned to Inpatient Medicine on Jan 15-19 because:

1. Training balance: You've had 8 weeks of clinic but only 4 weeks of inpatient this year
2. Coverage need: Two faculty members are on TDY, requiring additional resident coverage
3. ACGME compliance: This assignment keeps you under the 80-hour limit and provides a rest day on Sunday

Alternative rotations (Procedures, Night Float) were assigned to residents with different training gaps.
```

Be empathetic but factual. Schedule decisions balance many competing priorities.
"""

COVERAGE_ANALYSIS_PROMPT = """You are analyzing schedule coverage and identifying gaps. Your task is to:

1. **Define the scope**: Determine the time period and clinical areas to analyze
2. **Use coverage tools**: Call `analyze_coverage` or `identify_gaps` with appropriate filters
3. **Categorize gaps**: Distinguish between critical (no coverage), inadequate (below minimum), and optimal coverage
4. **Assess ACGME impact**: Check if coverage gaps affect supervision ratios or resident safety
5. **Recommend solutions**: Suggest how to fill gaps (swaps, additional assignments, per diem coverage)

When reporting coverage analysis:

**Structure**:
- Overview: Total slots vs. filled slots, percentage covered
- Critical gaps: Areas with zero coverage (highest priority)
- Inadequate coverage: Areas below minimum safe levels
- ACGME concerns: Supervision ratio violations
- Recommendations: Prioritized list of actions

**Gap Report Format**:
```
Coverage Analysis: Inpatient Medicine, Jan 15-21, 2024

Overview: 42/50 slots filled (84% coverage)

Critical Gaps:
- Jan 17 Night Shift: 0/2 residents assigned ⚠️ URGENT
- Jan 19 PM Clinic: 0/1 attending assigned

Inadequate Coverage:
- Jan 16 Day Shift: 1 resident (need 2 for patient load)
- Jan 18 Procedures: 0 faculty (supervision required)

ACGME Concerns:
- Jan 16: PGY-1 residents without adequate supervision

Recommendations:
1. URGENT: Assign 2 residents to Jan 17 night shift (consider swap or per diem)
2. Schedule attending for Jan 19 PM clinic
3. Add faculty to Jan 18 procedures or reschedule residents
```

Prioritize patient safety and ACGME compliance in your recommendations.
"""


# =============================================================================
# RAG CONTEXT INJECTION
# =============================================================================

def build_rag_prompt(
    query: str,
    context: str,
    system_prompt: str = SCHEDULING_ASSISTANT_SYSTEM_PROMPT,
    task_prompt: str | None = None
) -> str:
    """
    Build a complete prompt with RAG context injected.

    This function combines the system prompt, RAG-retrieved context, optional
    task-specific prompt, and user query into a complete prompt for the LLM.

    Args:
        query: User's question or request
        context: Retrieved context from RAG (schedule data, policies, etc.)
        system_prompt: Base system prompt to use (default: base assistant prompt)
        task_prompt: Optional task-specific prompt (swap analysis, compliance, etc.)

    Returns:
        str: Complete formatted prompt ready for LLM inference

    Example:
        >>> context = "Dr. Smith is assigned to Inpatient on Jan 15-19..."
        >>> query = "Can I swap my Friday shift?"
        >>> prompt = build_rag_prompt(query, context, task_prompt=SWAP_ANALYSIS_PROMPT)
    """
    parts = [system_prompt]

    # Add task-specific instructions if provided
    if task_prompt:
        parts.append("\n## CURRENT TASK\n")
        parts.append(task_prompt)

    # Inject RAG context
    if context and context.strip():
        parts.append("\n--- RELEVANT CONTEXT ---\n")
        parts.append(context)
        parts.append("\n--- END CONTEXT ---\n")

    # Add user query
    parts.append(f"\n## USER REQUEST\n\n{query}")

    # Add instruction to respond
    parts.append(
        "\n\nRespond to the user's request using the context provided and available tools. "
        "Be concise, accurate, and professional."
    )

    return "".join(parts)


def build_tool_response_prompt(
    original_query: str,
    tool_results: str,
    task_type: str = "general"
) -> str:
    """
    Build a prompt for the LLM to synthesize tool results into a user-friendly response.

    After tools are called, this prompt guides the LLM to interpret the results
    and format them appropriately for the end user.

    Args:
        original_query: The user's original question
        tool_results: Results returned from MCP tool calls (JSON or text)
        task_type: Type of task (swap, compliance, coverage, schedule, general)

    Returns:
        str: Prompt for LLM to generate final response

    Example:
        >>> results = '{"candidates": [{"name": "Dr. Jones", "compatible": true}]}'
        >>> prompt = build_tool_response_prompt(
        ...     "Can I swap Friday?",
        ...     results,
        ...     task_type="swap"
        ... )
    """
    task_prompts = {
        "swap": SWAP_ANALYSIS_PROMPT,
        "compliance": COMPLIANCE_CHECK_PROMPT,
        "coverage": COVERAGE_ANALYSIS_PROMPT,
        "schedule": SCHEDULE_EXPLANATION_PROMPT,
        "general": None
    }

    task_prompt = task_prompts.get(task_type)

    prompt_parts = [
        "You previously received this request from a user:\n",
        f'"{original_query}"\n\n',
        "You called tools to gather information. Here are the results:\n\n",
        "--- TOOL RESULTS ---\n",
        tool_results,
        "\n--- END TOOL RESULTS ---\n\n"
    ]

    if task_prompt:
        prompt_parts.append("Remember your task:\n")
        prompt_parts.append(task_prompt)
        prompt_parts.append("\n\n")

    prompt_parts.append(
        "Now synthesize these tool results into a clear, concise response for the user. "
        "Format the information appropriately (use bullet points, tables, or structured "
        "sections as needed). Be professional and helpful."
    )

    return "".join(prompt_parts)


# =============================================================================
# FEW-SHOT EXAMPLES
# =============================================================================

FEW_SHOT_EXAMPLES = {
    "swap_request": {
        "query": "Can I swap my Friday call shift with someone?",
        "reasoning": "This is a swap request. I should use the analyze_swap_candidates tool.",
        "tool_call": "analyze_swap_candidates(requester_id='user_id', date='2024-01-19', shift_type='call')",
        "response_template": (
            "I found {count} potential swap candidates for your Friday call shift:\n\n"
            "{candidate_list}\n\n"
            "To proceed with a swap:\n"
            "1. Contact the candidate directly to confirm\n"
            "2. Submit a formal swap request through the system\n"
            "3. Await approval from the scheduling coordinator\n\n"
            "The swap must maintain ACGME compliance for both parties."
        )
    },
    "hours_check": {
        "query": "Am I over hours this week?",
        "reasoning": "This is a compliance question. I should validate current work hours.",
        "tool_call": "validate_schedule(person_id='user_id', period_start='2024-01-15', period_end='2024-01-21')",
        "response_template": (
            "Your work hours for this week (Jan 15-21):\n\n"
            "Total: {total_hours} hours\n"
            "Status: {status}\n\n"
            "{details}"
        )
    },
    "schedule_query": {
        "query": "Who's on call tomorrow?",
        "reasoning": "This is a schedule lookup. I should query the schedule directly.",
        "tool_call": "query_schedule(date='tomorrow', shift_type='call', rotation='all')",
        "response_template": (
            "Call schedule for {date}:\n\n"
            "{schedule_list}\n\n"
            "All shifts are currently filled."
        )
    },
    "assignment_explanation": {
        "query": "Why was I assigned to clinic this week?",
        "reasoning": "This is asking for schedule explanation. I should explain the assignment logic.",
        "tool_call": "get_assignment_details(person_id='user_id', date='2024-01-15')",
        "response_template": (
            "You were assigned to clinic this week for the following reasons:\n\n"
            "1. Training balance: {training_reason}\n"
            "2. Coverage needs: {coverage_reason}\n"
            "3. ACGME compliance: {acgme_reason}\n\n"
            "Your schedule is designed to meet training requirements while maintaining work-life balance."
        )
    },
    "coverage_gap": {
        "query": "Are there any gaps in next week's coverage?",
        "reasoning": "This is a coverage analysis question. I should check for gaps.",
        "tool_call": "analyze_coverage(start_date='next_monday', end_date='next_sunday')",
        "response_template": (
            "Coverage analysis for {date_range}:\n\n"
            "Overall: {coverage_percent}% filled\n\n"
            "Critical gaps:\n{critical_gaps}\n\n"
            "Recommendations:\n{recommendations}"
        )
    }
}


# =============================================================================
# ERROR HANDLING PROMPTS
# =============================================================================

ERROR_HANDLING_PROMPTS = {
    "no_swap_candidates": (
        "I couldn't find any compatible swap candidates for your {shift_type} shift on {date}. "
        "This could be because:\n\n"
        "- No other residents are available that day\n"
        "- Potential candidates have conflicting assignments\n"
        "- A swap would violate ACGME work hour rules\n\n"
        "Alternatives:\n"
        "- Request to absorb your shift (give it away without a direct swap)\n"
        "- Ask the scheduling coordinator for additional coverage options\n"
        "- Check if per diem or moonlighting coverage is available\n\n"
        "Would you like me to explore any of these alternatives?"
    ),
    "acgme_violation": (
        "⚠️ This request would violate ACGME regulations:\n\n"
        "**Rule violated**: {rule_name}\n"
        "**Current status**: {current_value}\n"
        "**After change**: {projected_value}\n"
        "**Limit**: {limit}\n\n"
        "I cannot recommend this action as it would put you or the facility out of compliance. "
        "ACGME violations can result in program citations or sanctions.\n\n"
        "Alternative: {alternative_suggestion}"
    ),
    "tool_failure": (
        "I attempted to retrieve information using the scheduling system, but encountered an error:\n\n"
        "**Error**: {error_message}\n\n"
        "This might be due to:\n"
        "- Temporary system connectivity issues\n"
        "- Missing data for the requested period\n"
        "- Insufficient permissions for this query\n\n"
        "Please try:\n"
        "1. Rephrasing your question with more specific details\n"
        "2. Checking if you have access to view this information\n"
        "3. Contacting the scheduling coordinator directly if urgent\n\n"
        "I apologize for the inconvenience."
    ),
    "insufficient_context": (
        "I don't have enough information to answer that question accurately. "
        "To help you better, I need:\n\n"
        "{missing_info}\n\n"
        "Could you provide these details? Alternatively, I can help you:\n"
        "- Check a different date or rotation\n"
        "- Explain general scheduling policies\n"
        "- Guide you to the right resource for this question"
    ),
    "permission_denied": (
        "I don't have permission to access that information. "
        "This might be because:\n\n"
        "- You're trying to view another person's detailed schedule\n"
        "- The information is restricted to administrators\n"
        "- You're not authenticated or your session expired\n\n"
        "If you believe you should have access, please contact your program coordinator "
        "or check your system permissions."
    ),
    "ambiguous_request": (
        "Your request could be interpreted in multiple ways. Did you mean:\n\n"
        "{options}\n\n"
        "Please clarify which one you're asking about, or provide more details like:\n"
        "- Specific dates\n"
        "- Rotation or shift type\n"
        "- Whether this is for you or someone else"
    )
}


# =============================================================================
# PROMPT MANAGER CLASS
# =============================================================================

class PromptManager:
    """
    Manages prompt templates and builds complete prompts for the scheduling assistant.

    This class provides a centralized interface for:
    - Loading and managing prompt templates
    - Building prompts with RAG context injection
    - Selecting appropriate task-specific prompts
    - Supporting prompt versioning and A/B testing
    - Formatting few-shot examples

    Example:
        >>> pm = PromptManager()
        >>> prompt = pm.build_prompt(
        ...     query="Can I swap Friday?",
        ...     context="Dr. Smith is on call Friday...",
        ...     task_type="swap"
        ... )
        >>> print(prompt)
    """

    def __init__(self, version: str = "v1"):
        """
        Initialize the PromptManager.

        Args:
            version: Prompt version to use (for A/B testing, default: "v1")
        """
        self.version = version
        self.system_prompt = SCHEDULING_ASSISTANT_SYSTEM_PROMPT
        self.task_prompts = {
            "swap": SWAP_ANALYSIS_PROMPT,
            "compliance": COMPLIANCE_CHECK_PROMPT,
            "schedule": SCHEDULE_EXPLANATION_PROMPT,
            "coverage": COVERAGE_ANALYSIS_PROMPT,
        }
        self.error_prompts = ERROR_HANDLING_PROMPTS
        self.few_shot_examples = FEW_SHOT_EXAMPLES

    def build_prompt(
        self,
        query: str,
        context: str | None = None,
        task_type: str | None = None,
        include_examples: bool = False
    ) -> str:
        """
        Build a complete prompt for the LLM.

        Args:
            query: User's question or request
            context: Retrieved context from RAG (optional)
            task_type: Type of task (swap, compliance, coverage, schedule, or None)
            include_examples: Whether to include few-shot examples (default: False)

        Returns:
            str: Complete formatted prompt

        Example:
            >>> pm = PromptManager()
            >>> prompt = pm.build_prompt(
            ...     query="Am I over hours?",
            ...     context="Your hours: 72 this week",
            ...     task_type="compliance"
            ... )
        """
        task_prompt = self.task_prompts.get(task_type) if task_type else None

        # Build base prompt with RAG context
        prompt = build_rag_prompt(
            query=query,
            context=context or "",
            system_prompt=self.system_prompt,
            task_prompt=task_prompt
        )

        # Optionally include few-shot examples
        if include_examples and task_type:
            examples = self._get_relevant_examples(task_type)
            if examples:
                prompt += "\n\n## EXAMPLES OF SIMILAR QUERIES\n\n"
                prompt += examples

        return prompt

    def build_tool_response(
        self,
        original_query: str,
        tool_results: str,
        task_type: str = "general"
    ) -> str:
        """
        Build a prompt for synthesizing tool results into a user response.

        Args:
            original_query: The user's original question
            tool_results: Results from MCP tool calls
            task_type: Type of task (swap, compliance, coverage, schedule, general)

        Returns:
            str: Prompt for LLM to generate final response
        """
        return build_tool_response_prompt(original_query, tool_results, task_type)

    def get_error_prompt(
        self,
        error_type: str,
        **kwargs
    ) -> str:
        """
        Get a formatted error handling prompt.

        Args:
            error_type: Type of error (no_swap_candidates, acgme_violation, etc.)
            **kwargs: Variables to format into the error prompt

        Returns:
            str: Formatted error message

        Example:
            >>> pm = PromptManager()
            >>> msg = pm.get_error_prompt(
            ...     "no_swap_candidates",
            ...     shift_type="call",
            ...     date="Jan 19"
            ... )
        """
        template = self.error_prompts.get(error_type, "An error occurred. Please try again.")
        try:
            return template.format(**kwargs)
        except KeyError:
            # If formatting fails, return template as-is
            return template

    def get_few_shot_example(self, example_type: str) -> dict | None:
        """
        Get a specific few-shot example.

        Args:
            example_type: Type of example (swap_request, hours_check, etc.)

        Returns:
            dict: Example with query, reasoning, tool_call, response_template
                  or None if not found

        Example:
            >>> pm = PromptManager()
            >>> example = pm.get_few_shot_example("swap_request")
            >>> print(example["query"])
        """
        return self.few_shot_examples.get(example_type)

    def _get_relevant_examples(self, task_type: str) -> str:
        """
        Get formatted few-shot examples relevant to the task type.

        Args:
            task_type: Type of task (swap, compliance, etc.)

        Returns:
            str: Formatted examples as a string
        """
        # Map task types to example types
        task_to_examples = {
            "swap": ["swap_request"],
            "compliance": ["hours_check"],
            "schedule": ["schedule_query", "assignment_explanation"],
            "coverage": ["coverage_gap"],
        }

        example_types = task_to_examples.get(task_type, [])
        if not example_types:
            return ""

        formatted_examples = []
        for ex_type in example_types:
            example = self.few_shot_examples.get(ex_type)
            if example:
                formatted = (
                    f"**Query**: {example['query']}\n"
                    f"**Reasoning**: {example['reasoning']}\n"
                    f"**Tool Call**: `{example['tool_call']}`\n"
                    f"**Response Template**: {example['response_template']}\n"
                )
                formatted_examples.append(formatted)

        return "\n---\n".join(formatted_examples)

    def set_version(self, version: str) -> None:
        """
        Set the prompt version (for A/B testing).

        Args:
            version: Version identifier (e.g., "v1", "v2", "experimental")

        Note:
            Future versions can load different prompt variants from configuration.
        """
        self.version = version

    def get_version(self) -> str:
        """
        Get the current prompt version.

        Returns:
            str: Current version identifier
        """
        return self.version

    def add_custom_task_prompt(
        self,
        task_name: str,
        prompt_template: str
    ) -> None:
        """
        Add a custom task-specific prompt.

        Args:
            task_name: Name of the task (e.g., "vacation_request")
            prompt_template: The prompt template text

        Example:
            >>> pm = PromptManager()
            >>> pm.add_custom_task_prompt(
            ...     "vacation_request",
            ...     "You are analyzing a vacation request. Check ACGME impact..."
            ... )
        """
        self.task_prompts[task_name] = prompt_template

    def get_system_prompt(self) -> str:
        """
        Get the base system prompt.

        Returns:
            str: The base system prompt
        """
        return self.system_prompt

    def get_all_task_types(self) -> list[str]:
        """
        Get a list of all available task types.

        Returns:
            list[str]: List of task type identifiers
        """
        return list(self.task_prompts.keys())


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_default_prompt_manager() -> PromptManager:
    """
    Get a default PromptManager instance.

    Returns:
        PromptManager: Pre-configured prompt manager

    Example:
        >>> pm = get_default_prompt_manager()
        >>> prompt = pm.build_prompt("Can I swap Friday?", task_type="swap")
    """
    return PromptManager(version="v1")


def format_schedule_data_for_context(schedule_data: dict) -> str:
    """
    Format schedule data dictionary into readable context for RAG injection.

    Args:
        schedule_data: Dictionary containing schedule information

    Returns:
        str: Formatted context string

    Example:
        >>> data = {
        ...     "person": "Dr. Smith",
        ...     "assignments": [{"date": "2024-01-15", "rotation": "Clinic"}]
        ... }
        >>> context = format_schedule_data_for_context(data)
    """
    lines = []

    if "person" in schedule_data:
        lines.append(f"Person: {schedule_data['person']}")

    if "assignments" in schedule_data:
        lines.append("\nAssignments:")
        for assignment in schedule_data["assignments"]:
            date = assignment.get("date", "Unknown")
            rotation = assignment.get("rotation", "Unknown")
            shift_type = assignment.get("shift_type", "")
            lines.append(f"  - {date}: {rotation} {shift_type}".strip())

    if "hours_summary" in schedule_data:
        lines.append("\nWork Hours Summary:")
        summary = schedule_data["hours_summary"]
        for key, value in summary.items():
            lines.append(f"  {key}: {value}")

    if "compliance_status" in schedule_data:
        lines.append(f"\nCompliance Status: {schedule_data['compliance_status']}")

    return "\n".join(lines)


# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Main prompts
    "SCHEDULING_ASSISTANT_SYSTEM_PROMPT",
    "SWAP_ANALYSIS_PROMPT",
    "COMPLIANCE_CHECK_PROMPT",
    "SCHEDULE_EXPLANATION_PROMPT",
    "COVERAGE_ANALYSIS_PROMPT",
    # Functions
    "build_rag_prompt",
    "build_tool_response_prompt",
    "format_schedule_data_for_context",
    # Classes
    "PromptManager",
    "get_default_prompt_manager",
    # Constants
    "FEW_SHOT_EXAMPLES",
    "ERROR_HANDLING_PROMPTS",
]
