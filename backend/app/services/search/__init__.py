"""Search service package for full-text search capabilities.

This package provides comprehensive search functionality including:
- Full-text search across multiple entities
- Fuzzy matching for typo tolerance
- Faceted search for filtering results
- Search suggestions and autocomplete
- Result highlighting
- Relevance scoring and ranking
- Pagination support

The search implementation uses PostgreSQL's built-in full-text search
capabilities with custom analyzers and ranking algorithms optimized
for the residency scheduling domain.
"""

from app.services.search.analyzers import (
    MedicalTermAnalyzer,
    PersonNameAnalyzer,
    SearchAnalyzer,
    StandardAnalyzer,
)
from app.services.search.backends import (
    PostgreSQLSearchBackend,
    SearchBackend,
)
from app.services.search.indexer import SearchIndexer
from app.services.search.query import QueryBuilder, SearchQuery

__all__ = [
    "SearchAnalyzer",
    "StandardAnalyzer",
    "PersonNameAnalyzer",
    "MedicalTermAnalyzer",
    "SearchBackend",
    "PostgreSQLSearchBackend",
    "SearchIndexer",
    "QueryBuilder",
    "SearchQuery",
]
