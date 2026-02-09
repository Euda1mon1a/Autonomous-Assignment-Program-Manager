import {
  personTypeSchema,
  facultyRoleSchema,
  pgyLevelSchema,
  personBaseSchema,
  personUpdateSchema,
  assignmentRoleSchema,
  assignmentBaseSchema,
  blockSessionSchema,
  blockBaseSchema,
  swapTypeSchema,
  swapStatusSchema,
  swapRequestSchema,
  dateRangeFilterSchema,
  paginationParamsSchema,
  sortOrderSchema,
  sortParamsSchema,
  emailSchema,
  phoneSchema,
  passwordSchema,
  dateStringSchema,
} from '../schemas';

// ==================== Enum Schemas ====================

describe('personTypeSchema', () => {
  it('accepts "resident"', () => {
    expect(personTypeSchema.safeParse('resident').success).toBe(true);
  });

  it('accepts "faculty"', () => {
    expect(personTypeSchema.safeParse('faculty').success).toBe(true);
  });

  it('rejects invalid type', () => {
    expect(personTypeSchema.safeParse('student').success).toBe(false);
  });

  it('rejects empty string', () => {
    expect(personTypeSchema.safeParse('').success).toBe(false);
  });
});

describe('facultyRoleSchema', () => {
  const validRoles = ['pd', 'apd', 'oic', 'dept_chief', 'sports_med', 'core', 'adjunct'];

  it.each(validRoles)('accepts "%s"', (role) => {
    expect(facultyRoleSchema.safeParse(role).success).toBe(true);
  });

  it('rejects invalid role', () => {
    expect(facultyRoleSchema.safeParse('attending').success).toBe(false);
  });
});

describe('pgyLevelSchema', () => {
  it('accepts PGY 1', () => {
    expect(pgyLevelSchema.safeParse(1).success).toBe(true);
  });

  it('accepts PGY 3', () => {
    expect(pgyLevelSchema.safeParse(3).success).toBe(true);
  });

  it('rejects PGY 0', () => {
    expect(pgyLevelSchema.safeParse(0).success).toBe(false);
  });

  it('rejects PGY 4', () => {
    expect(pgyLevelSchema.safeParse(4).success).toBe(false);
  });

  it('rejects float', () => {
    expect(pgyLevelSchema.safeParse(1.5).success).toBe(false);
  });

  it('rejects string', () => {
    expect(pgyLevelSchema.safeParse('2').success).toBe(false);
  });
});

describe('assignmentRoleSchema', () => {
  it.each(['primary', 'supervising', 'backup'])('accepts "%s"', (role) => {
    expect(assignmentRoleSchema.safeParse(role).success).toBe(true);
  });

  it('rejects invalid role', () => {
    expect(assignmentRoleSchema.safeParse('observer').success).toBe(false);
  });
});

describe('blockSessionSchema', () => {
  it('accepts "AM"', () => {
    expect(blockSessionSchema.safeParse('AM').success).toBe(true);
  });

  it('accepts "PM"', () => {
    expect(blockSessionSchema.safeParse('PM').success).toBe(true);
  });

  it('rejects lowercase "am"', () => {
    expect(blockSessionSchema.safeParse('am').success).toBe(false);
  });
});

describe('swapTypeSchema', () => {
  it.each(['one_to_one', 'absorb', 'multi_way'])('accepts "%s"', (type) => {
    expect(swapTypeSchema.safeParse(type).success).toBe(true);
  });

  it('rejects camelCase (oneToOne)', () => {
    expect(swapTypeSchema.safeParse('oneToOne').success).toBe(false);
  });
});

describe('swapStatusSchema', () => {
  const statuses = ['pending', 'approved', 'executed', 'rejected', 'cancelled', 'rolled_back'];

  it.each(statuses)('accepts "%s"', (status) => {
    expect(swapStatusSchema.safeParse(status).success).toBe(true);
  });

  it('rejects camelCase (rolledBack)', () => {
    expect(swapStatusSchema.safeParse('rolledBack').success).toBe(false);
  });
});

describe('sortOrderSchema', () => {
  it('accepts "asc"', () => {
    expect(sortOrderSchema.safeParse('asc').success).toBe(true);
  });

  it('accepts "desc"', () => {
    expect(sortOrderSchema.safeParse('desc').success).toBe(true);
  });

  it('rejects "ASC"', () => {
    expect(sortOrderSchema.safeParse('ASC').success).toBe(false);
  });
});

// ==================== Object Schemas ====================

describe('personBaseSchema', () => {
  const validPerson = {
    name: 'Jane Doe',
    type: 'resident' as const,
  };

  it('accepts minimal valid person', () => {
    expect(personBaseSchema.safeParse(validPerson).success).toBe(true);
  });

  it('accepts person with all optional fields', () => {
    const full = {
      ...validPerson,
      email: 'jane@hospital.org',
      pgyLevel: 2,
      performsProcedures: true,
      specialties: ['sports'],
      primaryDuty: 'FM Clinic',
      facultyRole: 'core',
    };
    expect(personBaseSchema.safeParse(full).success).toBe(true);
  });

  it('rejects name shorter than 2 chars', () => {
    const result = personBaseSchema.safeParse({ ...validPerson, name: 'J' });
    expect(result.success).toBe(false);
  });

  it('rejects missing name', () => {
    const { name, ...rest } = validPerson;
    expect(personBaseSchema.safeParse(rest).success).toBe(false);
  });

  it('rejects missing type', () => {
    const { type, ...rest } = validPerson;
    expect(personBaseSchema.safeParse(rest).success).toBe(false);
  });

  it('rejects invalid email format', () => {
    const result = personBaseSchema.safeParse({ ...validPerson, email: 'not-an-email' });
    expect(result.success).toBe(false);
  });

  it('accepts null email', () => {
    const result = personBaseSchema.safeParse({ ...validPerson, email: null });
    expect(result.success).toBe(true);
  });
});

describe('personUpdateSchema', () => {
  it('accepts partial updates', () => {
    expect(personUpdateSchema.safeParse({ name: 'Updated' }).success).toBe(true);
  });

  it('accepts empty object', () => {
    expect(personUpdateSchema.safeParse({}).success).toBe(true);
  });
});

describe('assignmentBaseSchema', () => {
  const validUuid = '550e8400-e29b-41d4-a716-446655440000';

  const validAssignment = {
    blockId: validUuid,
    personId: validUuid,
    role: 'primary' as const,
  };

  it('accepts valid assignment', () => {
    expect(assignmentBaseSchema.safeParse(validAssignment).success).toBe(true);
  });

  it('rejects non-UUID blockId', () => {
    const result = assignmentBaseSchema.safeParse({ ...validAssignment, blockId: 'not-uuid' });
    expect(result.success).toBe(false);
  });

  it('rejects non-UUID personId', () => {
    const result = assignmentBaseSchema.safeParse({ ...validAssignment, personId: '123' });
    expect(result.success).toBe(false);
  });

  it('accepts optional notes', () => {
    const result = assignmentBaseSchema.safeParse({
      ...validAssignment,
      notes: 'Covering for leave',
    });
    expect(result.success).toBe(true);
  });

  it('rejects notes over 1000 chars', () => {
    const result = assignmentBaseSchema.safeParse({
      ...validAssignment,
      notes: 'x'.repeat(1001),
    });
    expect(result.success).toBe(false);
  });
});

describe('blockBaseSchema', () => {
  it('accepts valid date + session', () => {
    expect(blockBaseSchema.safeParse({ date: '2025-06-15', session: 'AM' }).success).toBe(true);
  });

  it('rejects invalid date format', () => {
    expect(blockBaseSchema.safeParse({ date: '06/15/2025', session: 'AM' }).success).toBe(false);
  });

  it('rejects date with no dashes', () => {
    expect(blockBaseSchema.safeParse({ date: '20250615', session: 'AM' }).success).toBe(false);
  });

  it('rejects missing session', () => {
    expect(blockBaseSchema.safeParse({ date: '2025-06-15' }).success).toBe(false);
  });
});

describe('swapRequestSchema', () => {
  const validUuid = '550e8400-e29b-41d4-a716-446655440000';

  const validSwap = {
    requester_id: validUuid,
    requester_assignmentId: validUuid,
    swapType: 'one_to_one' as const,
    reason: 'Need to attend mandatory training session',
  };

  it('accepts valid swap request', () => {
    expect(swapRequestSchema.safeParse(validSwap).success).toBe(true);
  });

  it('rejects reason shorter than 10 chars', () => {
    const result = swapRequestSchema.safeParse({ ...validSwap, reason: 'Short' });
    expect(result.success).toBe(false);
  });

  it('rejects reason over 500 chars', () => {
    const result = swapRequestSchema.safeParse({ ...validSwap, reason: 'x'.repeat(501) });
    expect(result.success).toBe(false);
  });

  it('accepts optional target fields', () => {
    const result = swapRequestSchema.safeParse({
      ...validSwap,
      target_id: validUuid,
      target_assignmentId: validUuid,
    });
    expect(result.success).toBe(true);
  });

  it('accepts null target fields', () => {
    const result = swapRequestSchema.safeParse({
      ...validSwap,
      target_id: null,
      target_assignmentId: null,
    });
    expect(result.success).toBe(true);
  });
});

// ==================== Filter & Pagination Schemas ====================

describe('dateRangeFilterSchema', () => {
  it('accepts valid range', () => {
    const result = dateRangeFilterSchema.safeParse({
      startDate: '2025-01-01',
      endDate: '2025-12-31',
    });
    expect(result.success).toBe(true);
  });

  it('accepts empty object', () => {
    expect(dateRangeFilterSchema.safeParse({}).success).toBe(true);
  });

  it('rejects invalid date format', () => {
    const result = dateRangeFilterSchema.safeParse({ startDate: '01-01-2025' });
    expect(result.success).toBe(false);
  });
});

describe('paginationParamsSchema', () => {
  it('applies defaults', () => {
    const result = paginationParamsSchema.parse({});
    expect(result.page).toBe(1);
    expect(result.pageSize).toBe(50);
  });

  it('accepts custom values', () => {
    const result = paginationParamsSchema.parse({ page: 3, pageSize: 100 });
    expect(result.page).toBe(3);
    expect(result.pageSize).toBe(100);
  });

  it('rejects page 0', () => {
    expect(paginationParamsSchema.safeParse({ page: 0 }).success).toBe(false);
  });

  it('rejects pageSize over 1000', () => {
    expect(paginationParamsSchema.safeParse({ pageSize: 1001 }).success).toBe(false);
  });
});

describe('sortParamsSchema', () => {
  it('accepts valid sort', () => {
    const result = sortParamsSchema.parse({ sort_by: 'name' });
    expect(result.sort_order).toBe('asc');
  });

  it('accepts desc order', () => {
    const result = sortParamsSchema.parse({ sort_by: 'date', sort_order: 'desc' });
    expect(result.sort_order).toBe('desc');
  });

  it('rejects missing sort_by', () => {
    expect(sortParamsSchema.safeParse({}).success).toBe(false);
  });
});

// ==================== Form Field Schemas ====================

describe('emailSchema', () => {
  it('accepts valid email', () => {
    expect(emailSchema.safeParse('user@hospital.org').success).toBe(true);
  });

  it('rejects empty string', () => {
    expect(emailSchema.safeParse('').success).toBe(false);
  });

  it('rejects no @', () => {
    expect(emailSchema.safeParse('invalid-email').success).toBe(false);
  });
});

describe('phoneSchema', () => {
  it('accepts digits with dashes', () => {
    expect(phoneSchema.safeParse('808-555-1234').success).toBe(true);
  });

  it('accepts digits with parens', () => {
    expect(phoneSchema.safeParse('(808) 555-1234').success).toBe(true);
  });

  it('accepts empty string', () => {
    expect(phoneSchema.safeParse('').success).toBe(true);
  });

  it('rejects letters', () => {
    expect(phoneSchema.safeParse('call me').success).toBe(false);
  });
});

describe('passwordSchema', () => {
  it('accepts strong password', () => {
    expect(passwordSchema.safeParse('MyStr0ng!Pass').success).toBe(true);
  });

  it('rejects short password', () => {
    const result = passwordSchema.safeParse('Short!1');
    expect(result.success).toBe(false);
  });

  it('rejects no uppercase', () => {
    expect(passwordSchema.safeParse('lowercaseonly1!x').success).toBe(false);
  });

  it('rejects no lowercase', () => {
    expect(passwordSchema.safeParse('UPPERCASEONLY1!X').success).toBe(false);
  });

  it('rejects no digit', () => {
    expect(passwordSchema.safeParse('NoDigitsHere!!!x').success).toBe(false);
  });

  it('rejects no special char', () => {
    expect(passwordSchema.safeParse('NoSpecials12345').success).toBe(false);
  });
});

describe('dateStringSchema', () => {
  it('accepts YYYY-MM-DD', () => {
    expect(dateStringSchema.safeParse('2025-06-15').success).toBe(true);
  });

  it('rejects MM/DD/YYYY', () => {
    expect(dateStringSchema.safeParse('06/15/2025').success).toBe(false);
  });

  it('rejects incomplete date', () => {
    expect(dateStringSchema.safeParse('2025-06').success).toBe(false);
  });
});
