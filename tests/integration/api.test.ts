/**
 * Comprehensive API Integration Tests
 *
 * Tests all API endpoints including auth, people, schedule, blocks,
 * absences, assignments, and exports.
 *
 * Tests cover:
 * - Success cases
 * - Error cases (401 unauthorized, 404 not found, 400 validation)
 * - Edge cases and boundary conditions
 * - ACGME compliance validation
 */

import {
  ApiClient,
  TestDatabase,
  TestContext,
  setupTestEnvironment,
  teardownTestEnvironment,
  TEST_USERS,
  FIXTURE_RESIDENTS,
  FIXTURE_FACULTY,
  assertSuccessResponse,
  assertErrorResponse,
  assertUnauthorized,
  assertNotFound,
  assertValidationError,
  assertForbidden,
  isValidUUID,
  formatDate,
  addDays,
  generateBlockFixtures,
  createAbsenceFixture,
  TEST_TIMEOUT,
} from './setup';

// ============================================================================
// Test Suite Setup
// ============================================================================

describe('API Integration Tests', () => {
  let context: TestContext;
  let client: ApiClient;
  let db: TestDatabase;

  beforeAll(async () => {
    context = await setupTestEnvironment();
    client = context.client;
    db = context.db;
  }, TEST_TIMEOUT);

  afterAll(async () => {
    await teardownTestEnvironment(context);
  }, TEST_TIMEOUT);

  // ============================================================================
  // Authentication Endpoints
  // ============================================================================

  describe('Auth Endpoints', () => {
    describe('POST /auth/register', () => {
      it('should register the first user as admin', async () => {
        const response = await client.register(TEST_USERS.admin);

        assertSuccessResponse(response, 201);
        expect(response.data).toHaveProperty('id');
        expect(response.data).toHaveProperty('username', TEST_USERS.admin.username);
        expect(response.data).toHaveProperty('email', TEST_USERS.admin.email);
        expect(response.data).toHaveProperty('role', 'admin');
        expect(response.data).not.toHaveProperty('password');
        expect(response.data).not.toHaveProperty('hashed_password');
        expect(isValidUUID(response.data.id)).toBe(true);
      });

      it('should not register duplicate username', async () => {
        const duplicateUser = { ...TEST_USERS.admin, email: 'different@test.com' };
        const response = await client.register(duplicateUser);

        assertErrorResponse(response, 400, 'Username already registered');
      });

      it('should require admin to create additional users', async () => {
        // Try to register without authentication
        const newClient = new ApiClient();
        const response = await newClient.register(TEST_USERS.coordinator);

        assertForbidden(response);
      });

      it('should validate email format', async () => {
        await client.login(TEST_USERS.admin.username, TEST_USERS.admin.password);

        const invalidUser = {
          username: 'testuser',
          email: 'invalid-email',
          password: 'TestPass123!',
        };
        const response = await client.register(invalidUser);

        expect(response.status).toBeGreaterThanOrEqual(400);
      });
    });

    describe('POST /auth/login/json', () => {
      it('should login with valid credentials', async () => {
        const response = await client.login(TEST_USERS.admin.username, TEST_USERS.admin.password);

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('access_token');
        expect(response.data).toHaveProperty('token_type', 'bearer');
        expect(typeof response.data.access_token).toBe('string');
        expect(response.data.access_token.length).toBeGreaterThan(0);
      });

      it('should reject invalid username', async () => {
        const newClient = new ApiClient();
        const response = await newClient.login('nonexistent', 'password');

        assertUnauthorized(response);
        expect(response.data.detail).toContain('Incorrect username or password');
      });

      it('should reject invalid password', async () => {
        const newClient = new ApiClient();
        const response = await newClient.login(TEST_USERS.admin.username, 'wrongpassword');

        assertUnauthorized(response);
        expect(response.data.detail).toContain('Incorrect username or password');
      });

      it('should reject empty credentials', async () => {
        const newClient = new ApiClient();
        const response = await newClient.post('/auth/login/json', {
          username: '',
          password: '',
        });

        expect(response.status).toBeGreaterThanOrEqual(400);
      });
    });

    describe('GET /auth/me', () => {
      it('should return current user info when authenticated', async () => {
        await client.login(TEST_USERS.admin.username, TEST_USERS.admin.password);
        const response = await client.getCurrentUser();

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('username', TEST_USERS.admin.username);
        expect(response.data).toHaveProperty('email', TEST_USERS.admin.email);
        expect(response.data).toHaveProperty('role');
        expect(response.data).not.toHaveProperty('password');
      });

      it('should return 401 when not authenticated', async () => {
        const newClient = new ApiClient();
        const response = await newClient.getCurrentUser();

        assertUnauthorized(response);
      });
    });

    describe('POST /auth/logout', () => {
      it('should logout successfully when authenticated', async () => {
        await client.login(TEST_USERS.admin.username, TEST_USERS.admin.password);
        const response = await client.logout();

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('message');
      });

      it('should return 401 when not authenticated', async () => {
        const newClient = new ApiClient();
        const response = await newClient.post('/auth/logout');

        assertUnauthorized(response);
      });
    });
  });

  // ============================================================================
  // People Endpoints
  // ============================================================================

  describe('People Endpoints', () => {
    beforeAll(async () => {
      // Ensure we're authenticated for people tests
      await client.login(TEST_USERS.admin.username, TEST_USERS.admin.password);
    });

    describe('POST /api/people', () => {
      it('should create a resident with valid data', async () => {
        const residentData = FIXTURE_RESIDENTS[0];
        const response = await client.post('/people', residentData);

        assertSuccessResponse(response, 201);
        expect(response.data).toHaveProperty('id');
        expect(response.data).toHaveProperty('name', residentData.name);
        expect(response.data).toHaveProperty('type', 'resident');
        expect(response.data).toHaveProperty('pgy_level', residentData.pgy_level);
        expect(isValidUUID(response.data.id)).toBe(true);
      });

      it('should create a faculty member with valid data', async () => {
        const facultyData = FIXTURE_FACULTY[0];
        const response = await client.post('/people', facultyData);

        assertSuccessResponse(response, 201);
        expect(response.data).toHaveProperty('id');
        expect(response.data).toHaveProperty('name', facultyData.name);
        expect(response.data).toHaveProperty('type', 'faculty');
        expect(response.data).toHaveProperty('performs_procedures', facultyData.performs_procedures);
        expect(response.data).toHaveProperty('specialties');
      });

      it('should require authentication', async () => {
        const newClient = new ApiClient();
        const response = await newClient.post('/people', FIXTURE_RESIDENTS[1]);

        assertUnauthorized(response);
      });

      it('should require PGY level for residents', async () => {
        const invalidResident = {
          name: 'Dr. Invalid Resident',
          type: 'resident',
          email: 'invalid@test.com',
          // Missing pgy_level
        };
        const response = await client.post('/people', invalidResident);

        assertValidationError(response);
        expect(response.data.detail).toContain('PGY level required');
      });

      it('should validate person type', async () => {
        const invalidPerson = {
          name: 'Dr. Invalid Type',
          type: 'invalid_type',
          email: 'invalid@test.com',
        };
        const response = await client.post('/people', invalidPerson);

        expect(response.status).toBeGreaterThanOrEqual(400);
      });

      it('should validate PGY level range', async () => {
        const invalidResident = {
          name: 'Dr. Invalid PGY',
          type: 'resident',
          email: 'invalidpgy@test.com',
          pgy_level: 5, // Invalid - should be 1-3
        };
        const response = await client.post('/people', invalidResident);

        expect(response.status).toBeGreaterThanOrEqual(400);
      });
    });

    describe('GET /api/people', () => {
      let createdPeople: any[] = [];

      beforeAll(async () => {
        // Create test people
        for (const residentData of FIXTURE_RESIDENTS) {
          const response = await client.post('/people', residentData);
          if (response.status === 201) {
            createdPeople.push(response.data);
          }
        }
      });

      it('should list all people', async () => {
        const response = await client.get('/people');

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('items');
        expect(response.data).toHaveProperty('total');
        expect(Array.isArray(response.data.items)).toBe(true);
        expect(response.data.total).toBeGreaterThanOrEqual(createdPeople.length);
      });

      it('should filter by type (residents)', async () => {
        const response = await client.get('/people', { type: 'resident' });

        assertSuccessResponse(response, 200);
        expect(response.data.items.length).toBeGreaterThan(0);
        response.data.items.forEach((person: any) => {
          expect(person.type).toBe('resident');
        });
      });

      it('should filter by type (faculty)', async () => {
        const response = await client.get('/people', { type: 'faculty' });

        assertSuccessResponse(response, 200);
        response.data.items.forEach((person: any) => {
          expect(person.type).toBe('faculty');
        });
      });

      it('should filter by PGY level', async () => {
        const response = await client.get('/people', { pgy_level: 2 });

        assertSuccessResponse(response, 200);
        response.data.items.forEach((person: any) => {
          if (person.type === 'resident') {
            expect(person.pgy_level).toBe(2);
          }
        });
      });
    });

    describe('GET /api/people/:id', () => {
      let testPerson: any;

      beforeAll(async () => {
        const response = await client.post('/people', {
          name: 'Dr. Test Get Person',
          type: 'resident',
          email: 'gettest@test.com',
          pgy_level: 1,
        });
        testPerson = response.data;
      });

      it('should get person by ID', async () => {
        const response = await client.get(`/people/${testPerson.id}`);

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('id', testPerson.id);
        expect(response.data).toHaveProperty('name', testPerson.name);
      });

      it('should return 404 for non-existent person', async () => {
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await client.get(`/people/${fakeId}`);

        assertNotFound(response, 'Person not found');
      });

      it('should return 400 for invalid UUID', async () => {
        const response = await client.get('/people/invalid-uuid');

        expect(response.status).toBeGreaterThanOrEqual(400);
      });
    });

    describe('PUT /api/people/:id', () => {
      let testPerson: any;

      beforeAll(async () => {
        const response = await client.post('/people', {
          name: 'Dr. Test Update Person',
          type: 'resident',
          email: 'updatetest@test.com',
          pgy_level: 1,
        });
        testPerson = response.data;
      });

      it('should update person', async () => {
        const updateData = {
          name: 'Dr. Updated Name',
          pgy_level: 2,
        };
        const response = await client.put(`/people/${testPerson.id}`, updateData);

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('name', updateData.name);
        expect(response.data).toHaveProperty('pgy_level', updateData.pgy_level);
      });

      it('should require authentication', async () => {
        const newClient = new ApiClient();
        const response = await newClient.put(`/people/${testPerson.id}`, { name: 'New Name' });

        assertUnauthorized(response);
      });

      it('should return 404 for non-existent person', async () => {
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await client.put(`/people/${fakeId}`, { name: 'New Name' });

        assertNotFound(response, 'Person not found');
      });
    });

    describe('DELETE /api/people/:id', () => {
      it('should delete person', async () => {
        // Create person to delete
        const createResponse = await client.post('/people', {
          name: 'Dr. Test Delete Person',
          type: 'resident',
          email: 'deletetest@test.com',
          pgy_level: 1,
        });
        const personId = createResponse.data.id;

        const response = await client.delete(`/people/${personId}`);

        expect(response.status).toBe(204);
      });

      it('should require authentication', async () => {
        const newClient = new ApiClient();
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await newClient.delete(`/people/${fakeId}`);

        assertUnauthorized(response);
      });

      it('should return 404 for non-existent person', async () => {
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await client.delete(`/people/${fakeId}`);

        assertNotFound(response, 'Person not found');
      });
    });
  });

  // ============================================================================
  // Blocks Endpoints
  // ============================================================================

  describe('Blocks Endpoints', () => {
    describe('POST /api/blocks', () => {
      it('should create a block with valid data', async () => {
        const today = new Date();
        const blockData = {
          date: formatDate(today),
          time_of_day: 'AM' as const,
          block_number: 1,
          is_weekend: false,
          is_holiday: false,
        };

        const response = await client.post('/blocks', blockData);

        assertSuccessResponse(response, 201);
        expect(response.data).toHaveProperty('id');
        expect(response.data).toHaveProperty('date', blockData.date);
        expect(response.data).toHaveProperty('time_of_day', blockData.time_of_day);
        expect(isValidUUID(response.data.id)).toBe(true);
      });

      it('should not create duplicate blocks', async () => {
        const today = new Date();
        const blockData = {
          date: formatDate(addDays(today, 1)),
          time_of_day: 'PM' as const,
          block_number: 1,
          is_weekend: false,
          is_holiday: false,
        };

        await client.post('/blocks', blockData);
        const response = await client.post('/blocks', blockData);

        assertValidationError(response);
        expect(response.data.detail).toContain('Block already exists');
      });

      it('should validate time_of_day', async () => {
        const today = new Date();
        const blockData = {
          date: formatDate(addDays(today, 2)),
          time_of_day: 'INVALID',
          block_number: 1,
          is_weekend: false,
          is_holiday: false,
        };

        const response = await client.post('/blocks', blockData);

        expect(response.status).toBeGreaterThanOrEqual(400);
      });
    });

    describe('GET /api/blocks', () => {
      beforeAll(async () => {
        // Create test blocks
        const startDate = addDays(new Date(), 10);
        const blockFixtures = generateBlockFixtures(startDate, 3);
        for (const blockData of blockFixtures) {
          await client.post('/blocks', blockData);
        }
      });

      it('should list all blocks', async () => {
        const response = await client.get('/blocks');

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('items');
        expect(response.data).toHaveProperty('total');
        expect(Array.isArray(response.data.items)).toBe(true);
      });

      it('should filter by date range', async () => {
        const startDate = formatDate(addDays(new Date(), 10));
        const endDate = formatDate(addDays(new Date(), 12));

        const response = await client.get('/blocks', {
          start_date: startDate,
          end_date: endDate,
        });

        assertSuccessResponse(response, 200);
        response.data.items.forEach((block: any) => {
          expect(block.date >= startDate).toBe(true);
          expect(block.date <= endDate).toBe(true);
        });
      });

      it('should filter by block number', async () => {
        const response = await client.get('/blocks', { block_number: 1 });

        assertSuccessResponse(response, 200);
        response.data.items.forEach((block: any) => {
          expect(block.block_number).toBe(1);
        });
      });
    });

    describe('GET /api/blocks/:id', () => {
      let testBlock: any;

      beforeAll(async () => {
        const response = await client.post('/blocks', {
          date: formatDate(addDays(new Date(), 20)),
          time_of_day: 'AM',
          block_number: 1,
          is_weekend: false,
          is_holiday: false,
        });
        testBlock = response.data;
      });

      it('should get block by ID', async () => {
        const response = await client.get(`/blocks/${testBlock.id}`);

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('id', testBlock.id);
      });

      it('should return 404 for non-existent block', async () => {
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await client.get(`/blocks/${fakeId}`);

        assertNotFound(response, 'Block not found');
      });
    });

    describe('POST /api/blocks/generate', () => {
      it('should generate blocks for date range', async () => {
        const startDate = formatDate(addDays(new Date(), 30));
        const endDate = formatDate(addDays(new Date(), 36));

        const response = await client.post(
          `/blocks/generate?start_date=${startDate}&end_date=${endDate}&base_block_number=1`,
          {}
        );

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('items');
        expect(response.data.items.length).toBeGreaterThan(0);
        // 7 days * 2 time slots = 14 blocks
        expect(response.data.items.length).toBe(14);
      });
    });

    describe('DELETE /api/blocks/:id', () => {
      it('should delete block', async () => {
        const createResponse = await client.post('/blocks', {
          date: formatDate(addDays(new Date(), 40)),
          time_of_day: 'PM',
          block_number: 1,
          is_weekend: false,
          is_holiday: false,
        });
        const blockId = createResponse.data.id;

        const response = await client.delete(`/blocks/${blockId}`);

        expect(response.status).toBe(204);
      });

      it('should return 404 for non-existent block', async () => {
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await client.delete(`/blocks/${fakeId}`);

        assertNotFound(response, 'Block not found');
      });
    });
  });

  // ============================================================================
  // Absences Endpoints
  // ============================================================================

  describe('Absences Endpoints', () => {
    let testPerson: any;

    beforeAll(async () => {
      const response = await client.post('/people', {
        name: 'Dr. Test Absence Person',
        type: 'resident',
        email: 'absencetest@test.com',
        pgy_level: 2,
      });
      testPerson = response.data;
    });

    describe('POST /api/absences', () => {
      it('should create an absence with valid data', async () => {
        const absenceData = createAbsenceFixture(
          testPerson.id,
          addDays(new Date(), 50),
          addDays(new Date(), 57),
          'vacation'
        );

        const response = await client.post('/absences', absenceData);

        assertSuccessResponse(response, 201);
        expect(response.data).toHaveProperty('id');
        expect(response.data).toHaveProperty('person_id', testPerson.id);
        expect(response.data).toHaveProperty('absence_type', 'vacation');
      });

      it('should validate absence type', async () => {
        const absenceData = {
          person_id: testPerson.id,
          start_date: formatDate(addDays(new Date(), 60)),
          end_date: formatDate(addDays(new Date(), 67)),
          absence_type: 'invalid_type',
        };

        const response = await client.post('/absences', absenceData);

        expect(response.status).toBeGreaterThanOrEqual(400);
      });

      it('should validate date range', async () => {
        const absenceData = {
          person_id: testPerson.id,
          start_date: formatDate(addDays(new Date(), 77)),
          end_date: formatDate(addDays(new Date(), 70)), // End before start
          absence_type: 'vacation',
        };

        const response = await client.post('/absences', absenceData);

        expect(response.status).toBeGreaterThanOrEqual(400);
      });
    });

    describe('GET /api/absences', () => {
      beforeAll(async () => {
        // Create test absences
        const absences = [
          createAbsenceFixture(testPerson.id, addDays(new Date(), 80), addDays(new Date(), 87), 'vacation'),
          createAbsenceFixture(testPerson.id, addDays(new Date(), 90), addDays(new Date(), 97), 'conference'),
        ];
        for (const absenceData of absences) {
          await client.post('/absences', absenceData);
        }
      });

      it('should list all absences', async () => {
        const response = await client.get('/absences');

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('items');
        expect(Array.isArray(response.data.items)).toBe(true);
      });

      it('should filter by person_id', async () => {
        const response = await client.get('/absences', { person_id: testPerson.id });

        assertSuccessResponse(response, 200);
        response.data.items.forEach((absence: any) => {
          expect(absence.person_id).toBe(testPerson.id);
        });
      });

      it('should filter by absence type', async () => {
        const response = await client.get('/absences', { absence_type: 'vacation' });

        assertSuccessResponse(response, 200);
        response.data.items.forEach((absence: any) => {
          expect(absence.absence_type).toBe('vacation');
        });
      });

      it('should filter by date range', async () => {
        const startDate = formatDate(addDays(new Date(), 75));
        const endDate = formatDate(addDays(new Date(), 100));

        const response = await client.get('/absences', {
          start_date: startDate,
          end_date: endDate,
        });

        assertSuccessResponse(response, 200);
      });
    });

    describe('GET /api/absences/:id', () => {
      let testAbsence: any;

      beforeAll(async () => {
        const absenceData = createAbsenceFixture(
          testPerson.id,
          addDays(new Date(), 100),
          addDays(new Date(), 107),
          'medical'
        );
        const response = await client.post('/absences', absenceData);
        testAbsence = response.data;
      });

      it('should get absence by ID', async () => {
        const response = await client.get(`/absences/${testAbsence.id}`);

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('id', testAbsence.id);
      });

      it('should return 404 for non-existent absence', async () => {
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await client.get(`/absences/${fakeId}`);

        assertNotFound(response, 'Absence not found');
      });
    });

    describe('PUT /api/absences/:id', () => {
      let testAbsence: any;

      beforeAll(async () => {
        const absenceData = createAbsenceFixture(
          testPerson.id,
          addDays(new Date(), 110),
          addDays(new Date(), 117),
          'vacation'
        );
        const response = await client.post('/absences', absenceData);
        testAbsence = response.data;
      });

      it('should update absence', async () => {
        const updateData = {
          absence_type: 'conference',
          notes: 'Updated notes',
        };
        const response = await client.put(`/absences/${testAbsence.id}`, updateData);

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('absence_type', updateData.absence_type);
        expect(response.data).toHaveProperty('notes', updateData.notes);
      });

      it('should return 404 for non-existent absence', async () => {
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await client.put(`/absences/${fakeId}`, { notes: 'New notes' });

        assertNotFound(response, 'Absence not found');
      });
    });

    describe('DELETE /api/absences/:id', () => {
      it('should delete absence', async () => {
        const absenceData = createAbsenceFixture(
          testPerson.id,
          addDays(new Date(), 120),
          addDays(new Date(), 127),
          'vacation'
        );
        const createResponse = await client.post('/absences', absenceData);
        const absenceId = createResponse.data.id;

        const response = await client.delete(`/absences/${absenceId}`);

        expect(response.status).toBe(204);
      });

      it('should return 404 for non-existent absence', async () => {
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await client.delete(`/absences/${fakeId}`);

        assertNotFound(response, 'Absence not found');
      });
    });
  });

  // ============================================================================
  // Assignments Endpoints
  // ============================================================================

  describe('Assignments Endpoints', () => {
    let testPerson: any;
    let testBlock: any;

    beforeAll(async () => {
      // Create test person
      const personResponse = await client.post('/people', {
        name: 'Dr. Test Assignment Person',
        type: 'resident',
        email: 'assignmenttest@test.com',
        pgy_level: 1,
      });
      testPerson = personResponse.data;

      // Create test block
      const blockResponse = await client.post('/blocks', {
        date: formatDate(addDays(new Date(), 150)),
        time_of_day: 'AM',
        block_number: 2,
        is_weekend: false,
        is_holiday: false,
      });
      testBlock = blockResponse.data;
    });

    describe('POST /api/assignments', () => {
      it('should create an assignment with valid data', async () => {
        const assignmentData = {
          block_id: testBlock.id,
          person_id: testPerson.id,
          role: 'primary',
          notes: 'Test assignment',
        };

        const response = await client.post('/assignments', assignmentData);

        assertSuccessResponse(response, 201);
        expect(response.data).toHaveProperty('id');
        expect(response.data).toHaveProperty('block_id', testBlock.id);
        expect(response.data).toHaveProperty('person_id', testPerson.id);
        expect(response.data).toHaveProperty('role', 'primary');
      });

      it('should require authentication', async () => {
        const newClient = new ApiClient();
        const assignmentData = {
          block_id: testBlock.id,
          person_id: testPerson.id,
          role: 'primary',
        };

        const response = await newClient.post('/assignments', assignmentData);

        assertUnauthorized(response);
      });

      it('should validate role', async () => {
        const blockResponse = await client.post('/blocks', {
          date: formatDate(addDays(new Date(), 151)),
          time_of_day: 'PM',
          block_number: 2,
          is_weekend: false,
          is_holiday: false,
        });

        const assignmentData = {
          block_id: blockResponse.data.id,
          person_id: testPerson.id,
          role: 'invalid_role',
        };

        const response = await client.post('/assignments', assignmentData);

        expect(response.status).toBeGreaterThanOrEqual(400);
      });

      it('should not create duplicate assignment for same person and block', async () => {
        const blockResponse = await client.post('/blocks', {
          date: formatDate(addDays(new Date(), 152)),
          time_of_day: 'AM',
          block_number: 2,
          is_weekend: false,
          is_holiday: false,
        });

        const assignmentData = {
          block_id: blockResponse.data.id,
          person_id: testPerson.id,
          role: 'primary',
        };

        await client.post('/assignments', assignmentData);
        const response = await client.post('/assignments', assignmentData);

        assertValidationError(response);
        expect(response.data.detail).toContain('already assigned');
      });
    });

    describe('GET /api/assignments', () => {
      it('should list all assignments', async () => {
        const response = await client.get('/assignments');

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('items');
        expect(Array.isArray(response.data.items)).toBe(true);
      });

      it('should require authentication', async () => {
        const newClient = new ApiClient();
        const response = await newClient.get('/assignments');

        assertUnauthorized(response);
      });

      it('should filter by person_id', async () => {
        const response = await client.get('/assignments', { person_id: testPerson.id });

        assertSuccessResponse(response, 200);
        response.data.items.forEach((assignment: any) => {
          expect(assignment.person_id).toBe(testPerson.id);
        });
      });

      it('should filter by role', async () => {
        const response = await client.get('/assignments', { role: 'primary' });

        assertSuccessResponse(response, 200);
        response.data.items.forEach((assignment: any) => {
          expect(assignment.role).toBe('primary');
        });
      });

      it('should filter by date range', async () => {
        const startDate = formatDate(addDays(new Date(), 145));
        const endDate = formatDate(addDays(new Date(), 155));

        const response = await client.get('/assignments', {
          start_date: startDate,
          end_date: endDate,
        });

        assertSuccessResponse(response, 200);
      });
    });

    describe('GET /api/assignments/:id', () => {
      let testAssignment: any;

      beforeAll(async () => {
        const blockResponse = await client.post('/blocks', {
          date: formatDate(addDays(new Date(), 160)),
          time_of_day: 'PM',
          block_number: 2,
          is_weekend: false,
          is_holiday: false,
        });

        const assignmentData = {
          block_id: blockResponse.data.id,
          person_id: testPerson.id,
          role: 'primary',
        };
        const response = await client.post('/assignments', assignmentData);
        testAssignment = response.data;
      });

      it('should get assignment by ID', async () => {
        const response = await client.get(`/assignments/${testAssignment.id}`);

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('id', testAssignment.id);
      });

      it('should require authentication', async () => {
        const newClient = new ApiClient();
        const response = await newClient.get(`/assignments/${testAssignment.id}`);

        assertUnauthorized(response);
      });

      it('should return 404 for non-existent assignment', async () => {
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await client.get(`/assignments/${fakeId}`);

        assertNotFound(response, 'Assignment not found');
      });
    });

    describe('PUT /api/assignments/:id', () => {
      let testAssignment: any;

      beforeAll(async () => {
        const blockResponse = await client.post('/blocks', {
          date: formatDate(addDays(new Date(), 170)),
          time_of_day: 'AM',
          block_number: 2,
          is_weekend: false,
          is_holiday: false,
        });

        const assignmentData = {
          block_id: blockResponse.data.id,
          person_id: testPerson.id,
          role: 'primary',
        };
        const response = await client.post('/assignments', assignmentData);
        testAssignment = response.data;
      });

      it('should update assignment', async () => {
        const updateData = {
          role: 'backup',
          notes: 'Updated assignment',
          updated_at: testAssignment.updated_at,
        };
        const response = await client.put(`/assignments/${testAssignment.id}`, updateData);

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('role', updateData.role);
        expect(response.data).toHaveProperty('notes', updateData.notes);
      });

      it('should require authentication', async () => {
        const newClient = new ApiClient();
        const updateData = {
          notes: 'New notes',
          updated_at: testAssignment.updated_at,
        };
        const response = await newClient.put(`/assignments/${testAssignment.id}`, updateData);

        assertUnauthorized(response);
      });

      it('should return 404 for non-existent assignment', async () => {
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await client.put(`/assignments/${fakeId}`, {
          notes: 'New notes',
          updated_at: new Date().toISOString(),
        });

        assertNotFound(response, 'Assignment not found');
      });

      it('should enforce optimistic locking', async () => {
        const updateData = {
          notes: 'Updated notes',
          updated_at: '2000-01-01T00:00:00.000Z', // Old timestamp
        };
        const response = await client.put(`/assignments/${testAssignment.id}`, updateData);

        expect(response.status).toBe(409);
        expect(response.data.detail).toContain('modified by another user');
      });
    });

    describe('DELETE /api/assignments/:id', () => {
      it('should delete assignment', async () => {
        const blockResponse = await client.post('/blocks', {
          date: formatDate(addDays(new Date(), 180)),
          time_of_day: 'PM',
          block_number: 2,
          is_weekend: false,
          is_holiday: false,
        });

        const assignmentData = {
          block_id: blockResponse.data.id,
          person_id: testPerson.id,
          role: 'primary',
        };
        const createResponse = await client.post('/assignments', assignmentData);
        const assignmentId = createResponse.data.id;

        const response = await client.delete(`/assignments/${assignmentId}`);

        expect(response.status).toBe(204);
      });

      it('should require authentication', async () => {
        const newClient = new ApiClient();
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await newClient.delete(`/assignments/${fakeId}`);

        assertUnauthorized(response);
      });

      it('should return 404 for non-existent assignment', async () => {
        const fakeId = '00000000-0000-0000-0000-000000000000';
        const response = await client.delete(`/assignments/${fakeId}`);

        assertNotFound(response, 'Assignment not found');
      });
    });
  });

  // ============================================================================
  // Schedule Endpoints
  // ============================================================================

  describe('Schedule Endpoints', () => {
    describe('GET /api/schedule/:start_date/:end_date', () => {
      beforeAll(async () => {
        // Create test data for schedule
        const startDate = addDays(new Date(), 200);
        const blockFixtures = generateBlockFixtures(startDate, 3);

        for (const blockData of blockFixtures) {
          await client.post('/blocks', blockData);
        }
      });

      it('should get schedule for date range', async () => {
        const startDate = formatDate(addDays(new Date(), 200));
        const endDate = formatDate(addDays(new Date(), 202));

        const response = await client.get(`/schedule/${startDate}/${endDate}`);

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('start_date', startDate);
        expect(response.data).toHaveProperty('end_date', endDate);
        expect(response.data).toHaveProperty('schedule');
        expect(response.data).toHaveProperty('total_assignments');
      });

      it('should return 400 for invalid date format', async () => {
        const response = await client.get('/schedule/invalid-date/2024-12-31');

        assertValidationError(response);
      });

      it('should return empty schedule for date range with no assignments', async () => {
        const futureDate = formatDate(addDays(new Date(), 500));
        const response = await client.get(`/schedule/${futureDate}/${futureDate}`);

        assertSuccessResponse(response, 200);
        expect(response.data.total_assignments).toBe(0);
      });
    });

    describe('POST /api/schedule/generate', () => {
      it('should require authentication', async () => {
        const newClient = new ApiClient();
        const scheduleRequest = {
          start_date: formatDate(addDays(new Date(), 300)),
          end_date: formatDate(addDays(new Date(), 327)),
          algorithm: 'greedy',
        };

        const response = await newClient.post('/schedule/generate', scheduleRequest);

        assertUnauthorized(response);
      });

      it('should validate date range', async () => {
        const scheduleRequest = {
          start_date: formatDate(addDays(new Date(), 327)),
          end_date: formatDate(addDays(new Date(), 300)), // End before start
          algorithm: 'greedy',
        };

        const response = await client.post('/schedule/generate', scheduleRequest);

        expect(response.status).toBeGreaterThanOrEqual(400);
      });

      it('should validate algorithm', async () => {
        const scheduleRequest = {
          start_date: formatDate(addDays(new Date(), 350)),
          end_date: formatDate(addDays(new Date(), 377)),
          algorithm: 'invalid_algorithm',
        };

        const response = await client.post('/schedule/generate', scheduleRequest);

        expect(response.status).toBeGreaterThanOrEqual(400);
      });
    });

    describe('GET /api/schedule/validate', () => {
      it('should validate schedule for date range', async () => {
        const startDate = formatDate(addDays(new Date(), 200));
        const endDate = formatDate(addDays(new Date(), 202));

        const response = await client.get('/schedule/validate', {
          start_date: startDate,
          end_date: endDate,
        });

        assertSuccessResponse(response, 200);
        expect(response.data).toHaveProperty('valid');
        expect(response.data).toHaveProperty('total_violations');
        expect(response.data).toHaveProperty('violations');
        expect(response.data).toHaveProperty('coverage_rate');
      });

      it('should return 400 for invalid date format', async () => {
        const response = await client.get('/schedule/validate', {
          start_date: 'invalid-date',
          end_date: '2024-12-31',
        });

        assertValidationError(response);
        expect(response.data.detail).toContain('Invalid date format');
      });
    });
  });

  // ============================================================================
  // Export Endpoints
  // ============================================================================

  describe('Export Endpoints', () => {
    describe('GET /api/export/people', () => {
      it('should export people as CSV', async () => {
        const response = await client.get('/export/people', { format: 'csv' });

        assertSuccessResponse(response, 200);
        expect(response.headers['content-type']).toContain('text/csv');
        expect(response.headers['content-disposition']).toContain('people.csv');
      });

      it('should export people as JSON', async () => {
        const response = await client.get('/export/people', { format: 'json' });

        assertSuccessResponse(response, 200);
        expect(response.headers['content-type']).toContain('application/json');
        expect(response.headers['content-disposition']).toContain('people.json');
      });
    });

    describe('GET /api/export/absences', () => {
      it('should export absences as CSV', async () => {
        const response = await client.get('/export/absences', { format: 'csv' });

        assertSuccessResponse(response, 200);
        expect(response.headers['content-type']).toContain('text/csv');
        expect(response.headers['content-disposition']).toContain('absences.csv');
      });

      it('should export absences as JSON', async () => {
        const response = await client.get('/export/absences', { format: 'json' });

        assertSuccessResponse(response, 200);
        expect(response.headers['content-type']).toContain('application/json');
      });

      it('should filter by date range', async () => {
        const startDate = formatDate(addDays(new Date(), 50));
        const endDate = formatDate(addDays(new Date(), 100));

        const response = await client.get('/export/absences', {
          format: 'csv',
          start_date: startDate,
          end_date: endDate,
        });

        assertSuccessResponse(response, 200);
      });
    });

    describe('GET /api/export/schedule', () => {
      it('should require start_date and end_date', async () => {
        const response = await client.get('/export/schedule', { format: 'csv' });

        expect(response.status).toBeGreaterThanOrEqual(400);
      });

      it('should export schedule as CSV', async () => {
        const startDate = formatDate(addDays(new Date(), 200));
        const endDate = formatDate(addDays(new Date(), 202));

        const response = await client.get('/export/schedule', {
          format: 'csv',
          start_date: startDate,
          end_date: endDate,
        });

        assertSuccessResponse(response, 200);
        expect(response.headers['content-type']).toContain('text/csv');
        expect(response.headers['content-disposition']).toContain('schedule.csv');
      });

      it('should export schedule as JSON', async () => {
        const startDate = formatDate(addDays(new Date(), 200));
        const endDate = formatDate(addDays(new Date(), 202));

        const response = await client.get('/export/schedule', {
          format: 'json',
          start_date: startDate,
          end_date: endDate,
        });

        assertSuccessResponse(response, 200);
        expect(response.headers['content-type']).toContain('application/json');
      });
    });

    describe('GET /api/export/schedule/xlsx', () => {
      it('should require start_date and end_date', async () => {
        const response = await client.get('/export/schedule/xlsx');

        expect(response.status).toBeGreaterThanOrEqual(400);
      });

      it('should export schedule as Excel file', async () => {
        const startDate = formatDate(addDays(new Date(), 200));
        const endDate = formatDate(addDays(new Date(), 202));

        const response = await client.get('/export/schedule/xlsx', {
          start_date: startDate,
          end_date: endDate,
        });

        assertSuccessResponse(response, 200);
        expect(response.headers['content-type']).toContain('spreadsheetml.sheet');
        expect(response.headers['content-disposition']).toContain('.xlsx');
      });

      it('should validate date format', async () => {
        const response = await client.get('/export/schedule/xlsx', {
          start_date: 'invalid-date',
          end_date: '2024-12-31',
        });

        expect(response.status).toBeGreaterThanOrEqual(400);
      });
    });
  });

  // ============================================================================
  // Error Handling Tests
  // ============================================================================

  describe('Error Handling', () => {
    it('should return 404 for non-existent endpoints', async () => {
      const response = await client.get('/non-existent-endpoint');

      expect(response.status).toBe(404);
    });

    it('should handle malformed JSON', async () => {
      const response = await client.post('/people', 'invalid-json');

      expect(response.status).toBeGreaterThanOrEqual(400);
    });

    it('should validate required fields', async () => {
      const response = await client.post('/people', {
        // Missing required fields
        type: 'resident',
      });

      expect(response.status).toBeGreaterThanOrEqual(400);
    });

    it('should handle invalid UUIDs', async () => {
      const response = await client.get('/people/not-a-uuid');

      expect(response.status).toBeGreaterThanOrEqual(400);
    });
  });
});
