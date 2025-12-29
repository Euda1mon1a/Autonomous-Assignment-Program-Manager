"""SQLAlchemy models for agent memory and vector storage."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class ModelTier(Base):
    """Static lookup table for default model assignments per agent."""

    __tablename__ = "model_tiers"

    agent_name: Mapped[str] = mapped_column(String, primary_key=True)
    default_model: Mapped[str] = mapped_column(
        String, nullable=False
    )  # haiku, sonnet, opus
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AgentEmbedding(Base):
    """Pre-computed embeddings of agent specification files."""

    __tablename__ = "agent_embeddings"

    agent_name: Mapped[str] = mapped_column(String, primary_key=True)
    embedding = mapped_column(
        Vector(384), nullable=False
    )  # sentence-transformers all-MiniLM-L6-v2
    spec_hash: Mapped[str] = mapped_column(
        String, nullable=False
    )  # SHA256 of spec content
    capabilities: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Extracted capabilities text
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class TaskHistory(Base):
    """Historical record of task executions for learning optimal agent/model pairs."""

    __tablename__ = "task_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(384), nullable=True)  # Embedded task description
    agent_used: Mapped[str] = mapped_column(String, nullable=False)
    model_used: Mapped[str] = mapped_column(
        String, nullable=False
    )  # haiku, sonnet, opus
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
