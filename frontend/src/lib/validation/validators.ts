/**
 * Custom validation functions for frontend.
 */

/**
 * Validate future date.
 */
export function validateFutureDate(
  dateString: string,
  minDaysAhead: number = 0
): { isValid: boolean; error?: string } {
  const inputDate = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const minDate = new Date(today);
  minDate.setDate(minDate.getDate() + minDaysAhead);

  if (inputDate < minDate) {
    return {
      isValid: false,
      error:
        minDaysAhead > 0
          ? `Date must be at least ${minDaysAhead} days in the future`
          : "Date must be in the future",
    };
  }

  return { isValid: true };
}

/**
 * Validate date range.
 */
export function validateDateRange(
  startDate: string,
  endDate: string
): { isValid: boolean; error?: string } {
  const start = new Date(startDate);
  const end = new Date(endDate);

  if (end < start) {
    return {
      isValid: false,
      error: "End date must be after start date",
    };
  }

  return { isValid: true };
}

/**
 * Validate email domain.
 */
export function validateEmailDomain(
  email: string,
  allowedDomains?: string[]
): { isValid: boolean; error?: string } {
  if (!email || !email.includes("@")) {
    return { isValid: false, error: "Invalid email format" };
  }

  const domain = email.split("@")[1].toLowerCase();

  if (allowedDomains && allowedDomains.length > 0) {
    const isAllowed = allowedDomains.some((d) => d.toLowerCase() === domain);
    if (!isAllowed) {
      return {
        isValid: false,
        error: `Email domain must be one of: ${allowedDomains.join(", ")}`,
      };
    }
  }

  return { isValid: true };
}

/**
 * Validate file extension.
 */
export function validateFileExtension(
  filename: string,
  allowedExtensions: string[]
): { isValid: boolean; error?: string } {
  if (!filename || !filename.includes(".")) {
    return { isValid: false, error: "File must have an extension" };
  }

  const extension = filename.split(".").pop()?.toLowerCase();

  if (!extension || !allowedExtensions.includes(extension)) {
    return {
      isValid: false,
      error: `File extension must be one of: ${allowedExtensions.join(", ")}`,
    };
  }

  return { isValid: true };
}

/**
 * Validate file size.
 */
export function validateFileSize(
  sizeBytes: number,
  maxSizeMB: number
): { isValid: boolean; error?: string } {
  const maxBytes = maxSizeMB * 1024 * 1024;

  if (sizeBytes > maxBytes) {
    const actualMB = (sizeBytes / (1024 * 1024)).toFixed(1);
    return {
      isValid: false,
      error: `File size (${actualMB}MB) exceeds maximum (${maxSizeMB}MB)`,
    };
  }

  return { isValid: true };
}

/**
 * Validate PGY level for person type.
 */
export function validatePgyLevel(
  pgyLevel: number | null,
  personType: string
): { isValid: boolean; error?: string } {
  if (personType === "faculty") {
    if (pgyLevel !== null) {
      return {
        isValid: false,
        error: "Faculty cannot have a PGY level",
      };
    }
  } else if (personType === "resident") {
    if (pgyLevel === null) {
      return {
        isValid: false,
        error: "Residents must have a PGY level",
      };
    }
    if (pgyLevel < 1 || pgyLevel > 3) {
      return {
        isValid: false,
        error: "PGY level must be between 1 and 3",
      };
    }
  }

  return { isValid: true };
}

/**
 * Validate faculty role for person type.
 */
export function validateFacultyRole(
  facultyRole: string | null,
  personType: string
): { isValid: boolean; error?: string } {
  if (personType === "resident" && facultyRole !== null) {
    return {
      isValid: false,
      error: "Residents cannot have a faculty role",
    };
  }

  return { isValid: true };
}

/**
 * Validate assignment role compatibility.
 */
export function validateAssignmentRole(
  role: string,
  personType: string
): { isValid: boolean; error?: string } {
  if (role === "supervising" && personType !== "faculty") {
    return {
      isValid: false,
      error: "Only faculty can have 'supervising' role",
    };
  }

  return { isValid: true };
}

/**
 * Validate unique values in list.
 */
export function validateUniqueValues<T>(
  values: T[],
  fieldName?: string
): { isValid: boolean; error?: string; duplicates?: T[] } {
  const seen = new Set<T>();
  const duplicates: T[] = [];

  for (const value of values) {
    if (seen.has(value)) {
      duplicates.push(value);
    } else {
      seen.add(value);
    }
  }

  if (duplicates.length > 0) {
    return {
      isValid: false,
      error: fieldName
        ? `${fieldName} contains duplicate values`
        : "List contains duplicate values",
      duplicates,
    };
  }

  return { isValid: true };
}

/**
 * Validate password strength.
 */
export function validatePasswordStrength(password: string): {
  isValid: boolean;
  errors: string[];
  strength: "weak" | "medium" | "strong";
} {
  const errors: string[] = [];
  let score = 0;

  if (password.length < 12) {
    errors.push("Password must be at least 12 characters");
  } else {
    score += 1;
  }

  if (!/[A-Z]/.test(password)) {
    errors.push("Password must contain at least one uppercase letter");
  } else {
    score += 1;
  }

  if (!/[a-z]/.test(password)) {
    errors.push("Password must contain at least one lowercase letter");
  } else {
    score += 1;
  }

  if (!/\d/.test(password)) {
    errors.push("Password must contain at least one digit");
  } else {
    score += 1;
  }

  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push("Password must contain at least one special character");
  } else {
    score += 1;
  }

  // Additional strength checks
  if (password.length >= 16) score += 1;
  if (/[!@#$%^&*(),.?":{}|<>]{2,}/.test(password)) score += 1;

  let strength: "weak" | "medium" | "strong";
  if (score < 3) strength = "weak";
  else if (score < 5) strength = "medium";
  else strength = "strong";

  return {
    isValid: errors.length === 0,
    errors,
    strength,
  };
}
