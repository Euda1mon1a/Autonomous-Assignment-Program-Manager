import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * ImportExportPage - Page object for import/export E2E tests
 *
 * Covers half-day import workflow (upload, preview, draft),
 * batch review/apply, and block export.
 */
export class ImportExportPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // ── Navigation ──────────────────────────────────────────────

  async navigateToImport(): Promise<void> {
    await this.goto('/import');
  }

  async navigateToHalfDayImport(): Promise<void> {
    await this.goto('/import/half-day');
  }

  async navigateToBatch(batchId: string): Promise<void> {
    await this.goto(`/import/${batchId}`);
  }

  // ── Half-day import: upload step ────────────────────────────

  async uploadHalfDayFile(
    filePath: string,
    blockNumber: number,
    academicYear: number
  ): Promise<void> {
    await this.page
      .locator('[data-testid="hd-file-input"]')
      .setInputFiles(filePath);
    await this.page
      .locator('[data-testid="hd-block-number"]')
      .fill(String(blockNumber));
    await this.page
      .locator('[data-testid="hd-academic-year"]')
      .fill(String(academicYear));
  }

  async stageHalfDay(): Promise<void> {
    await this.page.locator('[data-testid="hd-stage-btn"]').click();
    await this.waitForPageLoad();
  }

  // ── Half-day import: preview step ───────────────────────────

  async getDiffMetrics(): Promise<{
    total: string;
    changed: string;
    addedRemoved: string;
    hours: string;
  }> {
    const total = await this.page
      .locator('[data-testid="hd-metric-total"]')
      .textContent();
    const changed = await this.page
      .locator('[data-testid="hd-metric-changed"]')
      .textContent();
    const addedRemoved = await this.page
      .locator('[data-testid="hd-metric-added-removed"]')
      .textContent();
    const hours = await this.page
      .locator('[data-testid="hd-metric-hours"]')
      .textContent();

    return {
      total: total ?? '',
      changed: changed ?? '',
      addedRemoved: addedRemoved ?? '',
      hours: hours ?? '',
    };
  }

  async selectAllDiffs(): Promise<void> {
    await this.page.locator('[data-testid="hd-select-page-btn"]').click();
  }

  async createDraft(notes?: string): Promise<void> {
    if (notes) {
      await this.page
        .locator('[data-testid="hd-draft-notes"]')
        .fill(notes);
    }
    await this.page.locator('[data-testid="hd-create-draft-btn"]').click();
    await this.waitForPageLoad();
  }

  // ── Batch review page ───────────────────────────────────────

  async getBatchStatus(): Promise<string> {
    const text = await this.page
      .locator('[data-testid="batch-status-badge"]')
      .textContent();
    return text ?? '';
  }

  async applyBatch(): Promise<void> {
    await this.page.locator('[data-testid="batch-apply-btn"]').click();
    await this.waitForAPIResponse('/api/import');
  }

  async getPreviewStats(): Promise<{
    new: string;
    updates: string;
    conflicts: string;
    violations: string;
  }> {
    const newStat = await this.page
      .locator('[data-testid="batch-stat-new"]')
      .textContent();
    const updates = await this.page
      .locator('[data-testid="batch-stat-updates"]')
      .textContent();
    const conflicts = await this.page
      .locator('[data-testid="batch-stat-conflicts"]')
      .textContent();
    const violations = await this.page
      .locator('[data-testid="batch-stat-violations"]')
      .textContent();

    return {
      new: newStat ?? '',
      updates: updates ?? '',
      conflicts: conflicts ?? '',
      violations: violations ?? '',
    };
  }

  // ── Export ──────────────────────────────────────────────────

  async exportBlock(): Promise<void> {
    await this.page.locator('[data-testid="export-submit-btn"]').click();
  }
}
