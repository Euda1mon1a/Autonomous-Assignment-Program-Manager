/**
 * Form Validation Utilities
 *
 * Provides reusable validation functions for form inputs including
 * email format, password complexity, date ranges, and field requirements.
 * All validators return null for valid input or an error message string.
 *
 * @module lib/validation
 */

/**
 * Validation result containing success status and field-specific errors.
 */
export interface ValidationResult {
  /** Whether validation passed for all fields */
  valid: boolean;
  /** Map of field names to error messages */
  errors: Record<string, string>;
}

/**
 * Validates email address format using standard regex pattern.
 *
 * This function checks for basic email format compliance. Empty strings
 * are considered valid - use `validateRequired` for required field checking.
 *
 * @param email - The email address to validate
 * @returns Error message if invalid, null if valid or empty
 *
 * @example
 * ```ts
 * const error = validateEmail('user@example.com');
 * if (error) {
 *   console.error(error); // null - valid email
 * }
 *
 * const invalidError = validateEmail('invalid-email');
 * console.log(invalidError); // "Please enter a valid email address"
 * ```
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
 * Validates that a required field has a non-empty value.
 *
 * Checks that the value is not null, undefined, empty string, or whitespace-only.
 * Used to enforce required field constraints in forms.
 *
 * @param value - The value to validate
 * @param fieldName - The name of the field for personalized error message
 * @returns Error message if empty, null if valid
 *
 * @example
 * ```ts
 * const nameError = validateRequired('John Doe', 'Name');
 * console.log(nameError); // null - valid
 *
 * const emptyError = validateRequired('', 'Email');
 * console.log(emptyError); // "Email is required"
 *
 * const whitespaceError = validateRequired('   ', 'Username');
 * console.log(whitespaceError); // "Username is required"
 * ```
 */
export function validateRequired(value: string, fieldName: string): string | null {
  if (!value || !value.trim()) {
    return `${fieldName} is required`;
  }
  return null;
}

/**
 * Validates that an end date is not before a start date.
 *
 * Ensures date ranges are logically valid by checking that the end date
 * occurs on or after the start date. Both dates must be valid date strings.
 *
 * @param start - Start date string (YYYY-MM-DD format recommended)
 * @param end - End date string (YYYY-MM-DD format recommended)
 * @returns Error message if invalid, null if valid or if either date is empty
 *
 * @example
 * ```ts
 * const error = validateDateRange('2024-01-01', '2024-12-31');
 * console.log(error); // null - valid range
 *
 * const invalidError = validateDateRange('2024-12-31', '2024-01-01');
 * console.log(invalidError); // "End date must be on or after start date"
 *
 * const badFormatError = validateDateRange('invalid', '2024-01-01');
 * console.log(badFormatError); // "Invalid start date"
 * ```
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
 * List of commonly used weak passwords to reject.
 * These passwords are easily guessable and should not be accepted.
 */
const COMMON_PASSWORDS = [
  'password', 'password123', '123456', '12345678', 'qwerty',
  'abc123', 'monkey', 'master', 'dragon', 'letmein',
  'admin', 'welcome', 'login', 'passw0rd', 'password1'
];

/**
 * Validates password against security requirements.
 *
 * Password Requirements:
 * - Minimum 12 characters
 * - Maximum 128 characters
 * - At least 3 of: lowercase, uppercase, numbers, special characters
 * - Not in list of common weak passwords
 *
 * These requirements align with NIST password guidelines and industry
 * best practices for secure authentication.
 *
 * @param password - The password to validate
 * @returns Error message if invalid, null if valid
 *
 * @example
 * ```ts
 * const error = validatePassword('MyS3cure!Pass');
 * console.log(error); // null - meets all requirements
 *
 * const shortError = validatePassword('short');
 * console.log(shortError); // "Password must be at least 12 characters"
 *
 * const weakError = validatePassword('password123');
 * console.log(weakError); // "Password is too common. Please choose a stronger password"
 *
 * const complexError = validatePassword('alllowercase12chars');
 * console.log(complexError); // "Password must contain at least 3 of: lowercase, uppercase, numbers, special characters"
 * ```
 */
export function validatePassword(password: string): string | null {
  if (!password) {
    return 'Password is required';
  }

  if (password.length < 12) {
    return 'Password must be at least 12 characters';
  }

  if (password.length > 128) {
    return 'Password must be less than 128 characters';
  }

  const hasLower = /[a-z]/.test(password);
  const hasUpper = /[A-Z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

  const complexity = [hasLower, hasUpper, hasNumber, hasSpecial].filter(Boolean).length;

  if (complexity < 3) {
    return 'Password must contain at least 3 of: lowercase, uppercase, numbers, special characters';
  }

  if (COMMON_PASSWORDS.includes(password.toLowerCase())) {
    return 'Password is too common. Please choose a stronger password';
  }

  return null;
}

/**
 * Validates that a field meets minimum length requirements.
 *
 * Checks the trimmed length of the value after removing leading/trailing
 * whitespace. Empty values are considered valid - use `validateRequired`
 * for required field checking.
 *
 * @param value - The value to validate
 * @param minLength - Minimum required length (after trimming)
 * @param fieldName - The name of the field for personalized error message
 * @returns Error message if too short, null if valid or empty
 *
 * @example
 * ```ts
 * const error = validateMinLength('John Smith', 3, 'Name');
 * console.log(error); // null - valid
 *
 * const shortError = validateMinLength('Jo', 3, 'Name');
 * console.log(shortError); // "Name must be at least 3 characters"
 *
 * const emptyError = validateMinLength('', 3, 'Name');
 * console.log(emptyError); // null - use validateRequired for this case
 * ```
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
 * Validates PGY (Post-Graduate Year) level for medical residents.
 *
 * PGY levels typically range from 1 (intern) to 8 (for extended residencies
 * or fellowships). This function accepts either string or number input.
 *
 * Valid Range: 1-8
 * - PGY-1: Intern (first year)
 * - PGY-2/3: Junior residents
 * - PGY-4+: Senior residents
 * - PGY-6+: Extended programs or fellowships
 *
 * @param pgyLevel - The PGY level to validate (string or number)
 * @returns Error message if invalid, null if valid
 *
 * @example
 * ```ts
 * const error = validatePgyLevel(3);
 * console.log(error); // null - valid PGY level
 *
 * const stringError = validatePgyLevel('2');
 * console.log(stringError); // null - valid as string
 *
 * const outOfRangeError = validatePgyLevel(10);
 * console.log(outOfRangeError); // "PGY level must be between 1 and 8"
 *
 * const invalidError = validatePgyLevel('abc');
 * console.log(invalidError); // "PGY level must be a number"
 * ```
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
