/**
 * Integration Test Setup
 *
 * Provides test database setup/teardown, fixtures, and helper functions
 * for API integration tests.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// Configuration
export const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000/api';
export const TEST_TIMEOUT = 30000;

// Test user credentials
export const TEST_USERS = {
  admin: {
    username: 'test_admin',
    email: 'admin@test.com',
    password: 'TestPass123!',
    role: 'admin',
  },
  coordinator: {
    username: 'test_coordinator',
    email: 'coordinator@test.com',
    password: 'TestPass123!',
    role: 'coordinator',
  },
  faculty: {
    username: 'test_faculty',
    email: 'faculty@test.com',
    password: 'TestPass123!',
    role: 'faculty',
  },
};

// API Client with axios
export class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      validateStatus: () => true, // Don't throw on any status
    });
  }

  setToken(token: string): void {
    this.token = token;
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearToken(): void {
    this.token = null;
    delete this.client.defaults.headers.common['Authorization'];
  }

  getToken(): string | null {
    return this.token;
  }

  // HTTP Methods
  async get(url: string, params?: any) {
    return this.client.get(url, { params });
  }

  async post(url: string, data?: any) {
    return this.client.post(url, data);
  }

  async put(url: string, data?: any) {
    return this.client.put(url, data);
  }

  async delete(url: string) {
    return this.client.delete(url);
  }

  // Auth helpers
  async login(username: string, password: string) {
    const response = await this.post('/auth/login/json', { username, password });
    if (response.status === 200 && response.data.access_token) {
      this.setToken(response.data.access_token);
    }
    return response;
  }

  async logout() {
    const response = await this.post('/auth/logout');
    this.clearToken();
    return response;
  }

  async register(userData: any) {
    return this.post('/auth/register', userData);
  }

  async getCurrentUser() {
    return this.get('/auth/me');
  }
}

// Test Fixtures
export interface PersonFixture {
  name: string;
  type: 'resident' | 'faculty';
  email: string;
  pgy_level?: number;
  performs_procedures?: boolean;
  specialties?: string[];
}

export const FIXTURE_RESIDENTS: PersonFixture[] = [
  {
    name: 'Dr. Test Resident PGY1',
    type: 'resident',
    email: 'pgy1@test.com',
    pgy_level: 1,
  },
  {
    name: 'Dr. Test Resident PGY2',
    type: 'resident',
    email: 'pgy2@test.com',
    pgy_level: 2,
  },
  {
    name: 'Dr. Test Resident PGY3',
    type: 'resident',
    email: 'pgy3@test.com',
    pgy_level: 3,
  },
];

export const FIXTURE_FACULTY: PersonFixture[] = [
  {
    name: 'Dr. Test Attending 1',
    type: 'faculty',
    email: 'faculty1@test.com',
    performs_procedures: true,
    specialties: ['Sports Medicine', 'Primary Care'],
  },
  {
    name: 'Dr. Test Attending 2',
    type: 'faculty',
    email: 'faculty2@test.com',
    performs_procedures: false,
    specialties: ['General Medicine'],
  },
];

export interface BlockFixture {
  date: string;
  time_of_day: 'AM' | 'PM';
  block_number: number;
  is_weekend: boolean;
  is_holiday: boolean;
}

export function generateBlockFixtures(
  startDate: Date,
  days: number = 7,
  blockNumber: number = 1
): BlockFixture[] {
  const blocks: BlockFixture[] = [];

  for (let i = 0; i < days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];
    const isWeekend = date.getDay() === 0 || date.getDay() === 6;

    for (const timeOfDay of ['AM', 'PM'] as const) {
      blocks.push({
        date: dateStr,
        time_of_day: timeOfDay,
        block_number: blockNumber + Math.floor(i / 28),
        is_weekend: isWeekend,
        is_holiday: false,
      });
    }
  }

  return blocks;
}

export interface AbsenceFixture {
  person_id: string;
  start_date: string;
  end_date: string;
  absence_type: string;
  notes?: string;
}

export function createAbsenceFixture(
  personId: string,
  startDate: Date,
  endDate: Date,
  type: string = 'vacation'
): AbsenceFixture {
  return {
    person_id: personId,
    start_date: startDate.toISOString().split('T')[0],
    end_date: endDate.toISOString().split('T')[0],
    absence_type: type,
    notes: `Test absence - ${type}`,
  };
}

export interface AssignmentFixture {
  block_id: string;
  person_id: string;
  rotation_template_id?: string;
  role: 'primary' | 'supervising' | 'backup';
  notes?: string;
}

// Test Database Helpers
export class TestDatabase {
  private client: ApiClient;

  constructor(client: ApiClient) {
    this.client = client;
  }

  // Setup: Create test users
  async setupUsers(): Promise<{ admin: any; coordinator: any }> {
    const users: any = {};

    // First user becomes admin automatically
    const adminResponse = await this.client.register(TEST_USERS.admin);
    if (adminResponse.status === 201) {
      users.admin = adminResponse.data;

      // Login as admin to create other users
      await this.client.login(TEST_USERS.admin.username, TEST_USERS.admin.password);

      // Create coordinator
      const coordResponse = await this.client.register(TEST_USERS.coordinator);
      if (coordResponse.status === 201) {
        users.coordinator = coordResponse.data;
      }
    }

    return users;
  }

  // Setup: Create test people
  async setupPeople(): Promise<{ residents: any[]; faculty: any[] }> {
    const residents = [];
    const faculty = [];

    for (const residentData of FIXTURE_RESIDENTS) {
      const response = await this.client.post('/people', residentData);
      if (response.status === 201) {
        residents.push(response.data);
      }
    }

    for (const facultyData of FIXTURE_FACULTY) {
      const response = await this.client.post('/people', facultyData);
      if (response.status === 201) {
        faculty.push(response.data);
      }
    }

    return { residents, faculty };
  }

  // Setup: Create test blocks
  async setupBlocks(startDate: Date, days: number = 7): Promise<any[]> {
    const blockFixtures = generateBlockFixtures(startDate, days);
    const blocks = [];

    for (const blockData of blockFixtures) {
      const response = await this.client.post('/blocks', blockData);
      if (response.status === 201) {
        blocks.push(response.data);
      }
    }

    return blocks;
  }

  // Setup: Create test absences
  async setupAbsences(absenceFixtures: AbsenceFixture[]): Promise<any[]> {
    const absences = [];

    for (const absenceData of absenceFixtures) {
      const response = await this.client.post('/absences', absenceData);
      if (response.status === 201) {
        absences.push(response.data);
      }
    }

    return absences;
  }

  // Setup: Create test assignments
  async setupAssignments(assignmentFixtures: AssignmentFixture[]): Promise<any[]> {
    const assignments = [];

    for (const assignmentData of assignmentFixtures) {
      const response = await this.client.post('/assignments', assignmentData);
      if (response.status === 201) {
        assignments.push(response.data);
      }
    }

    return assignments;
  }

  // Cleanup: Delete all test data
  async cleanup(): Promise<void> {
    // Note: In a real test environment, you would typically:
    // 1. Use a separate test database
    // 2. Truncate tables or use transactions
    // 3. Reset to a known state
    //
    // For these integration tests, we assume each test will clean up
    // its own data or use a fresh database instance
  }
}

// Test Utilities
export function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

export function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

export function getDateRange(startDate: Date, endDate: Date): string[] {
  const dates: string[] = [];
  const current = new Date(startDate);

  while (current <= endDate) {
    dates.push(formatDate(current));
    current.setDate(current.getDate() + 1);
  }

  return dates;
}

// Assertion Helpers
export function assertSuccessResponse(response: any, expectedStatus: number = 200): void {
  expect(response.status).toBe(expectedStatus);
}

export function assertErrorResponse(
  response: any,
  expectedStatus: number,
  expectedMessage?: string
): void {
  expect(response.status).toBe(expectedStatus);
  expect(response.data).toHaveProperty('detail');
  if (expectedMessage) {
    expect(response.data.detail).toContain(expectedMessage);
  }
}

export function assertValidationError(response: any, field?: string): void {
  expect(response.status).toBe(400);
  expect(response.data).toHaveProperty('detail');
}

export function assertUnauthorized(response: any): void {
  expect(response.status).toBe(401);
  expect(response.data).toHaveProperty('detail');
}

export function assertNotFound(response: any, resource?: string): void {
  expect(response.status).toBe(404);
  expect(response.data).toHaveProperty('detail');
  if (resource) {
    expect(response.data.detail).toContain(resource);
  }
}

export function assertForbidden(response: any): void {
  expect(response.status).toBe(403);
  expect(response.data).toHaveProperty('detail');
}

// UUID validation helper
export function isValidUUID(uuid: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
}

// Retry helper for flaky tests
export async function retry<T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  delayMs: number = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxAttempts) throw error;
      await new Promise(resolve => setTimeout(resolve, delayMs));
    }
  }
  throw new Error('Retry failed');
}

// Wait helper
export function wait(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Export types
export interface TestContext {
  client: ApiClient;
  db: TestDatabase;
  users?: any;
  people?: { residents: any[]; faculty: any[] };
  blocks?: any[];
  absences?: any[];
  assignments?: any[];
}

// Global test setup/teardown helpers
export async function setupTestEnvironment(): Promise<TestContext> {
  const client = new ApiClient();
  const db = new TestDatabase(client);

  return { client, db };
}

export async function teardownTestEnvironment(context: TestContext): Promise<void> {
  // Logout if authenticated
  if (context.client.getToken()) {
    await context.client.logout();
  }

  // Additional cleanup if needed
  await context.db.cleanup();
}
