"""
Constants for Fatigue Risk Management System (FRMS).

This module centralizes magic numbers used in the three-process model,
performance prediction, and fatigue monitoring.
"""

***REMOVED*** ==============================================================================
***REMOVED*** Fatigue Threshold Constants (Based on Industry Standards)
***REMOVED*** ==============================================================================

***REMOVED*** Effectiveness thresholds (percentage)
THRESHOLD_OPTIMAL = 95.0  ***REMOVED*** Optimal performance level
THRESHOLD_ACCEPTABLE = 85.0  ***REMOVED*** Acceptable but below optimal
THRESHOLD_FAA_CAUTION = 77.0  ***REMOVED*** FAA caution threshold (aviation standard)
THRESHOLD_FRA_HIGH_RISK = 70.0  ***REMOVED*** FRA high-risk threshold (rail standard)
THRESHOLD_CRITICAL = 60.0  ***REMOVED*** Critical - immediate action required

***REMOVED*** Alert severity mappings
EMERGENCY_THRESHOLD = THRESHOLD_CRITICAL  ***REMOVED*** 60%
CRITICAL_ALERT_THRESHOLD = THRESHOLD_FRA_HIGH_RISK  ***REMOVED*** 70%
WARNING_ALERT_THRESHOLD = THRESHOLD_FAA_CAUTION  ***REMOVED*** 77%
INFO_ALERT_THRESHOLD = THRESHOLD_ACCEPTABLE  ***REMOVED*** 85%

***REMOVED*** ==============================================================================
***REMOVED*** Trend Detection Constants
***REMOVED*** ==============================================================================

***REMOVED*** Trend analysis window
TREND_WINDOW_HOURS = 4.0  ***REMOVED*** Look back 4 hours for trend calculation
TREND_THRESHOLD_PERCENT = 5.0  ***REMOVED*** 5% change is significant

***REMOVED*** Historical data retention
EFFECTIVENESS_HISTORY_HOURS = 48  ***REMOVED*** Keep last 48 hours
ALERT_DEDUPLICATION_HOURS = 1  ***REMOVED*** Don't repeat same alert within 1 hour

***REMOVED*** ==============================================================================
***REMOVED*** Physiological Constants
***REMOVED*** ==============================================================================

***REMOVED*** Extended wakefulness thresholds
EXTENDED_WAKEFULNESS_HOURS = 16  ***REMOVED*** Hours awake threshold for warning
CRITICAL_WAKEFULNESS_HOURS = 24  ***REMOVED*** Hours awake for critical warning

***REMOVED*** Circadian rhythm
WOCL_START_HOUR = 2  ***REMOVED*** Window of Circadian Low start (2 AM)
WOCL_END_HOUR = 6  ***REMOVED*** Window of Circadian Low end (6 AM)

***REMOVED*** Sleep requirements
MINIMUM_SLEEP_HOURS = 7  ***REMOVED*** Minimum recommended sleep
OPTIMAL_SLEEP_HOURS = 8  ***REMOVED*** Optimal sleep duration
REST_PERIOD_HOURS = 2  ***REMOVED*** Minimum rest period before returning to duty

***REMOVED*** ==============================================================================
***REMOVED*** Three-Process Model Constants
***REMOVED*** ==============================================================================

***REMOVED*** Process S (Sleep/Wake Homeostasis)
HOMEOSTATIC_INCREASE_RATE_PER_HOUR = 1.0  ***REMOVED*** Rate of sleep pressure buildup
HOMEOSTATIC_DECREASE_RATE_PER_HOUR = 2.0  ***REMOVED*** Rate of sleep pressure relief
HOMEOSTATIC_MAX_VALUE = 24.0  ***REMOVED*** Maximum homeostatic pressure
HOMEOSTATIC_MIN_VALUE = 0.0  ***REMOVED*** Minimum homeostatic pressure

***REMOVED*** Process C (Circadian Rhythm)
CIRCADIAN_AMPLITUDE = 10.0  ***REMOVED*** Amplitude of circadian variation
CIRCADIAN_PERIOD_HOURS = 24.0  ***REMOVED*** Circadian period
CIRCADIAN_ACROPHASE_HOUR = 16.0  ***REMOVED*** Peak circadian alertness time

***REMOVED*** Process W (Wake Inertia)
WAKE_INERTIA_DURATION_HOURS = 2.0  ***REMOVED*** Duration of wake inertia after waking
WAKE_INERTIA_MAX_IMPAIRMENT = 15.0  ***REMOVED*** Maximum impairment from wake inertia

***REMOVED*** ==============================================================================
***REMOVED*** Performance Prediction Constants
***REMOVED*** ==============================================================================

***REMOVED*** Effectiveness calculation weights
HOMEOSTATIC_WEIGHT = 0.4
CIRCADIAN_WEIGHT = 0.35
INERTIA_WEIGHT = 0.25

***REMOVED*** Risk level thresholds
NEGLIGIBLE_RISK_THRESHOLD = 95.0
LOW_RISK_THRESHOLD = 85.0
MODERATE_RISK_THRESHOLD = 77.0
HIGH_RISK_THRESHOLD = 70.0
VERY_HIGH_RISK_THRESHOLD = 60.0

***REMOVED*** ==============================================================================
***REMOVED*** Dashboard and Reporting Constants
***REMOVED*** ==============================================================================

***REMOVED*** Time windows for statistics
LAST_24_HOURS = 24
LAST_7_DAYS = 168  ***REMOVED*** 7 * 24 hours
LAST_30_DAYS = 720  ***REMOVED*** 30 * 24 hours

***REMOVED*** Top-N lists
TOP_RISK_RESIDENTS_COUNT = 5  ***REMOVED*** Number of highest-risk residents to show
TOP_UPCOMING_SHIFTS_COUNT = 10  ***REMOVED*** Number of upcoming risky shifts to display

***REMOVED*** Update intervals
REAL_TIME_UPDATE_SECONDS = 60  ***REMOVED*** Update dashboard every minute
BACKGROUND_UPDATE_SECONDS = 300  ***REMOVED*** Background updates every 5 minutes

***REMOVED*** ==============================================================================
***REMOVED*** Monitoring Constants
***REMOVED*** ==============================================================================

***REMOVED*** Alert deduplication
DEDUPLICATION_WINDOW_HOURS = 1.0  ***REMOVED*** Hours before same alert can be generated again

***REMOVED*** Batch processing
MAX_RESIDENTS_PER_BATCH = 100  ***REMOVED*** Maximum residents to process in one batch
CONCURRENT_UPDATE_LIMIT = 10  ***REMOVED*** Maximum concurrent resident updates

***REMOVED*** Calculation intervals
EFFECTIVENESS_CALCULATION_INTERVAL_MINUTES = 15  ***REMOVED*** Recalculate every 15 minutes
STATE_UPDATE_INTERVAL_MINUTES = 30  ***REMOVED*** Update fatigue state every 30 minutes

***REMOVED*** ==============================================================================
***REMOVED*** Clinical Implications Constants
***REMOVED*** ==============================================================================

***REMOVED*** Procedure risk multipliers
HIGH_RISK_PROCEDURE_MIN_EFFECTIVENESS = 85.0  ***REMOVED*** Minimum for high-risk procedures
MODERATE_RISK_PROCEDURE_MIN_EFFECTIVENESS = 75.0  ***REMOVED*** Minimum for moderate-risk

***REMOVED*** Supervision requirements
UNSUPERVISED_WORK_MIN_EFFECTIVENESS = 85.0  ***REMOVED*** Minimum for unsupervised work
CLOSE_SUPERVISION_THRESHOLD = 77.0  ***REMOVED*** Require close supervision below this

***REMOVED*** Mandatory interventions
MANDATORY_REST_THRESHOLD = 70.0  ***REMOVED*** Mandatory rest below this
IMMEDIATE_RELIEF_THRESHOLD = 60.0  ***REMOVED*** Immediate relief required

***REMOVED*** ==============================================================================
***REMOVED*** Precision Constants
***REMOVED*** ==============================================================================

***REMOVED*** Rounding precision
EFFECTIVENESS_DECIMAL_PLACES = 2  ***REMOVED*** Round effectiveness scores to 2 decimals
TREND_DECIMAL_PLACES = 1  ***REMOVED*** Round trend values to 1 decimal
PERCENTAGE_DECIMAL_PLACES = 1  ***REMOVED*** Round percentages to 1 decimal
