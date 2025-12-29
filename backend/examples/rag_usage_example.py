"""
Example usage of the RAG (Retrieval-Augmented Generation) service.

This script demonstrates how to:
1. Ingest documents with embeddings
2. Retrieve relevant documents using semantic search
3. Build context for LLM injection
4. Check system health

Prerequisites:
- PostgreSQL with pgvector extension enabled
- Run migrations: `alembic upgrade head`
- sentence-transformers installed: `pip install sentence-transformers`

Usage:
    python examples/rag_usage_example.py
"""

import asyncio
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.rag_service import RAGService


async def example_ingest_acgme_rules(db: Session):
    """Example: Ingest ACGME duty hour documentation."""
    service = RAGService(db)

    acgme_content = """
    ACGME Duty Hour Requirements (2024)

    1. 80-Hour Work Week Limit
    Clinical and educational work hours must not exceed 80 hours per week,
    averaged over a four-week period, inclusive of all in-house clinical
    and educational activities, clinical work done from home, and all
    moonlighting.

    2. 1-in-7 Day Free of Duty
    Residents must have at least one day (24-hour period) in seven free
    from all educational and clinical responsibilities, averaged over a
    four-week period, inclusive of call.

    3. Supervision Requirements
    All patient care must be supervised, with levels of supervision
    appropriate to the resident's level of training, patient complexity,
    and urgency of care.

    4. Maximum Shift Length
    PGY-1 residents: 16 hours maximum
    PGY-2 and above: 24 hours + 4 hours for transition

    5. Minimum Time Between Shifts
    Residents should have at least 8 hours of rest between shifts.
    This may be reduced to 6 hours when transition activities are required.
    """

    print("🔄 Ingesting ACGME documentation...")
    response = await service.ingest_document(
        content=acgme_content,
        doc_type="acgme_rules",
        metadata={
            "source": "ACGME Common Program Requirements 2024",
            "section": "Duty Hours",
            "date": "2024-01-01",
            "version": "2024.1",
        },
        chunk_size=300,  # Smaller chunks for this example
        chunk_overlap=50,
    )

    print(f"✅ Status: {response.status}")
    print(f"📄 Chunks created: {response.chunks_created}")
    print(f"🆔 Chunk IDs: {response.chunk_ids[:3]}...")  # Show first 3
    print()


async def example_ingest_scheduling_policy(db: Session):
    """Example: Ingest institutional scheduling policy."""
    service = RAGService(db)

    policy_content = """
    Residency Program Scheduling Policy

    Call Rotation Policy:
    - Faculty must take at least one call shift per month
    - No faculty member should exceed 5 call shifts per month
    - Call shifts should be distributed equitably across all faculty

    Vacation and Leave:
    - Residents receive 20 days of vacation per academic year
    - Vacation requests must be submitted at least 30 days in advance
    - At least 50% coverage must be maintained during vacation periods

    Swap Procedures:
    - Faculty may swap call shifts with mutual agreement
    - All swaps must be recorded in the scheduling system
    - Swaps must not violate ACGME duty hour requirements
    - PD or APD approval required for swaps during high-volume periods

    Emergency Coverage:
    - A backup call list must be maintained at all times
    - Faculty must respond to emergency coverage requests within 2 hours
    - Emergency coverage activates for illness, family emergency, or TDY
    """

    print("🔄 Ingesting scheduling policy...")
    response = await service.ingest_document(
        content=policy_content,
        doc_type="scheduling_policy",
        metadata={
            "source": "Residency Program Policy Manual",
            "section": "Scheduling",
            "institution": "Example Medical Center",
            "updated": str(datetime.now()),
        },
    )

    print(f"✅ Status: {response.status}")
    print(f"📄 Chunks created: {response.chunks_created}")
    print()


async def example_semantic_search(db: Session):
    """Example: Search for documents using semantic similarity."""
    service = RAGService(db)

    queries = [
        "What are the work hour limits for residents?",
        "How do I request a call swap?",
        "What are supervision requirements?",
        "How much vacation do residents get?",
    ]

    for query in queries:
        print(f"🔍 Query: '{query}'")
        response = await service.retrieve(
            query=query,
            top_k=3,
            min_similarity=0.3,  # Lower threshold for demo
        )

        print(f"📊 Found {response.total_results} results in {response.execution_time_ms:.2f}ms")

        for i, doc in enumerate(response.documents, 1):
            print(f"\n  Result {i} (similarity: {doc.similarity_score:.3f}):")
            print(f"  Type: {doc.doc_type}")
            print(f"  Content preview: {doc.content[:150]}...")
            if doc.metadata:
                print(f"  Metadata: {doc.metadata}")

        print("\n" + "="*80 + "\n")


async def example_build_context(db: Session):
    """Example: Build context for LLM injection."""
    service = RAGService(db)

    query = "What are the ACGME requirements for resident work hours and supervision?"

    print(f"🤖 Building LLM context for query: '{query}'")
    context = await service.build_context(
        query=query,
        max_tokens=1500,
        include_metadata=True,
    )

    print(f"\n📝 Generated Context ({context.token_count} tokens):")
    print("="*80)
    print(context.context)
    print("="*80)

    print(f"\n📚 Used {len(context.sources)} source documents:")
    for i, source in enumerate(context.sources, 1):
        print(f"  {i}. {source.doc_type} (similarity: {source.similarity_score:.3f})")

    print(f"\n💡 This context can now be injected into an LLM prompt!")
    print()


async def example_filtered_search(db: Session):
    """Example: Search with doc_type filter."""
    service = RAGService(db)

    print("🔍 Searching only ACGME rules (doc_type filter)...")
    response = await service.retrieve(
        query="supervision requirements",
        doc_type="acgme_rules",  # Filter to only ACGME docs
        top_k=5,
    )

    print(f"📊 Found {response.total_results} ACGME documents")
    for doc in response.documents:
        assert doc.doc_type == "acgme_rules", "Filter failed!"
        print(f"  ✓ {doc.doc_type}: {doc.content[:100]}...")

    print()


async def example_health_check(db: Session):
    """Example: Check RAG system health."""
    service = RAGService(db)

    print("🏥 Checking RAG system health...")
    health = await service.get_health()

    print(f"Status: {health.status}")
    print(f"Total documents: {health.total_documents}")
    print(f"Embedding model: {health.embedding_model} ({health.embedding_dimensions} dimensions)")
    print(f"Vector index status: {health.vector_index_status}")

    print("\nDocuments by type:")
    for doc_type, count in health.documents_by_type.items():
        print(f"  - {doc_type}: {count}")

    if health.recommendations:
        print("\nRecommendations:")
        for rec in health.recommendations:
            print(f"  ⚠️  {rec}")

    print()


async def example_cleanup(db: Session):
    """Example: Delete documents by type."""
    service = RAGService(db)

    print("🗑️  Cleaning up test documents...")

    # Delete by doc_type
    count_acgme = service.delete_by_doc_type("acgme_rules")
    count_policy = service.delete_by_doc_type("scheduling_policy")

    print(f"Deleted {count_acgme} ACGME documents")
    print(f"Deleted {count_policy} policy documents")
    print()


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("RAG Service Usage Examples")
    print("="*80 + "\n")

    db = SessionLocal()
    try:
        # Example 1: Ingest documents
        await example_ingest_acgme_rules(db)
        await example_ingest_scheduling_policy(db)

        # Example 2: Check health
        await example_health_check(db)

        # Example 3: Semantic search
        await example_semantic_search(db)

        # Example 4: Filtered search
        await example_filtered_search(db)

        # Example 5: Build context for LLM
        await example_build_context(db)

        # Example 6: Cleanup
        await example_cleanup(db)

        # Final health check
        await example_health_check(db)

        print("✅ All examples completed successfully!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
