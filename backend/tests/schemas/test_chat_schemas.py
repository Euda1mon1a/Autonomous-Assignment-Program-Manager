"""Tests for chat integration schemas (defaults, nested models)."""

from datetime import datetime

from app.schemas.chat import (
    StreamUpdate,
    CodeBlock,
    ChatArtifact,
    ChatMessage,
    ConstraintContext,
    ResidentContext,
    RotationContext,
    ScheduleContext,
    ClaudeCodeExecutionContext,
    ClaudeCodeRequest,
    ClaudeCodeResponse,
    ChatSession,
    ChatHistoryExport,
)


class TestStreamUpdate:
    def test_valid(self):
        r = StreamUpdate(type="text", content="Hello")
        assert r.metadata is None

    def test_with_metadata(self):
        r = StreamUpdate(
            type="code", content="print('hi')", metadata={"lang": "python"}
        )
        assert r.metadata["lang"] == "python"


class TestCodeBlock:
    def test_valid(self):
        r = CodeBlock(language="python", code="print(1)")
        assert r.filename is None

    def test_with_filename(self):
        r = CodeBlock(language="typescript", code="console.log(1)", filename="app.ts")
        assert r.filename == "app.ts"


class TestChatArtifact:
    def test_valid(self):
        r = ChatArtifact(
            id="art-1", type="schedule", title="Block 10 Schedule", data={}
        )
        assert r.data == {}


class TestChatMessage:
    def test_valid_minimal(self):
        r = ChatMessage(id="msg-1", role="user", content="Hello")
        assert r.is_streaming is False
        assert r.error is None
        assert r.code_blocks is None
        assert r.artifacts is None

    def test_full(self):
        code = CodeBlock(language="python", code="pass")
        art = ChatArtifact(id="a1", type="report", title="R", data={})
        r = ChatMessage(
            id="msg-2",
            role="assistant",
            content="Here's the result",
            is_streaming=True,
            error=None,
            code_blocks=[code],
            artifacts=[art],
        )
        assert len(r.code_blocks) == 1
        assert len(r.artifacts) == 1


class TestConstraintContext:
    def test_defaults(self):
        r = ConstraintContext()
        assert r.max_hours_per_week == 80
        assert r.max_consecutive_days == 7
        assert r.min_rest_days == 1
        assert r.min_rotation_length == 4
        assert r.custom_rules is None


class TestResidentContext:
    def test_valid_minimal(self):
        r = ResidentContext(id="res-1", name="Dr. Smith")
        assert r.preferred_rotations is None
        assert r.restrictions is None
        assert r.absences is None


class TestRotationContext:
    def test_valid(self):
        r = RotationContext(
            id="rot-1",
            name="ICU",
            residents=["res-1", "res-2"],
            start_date=datetime(2026, 3, 1),
            end_date=datetime(2026, 3, 28),
        )
        assert len(r.residents) == 2


class TestScheduleContext:
    def test_valid(self):
        rot = RotationContext(
            id="r1",
            name="FM",
            residents=[],
            start_date=datetime(2026, 3, 1),
            end_date=datetime(2026, 3, 28),
        )
        r = ScheduleContext(academic_year="2025-2026", weeks=52, rotations=[rot])
        assert len(r.rotations) == 1


class TestClaudeCodeExecutionContext:
    def test_valid_minimal(self):
        r = ClaudeCodeExecutionContext(
            program_id="prog-1", admin_id="admin-1", session_id="sess-1"
        )
        assert r.current_schedule is None
        assert r.constraints is None
        assert r.residents is None


class TestClaudeCodeRequest:
    def test_valid(self):
        ctx = ClaudeCodeExecutionContext(
            program_id="p1", admin_id="a1", session_id="s1"
        )
        r = ClaudeCodeRequest(context=ctx, user_query="Generate a schedule")
        assert r.action == "custom"
        assert r.parameters is None


class TestClaudeCodeResponse:
    def test_valid_minimal(self):
        r = ClaudeCodeResponse(success=True, message="Done")
        assert r.result is None
        assert r.artifacts is None
        assert r.next_actions is None
        assert r.error is None


class TestChatSession:
    def test_valid(self):
        r = ChatSession(id="s1", title="Test Session", program_id="p1", admin_id="a1")
        assert r.messages == []


class TestChatHistoryExport:
    def test_valid(self):
        session = ChatSession(id="s1", title="Test", program_id="p1", admin_id="a1")
        r = ChatHistoryExport(
            session=session,
            total_messages=10,
            artifacts_generated=2,
            duration_minutes=15.5,
        )
        assert r.total_messages == 10
