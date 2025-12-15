/**
 * Form validation utilities
 */

export interface ValidationResult {
  valid: boolean;
  errors: Record<string, string>;
}

/**
 * Validates email format
 * @param email - The email to validate
 * @returns Error message if invalid, null if valid
 */
export function validateEmail(email: string): string | null {
  if (!email) {
    return null; // Empty email is valid (use validateRequired for required check)
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return 'Please enter a valid email address';
  }

  return null;
}

/**
 * Validates that a value is not empty
 * @param value - The value to validate
 * @param fieldName - The name of the field for error message
 * @returns Error message if empty, null if valid
 */
export function validateRequired(value: string, fieldName: string): string | null {
  if (!value || !value.trim()) {
    return `${fieldName} is required`;
  }
  return null;
}

/**
 * Validates that end date is not before start date
 * @param start - Start date string (YYYY-MM-DD format)
 * @param end - End date string (YYYY-MM-DD format)
 * @returns Error message if invalid, null if valid
 */
export function validateDateRange(start: string, end: string): string | null {
  if (!start || !end) {
    return null; // Use validateRequired for required check
  }

  const startDate = new Date(start);
  const endDate = new Date(end);

  if (isNaN(startDate.getTime())) {
    return 'Invalid start date';
  }

  if (isNaN(endDate.getTime())) {
    return 'Invalid end date';
  }

  if (startDate > endDate) {
    return 'End date must be on or after start date';
  }

  return null;
}

/**
 * Validates password requirements
 * @param password - The password to validate
 * @returns Error message if invalid, null if valid
 */
export function validatePassword(password: string): string | null {
  if (!password) {
    return 'Password is required';
  }

  if (password.length < 1) {
    return 'Password cannot be empty';
  }

  return null;
}

/**
 * Validates minimum length requirement
 * @param value - The value to validate
 * @param minLength - Minimum required length
 * @param fieldName - The name of the field for error message
 * @returns Error message if invalid, null if valid
 */
export function validateMinLength(value: string, minLength: number, fieldName: string): string | null {
  if (!value) {
    return null; // Use validateRequired for required check
  }

  if (value.trim().length < minLength) {
    return `${fieldName} must be at least ${minLength} characters`;
  }

  return null;
}

/**
 * Validates PGY level for residents (1-8)
 * @param pgyLevel - The PGY level to validate
 * @returns Error message if invalid, null if valid
 */
export function validatePgyLevel(pgyLevel: string | number): string | null {
  const level = typeof pgyLevel === 'string' ? parseInt(pgyLevel, 10) : pgyLevel;

  if (isNaN(level)) {
    return 'PGY level must be a number';
  }

  if (level < 1 || level > 8) {
    return 'PGY level must be between 1 and 8';
  }

  return null;
}
