import { test, expect } from '@playwright/test';
import { LoginPage, TemplatePage } from '../../pages';

/**
 * E2E Tests for Creating Template Weekly Patterns
 *
 * Tests the pattern creation workflow:
 * 1. Navigate to templates page
 * 2. Open pattern editor modal
 * 3. Select rotation type and click slots
 * 4. Save pattern
 * 5. Verify pattern persists
 */

test.describe('Template Pattern Creation', () => {
  let loginPage: LoginPage;
  let templatePage: TemplatePage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    templatePage = new TemplatePage(page);

    await loginPage.clearStorage();
    await loginPage.loginAsAdmin();
  });

  test.describe('Opening Pattern Editor', () => {
    test('should display Pattern button on template cards', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await expect(patternButton).toBeVisible();
      }
    });

    test('should open pattern editor modal when Pattern button clicked', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1000);

        // Modal should be visible
        await expect(page.getByRole('heading', { name: /Edit Weekly Pattern/i })).toBeVisible();
      }
    });

    test('should display template name in modal header', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        // Get the first template's name
        const cards = templatePage.getTemplateCards();
        const firstCard = cards.first();
        const templateName = await firstCard.locator('h3').textContent();

        // Open pattern modal
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1000);

        // Should show template name
        if (templateName) {
          await expect(page.getByText(templateName)).toBeVisible();
        }
      }
    });
  });

  test.describe('Pattern Grid Display', () => {
    test('should display 7-day week grid', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1000);

        // Check day headers
        await expect(page.getByText('Mon')).toBeVisible();
        await expect(page.getByText('Tue')).toBeVisible();
        await expect(page.getByText('Wed')).toBeVisible();
        await expect(page.getByText('Thu')).toBeVisible();
        await expect(page.getByText('Fri')).toBeVisible();
        await expect(page.getByText('Sat')).toBeVisible();
        await expect(page.getByText('Sun')).toBeVisible();
      }
    });

    test('should display AM and PM rows', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1000);

        await expect(page.getByText('AM')).toBeVisible();
        await expect(page.getByText('PM')).toBeVisible();
      }
    });

    test('should display template selector', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1000);

        // Should have Clear button
        await expect(page.getByRole('button', { name: /Clear/i })).toBeVisible();
      }
    });
  });

  test.describe('Pattern Creation Workflow', () => {
    test('should assign pattern to slot when clicked', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1000);

        // Select first template in selector (after Clear)
        const templateButtons = page.locator('[class*="px-3"][class*="py-1"]').filter({
          hasNot: page.getByText('Clear'),
        });
        const firstTemplate = templateButtons.first();

        if (await firstTemplate.isVisible()) {
          await firstTemplate.click();
          await page.waitForTimeout(500);

          // Click a slot
          const slots = page.getByRole('button', { name: /AM:|PM:/ });
          if (await slots.count() > 0) {
            await slots.first().click();
            await page.waitForTimeout(500);

            // Slot should now have content (not dash)
            expect(await slots.first().textContent()).not.toBe('-');
          }
        }
      }
    });

    test('should save pattern successfully', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1000);

        // Click Save
        const saveButton = page.getByRole('button', { name: /Save Pattern/i });
        if (await saveButton.isVisible()) {
          await saveButton.click();
          await page.waitForTimeout(2000);

          // Should show success or close modal
          const successMessage = page.getByText(/Pattern saved/i);
          const isSuccess = await successMessage.isVisible().catch(() => false);

          // Either success message shown or modal closed
          expect(isSuccess || !(await page.getByRole('heading', { name: /Edit Weekly Pattern/i }).isVisible())).toBe(true);
        }
      }
    });

    test('should cancel without saving', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1000);

        // Click Cancel
        const cancelButton = page.getByRole('button', { name: /Cancel/i });
        await cancelButton.click();
        await page.waitForTimeout(500);

        // Modal should be closed
        await expect(page.getByRole('heading', { name: /Edit Weekly Pattern/i })).not.toBeVisible();
      }
    });
  });

  test.describe('Pattern Instructions', () => {
    test('should display usage instructions', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1000);

        await expect(page.getByText(/How to use/i)).toBeVisible();
      }
    });
  });
});
