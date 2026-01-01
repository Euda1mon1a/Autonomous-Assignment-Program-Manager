"""Mathematical utility functions for calculations."""

Number = int | float


def clamp(value: Number, min_val: Number, max_val: Number) -> Number:
    """
    Clamp a value between minimum and maximum bounds.

    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Clamped value between min_val and max_val
    """
    return max(min_val, min(max_val, value))


def percentage(part: Number, whole: Number, decimals: int = 2) -> float:
    """
    Calculate percentage with safe division.

    Args:
        part: Partial value
        whole: Total value
        decimals: Number of decimal places to round to

    Returns:
        Percentage value (0.0 if whole is 0)
    """
    if whole == 0:
        return 0.0

    result = (part / whole) * 100
    return round(result, decimals)


def round_to(value: float, decimals: int = 2) -> float:
    """
    Round a float to specified decimal places.

    Args:
        value: Value to round
        decimals: Number of decimal places

    Returns:
        Rounded value
    """
    return round(value, decimals)


def safe_divide(a: Number, b: Number, default: Number = 0) -> float:
    """
    Safely divide two numbers, returning default if division by zero.

    Args:
        a: Numerator
        b: Denominator
        default: Default value to return if b is 0

    Returns:
        Result of a/b, or default if b is 0
    """
    if b == 0:
        return float(default)

    return a / b


def moving_average(values: list[Number], window: int) -> list[float]:
    """
    Calculate moving average over a list of values.

    Args:
        values: List of numeric values
        window: Size of the moving window

    Returns:
        List of moving averages (length = len(values) - window + 1)
    """
    if window <= 0:
        raise ValueError("Window size must be positive")

    if len(values) < window:
        return []

    averages = []
    for i in range(len(values) - window + 1):
        window_values = values[i:i + window]
        avg = sum(window_values) / window
        averages.append(avg)

    return averages
