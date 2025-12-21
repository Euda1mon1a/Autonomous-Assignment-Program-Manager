import { Page, expect, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * TemplatePage - Page object for template library
 *
 * Handles template browsing, creation, editing, and sharing interactions
 */
export class TemplatePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to templates page
   */
  async navigate(): Promise<void> {
    await this.goto('/templates');
    await this.waitForPageLoad();
  }

  /**
   * Verify template library page is loaded
   */
  async verifyTemplateLibraryPage(): Promise<void> {
    await expect(this.getHeading('Template Library')).toBeVisible();
  }

  /**
   * Get "New Template" button
   */
  getNewTemplateButton(): Locator {
    return this.getButton(/New Template/i);
  }

  /**
   * Click "New Template" button
   */
  async clickNewTemplate(): Promise<void> {
    await this.getNewTemplateButton().click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Get template search input
   */
  getSearchInput(): Locator {
    return this.page.locator('input[placeholder*="Search" i], input[type="search"]').first();
  }

  /**
   * Search for templates
   */
  async searchTemplates(query: string): Promise<void> {
    const searchInput = this.getSearchInput();
    if (await this.isVisible(searchInput)) {
      await searchInput.fill(query);
      await this.page.waitForTimeout(1000); // Wait for search results
    }
  }

  /**
   * Get category tabs/pills
   */
  getCategoryButtons(): Locator {
    return this.page.locator('[class*="pill"], button[role="tab"]');
  }

  /**
   * Select a template category
   */
  async selectCategory(category: string): Promise<void> {
    const categoryButton = this.page.getByRole('button', { name: new RegExp(category, 'i') });
    if (await this.isVisible(categoryButton)) {
      await categoryButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Get template cards
   */
  getTemplateCards(): Locator {
    return this.page.locator('[class*="card"]').filter({ has: this.page.locator('h3') });
  }

  /**
   * Get template count
   */
  async getTemplateCount(): Promise<number> {
    return await this.getTemplateCards().count();
  }

  /**
   * Click on a template card by index
   */
  async clickTemplateCard(index: number): Promise<void> {
    const cards = this.getTemplateCards();
    await cards.nth(index).click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Click on a template card by name
   */
  async clickTemplateByName(name: string): Promise<void> {
    const template = this.page.locator('[class*="card"]').filter({ hasText: name });
    if (await this.isVisible(template)) {
      await template.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Get template preview modal
   */
  getPreviewModal(): Locator {
    return this.page.locator('[class*="modal"], [role="dialog"]').filter({ hasText: /Preview|Template/i });
  }

  /**
   * Open template preview
   */
  async previewTemplate(index: number): Promise<void> {
    const cards = this.getTemplateCards();
    const previewButton = cards.nth(index).getByRole('button', { name: /Preview|View/i });
    if (await this.isVisible(previewButton)) {
      await previewButton.click();
      await this.page.waitForTimeout(500);
    } else {
      // If no preview button, click the card itself
      await this.clickTemplateCard(index);
    }
  }

  /**
   * Close preview modal
   */
  async closePreview(): Promise<void> {
    const closeButton = this.page.getByRole('button', { name: /Close|Cancel/i }).first();
    await closeButton.click();
    await this.page.waitForTimeout(300);
  }

  /**
   * Switch between My Templates and Predefined Templates tabs
   */
  async switchTab(tab: 'my-templates' | 'predefined'): Promise<void> {
    const tabName = tab === 'my-templates' ? 'My Templates' : 'Predefined Templates';
    const tabButton = this.page.getByRole('button', { name: new RegExp(tabName, 'i') });
    await tabButton.click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Get view mode toggle buttons (Grid/List)
   */
  getViewModeButtons(): Locator {
    return this.page.locator('button[title*="view" i]');
  }

  /**
   * Switch view mode
   */
  async switchViewMode(mode: 'grid' | 'list'): Promise<void> {
    const viewButton = this.page.locator(`button[title*="${mode} view" i]`);
    if (await this.isVisible(viewButton)) {
      await viewButton.click();
      await this.page.waitForTimeout(300);
    }
  }

  /**
   * Share a template
   */
  async shareTemplate(index: number): Promise<void> {
    const cards = this.getTemplateCards();
    const shareButton = cards.nth(index).getByRole('button', { name: /Share/i });
    if (await this.isVisible(shareButton)) {
      await shareButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Get share modal
   */
  getShareModal(): Locator {
    return this.page.locator('[class*="modal"], [role="dialog"]').filter({ hasText: /Share/i });
  }

  /**
   * Duplicate a template
   */
  async duplicateTemplate(index: number): Promise<void> {
    const cards = this.getTemplateCards();
    const duplicateButton = cards.nth(index).getByRole('button', { name: /Duplicate|Copy/i });
    if (await this.isVisible(duplicateButton)) {
      await duplicateButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Delete a template
   */
  async deleteTemplate(index: number): Promise<void> {
    const cards = this.getTemplateCards();
    const deleteButton = cards.nth(index).getByRole('button', { name: /Delete/i });
    if (await this.isVisible(deleteButton)) {
      await deleteButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Confirm delete action
   */
  async confirmDelete(): Promise<void> {
    const confirmButton = this.page.getByRole('button', { name: /Delete|Confirm/i }).last();
    await confirmButton.click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Edit a template
   */
  async editTemplate(index: number): Promise<void> {
    const cards = this.getTemplateCards();
    const editButton = cards.nth(index).getByRole('button', { name: /Edit/i });
    if (await this.isVisible(editButton)) {
      await editButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Get template editor modal
   */
  getEditorModal(): Locator {
    return this.page.locator('[class*="modal"], [role="dialog"]').filter({ hasText: /Template|Editor/i });
  }

  /**
   * Fill template form
   */
  async fillTemplateForm(data: {
    name?: string;
    category?: string;
    description?: string;
  }): Promise<void> {
    if (data.name) {
      const nameInput = this.page.locator('input[name*="name" i], input[label*="name" i]').first();
      if (await this.isVisible(nameInput)) {
        await nameInput.fill(data.name);
      }
    }

    if (data.category) {
      const categorySelect = this.page.locator('select[name*="category" i]').first();
      if (await this.isVisible(categorySelect)) {
        await categorySelect.selectOption(data.category);
      }
    }

    if (data.description) {
      const descInput = this.page.locator('textarea[name*="description" i], input[name*="description" i]').first();
      if (await this.isVisible(descInput)) {
        await descInput.fill(data.description);
      }
    }
  }

  /**
   * Save template
   */
  async saveTemplate(): Promise<void> {
    const saveButton = this.getButton(/Save|Create/i);
    await saveButton.click();
    await this.page.waitForTimeout(1000);
  }

  /**
   * Import a predefined template
   */
  async importPredefinedTemplate(index: number): Promise<void> {
    const importButtons = this.page.getByRole('button', { name: /Import/i });
    const count = await importButtons.count();
    if (count > index) {
      await importButtons.nth(index).click();
      await this.page.waitForTimeout(1000);
    }
  }

  /**
   * Verify empty state
   */
  async verifyEmptyState(): Promise<void> {
    const emptyState = this.page.locator('[class*="empty"]').or(this.getText(/No templates/i));
    await expect(emptyState).toBeVisible();
  }

  /**
   * Verify template exists by name
   */
  async verifyTemplateExists(name: string): Promise<void> {
    const template = this.page.locator('[class*="card"]').filter({ hasText: name });
    await expect(template).toBeVisible();
  }

  /**
   * Apply filters
   */
  async applyFilters(filters: { category?: string; search?: string }): Promise<void> {
    if (filters.search) {
      await this.searchTemplates(filters.search);
    }
    if (filters.category) {
      await this.selectCategory(filters.category);
    }
    await this.page.waitForTimeout(500);
  }

  /**
   * Clear all filters
   */
  async clearFilters(): Promise<void> {
    const clearButton = this.page.getByRole('button', { name: /Clear/i }).first();
    if (await this.isVisible(clearButton)) {
      await clearButton.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * Get total results count from UI
   */
  async getTotalResults(): Promise<number | null> {
    const resultsText = this.page.locator('text=/\\d+ (templates?|results?)/i').first();
    if (await this.isVisible(resultsText)) {
      const text = await resultsText.textContent();
      const match = text?.match(/(\d+)/);
      return match ? parseInt(match[1]) : null;
    }
    return null;
  }
}
