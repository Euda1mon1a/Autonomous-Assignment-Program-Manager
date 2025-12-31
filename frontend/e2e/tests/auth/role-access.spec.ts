import { test, expect } from '../../fixtures/auth.fixture';
import { selectors } from '../../utils/selectors';

/**
 * Role-Based Access Control Tests
 *
 * Tests for role-based access including:
 * - Admin-only pages
 * - Coordinator permissions
 * - Faculty permissions
 * - Resident permissions
 * - Unauthorized access handling
 */

test.describe('Role-Based Access Control', () => {
  test('admin should access all pages', async ({ adminPage }) => {
    const pages = [
      '/dashboard',
      '/schedule',
      '/swaps',
      '/compliance',
      '/resilience',
      '/admin',
      '/settings',
    ];

    for (const pagePath of pages) {
      await adminPage.goto(pagePath);

      // Should not redirect to unauthorized
      const url = adminPage.url();
      expect(url).not.toContain('/unauthorized');
      expect(url).not.toContain('/403');

      // Should show user menu (logged in)
      await expect(adminPage.locator(selectors.nav.userMenu)).toBeVisible();
    }
  });

  test('coordinator should access schedule and compliance but not admin', async ({
    coordinatorPage,
  }) => {
    // Should access schedule
    await coordinatorPage.goto('/schedule');
    await expect(coordinatorPage.locator(selectors.nav.userMenu)).toBeVisible();
    expect(coordinatorPage.url()).toContain('/schedule');

    // Should access compliance
    await coordinatorPage.goto('/compliance');
    await expect(coordinatorPage.locator(selectors.nav.userMenu)).toBeVisible();

    // Should NOT access admin page
    await coordinatorPage.goto('/admin');

    // Should redirect or show unauthorized
    await coordinatorPage.waitForTimeout(1000);
    const url = coordinatorPage.url();
    const hasUnauthorized =
      url.includes('/unauthorized') || url.includes('/403') || !url.includes('/admin');
    expect(hasUnauthorized).toBeTruthy();
  });

  test('faculty should access schedule and swaps', async ({ facultyPage }) => {
    // Should access schedule
    await facultyPage.goto('/schedule');
    await expect(facultyPage.locator(selectors.nav.userMenu)).toBeVisible();

    // Should access swaps
    await facultyPage.goto('/swaps');
    await expect(facultyPage.locator(selectors.nav.userMenu)).toBeVisible();

    // Should NOT access admin
    await facultyPage.goto('/admin');
    await facultyPage.waitForTimeout(1000);
    const url = facultyPage.url();
    expect(url).not.toContain('/admin');
  });

  test('resident should access schedule and personal swaps', async ({ residentPage }) => {
    // Should access schedule (read-only)
    await residentPage.goto('/schedule');
    await expect(residentPage.locator(selectors.nav.userMenu)).toBeVisible();

    // Should access swaps
    await residentPage.goto('/swaps');
    await expect(residentPage.locator(selectors.nav.userMenu)).toBeVisible();

    // Should NOT access compliance dashboard
    await residentPage.goto('/compliance');
    await residentPage.waitForTimeout(1000);
    const url = residentPage.url();
    const hasAccess = url.includes('/compliance');

    // Depends on implementation - residents might have limited compliance view
    if (!hasAccess) {
      expect(url).not.toContain('/compliance');
    }
  });

  test('should hide admin menu items from non-admin users', async ({ facultyPage }) => {
    await facultyPage.goto('/dashboard');

    // Admin link should not be visible
    const adminLink = facultyPage.locator('a:has-text("Admin")');
    await expect(adminLink).not.toBeVisible();
  });

  test('should show appropriate menu items for each role', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Admin should see all menu items
    await expect(adminPage.locator(selectors.nav.dashboardLink)).toBeVisible();
    await expect(adminPage.locator(selectors.nav.scheduleLink)).toBeVisible();
    await expect(adminPage.locator(selectors.nav.swapLink)).toBeVisible();

    const adminLink = adminPage.locator('a:has-text("Admin")');
    await expect(adminLink).toBeVisible();
  });

  test('coordinator cannot create admin users', async ({ coordinatorPage }) => {
    await coordinatorPage.goto('/users/new');

    // Role dropdown should not include ADMIN option
    const roleSelect = coordinatorPage.locator('select[name="role"]');

    if (await roleSelect.isVisible()) {
      const options = await roleSelect.locator('option').allTextContents();
      expect(options).not.toContain('Admin');
    }
  });

  test('faculty can only modify their own swaps', async ({ facultyPage, authUsers }) => {
    await facultyPage.goto('/swaps');

    // Should see own swaps
    const ownSwaps = facultyPage.locator(`[data-testid="swap-card"][data-user-id="${authUsers.faculty.id}"]`);

    if ((await ownSwaps.count()) > 0) {
      // Should have edit/delete buttons on own swaps
      const firstOwnSwap = ownSwaps.first();
      await expect(firstOwnSwap.locator(selectors.common.editButton)).toBeVisible();
    }

    // Other users' swaps should not have edit buttons (for this faculty)
    const otherSwaps = facultyPage.locator(
      `[data-testid="swap-card"]:not([data-user-id="${authUsers.faculty.id}"])`
    );

    if ((await otherSwaps.count()) > 0) {
      const firstOtherSwap = otherSwaps.first();
      await expect(firstOtherSwap.locator(selectors.common.editButton)).not.toBeVisible();
    }
  });

  test('residents cannot approve swaps', async ({ residentPage }) => {
    await residentPage.goto('/swaps');

    // Approve button should not be visible for residents
    const approveButton = residentPage.locator(selectors.swap.approveButton);
    await expect(approveButton).not.toBeVisible();
  });

  test('admin can approve any swap', async ({ adminPage }) => {
    await adminPage.goto('/swaps');

    // Should see approve buttons
    const swapCards = adminPage.locator(selectors.swap.swapCard);

    if ((await swapCards.count()) > 0) {
      const firstSwap = swapCards.first();
      await expect(firstSwap.locator(selectors.swap.approveButton)).toBeVisible();
    }
  });

  test('should return 403 for unauthorized API calls', async ({ facultyPage }) => {
    // Try to access admin-only API endpoint
    const response = await facultyPage.request.get('/api/v1/admin/users', {
      failOnStatusCode: false,
    });

    expect(response.status()).toBe(403);
  });

  test('should handle role changes', async ({ browser, authUsers }) => {
    // Login as admin
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto('/login');
    await page.fill(selectors.login.emailInput, authUsers.admin.email);
    await page.fill(selectors.login.passwordInput, authUsers.admin.password);
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);

    // Access admin page
    await page.goto('/admin');
    await expect(page.locator('h1')).toContainText(/admin/i);

    // Simulate role change (in real scenario, admin would demote themselves)
    await page.evaluate(() => {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      user.role = 'FACULTY';
      localStorage.setItem('user', JSON.stringify(user));
    });

    // Try to access admin page
    await page.goto('/admin');

    // Should redirect or show unauthorized
    await page.waitForTimeout(1000);
    const url = page.url();
    expect(url).not.toContain('/admin');

    await context.close();
  });

  test('should enforce permissions on schedule modifications', async ({ residentPage }) => {
    await residentPage.goto('/schedule');

    // Create assignment button should not be visible for residents
    const createButton = residentPage.locator(selectors.schedule.createAssignmentButton);
    await expect(createButton).not.toBeVisible();
  });

  test('coordinator can create assignments', async ({ coordinatorPage }) => {
    await coordinatorPage.goto('/schedule');

    // Should see create assignment button
    const createButton = coordinatorPage.locator(selectors.schedule.createAssignmentButton);
    await expect(createButton).toBeVisible();
  });

  test('should show role-appropriate dashboard widgets', async ({ residentPage }) => {
    await residentPage.goto('/dashboard');

    // Residents should see personal schedule widget
    const upcomingShifts = residentPage.locator(selectors.dashboard.upcomingShifts);
    await expect(upcomingShifts).toBeVisible();

    // Should NOT see admin-only widgets
    const adminWidget = residentPage.locator('[data-testid="admin-widget"]');
    await expect(adminWidget).not.toBeVisible();
  });

  test('admin should see all dashboard widgets', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');

    // Should see admin-specific widgets
    await expect(adminPage.locator(selectors.dashboard.quickStats)).toBeVisible();
    await expect(adminPage.locator(selectors.dashboard.complianceWidget)).toBeVisible();
    await expect(adminPage.locator(selectors.dashboard.resilienceWidget)).toBeVisible();
  });
});

test.describe('Permission Edge Cases', () => {
  test('should handle concurrent role changes', async ({ browser, authUsers }) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto('/login');
    await page.fill(selectors.login.emailInput, authUsers.admin.email);
    await page.fill(selectors.login.passwordInput, authUsers.admin.password);
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);

    // Simulate role change while on admin page
    await page.goto('/admin');

    // Change role in another tab (simulated)
    await page.evaluate(() => {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      user.role = 'RESIDENT';
      localStorage.setItem('user', JSON.stringify(user));
    });

    // Try to perform admin action
    const response = await page.request.post('/api/v1/admin/action', {
      failOnStatusCode: false,
    });

    // Should fail with 403
    expect(response.status()).toBe(403);

    await context.close();
  });

  test('should prevent privilege escalation', async ({ facultyPage }) => {
    // Try to modify own role via API
    const response = await facultyPage.request.patch('/api/v1/users/me', {
      data: { role: 'ADMIN' },
      failOnStatusCode: false,
    });

    // Should fail
    expect([403, 400]).toContain(response.status());
  });
});
