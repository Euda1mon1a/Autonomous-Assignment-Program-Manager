import { Page, expect, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * DashboardPage - Page object for dashboard/home page
 *
 * Handles dashboard navigation, widgets, and quick actions
 */
export class DashboardPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to dashboard
   */
  async navigate(): Promise<void> {
    await this.goto('/');
    await this.waitForURL('/', 10000);
  }

  /**
   * Verify dashboard page is loaded
   */
  async verifyDashboardPage(): Promise<void> {
    await expect(this.getHeading('Dashboard')).toBeVisible();
  }

  // ==========================================================================
  // Dashboard Widgets
  // ==========================================================================

  /**
   * Get Schedule Summary widget heading
   */
  getScheduleSummaryHeading(): Locator {
    return this.getHeading("This Week's Schedule");
  }

  /**
   * Get Compliance widget
   */
  getComplianceWidget(): Locator {
    return this.getText(/Compliance/i);
  }

  /**
   * Get Upcoming Absences widget
   */
  getUpcomingAbsencesWidget(): Locator {
    return this.getText(/Upcoming Absences/i);
  }

  /**
   * Get Quick Actions widget heading
   */
  getQuickActionsHeading(): Locator {
    return this.getHeading('Quick Actions');
  }

  /**
   * Verify all dashboard widgets are visible
   */
  async verifyAllWidgets(): Promise<void> {
    await expect(this.getScheduleSummaryHeading()).toBeVisible();
    await expect(this.getComplianceWidget()).toBeVisible();
    await expect(this.getUpcomingAbsencesWidget()).toBeVisible();
    await expect(this.getQuickActionsHeading()).toBeVisible();
  }

  // ==========================================================================
  // Schedule Summary Widget
  // ==========================================================================

  /**
   * Get View Full Schedule link
   */
  getViewFullScheduleLink(): Locator {
    return this.getLink(/View Full Schedule/i);
  }

  /**
   * Navigate to full schedule from dashboard
   */
  async goToFullSchedule(): Promise<void> {
    await this.getViewFullScheduleLink().click();
    await this.waitForURL('/schedule', 10000);
  }

  /**
   * Check if schedule data is present
   */
  async hasScheduleData(): Promise<boolean> {
    const hasData = await this.isVisible(this.getText(/residents scheduled/i));
    return hasData;
  }

  /**
   * Get "No schedule generated" message
   */
  async hasNoScheduleMessage(): Promise<boolean> {
    return await this.isVisible(this.getText(/No schedule generated/i));
  }

  // ==========================================================================
  // Quick Actions
  // ==========================================================================

  /**
   * Get Generate Schedule button
   */
  getGenerateScheduleButton(): Locator {
    return this.getButton('Generate Schedule');
  }

  /**
   * Get Add Person link
   */
  getAddPersonLink(): Locator {
    return this.getLink('Add Person');
  }

  /**
   * Get View Templates link
   */
  getViewTemplatesLink(): Locator {
    return this.getLink('View Templates');
  }

  /**
   * Get Compliance link
   */
  getComplianceLink(): Locator {
    return this.getLink('Compliance');
  }

  /**
   * Open Generate Schedule dialog
   */
  async openGenerateScheduleDialog(): Promise<void> {
    await this.getGenerateScheduleButton().click();
    await expect(this.getText(/Generate Schedule/i).first()).toBeVisible({ timeout: 5000 });
  }

  /**
   * Navigate to People page from Quick Actions
   */
  async goToPeoplePage(): Promise<void> {
    await this.getAddPersonLink().click();
    await this.waitForURL('/people', 10000);
  }

  /**
   * Navigate to Templates page from Quick Actions
   */
  async goToTemplatesPage(): Promise<void> {
    await this.getViewTemplatesLink().click();
    await this.waitForURL('/templates', 10000);
  }

  /**
   * Navigate to Compliance page from Quick Actions
   */
  async goToCompliancePage(): Promise<void> {
    await this.getComplianceLink().click();
    await this.waitForURL('/compliance', 10000);
  }

  // ==========================================================================
  // Navigation
  // ==========================================================================

  /**
   * Get navigation menu items
   */
  getNavigationMenu(): Locator {
    return this.page.locator('nav');
  }

  /**
   * Navigate to a specific page via sidebar/menu
   */
  async navigateToPage(pageName: 'Schedule' | 'People' | 'Absences' | 'Templates' | 'Compliance' | 'Analytics'): Promise<void> {
    const link = this.getLink(pageName);
    await link.click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Verify navigation menu is visible
   */
  async verifyNavigationVisible(): Promise<void> {
    await expect(this.getNavigationMenu()).toBeVisible();
  }

  // ==========================================================================
  // Compliance Widget
  // ==========================================================================

  /**
   * Get compliance status indicators
   */
  async getComplianceStatus(): Promise<string | null> {
    const greenStatus = await this.isVisible(this.getText(/All systems green|compliant/i));
    const warningStatus = await this.isVisible(this.getText(/warning|alert/i));
    const errorStatus = await this.isVisible(this.getText(/violation|error/i));

    if (greenStatus) return 'compliant';
    if (warningStatus) return 'warning';
    if (errorStatus) return 'error';
    return null;
  }

  // ==========================================================================
  // Upcoming Absences Widget
  // ==========================================================================

  /**
   * Get upcoming absences list
   */
  getUpcomingAbsencesList(): Locator {
    return this.page.locator('[data-testid="upcoming-absences-list"], ul').filter({
      has: this.page.getByText(/absence|vacation|medical/i)
    });
  }

  /**
   * Check if there are upcoming absences
   */
  async hasUpcomingAbsences(): Promise<boolean> {
    const list = this.getUpcomingAbsencesList();
    return await this.isVisible(list);
  }

  /**
   * Get count of upcoming absences
   */
  async getUpcomingAbsencesCount(): Promise<number> {
    const items = this.getUpcomingAbsencesList().locator('li');
    return await items.count();
  }

  // ==========================================================================
  // Pending Items
  // ==========================================================================

  /**
   * Get pending swaps count badge
   */
  async getPendingSwapsCount(): Promise<number> {
    const badge = this.page.locator('[class*="badge"]').filter({ hasText: /pending/i });
    const text = await badge.textContent().catch(() => '0');
    const match = text?.match(/\d+/);
    return match ? parseInt(match[0], 10) : 0;
  }

  /**
   * Navigate to pending swaps
   */
  async goToPendingSwaps(): Promise<void> {
    const pendingSwapsLink = this.page.getByText(/Pending.*Swap|Swap.*Request/i);
    if (await this.isVisible(pendingSwapsLink)) {
      await pendingSwapsLink.click();
      await this.page.waitForTimeout(500);
    }
  }

  // ==========================================================================
  // User Menu
  // ==========================================================================

  /**
   * Get user menu button
   */
  getUserMenuButton(): Locator {
    return this.page.getByRole('button', { name: /admin|coordinator|faculty|resident/i });
  }

  /**
   * Open user menu dropdown
   */
  async openUserMenu(): Promise<void> {
    await this.getUserMenuButton().click();
    await this.page.waitForTimeout(300);
  }

  /**
   * Logout from user menu
   */
  async logout(): Promise<void> {
    await this.openUserMenu();
    await this.clickButton('Logout');
    await this.waitForURL(/\/login/, 10000);
  }

  // ==========================================================================
  // Statistics and Summaries
  // ==========================================================================

  /**
   * Get statistics displayed on dashboard
   */
  async getDashboardStats(): Promise<{ [key: string]: string }> {
    const stats: { [key: string]: string } = {};

    // Try to find common stat elements
    const statElements = this.page.locator('[class*="stat"], [data-testid*="stat"]');
    const count = await statElements.count();

    for (let i = 0; i < count; i++) {
      const element = statElements.nth(i);
      const text = await element.textContent();
      if (text) {
        stats[`stat_${i}`] = text.trim();
      }
    }

    return stats;
  }

  /**
   * Verify dashboard loads without errors
   */
  async verifyDashboardLoaded(): Promise<void> {
    await this.verifyDashboardPage();
    await this.verifyAllWidgets();
    await this.verifyNavigationVisible();
  }
}
