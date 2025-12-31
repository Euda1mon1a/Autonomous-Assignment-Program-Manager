import { test as base } from '@playwright/test';
import { APIRequestContext } from '@playwright/test';

/**
 * Database Seeding Fixtures for E2E Tests
 *
 * Provides database setup/teardown and seeding capabilities
 * for consistent test data across test runs.
 */

export type DatabaseContext = {
  db: DatabaseHelper;
};

export class DatabaseHelper {
  private apiContext: APIRequestContext;
  private baseURL: string;
  private createdEntities: Map<string, string[]>;

  constructor(apiContext: APIRequestContext, baseURL: string) {
    this.apiContext = apiContext;
    this.baseURL = baseURL;
    this.createdEntities = new Map();
  }

  /**
   * Seed test users
   */
  async seedUsers(): Promise<void> {
    const users = [
      {
        email: 'admin@test.mil',
        password: 'TestPassword123!',
        role: 'ADMIN',
        first_name: 'Admin',
        last_name: 'User',
        id: 'test-admin-001',
      },
      {
        email: 'coordinator@test.mil',
        password: 'TestPassword123!',
        role: 'COORDINATOR',
        first_name: 'Coordinator',
        last_name: 'User',
        id: 'test-coord-001',
      },
      {
        email: 'faculty@test.mil',
        password: 'TestPassword123!',
        role: 'FACULTY',
        first_name: 'Faculty',
        last_name: 'Member',
        id: 'test-faculty-001',
      },
      {
        email: 'resident@test.mil',
        password: 'TestPassword123!',
        role: 'RESIDENT',
        first_name: 'PGY2',
        last_name: 'Resident',
        id: 'test-resident-001',
      },
    ];

    const userIds: string[] = [];

    for (const user of users) {
      const response = await this.apiContext.post(`${this.baseURL}/api/v1/users`, {
        data: user,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok()) {
        const data = await response.json();
        userIds.push(data.id);
      }
    }

    this.createdEntities.set('users', userIds);
  }

  /**
   * Seed test residents
   */
  async seedResidents(count: number = 10): Promise<string[]> {
    const residents: string[] = [];

    for (let i = 1; i <= count; i++) {
      const pgyLevel = (i % 3) + 1; // PGY1, PGY2, PGY3
      const resident = {
        id: `test-resident-${String(i).padStart(3, '0')}`,
        first_name: `PGY${pgyLevel}`,
        last_name: `Resident${i}`,
        email: `resident${i}@test.mil`,
        role: 'RESIDENT',
        pgy_level: pgyLevel,
        specialty: 'Family Medicine',
        status: 'ACTIVE',
      };

      const response = await this.apiContext.post(`${this.baseURL}/api/v1/persons`, {
        data: resident,
      });

      if (response.ok()) {
        const data = await response.json();
        residents.push(data.id);
      }
    }

    this.createdEntities.set('residents', residents);
    return residents;
  }

  /**
   * Seed test faculty
   */
  async seedFaculty(count: number = 5): Promise<string[]> {
    const faculty: string[] = [];

    for (let i = 1; i <= count; i++) {
      const facultyMember = {
        id: `test-faculty-${String(i).padStart(3, '0')}`,
        first_name: `Faculty`,
        last_name: `Member${i}`,
        email: `faculty${i}@test.mil`,
        role: 'FACULTY',
        specialty: 'Family Medicine',
        status: 'ACTIVE',
      };

      const response = await this.apiContext.post(`${this.baseURL}/api/v1/persons`, {
        data: facultyMember,
      });

      if (response.ok()) {
        const data = await response.json();
        faculty.push(data.id);
      }
    }

    this.createdEntities.set('faculty', faculty);
    return faculty;
  }

  /**
   * Seed rotation templates
   */
  async seedRotations(): Promise<string[]> {
    const rotations = [
      {
        id: 'test-rotation-clinic',
        name: 'Family Medicine Clinic',
        code: 'FMIT',
        hours_per_session: 4,
        requires_supervision: true,
      },
      {
        id: 'test-rotation-inpatient',
        name: 'Inpatient Medicine',
        code: 'INPT',
        hours_per_session: 12,
        requires_supervision: true,
      },
      {
        id: 'test-rotation-procedures',
        name: 'Procedures',
        code: 'PROC',
        hours_per_session: 4,
        requires_supervision: true,
      },
      {
        id: 'test-rotation-call',
        name: 'Night Call',
        code: 'CALL',
        hours_per_session: 12,
        requires_supervision: false,
      },
      {
        id: 'test-rotation-conference',
        name: 'Conference',
        code: 'CONF',
        hours_per_session: 2,
        requires_supervision: false,
      },
    ];

    const rotationIds: string[] = [];

    for (const rotation of rotations) {
      const response = await this.apiContext.post(`${this.baseURL}/api/v1/rotations`, {
        data: rotation,
      });

      if (response.ok()) {
        const data = await response.json();
        rotationIds.push(data.id);
      }
    }

    this.createdEntities.set('rotations', rotationIds);
    return rotationIds;
  }

  /**
   * Seed blocks (schedule time slots)
   */
  async seedBlocks(days: number = 30): Promise<string[]> {
    const blocks: string[] = [];
    const today = new Date();

    for (let i = 0; i < days; i++) {
      const date = new Date(today);
      date.setDate(date.getDate() + i);

      // AM block
      const amBlock = {
        id: `test-block-${date.toISOString().split('T')[0]}-am`,
        date: date.toISOString().split('T')[0],
        session: 'AM',
        status: 'ACTIVE',
      };

      const amResponse = await this.apiContext.post(`${this.baseURL}/api/v1/blocks`, {
        data: amBlock,
      });

      if (amResponse.ok()) {
        const data = await amResponse.json();
        blocks.push(data.id);
      }

      // PM block
      const pmBlock = {
        id: `test-block-${date.toISOString().split('T')[0]}-pm`,
        date: date.toISOString().split('T')[0],
        session: 'PM',
        status: 'ACTIVE',
      };

      const pmResponse = await this.apiContext.post(`${this.baseURL}/api/v1/blocks`, {
        data: pmBlock,
      });

      if (pmResponse.ok()) {
        const data = await pmResponse.json();
        blocks.push(data.id);
      }
    }

    this.createdEntities.set('blocks', blocks);
    return blocks;
  }

  /**
   * Create test assignments
   */
  async createAssignments(
    residentIds: string[],
    blockIds: string[],
    rotationIds: string[]
  ): Promise<string[]> {
    const assignments: string[] = [];

    for (let i = 0; i < Math.min(residentIds.length, blockIds.length); i++) {
      const assignment = {
        person_id: residentIds[i % residentIds.length],
        block_id: blockIds[i],
        rotation_id: rotationIds[i % rotationIds.length],
        status: 'CONFIRMED',
      };

      const response = await this.apiContext.post(`${this.baseURL}/api/v1/assignments`, {
        data: assignment,
      });

      if (response.ok()) {
        const data = await response.json();
        assignments.push(data.id);
      }
    }

    this.createdEntities.set('assignments', assignments);
    return assignments;
  }

  /**
   * Clean up all created entities
   */
  async cleanup(): Promise<void> {
    // Clean up in reverse order of creation
    const cleanupOrder = ['assignments', 'blocks', 'rotations', 'residents', 'faculty', 'users'];

    for (const entityType of cleanupOrder) {
      const ids = this.createdEntities.get(entityType) || [];

      for (const id of ids) {
        try {
          await this.apiContext.delete(`${this.baseURL}/api/v1/${entityType}/${id}`);
        } catch (error) {
          // Ignore errors during cleanup
          console.warn(`Failed to delete ${entityType}/${id}:`, error);
        }
      }
    }

    this.createdEntities.clear();
  }

  /**
   * Reset database to clean state
   */
  async resetDatabase(): Promise<void> {
    await this.apiContext.post(`${this.baseURL}/api/v1/test/reset-database`);
  }

  /**
   * Get created entity IDs
   */
  getCreatedIds(entityType: string): string[] {
    return this.createdEntities.get(entityType) || [];
  }
}

/**
 * Extended test with database helpers
 */
export const test = base.extend<DatabaseContext>({
  db: async ({ request }, use, testInfo) => {
    const baseURL = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';
    const db = new DatabaseHelper(request, baseURL);

    // Setup: seed database before test
    await db.resetDatabase();
    await db.seedUsers();

    await use(db);

    // Teardown: cleanup after test
    await db.cleanup();
  },
});

export { expect } from '@playwright/test';
