"""Tests for Claude chat session helpers."""

from datetime import datetime, timedelta

from app.api.routes import claude_chat


def test_get_or_create_session_reuses_existing() -> None:
    claude_chat._sessions.clear()

    session = claude_chat.get_or_create_session("user-1")
    original_last_activity = session.last_activity

    reused = claude_chat.get_or_create_session("user-1", session.session_id)

    assert reused.session_id == session.session_id
    assert reused.user_id == "user-1"
    assert reused.last_activity >= original_last_activity


def test_get_or_create_session_creates_new_when_missing() -> None:
    claude_chat._sessions.clear()

    created = claude_chat.get_or_create_session("user-2", "explicit-id")

    assert created.session_id == "explicit-id"
    assert created.user_id == "user-2"
    assert created.created_at <= datetime.utcnow() + timedelta(seconds=1)
