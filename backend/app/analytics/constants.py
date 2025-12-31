"""
Constants for Analytics Engine.

This module centralizes magic numbers used in trend detection, anomaly detection,
and statistical analysis components.
"""

# ==============================================================================
# Trend Detection Constants
# ==============================================================================

# Minimum data requirements
MIN_OBSERVATIONS_FOR_TREND = 4  # Minimum data points for trend analysis
MIN_OBSERVATIONS_FOR_CHANGE_POINT = 3  # Minimum for change point detection
MIN_OBSERVATIONS_FOR_VOLATILITY = 2  # Minimum for volatility calculation

# Trend thresholds
STABLE_TREND_SLOPE_THRESHOLD = 0.01  # Absolute slope below this is "stable"

# Statistical significance thresholds
HIGH_CONFIDENCE_P_VALUE = 0.01  # p-value threshold for high confidence
HIGH_CONFIDENCE_R_SQUARED = 0.7  # R² threshold for high confidence
MEDIUM_CONFIDENCE_P_VALUE = 0.05  # p-value threshold for medium confidence
MEDIUM_CONFIDENCE_R_SQUARED = 0.5  # R² threshold for medium confidence

# Change point detection
DEFAULT_CHANGE_POINT_Z_THRESHOLD = 2.0  # ~95% confidence interval

# Cycle detection
DEFAULT_MAX_CYCLE_PERIOD = 30  # Maximum period to test for cycles (days)
MIN_CYCLE_PERIOD = 1  # Minimum cycle period
CYCLE_STRENGTH_THRESHOLD = 0.3  # Minimum autocorrelation for significant cycle

# Volatility analysis
DEFAULT_VOLATILITY_WINDOW = 7  # Rolling window for volatility (7 days)

# Outlier detection
DEFAULT_ZSCORE_THRESHOLD = 3.0  # Standard deviations for zscore method
DEFAULT_IQR_MULTIPLIER = 3.0  # IQR multiplier for outlier detection (more conservative)
STANDARD_IQR_MULTIPLIER = 1.5  # Standard IQR multiplier (less conservative)

# Percentiles for analysis
FIRST_QUARTILE = 0.25
THIRD_QUARTILE = 0.75

# ==============================================================================
# Anomaly Detection Constants
# ==============================================================================

# Anomaly score thresholds
ANOMALY_SCORE_LOW = 0.3
ANOMALY_SCORE_MEDIUM = 0.6
ANOMALY_SCORE_HIGH = 0.8

# Window sizes for rolling statistics
ANOMALY_DETECTION_WINDOW = 14  # 2 weeks
SHORT_TERM_WINDOW = 7  # 1 week
LONG_TERM_WINDOW = 30  # 1 month

# Statistical thresholds for anomalies
ANOMALY_Z_SCORE_THRESHOLD = 3.0
ANOMALY_PERCENTILE_THRESHOLD = 95.0

# ==============================================================================
# Time Series Constants
# ==============================================================================

# Resampling intervals
HOURLY_INTERVAL_MINUTES = 60
DAILY_INTERVAL_HOURS = 24
WEEKLY_INTERVAL_DAYS = 7
MONTHLY_INTERVAL_DAYS = 30

# Historical data retention
DEFAULT_HISTORY_RETENTION_DAYS = 90
EXTENDED_HISTORY_RETENTION_DAYS = 365

# ==============================================================================
# Reporting Constants
# ==============================================================================

# Top-N lists
TOP_ITEMS_COUNT = 10  # Number of top items to show in reports
TOP_RISKS_COUNT = 5  # Number of top risks to highlight

# Percentage formatting
PERCENTAGE_PRECISION_DECIMALS = 2
METRIC_PRECISION_DECIMALS = 4

# ==============================================================================
# Performance Constants
# ==============================================================================

# Batch sizes for processing
DEFAULT_BATCH_SIZE = 1000
LARGE_BATCH_SIZE = 5000

# Cache timeouts
CACHE_TIMEOUT_SECONDS = 300  # 5 minutes
EXTENDED_CACHE_TIMEOUT_SECONDS = 3600  # 1 hour
