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

# ==============================================================================
# Utilization Threshold Constants (Queuing Theory)
# ==============================================================================

# Utilization thresholds (based on queuing theory M/M/1 formula)
UTILIZATION_MAX_THRESHOLD = 0.80  # Target maximum (80% rule from queuing theory)
UTILIZATION_WARNING_THRESHOLD = 0.70  # Yellow alert threshold
UTILIZATION_CRITICAL_THRESHOLD = 0.90  # Red alert threshold
UTILIZATION_EMERGENCY_THRESHOLD = 0.95  # Black alert threshold

# Blocks per day
DEFAULT_BLOCKS_PER_FACULTY_PER_DAY = 2.0  # AM + PM sessions

# Forecast horizon
DEFAULT_FORECAST_DAYS = 90  # Days to project utilization ahead

# Cache settings
UTILIZATION_CACHE_SIZE = 256  # LRU cache size for utilization calculations

# ==============================================================================
# Defense in Depth Constants
# ==============================================================================

# Coverage thresholds for defense levels (percentages as decimals)
DEFENSE_PREVENTION_COVERAGE_THRESHOLD = 0.95  # Level 1: Prevention
DEFENSE_CONTROL_COVERAGE_THRESHOLD = 0.90  # Level 2: Control monitoring
DEFENSE_SAFETY_COVERAGE_THRESHOLD = 0.80  # Level 3: Safety systems engage
DEFENSE_CONTAINMENT_COVERAGE_THRESHOLD = 0.70  # Level 4: Containment
DEFENSE_EMERGENCY_COVERAGE_THRESHOLD = 0.60  # Level 5: Emergency (< 60%)

# Overtime authorization trigger
OVERTIME_COVERAGE_TRIGGER_THRESHOLD = 0.85  # Coverage threshold for overtime auth

# ==============================================================================
# Circuit Breaker Constants
# ==============================================================================

# Default circuit breaker configuration
DEFAULT_FAILURE_THRESHOLD = 5  # Failures before opening circuit
DEFAULT_SUCCESS_THRESHOLD = 2  # Successes in half-open before closing
DEFAULT_CIRCUIT_TIMEOUT_SECONDS = 60.0  # Time before attempting recovery
DEFAULT_HALF_OPEN_MAX_CALLS = 3  # Max calls allowed in half-open state

# Cache size
CIRCUIT_BREAKER_CACHE_SIZE = 128  # LRU cache for recommended level

# ==============================================================================
# Retry Strategy Constants
# ==============================================================================

# Fixed delay strategy
DEFAULT_FIXED_DELAY_SECONDS = 1.0

# Linear backoff strategy
DEFAULT_LINEAR_BASE_DELAY_SECONDS = 1.0
DEFAULT_LINEAR_INCREMENT_SECONDS = 1.0

# Exponential backoff strategy
DEFAULT_EXPONENTIAL_BASE_DELAY_SECONDS = 1.0
DEFAULT_EXPONENTIAL_MULTIPLIER = 2.0
DEFAULT_EXPONENTIAL_MAX_DELAY_SECONDS = 60.0

# ==============================================================================
# SPC Monitoring Constants (Western Electric Rules)
# ==============================================================================

# Target hours (control chart centerline)
SPC_DEFAULT_TARGET_HOURS = 60.0  # Target weekly hours
SPC_DEFAULT_SIGMA = 5.0  # Process standard deviation (hours)

# ACGME compliance limits
ACGME_MAX_HOURS_PER_WEEK = 80  # Hard limit per ACGME regulations
ACGME_MIN_HOURS_PER_WEEK = 40  # Minimum for adequate training

# Rule thresholds (sigma multipliers)
SPC_RULE_1_SIGMA = 3  # 1 point beyond 3 sigma
SPC_RULE_2_SIGMA = 2  # 2 of 3 points beyond 2 sigma
SPC_RULE_3_SIGMA = 1  # 4 of 5 points beyond 1 sigma
SPC_RULE_4_CONSECUTIVE = 8  # 8 consecutive points on same side

# Process capability targets
PROCESS_CAPABILITY_MINIMUM = 1.0  # Cpk minimum (barely capable)
PROCESS_CAPABILITY_GOOD = 1.33  # Cpk for 4-sigma process
PROCESS_CAPABILITY_EXCELLENT = 1.67  # Cpk for 5-sigma process
PROCESS_CAPABILITY_WORLD_CLASS = 2.0  # Cpk for 6-sigma process

# ==============================================================================
# Seismic Detection Constants (STA/LTA Burnout Early Warning)
# ==============================================================================

# Window sizes
STA_LTA_SHORT_WINDOW = 5  # Short-term average window (data points)
STA_LTA_LONG_WINDOW = 30  # Long-term average window (data points)

# Trigger thresholds
STA_LTA_ON_THRESHOLD = 2.5  # Ratio threshold to trigger alert
STA_LTA_OFF_THRESHOLD = 1.0  # Ratio threshold to deactivate alert

# Severity thresholds (based on STA/LTA ratio)
SEISMIC_SEVERITY_LOW_RATIO = 2.5  # Low severity (< 3.5)
SEISMIC_SEVERITY_MEDIUM_RATIO = 3.5  # Medium severity (3.5 - 5.0)
SEISMIC_SEVERITY_HIGH_RATIO = 5.0  # High severity (5.0 - 10.0)
SEISMIC_SEVERITY_CRITICAL_RATIO = 10.0  # Critical severity (>= 10.0)

# Growth rate threshold for time-to-event prediction
SEISMIC_SIGNIFICANT_GROWTH_RATE = 0.01

# Magnitude estimation
SEISMIC_MAGNITUDE_MIN = 1.0
SEISMIC_MAGNITUDE_MAX = 10.0
SEISMIC_MULTI_SIGNAL_BONUS = 1.2  # 20% bonus for 3+ signals

# Time to event limits
TIME_TO_EVENT_MIN_DAYS = 1
TIME_TO_EVENT_MAX_DAYS = 365

# ==============================================================================
# Burnout Fire Index Constants (CFFDRS Adaptation)
# ==============================================================================

# Target hours for fire index calculations
BFI_FFMC_TARGET_HOURS = 60.0  # Target 60 hours per 2 weeks
BFI_DMC_TARGET_HOURS = 240.0  # Target 240 hours per 3 months

# Exponential constants for moisture code calculations
BFI_FFMC_K_CONSTANT = 3.5  # FFMC exponential scaling factor
BFI_DMC_K_CONSTANT = 2.5  # DMC exponential scaling factor

# BUI calculation coefficients (adapted from Van Wagner 1987)
BFI_BUI_DMC_COEFFICIENT = 0.9  # BUI numerator coefficient
BFI_BUI_DC_COEFFICIENT = 0.4  # BUI denominator DC coefficient

# FWI calculation
BFI_ISI_COEFFICIENT = 0.35  # ISI calculation coefficient
BFI_FWI_SCALE_FACTOR = 0.12  # FWI final scale factor
BFI_FD_POWER_LAW_COEFFICIENT = 0.626  # fD power law coefficient
BFI_FD_POWER_LAW_EXPONENT = 0.809  # fD power law exponent
BFI_BUI_TRANSITION_THRESHOLD = 80  # BUI threshold for formula switch

# Danger class thresholds (FWI score boundaries)
BFI_DANGER_LOW_THRESHOLD = 20
BFI_DANGER_MODERATE_THRESHOLD = 40
BFI_DANGER_HIGH_THRESHOLD = 60
BFI_DANGER_VERY_HIGH_THRESHOLD = 80

# Velocity factor divisor
BFI_VELOCITY_DIVISOR = 10.0

# ==============================================================================
# Circadian Model Constants
# ==============================================================================

# Circadian period (hours)
CIRCADIAN_NATURAL_PERIOD_HOURS = 24.2  # Free-running period
CIRCADIAN_ENTRAINED_PERIOD_HOURS = 24.0  # Entrained to light/dark cycle

# Amplitude bounds
CIRCADIAN_MIN_AMPLITUDE = 0.0
CIRCADIAN_MAX_AMPLITUDE = 1.0

# Phase Response Curve (PRC) parameters
CIRCADIAN_PRC_ADVANCE_MAX = 1.5  # Maximum advance (hours)
CIRCADIAN_PRC_DELAY_MAX = -2.5  # Maximum delay (hours)
CIRCADIAN_PRC_DEAD_ZONE_START = 12  # Dead zone start (noon)
CIRCADIAN_PRC_DEAD_ZONE_END = 16  # Dead zone end (4 PM)

# Amplitude decay/recovery rates
CIRCADIAN_AMPLITUDE_DECAY_RATE = 0.05  # 5% per irregular shift
CIRCADIAN_AMPLITUDE_RECOVERY_RATE = 0.02  # 2% per regular shift
CIRCADIAN_AMPLITUDE_RECOVERY_DAYS = 14  # Days for full recovery

# Quality score thresholds
CIRCADIAN_QUALITY_EXCELLENT = 0.85
CIRCADIAN_QUALITY_GOOD = 0.70
CIRCADIAN_QUALITY_FAIR = 0.55
CIRCADIAN_QUALITY_POOR = 0.40

# Schedule regularity threshold
CIRCADIAN_REGULARITY_THRESHOLD = 0.8  # Threshold for regular vs irregular

# Shift type modifiers
CIRCADIAN_NIGHT_SHIFT_MODIFIER = 1.5  # Night shifts have stronger effect
CIRCADIAN_SPLIT_SHIFT_MODIFIER = 0.5  # Split shifts have weaker effect

# ==============================================================================
# Contingency Analysis Constants
# ==============================================================================

# N-1 analysis
CONTINGENCY_HIGH_AFFECTED_BLOCKS_THRESHOLD = 5  # Threshold for "high" severity

# N-2 analysis
CONTINGENCY_TOP_FACULTY_LIMIT = 5  # If no critical faculty, analyze top N

# Centrality score weights
CENTRALITY_WEIGHT_SERVICES = 0.30
CENTRALITY_WEIGHT_UNIQUE_COVERAGE = 0.30
CENTRALITY_WEIGHT_REPLACEMENT_DIFFICULTY = 0.20
CENTRALITY_WEIGHT_WORKLOAD_SHARE = 0.20

# NetworkX centrality weights
NX_CENTRALITY_WEIGHT_BETWEENNESS = 0.25
NX_CENTRALITY_WEIGHT_PAGERANK = 0.25
NX_CENTRALITY_WEIGHT_DEGREE = 0.15
NX_CENTRALITY_WEIGHT_EIGENVECTOR = 0.10
NX_CENTRALITY_WEIGHT_REPLACEMENT = 0.15
NX_CENTRALITY_WEIGHT_WORKLOAD = 0.10

# PageRank damping factor
PAGERANK_ALPHA = 0.85

# Eigenvector centrality max iterations
EIGENVECTOR_MAX_ITERATIONS = 1000

# Cascade simulation
CASCADE_MAX_UTILIZATION = 0.80  # Normal max utilization
CASCADE_OVERLOAD_THRESHOLD = 1.2  # 120% triggers cascade failure
CASCADE_CATASTROPHIC_COVERAGE = 0.5  # Below 50% is catastrophic

# Critical failure points
CRITICAL_FAILURE_TOP_N = 10  # Analyze top N for cascade simulation

# Phase transition detection
PHASE_TRANSITION_CRITICAL_UTILIZATION = 0.95
PHASE_TRANSITION_HIGH_UTILIZATION = 0.90
PHASE_TRANSITION_ELEVATED_UTILIZATION = 0.85
PHASE_TRANSITION_HIGH_CHANGE_COUNT = 20  # Changes per week
PHASE_TRANSITION_ELEVATED_CHANGE_COUNT = 10  # Changes per week
PHASE_TRANSITION_LOOKBACK_DAYS = 7

# ==============================================================================
# Hub Analysis Constants (Extended)
# ==============================================================================

# Hub designation thresholds
HUB_THRESHOLD = 0.4  # Composite score for hub designation
CRITICAL_HUB_THRESHOLD = 0.6  # Composite score for critical hub

# Risk level thresholds (composite score)
HUB_RISK_CATASTROPHIC_SCORE = 0.8
HUB_RISK_CATASTROPHIC_UNIQUE_SERVICES = 3
HUB_RISK_CRITICAL_SCORE = 0.6
HUB_RISK_CRITICAL_UNIQUE_SERVICES = 2
HUB_RISK_HIGH_SCORE = 0.4
HUB_RISK_HIGH_UNIQUE_SERVICES = 1
HUB_RISK_MODERATE_SCORE = 0.2

# Centrality weights for composite score
HUB_WEIGHT_DEGREE = 0.2
HUB_WEIGHT_BETWEENNESS = 0.3
HUB_WEIGHT_EIGENVECTOR = 0.2
HUB_WEIGHT_PAGERANK = 0.15
HUB_WEIGHT_REPLACEMENT = 0.15

# Cross-training recommendations
CROSS_TRAINING_HOURS_NO_COVERAGE = 40  # Hours for service with no coverage
CROSS_TRAINING_HOURS_SINGLE_PROVIDER = 20  # Hours for single provider service
CROSS_TRAINING_RISK_REDUCTION_NO_COVERAGE = 1.0
CROSS_TRAINING_RISK_REDUCTION_SINGLE_PROVIDER = 0.8
CROSS_TRAINING_RISK_REDUCTION_DUAL_COVERAGE = 0.4

# Protection plan defaults
HUB_PROTECTION_WORKLOAD_REDUCTION = 0.3  # 30% reduction
HUB_PROTECTION_BACKUP_COUNT = 2  # Number of backup faculty
HUB_PROTECTION_CRITICAL_ONLY_THRESHOLD = 0.5  # Workload reduction threshold

# Hub concentration
HUB_CONCENTRATION_HIGH_THRESHOLD = 0.5  # Gini-like concentration threshold

# Cross-training priority limits
CROSS_TRAINING_DISPLAY_LIMIT = 10  # Max recommendations to display

# ==============================================================================
# Erlang C Coverage Constants
# ==============================================================================

# Default target wait probability
ERLANG_DEFAULT_TARGET_WAIT_PROB = 0.05  # 5% (95% answered immediately)

# Maximum servers to consider
ERLANG_MAX_SERVERS = 20

# Staffing table defaults
ERLANG_DEFAULT_STAFFING_TABLE_RANGE = 10  # Additional servers beyond minimum

# Service time multiplier for typical target wait
ERLANG_TYPICAL_TARGET_WAIT_MULTIPLIER = 0.5  # Half of service time
