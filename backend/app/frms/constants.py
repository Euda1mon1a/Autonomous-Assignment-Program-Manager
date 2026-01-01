"""
Constants for Fatigue Risk Management System (FRMS).

This module centralizes magic numbers used in the three-process model,
performance prediction, and fatigue monitoring.
"""

# ==============================================================================
# Fatigue Threshold Constants (Based on Industry Standards)
# ==============================================================================

# Effectiveness thresholds (percentage)
THRESHOLD_OPTIMAL = 95.0  # Optimal performance level
THRESHOLD_ACCEPTABLE = 85.0  # Acceptable but below optimal
THRESHOLD_FAA_CAUTION = 77.0  # FAA caution threshold (aviation standard)
THRESHOLD_FRA_HIGH_RISK = 70.0  # FRA high-risk threshold (rail standard)
THRESHOLD_CRITICAL = 60.0  # Critical - immediate action required

# Alert severity mappings
EMERGENCY_THRESHOLD = THRESHOLD_CRITICAL  # 60%
CRITICAL_ALERT_THRESHOLD = THRESHOLD_FRA_HIGH_RISK  # 70%
WARNING_ALERT_THRESHOLD = THRESHOLD_FAA_CAUTION  # 77%
INFO_ALERT_THRESHOLD = THRESHOLD_ACCEPTABLE  # 85%

# ==============================================================================
# Trend Detection Constants
# ==============================================================================

# Trend analysis window
TREND_WINDOW_HOURS = 4.0  # Look back 4 hours for trend calculation
TREND_THRESHOLD_PERCENT = 5.0  # 5% change is significant

# Historical data retention
EFFECTIVENESS_HISTORY_HOURS = 48  # Keep last 48 hours
ALERT_DEDUPLICATION_HOURS = 1  # Don't repeat same alert within 1 hour

# ==============================================================================
# Physiological Constants
# ==============================================================================

# Extended wakefulness thresholds
EXTENDED_WAKEFULNESS_HOURS = 16  # Hours awake threshold for warning
CRITICAL_WAKEFULNESS_HOURS = 24  # Hours awake for critical warning

# Circadian rhythm
WOCL_START_HOUR = 2  # Window of Circadian Low start (2 AM)
WOCL_END_HOUR = 6  # Window of Circadian Low end (6 AM)

# Sleep requirements
MINIMUM_SLEEP_HOURS = 7  # Minimum recommended sleep
OPTIMAL_SLEEP_HOURS = 8  # Optimal sleep duration
REST_PERIOD_HOURS = 2  # Minimum rest period before returning to duty

# ==============================================================================
# Three-Process Model Constants
# ==============================================================================

# Process S (Sleep/Wake Homeostasis)
HOMEOSTATIC_INCREASE_RATE_PER_HOUR = 1.0  # Rate of sleep pressure buildup
HOMEOSTATIC_DECREASE_RATE_PER_HOUR = 2.0  # Rate of sleep pressure relief
HOMEOSTATIC_MAX_VALUE = 24.0  # Maximum homeostatic pressure
HOMEOSTATIC_MIN_VALUE = 0.0  # Minimum homeostatic pressure

# Process C (Circadian Rhythm)
CIRCADIAN_AMPLITUDE = 10.0  # Amplitude of circadian variation
CIRCADIAN_PERIOD_HOURS = 24.0  # Circadian period
CIRCADIAN_ACROPHASE_HOUR = 16.0  # Peak circadian alertness time

# Process W (Wake Inertia)
WAKE_INERTIA_DURATION_HOURS = 2.0  # Duration of wake inertia after waking
WAKE_INERTIA_MAX_IMPAIRMENT = 15.0  # Maximum impairment from wake inertia

# ==============================================================================
# Performance Prediction Constants
# ==============================================================================

# Effectiveness calculation weights
HOMEOSTATIC_WEIGHT = 0.4
CIRCADIAN_WEIGHT = 0.35
INERTIA_WEIGHT = 0.25

# Risk level thresholds
NEGLIGIBLE_RISK_THRESHOLD = 95.0
LOW_RISK_THRESHOLD = 85.0
MODERATE_RISK_THRESHOLD = 77.0
HIGH_RISK_THRESHOLD = 70.0
VERY_HIGH_RISK_THRESHOLD = 60.0

# ==============================================================================
# Dashboard and Reporting Constants
# ==============================================================================

# Time windows for statistics
LAST_24_HOURS = 24
LAST_7_DAYS = 168  # 7 * 24 hours
LAST_30_DAYS = 720  # 30 * 24 hours

# Top-N lists
TOP_RISK_RESIDENTS_COUNT = 5  # Number of highest-risk residents to show
TOP_UPCOMING_SHIFTS_COUNT = 10  # Number of upcoming risky shifts to display

# Update intervals
REAL_TIME_UPDATE_SECONDS = 60  # Update dashboard every minute
BACKGROUND_UPDATE_SECONDS = 300  # Background updates every 5 minutes

# ==============================================================================
# Monitoring Constants
# ==============================================================================

# Alert deduplication
DEDUPLICATION_WINDOW_HOURS = 1.0  # Hours before same alert can be generated again

# Batch processing
MAX_RESIDENTS_PER_BATCH = 100  # Maximum residents to process in one batch
CONCURRENT_UPDATE_LIMIT = 10  # Maximum concurrent resident updates

# Calculation intervals
EFFECTIVENESS_CALCULATION_INTERVAL_MINUTES = 15  # Recalculate every 15 minutes
STATE_UPDATE_INTERVAL_MINUTES = 30  # Update fatigue state every 30 minutes

# ==============================================================================
# Clinical Implications Constants
# ==============================================================================

# Procedure risk multipliers
HIGH_RISK_PROCEDURE_MIN_EFFECTIVENESS = 85.0  # Minimum for high-risk procedures
MODERATE_RISK_PROCEDURE_MIN_EFFECTIVENESS = 75.0  # Minimum for moderate-risk

# Supervision requirements
UNSUPERVISED_WORK_MIN_EFFECTIVENESS = 85.0  # Minimum for unsupervised work
CLOSE_SUPERVISION_THRESHOLD = 77.0  # Require close supervision below this

# Mandatory interventions
MANDATORY_REST_THRESHOLD = 70.0  # Mandatory rest below this
IMMEDIATE_RELIEF_THRESHOLD = 60.0  # Immediate relief required

# ==============================================================================
# Precision Constants
# ==============================================================================

# Rounding precision
EFFECTIVENESS_DECIMAL_PLACES = 2  # Round effectiveness scores to 2 decimals
TREND_DECIMAL_PLACES = 1  # Round trend values to 1 decimal
PERCENTAGE_DECIMAL_PLACES = 1  # Round percentages to 1 decimal
