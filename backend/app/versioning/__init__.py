"""
Data versioning module for tracking entity versions, branches, and merges.

This module provides comprehensive version control functionality for schedule data,
enabling point-in-time queries, version comparison, rollback, and branch management.
"""

from .data_versioning import (
    DataVersioningService,
    VersionMetadata,
    VersionDiff,
    VersionBranch,
    MergeConflict,
    BranchInfo,
    PointInTimeQuery,
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
