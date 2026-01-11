#!/usr/bin/env python3
"""Initialize RAG embeddings from knowledge base documents.

This script reads markdown files from docs/rag-knowledge/ and embeds them
into the pgvector database for semantic search and RAG capabilities.

Features:
- Idempotent: Can be run multiple times (clears existing docs first)
- Progress tracking: Shows chunk creation progress
- Database validation: Checks connection before starting
- Flexible CLI: Process all docs or specific ones
- Dry run mode: Preview chunks without storing

Usage:
    # Embed all documents
    python scripts/init_rag_embeddings.py

    # Embed specific document
    python scripts/init_rag_embeddings.py --doc acgme-rules.md

    # Clear all embeddings
    python scripts/init_rag_embeddings.py --clear-all

    # Preview chunks without storing
    python scripts/init_rag_embeddings.py --dry-run
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.services.rag_service import RAGService

logger = get_logger(__name__)
settings = get_settings()

# Document type mapping (filename -> doc_type)
DOC_TYPE_MAP = {
    "acgme-rules.md": "acgme_rules",
    "scheduling-policies.md": "scheduling_policy",
    "swap-system.md": "swap_system",
    "military-specific.md": "military_specific",
    "resilience-concepts.md": "resilience_concepts",
    "user-guide-faq.md": "user_guide_faq",
    "session-learnings.md": "session_learnings",
    "session-protocols.md": "session_protocols",
    "delegation-patterns.md": "delegation_patterns",
    "L3-minimal-context-pattern.md": "delegation_patterns",
    "exotic-concepts.md": "exotic_concepts",
    # Session 087 additions
    "strict-button-pattern.md": "technical_doc",
    "agent-capabilities.md": "ai_patterns",
    "test-coverage-guide.md": "ai_patterns",
    "performance-testing-guide.md": "ai_patterns",
    "rag-ingestion-patterns.md": "ai_patterns",
}

# Base path for knowledge documents
DOCS_PATH = Path(__file__).parent.parent / "docs" / "rag-knowledge"


class EmbeddingInitializer:
    """Handles RAG embedding initialization."""

    def __init__(self, dry_run: bool = False):
        """Initialize the embedding initializer.

        Args:
            dry_run: If True, preview chunks without storing
        """
        self.dry_run = dry_run
        self.db = SessionLocal()
        self.rag_service = RAGService(self.db)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup database connection."""
        self.db.close()

    async def validate_database(self) -> bool:
        """Validate database connection and pgvector extension.

        Returns:
            True if database is ready, False otherwise
        """
        try:
            health = await self.rag_service.get_health()

            if health.status == "error":
                logger.error("RAG system health check failed")
                for rec in health.recommendations:
                    logger.error(f"  - {rec}")
                return False

            logger.info(f"✓ Database connection validated")
            logger.info(f"  - Embedding model: {health.embedding_model}")
            logger.info(f"  - Embedding dimensions: {health.embedding_dimensions}")
            logger.info(f"  - Vector index status: {health.vector_index_status}")
            logger.info(f"  - Existing documents: {health.total_documents}")

            if health.total_documents > 0:
                logger.info(f"  - Documents by type:")
                for doc_type, count in health.documents_by_type.items():
                    logger.info(f"    • {doc_type}: {count} chunks")

            return True

        except Exception as e:
            logger.error(f"Database validation failed: {e}", exc_info=True)
            return False

    async def clear_all_documents(self) -> int:
        """Clear all RAG documents from the database.

        Returns:
            Number of documents deleted
        """
        logger.info("Clearing all RAG documents...")

        total_deleted = 0
        for doc_type in DOC_TYPE_MAP.values():
            try:
                count = self.rag_service.delete_by_doc_type(doc_type)
                if count > 0:
                    logger.info(f"  ✓ Deleted {count} chunks of type '{doc_type}'")
                total_deleted += count
            except Exception as e:
                logger.error(f"  ✗ Failed to delete '{doc_type}': {e}")

        logger.info(f"✓ Cleared {total_deleted} total chunks")
        return total_deleted

    async def process_document(
        self,
        filepath: Path,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> dict[str, Any]:
        """Process a single document and create embeddings.

        Args:
            filepath: Path to the markdown file
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens

        Returns:
            Dict with processing results
        """
        filename = filepath.name
        doc_type = DOC_TYPE_MAP.get(filename, filename.replace(".md", ""))

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {filename}")
        logger.info(f"Doc Type: {doc_type}")
        logger.info(f"{'='*60}")

        try:
            # Read document content
            content = filepath.read_text(encoding="utf-8")
            content_size = len(content)
            logger.info(f"  • File size: {content_size:,} characters")

            if not content.strip():
                logger.warning(f"  ✗ Document is empty, skipping")
                return {
                    "filename": filename,
                    "status": "skipped",
                    "reason": "empty_content",
                }

            # Preview mode: show chunks without storing
            if self.dry_run:
                chunks = self.rag_service._chunk_text(content, chunk_size, chunk_overlap)
                logger.info(f"  • Generated {len(chunks)} chunks (DRY RUN)")

                # Show first chunk as preview
                if chunks:
                    preview = chunks[0][:200] + "..." if len(chunks[0]) > 200 else chunks[0]
                    logger.info(f"  • First chunk preview:")
                    logger.info(f"    {preview}")

                return {
                    "filename": filename,
                    "status": "dry_run",
                    "chunks_created": len(chunks),
                    "doc_type": doc_type,
                }

            # Clear existing documents of this type (idempotent)
            existing_count = self.rag_service.delete_by_doc_type(doc_type)
            if existing_count > 0:
                logger.info(f"  • Cleared {existing_count} existing chunks")

            # Ingest document
            metadata = {
                "filename": filename,
                "source": "docs/rag-knowledge",
                "file_size": content_size,
            }

            result = await self.rag_service.ingest_document(
                content=content,
                doc_type=doc_type,
                metadata=metadata,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            if result.status == "success":
                logger.info(f"  ✓ Created {result.chunks_created} chunks")
                logger.info(f"  ✓ Average chunk size: ~{content_size // result.chunks_created:,} chars")
                return {
                    "filename": filename,
                    "status": "success",
                    "chunks_created": result.chunks_created,
                    "doc_type": doc_type,
                }
            else:
                logger.error(f"  ✗ Ingestion failed: {result.message}")
                return {
                    "filename": filename,
                    "status": "error",
                    "error": result.message,
                    "doc_type": doc_type,
                }

        except Exception as e:
            logger.error(f"  ✗ Error processing {filename}: {e}", exc_info=True)
            return {
                "filename": filename,
                "status": "error",
                "error": str(e),
                "doc_type": doc_type,
            }

    async def process_all_documents(
        self,
        doc_filter: str | None = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> dict[str, Any]:
        """Process all documents in the knowledge base.

        Args:
            doc_filter: Optional filename filter (e.g., "acgme-rules.md")
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens

        Returns:
            Dict with summary of all processed documents
        """
        # Get all markdown files
        if doc_filter:
            files = [DOCS_PATH / doc_filter]
            if not files[0].exists():
                logger.error(f"Document not found: {doc_filter}")
                return {"status": "error", "error": f"File not found: {doc_filter}"}
        else:
            files = sorted(DOCS_PATH.glob("*.md"))

        if not files:
            logger.warning(f"No markdown files found in {DOCS_PATH}")
            return {"status": "error", "error": "No documents found"}

        logger.info(f"\n{'='*60}")
        logger.info(f"Found {len(files)} document(s) to process")
        logger.info(f"{'='*60}\n")

        results = []
        total_chunks = 0

        for filepath in files:
            result = await self.process_document(filepath, chunk_size, chunk_overlap)
            results.append(result)

            if result["status"] in ["success", "dry_run"]:
                total_chunks += result.get("chunks_created", 0)

        # Summary
        success_count = sum(1 for r in results if r["status"] in ["success", "dry_run"])
        error_count = sum(1 for r in results if r["status"] == "error")

        logger.info(f"\n{'='*60}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"  ✓ Successful: {success_count}/{len(files)}")
        logger.info(f"  ✗ Errors: {error_count}/{len(files)}")
        logger.info(f"  • Total chunks created: {total_chunks}")

        if self.dry_run:
            logger.info(f"  • DRY RUN - no data stored")

        logger.info(f"{'='*60}\n")

        return {
            "status": "completed",
            "documents_processed": len(files),
            "documents_successful": success_count,
            "documents_failed": error_count,
            "total_chunks": total_chunks,
            "results": results,
        }


async def main(args: argparse.Namespace) -> int:
    """Main entry point for the script.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("RAG Embeddings Initialization Script")
    logger.info("=" * 60)

    try:
        with EmbeddingInitializer(dry_run=args.dry_run) as initializer:
            # Validate database connection
            if not await initializer.validate_database():
                logger.error("Database validation failed. Exiting.")
                return 1

            # Handle clear-all flag
            if args.clear_all:
                await initializer.clear_all_documents()
                logger.info("✓ All documents cleared successfully")
                return 0

            # Process documents
            result = await initializer.process_all_documents(
                doc_filter=args.doc,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
            )

            if result["status"] == "error":
                logger.error(f"Processing failed: {result.get('error')}")
                return 1

            if result["documents_failed"] > 0:
                logger.warning(f"Some documents failed to process")
                return 1

            logger.info("✓ All documents processed successfully")
            return 0

    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user. Exiting.")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Initialize RAG embeddings from knowledge base documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Embed all documents
  %(prog)s

  # Embed specific document
  %(prog)s --doc acgme-rules.md

  # Preview chunks without storing
  %(prog)s --dry-run

  # Clear all embeddings
  %(prog)s --clear-all

  # Custom chunk size
  %(prog)s --chunk-size 1000 --chunk-overlap 100
        """,
    )

    parser.add_argument(
        "--doc",
        type=str,
        help="Process only a specific document (e.g., acgme-rules.md)",
    )

    parser.add_argument(
        "--clear-all",
        action="store_true",
        help="Clear all existing RAG documents before processing",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview chunks without storing in database",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Target chunk size in tokens (default: 500)",
    )

    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Overlap between chunks in tokens (default: 50)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)
