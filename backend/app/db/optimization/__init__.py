"""Database query optimization utilities.

This package provides tools for analyzing, optimizing, and monitoring database queries:
- Query performance analysis and N+1 detection
- Index recommendation engine
- Optimized query builders
- Prefetch and eager loading utilities

Usage:
    from app.db.optimization import QueryAnalyzer, IndexAdvisor, OptimizedQueryBuilder
    from app.db.optimization.prefetch import prefetch_assignments_with_relations
"""

from app.db.optimization.index_advisor import IndexAdvisor
from app.db.optimization.prefetch import (
    prefetch_assignments_with_relations,
    prefetch_persons_with_assignments,
    prefetch_schedule_data,
)
from app.db.optimization.query_analyzer import QueryAnalyzer
from app.db.optimization.query_builder import OptimizedQueryBuilder

__all__ = [
    "QueryAnalyzer",
    "IndexAdvisor",
    "OptimizedQueryBuilder",
    "prefetch_assignments_with_relations",
    "prefetch_persons_with_assignments",
    "prefetch_schedule_data",
]
