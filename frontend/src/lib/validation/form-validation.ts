/**
 * Form validation utilities.
 */

import { ZodSchema } from "zod";
import { formatZodError } from "./error-messages";

/**
 * Form field state.
 */
export interface FieldState<T = any> {
  value: T;
  error?: string;
  touched: boolean;
  dirty: boolean;
}

/**
 * Form state.
 */
export interface FormState<T extends Record<string, any>> {
  values: T;
  errors: Partial<Record<keyof T, string>>;
  touched: Partial<Record<keyof T, boolean>>;
  isValid: boolean;
  isSubmitting: boolean;
  isDirty: boolean;
}

/**
 * Validate single field with schema.
 */
export function validateField<T>(
  value: T,
  schema: ZodSchema<T>
): { isValid: boolean; error?: string } {
  try {
    schema.parse(value);
    return { isValid: true };
  } catch (error: any) {
    const errors = formatZodError(error);
    const firstError = Object.values(errors)[0];
    return { isValid: false, error: firstError };
  }
}

/**
 * Validate entire form with schema.
 */
export function validateForm<T extends Record<string, any>>(
  values: T,
  schema: ZodSchema<T>
): {
  isValid: boolean;
  errors: Partial<Record<keyof T, string>>;
} {
  try {
    schema.parse(values);
    return { isValid: true, errors: {} };
  } catch (error: any) {
    const errors = formatZodError(error) as Partial<Record<keyof T, string>>;
    return { isValid: false, errors };
  }
}

/**
 * Create field validator function.
 */
export function createFieldValidator<T>(
  schema: ZodSchema<T>
): (value: T) => string | undefined {
  return (value: T) => {
    const result = validateField(value, schema);
    return result.error;
  };
}

/**
 * Debounce validation for async fields.
 */
export function debounceValidation<T>(
  validator: (value: T) => Promise<string | undefined>,
  delay: number = 300
): (value: T) => Promise<string | undefined> {
  let timeoutId: NodeJS.Timeout;

  return (value: T) => {
    return new Promise((resolve) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(async () => {
        const error = await validator(value);
        resolve(error);
      }, delay);
    });
  };
}

/**
 * Validate required field.
 */
export function validateRequired(value: any): string | undefined {
  if (value === null || value === undefined || value === "") {
    return "This field is required";
  }
  return undefined;
}

/**
 * Validate required array field.
 */
export function validateRequiredArray(value: any[]): string | undefined {
  if (!value || value.length === 0) {
    return "At least one item is required";
  }
  return undefined;
}

/**
 * Compose multiple validators.
 */
export function composeValidators<T>(
  ...validators: Array<(value: T) => string | undefined>
): (value: T) => string | undefined {
  return (value: T) => {
    for (const validator of validators) {
      const error = validator(value);
      if (error) return error;
    }
    return undefined;
  };
}

/**
 * Validate on blur (for form fields).
 */
export function createBlurHandler<T>(
  fieldName: string,
  value: T,
  setFieldError: (field: string, error?: string) => void,
  setFieldTouched: (field: string) => void,
  validator?: (value: T) => string | undefined
) {
  return () => {
    setFieldTouched(fieldName);
    if (validator) {
      const error = validator(value);
      setFieldError(fieldName, error);
    }
  };
}

/**
 * Validate on change (for form fields).
 */
export function createChangeHandler<T>(
  fieldName: string,
  setValue: (field: string, value: T) => void,
  setFieldError: (field: string, error?: string) => void,
  setFieldDirty: (field: string) => void,
  validator?: (value: T) => string | undefined
) {
  return (value: T) => {
    setValue(fieldName, value);
    setFieldDirty(fieldName);
    if (validator) {
      const error = validator(value);
      setFieldError(fieldName, error);
    }
  };
}

/**
 * Check if form has errors.
 */
export function hasFormErrors<T extends Record<string, any>>(
  errors: Partial<Record<keyof T, string>>
): boolean {
  return Object.values(errors).some((error) => error !== undefined);
}

/**
 * Get first error in form.
 */
export function getFirstFormError<T extends Record<string, any>>(
  errors: Partial<Record<keyof T, string>>
): string | undefined {
  return Object.values(errors).find((error) => error !== undefined);
}

/**
 * Check if field should show error.
 */
export function shouldShowError(
  error?: string,
  touched?: boolean,
  submitCount: number = 0
): boolean {
  return Boolean(error && (touched || submitCount > 0));
}
