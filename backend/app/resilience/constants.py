"""
Constants for Resilience Framework.

This module centralizes magic numbers used in Tier 3 resilience components
including persistence, cognitive load tracking, and hub analysis.
"""

***REMOVED*** ==============================================================================
***REMOVED*** Database Persistence Constants
***REMOVED*** ==============================================================================

***REMOVED*** Query limits
DEFAULT_SESSION_HISTORY_LIMIT = 50
DEFAULT_CENTRALITY_SCORES_LIMIT = 50

***REMOVED*** Time-to-Live (TTL) for historical data
EFFECTIVENESS_HISTORY_TTL_HOURS = 48  ***REMOVED*** Keep last 48 hours of effectiveness scores

***REMOVED*** Trail strength thresholds
MIN_TRAIL_STRENGTH_THRESHOLD = 0.01  ***REMOVED*** Minimum strength before deletion

***REMOVED*** ==============================================================================
***REMOVED*** Cognitive Load Constants
***REMOVED*** ==============================================================================

***REMOVED*** Decision limits
DEFAULT_MAX_DECISIONS_BEFORE_BREAK = 20

***REMOVED*** Cognitive cost thresholds
COGNITIVE_COST_LOW_THRESHOLD = 5.0
COGNITIVE_COST_MEDIUM_THRESHOLD = 10.0
COGNITIVE_COST_HIGH_THRESHOLD = 15.0

***REMOVED*** Time limits
DECISION_TIMEOUT_HOURS = 24  ***REMOVED*** Maximum time to make a decision

***REMOVED*** ==============================================================================
***REMOVED*** Hub Analysis Constants
***REMOVED*** ==============================================================================

***REMOVED*** Centrality thresholds
HUB_CENTRALITY_THRESHOLD = 0.75  ***REMOVED*** Composite score threshold for hub designation
HIGH_RISK_CENTRALITY_THRESHOLD = 0.85

***REMOVED*** Network analysis
MIN_NETWORK_SIZE = 5  ***REMOVED*** Minimum number of faculty for meaningful analysis
MAX_NETWORK_SIZE = 200  ***REMOVED*** Maximum network size for performance

***REMOVED*** Protection plan defaults
DEFAULT_WORKLOAD_REDUCTION_PERCENT = 25.0
DEFAULT_PROTECTION_PERIOD_DAYS = 30

***REMOVED*** ==============================================================================
***REMOVED*** Stigmergy (Preference Trails) Constants
***REMOVED*** ==============================================================================

***REMOVED*** Evaporation rates
DEFAULT_EVAPORATION_RATE = 0.05  ***REMOVED*** 5% evaporation per time unit
RAPID_EVAPORATION_RATE = 0.15  ***REMOVED*** 15% for rapidly changing preferences

***REMOVED*** Reinforcement
DEFAULT_REINFORCEMENT_STRENGTH = 1.0
STRONG_REINFORCEMENT_MULTIPLIER = 2.0
WEAK_REINFORCEMENT_MULTIPLIER = 0.5

***REMOVED*** Trail strength bounds
MIN_TRAIL_STRENGTH = 0.0
MAX_TRAIL_STRENGTH = 100.0
INITIAL_TRAIL_STRENGTH = 10.0

***REMOVED*** Significant trail threshold
SIGNIFICANT_TRAIL_THRESHOLD = 25.0  ***REMOVED*** Trails above this are considered significant

***REMOVED*** ==============================================================================
***REMOVED*** Utilization Threshold Constants (Queuing Theory)
***REMOVED*** ==============================================================================

***REMOVED*** Utilization thresholds (based on queuing theory M/M/1 formula)
UTILIZATION_MAX_THRESHOLD = 0.80  ***REMOVED*** Target maximum (80% rule from queuing theory)
UTILIZATION_WARNING_THRESHOLD = 0.70  ***REMOVED*** Yellow alert threshold
UTILIZATION_CRITICAL_THRESHOLD = 0.90  ***REMOVED*** Red alert threshold
UTILIZATION_EMERGENCY_THRESHOLD = 0.95  ***REMOVED*** Black alert threshold

***REMOVED*** Blocks per day
DEFAULT_BLOCKS_PER_FACULTY_PER_DAY = 2.0  ***REMOVED*** AM + PM sessions

***REMOVED*** Forecast horizon
DEFAULT_FORECAST_DAYS = 90  ***REMOVED*** Days to project utilization ahead

***REMOVED*** Cache settings
UTILIZATION_CACHE_SIZE = 256  ***REMOVED*** LRU cache size for utilization calculations

***REMOVED*** ==============================================================================
***REMOVED*** Defense in Depth Constants
***REMOVED*** ==============================================================================

***REMOVED*** Coverage thresholds for defense levels (percentages as decimals)
DEFENSE_PREVENTION_COVERAGE_THRESHOLD = 0.95  ***REMOVED*** Level 1: Prevention
DEFENSE_CONTROL_COVERAGE_THRESHOLD = 0.90  ***REMOVED*** Level 2: Control monitoring
DEFENSE_SAFETY_COVERAGE_THRESHOLD = 0.80  ***REMOVED*** Level 3: Safety systems engage
DEFENSE_CONTAINMENT_COVERAGE_THRESHOLD = 0.70  ***REMOVED*** Level 4: Containment
DEFENSE_EMERGENCY_COVERAGE_THRESHOLD = 0.60  ***REMOVED*** Level 5: Emergency (< 60%)

***REMOVED*** Overtime authorization trigger
OVERTIME_COVERAGE_TRIGGER_THRESHOLD = 0.85  ***REMOVED*** Coverage threshold for overtime auth

***REMOVED*** ==============================================================================
***REMOVED*** Circuit Breaker Constants
***REMOVED*** ==============================================================================

***REMOVED*** Default circuit breaker configuration
DEFAULT_FAILURE_THRESHOLD = 5  ***REMOVED*** Failures before opening circuit
DEFAULT_SUCCESS_THRESHOLD = 2  ***REMOVED*** Successes in half-open before closing
DEFAULT_CIRCUIT_TIMEOUT_SECONDS = 60.0  ***REMOVED*** Time before attempting recovery
DEFAULT_HALF_OPEN_MAX_CALLS = 3  ***REMOVED*** Max calls allowed in half-open state

***REMOVED*** Cache size
CIRCUIT_BREAKER_CACHE_SIZE = 128  ***REMOVED*** LRU cache for recommended level

***REMOVED*** ==============================================================================
***REMOVED*** Retry Strategy Constants
***REMOVED*** ==============================================================================

***REMOVED*** Fixed delay strategy
DEFAULT_FIXED_DELAY_SECONDS = 1.0

***REMOVED*** Linear backoff strategy
DEFAULT_LINEAR_BASE_DELAY_SECONDS = 1.0
DEFAULT_LINEAR_INCREMENT_SECONDS = 1.0

***REMOVED*** Exponential backoff strategy
DEFAULT_EXPONENTIAL_BASE_DELAY_SECONDS = 1.0
DEFAULT_EXPONENTIAL_MULTIPLIER = 2.0
DEFAULT_EXPONENTIAL_MAX_DELAY_SECONDS = 60.0

***REMOVED*** ==============================================================================
***REMOVED*** SPC Monitoring Constants (Western Electric Rules)
***REMOVED*** ==============================================================================

***REMOVED*** Target hours (control chart centerline)
SPC_DEFAULT_TARGET_HOURS = 60.0  ***REMOVED*** Target weekly hours
SPC_DEFAULT_SIGMA = 5.0  ***REMOVED*** Process standard deviation (hours)

***REMOVED*** ACGME compliance limits
ACGME_MAX_HOURS_PER_WEEK = 80  ***REMOVED*** Hard limit per ACGME regulations
ACGME_MIN_HOURS_PER_WEEK = 40  ***REMOVED*** Minimum for adequate training

***REMOVED*** Rule thresholds (sigma multipliers)
SPC_RULE_1_SIGMA = 3  ***REMOVED*** 1 point beyond 3 sigma
SPC_RULE_2_SIGMA = 2  ***REMOVED*** 2 of 3 points beyond 2 sigma
SPC_RULE_3_SIGMA = 1  ***REMOVED*** 4 of 5 points beyond 1 sigma
SPC_RULE_4_CONSECUTIVE = 8  ***REMOVED*** 8 consecutive points on same side

***REMOVED*** Process capability targets
PROCESS_CAPABILITY_MINIMUM = 1.0  ***REMOVED*** Cpk minimum (barely capable)
PROCESS_CAPABILITY_GOOD = 1.33  ***REMOVED*** Cpk for 4-sigma process
PROCESS_CAPABILITY_EXCELLENT = 1.67  ***REMOVED*** Cpk for 5-sigma process
PROCESS_CAPABILITY_WORLD_CLASS = 2.0  ***REMOVED*** Cpk for 6-sigma process

***REMOVED*** ==============================================================================
***REMOVED*** Seismic Detection Constants (STA/LTA Burnout Early Warning)
***REMOVED*** ==============================================================================

***REMOVED*** Window sizes
STA_LTA_SHORT_WINDOW = 5  ***REMOVED*** Short-term average window (data points)
STA_LTA_LONG_WINDOW = 30  ***REMOVED*** Long-term average window (data points)

***REMOVED*** Trigger thresholds
STA_LTA_ON_THRESHOLD = 2.5  ***REMOVED*** Ratio threshold to trigger alert
STA_LTA_OFF_THRESHOLD = 1.0  ***REMOVED*** Ratio threshold to deactivate alert

***REMOVED*** Severity thresholds (based on STA/LTA ratio)
SEISMIC_SEVERITY_LOW_RATIO = 2.5  ***REMOVED*** Low severity (< 3.5)
SEISMIC_SEVERITY_MEDIUM_RATIO = 3.5  ***REMOVED*** Medium severity (3.5 - 5.0)
SEISMIC_SEVERITY_HIGH_RATIO = 5.0  ***REMOVED*** High severity (5.0 - 10.0)
SEISMIC_SEVERITY_CRITICAL_RATIO = 10.0  ***REMOVED*** Critical severity (>= 10.0)

***REMOVED*** Growth rate threshold for time-to-event prediction
SEISMIC_SIGNIFICANT_GROWTH_RATE = 0.01

***REMOVED*** Magnitude estimation
SEISMIC_MAGNITUDE_MIN = 1.0
SEISMIC_MAGNITUDE_MAX = 10.0
SEISMIC_MULTI_SIGNAL_BONUS = 1.2  ***REMOVED*** 20% bonus for 3+ signals

***REMOVED*** Time to event limits
TIME_TO_EVENT_MIN_DAYS = 1
TIME_TO_EVENT_MAX_DAYS = 365

***REMOVED*** ==============================================================================
***REMOVED*** Burnout Fire Index Constants (CFFDRS Adaptation)
***REMOVED*** ==============================================================================

***REMOVED*** Target hours for fire index calculations
BFI_FFMC_TARGET_HOURS = 60.0  ***REMOVED*** Target 60 hours per 2 weeks
BFI_DMC_TARGET_HOURS = 240.0  ***REMOVED*** Target 240 hours per 3 months

***REMOVED*** Exponential constants for moisture code calculations
BFI_FFMC_K_CONSTANT = 3.5  ***REMOVED*** FFMC exponential scaling factor
BFI_DMC_K_CONSTANT = 2.5  ***REMOVED*** DMC exponential scaling factor

***REMOVED*** BUI calculation coefficients (adapted from Van Wagner 1987)
BFI_BUI_DMC_COEFFICIENT = 0.9  ***REMOVED*** BUI numerator coefficient
BFI_BUI_DC_COEFFICIENT = 0.4  ***REMOVED*** BUI denominator DC coefficient

***REMOVED*** FWI calculation
BFI_ISI_COEFFICIENT = 0.35  ***REMOVED*** ISI calculation coefficient
BFI_FWI_SCALE_FACTOR = 0.12  ***REMOVED*** FWI final scale factor
BFI_FD_POWER_LAW_COEFFICIENT = 0.626  ***REMOVED*** fD power law coefficient
BFI_FD_POWER_LAW_EXPONENT = 0.809  ***REMOVED*** fD power law exponent
BFI_BUI_TRANSITION_THRESHOLD = 80  ***REMOVED*** BUI threshold for formula switch

***REMOVED*** Danger class thresholds (FWI score boundaries)
BFI_DANGER_LOW_THRESHOLD = 20
BFI_DANGER_MODERATE_THRESHOLD = 40
BFI_DANGER_HIGH_THRESHOLD = 60
BFI_DANGER_VERY_HIGH_THRESHOLD = 80

***REMOVED*** Velocity factor divisor
BFI_VELOCITY_DIVISOR = 10.0

***REMOVED*** ==============================================================================
***REMOVED*** Circadian Model Constants
***REMOVED*** ==============================================================================

***REMOVED*** Circadian period (hours)
CIRCADIAN_NATURAL_PERIOD_HOURS = 24.2  ***REMOVED*** Free-running period
CIRCADIAN_ENTRAINED_PERIOD_HOURS = 24.0  ***REMOVED*** Entrained to light/dark cycle

***REMOVED*** Amplitude bounds
CIRCADIAN_MIN_AMPLITUDE = 0.0
CIRCADIAN_MAX_AMPLITUDE = 1.0

***REMOVED*** Phase Response Curve (PRC) parameters
CIRCADIAN_PRC_ADVANCE_MAX = 1.5  ***REMOVED*** Maximum advance (hours)
CIRCADIAN_PRC_DELAY_MAX = -2.5  ***REMOVED*** Maximum delay (hours)
CIRCADIAN_PRC_DEAD_ZONE_START = 12  ***REMOVED*** Dead zone start (noon)
CIRCADIAN_PRC_DEAD_ZONE_END = 16  ***REMOVED*** Dead zone end (4 PM)

***REMOVED*** Amplitude decay/recovery rates
CIRCADIAN_AMPLITUDE_DECAY_RATE = 0.05  ***REMOVED*** 5% per irregular shift
CIRCADIAN_AMPLITUDE_RECOVERY_RATE = 0.02  ***REMOVED*** 2% per regular shift
CIRCADIAN_AMPLITUDE_RECOVERY_DAYS = 14  ***REMOVED*** Days for full recovery

***REMOVED*** Quality score thresholds
CIRCADIAN_QUALITY_EXCELLENT = 0.85
CIRCADIAN_QUALITY_GOOD = 0.70
CIRCADIAN_QUALITY_FAIR = 0.55
CIRCADIAN_QUALITY_POOR = 0.40

***REMOVED*** Schedule regularity threshold
CIRCADIAN_REGULARITY_THRESHOLD = 0.8  ***REMOVED*** Threshold for regular vs irregular

***REMOVED*** Shift type modifiers
CIRCADIAN_NIGHT_SHIFT_MODIFIER = 1.5  ***REMOVED*** Night shifts have stronger effect
CIRCADIAN_SPLIT_SHIFT_MODIFIER = 0.5  ***REMOVED*** Split shifts have weaker effect

***REMOVED*** ==============================================================================
***REMOVED*** Contingency Analysis Constants
***REMOVED*** ==============================================================================

***REMOVED*** N-1 analysis
CONTINGENCY_HIGH_AFFECTED_BLOCKS_THRESHOLD = 5  ***REMOVED*** Threshold for "high" severity

***REMOVED*** N-2 analysis
CONTINGENCY_TOP_FACULTY_LIMIT = 5  ***REMOVED*** If no critical faculty, analyze top N

***REMOVED*** Centrality score weights
CENTRALITY_WEIGHT_SERVICES = 0.30
CENTRALITY_WEIGHT_UNIQUE_COVERAGE = 0.30
CENTRALITY_WEIGHT_REPLACEMENT_DIFFICULTY = 0.20
CENTRALITY_WEIGHT_WORKLOAD_SHARE = 0.20

***REMOVED*** NetworkX centrality weights
NX_CENTRALITY_WEIGHT_BETWEENNESS = 0.25
NX_CENTRALITY_WEIGHT_PAGERANK = 0.25
NX_CENTRALITY_WEIGHT_DEGREE = 0.15
NX_CENTRALITY_WEIGHT_EIGENVECTOR = 0.10
NX_CENTRALITY_WEIGHT_REPLACEMENT = 0.15
NX_CENTRALITY_WEIGHT_WORKLOAD = 0.10

***REMOVED*** PageRank damping factor
PAGERANK_ALPHA = 0.85

***REMOVED*** Eigenvector centrality max iterations
EIGENVECTOR_MAX_ITERATIONS = 1000

***REMOVED*** Cascade simulation
CASCADE_MAX_UTILIZATION = 0.80  ***REMOVED*** Normal max utilization
CASCADE_OVERLOAD_THRESHOLD = 1.2  ***REMOVED*** 120% triggers cascade failure
CASCADE_CATASTROPHIC_COVERAGE = 0.5  ***REMOVED*** Below 50% is catastrophic

***REMOVED*** Critical failure points
CRITICAL_FAILURE_TOP_N = 10  ***REMOVED*** Analyze top N for cascade simulation

***REMOVED*** Phase transition detection
PHASE_TRANSITION_CRITICAL_UTILIZATION = 0.95
PHASE_TRANSITION_HIGH_UTILIZATION = 0.90
PHASE_TRANSITION_ELEVATED_UTILIZATION = 0.85
PHASE_TRANSITION_HIGH_CHANGE_COUNT = 20  ***REMOVED*** Changes per week
PHASE_TRANSITION_ELEVATED_CHANGE_COUNT = 10  ***REMOVED*** Changes per week
PHASE_TRANSITION_LOOKBACK_DAYS = 7

***REMOVED*** ==============================================================================
***REMOVED*** Hub Analysis Constants (Extended)
***REMOVED*** ==============================================================================

***REMOVED*** Hub designation thresholds
HUB_THRESHOLD = 0.4  ***REMOVED*** Composite score for hub designation
CRITICAL_HUB_THRESHOLD = 0.6  ***REMOVED*** Composite score for critical hub

***REMOVED*** Risk level thresholds (composite score)
HUB_RISK_CATASTROPHIC_SCORE = 0.8
HUB_RISK_CATASTROPHIC_UNIQUE_SERVICES = 3
HUB_RISK_CRITICAL_SCORE = 0.6
HUB_RISK_CRITICAL_UNIQUE_SERVICES = 2
HUB_RISK_HIGH_SCORE = 0.4
HUB_RISK_HIGH_UNIQUE_SERVICES = 1
HUB_RISK_MODERATE_SCORE = 0.2

***REMOVED*** Centrality weights for composite score
HUB_WEIGHT_DEGREE = 0.2
HUB_WEIGHT_BETWEENNESS = 0.3
HUB_WEIGHT_EIGENVECTOR = 0.2
HUB_WEIGHT_PAGERANK = 0.15
HUB_WEIGHT_REPLACEMENT = 0.15

***REMOVED*** Cross-training recommendations
CROSS_TRAINING_HOURS_NO_COVERAGE = 40  ***REMOVED*** Hours for service with no coverage
CROSS_TRAINING_HOURS_SINGLE_PROVIDER = 20  ***REMOVED*** Hours for single provider service
CROSS_TRAINING_RISK_REDUCTION_NO_COVERAGE = 1.0
CROSS_TRAINING_RISK_REDUCTION_SINGLE_PROVIDER = 0.8
CROSS_TRAINING_RISK_REDUCTION_DUAL_COVERAGE = 0.4

***REMOVED*** Protection plan defaults
HUB_PROTECTION_WORKLOAD_REDUCTION = 0.3  ***REMOVED*** 30% reduction
HUB_PROTECTION_BACKUP_COUNT = 2  ***REMOVED*** Number of backup faculty
HUB_PROTECTION_CRITICAL_ONLY_THRESHOLD = 0.5  ***REMOVED*** Workload reduction threshold

***REMOVED*** Hub concentration
HUB_CONCENTRATION_HIGH_THRESHOLD = 0.5  ***REMOVED*** Gini-like concentration threshold

***REMOVED*** Cross-training priority limits
CROSS_TRAINING_DISPLAY_LIMIT = 10  ***REMOVED*** Max recommendations to display

***REMOVED*** ==============================================================================
***REMOVED*** Erlang C Coverage Constants
***REMOVED*** ==============================================================================

***REMOVED*** Default target wait probability
ERLANG_DEFAULT_TARGET_WAIT_PROB = 0.05  ***REMOVED*** 5% (95% answered immediately)

***REMOVED*** Maximum servers to consider
ERLANG_MAX_SERVERS = 20

***REMOVED*** Staffing table defaults
ERLANG_DEFAULT_STAFFING_TABLE_RANGE = 10  ***REMOVED*** Additional servers beyond minimum

***REMOVED*** Service time multiplier for typical target wait
ERLANG_TYPICAL_TARGET_WAIT_MULTIPLIER = 0.5  ***REMOVED*** Half of service time
