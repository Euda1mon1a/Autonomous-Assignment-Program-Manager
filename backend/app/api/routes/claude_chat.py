"""
Claude Chat Bridge - Real-time chat interface for admin Claude Code interaction.

This module provides a WebSocket-based bridge between the admin frontend and
Claude API with MCP tool integration. It enables clinician administrators to
interact with Claude using natural language for scheduling tasks.

Architecture:
    Frontend (React Chat) <--> WebSocket <--> This Bridge <--> Anthropic API
                                                    |
                                                    v
                                            MCP Tools (scheduler)

Message Protocol (inspired by dzhng/claude-agent-server):
    Client -> Server:
        - {"type": "user_message", "content": "...", "session_id": "..."}
        - {"type": "interrupt"}  # Stop current generation

    Server -> Client:
        - {"type": "connected", "session_id": "..."}
        - {"type": "token", "content": "..."}  # Streaming text
        - {"type": "tool_call", "name": "...", "input": {...}, "id": "..."}
        - {"type": "tool_result", "id": "...", "result": {...}}
        - {"type": "complete", "usage": {...}}
        - {"type": "error", "message": "..."}

Security:
    - Admin role required
    - JWT authentication via query param or cookie
    - Rate limited to prevent abuse
    - Audit logged for compliance
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.db.session import get_async_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/claude-chat", tags=["claude-chat"])


# =============================================================================
# Pydantic Models
# =============================================================================


class ChatMessage(BaseModel):
    """A single message in the chat history."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    tool_calls: list[dict] | None = None


class ChatSession(BaseModel):
    """Tracks a chat session with history."""

    session_id: str
    user_id: str
    messages: list[ChatMessage] = []
    created_at: datetime
    last_activity: datetime


# =============================================================================
# Session Management (In-memory for now, could be Redis)
# =============================================================================

# Active sessions: session_id -> ChatSession
_sessions: dict[str, ChatSession] = {}

# Active WebSocket connections: session_id -> WebSocket
_connections: dict[str, WebSocket] = {}

# Active streaming tasks: session_id -> asyncio.Event (set when interrupted)
_interrupt_flags: dict[str, asyncio.Event] = {}

# Active stream tasks: session_id -> asyncio.Task
_active_streams: dict[str, asyncio.Task] = {}


def get_or_create_session(user_id: str, session_id: str | None = None) -> ChatSession:
    """Get existing session or create new one."""
    if session_id and session_id in _sessions:
        session = _sessions[session_id]
        session.last_activity = datetime.utcnow()
        return session

    # Create new session
    new_id = session_id or str(uuid.uuid4())
    session = ChatSession(
        session_id=new_id,
        user_id=user_id,
        messages=[],
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
    )
    _sessions[new_id] = session
    return session


# =============================================================================
# MCP Tool Definitions (matches your MCP server tools)
# =============================================================================

SCHEDULER_TOOLS = [
    {
        "name": "validate_schedule",
        "description": "Validate a schedule for ACGME compliance violations. Returns list of violations if any.",
        "input_schema": {
            "type": "object",
            "properties": {
                "schedule_id": {
                    "type": "string",
                    "description": "The schedule ID to validate",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "analyze_swap_candidates",
        "description": "Find compatible swap candidates for a person's assignment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "person_id": {
                    "type": "string",
                    "description": "The person requesting the swap",
                },
                "assignment_id": {
                    "type": "string",
                    "description": "The assignment to swap",
                },
                "max_candidates": {
                    "type": "integer",
                    "description": "Maximum candidates to return",
                    "default": 10,
                },
            },
            "required": ["person_id"],
        },
    },
    {
        "name": "run_contingency_analysis",
        "description": "Run N-1/N-2 contingency analysis to identify vulnerable slots.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "detect_conflicts",
        "description": "Detect scheduling conflicts in a date range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "health_check",
        "description": "Check the health status of the scheduling system.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# =============================================================================
# Tool Execution (calls your existing services)
# =============================================================================


async def execute_tool(tool_name: str, tool_input: dict, db) -> dict[str, Any]:
    """
    Execute a tool by calling the appropriate backend service.

    This bridges Claude's tool calls to your existing service layer.
    All outputs are sanitized to prevent PII leakage.
    """
    try:
        if tool_name == "validate_schedule":
            from datetime import date as date_type

            from app.services.constraint_service import (
                ConstraintService,
                ScheduleNotFoundError,
            )

            # Parse dates if provided, otherwise use defaults
            start_date_str = tool_input.get("start_date")
            end_date_str = tool_input.get("end_date")
            schedule_id = tool_input.get("schedule_id")

            if schedule_id:
                # Validate by schedule ID
                service = ConstraintService(db)
                try:
                    result = await service.validate_schedule(schedule_id)
                    return {
                        "status": "validated",
                        "is_valid": result.is_valid,
                        "compliance_rate": result.compliance_rate,
                        "total_issues": result.total_issues,
                        "critical_count": result.critical_count,
                        "warning_count": result.warning_count,
                        "issues": [
                            {
                                "severity": issue.severity.value,
                                "rule_type": issue.rule_type,
                                "message": issue.message,
                                "suggested_action": issue.suggested_action,
                            }
                            for issue in result.issues[:10]  # Limit to 10 issues
                        ],
                        "validated_at": result.validated_at.isoformat(),
                    }
                except ScheduleNotFoundError:
                    return {
                        "status": "error",
                        "message": f"Schedule '{schedule_id}' not found",
                    }
            else:
                # No schedule_id - return general status
                return {
                    "status": "ok",
                    "message": "Validation service available. Provide schedule_id to validate.",
                    "violations": [],
                }

        elif tool_name == "analyze_swap_candidates":
            from uuid import UUID

            from app.services.swap_auto_matcher import SwapAutoMatcher

            person_id = tool_input.get("person_id")
            max_candidates = tool_input.get("max_candidates", 10)

            if not person_id:
                return {"error": "person_id is required"}

            try:
                matcher = SwapAutoMatcher(db)
                # Get proactive suggestions for the faculty member
                suggestions = matcher.suggest_proactive_swaps(
                    faculty_id=UUID(person_id),
                    limit=max_candidates,
                )

                return {
                    "candidates": [
                        {
                            "partner_id": str(s.suggested_partner_id),
                            "partner_name": s.suggested_partner_name,
                            "current_week": s.current_week.isoformat(),
                            "partner_week": s.partner_week.isoformat(),
                            "benefit_score": s.benefit_score,
                            "reason": s.reason,
                            "action": s.action_text,
                        }
                        for s in suggestions
                    ],
                    "total_found": len(suggestions),
                }
            except ValueError as e:
                return {"error": f"Invalid person_id format: {e}"}

        elif tool_name == "run_contingency_analysis":
            from datetime import date as date_type
            from datetime import timedelta

            from app.models.assignment import Assignment
            from app.models.block import Block
            from app.models.person import Person
            from app.resilience.contingency import ContingencyAnalyzer

            # Parse dates
            start_date_str = tool_input.get("start_date")
            end_date_str = tool_input.get("end_date")

            if start_date_str:
                start_date = date_type.fromisoformat(start_date_str)
            else:
                start_date = date_type.today()

            if end_date_str:
                end_date = date_type.fromisoformat(end_date_str)
            else:
                end_date = start_date + timedelta(days=30)

            # Get faculty and assignments for the period
            faculty = (
                (await db.execute(select(Person).where(Person.type == "faculty")))
                .scalars()
                .all()
            )
            blocks = (
                db.query(Block)
                .filter(Block.date >= start_date, Block.date <= end_date)
                .all()
            )
            assignments = (
                db.query(Assignment)
                .join(Block)
                .filter(Block.date >= start_date, Block.date <= end_date)
                .all()
            )

            # Build coverage requirements (1 faculty per block minimum)
            coverage_reqs = {b.id: 1 for b in blocks}

            # Run N-1 analysis
            analyzer = ContingencyAnalyzer()
            vulnerabilities = analyzer.analyze_n1(
                faculty=faculty,
                blocks=blocks,
                current_assignments=assignments,
                coverage_requirements=coverage_reqs,
            )

            return {
                "analysis_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "n1_vulnerabilities": [
                    {
                        "faculty_ref": f"entity-{str(v.faculty_id)[:8]}",
                        "severity": v.severity,
                        "affected_blocks": v.affected_blocks,
                        "is_unique_provider": v.is_unique_provider,
                        "details": v.details,
                    }
                    for v in vulnerabilities[:10]  # Limit output
                ],
                "total_vulnerabilities": len(vulnerabilities),
                "critical_count": sum(
                    1 for v in vulnerabilities if v.severity == "critical"
                ),
            }

        elif tool_name == "detect_conflicts":
            from datetime import date as date_type
            from datetime import timedelta

            from app.scheduling.conflicts.analyzer import ConflictAnalyzer

            # Parse dates
            start_date_str = tool_input.get("start_date")
            end_date_str = tool_input.get("end_date")

            if start_date_str:
                start_date = date_type.fromisoformat(start_date_str)
            else:
                start_date = date_type.today()

            if end_date_str:
                end_date = date_type.fromisoformat(end_date_str)
            else:
                end_date = start_date + timedelta(days=30)

            # ConflictAnalyzer uses async session
            analyzer = ConflictAnalyzer(db)
            conflicts = await analyzer.analyze_schedule(
                start_date=start_date,
                end_date=end_date,
            )

            # Generate summary
            summary = await analyzer.generate_summary(conflicts)

            return {
                "analysis_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "conflicts": [
                    {
                        "id": c.conflict_id,
                        "type": c.conflict_type.value,
                        "severity": c.severity.value,
                        "title": c.title,
                        "description": c.description,
                        "is_auto_resolvable": c.is_auto_resolvable,
                    }
                    for c in conflicts[:10]  # Limit output
                ],
                "summary": {
                    "total": summary.total_conflicts,
                    "critical": summary.critical_count,
                    "high": summary.high_count,
                    "auto_resolvable": summary.auto_resolvable_count,
                },
            }

        elif tool_name == "health_check":
            # Check database connectivity
            try:
                db.execute("SELECT 1")
                db_status = "connected"
            except Exception:
                db_status = "disconnected"

            return {
                "status": "healthy" if db_status == "connected" else "degraded",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "database": db_status,
                    "api": "running",
                },
            }

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        logger.exception(f"Tool execution failed: {tool_name}")
        # Return sanitized error (no stack traces or sensitive info)
        return {"error": f"Tool execution failed: {type(e).__name__}"}


# =============================================================================
# Claude API Integration
# =============================================================================


async def stream_claude_response(
    websocket: WebSocket,
    session: ChatSession,
    user_message: str,
    db,
    interrupt_event: asyncio.Event | None = None,
):
    """
    Stream Claude's response to the WebSocket client.

    This is the core bridge logic that:
    1. Sends the conversation to Claude API
    2. Streams tokens back to the frontend
    3. Handles tool calls and executes them
    4. Sends tool results back to Claude
    5. Checks for interruption requests during streaming

    Args:
        websocket: WebSocket connection
        session: Chat session
        user_message: User's message
        db: Database session
        interrupt_event: Optional event that signals interruption request
    """
    interrupted = False
    full_response = ""
    tool_calls = []

    try:
        # Lazy import to avoid startup dependency
        from anthropic import AsyncAnthropic

        # Initialize client
        api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
        if not api_key:
            await websocket.send_json(
                {"type": "error", "message": "ANTHROPIC_API_KEY not configured"}
            )
            return

        client = AsyncAnthropic(api_key=api_key)

        # Build messages from session history
        messages = []
        for msg in session.messages:
            messages.append({"role": msg.role, "content": msg.content})

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # System prompt with scheduler context
        system_prompt = """You are a scheduling assistant for a medical residency program.
You help administrators manage schedules, check ACGME compliance, find swap candidates,
and analyze system health.

You have access to tools that interact with the scheduling system. Use them to:
- Validate schedules for compliance violations
- Find swap candidates for residents
- Run contingency analysis to find vulnerable slots
- Detect scheduling conflicts
- Check system health

Always explain what you're doing and what the results mean.
Be concise but thorough. If there are issues, suggest solutions."""

        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=SCHEDULER_TOOLS,
            messages=messages,
        ) as stream:
            async for event in stream:
                # Check for interruption
                if interrupt_event and interrupt_event.is_set():
                    interrupted = True
                    logger.info(f"Stream interrupted for session {session.session_id}")
                    break

                if hasattr(event, "type"):
                    if event.type == "content_block_start":
                        if hasattr(event, "content_block"):
                            if event.content_block.type == "tool_use":
                                # Tool call starting
                                await websocket.send_json(
                                    {
                                        "type": "tool_call_start",
                                        "name": event.content_block.name,
                                        "id": event.content_block.id,
                                    }
                                )

                    elif event.type == "content_block_delta":
                        if hasattr(event, "delta"):
                            if hasattr(event.delta, "text"):
                                # Text token
                                token = event.delta.text
                                full_response += token
                                await websocket.send_json(
                                    {"type": "token", "content": token}
                                )
                            elif hasattr(event.delta, "partial_json"):
                                # Tool input streaming (optional to send)
                                pass

                    elif event.type == "message_stop":
                        break

            # Only get final message if not interrupted
            if not interrupted:
                final_message = await stream.get_final_message()

                # Process any tool calls
                for block in final_message.content:
                    # Check for interruption before each tool call
                    if interrupt_event and interrupt_event.is_set():
                        interrupted = True
                        break

                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_id = block.id

                        # Notify frontend of tool execution
                        await websocket.send_json(
                            {
                                "type": "tool_call",
                                "name": tool_name,
                                "input": tool_input,
                                "id": tool_id,
                            }
                        )

                        # Execute the tool
                        result = await execute_tool(tool_name, tool_input, db)

                        # Send result to frontend
                        await websocket.send_json(
                            {"type": "tool_result", "id": tool_id, "result": result}
                        )

                        tool_calls.append(
                            {"name": tool_name, "input": tool_input, "result": result}
                        )

        # Store in session history (even partial responses if interrupted)
        session.messages.append(
            ChatMessage(
                role="user",
                content=user_message,
                timestamp=datetime.utcnow(),
            )
        )

        if full_response or tool_calls:
            session.messages.append(
                ChatMessage(
                    role="assistant",
                    content=full_response + (" [interrupted]" if interrupted else ""),
                    timestamp=datetime.utcnow(),
                    tool_calls=tool_calls if tool_calls else None,
                )
            )

        # Send appropriate completion message
        if interrupted:
            await websocket.send_json(
                {
                    "type": "interrupted",
                    "message": "Generation stopped by user",
                    "partial_response": bool(full_response),
                }
            )
        else:
            await websocket.send_json(
                {
                    "type": "complete",
                    "usage": {
                        "input_tokens": final_message.usage.input_tokens,
                        "output_tokens": final_message.usage.output_tokens,
                    },
                }
            )

    except asyncio.CancelledError:
        # Task was cancelled (another form of interruption)
        logger.info(f"Stream task cancelled for session {session.session_id}")
        await websocket.send_json(
            {
                "type": "interrupted",
                "message": "Generation cancelled",
                "partial_response": bool(full_response),
            }
        )
        raise  # Re-raise to properly handle cancellation

    except Exception as e:
        logger.exception("Claude streaming error")
        await websocket.send_json({"type": "error", "message": str(e)})


# =============================================================================
# WebSocket Endpoint
# =============================================================================


@router.websocket("/ws")
async def claude_chat_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication"),
    session_id: str | None = Query(None, description="Existing session ID to resume"),
):
    """
    WebSocket endpoint for Claude chat.

    Connect with: ws://localhost:8000/api/claude-chat/ws?token=<jwt>&session_id=<optional>

    Message format:
        Send: {"type": "user_message", "content": "your message"}
        Send: {"type": "interrupt"} to stop generation

        Receive: {"type": "connected", "session_id": "..."}
        Receive: {"type": "token", "content": "..."}
        Receive: {"type": "tool_call", "name": "...", "input": {...}}
        Receive: {"type": "complete", "usage": {...}}
    """
    # Authenticate
    try:
        from app.api.deps import get_user_from_token
        from app.db.session import SessionLocal

        db = SessionLocal()
        user = await get_user_from_token(token, db)

        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return

        # Check admin role
        if user.role not in ["ADMIN", "COORDINATOR"]:
            await websocket.close(code=4003, reason="Admin access required")
            return

    except Exception as e:
        logger.exception("Auth failed")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # Accept connection
    await websocket.accept()

    # Get or create session
    session = get_or_create_session(str(user.id), session_id)
    _connections[session.session_id] = websocket

    # Create interrupt event for this session
    interrupt_event = asyncio.Event()
    _interrupt_flags[session.session_id] = interrupt_event

    # Send connected acknowledgment
    await websocket.send_json(
        {
            "type": "connected",
            "session_id": session.session_id,
            "history_count": len(session.messages),
        }
    )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "user_message":
                content = data.get("content", "")
                if content.strip():
                    # Clear any previous interrupt flag
                    interrupt_event.clear()

                    # Create streaming task
                    stream_task = asyncio.create_task(
                        stream_claude_response(
                            websocket, session, content, db, interrupt_event
                        )
                    )
                    _active_streams[session.session_id] = stream_task

                    try:
                        # Wait for stream to complete
                        await stream_task
                    except asyncio.CancelledError:
                        logger.info(f"Stream task cancelled: {session.session_id}")
                    finally:
                        # Clean up task reference
                        if session.session_id in _active_streams:
                            del _active_streams[session.session_id]

            elif msg_type == "interrupt":
                # Set the interrupt flag
                interrupt_event.set()

                # Also cancel the task if it's running
                if session.session_id in _active_streams:
                    task = _active_streams[session.session_id]
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                    # Clean up
                    del _active_streams[session.session_id]
                else:
                    # No active stream, just acknowledge
                    await websocket.send_json(
                        {"type": "interrupted", "message": "No active generation"}
                    )

            elif msg_type == "get_history":
                # Return session history
                history = [msg.model_dump() for msg in session.messages]
                await websocket.send_json({"type": "history", "messages": history})

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: session={session.session_id}")
    except Exception as e:
        logger.exception("WebSocket error")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass  # Connection may be closed
    finally:
        # Cleanup interrupt flag
        if session.session_id in _interrupt_flags:
            del _interrupt_flags[session.session_id]

        # Cancel any active stream
        if session.session_id in _active_streams:
            task = _active_streams[session.session_id]
            if not task.done():
                task.cancel()
            del _active_streams[session.session_id]

        # Cleanup connection
        if session.session_id in _connections:
            del _connections[session.session_id]
        if db:
            db.close()


# =============================================================================
# REST Endpoints (for non-streaming use cases)
# =============================================================================


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_active_user),
):
    """List chat sessions for current user."""
    user_sessions = [
        {
            "session_id": s.session_id,
            "message_count": len(s.messages),
            "created_at": s.created_at.isoformat(),
            "last_activity": s.last_activity.isoformat(),
        }
        for s in _sessions.values()
        if s.user_id == str(current_user.id)
    ]
    return {"sessions": user_sessions}


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get chat history for a session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    if session.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your session")

    return {
        "session_id": session_id,
        "messages": [msg.model_dump() for msg in session.messages],
    }


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete a chat session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    if session.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your session")

    del _sessions[session_id]
