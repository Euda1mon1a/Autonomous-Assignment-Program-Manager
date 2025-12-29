"""
Example usage of scheduling assistant prompts.

This script demonstrates how to use the PromptManager and various prompt templates
for different scheduling scenarios.

Run this script to see example prompts:
    python -m app.prompts.examples
"""

from app.prompts import (
    get_default_prompt_manager,
    format_schedule_data_for_context,
)


def example_swap_request():
    """Example: User requests a schedule swap."""
    print("=" * 80)
    print("EXAMPLE 1: Swap Request")
    print("=" * 80)

    pm = get_default_prompt_manager()

    # Simulated RAG context
    context = """
Dr. Sarah Smith (PGY-2) is assigned to:
- Friday, Jan 19, 2024: Inpatient Call (7 AM - 7 AM next day, 24 hours)

Current work hours:
- This week (Jan 15-21): 48 hours scheduled (before Friday call)
- After Friday call: 72 hours total
- 4-week rolling average: 68 hours

Potential swap candidates:
- Dr. James Lee (PGY-2): Available, same rotation level, 52 hours this week
- Dr. Maria Garcia (PGY-3): Not available, already scheduled
"""

    query = "Can I swap my Friday call shift with someone? I have a family emergency."

    prompt = pm.build_prompt(
        query=query,
        context=context,
        task_type="swap",
        include_examples=False
    )

    print(f"\nUSER QUERY:\n{query}\n")
    print(f"GENERATED PROMPT:\n{prompt}\n")
    print("\n")


def example_compliance_check():
    """Example: User checks work hour compliance."""
    print("=" * 80)
    print("EXAMPLE 2: Compliance Check")
    print("=" * 80)

    pm = get_default_prompt_manager()

    # Format schedule data as context
    schedule_data = {
        "person": "Dr. Michael Chen (PGY-1)",
        "assignments": [
            {"date": "2024-01-15", "rotation": "Clinic", "shift_type": "AM", "hours": 8},
            {"date": "2024-01-15", "rotation": "Clinic", "shift_type": "PM", "hours": 4},
            {"date": "2024-01-16", "rotation": "Inpatient", "shift_type": "Day", "hours": 12},
            {"date": "2024-01-17", "rotation": "Inpatient", "shift_type": "Day", "hours": 12},
            {"date": "2024-01-18", "rotation": "Inpatient", "shift_type": "Day", "hours": 12},
            {"date": "2024-01-19", "rotation": "Clinic", "shift_type": "AM", "hours": 8},
            {"date": "2024-01-20", "rotation": "Call", "shift_type": "24hr", "hours": 24},
        ],
        "hours_summary": {
            "This week": "80 hours",
            "Last week": "68 hours",
            "4-week average": "74 hours"
        },
        "compliance_status": "AT LIMIT - 80 hours this week"
    }

    context = format_schedule_data_for_context(schedule_data)

    query = "Am I over my work hour limit this week?"

    prompt = pm.build_prompt(
        query=query,
        context=context,
        task_type="compliance"
    )

    print(f"\nUSER QUERY:\n{query}\n")
    print(f"FORMATTED CONTEXT:\n{context}\n")
    print(f"\nGENERATED PROMPT LENGTH: {len(prompt)} characters\n")
    print(f"FIRST 500 CHARS:\n{prompt[:500]}...\n")


def example_coverage_gap():
    """Example: Checking for coverage gaps."""
    print("=" * 80)
    print("EXAMPLE 3: Coverage Gap Analysis")
    print("=" * 80)

    pm = get_default_prompt_manager()

    context = """
Coverage Analysis for Jan 22-28, 2024:

Inpatient Medicine:
- Mon AM: 2/2 residents ✓
- Mon PM: 2/2 residents ✓
- Tue AM: 1/2 residents ⚠️ (Dr. Smith on leave)
- Tue PM: 1/2 residents ⚠️
- Wed AM: 0/2 residents ❌ CRITICAL GAP
- Wed PM: 2/2 residents ✓

Night Float:
- Mon: 1/1 resident ✓
- Tue: 1/1 resident ✓
- Wed: 0/1 resident ❌ CRITICAL GAP

Call Coverage:
- All shifts filled ✓

ACGME Concerns:
- Wednesday: No residents assigned to inpatient or night float
- Tuesday: Supervision ratio at risk (1:10 resident:patient, need 1:5 for PGY-1)
"""

    query = "Are there any coverage gaps next week that I should be worried about?"

    prompt = pm.build_prompt(
        query=query,
        context=context,
        task_type="coverage"
    )

    print(f"\nUSER QUERY:\n{query}\n")
    print(f"GENERATED PROMPT:\n{prompt}\n")


def example_error_handling():
    """Example: Error handling prompts."""
    print("=" * 80)
    print("EXAMPLE 4: Error Handling")
    print("=" * 80)

    pm = get_default_prompt_manager()

    # No swap candidates
    error1 = pm.get_error_prompt(
        "no_swap_candidates",
        shift_type="call",
        date="Jan 19"
    )
    print("\nERROR TYPE: No Swap Candidates")
    print(f"{error1}\n")

    # ACGME violation
    error2 = pm.get_error_prompt(
        "acgme_violation",
        rule_name="80-Hour Weekly Limit",
        current_value="72 hours",
        projected_value="96 hours",
        limit="80 hours (4-week average)",
        alternative_suggestion="Swap a different shift earlier in the week to stay under limit"
    )
    print("\nERROR TYPE: ACGME Violation")
    print(f"{error2}\n")

    # Tool failure
    error3 = pm.get_error_prompt(
        "tool_failure",
        error_message="Database connection timeout after 30 seconds"
    )
    print("\nERROR TYPE: Tool Failure")
    print(f"{error3}\n")


def example_few_shot():
    """Example: Using few-shot examples."""
    print("=" * 80)
    print("EXAMPLE 5: Few-Shot Examples")
    print("=" * 80)

    pm = get_default_prompt_manager()

    # Get a specific example
    example = pm.get_few_shot_example("swap_request")

    print("\nFEW-SHOT EXAMPLE: Swap Request")
    print(f"Query: {example['query']}")
    print(f"Reasoning: {example['reasoning']}")
    print(f"Tool Call: {example['tool_call']}")
    print(f"\nResponse Template:\n{example['response_template']}\n")

    # Build prompt with examples included
    query = "Can I swap my Monday clinic shift?"
    prompt = pm.build_prompt(
        query=query,
        context="Dr. Jones is assigned to Monday clinic...",
        task_type="swap",
        include_examples=True  # Include few-shot examples
    )

    print(f"\nPROMPT WITH EXAMPLES (length: {len(prompt)} chars)")
    print("Examples are included in the prompt to guide the model.\n")


def example_tool_response():
    """Example: Building a prompt to synthesize tool results."""
    print("=" * 80)
    print("EXAMPLE 6: Tool Response Synthesis")
    print("=" * 80)

    pm = get_default_prompt_manager()

    original_query = "Can I swap my Friday call shift?"

    # Simulated tool results (JSON)
    tool_results = """{
  "candidates": [
    {
      "id": "person_456",
      "name": "Dr. James Lee",
      "rotation": "Inpatient",
      "compatible": true,
      "hours_after_swap": 76,
      "acgme_compliant": true,
      "reason": "Same rotation level, available, swap maintains compliance"
    },
    {
      "id": "person_789",
      "name": "Dr. Emily White",
      "rotation": "Clinic",
      "compatible": false,
      "hours_after_swap": 84,
      "acgme_compliant": false,
      "reason": "Swap would put Dr. White over 80-hour limit"
    }
  ],
  "recommendation": "Dr. James Lee is the best candidate"
}"""

    response_prompt = pm.build_tool_response(
        original_query=original_query,
        tool_results=tool_results,
        task_type="swap"
    )

    print(f"\nORIGINAL QUERY:\n{original_query}\n")
    print(f"TOOL RESULTS:\n{tool_results}\n")
    print(f"\nRESPONSE SYNTHESIS PROMPT:\n{response_prompt}\n")


def example_custom_task():
    """Example: Adding a custom task type."""
    print("=" * 80)
    print("EXAMPLE 7: Custom Task Prompt")
    print("=" * 80)

    pm = get_default_prompt_manager()

    # Add a custom task type
    vacation_prompt = """You are analyzing a vacation/leave request. Your task is to:

1. **Check ACGME impact**: Ensure the absence doesn't violate work hour rules for others
2. **Verify coverage**: Ensure minimum staffing is maintained during the absence
3. **Suggest alternatives**: If requested dates are problematic, suggest better dates
4. **Consider training requirements**: Check if absence affects required training milestones

When responding:
- Approve if no issues
- Explain concerns if problematic
- Suggest alternative dates if needed
- Reference facility leave policies
"""

    pm.add_custom_task_prompt("vacation_request", vacation_prompt)

    query = "Can I take leave from Feb 1-7 for a family event?"
    context = "Your training: 80% clinic completion, on track for milestones..."

    prompt = pm.build_prompt(
        query=query,
        context=context,
        task_type="vacation_request"
    )

    print(f"\nCUSTOM TASK: vacation_request")
    print(f"QUERY: {query}\n")
    print(f"Available task types: {pm.get_all_task_types()}\n")
    print(f"Generated prompt includes custom task instructions.\n")


def main():
    """Run all examples."""
    print("\n")
    print("=" * 80)
    print(" SCHEDULING ASSISTANT PROMPT EXAMPLES")
    print("=" * 80)
    print("\n")

    examples = [
        example_swap_request,
        example_compliance_check,
        example_coverage_gap,
        example_error_handling,
        example_few_shot,
        example_tool_response,
        example_custom_task,
    ]

    for i, example_func in enumerate(examples, 1):
        example_func()
        if i < len(examples):
            input("\nPress Enter to continue to next example...")
            print("\n")

    print("=" * 80)
    print("All examples completed!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review the generated prompts")
    print("2. Test with your local LLM (Mistral-7B or Llama)")
    print("3. Adjust prompts based on model performance")
    print("4. Integrate with LLMService and RAG pipeline")
    print("\nSee: backend/app/prompts/README.md for full documentation")
    print("=" * 80)


if __name__ == "__main__":
    main()
