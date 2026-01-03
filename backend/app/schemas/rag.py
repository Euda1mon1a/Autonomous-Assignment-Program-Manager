"""Pydantic schemas for RAG (Retrieval-Augmented Generation) service."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Request Schemas
# =============================================================================


class DocumentIngestRequest(BaseModel):
    """Request to ingest a document into the RAG system."""

    content: str = Field(
        ...,
        min_length=1,
        description="Document content to ingest and chunk",
    )
    doc_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Document type: acgme_rules, scheduling_policy, user_guide, etc.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata: source_file, page_number, section, author, etc.",
    )
    chunk_size: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="Target chunk size in tokens",
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=500,
        description="Overlap between chunks in tokens",
    )

    @field_validator("doc_type")
    @classmethod
    def validate_doc_type(cls, v: str) -> str:
        """Validate and normalize doc_type."""
        allowed_types = {
            # Core documentation types
            "acgme_rules",
            "scheduling_policy",
            "user_guide",
            "technical_doc",
            "meeting_notes",
            "research_paper",
            "clinical_guideline",
            # RAG knowledge base categories (from docs/rag-knowledge/)
            "swap_system",
            "military_specific",
            "resilience_concepts",
            "user_guide_faq",
            "session_handoff",
            "ai_patterns",
            "ai_decisions",
            "delegation_patterns",
            "exotic_concepts",
            "agent_spec",
            # Fallback
            "other",
        }
        if v.lower() not in allowed_types:
            raise ValueError(
                f"Invalid doc_type. Must be one of: {', '.join(sorted(allowed_types))}"
            )
        return v.lower()


class RAGRetrievalRequest(BaseModel):
    """Request to retrieve relevant documents for a query."""

    query: str = Field(
        ...,
        min_length=1,
        description="Query text for semantic search",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of top results to return",
    )
    doc_type: str | None = Field(
        default=None,
        description="Filter by document type (optional)",
    )
    min_similarity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold (0-1)",
    )
    metadata_filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata filters",
    )


class ContextBuildRequest(BaseModel):
    """Request to build context string for LLM injection."""

    query: str = Field(
        ...,
        min_length=1,
        description="Query to retrieve context for",
    )
    max_tokens: int = Field(
        default=2000,
        ge=100,
        le=8000,
        description="Maximum tokens in context string",
    )
    doc_type: str | None = Field(
        default=None,
        description="Filter by document type (optional)",
    )
    include_metadata: bool = Field(
        default=True,
        description="Include metadata in context string",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class DocumentChunk(BaseModel):
    """Individual document chunk with metadata."""

    id: UUID
    content: str
    doc_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class RetrievedDocument(BaseModel):
    """Document retrieved from vector search with similarity score."""

    id: UUID
    content: str
    doc_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    similarity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Cosine similarity score (0-1, higher is more similar)",
    )
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class IngestResponse(BaseModel):
    """Response for document ingestion."""

    status: str = Field(description="success or error")
    chunks_created: int = Field(description="Number of chunks created")
    chunk_ids: list[UUID] = Field(default_factory=list)
    doc_type: str
    message: str = Field(default="")


class RetrievalResponse(BaseModel):
    """Response for document retrieval."""

    query: str
    documents: list[RetrievedDocument]
    total_results: int
    execution_time_ms: float = Field(description="Query execution time in milliseconds")


class RAGContext(BaseModel):
    """Formatted context for LLM injection."""

    query: str
    context: str = Field(description="Formatted context string ready for LLM injection")
    sources: list[RetrievedDocument] = Field(
        default_factory=list,
        description="Source documents used to build context",
    )
    token_count: int = Field(description="Approximate token count of context string")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about context generation",
    )


class RAGHealthResponse(BaseModel):
    """Response for RAG system health check."""

    status: str = Field(description="healthy or unhealthy")
    total_documents: int
    documents_by_type: dict[str, int]
    embedding_model: str
    embedding_dimensions: int
    vector_index_status: str = Field(
        description="Status of vector indexes (ready, building, missing)"
    )
    recommendations: list[str] = Field(default_factory=list)
