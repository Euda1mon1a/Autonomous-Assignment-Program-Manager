/**
 * Tests for Form Validation Utilities
 *
 * Tests all validation functions including email, password, required fields,
 * date ranges, minimum length, and PGY level validation.
 */
import {
  validateEmail,
  validateRequired,
  validateDateRange,
  validatePassword,
  validateMinLength,
  validatePgyLevel,
  type ValidationResult,
} from '@/lib/validation'

// ============================================================================
// validateEmail Tests
// ============================================================================

describe('validateEmail', () => {
  describe('valid emails', () => {
    it('should return null for valid email addresses', () => {
      const validEmails = [
        'user@example.com',
        'test.user@domain.com',
        'john.doe@company.co.uk',
        'admin@localhost.local',
        'user+tag@example.com',
        'name123@test-domain.com',
      ]

      validEmails.forEach((email) => {
        expect(validateEmail(email)).toBeNull()
      })
    })

    it('should return null for empty string', () => {
      expect(validateEmail('')).toBeNull()
    })

    it('should handle emails with numbers', () => {
      expect(validateEmail('user123@example123.com')).toBeNull()
    })

    it('should handle emails with hyphens in domain', () => {
      expect(validateEmail('user@test-domain.com')).toBeNull()
    })

    it('should handle emails with subdomains', () => {
      expect(validateEmail('user@mail.example.com')).toBeNull()
    })
  })

  describe('invalid emails', () => {
    it('should return error for email without @', () => {
      expect(validateEmail('userexample.com')).toBe('Please enter a valid email address')
    })

    it('should return error for email without domain', () => {
      expect(validateEmail('user@')).toBe('Please enter a valid email address')
    })

    it('should return error for email without username', () => {
      expect(validateEmail('@example.com')).toBe('Please enter a valid email address')
    })

    it('should return error for email without TLD', () => {
      expect(validateEmail('user@domain')).toBe('Please enter a valid email address')
    })

    it('should return error for email with spaces', () => {
      expect(validateEmail('user name@example.com')).toBe('Please enter a valid email address')
      expect(validateEmail('user@example .com')).toBe('Please enter a valid email address')
    })

    it('should return error for email with multiple @', () => {
      expect(validateEmail('user@@example.com')).toBe('Please enter a valid email address')
      expect(validateEmail('user@test@example.com')).toBe('Please enter a valid email address')
    })

    it('should return error for plain text', () => {
      expect(validateEmail('not-an-email')).toBe('Please enter a valid email address')
    })

    it('should return error for email missing dot in domain', () => {
      expect(validateEmail('user@examplecom')).toBe('Please enter a valid email address')
    })
  })
})

// ============================================================================
// validateRequired Tests
// ============================================================================

describe('validateRequired', () => {
  describe('valid inputs', () => {
    it('should return null for non-empty strings', () => {
      expect(validateRequired('John Doe', 'Name')).toBeNull()
      expect(validateRequired('test@example.com', 'Email')).toBeNull()
      expect(validateRequired('a', 'Field')).toBeNull()
    })

    it('should return null for strings with content after trimming', () => {
      expect(validateRequired('  value  ', 'Field')).toBeNull()
      expect(validateRequired('\tvalue\t', 'Field')).toBeNull()
    })
  })

  describe('invalid inputs', () => {
    it('should return error for empty string', () => {
      expect(validateRequired('', 'Name')).toBe('Name is required')
      expect(validateRequired('', 'Email')).toBe('Email is required')
    })

    it('should return error for whitespace-only strings', () => {
      expect(validateRequired('   ', 'Username')).toBe('Username is required')
      expect(validateRequired('\t\n', 'Field')).toBe('Field is required')
    })

    it('should use field name in error message', () => {
      expect(validateRequired('', 'Email Address')).toBe('Email Address is required')
      expect(validateRequired('', 'Password')).toBe('Password is required')
    })
  })
})

// ============================================================================
// validateDateRange Tests
// ============================================================================

describe('validateDateRange', () => {
  describe('valid date ranges', () => {
    it('should return null for valid date ranges', () => {
      expect(validateDateRange('2024-01-01', '2024-12-31')).toBeNull()
      expect(validateDateRange('2024-06-15', '2024-06-15')).toBeNull() // Same day
    })

    it('should return null for empty dates', () => {
      expect(validateDateRange('', '')).toBeNull()
      expect(validateDateRange('', '2024-01-01')).toBeNull()
      expect(validateDateRange('2024-01-01', '')).toBeNull()
    })

    it('should handle different date formats', () => {
      expect(validateDateRange('2024/01/01', '2024/12/31')).toBeNull()
      expect(validateDateRange('01-01-2024', '12-31-2024')).toBeNull()
    })

    it('should accept ISO datetime strings', () => {
      expect(validateDateRange(
        '2024-01-01T00:00:00Z',
        '2024-12-31T23:59:59Z'
      )).toBeNull()
    })

    it('should handle dates far apart', () => {
      expect(validateDateRange('2020-01-01', '2030-12-31')).toBeNull()
    })
  })

  describe('invalid date ranges', () => {
    it('should return error when end date is before start date', () => {
      expect(validateDateRange('2024-12-31', '2024-01-01')).toBe(
        'End date must be on or after start date'
      )
    })

    it('should return error for invalid start date', () => {
      expect(validateDateRange('invalid-date', '2024-12-31')).toBe('Invalid start date')
      expect(validateDateRange('2024-13-01', '2024-12-31')).toBe('Invalid start date')
      expect(validateDateRange('not-a-date', '2024-01-01')).toBe('Invalid start date')
    })

    it('should return error for invalid end date', () => {
      expect(validateDateRange('2024-01-01', 'invalid-date')).toBe('Invalid end date')
      expect(validateDateRange('2024-01-01', '2024-13-45')).toBe('Invalid end date')
      expect(validateDateRange('2024-01-01', 'not-a-date')).toBe('Invalid end date')
    })

    it('should handle year 2038 boundary correctly', () => {
      // Test dates beyond 2038 (potential timestamp overflow)
      expect(validateDateRange('2040-01-01', '2039-12-31')).toBe(
        'End date must be on or after start date'
      )
    })
  })
})

// ============================================================================
// validatePassword Tests
// ============================================================================

describe('validatePassword', () => {
  describe('valid passwords', () => {
    it('should return null for passwords meeting all requirements', () => {
      const validPasswords = [
        'MyS3cure!Pass',
        'Abcdefgh123!',
        'P@ssw0rd1234',
        'Complex!Pass123',
        'Tr0ng#Password',
        '12CharPass!A',
      ]

      validPasswords.forEach((password) => {
        expect(validatePassword(password)).toBeNull()
      })
    })

    it('should accept passwords with 3 of 4 character types', () => {
      expect(validatePassword('LowercaseUpper123')).toBeNull() // lower + upper + number
      expect(validatePassword('LowercaseUpper!!!')).toBeNull() // lower + upper + special
      expect(validatePassword('lowercase123!!!')).toBeNull() // lower + number + special
      expect(validatePassword('UPPERCASE123!!!')).toBeNull() // upper + number + special
    })

    it('should accept long passwords up to 128 characters', () => {
      const longPassword = 'A'.repeat(64) + 'a'.repeat(32) + '1'.repeat(32)
      expect(validatePassword(longPassword)).toBeNull()
    })

    it('should accept passwords exactly 128 characters', () => {
      const password = 'A'.repeat(64) + 'a'.repeat(32) + '1'.repeat(32)
      expect(validatePassword(password)).toBeNull()
    })

    it('should accept passwords with various special characters', () => {
      expect(validatePassword('Test123!@#$%')).toBeNull()
      expect(validatePassword('Test123^&*()')).toBeNull()
      expect(validatePassword('Test123,.?":{}|<>')).toBeNull()
    })
  })

  describe('invalid passwords - length', () => {
    it('should return error for empty password', () => {
      expect(validatePassword('')).toBe('Password is required')
    })

    it('should return error for passwords under 12 characters', () => {
      expect(validatePassword('Short1!')).toBe('Password must be at least 12 characters')
      expect(validatePassword('Ab1!')).toBe('Password must be at least 12 characters')
      expect(validatePassword('12345678901')).toBe('Password must be at least 12 characters')
    })

    it('should return error for passwords over 128 characters', () => {
      const tooLong = 'A'.repeat(129)
      expect(validatePassword(tooLong)).toBe('Password must be less than 128 characters')
    })
  })

  describe('invalid passwords - complexity', () => {
    it('should return error for passwords with only 1 character type', () => {
      expect(validatePassword('alllowercase')).toBe(
        'Password must contain at least 3 of: lowercase, uppercase, numbers, special characters'
      )
      expect(validatePassword('ALLUPPERCASE')).toBe(
        'Password must contain at least 3 of: lowercase, uppercase, numbers, special characters'
      )
      expect(validatePassword('123456789012')).toBe(
        'Password must contain at least 3 of: lowercase, uppercase, numbers, special characters'
      )
    })

    it('should return error for passwords with only 2 character types', () => {
      expect(validatePassword('lowercase123')).toBe(
        'Password must contain at least 3 of: lowercase, uppercase, numbers, special characters'
      )
      expect(validatePassword('UPPERCASE123')).toBe(
        'Password must contain at least 3 of: lowercase, uppercase, numbers, special characters'
      )
      expect(validatePassword('lowercaseUPPER')).toBe(
        'Password must contain at least 3 of: lowercase, uppercase, numbers, special characters'
      )
    })
  })

  describe('invalid passwords - common passwords', () => {
    it('should check common passwords list (unreachable with current list)', () => {
      // NOTE: ALL passwords in current COMMON_PASSWORDS list are < 12 characters!
      // The common password check happens AFTER length check,
      // so it's effectively unreachable with the current list.
      //
      // Longest password in list: "password123" (11 chars)
      // All others are shorter (8 chars or less)

      // Example: "password123" is in the list but only 11 chars
      expect(validatePassword('password123')).toBe(
        'Password must be at least 12 characters'
      )

      // If we pad it to 12 chars, it's no longer in the list
      expect(validatePassword('password1234')).toBe(
        'Password must contain at least 3 of: lowercase, uppercase, numbers, special characters'
      )

      // If we make it pass all checks, it's not in the list anymore
      expect(validatePassword('Password123!')).toBeNull()
    })

    it('should perform case-insensitive check against common passwords', () => {
      // The check uses .toLowerCase() so case variations of listed passwords
      // would be caught IF they passed length and complexity checks first.
      //
      // Current behavior: all common passwords fail length check first
      expect(validatePassword('password123')).toBe('Password must be at least 12 characters')
      expect(validatePassword('PASSWORD123')).toBe('Password must be at least 12 characters')
      expect(validatePassword('Password123')).toBe('Password must be at least 12 characters')
    })

    it('should check common passwords after length and complexity', () => {
      // Common password check is the LAST check (after length, complexity)
      // This means all current common passwords fail earlier checks first

      // All passwords in COMMON_PASSWORDS are < 12 chars
      const commonPasswords = [
        'password',    // 8 chars
        'password123', // 11 chars
        '12345678',    // 8 chars
        'admin',       // 5 chars
      ]

      commonPasswords.forEach((pwd) => {
        expect(validatePassword(pwd)).toBe('Password must be at least 12 characters')
      })
    })
  })
})

// ============================================================================
// validateMinLength Tests
// ============================================================================

describe('validateMinLength', () => {
  describe('valid inputs', () => {
    it('should return null for strings meeting minimum length', () => {
      expect(validateMinLength('John Doe', 3, 'Name')).toBeNull()
      expect(validateMinLength('test', 4, 'Username')).toBeNull()
      expect(validateMinLength('exactly', 7, 'Field')).toBeNull()
    })

    it('should return null for empty strings', () => {
      expect(validateMinLength('', 5, 'Field')).toBeNull()
    })

    it('should trim whitespace before checking length', () => {
      expect(validateMinLength('  abc  ', 3, 'Field')).toBeNull()
      expect(validateMinLength('  abcd  ', 4, 'Field')).toBeNull()
    })

    it('should handle very long strings', () => {
      const longString = 'a'.repeat(1000)
      expect(validateMinLength(longString, 500, 'Field')).toBeNull()
    })
  })

  describe('invalid inputs', () => {
    it('should return error for strings below minimum length', () => {
      expect(validateMinLength('Jo', 3, 'Name')).toBe('Name must be at least 3 characters')
      expect(validateMinLength('ab', 5, 'Username')).toBe(
        'Username must be at least 5 characters'
      )
    })

    it('should use field name in error message', () => {
      expect(validateMinLength('a', 10, 'Description')).toBe(
        'Description must be at least 10 characters'
      )
      expect(validateMinLength('ab', 20, 'Comment')).toBe(
        'Comment must be at least 20 characters'
      )
    })

    it('should count trimmed length', () => {
      expect(validateMinLength('  ab  ', 5, 'Field')).toBe(
        'Field must be at least 5 characters'
      )
      expect(validateMinLength('\t\ttest\t\t', 10, 'Field')).toBe(
        'Field must be at least 10 characters'
      )
    })

    it('should handle edge case of exactly one character short', () => {
      expect(validateMinLength('abcd', 5, 'Field')).toBe(
        'Field must be at least 5 characters'
      )
    })
  })

  describe('boundary conditions', () => {
    it('should accept string exactly at minimum length', () => {
      expect(validateMinLength('abc', 3, 'Field')).toBeNull()
      expect(validateMinLength('12345', 5, 'Field')).toBeNull()
    })

    it('should handle minimum length of 1', () => {
      expect(validateMinLength('a', 1, 'Field')).toBeNull()
      expect(validateMinLength('', 1, 'Field')).toBeNull()
    })

    it('should handle minimum length of 0', () => {
      expect(validateMinLength('', 0, 'Field')).toBeNull()
      expect(validateMinLength('anything', 0, 'Field')).toBeNull()
    })
  })
})

// ============================================================================
// validatePgyLevel Tests
// ============================================================================

describe('validatePgyLevel', () => {
  describe('valid PGY levels', () => {
    it('should return null for valid PGY levels as numbers', () => {
      const validLevels = [1, 2, 3, 4, 5, 6, 7, 8]
      validLevels.forEach((level) => {
        expect(validatePgyLevel(level)).toBeNull()
      })
    })

    it('should return null for valid PGY levels as strings', () => {
      const validLevels = ['1', '2', '3', '4', '5', '6', '7', '8']
      validLevels.forEach((level) => {
        expect(validatePgyLevel(level)).toBeNull()
      })
    })

    it('should handle PGY-1 (intern)', () => {
      expect(validatePgyLevel(1)).toBeNull()
      expect(validatePgyLevel('1')).toBeNull()
    })

    it('should handle PGY-8 (extended programs)', () => {
      expect(validatePgyLevel(8)).toBeNull()
      expect(validatePgyLevel('8')).toBeNull()
    })
  })

  describe('invalid PGY levels - out of range', () => {
    it('should return error for PGY levels below 1', () => {
      expect(validatePgyLevel(0)).toBe('PGY level must be between 1 and 8')
      expect(validatePgyLevel(-1)).toBe('PGY level must be between 1 and 8')
      expect(validatePgyLevel(-10)).toBe('PGY level must be between 1 and 8')
    })

    it('should return error for PGY levels above 8', () => {
      expect(validatePgyLevel(9)).toBe('PGY level must be between 1 and 8')
      expect(validatePgyLevel(10)).toBe('PGY level must be between 1 and 8')
      expect(validatePgyLevel(100)).toBe('PGY level must be between 1 and 8')
    })

    it('should return error for out of range string values', () => {
      expect(validatePgyLevel('0')).toBe('PGY level must be between 1 and 8')
      expect(validatePgyLevel('9')).toBe('PGY level must be between 1 and 8')
      expect(validatePgyLevel('15')).toBe('PGY level must be between 1 and 8')
    })
  })

  describe('invalid PGY levels - non-numeric', () => {
    it('should return error for non-numeric strings', () => {
      expect(validatePgyLevel('abc')).toBe('PGY level must be a number')
      expect(validatePgyLevel('PGY-1')).toBe('PGY level must be a number')
      expect(validatePgyLevel('first')).toBe('PGY level must be a number')
    })

    it('should return error for empty string', () => {
      expect(validatePgyLevel('')).toBe('PGY level must be a number')
    })

    it('should handle strings with spaces (parseInt behavior)', () => {
      // parseInt trims leading/trailing whitespace and parses successfully
      expect(validatePgyLevel('1 ')).toBeNull() // parseInt('1 ') = 1
      expect(validatePgyLevel(' 1')).toBeNull() // parseInt(' 1') = 1
    })

    it('should handle decimal numbers (parseInt truncates)', () => {
      // parseInt truncates decimals to integers
      expect(validatePgyLevel(1.5)).toBeNull() // parseInt(1.5) = 1
      expect(validatePgyLevel('2.5')).toBeNull() // parseInt('2.5') = 2
      // But out of range decimals still fail
      expect(validatePgyLevel(9.5)).toBe('PGY level must be between 1 and 8')
      expect(validatePgyLevel('10.5')).toBe('PGY level must be between 1 and 8')
    })

    it('should return error for special characters', () => {
      expect(validatePgyLevel('!')).toBe('PGY level must be a number')
      expect(validatePgyLevel('@')).toBe('PGY level must be a number')
    })
  })

  describe('edge cases', () => {
    it('should handle string numbers with leading zeros', () => {
      expect(validatePgyLevel('01')).toBeNull()
      expect(validatePgyLevel('003')).toBeNull()
    })

    it('should handle positive infinity', () => {
      expect(validatePgyLevel(Infinity)).toBe('PGY level must be between 1 and 8')
    })

    it('should handle negative infinity', () => {
      expect(validatePgyLevel(-Infinity)).toBe('PGY level must be between 1 and 8')
    })

    it('should handle very large numbers', () => {
      expect(validatePgyLevel(999999)).toBe('PGY level must be between 1 and 8')
    })
  })
})

// ============================================================================
// ValidationResult Interface Tests (indirectly tested)
// ============================================================================

describe('ValidationResult type', () => {
  it('should support ValidationResult structure', () => {
    const result: ValidationResult = {
      valid: true,
      errors: {},
    }
    expect(result.valid).toBe(true)
    expect(result.errors).toEqual({})
  })

  it('should support ValidationResult with errors', () => {
    const result: ValidationResult = {
      valid: false,
      errors: {
        email: 'Please enter a valid email address',
        password: 'Password must be at least 12 characters',
      },
    }
    expect(result.valid).toBe(false)
    expect(result.errors.email).toBe('Please enter a valid email address')
    expect(result.errors.password).toBe('Password must be at least 12 characters')
  })

  it('should allow dynamic field names in errors', () => {
    const result: ValidationResult = {
      valid: false,
      errors: {},
    }

    result.errors['dynamicField'] = 'Error message'
    expect(result.errors.dynamicField).toBe('Error message')
  })
})

// ============================================================================
// Integration Tests - Combining Multiple Validators
// ============================================================================

describe('Multiple Validator Integration', () => {
  it('should validate a complete registration form', () => {
    const formData = {
      email: 'user@example.com',
      password: 'MyS3cure!Pass',
      name: 'John Doe',
      pgyLevel: '2',
    }

    const errors: Record<string, string> = {}

    const emailError = validateEmail(formData.email)
    if (emailError) errors.email = emailError

    const passwordError = validatePassword(formData.password)
    if (passwordError) errors.password = passwordError

    const nameError = validateRequired(formData.name, 'Name')
    if (nameError) errors.name = nameError

    const pgyError = validatePgyLevel(formData.pgyLevel)
    if (pgyError) errors.pgyLevel = pgyError

    expect(Object.keys(errors).length).toBe(0)
  })

  it('should collect multiple validation errors', () => {
    const formData = {
      email: 'invalid-email',
      password: 'short',
      name: '',
      pgyLevel: '10',
    }

    const errors: Record<string, string> = {}

    const emailError = validateEmail(formData.email)
    if (emailError) errors.email = emailError

    const passwordError = validatePassword(formData.password)
    if (passwordError) errors.password = passwordError

    const nameError = validateRequired(formData.name, 'Name')
    if (nameError) errors.name = nameError

    const pgyError = validatePgyLevel(formData.pgyLevel)
    if (pgyError) errors.pgyLevel = pgyError

    expect(Object.keys(errors).length).toBe(4)
    expect(errors.email).toBeDefined()
    expect(errors.password).toBeDefined()
    expect(errors.name).toBeDefined()
    expect(errors.pgyLevel).toBeDefined()
  })

  it('should validate schedule date range', () => {
    const startDate = '2024-01-01'
    const endDate = '2024-12-31'

    const errors: Record<string, string> = {}

    const startError = validateRequired(startDate, 'Start Date')
    if (startError) errors.startDate = startError

    const endError = validateRequired(endDate, 'End Date')
    if (endError) errors.endDate = endError

    const rangeError = validateDateRange(startDate, endDate)
    if (rangeError) errors.dateRange = rangeError

    expect(Object.keys(errors).length).toBe(0)
  })

  it('should validate with minimum length and required', () => {
    const description = 'Test desc'

    const errors: Record<string, string> = {}

    const requiredError = validateRequired(description, 'Description')
    if (requiredError) errors.description = requiredError

    const lengthError = validateMinLength(description, 5, 'Description')
    if (lengthError) errors.description = lengthError

    expect(Object.keys(errors).length).toBe(0)
  })
})
