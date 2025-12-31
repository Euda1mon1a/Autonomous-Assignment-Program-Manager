"""Tests for Claude service."""

import json
import os
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import anthropic
import pytest

from app.schemas.chat import (
    ClaudeCodeExecutionContext,
    ClaudeCodeRequest,
    ConstraintContext,
    ResidentContext,
    RotationContext,
    ScheduleContext,
    StreamUpdate,
)
from app.services.claude_service import ClaudeService


class TestClaudeServiceInitialization:
    """Test suite for ClaudeService initialization."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-api-key-123"}, clear=True)
    def test_initialization_with_api_key(self):
        """Test successful initialization with API key."""
        service = ClaudeService()

        assert service.api_key == "test-api-key-123"
        assert service.client is not None
        assert service.model == "claude-3-5-sonnet-20241022"

    @patch.dict(os.environ, {}, clear=True)
    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY environment variable not set"):
            ClaudeService()

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=True)
    def test_initialization_with_empty_api_key(self):
        """Test initialization fails with empty API key."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY environment variable not set"):
            ClaudeService()


class TestClaudeServiceBuildSystemPrompt:
    """Test suite for ClaudeService._build_system_prompt()."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def setup_method(self):
        """Setup service for each test."""
        self.service = ClaudeService()

    def test_build_system_prompt_generate_schedule(self):
        """Test system prompt for generate_schedule action."""
        prompt = self.service._build_system_prompt("generate_schedule")

        assert "expert scheduling assistant for medical residency programs" in prompt
        assert "ACGME regulations" in prompt
        assert "ACGME duty hour regulations" in prompt
        assert "Distribute rotations equitably" in prompt
        assert "consecutive night shifts" in prompt
        assert "JSON format" in prompt

    def test_build_system_prompt_validate_compliance(self):
        """Test system prompt for validate_compliance action."""
        prompt = self.service._build_system_prompt("validate_compliance")

        assert "expert scheduling assistant" in prompt
        assert "80-hour weekly maximums" in prompt
        assert "duty hour limit violations" in prompt
        assert "adequate rest periods" in prompt
        assert "remediation suggestions" in prompt
        assert "structured JSON" in prompt

    def test_build_system_prompt_optimize_fairness(self):
        """Test system prompt for optimize_fairness action."""
        prompt = self.service._build_system_prompt("optimize_fairness")

        assert "expert scheduling assistant" in prompt
        assert "rotation distribution variance" in prompt
        assert "inequities in call schedules" in prompt
        assert "night shift frequency distribution" in prompt
        assert "equity improvements" in prompt
        assert "JSON" in prompt

    def test_build_system_prompt_export_report(self):
        """Test system prompt for export_report action."""
        prompt = self.service._build_system_prompt("export_report")

        assert "expert scheduling assistant" in prompt
        assert "schedule metrics" in prompt
        assert "compliance status" in prompt
        assert "fairness indicators" in prompt
        assert "actionable recommendations" in prompt
        assert "professional report" in prompt

    def test_build_system_prompt_custom(self):
        """Test system prompt for custom action."""
        prompt = self.service._build_system_prompt("custom")

        assert "expert scheduling assistant for medical residency programs" in prompt
        assert "ACGME regulations" in prompt
        assert "implementable solutions" in prompt

    def test_build_system_prompt_unknown_action(self):
        """Test system prompt for unknown action defaults to base prompt."""
        prompt = self.service._build_system_prompt("unknown_action_type")

        assert "expert scheduling assistant for medical residency programs" in prompt
        assert "ACGME regulations" in prompt
        # Should not contain action-specific content
        assert "ACGME duty hour regulations" not in prompt
        assert "80-hour weekly maximums" not in prompt


class TestClaudeServiceBuildUserMessage:
    """Test suite for ClaudeService._build_user_message()."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def setup_method(self):
        """Setup service for each test."""
        self.service = ClaudeService()

    def create_sample_request(
        self,
        action: str = "custom",
        user_query: str = "Test query",
        parameters: dict | None = None,
    ) -> ClaudeCodeRequest:
        """Helper to create a sample request."""
        context = ClaudeCodeExecutionContext(
            program_id=str(uuid4()),
            admin_id=str(uuid4()),
            session_id=str(uuid4()),
            constraints=ConstraintContext(
                max_hours_per_week=80,
                max_consecutive_days=7,
                min_rest_days=1,
            ),
            residents=[
                ResidentContext(
                    id=str(uuid4()),
                    name="Dr. Test Resident",
                    preferred_rotations=["clinic"],
                    restrictions=["no_weekends"],
                )
            ],
        )

        return ClaudeCodeRequest(
            action=action,
            context=context,
            parameters=parameters,
            userQuery=user_query,
        )

    def test_build_user_message_basic(self):
        """Test building user message with basic request."""
        request = self.create_sample_request(
            action="generate_schedule",
            user_query="Generate a new schedule for Q1",
        )

        message = self.service._build_user_message(request)

        assert "Program Context:" in message
        assert "Task Parameters:" in message
        assert "User Request:" in message
        assert "Generate a new schedule for Q1" in message
        assert request.context.program_id in message
        assert request.context.admin_id in message

    def test_build_user_message_with_parameters(self):
        """Test building user message with custom parameters."""
        request = self.create_sample_request(
            action="optimize_fairness",
            user_query="Optimize the schedule for fairness",
            parameters={
                "optimization_type": "rotation_distribution",
                "target_variance": 0.1,
                "priority": "high",
            },
        )

        message = self.service._build_user_message(request)

        assert "Program Context:" in message
        assert "Task Parameters:" in message
        assert "optimization_type" in message
        assert "rotation_distribution" in message
        assert "target_variance" in message
        assert "0.1" in message

    def test_build_user_message_with_empty_parameters(self):
        """Test building user message with no parameters."""
        request = self.create_sample_request(
            action="custom",
            user_query="What are the current schedules?",
            parameters=None,
        )

        message = self.service._build_user_message(request)

        assert "Program Context:" in message
        assert "Task Parameters:" in message
        assert "User Request:" in message
        assert "What are the current schedules?" in message
        # Should show empty dict for None parameters
        assert "{}" in message

    def test_build_user_message_includes_constraints(self):
        """Test that message includes constraint context."""
        request = self.create_sample_request()

        message = self.service._build_user_message(request)

        # Context should be JSON-formatted with constraint details
        assert "max_hours_per_week" in message.lower() or "80" in message
        assert "constraints" in message.lower()

    def test_build_user_message_includes_residents(self):
        """Test that message includes resident context."""
        request = self.create_sample_request()

        message = self.service._build_user_message(request)

        assert "Dr. Test Resident" in message
        assert "residents" in message.lower()


class TestClaudeServiceStreamTask:
    """Test suite for ClaudeService.stream_task()."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def setup_method(self):
        """Setup service for each test."""
        self.service = ClaudeService()

    def create_sample_request(self) -> ClaudeCodeRequest:
        """Helper to create a sample request."""
        context = ClaudeCodeExecutionContext(
            program_id=str(uuid4()),
            admin_id=str(uuid4()),
            session_id=str(uuid4()),
        )

        return ClaudeCodeRequest(
            action="custom",
            context=context,
            userQuery="Test query",
        )

    @pytest.mark.asyncio
    async def test_stream_task_success(self):
        """Test successful streaming task execution."""
        request = self.create_sample_request()

        # Mock the streaming response
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=None)
        mock_stream.text_stream = iter(["Hello ", "world", "!"])

        with patch.object(
            self.service.client.messages,
            "stream",
            return_value=mock_stream,
        ):
            updates = []
            async for update in self.service.stream_task(request, user_id="test-user"):
                updates.append(update)

        # Should have text updates + completion status
        assert len(updates) >= 4  # 3 text + 1 status
        assert all(isinstance(u, StreamUpdate) for u in updates)

        # Check text updates
        text_updates = [u for u in updates if u.type == "text"]
        assert len(text_updates) == 3
        assert text_updates[0].content == "Hello "
        assert text_updates[1].content == "world"
        assert text_updates[2].content == "!"

        # Check completion status
        status_updates = [u for u in updates if u.type == "status"]
        assert len(status_updates) == 1
        assert "completed successfully" in status_updates[0].content

    @pytest.mark.asyncio
    async def test_stream_task_with_artifact_marker(self):
        """Test streaming with artifact marker detection."""
        request = self.create_sample_request()

        # Mock stream with artifact marker
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=None)
        mock_stream.text_stream = iter(["Here is your ", "[ARTIFACT]", " schedule"])

        with patch.object(
            self.service.client.messages,
            "stream",
            return_value=mock_stream,
        ):
            updates = []
            async for update in self.service.stream_task(request, user_id="test-user"):
                updates.append(update)

        # Should have artifact update
        artifact_updates = [u for u in updates if u.type == "artifact"]
        assert len(artifact_updates) == 1
        assert artifact_updates[0].content == "Artifact generated"
        assert artifact_updates[0].metadata is not None
        assert artifact_updates[0].metadata["type"] == "schedule"

    @pytest.mark.asyncio
    async def test_stream_task_api_error(self):
        """Test streaming handles Anthropic API errors."""
        request = self.create_sample_request()

        # Mock API error
        with patch.object(
            self.service.client.messages,
            "stream",
            side_effect=anthropic.APIError("API rate limit exceeded"),
        ):
            updates = []
            async for update in self.service.stream_task(request, user_id="test-user"):
                updates.append(update)

        # Should have error update
        assert len(updates) == 1
        assert updates[0].type == "error"
        assert "API Error" in updates[0].content
        assert "API rate limit exceeded" in updates[0].content

    @pytest.mark.asyncio
    async def test_stream_task_generic_exception(self):
        """Test streaming handles generic exceptions."""
        request = self.create_sample_request()

        # Mock generic exception
        with patch.object(
            self.service.client.messages,
            "stream",
            side_effect=Exception("Connection timeout"),
        ):
            updates = []
            async for update in self.service.stream_task(request, user_id="test-user"):
                updates.append(update)

        # Should have error update
        assert len(updates) == 1
        assert updates[0].type == "error"
        assert "Unexpected error" in updates[0].content
        assert "Connection timeout" in updates[0].content

    @pytest.mark.asyncio
    async def test_stream_task_builds_correct_request(self):
        """Test that stream_task builds correct API request."""
        request = self.create_sample_request()
        request.action = "generate_schedule"

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=None)
        mock_stream.text_stream = iter(["test"])

        with patch.object(
            self.service.client.messages,
            "stream",
            return_value=mock_stream,
        ) as mock_stream_method:
            async for _ in self.service.stream_task(request, user_id="test-user"):
                pass

        # Verify API was called with correct parameters
        mock_stream_method.assert_called_once()
        call_kwargs = mock_stream_method.call_args[1]

        assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert call_kwargs["max_tokens"] == 4096
        assert "ACGME duty hour regulations" in call_kwargs["system"]
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"


class TestClaudeServiceExecuteTask:
    """Test suite for ClaudeService.execute_task()."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def setup_method(self):
        """Setup service for each test."""
        self.service = ClaudeService()

    def create_sample_request(self) -> ClaudeCodeRequest:
        """Helper to create a sample request."""
        context = ClaudeCodeExecutionContext(
            program_id=str(uuid4()),
            admin_id=str(uuid4()),
            session_id=str(uuid4()),
        )

        return ClaudeCodeRequest(
            action="custom",
            context=context,
            userQuery="Test query",
        )

    @pytest.mark.asyncio
    async def test_execute_task_success(self):
        """Test successful non-streaming task execution."""
        request = self.create_sample_request()

        # Mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is the response text")]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

        with patch.object(
            self.service.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await self.service.execute_task(request, user_id="test-user")

        assert result["status"] == "success"
        assert result["result"] == "This is the response text"
        assert result["usage"]["input_tokens"] == 100
        assert result["usage"]["output_tokens"] == 50

    @pytest.mark.asyncio
    async def test_execute_task_with_empty_content(self):
        """Test execution with empty content response."""
        request = self.create_sample_request()

        # Mock response with empty content
        mock_response = MagicMock()
        mock_response.content = []
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=0)

        with patch.object(
            self.service.client.messages,
            "create",
            return_value=mock_response,
        ):
            result = await self.service.execute_task(request, user_id="test-user")

        assert result["status"] == "success"
        assert result["result"] == ""
        assert result["usage"]["input_tokens"] == 10

    @pytest.mark.asyncio
    async def test_execute_task_builds_correct_request(self):
        """Test that execute_task builds correct API request."""
        request = self.create_sample_request()
        request.action = "validate_compliance"

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=10)

        with patch.object(
            self.service.client.messages,
            "create",
            return_value=mock_response,
        ) as mock_create:
            await self.service.execute_task(request, user_id="test-user")

        # Verify API was called with correct parameters
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]

        assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert call_kwargs["max_tokens"] == 4096
        assert "80-hour weekly maximums" in call_kwargs["system"]
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_execute_task_api_error(self):
        """Test execution handles API errors."""
        request = self.create_sample_request()

        with patch.object(
            self.service.client.messages,
            "create",
            side_effect=anthropic.APIError("Invalid API key"),
        ):
            with pytest.raises(anthropic.APIError, match="Invalid API key"):
                await self.service.execute_task(request, user_id="test-user")

    @pytest.mark.asyncio
    async def test_execute_task_generic_exception(self):
        """Test execution handles generic exceptions."""
        request = self.create_sample_request()

        with patch.object(
            self.service.client.messages,
            "create",
            side_effect=Exception("Network error"),
        ):
            with pytest.raises(Exception, match="Network error"):
                await self.service.execute_task(request, user_id="test-user")

    @pytest.mark.asyncio
    async def test_execute_task_different_actions(self):
        """Test execution with different action types."""
        actions = [
            "generate_schedule",
            "validate_compliance",
            "optimize_fairness",
            "export_report",
            "custom",
        ]

        for action in actions:
            request = self.create_sample_request()
            request.action = action

            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=f"Response for {action}")]
            mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)

            with patch.object(
                self.service.client.messages,
                "create",
                return_value=mock_response,
            ):
                result = await self.service.execute_task(request, user_id="test-user")

            assert result["status"] == "success"
            assert f"Response for {action}" in result["result"]


class TestClaudeServiceIntegration:
    """Integration tests for ClaudeService."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
    def test_service_uses_correct_model(self):
        """Test that service uses the correct Claude model."""
        service = ClaudeService()

        assert service.model == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_stream_and_execute_use_same_system_prompt(self):
        """Test that stream_task and execute_task use same system prompt."""
        service = ClaudeService()

        context = ClaudeCodeExecutionContext(
            program_id=str(uuid4()),
            admin_id=str(uuid4()),
            session_id=str(uuid4()),
        )

        request = ClaudeCodeRequest(
            action="generate_schedule",
            context=context,
            userQuery="Test",
        )

        # Mock for streaming
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=None)
        mock_stream.text_stream = iter(["test"])

        stream_system_prompt = None
        with patch.object(
            service.client.messages,
            "stream",
            return_value=mock_stream,
        ) as mock_stream_method:
            async for _ in service.stream_task(request, user_id="test"):
                pass
            stream_system_prompt = mock_stream_method.call_args[1]["system"]

        # Mock for execute
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="test")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=10)

        execute_system_prompt = None
        with patch.object(
            service.client.messages,
            "create",
            return_value=mock_response,
        ) as mock_create:
            await service.execute_task(request, user_id="test")
            execute_system_prompt = mock_create.call_args[1]["system"]

        # Both should use the same system prompt
        assert stream_system_prompt == execute_system_prompt
        assert "ACGME duty hour regulations" in stream_system_prompt
