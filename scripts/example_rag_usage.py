#!/usr/bin/env python3
"""Example usage of RAG embedding initialization.

This script demonstrates different ways to initialize and use
RAG embeddings programmatically.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.services.rag_service import RAGService

logger = get_logger(__name__)


async def example_1_health_check():
    """Example 1: Check RAG system health."""
    logger.info("Example 1: Health Check")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        rag_service = RAGService(db)
        health = await rag_service.get_health()

        logger.info(f"Status: {health.status}")
        logger.info(f"Total documents: {health.total_documents}")
        logger.info(f"Embedding model: {health.embedding_model}")
        logger.info(f"Vector dimensions: {health.embedding_dimensions}")
        logger.info(f"Index status: {health.vector_index_status}")

        if health.documents_by_type:
            logger.info("Documents by type:")
            for doc_type, count in health.documents_by_type.items():
                logger.info(f"  - {doc_type}: {count}")

        if health.recommendations:
            logger.info("Recommendations:")
            for rec in health.recommendations:
                logger.info(f"  - {rec}")

    finally:
        db.close()


async def example_2_ingest_document():
    """Example 2: Ingest a single document."""
    logger.info("\nExample 2: Ingest Single Document")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        rag_service = RAGService(db)

        # Sample document content
        content = """
        # Sample Scheduling Policy

        ## Policy Overview
        This policy defines the scheduling guidelines for medical residents.

        ## Work Hours
        - Maximum 80 hours per week averaged over 4 weeks
        - Minimum 1 day off per 7 days

        ## Call Schedules
        - Night call should be distributed fairly
        - No more than 6 consecutive nights
        """

        # Ingest the document
        result = await rag_service.ingest_document(
            content=content,
            doc_type="test_policy",
            metadata={
                "source": "example",
                "created_by": "example_script",
            },
            chunk_size=200,  # Smaller chunks for this example
            chunk_overlap=20,
        )

        logger.info(f"Status: {result.status}")
        logger.info(f"Chunks created: {result.chunks_created}")
        logger.info(f"Message: {result.message}")

        if result.status == "success":
            logger.info(f"Chunk IDs: {result.chunk_ids}")

    finally:
        db.close()


async def example_3_semantic_search():
    """Example 3: Perform semantic search."""
    logger.info("\nExample 3: Semantic Search")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        rag_service = RAGService(db)

        # Search for documents about work hours
        query = "What are the maximum work hours allowed?"

        result = await rag_service.retrieve(
            query=query,
            top_k=3,
            min_similarity=0.3,  # Lower threshold for demo
        )

        logger.info(f"Query: {query}")
        logger.info(f"Found {result.total_results} results")
        logger.info(f"Execution time: {result.execution_time_ms:.2f}ms")

        for i, doc in enumerate(result.documents, 1):
            logger.info(f"\nResult {i}:")
            logger.info(f"  Doc Type: {doc.doc_type}")
            logger.info(f"  Similarity: {doc.similarity_score:.3f}")
            logger.info(f"  Content preview: {doc.content[:150]}...")
            if doc.metadata:
                logger.info(f"  Metadata: {doc.metadata}")

    finally:
        db.close()


async def example_4_build_context():
    """Example 4: Build context for LLM injection."""
    logger.info("\nExample 4: Build RAG Context for LLM")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        rag_service = RAGService(db)

        # Build context for a query
        query = "How do I request a schedule swap?"

        context = await rag_service.build_context(
            query=query,
            max_tokens=1000,
            include_metadata=True,
        )

        logger.info(f"Query: {query}")
        logger.info(f"Sources used: {len(context.sources)}")
        logger.info(f"Token count: ~{context.token_count}")
        logger.info(f"\nContext preview:")
        logger.info("-" * 60)
        logger.info(context.context[:500] + "...")
        logger.info("-" * 60)

        logger.info("\nThis context can be injected into an LLM prompt like:")
        logger.info(f'''
        prompt = """
        {context.context}

        Based on the context above, answer this question:
        {query}
        """
        ''')

    finally:
        db.close()


async def example_5_cleanup():
    """Example 5: Cleanup test documents."""
    logger.info("\nExample 5: Cleanup Test Documents")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        rag_service = RAGService(db)

        # Delete test documents
        deleted_count = rag_service.delete_by_doc_type("test_policy")
        logger.info(f"Deleted {deleted_count} test documents")

    finally:
        db.close()


async def example_6_celery_tasks():
    """Example 6: Using Celery tasks."""
    logger.info("\nExample 6: Celery Tasks (requires Celery running)")
    logger.info("=" * 60)

    try:
        from app.tasks import (
            check_rag_health,
            initialize_embeddings,
            refresh_single_document,
        )

        logger.info("Available RAG tasks:")
        logger.info("  - initialize_embeddings.delay()")
        logger.info("  - refresh_single_document.delay('acgme-rules.md')")
        logger.info("  - check_rag_health.delay()")

        logger.info("\nExample usage:")
        logger.info("""
        # Initialize all embeddings
        task = initialize_embeddings.delay()
        result = task.get(timeout=300)
        print(result)

        # Check health
        health_task = check_rag_health.delay()
        health = health_task.get(timeout=30)
        print(f"RAG Status: {health['status']}")
        print(f"Total docs: {health['total_documents']}")
        """)

    except ImportError as e:
        logger.warning(f"Could not import tasks (Celery may not be configured): {e}")


async def main():
    """Run all examples."""
    logger.info("RAG Embedding Examples")
    logger.info("=" * 60)

    try:
        # Run examples in sequence
        await example_1_health_check()
        await example_2_ingest_document()
        await example_3_semantic_search()
        await example_4_build_context()
        await example_5_cleanup()
        await example_6_celery_tasks()

        logger.info("\n" + "=" * 60)
        logger.info("All examples completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
