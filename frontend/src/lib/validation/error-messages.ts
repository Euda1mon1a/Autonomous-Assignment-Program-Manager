/**
 * Standardized validation error messages for frontend.
 */

export const validationErrors = {
  // Required field errors
  required: (fieldName: string) => `${fieldName} is required`,
  requiredField: "This field is required",

  // String validation errors
  minLength: (fieldName: string, min: number) =>
    `${fieldName} must be at least ${min} characters`,
  maxLength: (fieldName: string, max: number) =>
    `${fieldName} must be at most ${max} characters`,
  invalidFormat: (fieldName: string) => `${fieldName} has invalid format`,

  // Email errors
  invalidEmail: "Invalid email address",
  emailDomain: (allowedDomains: string[]) =>
    `Email domain must be one of: ${allowedDomains.join(", ")}`,

  // Phone errors
  invalidPhone: "Invalid phone number format",

  // Date errors
  invalidDate: "Invalid date format (use YYYY-MM-DD)",
  futureDate: "Date must be in the future",
  pastDate: "Date must be in the past",
  dateRange: "End date must be after start date",
  dateTooSoon: (days: number) => `Date must be at least ${days} days in the future`,
  dateTooFar: (days: number) => `Date cannot be more than ${days} days in the future`,

  // Number errors
  minValue: (fieldName: string, min: number) =>
    `${fieldName} must be at least ${min}`,
  maxValue: (fieldName: string, max: number) =>
    `${fieldName} must be at most ${max}`,
  positiveNumber: (fieldName: string) => `${fieldName} must be a positive number`,

  // Person validation errors
  invalidPersonType: "Person type must be 'resident' or 'faculty'",
  pgyRequired: "Residents must have a PGY level",
  pgyInvalid: "PGY level must be between 1 and 3",
  pgyNotAllowed: "Faculty cannot have a PGY level",
  facultyRoleNotAllowed: "Residents cannot have a faculty role",

  // Assignment validation errors
  invalidAssignmentRole: "Role must be 'primary', 'supervising', or 'backup'",
  supervisingRequiresFaculty: "Only faculty can have 'supervising' role",
  doubleBooking: "Person is already assigned to this block",

  // Swap validation errors
  invalidSwapType: "Swap type must be 'one_to_one', 'absorb', or 'multi_way'",
  swapReasonRequired: "Swap reason is required",
  swapReasonTooShort: "Swap reason must be at least 10 characters",
  cannotSwapWithSelf: "Cannot swap assignments with yourself",

  // File upload errors
  fileExtension: (allowedExtensions: string[]) =>
    `File extension must be one of: ${allowedExtensions.join(", ")}`,
  fileSize: (maxSizeMB: number) =>
    `File size exceeds maximum of ${maxSizeMB}MB`,
  fileTooLarge: (actualMB: string, maxMB: number) =>
    `File size (${actualMB}MB) exceeds maximum (${maxMB}MB)`,

  // Password errors
  passwordTooShort: (min: number) => `Password must be at least ${min} characters`,
  passwordNoUppercase: "Password must contain at least one uppercase letter",
  passwordNoLowercase: "Password must contain at least one lowercase letter",
  passwordNoDigit: "Password must contain at least one digit",
  passwordNoSpecial: "Password must contain at least one special character",
  passwordsDoNotMatch: "Passwords do not match",

  // List/Array errors
  duplicateValues: (fieldName: string) => `${fieldName} contains duplicate values`,
  emptyList: (fieldName: string) => `${fieldName} cannot be empty`,
  tooManyItems: (fieldName: string, max: number) =>
    `${fieldName} cannot have more than ${max} items`,

  // UUID errors
  invalidUuid: "Invalid ID format",

  // Generic errors
  invalidValue: "Invalid value",
  somethingWentWrong: "Something went wrong. Please try again.",
  networkError: "Network error. Please check your connection.",
};

/**
 * Get field-specific error message.
 */
export function getFieldError(
  fieldName: string,
  errorType: keyof typeof validationErrors,
  ...args: any[]
): string {
  const errorFunc = validationErrors[errorType];
  if (typeof errorFunc === "function") {
    return errorFunc(fieldName, ...args);
  }
  return errorFunc as string;
}

/**
 * Format Zod error messages for display.
 */
export function formatZodError(error: any): Record<string, string> {
  const fieldErrors: Record<string, string> = {};

  if (error.errors) {
    error.errors.forEach((err: any) => {
      const path = err.path.join(".");
      fieldErrors[path] = err.message;
    });
  }

  return fieldErrors;
}

/**
 * Get user-friendly error message from API error.
 */
export function getApiErrorMessage(error: any): string {
  if (error.response?.data?.error) {
    return error.response.data.error;
  }

  if (error.response?.data?.message) {
    return error.response.data.message;
  }

  if (error.message) {
    return error.message;
  }

  return validationErrors.somethingWentWrong;
}
