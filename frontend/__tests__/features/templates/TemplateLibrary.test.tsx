/**
 * Tests for TemplateLibrary Component
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { TemplateLibrary } from '@/features/templates/components/TemplateLibrary';
import { createWrapper } from '../../utils/test-utils';

// Mock child components
jest.mock('@/features/templates/components/TemplateSearch', () => ({
  TemplateSearch: () => <div data-testid="template-search">Search</div>,
}));

jest.mock('@/features/templates/components/TemplateCategories', () => ({
  TemplateCategories: () => <div data-testid="template-categories">Categories</div>,
}));

jest.mock('@/features/templates/components/TemplateList', () => ({
  TemplateList: () => <div data-testid="template-list">List</div>,
  PredefinedTemplateCard: () => <div>Predefined Card</div>,
}));

describe('TemplateLibrary', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should render library header', async () => {
    render(<TemplateLibrary />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Template Library')).toBeInTheDocument();
    });
  });

  it('should render New Template button', async () => {
    render(<TemplateLibrary />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('New Template')).toBeInTheDocument();
    });
  });

  it('should show My Templates tab by default', async () => {
    render(<TemplateLibrary />, { wrapper: createWrapper() });

    await waitFor(() => {
      const myTemplatesTab = screen.getByText('My Templates');
      expect(myTemplatesTab.closest('button')).toHaveClass('border-blue-600');
    });
  });

  it('should switch to Predefined Templates tab', async () => {
    const user = userEvent.setup();
    render(<TemplateLibrary />, { wrapper: createWrapper() });

    await waitFor(() => {
      const predefinedTab = screen.getByText('Predefined Templates');
      expect(predefinedTab).toBeInTheDocument();
    });

    const predefinedTab = screen.getByText('Predefined Templates');
    await user.click(predefinedTab);

    await waitFor(() => {
      expect(predefinedTab.closest('button')).toHaveClass('border-blue-600');
    });
  });

  it('should show view mode toggle buttons', async () => {
    render(<TemplateLibrary />, { wrapper: createWrapper() });

    await waitFor(() => {
      const buttons = screen.getAllByRole('button');
      const gridButton = buttons.find(btn => btn.getAttribute('title') === 'Grid view');
      const listButton = buttons.find(btn => btn.getAttribute('title') === 'List view');
      expect(gridButton).toBeInTheDocument();
      expect(listButton).toBeInTheDocument();
    });
  });

  it('should toggle view mode', async () => {
    const user = userEvent.setup();
    render(<TemplateLibrary />, { wrapper: createWrapper() });

    await waitFor(() => {
      const buttons = screen.getAllByRole('button');
      const listButton = buttons.find(btn => btn.getAttribute('title') === 'List view');
      expect(listButton).toBeInTheDocument();
    });

    const buttons = screen.getAllByRole('button');
    const listButton = buttons.find(btn => btn.getAttribute('title') === 'List view');
    if (listButton) {
      await user.click(listButton);
      await waitFor(() => {
        expect(listButton).toHaveClass('bg-gray-200');
      });
    }
  });

  it('should render search component', async () => {
    render(<TemplateLibrary />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('template-search')).toBeInTheDocument();
    });
  });

  it('should render categories component', async () => {
    render(<TemplateLibrary />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('template-categories')).toBeInTheDocument();
    });
  });

  it('should render template list', async () => {
    render(<TemplateLibrary />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('template-list')).toBeInTheDocument();
    });
  });

  it('should show template count in My Templates tab', async () => {
    render(<TemplateLibrary />, { wrapper: createWrapper() });

    await waitFor(() => {
      const myTemplatesTab = screen.getByText('My Templates');
      const count = myTemplatesTab.parentElement?.querySelector('.bg-gray-100');
      expect(count).toBeInTheDocument();
    });
  });
});
