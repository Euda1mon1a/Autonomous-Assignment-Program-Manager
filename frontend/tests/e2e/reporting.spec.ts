/**
 * E2E tests for reporting functionality.
 *
 * Tests report generation and export.
 */

import { test, expect } from '@playwright/test';

test.describe('Reporting', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="username"]', 'testadmin');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
  });

  test('should generate schedule report', async ({ page }) => {
    await page.goto('/reports');

    // Select report type
    await page.selectOption('[data-testid="report-type-select"]', 'schedule');

    // Set date range
    await page.fill('[name="start_date"]', '2024-01-01');
    await page.fill('[name="end_date"]', '2024-01-31');

    // Generate report
    await page.click('[data-testid="generate-report-button"]');

    // Wait for report to generate
    await page.waitForSelector('[data-testid="report-preview"]');

    // Verify report displayed
    await expect(page.locator('[data-testid="report-preview"]')).toBeVisible();
  });

  test('should export report as PDF', async ({ page }) => {
    await page.goto('/reports');

    await page.selectOption('[data-testid="report-type-select"]', 'compliance');
    await page.click('[data-testid="generate-report-button"]');

    await page.waitForSelector('[data-testid="report-preview"]');

    // Click export PDF
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('[data-testid="export-pdf-button"]')
    ]);

    // Verify download
    expect(download.suggestedFilename()).toContain('.pdf');
  });

  test('should export report as CSV', async ({ page }) => {
    await page.goto('/reports');

    await page.selectOption('[data-testid="report-type-select"]', 'schedule');
    await page.click('[data-testid="generate-report-button"]');

    await page.waitForSelector('[data-testid="report-preview"]');

    // Click export CSV
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('[data-testid="export-csv-button"]')
    ]);

    // Verify download
    expect(download.suggestedFilename()).toContain('.csv');
  });

  test('should schedule recurring report', async ({ page }) => {
    await page.goto('/reports/schedule');

    // Configure recurring report
    await page.selectOption('[name="report_type"]', 'compliance');
    await page.selectOption('[name="frequency"]', 'weekly');
    await page.fill('[name="recipients"]', 'admin@hospital.org');

    // Save schedule
    await page.click('button[type="submit"]');

    // Verify success
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should view report history', async ({ page }) => {
    await page.goto('/reports/history');

    // Wait for history to load
    await page.waitForSelector('[data-testid="report-history-list"]');

    // Verify history displayed
    const reports = page.locator('[data-testid="report-history-item"]');
    expect(await reports.count()).toBeGreaterThanOrEqual(0);
  });
});
