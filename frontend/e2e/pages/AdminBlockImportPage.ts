import { Page, Locator } from '@playwright/test';

export class AdminBlockImportPage {
  readonly page: Page;
  readonly fileInput: Locator;
  readonly blockNumberInput: Locator;
  readonly academicYearInput: Locator;
  readonly uploadBtn: Locator;
  readonly stageBtn: Locator;

  // Step 2 Review
  readonly stagedDataTable: Locator;
  readonly recordCount: Locator;
  readonly nextStepBtn: Locator;

  // Step 3 Apply
  readonly applyBtn: Locator;
  readonly rejectBtn: Locator;
  readonly statusBadge: Locator;

  constructor(page: Page) {
    this.page = page;

    // Step 1
    this.fileInput = page.locator('input[type="file"], [data-testid="import-file-input"]');
    this.blockNumberInput = page.locator('input[name="block_number"], [data-testid="block-number-input"]');
    this.academicYearInput = page.locator('input[name="academic_year"], [data-testid="academic-year-input"]');
    this.uploadBtn = page.locator('button:has-text("Upload"), [data-testid="upload-btn"]');
    this.stageBtn = page.locator('button:has-text("Stage"), [data-testid="stage-btn"]');

    // Step 2
    this.stagedDataTable = page.locator('[data-testid="staged-data-table"], table');
    this.recordCount = page.locator('[data-testid="record-count"]');
    this.nextStepBtn = page.locator('button:has-text("Next"), button:has-text("Review")');

    // Step 3
    this.applyBtn = page.locator('button:has-text("Apply"), [data-testid="apply-btn"]');
    this.rejectBtn = page.locator('button:has-text("Reject"), button:has-text("Cancel")');
    this.statusBadge = page.locator('[data-testid="import-status-badge"]');
  }

  async navigate() {
    await this.page.goto('/admin/block-import');
    await this.page.waitForLoadState('networkidle');
  }

  async uploadFile(filePath: string, blockNum: string, year: string) {
    await this.fileInput.setInputFiles(filePath);

    if (await this.blockNumberInput.isVisible()) {
      await this.blockNumberInput.fill(blockNum);
    }

    if (await this.academicYearInput.isVisible()) {
      await this.academicYearInput.fill(year);
    }

    if (await this.uploadBtn.isVisible()) {
      await this.uploadBtn.click();
    } else if (await this.stageBtn.isVisible()) {
      await this.stageBtn.click();
    }
  }

  async getRecordCount(): Promise<number> {
    if (await this.recordCount.isVisible()) {
      const text = await this.recordCount.innerText();
      const match = text.match(/\d+/);
      return match ? parseInt(match[0], 10) : 0;
    }
    return 0;
  }
}
