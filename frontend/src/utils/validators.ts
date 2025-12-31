/**
 * Validation utilities for form inputs and data.
 */

/**
 * Validate email format.
 *
 * @param value - Email string to validate
 * @returns True if valid email format
 */
export function isValidEmail(value: string): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  // Simple but robust email regex
  const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return emailRegex.test(value);
}

/**
 * Validate UUID format.
 *
 * @param value - String to validate as UUID
 * @returns True if valid UUID (v4 format)
 */
export function isValidUUID(value: string): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }

  // UUID v4 regex pattern
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(value);
}

/**
 * Validate that date range is logical (start <= end).
 *
 * @param start - Start date
 * @param end - End date
 * @returns True if start date is before or equal to end date
 */
export function isValidDateRange(start: Date | string, end: Date | string): boolean {
  const startDate = typeof start === 'string' ? new Date(start) : start;
  const endDate = typeof end === 'string' ? new Date(end) : end;

  // Check if dates are valid
  if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
    return false;
  }

  return startDate <= endDate;
}

/**
 * Check if a value is non-empty (not null, undefined, or empty string).
 *
 * @param value - Value to check
 * @returns True if value is non-empty
 */
export function isNonEmpty(value: unknown): boolean {
  if (value === null || value === undefined) {
    return false;
  }

  if (typeof value === 'string') {
    return value.trim().length > 0;
  }

  if (Array.isArray(value)) {
    return value.length > 0;
  }

  return true;
}

/**
 * Check if a number is within a specified range (inclusive).
 *
 * @param value - Number to check
 * @param min - Minimum value (inclusive)
 * @param max - Maximum value (inclusive)
 * @returns True if value is in range [min, max]
 */
export function isInRange(value: number, min: number, max: number): boolean {
  if (typeof value !== 'number' || isNaN(value)) {
    return false;
  }

  return value >= min && value <= max;
}
