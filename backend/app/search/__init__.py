"""
Search module for full-text search and document indexing.

Provides comprehensive search capabilities with:
- Document indexing with custom mappings
- Incremental and full reindexing
- Index versioning and aliases
- Field analyzers and tokenizers
- Index health monitoring
- Bulk indexing operations
- Full-text search with relevance scoring
- Query parsing and tokenization
- Term highlighting
- Spell correction
- Search analytics

Example:
    from app.search.indexer import SearchIndexer, get_search_indexer
    from app.search.full_text import FullTextSearchService, get_search_service

    indexer = get_search_indexer()
    await indexer.index_document("person", person_id, person_data)
    await indexer.search("person", "john doe")

    # Full-text search
    search_service = get_search_service(db)
    results = await search_service.search(search_request)
"""

from app.search.full_text import (
    FullTextSearchService,
    QueryTokenizer,
    RelevanceScorer,
    SearchAnalytics,
    SpellCorrector,
    TextHighlighter,
    get_search_service,
)
from app.search.indexer import (
    DocumentMapping,
    FieldAnalyzer,
    FieldType,
    IndexAlias,
    IndexHealth,
    IndexStatus,
    IndexVersion,
    SearchIndexer,
    get_search_indexer,
)

__all__ = [
    # Indexer
    "SearchIndexer",
    "get_search_indexer",
    "DocumentMapping",
    "FieldType",
    "FieldAnalyzer",
    "IndexVersion",
    "IndexAlias",
    "IndexHealth",
    "IndexStatus",
    # Full-text search
    "FullTextSearchService",
    "get_search_service",
    "QueryTokenizer",
    "RelevanceScorer",
    "TextHighlighter",
    "SpellCorrector",
    "SearchAnalytics",
]
