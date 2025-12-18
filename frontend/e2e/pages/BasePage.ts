import { Page, Locator, expect } from '@playwright/test';

/**
 * BasePage - Common functionality for all page objects
 *
 * Provides shared methods for navigation, waiting, and interactions
 * that are used across all page objects in the test suite.
 */
export class BasePage {
  protected page: Page;
  protected baseURL: string;

  constructor(page: Page, baseURL: string = 'http://localhost:3000') {
    this.page = page;
    this.baseURL = baseURL;
  }

  /**
   * Navigate to a specific path
   */
  async goto(path: string): Promise<void> {
    await this.page.goto(`${this.baseURL}${path}`);
  }

  /**
   * Wait for the page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle', { timeout: 10000 });
  }

  /**
   * Wait for loading spinner to disappear
   */
  async waitForLoadingComplete(): Promise<void> {
    const loadingSpinner = this.page.locator('.animate-spin');
    if (await loadingSpinner.isVisible().catch(() => false)) {
      await loadingSpinner.waitFor({ state: 'hidden', timeout: 10000 });
    }
    await this.page.waitForLoadState('networkidle', { timeout: 10000 });
  }

  /**
   * Get a button by its name
   */
  getButton(name: string | RegExp): Locator {
    return this.page.getByRole('button', { name });
  }

  /**
   * Click a button by its name
   */
  async clickButton(name: string | RegExp): Promise<void> {
    await this.getButton(name).click();
  }

  /**
   * Get a heading by its name
   */
  getHeading(name: string | RegExp): Locator {
    return this.page.getByRole('heading', { name });
  }

  /**
   * Get an input by its label
   */
  getInput(label: string | RegExp): Locator {
    return this.page.getByLabel(label);
  }

  /**
   * Fill an input field
   */
  async fillInput(label: string | RegExp, value: string): Promise<void> {
    await this.getInput(label).fill(value);
  }

  /**
   * Get a link by its name
   */
  getLink(name: string | RegExp): Locator {
    return this.page.getByRole('link', { name });
  }

  /**
   * Get text element
   */
  getText(text: string | RegExp): Locator {
    return this.page.getByText(text);
  }

  /**
   * Check if an element is visible
   */
  async isVisible(locator: Locator): Promise<boolean> {
    return await locator.isVisible().catch(() => false);
  }

  /**
   * Wait for a specific URL pattern
   */
  async waitForURL(urlPattern: string | RegExp, timeout: number = 10000): Promise<void> {
    await this.page.waitForURL(urlPattern, { timeout });
  }

  /**
   * Get current URL
   */
  getCurrentURL(): string {
    return this.page.url();
  }

  /**
   * Verify page heading
   */
  async verifyHeading(name: string | RegExp): Promise<void> {
    await expect(this.getHeading(name)).toBeVisible();
  }

  /**
   * Verify text is visible
   */
  async verifyText(text: string | RegExp): Promise<void> {
    await expect(this.getText(text)).toBeVisible();
  }

  /**
   * Take a screenshot
   */
  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ path: `screenshots/${name}.png`, fullPage: true });
  }

  /**
   * Wait for API response
   */
  async waitForAPIResponse(urlPattern: string | RegExp, timeout: number = 5000): Promise<void> {
    await this.page.waitForResponse(
      (response) => {
        const url = response.url();
        if (typeof urlPattern === 'string') {
          return url.includes(urlPattern);
        }
        return urlPattern.test(url);
      },
      { timeout }
    );
  }

  /**
   * Mock API response
   */
  async mockAPIResponse(
    urlPattern: string | RegExp,
    response: unknown,
    status: number = 200
  ): Promise<void> {
    await this.page.route(urlPattern, (route) => {
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(response),
      });
    });
  }

  /**
   * Open modal by clicking button
   */
  async openModal(buttonName: string | RegExp): Promise<void> {
    await this.clickButton(buttonName);
    await this.page.waitForTimeout(500);
  }

  /**
   * Close modal
   */
  async closeModal(useCancelButton: boolean = true): Promise<void> {
    if (useCancelButton) {
      await this.clickButton('Cancel');
    } else {
      await this.page.keyboard.press('Escape');
    }
    await this.page.waitForTimeout(500);
  }

  /**
   * Verify notification/toast message
   */
  async verifyNotification(message: string | RegExp): Promise<void> {
    await expect(this.getText(message)).toBeVisible({ timeout: 5000 });
  }

  /**
   * Select option from dropdown
   */
  async selectOption(label: string | RegExp, value: string): Promise<void> {
    const select = this.getInput(label);
    await select.selectOption(value);
  }

  /**
   * Get table row count
   */
  async getTableRowCount(): Promise<number> {
    return await this.page.locator('table tbody tr').count();
  }

  /**
   * Click table row by index
   */
  async clickTableRow(index: number): Promise<void> {
    await this.page.locator(`table tbody tr:nth-child(${index + 1})`).click();
  }
}
