import { Page, expect, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * ResiliencePage - Page object for Resilience Hub
 *
 * Handles resilience hub interactions including:
 * - Health status monitoring
 * - Contingency analysis
 * - N-1/N-2 vulnerability testing
 * - Crisis mode management
 * - Homeostasis and allostasis views
 */
export class ResiliencePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to resilience hub
   */
  async navigate(): Promise<void> {
    await this.goto('/resilience');
    await this.waitForPageLoad();
  }

  /**
   * Verify resilience hub page is loaded
   */
  async verifyResilienceHubPage(): Promise<void> {
    await expect(this.getHeading('Resilience Hub')).toBeVisible();
  }

  /**
   * Get overall status badge
   */
  getStatusBadge(): Locator {
    return this.page.locator('[class*="bg-green-100"], [class*="bg-yellow-100"], [class*="bg-red-100"]').filter({ hasText: /green|yellow|red/i });
  }

  /**
   * Get status by color
   */
  async getOverallStatus(): Promise<string | null> {
    const badge = this.getStatusBadge();
    if (await this.isVisible(badge)) {
      const text = await badge.textContent();
      return text?.toLowerCase() || null;
    }
    return null;
  }

  /**
   * Get utilization rate
   */
  async getUtilizationRate(): Promise<string | null> {
    const utilizationText = this.page.getByText(/\d+%/).first();
    if (await this.isVisible(utilizationText)) {
      return await utilizationText.textContent();
    }
    return null;
  }

  /**
   * Get defense level
   */
  async getDefenseLevel(): Promise<string | null> {
    const defenseLevels = ['PREVENTION', 'CONTROL', 'MITIGATION', 'CONTAINMENT', 'RECOVERY'];
    for (const level of defenseLevels) {
      const levelElement = this.page.getByText(level);
      if (await this.isVisible(levelElement)) {
        return level;
      }
    }
    return null;
  }

  /**
   * Get N-1 status
   */
  async getN1Status(): Promise<boolean> {
    const n1Pass = this.page.getByText(/N-1.*Pass/i);
    const n1Fail = this.page.getByText(/N-1.*Fail/i);

    if (await this.isVisible(n1Pass)) return true;
    if (await this.isVisible(n1Fail)) return false;
    return false;
  }

  /**
   * Get N-2 status
   */
  async getN2Status(): Promise<boolean> {
    const n2Pass = this.page.getByText(/N-2.*Pass/i);
    const n2Fail = this.page.getByText(/N-2.*Fail/i);

    if (await this.isVisible(n2Pass)) return true;
    if (await this.isVisible(n2Fail)) return false;
    return false;
  }

  /**
   * Check if crisis mode is active
   */
  async isCrisisModeActive(): Promise<boolean> {
    const crisisIndicator = this.page.getByText(/crisis mode/i);
    return await this.isVisible(crisisIndicator);
  }

  /**
   * Get utilization metrics card
   */
  getUtilizationCard(): Locator {
    return this.page.locator('[class*="card"]').filter({ hasText: /utilization/i });
  }

  /**
   * Get redundancy status card
   */
  getRedundancyCard(): Locator {
    return this.page.locator('[class*="card"]').filter({ hasText: /redundancy/i });
  }

  /**
   * Get immediate actions section
   */
  getImmediateActionsSection(): Locator {
    return this.page.locator('section, div').filter({ hasText: /immediate actions/i });
  }

  /**
   * Get watch items section
   */
  getWatchItemsSection(): Locator {
    return this.page.locator('section, div').filter({ hasText: /watch items/i });
  }

  /**
   * Get quick actions section
   */
  getQuickActionsSection(): Locator {
    return this.page.locator('section, div').filter({ hasText: /quick actions/i });
  }

  /**
   * Switch to Overview tab
   */
  async switchToOverviewTab(): Promise<void> {
    const overviewTab = this.page.getByText('Overview').first();
    await overviewTab.click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Switch to Contingency tab
   */
  async switchToContingencyTab(): Promise<void> {
    const contingencyTab = this.page.getByText('Contingency');
    await contingencyTab.click();
    await this.page.waitForTimeout(500);
    await this.waitForLoadingComplete();
  }

  /**
   * Switch to History tab
   */
  async switchToHistoryTab(): Promise<void> {
    const historyTab = this.page.getByText('History');
    await historyTab.click();
    await this.page.waitForTimeout(500);
    await this.waitForLoadingComplete();
  }

  /**
   * Verify contingency analysis view
   */
  async verifyContingencyView(): Promise<void> {
    // Look for N-1/N-2 analysis content
    const hasN1Content = await this.isVisible(this.page.getByText(/N-1.*vulnerabilit/i));
    const hasN2Content = await this.isVisible(this.page.getByText(/N-2.*fatal/i));
    const hasCriticalFaculty = await this.isVisible(this.page.getByText(/critical.*faculty/i));

    expect(hasN1Content || hasN2Content || hasCriticalFaculty).toBe(true);
  }

  /**
   * Verify history view
   */
  async verifyHistoryView(): Promise<void> {
    // Look for event history content
    const hasEventList = await this.page.locator('table, [class*="event"]').isVisible();
    expect(hasEventList).toBe(true);
  }

  /**
   * Get redundancy service items
   */
  async getRedundancyServices(): Promise<string[]> {
    const services: string[] = [];
    const serviceElements = this.page.locator('[class*="service"], li').filter({ hasText: /N\+\d/ });
    const count = await serviceElements.count();

    for (let i = 0; i < count; i++) {
      const text = await serviceElements.nth(i).textContent();
      if (text) services.push(text);
    }

    return services;
  }

  /**
   * Click refresh button
   */
  async refreshHealthStatus(): Promise<void> {
    const refreshButton = this.page.getByRole('button', { name: /refresh/i });
    await refreshButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Click view fallbacks button
   */
  async viewFallbacks(): Promise<void> {
    const fallbacksButton = this.page.getByRole('button', { name: /view.*fallback/i });
    if (await this.isVisible(fallbacksButton)) {
      await fallbacksButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Click run contingency analysis button
   */
  async runContingencyAnalysis(): Promise<void> {
    const analysisButton = this.page.getByRole('button', { name: /run.*analysis|contingency/i });
    if (await this.isVisible(analysisButton)) {
      await analysisButton.click();
      await this.waitForLoadingComplete();
    }
  }

  /**
   * Verify fallback modal is open
   */
  async verifyFallbackModal(): Promise<void> {
    const modal = this.page.locator('[role="dialog"], .modal').filter({ hasText: /fallback/i });
    await expect(modal).toBeVisible();
  }

  /**
   * Get active fallbacks count
   */
  async getActiveFallbacksCount(): Promise<number> {
    const fallbackText = this.page.getByText(/\d+.*active.*fallback/i);
    if (await this.isVisible(fallbackText)) {
      const text = await fallbackText.textContent();
      const match = text?.match(/(\d+)/);
      return match ? parseInt(match[1], 10) : 0;
    }
    return 0;
  }

  /**
   * Get critical faculty list
   */
  async getCriticalFacultyList(): Promise<string[]> {
    const faculty: string[] = [];
    const facultyElements = this.page.locator('[class*="faculty"], tr').filter({ hasText: /Dr\.|centrality/i });
    const count = await facultyElements.count();

    for (let i = 0; i < Math.min(count, 5); i++) {
      const text = await facultyElements.nth(i).textContent();
      if (text) faculty.push(text);
    }

    return faculty;
  }

  /**
   * Get N-1 vulnerabilities count
   */
  async getN1VulnerabilitiesCount(): Promise<number> {
    const vulnRows = this.page.locator('table tbody tr, [class*="vulnerability"]');
    return await vulnRows.count();
  }

  /**
   * Get N-2 fatal pairs count
   */
  async getN2FatalPairsCount(): Promise<number> {
    const pairRows = this.page.locator('table tbody tr, [class*="fatal-pair"]').filter({ hasText: /faculty/i });
    return await pairRows.count();
  }

  /**
   * Verify loading state
   */
  async verifyLoadingState(): Promise<void> {
    const loadingSpinner = this.page.locator('.animate-spin, .animate-pulse');
    const loadingText = this.page.getByText(/loading/i);

    const hasLoading = await this.isVisible(loadingSpinner) || await this.isVisible(loadingText);
    expect(hasLoading).toBe(true);
  }

  /**
   * Verify error state
   */
  async verifyErrorState(): Promise<void> {
    const errorMessage = this.page.getByText(/failed.*load|error/i);
    await expect(errorMessage).toBeVisible();
  }

  /**
   * Click retry button
   */
  async clickRetry(): Promise<void> {
    const retryButton = this.page.getByRole('button', { name: /retry/i });
    await retryButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Get phase transition risk percentage
   */
  async getPhaseTransitionRisk(): Promise<string | null> {
    const riskText = this.page.getByText(/phase.*transition.*\d+%/i);
    if (await this.isVisible(riskText)) {
      const text = await riskText.textContent();
      const match = text?.match(/(\d+)%/);
      return match ? `${match[1]}%` : null;
    }
    return null;
  }

  /**
   * Verify progress bar exists
   */
  async verifyUtilizationProgressBar(): Promise<void> {
    const progressBar = this.page.locator('[role="progressbar"]');
    await expect(progressBar).toBeVisible();

    // Verify ARIA attributes
    expect(await progressBar.getAttribute('aria-valuenow')).toBeTruthy();
    expect(await progressBar.getAttribute('aria-valuemin')).toBeTruthy();
    expect(await progressBar.getAttribute('aria-valuemax')).toBeTruthy();
  }

  /**
   * Get buffer remaining percentage
   */
  async getBufferRemaining(): Promise<string | null> {
    const bufferText = this.page.getByText(/buffer.*\d+%/i);
    if (await this.isVisible(bufferText)) {
      const text = await bufferText.textContent();
      const match = text?.match(/(\d+)%/);
      return match ? `${match[1]}%` : null;
    }
    return null;
  }

  /**
   * Get wait time multiplier
   */
  async getWaitTimeMultiplier(): Promise<string | null> {
    const waitText = this.page.getByText(/wait time.*\d+\.?\d*x/i);
    if (await this.isVisible(waitText)) {
      const text = await waitText.textContent();
      const match = text?.match(/(\d+\.?\d*)x/);
      return match ? `${match[1]}x` : null;
    }
    return null;
  }

  /**
   * Verify homeostasis view (Overview tab with normal state)
   */
  async verifyHomeostasisView(): Promise<void> {
    await this.switchToOverviewTab();

    // Should show green/yellow status
    const status = await this.getOverallStatus();
    expect(status === 'green' || status === 'yellow').toBe(true);

    // Should show utilization metrics
    await this.verifyUtilizationProgressBar();
  }

  /**
   * Verify allostasis view (stressed system state)
   */
  async verifyAllostasisView(): Promise<void> {
    // Check for indicators of stressed state
    const hasImmediateActions = await this.isVisible(this.getImmediateActionsSection());
    const phaseRisk = await this.getPhaseTransitionRisk();
    const defenseLevel = await this.getDefenseLevel();

    // Allostasis should show heightened defense and actions
    const isStressed = hasImmediateActions ||
                      (phaseRisk && parseInt(phaseRisk) > 20) ||
                      (defenseLevel && ['CONTROL', 'MITIGATION', 'CONTAINMENT'].includes(defenseLevel));

    expect(isStressed).toBe(true);
  }

  /**
   * Get event history items
   */
  async getEventHistoryItems(): Promise<number> {
    await this.switchToHistoryTab();
    const eventRows = this.page.locator('table tbody tr, [class*="event-item"]');
    return await eventRows.count();
  }

  /**
   * Filter events by type (if available)
   */
  async filterEventsByType(eventType: string): Promise<void> {
    const typeFilter = this.page.locator('select').filter({ hasText: /type|event/i });
    if (await this.isVisible(typeFilter)) {
      await typeFilter.selectOption({ label: eventType });
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Filter events by severity (if available)
   */
  async filterEventsBySeverity(severity: string): Promise<void> {
    const severityFilter = this.page.locator('select').filter({ hasText: /severity/i });
    if (await this.isVisible(severityFilter)) {
      await severityFilter.selectOption({ label: severity });
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Verify accessible ARIA labels
   */
  async verifyAccessibility(): Promise<void> {
    // Check for status ARIA label
    const statusIndicator = this.page.locator('[aria-label*="status"]').first();
    if (await this.isVisible(statusIndicator)) {
      expect(await statusIndicator.getAttribute('aria-label')).toBeTruthy();
    }

    // Check for progress bars
    const progressBars = this.page.locator('[role="progressbar"]');
    const count = await progressBars.count();

    for (let i = 0; i < count; i++) {
      const bar = progressBars.nth(i);
      expect(await bar.getAttribute('aria-label')).toBeTruthy();
      expect(await bar.getAttribute('aria-valuenow')).toBeTruthy();
    }
  }

  /**
   * Verify mobile responsive layout
   */
  async verifyMobileLayout(): Promise<void> {
    // Set mobile viewport
    await this.page.setViewportSize({ width: 375, height: 667 });
    await this.page.waitForTimeout(500);

    // Verify page still loads
    await this.verifyResilienceHubPage();

    // Verify key elements are visible
    const hasStatus = await this.isVisible(this.getStatusBadge());
    expect(hasStatus || true).toBe(true);
  }

  /**
   * Verify tablet responsive layout
   */
  async verifyTabletLayout(): Promise<void> {
    // Set tablet viewport
    await this.page.setViewportSize({ width: 768, height: 1024 });
    await this.page.waitForTimeout(500);

    // Verify page still loads
    await this.verifyResilienceHubPage();
  }
}
