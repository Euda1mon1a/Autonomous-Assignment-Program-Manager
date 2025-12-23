import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * LoginPage - Page object for authentication
 *
 * Handles login operations and authentication flows
 */
export class LoginPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to login page
   */
  async navigate(): Promise<void> {
    await this.goto('/login');
  }

  /**
   * Login with credentials
   */
  async login(username: string, password: string): Promise<void> {
    await this.navigate();
    await this.fillInput('Username', username);
    await this.fillInput('Password', password);
    await this.clickButton('Sign In');
    await this.waitForURL('/', 10000);
  }

  /**
   * Login as admin
   */
  async loginAsAdmin(): Promise<void> {
    await this.login('admin', 'admin123');
  }

  /**
   * Login as coordinator
   */
  async loginAsCoordinator(): Promise<void> {
    await this.login('coordinator', 'coord123');
  }

  /**
   * Login as faculty
   */
  async loginAsFaculty(): Promise<void> {
    await this.login('faculty', 'faculty123');
  }

  /**
   * Login as resident
   */
  async loginAsResident(): Promise<void> {
    await this.login('resident', 'resident123');
  }

  /**
   * Verify login page is displayed
   */
  async verifyLoginPage(): Promise<void> {
    await expect(this.getHeading('Welcome Back')).toBeVisible();
    await expect(this.getInput('Username')).toBeVisible();
    await expect(this.getInput('Password')).toBeVisible();
  }

  /**
   * Logout
   */
  async logout(): Promise<void> {
    // Click on user menu to open dropdown
    await this.page.getByRole('button', { name: /admin|coordinator|faculty|resident/i }).click();
    // Click logout button
    await this.clickButton('Logout');
    // Wait for redirect to login page
    await this.waitForURL(/\/login/, 10000);
  }

  /**
   * Clear storage (logout without UI)
   */
  async clearStorage(): Promise<void> {
    await this.page.context().clearCookies();
    await this.page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  }
}
