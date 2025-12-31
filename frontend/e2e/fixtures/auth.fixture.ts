import { test as base, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Authentication Fixtures for E2E Tests
 *
 * Provides authenticated contexts for different user roles:
 * - Admin
 * - Coordinator
 * - Faculty
 * - Resident
 */

export type AuthUser = {
  email: string;
  password: string;
  role: string;
  id: string;
  firstName: string;
  lastName: string;
};

export type AuthContext = {
  adminPage: Page;
  coordinatorPage: Page;
  facultyPage: Page;
  residentPage: Page;
  authUsers: {
    admin: AuthUser;
    coordinator: AuthUser;
    faculty: AuthUser;
    resident: AuthUser;
  };
};

const STORAGE_STATE_DIR = path.join(__dirname, '../.auth');

// Test users for different roles
const TEST_USERS = {
  admin: {
    email: 'admin@test.mil',
    password: 'TestPassword123!',
    role: 'ADMIN',
    id: 'test-admin-001',
    firstName: 'Admin',
    lastName: 'User',
  },
  coordinator: {
    email: 'coordinator@test.mil',
    password: 'TestPassword123!',
    role: 'COORDINATOR',
    id: 'test-coord-001',
    firstName: 'Coordinator',
    lastName: 'User',
  },
  faculty: {
    email: 'faculty@test.mil',
    password: 'TestPassword123!',
    role: 'FACULTY',
    id: 'test-faculty-001',
    firstName: 'Faculty',
    lastName: 'Member',
  },
  resident: {
    email: 'resident@test.mil',
    password: 'TestPassword123!',
    role: 'RESIDENT',
    id: 'test-resident-001',
    firstName: 'PGY2',
    lastName: 'Resident',
  },
};

/**
 * Login helper function
 */
async function login(page: Page, user: AuthUser): Promise<void> {
  await page.goto('/login');
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
  await page.click('button[type="submit"]');

  // Wait for redirect to dashboard
  await page.waitForURL(/\/(dashboard|schedule)/);

  // Verify login success by checking for user menu or logout button
  await page.waitForSelector('[data-testid="user-menu"]', { timeout: 5000 });
}

/**
 * Save authentication state to file
 */
async function saveAuthState(page: Page, filename: string): Promise<void> {
  if (!fs.existsSync(STORAGE_STATE_DIR)) {
    fs.mkdirSync(STORAGE_STATE_DIR, { recursive: true });
  }

  const storagePath = path.join(STORAGE_STATE_DIR, filename);
  await page.context().storageState({ path: storagePath });
}

/**
 * Load authentication state from file
 */
function getAuthStatePath(role: string): string {
  return path.join(STORAGE_STATE_DIR, `${role}.json`);
}

/**
 * Extended test with authenticated contexts
 */
export const test = base.extend<AuthContext>({
  authUsers: async ({}, use) => {
    await use(TEST_USERS);
  },

  adminPage: async ({ browser, authUsers }, use) => {
    const storagePath = getAuthStatePath('admin');

    let context;
    if (fs.existsSync(storagePath)) {
      // Reuse existing auth state
      context = await browser.newContext({ storageState: storagePath });
    } else {
      // Create new auth state
      context = await browser.newContext();
      const page = await context.newPage();
      await login(page, authUsers.admin);
      await saveAuthState(page, 'admin.json');
      await page.close();
      context = await browser.newContext({ storageState: storagePath });
    }

    const page = await context.newPage();
    await use(page);
    await context.close();
  },

  coordinatorPage: async ({ browser, authUsers }, use) => {
    const storagePath = getAuthStatePath('coordinator');

    let context;
    if (fs.existsSync(storagePath)) {
      context = await browser.newContext({ storageState: storagePath });
    } else {
      context = await browser.newContext();
      const page = await context.newPage();
      await login(page, authUsers.coordinator);
      await saveAuthState(page, 'coordinator.json');
      await page.close();
      context = await browser.newContext({ storageState: storagePath });
    }

    const page = await context.newPage();
    await use(page);
    await context.close();
  },

  facultyPage: async ({ browser, authUsers }, use) => {
    const storagePath = getAuthStatePath('faculty');

    let context;
    if (fs.existsSync(storagePath)) {
      context = await browser.newContext({ storageState: storagePath });
    } else {
      context = await browser.newContext();
      const page = await context.newPage();
      await login(page, authUsers.faculty);
      await saveAuthState(page, 'faculty.json');
      await page.close();
      context = await browser.newContext({ storageState: storagePath });
    }

    const page = await context.newPage();
    await use(page);
    await context.close();
  },

  residentPage: async ({ browser, authUsers }, use) => {
    const storagePath = getAuthStatePath('resident');

    let context;
    if (fs.existsSync(storagePath)) {
      context = await browser.newContext({ storageState: storagePath });
    } else {
      context = await browser.newContext();
      const page = await context.newPage();
      await login(page, authUsers.resident);
      await saveAuthState(page, 'resident.json');
      await page.close();
      context = await browser.newContext({ storageState: storagePath });
    }

    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export { expect } from '@playwright/test';

/**
 * Clean up auth state files
 */
export function cleanAuthState(): void {
  if (fs.existsSync(STORAGE_STATE_DIR)) {
    fs.rmSync(STORAGE_STATE_DIR, { recursive: true, force: true });
  }
}

/**
 * Verify user is authenticated
 */
export async function verifyAuthenticated(page: Page): Promise<void> {
  await page.waitForSelector('[data-testid="user-menu"]', { timeout: 5000 });
}

/**
 * Logout helper
 */
export async function logout(page: Page): Promise<void> {
  await page.click('[data-testid="user-menu"]');
  await page.click('button:has-text("Logout")');
  await page.waitForURL('/login');
}
