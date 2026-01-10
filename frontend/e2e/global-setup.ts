import { chromium, FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Global Setup
 *
 * Runs once before all tests:
 * - Verify backend is accessible
 * - Create necessary directories
 * - Set up test database
 * - Pre-authenticate test users
 */

async function globalSetup(config: FullConfig) {
  console.log('\n🚀 Starting E2E Test Setup...\n');

  const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
  const apiURL = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';

  // 1. Check if servers are running
  console.log('✓ Checking server availability...');
  await checkServerHealth(baseURL, 'Frontend');
  await checkServerHealth(`${apiURL}/health`, 'Backend');

  // 2. Create necessary directories
  console.log('✓ Creating test directories...');
  const dirs = [
    'test-results',
    'test-results/screenshots',
    'test-results/videos',
    'test-results/traces',
    'snapshots',
    '.auth',
  ];

  for (const dir of dirs) {
    const dirPath = path.join(__dirname, dir);
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }

  // 3. Reset test database
  console.log('✓ Resetting test database...');
  try {
    const response = await fetch(`${apiURL}/api/v1/test/reset-database`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.warn('⚠ Could not reset database (non-critical)');
    }
  } catch (error) {
    console.warn('⚠ Database reset endpoint not available (non-critical)');
  }

  // 4. Seed test users
  console.log('✓ Seeding test users...');
  await seedTestUsers(apiURL);

  // 5. Pre-authenticate test users (for faster test execution)
  console.log('✓ Pre-authenticating test users...');
  await preAuthenticateUsers(baseURL);

  console.log('\n✅ E2E Test Setup Complete!\n');
}

/**
 * Check if server is healthy
 */
async function checkServerHealth(url: string, serverName: string): Promise<void> {
  const maxRetries = 30;
  const retryDelay = 2000; // 2 seconds

  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url);
      if (response.ok || response.status === 404) {
        console.log(`  ✓ ${serverName} is healthy at ${url}`);
        return;
      }
    } catch (error) {
      if (i === maxRetries - 1) {
        throw new Error(
          `❌ ${serverName} is not accessible at ${url}. Please start the server first.`
        );
      }
      console.log(`  ⏳ Waiting for ${serverName}... (${i + 1}/${maxRetries})`);
      await new Promise((resolve) => setTimeout(resolve, retryDelay));
    }
  }
}

/**
 * Seed test users in database
 */
async function seedTestUsers(apiURL: string): Promise<void> {
  const testUsers = [
    {
      email: 'admin@test.mil',
      password: 'TestPassword123!',
      role: 'ADMIN',
      firstName: 'Admin',
      lastName: 'User',
      id: 'test-admin-001',
    },
    {
      email: 'coordinator@test.mil',
      password: 'TestPassword123!',
      role: 'COORDINATOR',
      firstName: 'Coordinator',
      lastName: 'User',
      id: 'test-coord-001',
    },
    {
      email: 'faculty@test.mil',
      password: 'TestPassword123!',
      role: 'FACULTY',
      firstName: 'Faculty',
      lastName: 'Member',
      id: 'test-faculty-001',
    },
    {
      email: 'resident@test.mil',
      password: 'TestPassword123!',
      role: 'RESIDENT',
      firstName: 'PGY2',
      lastName: 'Resident',
      id: 'test-resident-001',
    },
  ];

  for (const user of testUsers) {
    try {
      const response = await fetch(`${apiURL}/api/v1/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(user),
      });

      if (response.ok) {
        console.log(`  ✓ Created test user: ${user.email}`);
      } else if (response.status === 409) {
        console.log(`  ℹ Test user already exists: ${user.email}`);
      } else {
        console.warn(`  ⚠ Failed to create user ${user.email}: ${response.statusText}`);
      }
    } catch (error) {
      console.warn(`  ⚠ Error creating user ${user.email}:`, error);
    }
  }
}

/**
 * Pre-authenticate test users and save auth state
 */
async function preAuthenticateUsers(baseURL: string): Promise<void> {
  const browser = await chromium.launch();
  const authStateDir = path.join(__dirname, '.auth');

  const users = [
    { email: 'admin@test.mil', password: 'TestPassword123!', file: 'admin.json' },
    { email: 'coordinator@test.mil', password: 'TestPassword123!', file: 'coordinator.json' },
    { email: 'faculty@test.mil', password: 'TestPassword123!', file: 'faculty.json' },
    { email: 'resident@test.mil', password: 'TestPassword123!', file: 'resident.json' },
  ];

  for (const user of users) {
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
      // Navigate to login page
      await page.goto(`${baseURL}/login`);

      // Fill login form
      await page.fill('input[name="email"]', user.email);
      await page.fill('input[name="password"]', user.password);
      await page.click('button[type="submit"]');

      // Wait for redirect to dashboard
      await page.waitForURL(/\/(dashboard|schedule)/, { timeout: 10000 });

      // Save auth state
      const authStatePath = path.join(authStateDir, user.file);
      await context.storageState({ path: authStatePath });

      console.log(`  ✓ Pre-authenticated: ${user.email}`);
    } catch (error) {
      console.warn(`  ⚠ Failed to pre-authenticate ${user.email}:`, error);
    } finally {
      await page.close();
      await context.close();
    }
  }

  await browser.close();
}

export default globalSetup;
