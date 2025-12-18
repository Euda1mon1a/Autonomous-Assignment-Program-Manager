import { Page, expect, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * SwapPage - Page object for swap marketplace
 *
 * Handles swap request creation, browsing, approval, and execution
 */
export class SwapPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to swap marketplace (if it exists as a route)
   * Note: Based on the code, swap marketplace might be embedded in dashboard or my-schedule
   */
  async navigate(): Promise<void> {
    // Try to navigate to potential swap routes
    await this.goto('/my-schedule');
    await this.waitForPageLoad();
  }

  /**
   * Navigate to swap marketplace tab
   */
  async navigateToSwapMarketplace(): Promise<void> {
    await this.navigate();
    // Look for swap marketplace or pending swaps section
    const swapSection = this.page.getByText(/Swap|Exchange/i).first();
    if (await this.isVisible(swapSection)) {
      await swapSection.click();
    }
  }

  /**
   * Open Create Swap Request dialog/form
   */
  async openCreateSwapRequest(): Promise<void> {
    const createButton = this.page.getByRole('button', { name: /Create.*Swap|New.*Swap|Request.*Swap/i });
    if (await this.isVisible(createButton)) {
      await createButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Fill swap request form
   */
  async fillSwapRequestForm(data: {
    date?: string;
    rotation?: string;
    reason?: string;
    preferredDates?: string[];
  }): Promise<void> {
    if (data.date) {
      const dateInput = this.page.locator('input[type="date"], input[name*="date"]').first();
      if (await this.isVisible(dateInput)) {
        await dateInput.fill(data.date);
      }
    }

    if (data.rotation) {
      const rotationSelect = this.page.locator('select[name*="rotation"], select[id*="rotation"]').first();
      if (await this.isVisible(rotationSelect)) {
        await rotationSelect.selectOption({ label: data.rotation });
      }
    }

    if (data.reason) {
      const reasonInput = this.page.locator('textarea[name*="reason"], textarea[id*="reason"], input[name*="reason"]').first();
      if (await this.isVisible(reasonInput)) {
        await reasonInput.fill(data.reason);
      }
    }
  }

  /**
   * Submit swap request
   */
  async submitSwapRequest(): Promise<void> {
    const submitButton = this.page.getByRole('button', { name: /Submit|Create|Request/i });
    await submitButton.click();
    await this.page.waitForTimeout(1000);
  }

  /**
   * Create a swap request (full flow)
   */
  async createSwapRequest(data: {
    date: string;
    rotation: string;
    reason: string;
  }): Promise<void> {
    await this.openCreateSwapRequest();
    await this.fillSwapRequestForm(data);
    await this.submitSwapRequest();
  }

  /**
   * Get Browse Swaps tab
   */
  async goToBrowseSwapsTab(): Promise<void> {
    const browseTab = this.page.getByRole('button', { name: /Browse.*Swap/i });
    if (await this.isVisible(browseTab)) {
      await browseTab.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Get My Requests tab
   */
  async goToMyRequestsTab(): Promise<void> {
    const myRequestsTab = this.page.getByRole('button', { name: /My.*Request/i });
    if (await this.isVisible(myRequestsTab)) {
      await myRequestsTab.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Get Create Request tab
   */
  async goToCreateRequestTab(): Promise<void> {
    const createTab = this.page.getByRole('button', { name: /Create.*Request/i });
    if (await this.isVisible(createTab)) {
      await createTab.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Get swap request cards
   */
  getSwapRequestCards(): Locator {
    return this.page.locator('[class*="card"]').filter({ hasText: /swap|exchange/i });
  }

  /**
   * Get count of available swap requests
   */
  async getSwapRequestCount(): Promise<number> {
    await this.page.waitForTimeout(1000);
    return await this.getSwapRequestCards().count();
  }

  /**
   * Click on a swap request by index
   */
  async clickSwapRequest(index: number = 0): Promise<void> {
    await this.getSwapRequestCards().nth(index).click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Approve a swap request
   */
  async approveSwapRequest(): Promise<void> {
    const approveButton = this.page.getByRole('button', { name: /Approve|Accept/i });
    if (await this.isVisible(approveButton)) {
      await approveButton.click();
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Reject a swap request
   */
  async rejectSwapRequest(): Promise<void> {
    const rejectButton = this.page.getByRole('button', { name: /Reject|Decline/i });
    if (await this.isVisible(rejectButton)) {
      await rejectButton.click();
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Cancel a swap request
   */
  async cancelSwapRequest(): Promise<void> {
    const cancelButton = this.page.getByRole('button', { name: /Cancel.*Request/i });
    if (await this.isVisible(cancelButton)) {
      await cancelButton.click();
      await this.page.waitForTimeout(500);

      // Confirm cancellation if there's a confirmation dialog
      const confirmButton = this.page.getByRole('button', { name: /Confirm|Yes/i });
      if (await this.isVisible(confirmButton)) {
        await confirmButton.click();
        await this.page.waitForTimeout(1000);
      }
    }
  }

  /**
   * Execute/Complete a swap
   */
  async executeSwap(): Promise<void> {
    const executeButton = this.page.getByRole('button', { name: /Execute|Complete|Finalize/i });
    if (await this.isVisible(executeButton)) {
      await executeButton.click();
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Filter swaps by rotation
   */
  async filterByRotation(rotation: string): Promise<void> {
    const filterSelect = this.page.locator('select').filter({ hasText: /Rotation|All Rotation/i });
    if (await this.isVisible(filterSelect)) {
      await filterSelect.selectOption({ label: rotation });
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Filter swaps by date range
   */
  async filterByDateRange(startDate: string, endDate: string): Promise<void> {
    const startInput = this.page.locator('input[name*="start"], input[placeholder*="Start"]').first();
    const endInput = this.page.locator('input[name*="end"], input[placeholder*="End"]').first();

    if (await this.isVisible(startInput)) {
      await startInput.fill(startDate);
    }
    if (await this.isVisible(endInput)) {
      await endInput.fill(endDate);
    }
    await this.page.waitForTimeout(1000);
  }

  /**
   * Verify swap request details
   */
  async verifySwapRequestDetails(data: {
    status?: string;
    requester?: string;
    date?: string;
  }): Promise<void> {
    if (data.status) {
      await expect(this.getText(new RegExp(data.status, 'i'))).toBeVisible();
    }
    if (data.requester) {
      await expect(this.getText(data.requester)).toBeVisible();
    }
    if (data.date) {
      await expect(this.getText(data.date)).toBeVisible();
    }
  }

  /**
   * Verify swap request status badge
   */
  async verifySwapStatus(status: 'pending' | 'approved' | 'rejected' | 'completed' | 'cancelled'): Promise<void> {
    const statusBadge = this.page.locator(`[class*="badge"]`).filter({ hasText: new RegExp(status, 'i') });
    await expect(statusBadge.first()).toBeVisible({ timeout: 5000 });
  }

  /**
   * Search for swap requests
   */
  async searchSwapRequests(query: string): Promise<void> {
    const searchInput = this.page.locator('input[type="search"], input[placeholder*="Search"]').first();
    if (await this.isVisible(searchInput)) {
      await searchInput.fill(query);
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Get pending swaps count
   */
  async getPendingSwapsCount(): Promise<number> {
    const pendingBadges = this.page.locator('[class*="badge"]').filter({ hasText: /pending/i });
    return await pendingBadges.count();
  }

  /**
   * Navigate to pending swaps (from dashboard)
   */
  async navigateToPendingSwaps(): Promise<void> {
    await this.goto('/');
    const pendingSwapsSection = this.page.getByText(/Pending.*Swap|Swap.*Request/i);
    if (await this.isVisible(pendingSwapsSection)) {
      await pendingSwapsSection.click();
      await this.page.waitForTimeout(500);
    }
  }
}
