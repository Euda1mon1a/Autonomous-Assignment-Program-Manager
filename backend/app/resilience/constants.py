"""
Constants for Resilience Framework.

This module centralizes magic numbers used in Tier 3 resilience components
including persistence, cognitive load tracking, and hub analysis.
"""

# ==============================================================================
# Database Persistence Constants
# ==============================================================================

# Query limits
DEFAULT_SESSION_HISTORY_LIMIT = 50
DEFAULT_CENTRALITY_SCORES_LIMIT = 50

# Time-to-Live (TTL) for historical data
EFFECTIVENESS_HISTORY_TTL_HOURS = 48  # Keep last 48 hours of effectiveness scores

# Trail strength thresholds
MIN_TRAIL_STRENGTH_THRESHOLD = 0.01  # Minimum strength before deletion

# ==============================================================================
# Cognitive Load Constants
# ==============================================================================

# Decision limits
DEFAULT_MAX_DECISIONS_BEFORE_BREAK = 20

# Cognitive cost thresholds
COGNITIVE_COST_LOW_THRESHOLD = 5.0
COGNITIVE_COST_MEDIUM_THRESHOLD = 10.0
COGNITIVE_COST_HIGH_THRESHOLD = 15.0

# Time limits
DECISION_TIMEOUT_HOURS = 24  # Maximum time to make a decision

# ==============================================================================
# Hub Analysis Constants
# ==============================================================================

# Centrality thresholds
HUB_CENTRALITY_THRESHOLD = 0.75  # Composite score threshold for hub designation
HIGH_RISK_CENTRALITY_THRESHOLD = 0.85

# Network analysis
MIN_NETWORK_SIZE = 5  # Minimum number of faculty for meaningful analysis
MAX_NETWORK_SIZE = 200  # Maximum network size for performance

# Protection plan defaults
DEFAULT_WORKLOAD_REDUCTION_PERCENT = 25.0
DEFAULT_PROTECTION_PERIOD_DAYS = 30

# ==============================================================================
# Stigmergy (Preference Trails) Constants
# ==============================================================================

# Evaporation rates
DEFAULT_EVAPORATION_RATE = 0.05  # 5% evaporation per time unit
RAPID_EVAPORATION_RATE = 0.15  # 15% for rapidly changing preferences

# Reinforcement
DEFAULT_REINFORCEMENT_STRENGTH = 1.0
STRONG_REINFORCEMENT_MULTIPLIER = 2.0
WEAK_REINFORCEMENT_MULTIPLIER = 0.5

# Trail strength bounds
MIN_TRAIL_STRENGTH = 0.0
MAX_TRAIL_STRENGTH = 100.0
INITIAL_TRAIL_STRENGTH = 10.0

# Significant trail threshold
SIGNIFICANT_TRAIL_THRESHOLD = 25.0  # Trails above this are considered significant
