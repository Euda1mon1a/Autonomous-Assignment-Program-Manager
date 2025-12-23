"""
Data versioning module for tracking entity versions, branches, and merges.

This module provides comprehensive version control functionality for schedule data,
enabling point-in-time queries, version comparison, rollback, and branch management.
"""

from .data_versioning import (
    BranchInfo,
    DataVersioningService,
    MergeConflict,
    PointInTimeQuery,
    VersionBranch,
    VersionDiff,
    VersionMetadata,
)

__all__ = [
    "DataVersioningService",
    "VersionMetadata",
    "VersionDiff",
    "VersionBranch",
    "MergeConflict",
    "BranchInfo",
    "PointInTimeQuery",
]
