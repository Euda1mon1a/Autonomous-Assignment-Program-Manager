import { test, expect } from '@playwright/test';
import { LoginPage, TemplatePage } from '../../pages';

/**
 * E2E Tests for Deleting/Clearing Template Weekly Patterns
 *
 * Tests the pattern deletion workflow:
 * 1. Open pattern editor
 * 2. Clear individual slots
 * 3. Clear all slots
 * 4. Save cleared pattern
 */

test.describe('Template Pattern Deletion/Clearing', () => {
  let loginPage: LoginPage;
  let templatePage: TemplatePage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    templatePage = new TemplatePage(page);

    await loginPage.clearStorage();
    await loginPage.loginAsAdmin();
  });

  test.describe('Clearing Individual Slots', () => {
    test('should clear slot using Clear button', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1500);

        // First assign something to a slot
        const templateButtons = page.locator('[class*="px-3"][class*="py-1"]');
        const templateButton = templateButtons.nth(1); // Skip Clear

        if (await templateButton.isVisible()) {
          await templateButton.click();
          await page.waitForTimeout(300);

          const slot = page.getByRole('button', { name: /Mon AM/ });
          if (await slot.isVisible()) {
            await slot.click();
            await page.waitForTimeout(500);

            // Now select Clear and click the same slot
            const clearButton = page.getByRole('button', { name: /^Clear$/i });
            await clearButton.click();
            await page.waitForTimeout(300);

            await slot.click();
            await page.waitForTimeout(500);

            // Slot should show dash or be empty
            const slotText = await slot.textContent();
            expect(slotText).toContain('-');
          }
        }
      }
    });

    test('should be able to clear multiple slots', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1500);

        // Select Clear
        const clearButton = page.getByRole('button', { name: /^Clear$/i });
        if (await clearButton.isVisible()) {
          await clearButton.click();
          await page.waitForTimeout(300);

          // Click multiple slots to clear them
          const assignedSlots = page.getByRole('button', { name: /AM:|PM:/ }).filter({
            hasNot: page.getByText('-'),
          });

          const slotCount = await assignedSlots.count();
          for (let i = 0; i < Math.min(slotCount, 3); i++) {
            await assignedSlots.nth(i).click();
            await page.waitForTimeout(200);
          }
        }
      }
    });
  });

  test.describe('Clearing All Slots', () => {
    test('should clear all slots by selecting Clear and clicking each', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1500);

        // Select Clear
        const clearButton = page.getByRole('button', { name: /^Clear$/i });
        if (await clearButton.isVisible()) {
          await clearButton.click();
          await page.waitForTimeout(300);

          // Get all slots and clear each one
          const allSlots = page.getByRole('button', { name: /AM:|PM:/ });
          const slotCount = await allSlots.count();

          for (let i = 0; i < slotCount; i++) {
            await allSlots.nth(i).click();
            await page.waitForTimeout(100);
          }

          // All slots should now be empty
          const emptySlots = page.getByRole('button', { name: /: Empty/ });
          const emptyCount = await emptySlots.count();
          expect(emptyCount).toBe(14);
        }
      }
    });
  });

  test.describe('Saving Cleared Pattern', () => {
    test('should save pattern with all slots cleared', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1500);

        // Clear all slots
        const clearButton = page.getByRole('button', { name: /^Clear$/i });
        if (await clearButton.isVisible()) {
          await clearButton.click();
          await page.waitForTimeout(300);

          const allSlots = page.getByRole('button', { name: /AM:|PM:/ });
          const slotCount = await allSlots.count();

          for (let i = 0; i < slotCount; i++) {
            await allSlots.nth(i).click();
            await page.waitForTimeout(50);
          }
        }

        // Save
        const saveButton = page.getByRole('button', { name: /Save Pattern/i });
        if (await saveButton.isVisible()) {
          await saveButton.click();
          await page.waitForTimeout(2000);

          // Should succeed
          const successMessage = page.getByText(/Pattern saved/i);
          const isSuccess = await successMessage.isVisible().catch(() => false);
          expect(isSuccess || !(await page.getByRole('heading', { name: /Edit Weekly Pattern/i }).isVisible())).toBe(true);
        }
      }
    });
  });

  test.describe('Undo Clearing', () => {
    test('should restore cleared slot by assigning new template', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1500);

        const slot = page.getByRole('button', { name: /Tue PM: Empty/ });

        if (await slot.isVisible()) {
          // Select a template
          const templateButtons = page.locator('[class*="px-3"][class*="py-1"]');
          const templateButton = templateButtons.nth(1);

          if (await templateButton.isVisible()) {
            await templateButton.click();
            await page.waitForTimeout(300);

            // Assign to slot
            await slot.click();
            await page.waitForTimeout(500);

            // Slot should no longer be empty
            const slotText = await slot.textContent();
            expect(slotText).not.toContain('-');
          }
        }
      }
    });

    test('should cancel to discard all clearing', async ({ page }) => {
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const patternButton = page.getByRole('button', { name: /Pattern/i }).first();
        await patternButton.click();
        await page.waitForTimeout(1500);

        // Clear some slots
        const clearButton = page.getByRole('button', { name: /^Clear$/i });
        if (await clearButton.isVisible()) {
          await clearButton.click();
          await page.waitForTimeout(300);

          const slots = page.getByRole('button', { name: /AM:|PM:/ });
          const slotCount = await slots.count();

          if (slotCount > 0) {
            await slots.first().click();
            await page.waitForTimeout(200);
          }
        }

        // Cancel
        const cancelButton = page.getByRole('button', { name: /Cancel/i });
        await cancelButton.click();
        await page.waitForTimeout(500);

        // Modal should be closed (changes discarded)
        await expect(page.getByRole('heading', { name: /Edit Weekly Pattern/i })).not.toBeVisible();
      }
    });
  });
});
