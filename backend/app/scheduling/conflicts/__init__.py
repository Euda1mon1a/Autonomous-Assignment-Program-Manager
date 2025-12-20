"""
Schedule Conflict Analysis Package.

This package provides comprehensive conflict detection, analysis, and resolution
suggestions for medical residency schedules.

Key Features:
    - Time overlap detection
    - Resource contention analysis
    - ACGME rule conflict detection
    - Conflict severity scoring
    - Resolution suggestions
    - Impact analysis
    - Visual conflict timeline generation

Usage:
    >>> from app.scheduling.conflicts import ConflictAnalyzer
    >>> analyzer = ConflictAnalyzer(db)
    >>> conflicts = await analyzer.analyze_schedule(start_date, end_date)
    >>> timeline = await analyzer.generate_timeline(conflicts)

Modules:
    - analyzer: Main conflict detection and analysis engine
    - types: Conflict type definitions and enums
    - resolver: Conflict resolution suggestion generator
    - visualizer: Conflict timeline visualization data generator
"""

from app.scheduling.conflicts.analyzer import ConflictAnalyzer
from app.scheduling.conflicts.resolver import ConflictResolver
from app.scheduling.conflicts.types import (
    Conflict,
    ConflictCategory,
    ConflictSeverity,
    ConflictType,
    TimeOverlapConflict,
    ResourceContentionConflict,
    ACGMEViolationConflict,
)
from app.scheduling.conflicts.visualizer import ConflictVisualizer

__all__ = [
    "ConflictAnalyzer",
    "ConflictResolver",
    "ConflictVisualizer",
    "Conflict",
    "ConflictCategory",
    "ConflictSeverity",
    "ConflictType",
    "TimeOverlapConflict",
    "ResourceContentionConflict",
    "ACGMEViolationConflict",
]
