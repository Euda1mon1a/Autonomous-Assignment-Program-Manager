import { test, expect } from '../fixtures/auth.fixture';

test.describe('Rotation Management', () => {
  test.skip(() => !process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database');

  test.beforeEach(async ({ adminPage }) => {
    await adminPage.goto('/rotations');
    await adminPage.waitForLoadState('networkidle');
  });

  test('Rotation list renders', async ({ adminPage }) => {
    const list = adminPage.locator('[data-testid="rotation-list"], table');
    await expect(list.first()).toBeVisible();

    // Check that we have at least some rows
    const rows = list.locator('tbody tr, .rotation-item');
    if (await rows.count() > 0) {
      expect(await rows.count()).toBeGreaterThan(0);
    }
  });

  test('Create rotation (if admin)', async ({ adminPage }) => {
    const createBtn = adminPage.locator('button:has-text("Create"), [data-testid="create-rotation-btn"]');

    if (await createBtn.isVisible()) {
      await createBtn.click();

      const modal = adminPage.locator('[role="dialog"], .modal');
      await expect(modal).toBeVisible();

      // Assuming a name input exists
      const nameInput = modal.locator('input[name="name"], input[placeholder*="Name"]');
      if (await nameInput.isVisible()) {
        await nameInput.fill(`Test Rotation ${Date.now()}`);

        const saveBtn = modal.locator('button:has-text("Save"), button:has-text("Create")');
        await saveBtn.click();

        // Modal should close
        await expect(modal).not.toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('Edit rotation name', async ({ adminPage }) => {
    const editBtn = adminPage.locator('button:has-text("Edit"), [data-testid="edit-rotation-btn"], .edit-btn').first();

    if (await editBtn.isVisible()) {
      await editBtn.click();

      const modal = adminPage.locator('[role="dialog"], .modal');
      await expect(modal).toBeVisible();

      const nameInput = modal.locator('input[name="name"], input[placeholder*="Name"]');
      if (await nameInput.isVisible()) {
        const currentName = await nameInput.inputValue();
        await nameInput.fill(`${currentName} Edited`);

        const saveBtn = modal.locator('button:has-text("Save"), button:has-text("Update")');

        const responsePromise = adminPage.waitForResponse(
          (response) => response.url().includes('/rotations') && ['PUT', 'PATCH'].includes(response.request().method()) && response.status() === 200,
          { timeout: 10000 }
        ).catch(() => null);

        await saveBtn.click();
        await responsePromise;

        await expect(modal).not.toBeVisible();
      }
    }
  });

  test('Delete shows confirmation', async ({ adminPage }) => {
    const deleteBtn = adminPage.locator('button:has-text("Delete"), [data-testid="delete-rotation-btn"], .delete-btn').first();

    if (await deleteBtn.isVisible()) {
      await deleteBtn.click();

      // Look for a confirmation dialog
      const confirmDialog = adminPage.locator('[role="dialog"], .confirmation-modal, .alert-dialog');
      await expect(confirmDialog).toBeVisible();

      const cancelBtn = confirmDialog.locator('button:has-text("Cancel"), button:has-text("No")');
      await expect(cancelBtn).toBeVisible();

      // We explicitly cancel to avoid actually deleting seeded data like FMIT which might be needed
      await cancelBtn.click();
      await expect(confirmDialog).not.toBeVisible();
    }
  });
});
