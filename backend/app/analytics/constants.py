"""
Constants for Analytics Engine.

This module centralizes magic numbers used in trend detection, anomaly detection,
and statistical analysis components.
"""

***REMOVED*** ==============================================================================
***REMOVED*** Trend Detection Constants
***REMOVED*** ==============================================================================

***REMOVED*** Minimum data requirements
MIN_OBSERVATIONS_FOR_TREND = 4  ***REMOVED*** Minimum data points for trend analysis
MIN_OBSERVATIONS_FOR_CHANGE_POINT = 3  ***REMOVED*** Minimum for change point detection
MIN_OBSERVATIONS_FOR_VOLATILITY = 2  ***REMOVED*** Minimum for volatility calculation

***REMOVED*** Trend thresholds
STABLE_TREND_SLOPE_THRESHOLD = 0.01  ***REMOVED*** Absolute slope below this is "stable"

***REMOVED*** Statistical significance thresholds
HIGH_CONFIDENCE_P_VALUE = 0.01  ***REMOVED*** p-value threshold for high confidence
HIGH_CONFIDENCE_R_SQUARED = 0.7  ***REMOVED*** R² threshold for high confidence
MEDIUM_CONFIDENCE_P_VALUE = 0.05  ***REMOVED*** p-value threshold for medium confidence
MEDIUM_CONFIDENCE_R_SQUARED = 0.5  ***REMOVED*** R² threshold for medium confidence

***REMOVED*** Change point detection
DEFAULT_CHANGE_POINT_Z_THRESHOLD = 2.0  ***REMOVED*** ~95% confidence interval

***REMOVED*** Cycle detection
DEFAULT_MAX_CYCLE_PERIOD = 30  ***REMOVED*** Maximum period to test for cycles (days)
MIN_CYCLE_PERIOD = 1  ***REMOVED*** Minimum cycle period
CYCLE_STRENGTH_THRESHOLD = 0.3  ***REMOVED*** Minimum autocorrelation for significant cycle

***REMOVED*** Volatility analysis
DEFAULT_VOLATILITY_WINDOW = 7  ***REMOVED*** Rolling window for volatility (7 days)

***REMOVED*** Outlier detection
DEFAULT_ZSCORE_THRESHOLD = 3.0  ***REMOVED*** Standard deviations for zscore method
DEFAULT_IQR_MULTIPLIER = 3.0  ***REMOVED*** IQR multiplier for outlier detection (more conservative)
STANDARD_IQR_MULTIPLIER = 1.5  ***REMOVED*** Standard IQR multiplier (less conservative)

***REMOVED*** Percentiles for analysis
FIRST_QUARTILE = 0.25
THIRD_QUARTILE = 0.75

***REMOVED*** ==============================================================================
***REMOVED*** Anomaly Detection Constants
***REMOVED*** ==============================================================================

***REMOVED*** Anomaly score thresholds
ANOMALY_SCORE_LOW = 0.3
ANOMALY_SCORE_MEDIUM = 0.6
ANOMALY_SCORE_HIGH = 0.8

***REMOVED*** Window sizes for rolling statistics
ANOMALY_DETECTION_WINDOW = 14  ***REMOVED*** 2 weeks
SHORT_TERM_WINDOW = 7  ***REMOVED*** 1 week
LONG_TERM_WINDOW = 30  ***REMOVED*** 1 month

***REMOVED*** Statistical thresholds for anomalies
ANOMALY_Z_SCORE_THRESHOLD = 3.0
ANOMALY_PERCENTILE_THRESHOLD = 95.0

***REMOVED*** ==============================================================================
***REMOVED*** Time Series Constants
***REMOVED*** ==============================================================================

***REMOVED*** Resampling intervals
HOURLY_INTERVAL_MINUTES = 60
DAILY_INTERVAL_HOURS = 24
WEEKLY_INTERVAL_DAYS = 7
MONTHLY_INTERVAL_DAYS = 30

***REMOVED*** Historical data retention
DEFAULT_HISTORY_RETENTION_DAYS = 90
EXTENDED_HISTORY_RETENTION_DAYS = 365

***REMOVED*** ==============================================================================
***REMOVED*** Reporting Constants
***REMOVED*** ==============================================================================

***REMOVED*** Top-N lists
TOP_ITEMS_COUNT = 10  ***REMOVED*** Number of top items to show in reports
TOP_RISKS_COUNT = 5  ***REMOVED*** Number of top risks to highlight

***REMOVED*** Percentage formatting
PERCENTAGE_PRECISION_DECIMALS = 2
METRIC_PRECISION_DECIMALS = 4

***REMOVED*** ==============================================================================
***REMOVED*** Performance Constants
***REMOVED*** ==============================================================================

***REMOVED*** Batch sizes for processing
DEFAULT_BATCH_SIZE = 1000
LARGE_BATCH_SIZE = 5000

***REMOVED*** Cache timeouts
CACHE_TIMEOUT_SECONDS = 300  ***REMOVED*** 5 minutes
EXTENDED_CACHE_TIMEOUT_SECONDS = 3600  ***REMOVED*** 1 hour
