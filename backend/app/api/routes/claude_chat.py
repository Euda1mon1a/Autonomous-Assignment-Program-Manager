"""Claude Code Chat integration endpoints for real-time agentic task execution."""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.chat import ClaudeCodeRequest, StreamUpdate
from app.services.claude_service import ClaudeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/claude", tags=["claude-chat"])
claude_service = ClaudeService()


@router.post("/chat")
async def claude_chat(
    request: ClaudeCodeRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Send a message to Claude Code with agentic execution context.
    Returns immediate response (non-streaming).
    """
    try:
        # Verify user has access to the program
        # This should be validated in your access control layer

        result = await claude_service.execute_task(
            request=request,
            user_id=current_user.id,
        )

        return {"success": True, "result": result, "artifacts": []}
    except Exception as e:
        logger.error(f"Claude chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/chat/stream")
async def claude_chat_stream(
    request: ClaudeCodeRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Stream messages from Claude Code with real-time updates.
    Returns Server-Sent Events (SSE) stream.
    """

    async def stream_generator() -> AsyncGenerator[str, None]:
        try:
            # Stream from Claude service
            async for update in claude_service.stream_task(
                request=request,
                user_id=current_user.id,
            ):
                # Send as SSE format
                yield f"data: {json.dumps(update.dict())}\n\n"
        except Exception as e:
            logger.error(f"Claude stream error: {str(e)}")
            error_update = StreamUpdate(
                type="error",
                content=str(e),
            )
            yield f"data: {json.dumps(error_update.dict())}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@router.post("/tasks/schedule-generation")
async def generate_schedule(
    request: ClaudeCodeRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Specialized endpoint for schedule generation with real-time progress.
    """

    async def stream_generator() -> AsyncGenerator[str, None]:
        try:
            request.action = "generate_schedule"
            async for update in claude_service.stream_task(
                request=request,
                user_id=current_user.id,
            ):
                yield f"data: {json.dumps(update.dict())}\n\n"
        except Exception as e:
            logger.error(f"Schedule generation error: {str(e)}")
            error_update = StreamUpdate(
                type="error",
                content=str(e),
            )
            yield f"data: {json.dumps(error_update.dict())}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
    )


@router.post("/tasks/compliance-check")
async def check_compliance(
    request: ClaudeCodeRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Specialized endpoint for compliance analysis with violations and remediation.
    """

    async def stream_generator() -> AsyncGenerator[str, None]:
        try:
            request.action = "validate_compliance"
            async for update in claude_service.stream_task(
                request=request,
                user_id=current_user.id,
            ):
                yield f"data: {json.dumps(update.dict())}\n\n"
        except Exception as e:
            logger.error(f"Compliance check error: {str(e)}")
            error_update = StreamUpdate(
                type="error",
                content=str(e),
            )
            yield f"data: {json.dumps(error_update.dict())}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
    )


@router.post("/tasks/export-report")
async def export_report(
    request: ClaudeCodeRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Specialized endpoint for report generation and export.
    """

    async def stream_generator() -> AsyncGenerator[str, None]:
        try:
            request.action = "export_report"
            async for update in claude_service.stream_task(
                request=request,
                user_id=current_user.id,
            ):
                yield f"data: {json.dumps(update.dict())}\n\n"
        except Exception as e:
            logger.error(f"Report export error: {str(e)}")
            error_update = StreamUpdate(
                type="error",
                content=str(e),
            )
            yield f"data: {json.dumps(error_update.dict())}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
    )


@router.post("/tasks/fairness-analysis")
async class optimize_fairness(
    request: ClaudeCodeRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Specialized endpoint for fairness and equity analysis.
    """

    async def stream_generator() -> AsyncGenerator[str, None]:
        try:
            request.action = "optimize_fairness"
            async for update in claude_service.stream_task(
                request=request,
                user_id=current_user.id,
            ):
                yield f"data: {json.dumps(update.dict())}\n\n"
        except Exception as e:
            logger.error(f"Fairness analysis error: {str(e)}")
            error_update = StreamUpdate(
                type="error",
                content=str(e),
            )
            yield f"data: {json.dumps(error_update.dict())}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
    )
