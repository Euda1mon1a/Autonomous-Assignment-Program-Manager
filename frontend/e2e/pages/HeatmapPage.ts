import { Page, expect, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * HeatmapPage - Page object for heatmap visualization
 *
 * Handles heatmap viewing, filtering, and interaction
 */
export class HeatmapPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to heatmap page
   * Note: Adjust path based on actual implementation
   */
  async navigate(): Promise<void> {
    // Heatmap might be embedded in analytics or schedule pages
    await this.goto('/analytics');
    await this.waitForPageLoad();
  }

  /**
   * Navigate to schedule heatmap view
   */
  async navigateToScheduleHeatmap(): Promise<void> {
    await this.goto('/schedule');
    await this.waitForPageLoad();

    // Look for heatmap toggle or tab
    const heatmapButton = this.page.getByRole('button', { name: /Heatmap|Heat Map/i });
    if (await this.isVisible(heatmapButton)) {
      await heatmapButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Get heatmap container
   */
  getHeatmapContainer(): Locator {
    return this.page.locator('.js-plotly-plot, canvas, svg[class*="main-svg"]').first();
  }

  /**
   * Verify heatmap is visible
   */
  async verifyHeatmapVisible(): Promise<void> {
    const heatmap = this.getHeatmapContainer();
    await expect(heatmap).toBeVisible({ timeout: 10000 });
  }

  /**
   * Get heatmap controls container
   */
  getControlsContainer(): Locator {
    return this.page.locator('[class*="controls"]').or(
      this.page.locator('div').filter({ has: this.page.getByText(/Date Range|Group by/i) })
    ).first();
  }

  /**
   * Get date range inputs
   */
  getDateRangeInputs(): { start: Locator; end: Locator } {
    return {
      start: this.page.locator('input[type="date"]').first(),
      end: this.page.locator('input[type="date"]').last(),
    };
  }

  /**
   * Set date range
   */
  async setDateRange(startDate: string, endDate: string): Promise<void> {
    const { start, end } = this.getDateRangeInputs();

    if (await this.isVisible(start)) {
      await start.fill(startDate);
      await start.blur();
    }

    if (await this.isVisible(end)) {
      await end.fill(endDate);
      await end.blur();
    }

    await this.page.waitForTimeout(1500); // Wait for heatmap to reload
  }

  /**
   * Get group by selector
   */
  getGroupBySelector(): Locator {
    return this.page.locator('select').filter({ hasText: /Day|Week|Month/i }).or(
      this.page.locator('label:has-text("Group by") + select, label:has-text("Group by") ~ select')
    ).first();
  }

  /**
   * Change grouping
   */
  async changeGroupBy(groupBy: 'day' | 'week' | 'month' | 'person' | 'rotation'): Promise<void> {
    const selector = this.getGroupBySelector();
    if (await this.isVisible(selector)) {
      await selector.selectOption(groupBy);
      await this.page.waitForTimeout(1500); // Wait for heatmap to reload
    }
  }

  /**
   * Get include FMIT checkbox
   */
  getIncludeFmitCheckbox(): Locator {
    return this.page.locator('input[type="checkbox"]').filter({ hasText: /FMIT/i }).or(
      this.page.locator('label:has-text("Include FMIT") input[type="checkbox"]')
    ).first();
  }

  /**
   * Toggle include FMIT
   */
  async toggleIncludeFmit(): Promise<void> {
    const checkbox = this.getIncludeFmitCheckbox();
    if (await this.isVisible(checkbox)) {
      await checkbox.click();
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Get filters toggle button
   */
  getFiltersButton(): Locator {
    return this.page.getByRole('button', { name: /Filters?/i });
  }

  /**
   * Open filters panel
   */
  async openFilters(): Promise<void> {
    const filtersButton = this.getFiltersButton();
    if (await this.isVisible(filtersButton)) {
      const isExpanded = await filtersButton.getAttribute('aria-expanded');
      if (isExpanded !== 'true') {
        await filtersButton.click();
        await this.page.waitForTimeout(500);
      }
    }
  }

  /**
   * Close filters panel
   */
  async closeFilters(): Promise<void> {
    const filtersButton = this.getFiltersButton();
    if (await this.isVisible(filtersButton)) {
      const isExpanded = await filtersButton.getAttribute('aria-expanded');
      if (isExpanded === 'true') {
        await filtersButton.click();
        await this.page.waitForTimeout(300);
      }
    }
  }

  /**
   * Select people filter
   */
  async selectPerson(personName: string): Promise<void> {
    await this.openFilters();
    const personCheckbox = this.page.locator('label').filter({ hasText: personName }).locator('input[type="checkbox"]');
    if (await this.isVisible(personCheckbox)) {
      await personCheckbox.click();
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Select rotation filter
   */
  async selectRotation(rotationName: string): Promise<void> {
    await this.openFilters();
    const rotationCheckbox = this.page.locator('label').filter({ hasText: rotationName }).locator('input[type="checkbox"]');
    if (await this.isVisible(rotationCheckbox)) {
      await rotationCheckbox.click();
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Clear all filters
   */
  async clearAllFilters(): Promise<void> {
    await this.openFilters();
    const clearButton = this.page.getByRole('button', { name: /Clear all filters/i });
    if (await this.isVisible(clearButton)) {
      await clearButton.click();
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Get active filter count
   */
  async getActiveFilterCount(): Promise<number> {
    const badge = this.page.locator('[class*="badge"]').filter({ hasText: /\d+/ }).first();
    if (await this.isVisible(badge)) {
      const text = await badge.textContent();
      const match = text?.match(/(\d+)/);
      return match ? parseInt(match[1]) : 0;
    }
    return 0;
  }

  /**
   * Get legend container
   */
  getLegendContainer(): Locator {
    return this.page.locator('[class*="legend"]').or(
      this.page.locator('div').filter({ hasText: /Legend|Intensity Scale/i })
    ).first();
  }

  /**
   * Verify legend is displayed
   */
  async verifyLegendDisplayed(): Promise<void> {
    const legend = this.getLegendContainer();
    await expect(legend).toBeVisible();
  }

  /**
   * Get export button
   */
  getExportButton(): Locator {
    return this.page.getByRole('button', { name: /Export/i });
  }

  /**
   * Click export
   */
  async clickExport(): Promise<void> {
    const exportButton = this.getExportButton();
    if (await this.isVisible(exportButton)) {
      await exportButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Click on a heatmap cell
   */
  async clickHeatmapCell(x: number, y: number): Promise<void> {
    const heatmap = this.getHeatmapContainer();
    const box = await heatmap.boundingBox();

    if (box) {
      // Click at approximate position within heatmap
      const clickX = box.x + (box.width * x / 100);
      const clickY = box.y + (box.height * y / 100);
      await this.page.mouse.click(clickX, clickY);
      await this.page.waitForTimeout(300);
    }
  }

  /**
   * Hover over heatmap to see tooltip
   */
  async hoverHeatmapCell(x: number, y: number): Promise<void> {
    const heatmap = this.getHeatmapContainer();
    const box = await heatmap.boundingBox();

    if (box) {
      const hoverX = box.x + (box.width * x / 100);
      const hoverY = box.y + (box.height * y / 100);
      await this.page.mouse.move(hoverX, hoverY);
      await this.page.waitForTimeout(500); // Wait for tooltip
    }
  }

  /**
   * Get tooltip/hover text
   */
  async getTooltipText(): Promise<string | null> {
    const tooltip = this.page.locator('.plotly-tooltip, [class*="tooltip"]').first();
    if (await this.isVisible(tooltip)) {
      return await tooltip.textContent();
    }
    return null;
  }

  /**
   * Verify loading state
   */
  async verifyLoadingState(): Promise<void> {
    const loadingIndicator = this.page.locator('.animate-spin, [class*="loading"]').or(
      this.getText(/Loading heatmap/i)
    );
    await expect(loadingIndicator).toBeVisible();
  }

  /**
   * Wait for heatmap to load
   */
  async waitForHeatmapLoad(): Promise<void> {
    // Wait for loading to disappear
    const loadingIndicator = this.page.locator('.animate-spin').first();
    if (await this.isVisible(loadingIndicator)) {
      await loadingIndicator.waitFor({ state: 'hidden', timeout: 10000 });
    }

    // Wait for heatmap to be visible
    await this.verifyHeatmapVisible();
  }

  /**
   * Verify error state
   */
  async verifyErrorState(): Promise<void> {
    const errorMessage = this.page.locator('[class*="error"], [class*="alert-danger"]').or(
      this.getText(/Failed to load|Error/i)
    ).first();
    await expect(errorMessage).toBeVisible();
  }

  /**
   * Verify empty state
   */
  async verifyEmptyState(): Promise<void> {
    const emptyState = this.page.locator('[class*="empty"]').or(
      this.getText(/No data available/i)
    ).first();
    await expect(emptyState).toBeVisible();
  }

  /**
   * Get color scale gradient
   */
  getColorScale(): Locator {
    return this.page.locator('[style*="gradient"]').or(
      this.page.locator('.colorbar, [class*="color-scale"]')
    ).first();
  }

  /**
   * Verify color scale is displayed
   */
  async verifyColorScaleDisplayed(): Promise<void> {
    const colorScale = this.getColorScale();
    await expect(colorScale).toBeVisible();
  }

  /**
   * Resize viewport for responsive testing
   */
  async setViewportSize(width: number, height: number): Promise<void> {
    await this.page.setViewportSize({ width, height });
    await this.page.waitForTimeout(1000); // Wait for responsive adjustments
  }

  /**
   * Verify heatmap responds to resize
   */
  async verifyResponsiveBehavior(): Promise<void> {
    // Get initial heatmap dimensions
    const heatmap = this.getHeatmapContainer();
    const initialBox = await heatmap.boundingBox();

    // Resize viewport
    await this.setViewportSize(768, 1024); // Tablet size
    await this.page.waitForTimeout(1000);

    // Get new dimensions
    const newBox = await heatmap.boundingBox();

    // Verify heatmap adjusted
    expect(newBox).toBeTruthy();
    expect(newBox?.width).toBeLessThan(initialBox?.width || 0);
  }

  /**
   * Get Plotly mode bar (zoom, pan, etc.)
   */
  getPlotlyModeBar(): Locator {
    return this.page.locator('.modebar, [class*="modebar"]').first();
  }

  /**
   * Verify Plotly controls are available
   */
  async verifyPlotlyControls(): Promise<void> {
    const modeBar = this.getPlotlyModeBar();
    await expect(modeBar).toBeVisible();
  }
}
