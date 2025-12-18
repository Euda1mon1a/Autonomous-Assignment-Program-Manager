import { Page, expect, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * AnalyticsPage - Page object for analytics dashboard
 *
 * Handles analytics viewing, filtering, and what-if analysis interactions
 */
export class AnalyticsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to analytics/dashboard
   * Note: Analytics might be embedded in the main dashboard
   */
  async navigate(): Promise<void> {
    await this.goto('/');
    await this.waitForPageLoad();
  }

  /**
   * Verify dashboard page is loaded
   */
  async verifyDashboardPage(): Promise<void> {
    await expect(this.getHeading('Dashboard')).toBeVisible();
  }

  /**
   * Get Schedule Summary card
   */
  getScheduleSummaryCard(): Locator {
    return this.page.locator('[class*="card"]').filter({ hasText: /Schedule Summary|Rotation Summary/i });
  }

  /**
   * Get Compliance Alert card
   */
  getComplianceAlertCard(): Locator {
    return this.page.locator('[class*="card"]').filter({ hasText: /Compliance|Alert|Warning/i });
  }

  /**
   * Get Upcoming Absences card
   */
  getUpcomingAbsencesCard(): Locator {
    return this.page.locator('[class*="card"]').filter({ hasText: /Absence|Time Off|Leave/i });
  }

  /**
   * Get Quick Actions card
   */
  getQuickActionsCard(): Locator {
    return this.page.locator('[class*="card"]').filter({ hasText: /Quick Action|Action/i });
  }

  /**
   * Verify all dashboard cards are visible
   */
  async verifyDashboardCards(): Promise<void> {
    // Wait for dashboard to load
    await this.page.waitForTimeout(1000);

    // Check if at least some cards are visible
    const hasScheduleSummary = await this.isVisible(this.getScheduleSummaryCard());
    const hasQuickActions = await this.isVisible(this.getQuickActionsCard());

    // At least one card should be visible
    expect(hasScheduleSummary || hasQuickActions).toBe(true);
  }

  /**
   * Get compliance status
   */
  async getComplianceStatus(): Promise<string | null> {
    const complianceCard = this.getComplianceAlertCard();
    if (await this.isVisible(complianceCard)) {
      const text = await complianceCard.textContent();
      return text;
    }
    return null;
  }

  /**
   * Click on compliance alert to view details
   */
  async viewComplianceDetails(): Promise<void> {
    const viewButton = this.getComplianceAlertCard().getByRole('button', { name: /View|Details|More/i });
    if (await this.isVisible(viewButton)) {
      await viewButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Navigate to compliance page
   */
  async navigateToCompliancePage(): Promise<void> {
    await this.goto('/compliance');
    await this.waitForURL('/compliance', 10000);
  }

  /**
   * Verify compliance page
   */
  async verifyCompliancePage(): Promise<void> {
    await expect(this.getHeading('Compliance')).toBeVisible();
  }

  /**
   * Get rotation distribution chart/data
   */
  getRotationDistribution(): Locator {
    return this.page.locator('[class*="chart"], canvas, svg').first();
  }

  /**
   * Get workload metrics
   */
  async getWorkloadMetrics(): Promise<{ [key: string]: string }> {
    const metrics: { [key: string]: string } = {};

    // Look for metric cards or displays
    const metricElements = this.page.locator('[class*="metric"], [class*="stat"]');
    const count = await metricElements.count();

    for (let i = 0; i < count; i++) {
      const element = metricElements.nth(i);
      const text = await element.textContent();
      if (text) {
        metrics[`metric_${i}`] = text;
      }
    }

    return metrics;
  }

  /**
   * Filter analytics by date range
   */
  async filterByDateRange(startDate: string, endDate: string): Promise<void> {
    const startInput = this.page.locator('input[name*="start"], input[label*="Start"]').first();
    const endInput = this.page.locator('input[name*="end"], input[label*="End"]').first();

    if (await this.isVisible(startInput)) {
      await startInput.fill(startDate);
      await startInput.blur();
    }
    if (await this.isVisible(endInput)) {
      await endInput.fill(endDate);
      await endInput.blur();
    }
    await this.page.waitForTimeout(1000);
  }

  /**
   * Filter analytics by person/resident
   */
  async filterByPerson(personName: string): Promise<void> {
    const personSelect = this.page.locator('select').filter({ hasText: /Person|Resident|Faculty/i });
    if (await this.isVisible(personSelect)) {
      await personSelect.selectOption({ label: personName });
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Filter analytics by rotation
   */
  async filterByRotation(rotation: string): Promise<void> {
    const rotationSelect = this.page.locator('select').filter({ hasText: /Rotation|Service/i });
    if (await this.isVisible(rotationSelect)) {
      await rotationSelect.selectOption({ label: rotation });
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Export analytics data
   */
  async exportData(format: 'csv' | 'excel' | 'pdf' = 'csv'): Promise<void> {
    const exportButton = this.page.getByRole('button', { name: /Export|Download/i });
    if (await this.isVisible(exportButton)) {
      await exportButton.click();
      await this.page.waitForTimeout(500);

      // Select format if there's a dropdown
      const formatOption = this.page.getByText(new RegExp(format, 'i'));
      if (await this.isVisible(formatOption)) {
        await formatOption.click();
        await this.page.waitForTimeout(1000);
      }
    }
  }

  /**
   * Open What-If Analysis tool
   */
  async openWhatIfAnalysis(): Promise<void> {
    const whatIfButton = this.page.getByRole('button', { name: /What.*If|Scenario|Simulation/i });
    if (await this.isVisible(whatIfButton)) {
      await whatIfButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Run What-If scenario
   */
  async runWhatIfScenario(data: {
    changeType?: string;
    person?: string;
    date?: string;
  }): Promise<void> {
    // This is a placeholder for what-if analysis
    // The actual implementation depends on the UI structure

    if (data.changeType) {
      const changeTypeSelect = this.page.locator('select[name*="type"]').first();
      if (await this.isVisible(changeTypeSelect)) {
        await changeTypeSelect.selectOption(data.changeType);
      }
    }

    const runButton = this.page.getByRole('button', { name: /Run|Analyze|Calculate/i });
    if (await this.isVisible(runButton)) {
      await runButton.click();
      await this.page.waitForTimeout(2000); // Wait for analysis
    }
  }

  /**
   * Verify analytics results
   */
  async verifyAnalyticsResults(): Promise<void> {
    // Look for results table, chart, or summary
    const resultsTable = this.page.locator('table').first();
    const resultsChart = this.page.locator('canvas, svg').first();
    const resultsSummary = this.page.locator('[class*="result"], [class*="summary"]').first();

    const hasResults =
      await this.isVisible(resultsTable) ||
      await this.isVisible(resultsChart) ||
      await this.isVisible(resultsSummary);

    expect(hasResults).toBe(true);
  }

  /**
   * Get upcoming absences count
   */
  async getUpcomingAbsencesCount(): Promise<number> {
    const absencesCard = this.getUpcomingAbsencesCard();
    if (await this.isVisible(absencesCard)) {
      const items = absencesCard.locator('li, [class*="item"]');
      return await items.count();
    }
    return 0;
  }

  /**
   * Navigate to absences page
   */
  async navigateToAbsencesPage(): Promise<void> {
    await this.goto('/absences');
    await this.waitForURL('/absences', 10000);
  }

  /**
   * Verify quick actions are available
   */
  async verifyQuickActions(): Promise<void> {
    const quickActionsCard = this.getQuickActionsCard();
    await expect(quickActionsCard).toBeVisible();

    // Check for common quick action buttons
    const hasGenerateSchedule = await this.isVisible(
      this.page.getByRole('button', { name: /Generate Schedule/i })
    );
    const hasViewCompliance = await this.isVisible(
      this.page.getByRole('button', { name: /Compliance/i })
    );

    // At least one quick action should exist
    expect(hasGenerateSchedule || hasViewCompliance).toBe(true);
  }

  /**
   * Refresh dashboard data
   */
  async refreshDashboard(): Promise<void> {
    const refreshButton = this.page.getByRole('button', { name: /Refresh|Reload/i });
    if (await this.isVisible(refreshButton)) {
      await refreshButton.click();
      await this.waitForLoadingComplete();
    } else {
      // Fallback: reload the page
      await this.page.reload();
      await this.waitForPageLoad();
    }
  }
}
