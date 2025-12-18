import { Page, expect, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * SchedulePage - Page object for schedule management
 *
 * Handles schedule viewing, navigation, and management operations
 */
export class SchedulePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to schedule page
   */
  async navigate(): Promise<void> {
    await this.goto('/schedule');
    await this.waitForURL('/schedule', 10000);
  }

  /**
   * Verify schedule page is loaded
   */
  async verifySchedulePage(): Promise<void> {
    await expect(this.getHeading('Schedule')).toBeVisible();
    await expect(this.getText('View and manage rotation assignments')).toBeVisible();
  }

  /**
   * Get navigation buttons
   */
  getPreviousBlockButton(): Locator {
    return this.getButton('Previous Block');
  }

  getNextBlockButton(): Locator {
    return this.getButton('Next Block');
  }

  getTodayButton(): Locator {
    return this.getButton('Today');
  }

  getThisBlockButton(): Locator {
    return this.getButton('This Block');
  }

  /**
   * Navigate to previous block
   */
  async goToPreviousBlock(): Promise<void> {
    await this.getPreviousBlockButton().click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Navigate to next block
   */
  async goToNextBlock(): Promise<void> {
    await this.getNextBlockButton().click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Jump to today
   */
  async goToToday(): Promise<void> {
    await this.getTodayButton().click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Jump to current block
   */
  async goToThisBlock(): Promise<void> {
    await this.getThisBlockButton().click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Get date range inputs
   */
  getStartDateInput(): Locator {
    return this.getInput('Start date');
  }

  getEndDateInput(): Locator {
    return this.getInput('End date');
  }

  /**
   * Get current start date
   */
  async getStartDate(): Promise<string> {
    return await this.getStartDateInput().inputValue();
  }

  /**
   * Get current end date
   */
  async getEndDate(): Promise<string> {
    return await this.getEndDateInput().inputValue();
  }

  /**
   * Set date range
   */
  async setDateRange(startDate: string, endDate?: string): Promise<void> {
    await this.getStartDateInput().fill(startDate);
    await this.getStartDateInput().blur();
    if (endDate) {
      await this.getEndDateInput().fill(endDate);
      await this.getEndDateInput().blur();
    }
    await this.page.waitForTimeout(500);
  }

  /**
   * Get schedule table
   */
  getScheduleTable(): Locator {
    return this.page.locator('table');
  }

  /**
   * Get schedule cells
   */
  getScheduleCells(): Locator {
    return this.page.locator('td[class*="bg-"]').filter({
      hasNot: this.page.locator('[class*="bg-gray-50"]')
    });
  }

  /**
   * Verify schedule has data
   */
  async hasScheduleData(): Promise<boolean> {
    const cellCount = await this.getScheduleCells().count();
    return cellCount > 0;
  }

  /**
   * Hover over schedule cell
   */
  async hoverScheduleCell(index: number = 0): Promise<void> {
    await this.getScheduleCells().nth(index).hover();
    await this.page.waitForTimeout(500);
  }

  /**
   * Click schedule cell
   */
  async clickScheduleCell(index: number = 0): Promise<void> {
    await this.getScheduleCells().nth(index).click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Open Generate Schedule dialog from dashboard
   */
  async openGenerateScheduleDialog(): Promise<void> {
    await this.goto('/');
    await this.waitForURL('/', 10000);
    await this.clickButton('Generate Schedule');
    await expect(this.getHeading('Generate Schedule')).toBeVisible({ timeout: 5000 });
  }

  /**
   * Verify Generate Schedule dialog fields
   */
  async verifyGenerateScheduleDialog(): Promise<void> {
    await expect(this.getText('Start Date')).toBeVisible();
    await expect(this.getText('End Date')).toBeVisible();
    await expect(this.getText('Algorithm')).toBeVisible();
    await expect(this.getButton('Cancel')).toBeVisible();
    await expect(this.getButton('Generate Schedule')).toBeVisible();
  }

  /**
   * Fill Generate Schedule form
   */
  async fillGenerateScheduleForm(data: {
    startDate?: string;
    endDate?: string;
    algorithm?: string;
  }): Promise<void> {
    if (data.startDate) {
      const startInput = this.page.locator('input[name="start_date"], input[id*="start"]').first();
      await startInput.fill(data.startDate);
    }
    if (data.endDate) {
      const endInput = this.page.locator('input[name="end_date"], input[id*="end"]').first();
      await endInput.fill(data.endDate);
    }
    if (data.algorithm) {
      const algorithmSelect = this.page.locator('select').filter({ hasText: /Greedy|CP-SAT|PuLP|Hybrid/i });
      await algorithmSelect.selectOption(data.algorithm);
    }
  }

  /**
   * Submit Generate Schedule form
   */
  async submitGenerateSchedule(): Promise<void> {
    await this.clickButton('Generate Schedule');
    await this.page.waitForTimeout(1000);
  }

  /**
   * Verify legend is visible
   */
  async verifyLegendVisible(): Promise<void> {
    await expect(this.getText('Legend:')).toBeVisible();
    await expect(this.getText('Clinic')).toBeVisible();
    await expect(this.getText('Inpatient')).toBeVisible();
  }
}
