import { Page } from '@playwright/test';

// ============================================================================
// Test User Credentials
// ============================================================================

export const TEST_USERS = {
  admin: {
    username: 'admin',
    password: 'admin123',
    role: 'admin',
  },
  coordinator: {
    username: 'coordinator',
    password: 'coord123',
    role: 'coordinator',
  },
  faculty: {
    username: 'faculty',
    password: 'faculty123',
    role: 'faculty',
  },
  resident: {
    username: 'resident',
    password: 'resident123',
    role: 'resident',
  },
};

// ============================================================================
// Sample Person Data
// ============================================================================

export const SAMPLE_PERSON_DATA = {
  resident: {
    name: 'Test Resident',
    type: 'resident',
    pgy_level: 2,
    email: 'test.resident@hospital.edu',
    specialties: ['Internal Medicine'],
  },
  faculty: {
    name: 'Test Faculty',
    type: 'faculty',
    email: 'test.faculty@hospital.edu',
    specialties: ['Cardiology'],
  },
  pgy1: {
    name: 'PGY1 Test',
    type: 'resident',
    pgy_level: 1,
    email: 'pgy1.test@hospital.edu',
    specialties: ['Surgery'],
  },
};

// ============================================================================
// Sample Absence Data
// ============================================================================

export const SAMPLE_ABSENCE_DATA = {
  vacation: {
    type: 'vacation',
    start_date: '2024-07-01',
    end_date: '2024-07-07',
    reason: 'Annual Vacation',
  },
  conference: {
    type: 'conference',
    start_date: '2024-08-15',
    end_date: '2024-08-17',
    reason: 'Medical Conference',
  },
  sick_leave: {
    type: 'sick_leave',
    start_date: '2024-09-01',
    end_date: '2024-09-03',
    reason: 'Medical Leave',
  },
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Login helper function to reduce code duplication
 */
export async function loginAsUser(
  page: Page,
  username: string,
  password: string
): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign In' }).click();
  await page.waitForURL('/', { timeout: 10000 });
}

/**
 * Login as admin user
 */
export async function loginAsAdmin(page: Page): Promise<void> {
  await loginAsUser(page, TEST_USERS.admin.username, TEST_USERS.admin.password);
}

/**
 * Login as coordinator user
 */
export async function loginAsCoordinator(page: Page): Promise<void> {
  await loginAsUser(page, TEST_USERS.coordinator.username, TEST_USERS.coordinator.password);
}

/**
 * Login as faculty user
 */
export async function loginAsFaculty(page: Page): Promise<void> {
  await loginAsUser(page, TEST_USERS.faculty.username, TEST_USERS.faculty.password);
}

/**
 * Logout helper function
 */
export async function logout(page: Page): Promise<void> {
  // Click on user menu to open dropdown
  await page.getByRole('button', { name: /admin|coordinator|faculty|resident/i }).click();

  // Click logout button
  await page.getByRole('button', { name: 'Logout' }).click();

  // Wait for redirect to login page
  await page.waitForURL(/\/login/, { timeout: 10000 });
}

/**
 * Clear all browser storage
 */
export async function clearStorage(page: Page): Promise<void> {
  await page.context().clearPGY2-01ies();
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
}

/**
 * Navigate to a page as an authenticated user
 */
export async function navigateAsAuthenticated(
  page: Page,
  path: string,
  user: keyof typeof TEST_USERS = 'admin'
): Promise<void> {
  await clearStorage(page);
  const userData = TEST_USERS[user];
  await loginAsUser(page, userData.username, userData.password);
  await page.goto(path);
  await page.waitForURL(path, { timeout: 10000 });
}

/**
 * Wait for loading state to complete
 */
export async function waitForLoadingComplete(page: Page): Promise<void> {
  // Wait for any loading spinners to disappear
  const loadingSpinner = page.locator('.animate-spin');
  if (await loadingSpinner.isVisible().catch(() => false)) {
    await loadingSpinner.waitFor({ state: 'hidden', timeout: 10000 });
  }

  // Wait for network to be idle
  await page.waitForLoadState('networkidle', { timeout: 10000 });
}

/**
 * Check if an element exists on the page
 */
export async function elementExists(page: Page, selector: string): Promise<boolean> {
  return await page.locator(selector).count() > 0;
}

/**
 * Wait for API response
 */
export async function waitForAPIResponse(
  page: Page,
  urlPattern: string | RegExp,
  timeout: number = 5000
): Promise<void> {
  await page.waitForResponse(
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
 * Fill form field by label
 */
export async function fillFormField(
  page: Page,
  label: string,
  value: string
): Promise<void> {
  const field = page.getByLabel(label, { exact: false });
  await field.fill(value);
}

/**
 * Select dropdown option by label
 */
export async function selectDropdownOption(
  page: Page,
  label: string,
  value: string
): Promise<void> {
  const select = page.getByLabel(label, { exact: false });
  await select.selectOption(value);
}

/**
 * Click button by name
 */
export async function clickButton(page: Page, name: string): Promise<void> {
  const button = page.getByRole('button', { name, exact: false });
  await button.click();
}

/**
 * Verify page heading
 */
export async function verifyPageHeading(
  page: Page,
  heading: string
): Promise<boolean> {
  const headingElement = page.getByRole('heading', { name: heading, exact: false });
  return await headingElement.isVisible();
}

/**
 * Open modal by clicking button
 */
export async function openModal(page: Page, buttonName: string): Promise<void> {
  await clickButton(page, buttonName);
  // Wait for modal to be visible
  await page.waitForTimeout(500);
}

/**
 * Close modal by clicking cancel or escape
 */
export async function closeModal(page: Page, useCancelButton: boolean = true): Promise<void> {
  if (useCancelButton) {
    await clickButton(page, 'Cancel');
  } else {
    await page.keyboard.press('Escape');
  }
  // Wait for modal to close
  await page.waitForTimeout(500);
}

/**
 * Verify toast/notification message
 */
export async function verifyNotification(
  page: Page,
  message: string | RegExp
): Promise<boolean> {
  const notification = typeof message === 'string'
    ? page.getByText(message, { exact: false })
    : page.getByText(message);
  return await notification.isVisible({ timeout: 5000 });
}

/**
 * Take screenshot for debugging
 */
export async function takeDebugScreenshot(
  page: Page,
  name: string
): Promise<void> {
  await page.screenshot({ path: `screenshots/${name}.png`, fullPage: true });
}

/**
 * Get current URL path
 */
export async function getCurrentPath(page: Page): Promise<string> {
  const url = new URL(page.url());
  return url.pathname;
}

/**
 * Verify element has specific class
 */
export async function hasClass(
  page: Page,
  selector: string,
  className: string
): Promise<boolean> {
  const element = page.locator(selector);
  const classes = await element.getAttribute('class');
  return classes?.includes(className) ?? false;
}

/**
 * Wait for specific text to appear
 */
export async function waitForText(
  page: Page,
  text: string | RegExp,
  timeout: number = 5000
): Promise<void> {
  const element = typeof text === 'string'
    ? page.getByText(text, { exact: false })
    : page.getByText(text);
  await element.waitFor({ state: 'visible', timeout });
}

/**
 * Count elements matching selector
 */
export async function countElements(
  page: Page,
  selector: string
): Promise<number> {
  return await page.locator(selector).count();
}

/**
 * Get input value by label
 */
export async function getInputValue(
  page: Page,
  label: string
): Promise<string> {
  const input = page.getByLabel(label, { exact: false });
  return await input.inputValue();
}

/**
 * Verify URL contains path
 */
export async function verifyURLContains(
  page: Page,
  path: string
): Promise<boolean> {
  return page.url().includes(path);
}

/**
 * Mock API response
 */
export async function mockAPIResponse(
  page: Page,
  url: string | RegExp,
  response: unknown,
  status: number = 200
): Promise<void> {
  await page.route(url, (route) => {
    route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

/**
 * Mock API error
 */
export async function mockAPIError(
  page: Page,
  url: string | RegExp,
  status: number = 500,
  message: string = 'Internal Server Error'
): Promise<void> {
  await page.route(url, (route) => {
    route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify({ detail: message }),
    });
  });
}

/**
 * Set viewport size
 */
export async function setViewportSize(
  page: Page,
  width: number,
  height: number
): Promise<void> {
  await page.setViewportSize({ width, height });
}

// ============================================================================
// Common Viewport Sizes
// ============================================================================

export const VIEWPORT_SIZES = {
  mobile: { width: 375, height: 667 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1280, height: 800 },
  largeDesktop: { width: 1920, height: 1080 },
};

// ============================================================================
// Common Timeouts
// ============================================================================

export const TIMEOUTS = {
  short: 1000,
  medium: 3000,
  long: 5000,
  veryLong: 10000,
};

// ============================================================================
// Common Selectors
// ============================================================================

export const SELECTORS = {
  loadingSpinner: '.animate-spin',
  errorMessage: '[class*="error"]',
  successMessage: '[class*="success"]',
  modal: '[role="dialog"]',
  card: '.card',
  button: 'button',
  input: 'input',
  select: 'select',
  table: 'table',
};
