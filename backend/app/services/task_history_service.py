"""Service for task history learning system.

Provides embed-on-write and vector similarity search over past task executions,
enabling agents to learn from prior successes and failures.

Follows the RAG service pattern: EmbeddingService for vectors, pgvector for search.
"""

import logging
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.agent_memory import TaskHistory
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class TaskHistoryService:
    """Service for recording and querying task execution history."""

    DEFAULT_TOP_K = 5
    DEFAULT_MIN_SIMILARITY = 0.5

    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_service = EmbeddingService()

    def log(
        self,
        task_description: str,
        agent_used: str,
        model_used: str,
        success: bool,
        duration_ms: int | None = None,
        session_id: str | None = None,
        notes: str | None = None,
        failure_reason: str | None = None,
        tags: list[str] | None = None,
        files_touched: list[str] | None = None,
    ) -> TaskHistory:
        """Log a task execution with embedded description for future search."""
        embedding = self.embedding_service.embed_text(task_description)

        entry = TaskHistory(
            task_description=task_description,
            embedding=embedding,
            agent_used=agent_used,
            model_used=model_used,
            success=success,
            duration_ms=duration_ms,
            session_id=session_id,
            notes=notes,
            failure_reason=failure_reason,
            tags=tags,
            files_touched=files_touched,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        logger.info(
            "Logged task history id=%d agent=%s success=%s",
            entry.id,
            agent_used,
            success,
        )
        return entry

    def search_similar(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        success_filter: bool | None = None,
        tags_filter: list[str] | None = None,
        min_similarity: float = DEFAULT_MIN_SIMILARITY,
    ) -> list[dict[str, Any]]:
        """Vector similarity search over past tasks."""
        query_embedding = self.embedding_service.embed_text(query)

        similarity_expr = (
            1 - TaskHistory.embedding.cosine_distance(query_embedding)
        ).label("similarity")

        stmt = select(TaskHistory, similarity_expr).where(
            TaskHistory.embedding.isnot(None),
            similarity_expr >= min_similarity,
        )

        if success_filter is not None:
            stmt = stmt.where(TaskHistory.success == success_filter)

        if tags_filter:
            # PG array overlap: task tags && filter tags
            stmt = stmt.where(TaskHistory.tags.overlap(tags_filter))

        stmt = stmt.order_by(text("similarity DESC")).limit(top_k)

        results = self.db.execute(stmt).all()

        return [
            {
                "id": row.TaskHistory.id,
                "task_description": row.TaskHistory.task_description,
                "agent_used": row.TaskHistory.agent_used,
                "model_used": row.TaskHistory.model_used,
                "success": row.TaskHistory.success,
                "duration_ms": row.TaskHistory.duration_ms,
                "session_id": row.TaskHistory.session_id,
                "notes": row.TaskHistory.notes,
                "failure_reason": row.TaskHistory.failure_reason,
                "tags": row.TaskHistory.tags,
                "files_touched": row.TaskHistory.files_touched,
                "created_at": row.TaskHistory.created_at,
                "similarity_score": float(row.similarity),
            }
            for row in results
        ]

    def get_lessons_for_files(
        self,
        file_paths: list[str],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Find past tasks involving specific files."""
        stmt = (
            select(TaskHistory)
            .where(TaskHistory.files_touched.overlap(file_paths))
            .order_by(TaskHistory.created_at.desc())
            .limit(limit)
        )
        results = self.db.execute(stmt).scalars().all()

        return [
            {
                "id": r.id,
                "task_description": r.task_description,
                "agent_used": r.agent_used,
                "model_used": r.model_used,
                "success": r.success,
                "notes": r.notes,
                "failure_reason": r.failure_reason,
                "tags": r.tags,
                "files_touched": r.files_touched,
                "created_at": r.created_at,
            }
            for r in results
        ]

    def get_session_history(
        self,
        session_id: str,
    ) -> list[TaskHistory]:
        """Retrieve all tasks from a session (episodic memory)."""
        stmt = (
            select(TaskHistory)
            .where(TaskHistory.session_id == session_id)
            .order_by(TaskHistory.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())
