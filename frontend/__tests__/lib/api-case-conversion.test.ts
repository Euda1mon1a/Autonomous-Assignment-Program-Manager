/**
 * Tests for API case conversion utilities
 *
 * The axios interceptor in frontend/src/lib/api.ts converts:
 * - Request: camelCase → snake_case (before sending to backend)
 * - Response: snake_case → camelCase (after receiving from backend)
 *
 * These tests ensure the conversion logic works correctly.
 * See: Session 079, 080 for context on why this is critical.
 */

// Note: The conversion functions are not exported from api.ts
// We recreate them here for testing. In a future refactor, consider
// exporting them from a shared utility module.

function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

function keysToSnakeCase(obj: unknown): unknown {
  if (Array.isArray(obj)) {
    return obj.map(keysToSnakeCase);
  }
  if (obj !== null && typeof obj === 'object' && !(obj instanceof Date)) {
    return Object.fromEntries(
      Object.entries(obj).map(([key, value]) => [
        toSnakeCase(key),
        keysToSnakeCase(value),
      ])
    );
  }
  return obj;
}

function keysToCamelCase(obj: unknown): unknown {
  if (Array.isArray(obj)) {
    return obj.map(keysToCamelCase);
  }
  if (obj !== null && typeof obj === 'object' && !(obj instanceof Date)) {
    return Object.fromEntries(
      Object.entries(obj).map(([key, value]) => [
        toCamelCase(key),
        keysToCamelCase(value),
      ])
    );
  }
  return obj;
}

describe('Case Conversion Utilities', () => {
  describe('toSnakeCase', () => {
    it('converts camelCase to snake_case', () => {
      expect(toSnakeCase('dayOfWeek')).toBe('day_of_week');
      expect(toSnakeCase('personId')).toBe('person_id');
      expect(toSnakeCase('createdAt')).toBe('created_at');
    });

    it('handles single words', () => {
      expect(toSnakeCase('name')).toBe('name');
      expect(toSnakeCase('id')).toBe('id');
    });

    it('handles consecutive capitals', () => {
      expect(toSnakeCase('userID')).toBe('user_i_d');
      expect(toSnakeCase('getHTTPResponse')).toBe('get_h_t_t_p_response');
    });

    it('handles empty string', () => {
      expect(toSnakeCase('')).toBe('');
    });
  });

  describe('toCamelCase', () => {
    it('converts snake_case to camelCase', () => {
      expect(toCamelCase('day_of_week')).toBe('dayOfWeek');
      expect(toCamelCase('person_id')).toBe('personId');
      expect(toCamelCase('created_at')).toBe('createdAt');
    });

    it('handles single words', () => {
      expect(toCamelCase('name')).toBe('name');
      expect(toCamelCase('id')).toBe('id');
    });

    it('handles multiple underscores', () => {
      expect(toCamelCase('very_long_property_name')).toBe('veryLongPropertyName');
    });

    it('handles empty string', () => {
      expect(toCamelCase('')).toBe('');
    });

    it('converts leading underscore followed by letter', () => {
      // Note: current implementation converts _[a-z] to uppercase letter
      // This is a known behavior - leading underscores are NOT preserved
      expect(toCamelCase('_private')).toBe('Private');
    });
  });

  describe('keysToSnakeCase', () => {
    it('converts object keys from camelCase to snake_case', () => {
      const input = { personId: '123', createdAt: '2024-01-01' };
      const expected = { person_id: '123', created_at: '2024-01-01' };
      expect(keysToSnakeCase(input)).toEqual(expected);
    });

    it('handles nested objects', () => {
      const input = {
        userData: {
          firstName: 'John',
          lastName: 'Doe',
        },
      };
      const expected = {
        user_data: {
          first_name: 'John',
          last_name: 'Doe',
        },
      };
      expect(keysToSnakeCase(input)).toEqual(expected);
    });

    it('handles arrays of objects', () => {
      const input = [
        { personId: '1', pgyLevel: 2 },
        { personId: '2', pgyLevel: 3 },
      ];
      const expected = [
        { person_id: '1', pgy_level: 2 },
        { person_id: '2', pgy_level: 3 },
      ];
      expect(keysToSnakeCase(input)).toEqual(expected);
    });

    it('preserves Date objects', () => {
      const date = new Date('2024-01-01');
      const input = { createdAt: date };
      const result = keysToSnakeCase(input) as { created_at: Date };
      expect(result.created_at).toBe(date);
      expect(result.created_at instanceof Date).toBe(true);
    });

    it('handles null and undefined', () => {
      expect(keysToSnakeCase(null)).toBe(null);
      expect(keysToSnakeCase(undefined)).toBe(undefined);
    });

    it('handles primitive values', () => {
      expect(keysToSnakeCase('string')).toBe('string');
      expect(keysToSnakeCase(123)).toBe(123);
      expect(keysToSnakeCase(true)).toBe(true);
    });

    it('handles empty objects and arrays', () => {
      expect(keysToSnakeCase({})).toEqual({});
      expect(keysToSnakeCase([])).toEqual([]);
    });
  });

  describe('keysToCamelCase', () => {
    it('converts object keys from snake_case to camelCase', () => {
      const input = { person_id: '123', created_at: '2024-01-01' };
      const expected = { personId: '123', createdAt: '2024-01-01' };
      expect(keysToCamelCase(input)).toEqual(expected);
    });

    it('handles nested objects', () => {
      const input = {
        user_data: {
          first_name: 'John',
          last_name: 'Doe',
        },
      };
      const expected = {
        userData: {
          firstName: 'John',
          lastName: 'Doe',
        },
      };
      expect(keysToCamelCase(input)).toEqual(expected);
    });

    it('handles arrays of objects', () => {
      const input = [
        { person_id: '1', pgy_level: 2 },
        { person_id: '2', pgy_level: 3 },
      ];
      const expected = [
        { personId: '1', pgyLevel: 2 },
        { personId: '2', pgyLevel: 3 },
      ];
      expect(keysToCamelCase(input)).toEqual(expected);
    });

    it('preserves Date objects', () => {
      const date = new Date('2024-01-01');
      const input = { created_at: date };
      const result = keysToCamelCase(input) as { createdAt: Date };
      expect(result.createdAt).toBe(date);
      expect(result.createdAt instanceof Date).toBe(true);
    });

    it('handles deeply nested structures', () => {
      const input = {
        outer_key: {
          inner_key: {
            deep_key: {
              value_here: 'found',
            },
          },
        },
      };
      const expected = {
        outerKey: {
          innerKey: {
            deepKey: {
              valueHere: 'found',
            },
          },
        },
      };
      expect(keysToCamelCase(input)).toEqual(expected);
    });

    it('handles mixed arrays with objects and primitives', () => {
      const input = [
        { person_id: '1' },
        'string_value',
        123,
        null,
        { another_key: 'value' },
      ];
      const expected = [
        { personId: '1' },
        'string_value', // strings are not converted
        123,
        null,
        { anotherKey: 'value' },
      ];
      expect(keysToCamelCase(input)).toEqual(expected);
    });
  });

  describe('Round-trip conversion', () => {
    it('camelCase → snake_case → camelCase returns original', () => {
      const original = {
        personId: '123',
        userData: {
          firstName: 'John',
          pgyLevel: 2,
        },
        items: [{ itemId: 'a' }, { itemId: 'b' }],
      };
      const snakeCase = keysToSnakeCase(original);
      const backToCamel = keysToCamelCase(snakeCase);
      expect(backToCamel).toEqual(original);
    });

    it('snake_case → camelCase → snake_case returns original', () => {
      const original = {
        person_id: '123',
        user_data: {
          first_name: 'John',
          pgy_level: 2,
        },
        items: [{ item_id: 'a' }, { item_id: 'b' }],
      };
      const camelCase = keysToCamelCase(original);
      const backToSnake = keysToSnakeCase(camelCase);
      expect(backToSnake).toEqual(original);
    });
  });
});
