"""Service for Claude Code integration and execution."""

import json
import logging
from typing import AsyncGenerator, Any, Dict
import os

import anthropic

from app.schemas.chat import ClaudeCodeRequest, StreamUpdate

logger = logging.getLogger(__name__)


class ClaudeService:
    """Handles Claude API interactions with streaming support."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model

    async def stream_task(
        self,
        request: ClaudeCodeRequest,
        user_id: str,
    ) -> AsyncGenerator[StreamUpdate, None]:
        """
        Stream task execution with real-time updates.
        Yields StreamUpdate objects as they become available.
        """
        try:
            # Build system prompt based on action
            system_prompt = self._build_system_prompt(request.action)

            # Build user message with context
            user_message = self._build_user_message(request)

            # Stream from Claude
            with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ],
            ) as stream:
                current_text = ""
                code_blocks = []
                artifacts = []

                for text in stream.text_stream:
                    current_text += text

                    # Yield text updates
                    yield StreamUpdate(
                        type="text",
                        content=text,
                    )

                    # Check for code blocks (simplified detection)
                    if "```" in text:
                        # More sophisticated code block parsing would go here
                        pass

                    # Check for artifact markers
                    if "[ARTIFACT]" in text:
                        yield StreamUpdate(
                            type="artifact",
                            content="Artifact generated",
                            metadata={
                                "type": "schedule",
                                "title": "Generated Schedule",
                            },
                        )

                # Final completion update
                yield StreamUpdate(
                    type="status",
                    content="Task completed successfully",
                )

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {str(e)}")
            yield StreamUpdate(
                type="error",
                content=f"API Error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Unexpected error in stream_task: {str(e)}")
            yield StreamUpdate(
                type="error",
                content=f"Unexpected error: {str(e)}",
            )

    async def execute_task(
        self,
        request: ClaudeCodeRequest,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Execute a task without streaming (returns complete result).
        """
        try:
            system_prompt = self._build_system_prompt(request.action)
            user_message = self._build_user_message(request)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ],
            )

            return {
                "status": "success",
                "result": response.content[0].text if response.content else "",
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            }
        except Exception as e:
            logger.error(f"Task execution error: {str(e)}")
            raise

    def _build_system_prompt(self, action: str) -> str:
        """
        Build specialized system prompt based on action type.
        """
        base_prompt = """You are an expert scheduling assistant for medical residency programs.
        You have deep knowledge of ACGME regulations, scheduling constraints, and fairness principles.
        Provide practical, implementable solutions."""

        action_prompts = {
            "generate_schedule": base_prompt
            + """
        When generating schedules:
        1. Ensure compliance with ACGME duty hour regulations
        2. Distribute rotations equitably among residents
        3. Avoid consecutive night shifts
        4. Consider resident preferences and restrictions
        5. Generate output in JSON format for system integration
        """,
            "validate_compliance": base_prompt
            + """
        When checking compliance:
        1. Flag violations of 80-hour weekly maximums
        2. Identify duty hour limit violations
        3. Check for adequate rest periods
        4. Provide specific remediation suggestions
        5. Output violations in structured JSON
        """,
            "optimize_fairness": base_prompt
            + """
        When analyzing fairness:
        1. Calculate rotation distribution variance
        2. Identify inequities in call schedules
        3. Assess night shift frequency distribution
        4. Recommend equity improvements
        5. Output metrics and recommendations in JSON
        """,
            "export_report": base_prompt
            + """
        When generating reports:
        1. Summarize schedule metrics
        2. Highlight compliance status
        3. Note fairness indicators
        4. Provide actionable recommendations
        5. Format as professional report
        """,
            "custom": base_prompt,
        }

        return action_prompts.get(action, base_prompt)

    def _build_user_message(self, request: ClaudeCodeRequest) -> str:
        """
        Build user message with context and query.
        """
        context_str = json.dumps(request.context.dict(), indent=2, default=str)

        message = f"""Program Context:
{context_str}

Task Parameters:
{json.dumps(request.parameters or {}, indent=2)}

User Request:
{request.userQuery}

Please provide a detailed, structured response that can be integrated into the scheduling system.
        """

        return message
