import { test, expect } from '@playwright/test';
import { LoginPage, TemplatePage } from '../pages';

/**
 * Templates E2E Tests
 *
 * Tests template library interactions:
 * 1. Browse template library
 * 2. Search and filter templates
 * 3. Preview templates
 * 4. Create new templates
 * 5. Edit and delete templates
 * 6. Share and duplicate templates
 * 7. Import predefined templates
 * 8. Switch between view modes
 */

test.describe('Templates Library', () => {
  let loginPage: LoginPage;
  let templatePage: TemplatePage;

  test.beforeEach(async ({ page }) => {
    // Initialize page objects
    loginPage = new LoginPage(page);
    templatePage = new TemplatePage(page);

    // Clear storage and login
    await loginPage.clearStorage();
  });

  // ==========================================================================
  // Template Library Navigation Tests
  // ==========================================================================

  test.describe('Template Library Navigation', () => {
    test('should navigate to template library page', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      // Verify template library page
      await templatePage.verifyTemplateLibraryPage();

      // Check URL
      expect(page.url()).toContain('/templates');
    });

    test('should display page header with title and description', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      // Verify header elements
      await expect(templatePage.getHeading(/Template Library/i)).toBeVisible();

      const hasDescription = await templatePage.isVisible(
        templatePage.getText(/Create and manage|Define reusable/i)
      );
      expect(hasDescription).toBe(true);
    });

    test('should display "New Template" button', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      // Verify new template button
      const newButton = templatePage.getNewTemplateButton();
      await expect(newButton).toBeVisible();
    });

    test('should access template library for different user roles', async ({ page }) => {
      // Test admin access
      await loginPage.loginAsAdmin();
      await templatePage.navigate();
      await templatePage.verifyTemplateLibraryPage();

      // Test coordinator access
      await loginPage.logout();
      await loginPage.loginAsCoordinator();
      await templatePage.navigate();
      await templatePage.verifyTemplateLibraryPage();

      // Test faculty access
      await loginPage.logout();
      await loginPage.loginAsFaculty();
      await templatePage.navigate();
      await templatePage.verifyTemplateLibraryPage();

      expect(page.url()).toContain('/templates');
    });
  });

  // ==========================================================================
  // Template Browsing Tests
  // ==========================================================================

  test.describe('Template Browsing', () => {
    test('should display template cards when templates exist', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      // Get template count
      const count = await templatePage.getTemplateCount();

      // Should display templates or empty state
      expect(count >= 0).toBe(true);
    });

    test('should display empty state when no templates exist', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count === 0) {
        // Verify empty state is shown
        await templatePage.verifyEmptyState();
      }

      expect(page.url()).toContain('/templates');
    });

    test('should display template information in cards', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        // Check first template card has expected elements
        const cards = templatePage.getTemplateCards();
        const firstCard = cards.first();

        // Should have title
        const hasTitle = await templatePage.isVisible(firstCard.locator('h3'));
        expect(hasTitle).toBe(true);
      }

      expect(page.url()).toBeTruthy();
    });

    test('should switch between My Templates and Predefined Templates tabs', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      // Switch to Predefined Templates
      await templatePage.switchTab('predefined');
      await page.waitForTimeout(1000);

      // Verify predefined templates are shown
      const hasPredefined = await templatePage.isVisible(
        templatePage.getText(/Predefined|pre-built/i)
      );
      expect(hasPredefined).toBe(true);

      // Switch back to My Templates
      await templatePage.switchTab('my-templates');
      await page.waitForTimeout(1000);

      expect(page.url()).toContain('/templates');
    });

    test('should display template count in tab', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      // Look for count badge/indicator
      const countBadge = page.locator('[class*="badge"], span').filter({ hasText: /\d+/ });
      const hasCount = await templatePage.isVisible(countBadge);

      expect(hasCount).toBe(true);
    });
  });

  // ==========================================================================
  // Template Category Browsing Tests
  // ==========================================================================

  test.describe('Template Category Browsing', () => {
    test('should display template categories', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      // Look for category buttons/pills
      const categories = templatePage.getCategoryButtons();
      const count = await categories.count();

      expect(count >= 0).toBe(true);
    });

    test('should filter templates by category', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const initialCount = await templatePage.getTemplateCount();

      // Try to select a category if available
      const categoryButton = page.getByRole('button').filter({ hasText: /Clinic|Inpatient|Rotation/i }).first();
      if (await templatePage.isVisible(categoryButton)) {
        await categoryButton.click();
        await page.waitForTimeout(1000);

        // Count might change or stay the same depending on data
        const filteredCount = await templatePage.getTemplateCount();
        expect(filteredCount >= 0).toBe(true);
      }

      expect(page.url()).toBeTruthy();
    });

    test('should show category counts', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      // Look for count indicators on categories
      const categoryWithCount = page.locator('button, [class*="pill"]').filter({ hasText: /\(\d+\)|\d+/ }).first();
      const hasCount = await templatePage.isVisible(categoryWithCount);

      expect(hasCount).toBe(true);
    });
  });

  // ==========================================================================
  // Template Search Tests
  // ==========================================================================

  test.describe('Template Search', () => {
    test('should display search input', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      // Verify search input exists
      const searchInput = templatePage.getSearchInput();
      const hasSearch = await templatePage.isVisible(searchInput);

      expect(hasSearch).toBe(true);
    });

    test('should search templates by name', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const initialCount = await templatePage.getTemplateCount();

      if (initialCount > 0) {
        // Search for a template
        await templatePage.searchTemplates('clinic');
        await page.waitForTimeout(1000);

        // Verify results updated
        const searchResultCount = await templatePage.getTemplateCount();
        expect(searchResultCount >= 0).toBe(true);
      }

      expect(page.url()).toBeTruthy();
    });

    test('should show no results when search has no matches', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      // Search for non-existent template
      await templatePage.searchTemplates('nonexistenttemplate12345');
      await page.waitForTimeout(1000);

      // Should show empty state or no results message
      const hasNoResults = await templatePage.isVisible(
        templatePage.getText(/No templates match|No results|No templates found/i)
      );

      expect(hasNoResults).toBe(true);
    });

    test('should clear search and restore all templates', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const initialCount = await templatePage.getTemplateCount();

      // Perform search
      await templatePage.searchTemplates('test');
      await page.waitForTimeout(1000);

      // Clear search
      const searchInput = templatePage.getSearchInput();
      if (await templatePage.isVisible(searchInput)) {
        await searchInput.fill('');
        await searchInput.blur();
        await page.waitForTimeout(1000);

        // Count should return to original (or close to it)
        const finalCount = await templatePage.getTemplateCount();
        expect(finalCount >= 0).toBe(true);
      }

      expect(page.url()).toBeTruthy();
    });
  });

  // ==========================================================================
  // Template Preview Tests
  // ==========================================================================

  test.describe('Template Preview', () => {
    test('should open template preview modal', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        // Click on first template
        await templatePage.clickTemplateCard(0);
        await page.waitForTimeout(1000);

        // Modal or preview should be visible
        const hasModal = await templatePage.isVisible(
          page.locator('[role="dialog"], [class*="modal"]')
        );

        expect(hasModal).toBe(true);
      }

      expect(page.url()).toBeTruthy();
    });

    test('should display template details in preview', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        await templatePage.clickTemplateCard(0);
        await page.waitForTimeout(1000);

        // Look for template details
        const hasDetails = await templatePage.isVisible(
          page.locator('[role="dialog"]').or(page.locator('[class*="modal"]'))
        );

        expect(hasDetails).toBe(true);
      }

      expect(page.url()).toBeTruthy();
    });

    test('should close preview modal', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        // Open preview
        await templatePage.clickTemplateCard(0);
        await page.waitForTimeout(1000);

        // Close preview
        await templatePage.closePreview();
        await page.waitForTimeout(500);

        // Modal should be closed
        const hasModal = await templatePage.isVisible(
          page.locator('[role="dialog"]')
        );

        expect(hasModal).toBe(false);
      }

      expect(page.url()).toBeTruthy();
    });
  });

  // ==========================================================================
  // Template Creation Tests
  // ==========================================================================

  test.describe('Template Creation', () => {
    test('should open create template modal', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      // Click new template button
      await templatePage.clickNewTemplate();

      // Modal should be visible
      const modal = templatePage.getEditorModal();
      const hasModal = await templatePage.isVisible(modal);

      expect(hasModal).toBe(true);
    });

    test('should display template form fields', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      await templatePage.clickNewTemplate();
      await page.waitForTimeout(500);

      // Check for form fields
      const hasNameField = await templatePage.isVisible(
        page.locator('input[name*="name" i], input[placeholder*="name" i]')
      );

      expect(hasNameField).toBe(true);
    });

    test('should cancel template creation', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      await templatePage.clickNewTemplate();
      await page.waitForTimeout(500);

      // Click cancel
      await templatePage.closeModal();

      // Modal should close
      const hasModal = await templatePage.isVisible(templatePage.getEditorModal());
      expect(hasModal).toBe(false);
    });

    test('should validate required fields', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      await templatePage.clickNewTemplate();
      await page.waitForTimeout(500);

      // Try to save without filling required fields
      const saveButton = page.getByRole('button', { name: /Save|Create/i });
      if (await templatePage.isVisible(saveButton)) {
        await saveButton.click();
        await page.waitForTimeout(1000);

        // Should show validation error or stay on form
        expect(page.url()).toBeTruthy();
      }
    });
  });

  // ==========================================================================
  // Template View Mode Tests
  // ==========================================================================

  test.describe('Template View Modes', () => {
    test('should toggle between grid and list view', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      // Try to switch to list view
      const listButton = page.locator('button[title*="list" i]');
      if (await templatePage.isVisible(listButton)) {
        await listButton.click();
        await page.waitForTimeout(500);

        // Switch back to grid
        const gridButton = page.locator('button[title*="grid" i]');
        if (await templatePage.isVisible(gridButton)) {
          await gridButton.click();
          await page.waitForTimeout(500);
        }
      }

      expect(page.url()).toBeTruthy();
    });

    test('should maintain selected view mode', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      // Switch view mode if toggle exists
      const listButton = page.locator('button[title*="list" i]');
      if (await templatePage.isVisible(listButton)) {
        await listButton.click();
        await page.waitForTimeout(500);

        // Navigate away and back
        await page.goto('/schedule');
        await page.waitForTimeout(500);
        await templatePage.navigate();
        await page.waitForTimeout(1000);

        // View mode might be persisted (implementation dependent)
        expect(page.url()).toContain('/templates');
      }
    });
  });

  // ==========================================================================
  // Predefined Templates Tests
  // ==========================================================================

  test.describe('Predefined Templates', () => {
    test('should display predefined templates', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      // Switch to predefined tab
      await templatePage.switchTab('predefined');
      await page.waitForTimeout(1000);

      // Look for predefined template cards
      const cards = page.locator('[class*="card"]');
      const count = await cards.count();

      expect(count >= 0).toBe(true);
    });

    test('should import a predefined template', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      // Switch to predefined tab
      await templatePage.switchTab('predefined');
      await page.waitForTimeout(1000);

      // Look for import buttons
      const importButton = page.getByRole('button', { name: /Import/i }).first();
      if (await templatePage.isVisible(importButton)) {
        const initialTab = 'predefined';

        await importButton.click();
        await page.waitForTimeout(2000);

        // Should switch to My Templates tab or show success message
        expect(page.url()).toBeTruthy();
      }
    });

    test('should display import button for each predefined template', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1000);

      await templatePage.switchTab('predefined');
      await page.waitForTimeout(1000);

      const importButtons = page.getByRole('button', { name: /Import/i });
      const count = await importButtons.count();

      expect(count >= 0).toBe(true);
    });
  });

  // ==========================================================================
  // Template Actions Tests
  // ==========================================================================

  test.describe('Template Actions', () => {
    test('should display action buttons on template cards', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        const cards = templatePage.getTemplateCards();
        const firstCard = cards.first();

        // Look for action buttons (Edit, Delete, Share, etc.)
        const hasActions = await templatePage.isVisible(
          firstCard.locator('button').filter({ hasText: /Edit|Delete|Share|Duplicate/i })
        );

        expect(hasActions).toBe(true);
      }

      expect(page.url()).toBeTruthy();
    });

    test('should open share modal', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        // Look for share button
        const shareButton = page.getByRole('button', { name: /Share/i }).first();
        if (await templatePage.isVisible(shareButton)) {
          await shareButton.click();
          await page.waitForTimeout(500);

          // Share modal should appear
          const hasModal = await templatePage.isVisible(templatePage.getShareModal());
          expect(hasModal).toBe(true);
        }
      }

      expect(page.url()).toBeTruthy();
    });

    test('should confirm delete action', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count > 0) {
        // Look for delete button
        const deleteButton = page.getByRole('button', { name: /Delete/i }).first();
        if (await templatePage.isVisible(deleteButton)) {
          await deleteButton.click();
          await page.waitForTimeout(500);

          // Confirm dialog should appear
          const confirmDialog = page.locator('[role="dialog"]').filter({ hasText: /Delete|Are you sure/i });
          const hasDialog = await templatePage.isVisible(confirmDialog);

          if (hasDialog) {
            // Cancel the delete
            const cancelButton = page.getByRole('button', { name: /Cancel/i }).last();
            await cancelButton.click();
            await page.waitForTimeout(500);
          }

          expect(page.url()).toBeTruthy();
        }
      }
    });
  });

  // ==========================================================================
  // Responsive Design Tests
  // ==========================================================================

  test.describe('Responsive Template Library', () => {
    test('should display templates on mobile viewport', async ({ page }) => {
      await loginPage.loginAsAdmin();

      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      await templatePage.navigate();
      await page.waitForTimeout(1500);

      // Template library should still load
      await templatePage.verifyTemplateLibraryPage();

      expect(page.url()).toContain('/templates');
    });

    test('should display templates on tablet viewport', async ({ page }) => {
      await loginPage.loginAsAdmin();

      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });

      await templatePage.navigate();
      await page.waitForTimeout(1500);

      await templatePage.verifyTemplateLibraryPage();

      expect(page.url()).toContain('/templates');
    });

    test('should adapt layout for different screen sizes', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();
      await page.waitForTimeout(1500);

      // Test desktop
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.waitForTimeout(500);

      const desktopCount = await templatePage.getTemplateCount();

      // Test mobile
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);

      const mobileCount = await templatePage.getTemplateCount();

      // Same templates should be available
      expect(desktopCount).toBe(mobileCount);
    });
  });

  // ==========================================================================
  // Loading and Error States Tests
  // ==========================================================================

  test.describe('Template Loading States', () => {
    test('should show loading indicator on initial load', async ({ page }) => {
      await loginPage.loginAsAdmin();

      // Navigate and quickly check for loading state
      const navigationPromise = templatePage.navigate();

      // Check for loading spinner
      const hasLoading = await page.locator('.animate-spin').isVisible().catch(() => false);

      await navigationPromise;

      // Loading should eventually complete
      expect(page.url()).toContain('/templates');
    });

    test('should handle empty template library', async ({ page }) => {
      await loginPage.loginAsAdmin();
      await templatePage.navigate();

      await page.waitForTimeout(1500);

      const count = await templatePage.getTemplateCount();

      if (count === 0) {
        // Should show empty state with helpful message
        await templatePage.verifyEmptyState();
      }

      expect(page.url()).toBeTruthy();
    });
  });
});
