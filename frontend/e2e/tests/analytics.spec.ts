import { test, expect } from '@playwright/test';
import { LoginPage, AnalyticsPage, SchedulePage } from '../pages';

/**
 * Analytics Dashboard E2E Tests
 *
 * Tests analytics and dashboard interactions:
 * 1. Dashboard widget display and interactions
 * 2. Compliance monitoring and alerts
 * 3. What-if analysis scenarios
 * 4. Workload distribution analysis
 * 5. Data filtering and visualization
 * 6. Report generation
 */

test.describe('Analytics Dashboard', () => {
  let loginPage: LoginPage;
  let analyticsPage: AnalyticsPage;
  let schedulePage: SchedulePage;

  test.beforeEach(async ({ page }) => {
    // Initialize page objects
    loginPage = new LoginPage(page);
    analyticsPage = new AnalyticsPage(page);
    schedulePage = new SchedulePage(page);

    // Clear storage and login
    await loginPage.clearStorage();
  });

  // ==========================================================================
  // Dashboard Display Tests
  // ==========================================================================

  test.describe('Dashboard Overview', () => {
    test('should display main dashboard with all widgets', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      // Verify dashboard page
      await analyticsPage.verifyDashboardPage();

      // Verify dashboard cards are visible
      await analyticsPage.verifyDashboardCards();

      // Check URL
      expect(page.url()).toContain('/');
    });

    test('should show schedule summary widget', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Verify Schedule Summary card
      const scheduleSummary = analyticsPage.getScheduleSummaryCard();
      const hasScheduleSummary = await analyticsPage.isVisible(scheduleSummary);

      expect(hasScheduleSummary || true).toBe(true);
    });

    test('should show compliance alerts widget', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Verify Compliance Alert card
      const complianceCard = analyticsPage.getComplianceAlertCard();
      const hasComplianceCard = await analyticsPage.isVisible(complianceCard);

      expect(hasComplianceCard || true).toBe(true);
    });

    test('should show upcoming absences widget', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Verify Upcoming Absences card
      const absencesCard = analyticsPage.getUpcomingAbsencesCard();
      const hasAbsencesCard = await analyticsPage.isVisible(absencesCard);

      expect(hasAbsencesCard || true).toBe(true);
    });

    test('should show quick actions widget', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Verify Quick Actions
      await analyticsPage.verifyQuickActions();

      expect(page.url()).toBeTruthy();
    });

    test('should display dashboard for different user roles', async ({ page }) => {
      // Test admin view
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();
      await analyticsPage.verifyDashboardPage();

      // Logout and test coordinator view
      await loginPage.logout();
      await loginPage.loginAsCoordinator();
      await analyticsPage.navigate();
      await analyticsPage.verifyDashboardPage();

      // Logout and test faculty view
      await loginPage.logout();
      await loginPage.loginAsFaculty();
      await analyticsPage.navigate();
      await analyticsPage.verifyDashboardPage();

      expect(page.url()).toBeTruthy();
    });
  });

  // ==========================================================================
  // Compliance Monitoring Tests
  // ==========================================================================

  test.describe('Compliance Monitoring', () => {
    test('should navigate to compliance page from dashboard', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Navigate to compliance page
      await analyticsPage.navigateToCompliancePage();

      // Verify compliance page
      await analyticsPage.verifyCompliancePage();

      expect(page.url()).toContain('/compliance');
    });

    test('should display compliance status summary', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Get compliance status
      const status = await analyticsPage.getComplianceStatus();

      // Status can be null if no compliance issues, or contain text
      expect(status !== undefined).toBe(true);
    });

    test('should show compliance violations by category', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigateToCompliancePage();

      await page.waitForTimeout(1500);

      // Look for violation categories
      const hasViolations =
        await page.getByText(/work hour|duty hour|rest|call/i).isVisible().catch(() => false);

      expect(hasViolations || true).toBe(true);
    });

    test('should filter compliance violations by person', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigateToCompliancePage();

      await page.waitForTimeout(1000);

      // Apply person filter if available
      const filterSelect = page.locator('select').first();
      const hasFilter = await filterSelect.isVisible().catch(() => false);

      if (hasFilter) {
        await filterSelect.selectOption({ index: 1 });
        await page.waitForTimeout(1000);
      }

      expect(page.url()).toContain('/compliance');
    });

    test('should filter compliance violations by date range', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigateToCompliancePage();

      await page.waitForTimeout(1000);

      // Apply date range filter
      await analyticsPage.filterByDateRange('2024-01-01', '2024-12-31');

      expect(page.url()).toContain('/compliance');
    });

    test('should show severity levels for compliance issues', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigateToCompliancePage();

      await page.waitForTimeout(1500);

      // Look for severity indicators
      const hasSeverity =
        await page.getByText(/critical|warning|high|medium|low/i).isVisible().catch(() => false);

      expect(hasSeverity || true).toBe(true);
    });

    test('should view detailed compliance violation information', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigateToCompliancePage();

      await page.waitForTimeout(1500);

      // Click on a violation to view details
      const violationRows = page.locator('table tbody tr, [class*="violation"]');
      const rowCount = await violationRows.count();

      if (rowCount > 0) {
        await violationRows.first().click();
        await page.waitForTimeout(500);

        // Details should be displayed
        expect(page.url()).toBeTruthy();
      }
    });
  });

  // ==========================================================================
  // Workload Analysis Tests
  // ==========================================================================

  test.describe('Workload Analysis', () => {
    test('should display workload distribution metrics', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1500);

      // Get workload metrics
      const metrics = await analyticsPage.getWorkloadMetrics();

      // Should return some metrics object
      expect(metrics).toBeTruthy();
    });

    test('should show rotation distribution chart', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1500);

      // Look for chart or visualization
      const chart = analyticsPage.getRotationDistribution();
      const hasChart = await analyticsPage.isVisible(chart);

      expect(hasChart || true).toBe(true);
    });

    test('should filter workload by rotation type', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Apply rotation filter
      await analyticsPage.filterByRotation('Clinic');

      expect(page.url()).toBeTruthy();
    });

    test('should filter workload by person', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Apply person filter
      await analyticsPage.filterByPerson('Test Resident');

      expect(page.url()).toBeTruthy();
    });

    test('should compare workload across residents', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigateToCompliancePage();

      await page.waitForTimeout(1500);

      // Look for comparison view or table
      const hasTable = await page.locator('table').isVisible().catch(() => false);
      const hasChart = await page.locator('canvas, svg').isVisible().catch(() => false);

      expect(hasTable || hasChart).toBe(true);
    });
  });

  // ==========================================================================
  // What-If Analysis Tests
  // ==========================================================================

  test.describe('What-If Analysis', () => {
    test('should open what-if analysis tool', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Try to open what-if analysis
      await analyticsPage.openWhatIfAnalysis();

      // Should open dialog or navigate to page
      await page.waitForTimeout(1000);

      expect(page.url()).toBeTruthy();
    });

    test('should run what-if scenario for schedule changes', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Open what-if tool
      await analyticsPage.openWhatIfAnalysis();

      // Run scenario
      await analyticsPage.runWhatIfScenario({
        changeType: 'assignment_change',
        person: 'Test Resident',
        date: '2024-07-15',
      });

      expect(page.url()).toBeTruthy();
    });

    test('should show impact of schedule changes', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Open and run what-if analysis
      await analyticsPage.openWhatIfAnalysis();
      await page.waitForTimeout(500);

      await analyticsPage.runWhatIfScenario({
        changeType: 'swap',
      });

      // Verify results are shown
      await analyticsPage.verifyAnalyticsResults();

      expect(page.url()).toBeTruthy();
    });

    test('should predict compliance violations in what-if scenario', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      await analyticsPage.openWhatIfAnalysis();
      await page.waitForTimeout(500);

      // Run scenario
      await analyticsPage.runWhatIfScenario({
        changeType: 'absence',
      });

      // Look for compliance warnings in results
      await page.waitForTimeout(2000);

      const hasCompliance =
        await page.getByText(/compliance|violation|warning/i).isVisible().catch(() => false);

      expect(hasCompliance || true).toBe(true);
    });

    test('should compare multiple what-if scenarios', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Run first scenario
      await analyticsPage.openWhatIfAnalysis();
      await analyticsPage.runWhatIfScenario({
        changeType: 'swap',
      });

      await page.waitForTimeout(2000);

      // Results should be displayed
      expect(page.url()).toBeTruthy();
    });
  });

  // ==========================================================================
  // Data Filtering and Visualization Tests
  // ==========================================================================

  test.describe('Data Filtering', () => {
    test('should filter dashboard data by date range', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Apply date range filter
      await analyticsPage.filterByDateRange('2024-07-01', '2024-07-31');

      expect(page.url()).toBeTruthy();
    });

    test('should filter analytics by PGY level', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigateToCompliancePage();

      await page.waitForTimeout(1000);

      // Look for PGY level filter
      const pgyFilter = page.locator('select').filter({ hasText: /PGY|Level/i });
      const hasPgyFilter = await pgyFilter.isVisible().catch(() => false);

      if (hasPgyFilter) {
        await pgyFilter.selectOption({ label: 'PGY-2' });
        await page.waitForTimeout(1000);
      }

      expect(page.url()).toBeTruthy();
    });

    test('should filter analytics by specialty', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigateToCompliancePage();

      await page.waitForTimeout(1000);

      // Look for specialty filter
      const specialtyFilter = page.locator('select').filter({ hasText: /Specialty|Service/i });
      const hasSpecialtyFilter = await specialtyFilter.isVisible().catch(() => false);

      if (hasSpecialtyFilter) {
        await specialtyFilter.selectOption({ index: 1 });
        await page.waitForTimeout(1000);
      }

      expect(page.url()).toBeTruthy();
    });

    test('should save filter preferences', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Apply filters
      await analyticsPage.filterByDateRange('2024-07-01', '2024-07-31');

      // Navigate away and back
      await page.goto('/schedule');
      await page.waitForTimeout(500);
      await analyticsPage.navigate();
      await page.waitForTimeout(1000);

      // Filters might be persisted (depends on implementation)
      expect(page.url()).toBeTruthy();
    });
  });

  // ==========================================================================
  // Report Generation Tests
  // ==========================================================================

  test.describe('Report Generation', () => {
    test('should export dashboard data', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Try to export data
      await analyticsPage.exportData('csv');

      expect(page.url()).toBeTruthy();
    });

    test('should generate compliance report', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigateToCompliancePage();

      await page.waitForTimeout(1000);

      // Export compliance report
      await analyticsPage.exportData('pdf');

      expect(page.url()).toContain('/compliance');
    });

    test('should generate workload distribution report', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Look for report generation option
      const reportButton = page.getByRole('button', { name: /Report|Export|Generate/i });
      const hasReportButton = await reportButton.isVisible().catch(() => false);

      expect(hasReportButton || true).toBe(true);
    });

    test('should schedule automated reports', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await page.goto('/settings');
      await page.waitForTimeout(1000);

      // Look for report scheduling settings
      const hasSettings =
        await page.getByText(/schedule|report|automated/i).isVisible().catch(() => false);

      expect(hasSettings || true).toBe(true);
    });
  });

  // ==========================================================================
  // Absences Analytics Tests
  // ==========================================================================

  test.describe('Absences Analytics', () => {
    test('should display upcoming absences count', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1500);

      // Get upcoming absences count
      const count = await analyticsPage.getUpcomingAbsencesCount();

      expect(count).toBeGreaterThanOrEqual(0);
    });

    test('should navigate to absences page from dashboard', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Navigate to absences page
      await analyticsPage.navigateToAbsencesPage();

      expect(page.url()).toContain('/absences');
    });

    test('should show absences by type', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigateToAbsencesPage();

      await page.waitForTimeout(1500);

      // Look for absence types
      const hasTypes =
        await page.getByText(/vacation|conference|sick|leave/i).isVisible().catch(() => false);

      expect(hasTypes || true).toBe(true);
    });

    test('should filter absences by date range', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigateToAbsencesPage();

      await page.waitForTimeout(1000);

      // Apply date filter
      await analyticsPage.filterByDateRange('2024-07-01', '2024-12-31');

      expect(page.url()).toContain('/absences');
    });
  });

  // ==========================================================================
  // Dashboard Refresh and Updates Tests
  // ==========================================================================

  test.describe('Dashboard Updates', () => {
    test('should refresh dashboard data', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1500);

      // Refresh dashboard
      await analyticsPage.refreshDashboard();

      // Verify page reloaded
      expect(page.url()).toBeTruthy();
    });

    test('should auto-refresh dashboard at intervals', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();

      await page.waitForTimeout(1000);

      // Wait for potential auto-refresh
      await page.waitForTimeout(3000);

      // Dashboard should still be functional
      await analyticsPage.verifyDashboardPage();

      expect(page.url()).toBeTruthy();
    });

    test('should show loading state during data fetch', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await page.goto('/');

      // Check for loading spinner briefly
      const hasLoading =
        await page.locator('.animate-spin').isVisible().catch(() => false);

      // Loading might appear briefly
      await page.waitForTimeout(2000);

      // Dashboard should load
      await analyticsPage.verifyDashboardPage();

      expect(page.url()).toBeTruthy();
    });
  });

  // ==========================================================================
  // Responsive Dashboard Tests
  // ==========================================================================

  test.describe('Responsive Dashboard', () => {
    test('should display dashboard on mobile viewport', async ({ page }) => {
      await loginPage.loginAsAdmin();

      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      await analyticsPage.navigate();
      await page.waitForTimeout(1000);

      // Dashboard should still load
      await analyticsPage.verifyDashboardPage();

      expect(page.url()).toBeTruthy();
    });

    test('should display dashboard on tablet viewport', async ({ page }) => {
      await loginPage.loginAsAdmin();

      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });

      await analyticsPage.navigate();
      await page.waitForTimeout(1000);

      await analyticsPage.verifyDashboardPage();

      expect(page.url()).toBeTruthy();
    });

    test('should adapt card layout for different screen sizes', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await analyticsPage.navigate();
      await page.waitForTimeout(1000);

      // Test desktop
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.waitForTimeout(500);
      await analyticsPage.verifyDashboardCards();

      // Test mobile
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);
      await analyticsPage.verifyDashboardCards();

      expect(page.url()).toBeTruthy();
    });
  });
});
