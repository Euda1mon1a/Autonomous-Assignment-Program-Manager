"""
Prompt management for local LLM scheduling assistant.

This package provides system prompts, task-specific prompts, and prompt management
utilities for the medical residency scheduling assistant.
"""

from .scheduling_assistant import (
    SCHEDULING_ASSISTANT_SYSTEM_PROMPT,
    SWAP_ANALYSIS_PROMPT,
    COMPLIANCE_CHECK_PROMPT,
    SCHEDULE_EXPLANATION_PROMPT,
    COVERAGE_ANALYSIS_PROMPT,
    PromptManager,
    get_default_prompt_manager,
    build_rag_prompt,
    build_tool_response_prompt,
    format_schedule_data_for_context,
)

__all__ = [
    "SCHEDULING_ASSISTANT_SYSTEM_PROMPT",
    "SWAP_ANALYSIS_PROMPT",
    "COMPLIANCE_CHECK_PROMPT",
    "SCHEDULE_EXPLANATION_PROMPT",
    "COVERAGE_ANALYSIS_PROMPT",
    "PromptManager",
    "get_default_prompt_manager",
    "build_rag_prompt",
    "build_tool_response_prompt",
    "format_schedule_data_for_context",
]
