import { Page, expect, Locator } from '@playwright/test';

/**
 * Common test utilities and helpers
 *
 * Reusable functions for Playwright E2E tests
 */

/**
 * Wait for network idle (no requests for 500ms)
 */
export async function waitForNetworkIdle(page: Page, timeout: number = 5000): Promise<void> {
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Wait for specific API call to complete
 */
export async function waitForAPICall(
  page: Page,
  urlPattern: string | RegExp,
  method: string = 'GET'
): Promise<void> {
  await page.waitForResponse(
    (response) => {
      const url = response.url();
      const matches = typeof urlPattern === 'string'
        ? url.includes(urlPattern)
        : urlPattern.test(url);
      return matches && response.request().method() === method;
    },
    { timeout: 10000 }
  );
}

/**
 * Fill form field with label
 */
export async function fillByLabel(page: Page, label: string, value: string): Promise<void> {
  const input = page.locator(`label:has-text("${label}")`).locator('+ input, + select, + textarea');
  await input.fill(value);
}

/**
 * Click button with specific text
 */
export async function clickButton(page: Page, text: string): Promise<void> {
  await page.click(`button:has-text("${text}")`);
}

/**
 * Wait for toast notification
 */
export async function waitForToast(page: Page, message?: string): Promise<Locator> {
  const toast = message
    ? page.locator(`[data-testid="toast"]:has-text("${message}")`)
    : page.locator('[data-testid="toast"]');

  await toast.waitFor({ state: 'visible', timeout: 5000 });
  return toast;
}

/**
 * Close toast notification
 */
export async function closeToast(page: Page): Promise<void> {
  const closeButton = page.locator('[data-testid="toast-close"]');
  if (await closeButton.isVisible()) {
    await closeButton.click();
    await closeButton.waitFor({ state: 'hidden' });
  }
}

/**
 * Wait for loading spinner to disappear
 */
export async function waitForLoading(page: Page): Promise<void> {
  const spinner = page.locator('[data-testid="loading-spinner"]');

  // Wait for spinner to appear (if it will)
  try {
    await spinner.waitFor({ state: 'visible', timeout: 1000 });
  } catch {
    // Spinner might not appear if data loads instantly
  }

  // Wait for spinner to disappear
  await spinner.waitFor({ state: 'hidden', timeout: 10000 });
}

/**
 * Check if element is visible
 */
export async function isVisible(locator: Locator): Promise<boolean> {
  try {
    await locator.waitFor({ state: 'visible', timeout: 1000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Scroll element into view
 */
export async function scrollIntoView(locator: Locator): Promise<void> {
  await locator.scrollIntoViewIfNeeded();
}

/**
 * Select option from dropdown
 */
export async function selectOption(page: Page, label: string, value: string): Promise<void> {
  const select = page.locator(`label:has-text("${label}")`).locator('+ select');
  await select.selectOption(value);
}

/**
 * Upload file
 */
export async function uploadFile(page: Page, selector: string, filePath: string): Promise<void> {
  const input = page.locator(selector);
  await input.setInputFiles(filePath);
}

/**
 * Take screenshot with name
 */
export async function takeScreenshot(page: Page, name: string): Promise<void> {
  await page.screenshot({ path: `test-results/screenshots/${name}.png`, fullPage: true });
}

/**
 * Wait for table to load
 */
export async function waitForTableData(page: Page, tableSelector: string = 'table'): Promise<void> {
  const table = page.locator(tableSelector);
  await table.waitFor({ state: 'visible' });

  // Wait for at least one row (besides header)
  const rows = table.locator('tbody tr');
  await expect(rows).not.toHaveCount(0);
}

/**
 * Get table cell value
 */
export async function getTableCellValue(
  page: Page,
  row: number,
  column: number,
  tableSelector: string = 'table'
): Promise<string> {
  const cell = page.locator(`${tableSelector} tbody tr:nth-child(${row}) td:nth-child(${column})`);
  return await cell.textContent() || '';
}

/**
 * Click table row
 */
export async function clickTableRow(
  page: Page,
  row: number,
  tableSelector: string = 'table'
): Promise<void> {
  await page.click(`${tableSelector} tbody tr:nth-child(${row})`);
}

/**
 * Wait for modal to open
 */
export async function waitForModal(page: Page, title?: string): Promise<Locator> {
  const modal = title
    ? page.locator(`[role="dialog"]:has-text("${title}")`)
    : page.locator('[role="dialog"]');

  await modal.waitFor({ state: 'visible', timeout: 5000 });
  return modal;
}

/**
 * Close modal
 */
export async function closeModal(page: Page): Promise<void> {
  const closeButton = page.locator('[role="dialog"] button:has-text("Close"), [role="dialog"] [aria-label="Close"]');
  await closeButton.click();
  await page.locator('[role="dialog"]').waitFor({ state: 'hidden' });
}

/**
 * Drag and drop element
 */
export async function dragAndDrop(
  page: Page,
  sourceSelector: string,
  targetSelector: string
): Promise<void> {
  const source = page.locator(sourceSelector);
  const target = page.locator(targetSelector);

  await source.hover();
  await page.mouse.down();
  await target.hover();
  await page.mouse.up();
}

/**
 * Wait for specific number of elements
 */
export async function waitForElementCount(
  page: Page,
  selector: string,
  count: number
): Promise<void> {
  const elements = page.locator(selector);
  await expect(elements).toHaveCount(count);
}

/**
 * Check element has class
 */
export async function hasClass(locator: Locator, className: string): Promise<boolean> {
  const classes = await locator.getAttribute('class');
  return classes?.split(' ').includes(className) || false;
}

/**
 * Wait for URL to match pattern
 */
export async function waitForURL(page: Page, pattern: string | RegExp): Promise<void> {
  await page.waitForURL(pattern, { timeout: 10000 });
}

/**
 * Navigate and wait for load
 */
export async function navigateAndWait(page: Page, url: string): Promise<void> {
  await page.goto(url);
  await waitForNetworkIdle(page);
}

/**
 * Check if checkbox is checked
 */
export async function isChecked(locator: Locator): Promise<boolean> {
  return await locator.isChecked();
}

/**
 * Toggle checkbox
 */
export async function toggleCheckbox(locator: Locator, checked: boolean): Promise<void> {
  const isCurrentlyChecked = await locator.isChecked();
  if (isCurrentlyChecked !== checked) {
    await locator.click();
  }
}

/**
 * Wait for element to contain text
 */
export async function waitForText(locator: Locator, text: string): Promise<void> {
  await expect(locator).toContainText(text);
}

/**
 * Get all text from elements
 */
export async function getAllText(page: Page, selector: string): Promise<string[]> {
  const elements = page.locator(selector);
  const count = await elements.count();
  const texts: string[] = [];

  for (let i = 0; i < count; i++) {
    const text = await elements.nth(i).textContent();
    if (text) texts.push(text.trim());
  }

  return texts;
}

/**
 * Type with delay (simulate real typing)
 */
export async function typeWithDelay(page: Page, selector: string, text: string, delay: number = 50): Promise<void> {
  await page.type(selector, text, { delay });
}

/**
 * Clear input field
 */
export async function clearInput(page: Page, selector: string): Promise<void> {
  await page.fill(selector, '');
}

/**
 * Wait for download
 */
export async function waitForDownload(page: Page): Promise<string> {
  const download = await page.waitForEvent('download');
  const path = await download.path();
  return path || '';
}

/**
 * Check element is disabled
 */
export async function isDisabled(locator: Locator): Promise<boolean> {
  return await locator.isDisabled();
}

/**
 * Check element is enabled
 */
export async function isEnabled(locator: Locator): Promise<boolean> {
  return await locator.isEnabled();
}

/**
 * Focus element
 */
export async function focus(locator: Locator): Promise<void> {
  await locator.focus();
}

/**
 * Blur element
 */
export async function blur(locator: Locator): Promise<void> {
  await locator.blur();
}

/**
 * Press key
 */
export async function pressKey(page: Page, key: string): Promise<void> {
  await page.keyboard.press(key);
}

/**
 * Hold key while performing action
 */
export async function holdKey(page: Page, key: string, action: () => Promise<void>): Promise<void> {
  await page.keyboard.down(key);
  await action();
  await page.keyboard.up(key);
}

/**
 * Right-click element
 */
export async function rightClick(locator: Locator): Promise<void> {
  await locator.click({ button: 'right' });
}

/**
 * Double-click element
 */
export async function doubleClick(locator: Locator): Promise<void> {
  await locator.dblclick();
}

/**
 * Hover over element
 */
export async function hover(locator: Locator): Promise<void> {
  await locator.hover();
}

/**
 * Get attribute value
 */
export async function getAttribute(locator: Locator, attribute: string): Promise<string | null> {
  return await locator.getAttribute(attribute);
}

/**
 * Set viewport size
 */
export async function setViewport(page: Page, width: number, height: number): Promise<void> {
  await page.setViewportSize({ width, height });
}

/**
 * Mock geolocation
 */
export async function mockGeolocation(page: Page, latitude: number, longitude: number): Promise<void> {
  await page.context().setGeolocation({ latitude, longitude });
}

/**
 * Mock time
 */
export async function mockTime(page: Page, date: Date): Promise<void> {
  await page.clock.setFixedTime(date);
}

/**
 * Reload page and wait
 */
export async function reloadAndWait(page: Page): Promise<void> {
  await page.reload();
  await waitForNetworkIdle(page);
}
