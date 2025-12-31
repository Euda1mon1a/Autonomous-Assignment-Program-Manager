import { test as base } from './database.fixture';
import { APIRequestContext } from '@playwright/test';

/**
 * Schedule-specific fixtures for E2E tests
 *
 * Provides pre-configured schedule scenarios:
 * - Empty schedule
 * - Partially filled schedule
 * - Fully staffed schedule
 * - Schedule with conflicts
 * - Schedule with ACGME violations
 */

export type ScheduleScenario = {
  name: string;
  residentIds: string[];
  facultyIds: string[];
  blockIds: string[];
  rotationIds: string[];
  assignmentIds: string[];
};

export type ScheduleContext = {
  scheduleHelper: ScheduleHelper;
};

export class ScheduleHelper {
  private apiContext: APIRequestContext;
  private baseURL: string;

  constructor(apiContext: APIRequestContext, baseURL: string) {
    this.apiContext = apiContext;
    this.baseURL = baseURL;
  }

  /**
   * Create empty schedule (blocks only, no assignments)
   */
  async createEmptySchedule(days: number = 7): Promise<ScheduleScenario> {
    const blocks: string[] = [];
    const today = new Date();

    for (let i = 0; i < days; i++) {
      const date = new Date(today);
      date.setDate(date.getDate() + i);
      const dateStr = date.toISOString().split('T')[0];

      // AM block
      const amResponse = await this.apiContext.post(`${this.baseURL}/api/v1/blocks`, {
        data: {
          date: dateStr,
          session: 'AM',
          status: 'ACTIVE',
        },
      });
      if (amResponse.ok()) {
        const data = await amResponse.json();
        blocks.push(data.id);
      }

      // PM block
      const pmResponse = await this.apiContext.post(`${this.baseURL}/api/v1/blocks`, {
        data: {
          date: dateStr,
          session: 'PM',
          status: 'ACTIVE',
        },
      });
      if (pmResponse.ok()) {
        const data = await pmResponse.json();
        blocks.push(data.id);
      }
    }

    return {
      name: 'empty',
      residentIds: [],
      facultyIds: [],
      blockIds: blocks,
      rotationIds: [],
      assignmentIds: [],
    };
  }

  /**
   * Create partially filled schedule (50% coverage)
   */
  async createPartialSchedule(days: number = 7, residentCount: number = 5): Promise<ScheduleScenario> {
    // Create residents
    const residents: string[] = [];
    for (let i = 1; i <= residentCount; i++) {
      const response = await this.apiContext.post(`${this.baseURL}/api/v1/persons`, {
        data: {
          first_name: `PGY${(i % 3) + 1}`,
          last_name: `Resident${i}`,
          email: `e2e-resident-${i}@test.mil`,
          role: 'RESIDENT',
          pgy_level: (i % 3) + 1,
        },
      });
      if (response.ok()) {
        const data = await response.json();
        residents.push(data.id);
      }
    }

    // Create rotations
    const rotations: string[] = [];
    const rotationTypes = ['FMIT', 'INPT', 'PROC'];
    for (const rotType of rotationTypes) {
      const response = await this.apiContext.post(`${this.baseURL}/api/v1/rotations`, {
        data: {
          name: `Test ${rotType}`,
          code: rotType,
          hours_per_session: 4,
        },
      });
      if (response.ok()) {
        const data = await response.json();
        rotations.push(data.id);
      }
    }

    // Create blocks
    const blocks: string[] = [];
    const today = new Date();
    for (let i = 0; i < days; i++) {
      const date = new Date(today);
      date.setDate(date.getDate() + i);
      const dateStr = date.toISOString().split('T')[0];

      const amResponse = await this.apiContext.post(`${this.baseURL}/api/v1/blocks`, {
        data: { date: dateStr, session: 'AM' },
      });
      if (amResponse.ok()) blocks.push((await amResponse.json()).id);

      const pmResponse = await this.apiContext.post(`${this.baseURL}/api/v1/blocks`, {
        data: { date: dateStr, session: 'PM' },
      });
      if (pmResponse.ok()) blocks.push((await pmResponse.json()).id);
    }

    // Create assignments for 50% of blocks
    const assignments: string[] = [];
    const assignmentCount = Math.floor(blocks.length / 2);
    for (let i = 0; i < assignmentCount; i++) {
      const response = await this.apiContext.post(`${this.baseURL}/api/v1/assignments`, {
        data: {
          person_id: residents[i % residents.length],
          block_id: blocks[i],
          rotation_id: rotations[i % rotations.length],
          status: 'CONFIRMED',
        },
      });
      if (response.ok()) {
        const data = await response.json();
        assignments.push(data.id);
      }
    }

    return {
      name: 'partial',
      residentIds: residents,
      facultyIds: [],
      blockIds: blocks,
      rotationIds: rotations,
      assignmentIds: assignments,
    };
  }

  /**
   * Create fully staffed schedule (100% coverage)
   */
  async createFullSchedule(days: number = 7, residentCount: number = 10): Promise<ScheduleScenario> {
    // Create all entities
    const residents: string[] = [];
    for (let i = 1; i <= residentCount; i++) {
      const response = await this.apiContext.post(`${this.baseURL}/api/v1/persons`, {
        data: {
          first_name: `PGY${(i % 3) + 1}`,
          last_name: `Resident${i}`,
          email: `e2e-resident-full-${i}@test.mil`,
          role: 'RESIDENT',
          pgy_level: (i % 3) + 1,
        },
      });
      if (response.ok()) residents.push((await response.json()).id);
    }

    const faculty: string[] = [];
    for (let i = 1; i <= 5; i++) {
      const response = await this.apiContext.post(`${this.baseURL}/api/v1/persons`, {
        data: {
          first_name: 'Faculty',
          last_name: `Member${i}`,
          email: `e2e-faculty-full-${i}@test.mil`,
          role: 'FACULTY',
        },
      });
      if (response.ok()) faculty.push((await response.json()).id);
    }

    const rotations: string[] = [];
    const rotationTypes = ['FMIT', 'INPT', 'PROC', 'CALL'];
    for (const rotType of rotationTypes) {
      const response = await this.apiContext.post(`${this.baseURL}/api/v1/rotations`, {
        data: {
          name: `Test ${rotType}`,
          code: rotType,
          hours_per_session: rotType === 'CALL' ? 12 : 4,
        },
      });
      if (response.ok()) rotations.push((await response.json()).id);
    }

    const blocks: string[] = [];
    const today = new Date();
    for (let i = 0; i < days; i++) {
      const date = new Date(today);
      date.setDate(date.getDate() + i);
      const dateStr = date.toISOString().split('T')[0];

      const amResponse = await this.apiContext.post(`${this.baseURL}/api/v1/blocks`, {
        data: { date: dateStr, session: 'AM' },
      });
      if (amResponse.ok()) blocks.push((await amResponse.json()).id);

      const pmResponse = await this.apiContext.post(`${this.baseURL}/api/v1/blocks`, {
        data: { date: dateStr, session: 'PM' },
      });
      if (pmResponse.ok()) blocks.push((await pmResponse.json()).id);
    }

    // Create assignments for all blocks
    const assignments: string[] = [];
    for (let i = 0; i < blocks.length; i++) {
      const response = await this.apiContext.post(`${this.baseURL}/api/v1/assignments`, {
        data: {
          person_id: residents[i % residents.length],
          block_id: blocks[i],
          rotation_id: rotations[i % rotations.length],
          status: 'CONFIRMED',
        },
      });
      if (response.ok()) assignments.push((await response.json()).id);
    }

    return {
      name: 'full',
      residentIds: residents,
      facultyIds: faculty,
      blockIds: blocks,
      rotationIds: rotations,
      assignmentIds: assignments,
    };
  }

  /**
   * Create schedule with intentional conflicts (double-booking)
   */
  async createConflictingSchedule(): Promise<ScheduleScenario> {
    // Create one resident
    const residentResponse = await this.apiContext.post(`${this.baseURL}/api/v1/persons`, {
      data: {
        first_name: 'Conflict',
        last_name: 'Resident',
        email: 'e2e-conflict@test.mil',
        role: 'RESIDENT',
        pgy_level: 2,
      },
    });
    const residentId = (await residentResponse.json()).id;

    // Create two rotations
    const rotation1Response = await this.apiContext.post(`${this.baseURL}/api/v1/rotations`, {
      data: { name: 'Clinic', code: 'FMIT', hours_per_session: 4 },
    });
    const rotation1Id = (await rotation1Response.json()).id;

    const rotation2Response = await this.apiContext.post(`${this.baseURL}/api/v1/rotations`, {
      data: { name: 'Inpatient', code: 'INPT', hours_per_session: 12 },
    });
    const rotation2Id = (await rotation2Response.json()).id;

    // Create one block
    const today = new Date().toISOString().split('T')[0];
    const blockResponse = await this.apiContext.post(`${this.baseURL}/api/v1/blocks`, {
      data: { date: today, session: 'AM' },
    });
    const blockId = (await blockResponse.json()).id;

    // Create two assignments for the same resident/block (conflict!)
    const assignment1Response = await this.apiContext.post(`${this.baseURL}/api/v1/assignments`, {
      data: {
        person_id: residentId,
        block_id: blockId,
        rotation_id: rotation1Id,
        status: 'CONFIRMED',
      },
    });
    const assignment1Id = (await assignment1Response.json()).id;

    // This should trigger a conflict
    const assignment2Response = await this.apiContext.post(`${this.baseURL}/api/v1/assignments`, {
      data: {
        person_id: residentId,
        block_id: blockId,
        rotation_id: rotation2Id,
        status: 'CONFIRMED',
      },
      headers: {
        'X-Force-Create': 'true', // Force creation even with conflict
      },
    });
    const assignment2Id = assignment2Response.ok() ? (await assignment2Response.json()).id : null;

    return {
      name: 'conflict',
      residentIds: [residentId],
      facultyIds: [],
      blockIds: [blockId],
      rotationIds: [rotation1Id, rotation2Id],
      assignmentIds: assignment2Id ? [assignment1Id, assignment2Id] : [assignment1Id],
    };
  }

  /**
   * Create schedule with ACGME violations (80-hour rule)
   */
  async createACGMEViolatingSchedule(): Promise<ScheduleScenario> {
    // Create resident
    const residentResponse = await this.apiContext.post(`${this.baseURL}/api/v1/persons`, {
      data: {
        first_name: 'Overworked',
        last_name: 'Resident',
        email: 'e2e-overworked@test.mil',
        role: 'RESIDENT',
        pgy_level: 1,
      },
    });
    const residentId = (await residentResponse.json()).id;

    // Create high-hour rotation (12 hours per session)
    const rotationResponse = await this.apiContext.post(`${this.baseURL}/api/v1/rotations`, {
      data: {
        name: 'Night Call',
        code: 'CALL',
        hours_per_session: 12,
      },
    });
    const rotationId = (await rotationResponse.json()).id;

    // Create blocks for 7 consecutive days
    const blocks: string[] = [];
    const assignments: string[] = [];
    const today = new Date();

    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(date.getDate() + i);
      const dateStr = date.toISOString().split('T')[0];

      // Both AM and PM shifts = 24 hours/day
      const amBlockResponse = await this.apiContext.post(`${this.baseURL}/api/v1/blocks`, {
        data: { date: dateStr, session: 'AM' },
      });
      const amBlockId = (await amBlockResponse.json()).id;
      blocks.push(amBlockId);

      const pmBlockResponse = await this.apiContext.post(`${this.baseURL}/api/v1/blocks`, {
        data: { date: dateStr, session: 'PM' },
      });
      const pmBlockId = (await pmBlockResponse.json()).id;
      blocks.push(pmBlockId);

      // Assign both blocks to resident
      const amAssignmentResponse = await this.apiContext.post(`${this.baseURL}/api/v1/assignments`, {
        data: {
          person_id: residentId,
          block_id: amBlockId,
          rotation_id: rotationId,
          status: 'CONFIRMED',
        },
      });
      assignments.push((await amAssignmentResponse.json()).id);

      const pmAssignmentResponse = await this.apiContext.post(`${this.baseURL}/api/v1/assignments`, {
        data: {
          person_id: residentId,
          block_id: pmBlockId,
          rotation_id: rotationId,
          status: 'CONFIRMED',
        },
      });
      assignments.push((await pmAssignmentResponse.json()).id);
    }

    // This should violate 80-hour/week rule (7 days × 24 hours = 168 hours)

    return {
      name: 'acgme-violation',
      residentIds: [residentId],
      facultyIds: [],
      blockIds: blocks,
      rotationIds: [rotationId],
      assignmentIds: assignments,
    };
  }
}

/**
 * Extended test with schedule helpers
 */
export const test = base.extend<ScheduleContext>({
  scheduleHelper: async ({ request }, use) => {
    const baseURL = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';
    const helper = new ScheduleHelper(request, baseURL);
    await use(helper);
  },
});

export { expect } from '@playwright/test';
