"""API routes for task history learning system."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.task_history import (
    TaskHistoryCreate,
    TaskHistoryResponse,
    TaskHistorySearchRequest,
    TaskHistorySearchResponse,
    TaskHistorySimilarResult,
    TaskHistorySessionResponse,
)
from app.services.task_history_service import TaskHistoryService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=TaskHistoryResponse)
def create_task_entry(
    request: TaskHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Log a completed task execution for the learning system."""
    try:
        service = TaskHistoryService(db)
        entry = service.log(
            task_description=request.task_description,
            agent_used=request.agent_used,
            model_used=request.model_used,
            success=request.success,
            duration_ms=request.duration_ms,
            session_id=request.session_id,
            notes=request.notes,
            failure_reason=request.failure_reason,
            tags=request.tags,
            files_touched=request.files_touched,
        )
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.error("Failed to log task history", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to log task")


@router.post("/search", response_model=TaskHistorySearchResponse)
def search_similar_tasks(
    request: TaskHistorySearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Search past tasks by vector similarity."""
    try:
        service = TaskHistoryService(db)
        results = service.search_similar(
            query=request.query,
            top_k=request.top_k,
            success_filter=request.success_filter,
            tags_filter=request.tags_filter,
            min_similarity=request.min_similarity,
        )
        return TaskHistorySearchResponse(
            query=request.query,
            results=[TaskHistorySimilarResult(**r) for r in results],
            total_results=len(results),
        )
    except Exception:
        logger.error("Task history search failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/session/{session_id}", response_model=TaskHistorySessionResponse)
def get_session_tasks(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Retrieve all tasks from a session (episodic recall)."""
    try:
        service = TaskHistoryService(db)
        tasks = service.get_session_history(session_id)
        return TaskHistorySessionResponse(
            session_id=session_id,
            tasks=[TaskHistoryResponse.model_validate(t) for t in tasks],
            total_tasks=len(tasks),
        )
    except Exception:
        logger.error("Session history retrieval failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Session retrieval failed")


@router.get("/files", response_model=list[TaskHistoryResponse])
def get_file_lessons(
    paths: list[str] = Query(..., description="File paths to search for lessons"),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Find past task lessons involving specific files."""
    try:
        service = TaskHistoryService(db)
        results = service.get_lessons_for_files(file_paths=paths, limit=limit)
        return [TaskHistoryResponse(**r) for r in results]
    except Exception:
        logger.error("File lessons retrieval failed", exc_info=True)
        raise HTTPException(status_code=500, detail="File lessons retrieval failed")
