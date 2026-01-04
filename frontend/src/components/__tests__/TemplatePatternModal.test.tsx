/**
 * Tests for TemplatePatternModal component.
 *
 * Tests cover:
 * - Modal opening/closing
 * - Loading states
 * - Error handling
 * - Save/cancel functionality
 * - Integration with WeeklyGridEditor
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { ReactNode } from 'react';

import { TemplatePatternModal } from '../TemplatePatternModal';

// ============================================================================
// Test Setup
// ============================================================================

const API_BASE = 'http://localhost:8000/api';

const mockPatterns = [
  {
    id: 'pattern-1',
    rotation_template_id: 'template-1',
    day_of_week: 1,
    time_of_day: 'AM' as const,
    activity_type: 'fm_clinic',
    linked_template_id: 'clinic-1',
    is_protected: false,
    notes: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockTemplates = {
  items: [
    {
      id: 'clinic-1',
      name: 'Clinic',
      activity_type: 'clinic',
      abbreviation: 'C',
      display_abbreviation: 'Clinic',
      font_color: 'text-blue-800',
      background_color: 'bg-blue-100',
    },
  ],
  total: 1,
};

// MSW Server
const server = setupServer(
  http.get(`${API_BASE}/rotation-templates/:id/patterns`, () => {
    return HttpResponse.json(mockPatterns);
  }),
  http.put(`${API_BASE}/rotation-templates/:id/patterns`, async () => {
    return HttpResponse.json([]);
  }),
  http.get(`${API_BASE}/rotation-templates`, () => {
    return HttpResponse.json(mockTemplates);
  })
);

beforeEach(() => {
  server.listen({ onUnhandledRequest: 'bypass' });
});

afterEach(() => {
  server.resetHandlers();
  server.close();
});

// Query client wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

// ============================================================================
// Tests
// ============================================================================

describe('TemplatePatternModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    templateId: 'template-1',
    templateName: 'Test Template',
    onSaved: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render modal when isOpen is true', async () => {
      render(<TemplatePatternModal {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Edit Weekly Pattern/i })).toBeInTheDocument();
      });
    });

    it('should not render when isOpen is false', () => {
      render(
        <TemplatePatternModal {...defaultProps} isOpen={false} />,
        { wrapper: createWrapper() }
      );

      expect(
        screen.queryByRole('heading', { name: /Edit Weekly Pattern/i })
      ).not.toBeInTheDocument();
    });

    it('should display template name', async () => {
      render(<TemplatePatternModal {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Test Template')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading indicator while fetching data', async () => {
      // Add delay to pattern fetch
      server.use(
        http.get(`${API_BASE}/rotation-templates/:id/patterns`, async () => {
          await new Promise((r) => setTimeout(r, 100));
          return HttpResponse.json(mockPatterns);
        })
      );

      render(<TemplatePatternModal {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/Loading pattern/i)).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByText(/Loading pattern/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should show error message when fetch fails', async () => {
      server.use(
        http.get(`${API_BASE}/rotation-templates/:id/patterns`, () => {
          return HttpResponse.json(
            { detail: 'Template not found' },
            { status: 404 }
          );
        })
      );

      render(<TemplatePatternModal {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText(/Failed to load pattern/i)).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      server.use(
        http.get(`${API_BASE}/rotation-templates/:id/patterns`, () => {
          return HttpResponse.json(
            { detail: 'Server error' },
            { status: 500 }
          );
        })
      );

      render(<TemplatePatternModal {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Retry/i })
        ).toBeInTheDocument();
      });
    });
  });

  describe('Close Behavior', () => {
    it('should call onClose when close button is clicked', async () => {
      const onClose = vi.fn();
      const user = userEvent.setup();

      render(
        <TemplatePatternModal {...defaultProps} onClose={onClose} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByRole('heading')).toBeInTheDocument();
      });

      const closeButton = screen.getByRole('button', { name: /Close modal/i });
      await user.click(closeButton);

      expect(onClose).toHaveBeenCalled();
    });

    it('should call onClose when backdrop is clicked', async () => {
      const onClose = vi.fn();
      const user = userEvent.setup();

      render(
        <TemplatePatternModal {...defaultProps} onClose={onClose} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByRole('heading')).toBeInTheDocument();
      });

      // Click backdrop
      const backdrop = document.querySelector('.bg-black\\/50');
      if (backdrop) {
        await user.click(backdrop);
      }

      expect(onClose).toHaveBeenCalled();
    });

    it('should call onClose when Cancel button is clicked', async () => {
      const onClose = vi.fn();
      const user = userEvent.setup();

      render(
        <TemplatePatternModal {...defaultProps} onClose={onClose} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Cancel/i })
        ).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Save Behavior', () => {
    it('should call onSaved after successful save', async () => {
      const onSaved = vi.fn();
      const user = userEvent.setup();

      render(
        <TemplatePatternModal {...defaultProps} onSaved={onSaved} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Save Pattern/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /Save Pattern/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(onSaved).toHaveBeenCalled();
      });
    });

    it('should show success message after save', async () => {
      const user = userEvent.setup();

      render(<TemplatePatternModal {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Save Pattern/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /Save Pattern/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/Pattern saved!/i)).toBeInTheDocument();
      });
    });

    it('should show error message when save fails', async () => {
      server.use(
        http.put(`${API_BASE}/rotation-templates/:id/patterns`, () => {
          return HttpResponse.json(
            { detail: 'Validation error' },
            { status: 400 }
          );
        })
      );

      const user = userEvent.setup();

      render(<TemplatePatternModal {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /Save Pattern/i })
        ).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /Save Pattern/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Failed to save pattern/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Grid Editor Integration', () => {
    it('should render WeeklyGridEditor with data', async () => {
      render(<TemplatePatternModal {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        // Check grid headers are rendered
        expect(screen.getByText('Mon')).toBeInTheDocument();
        expect(screen.getByText('AM')).toBeInTheDocument();
        expect(screen.getByText('PM')).toBeInTheDocument();
      });
    });

    it('should show instructions at bottom', async () => {
      render(<TemplatePatternModal {...defaultProps} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText(/How to use:/i)).toBeInTheDocument();
      });
    });
  });
});
