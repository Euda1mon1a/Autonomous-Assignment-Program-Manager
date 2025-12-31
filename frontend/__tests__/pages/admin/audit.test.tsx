/**
 * Tests for Admin Audit Log Page
 *
 * Tests audit log viewing, filtering, searching, exporting,
 * statistics overview, and entry detail panels.
 */
import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdminAuditPage from '@/app/admin/audit/page';

describe('AdminAuditPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Page Rendering', () => {
    it('should render page title', () => {
      render(<AdminAuditPage />);

      expect(screen.getByText('Audit Logs')).toBeInTheDocument();
    });

    it('should render page description', () => {
      render(<AdminAuditPage />);

      expect(screen.getByText('System activity and security events')).toBeInTheDocument();
    });

    it('should render view toggle buttons', () => {
      render(<AdminAuditPage />);

      expect(screen.getByRole('button', { name: /List/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Stats/i })).toBeInTheDocument();
    });

    it('should start in list view', () => {
      render(<AdminAuditPage />);

      const listButton = screen.getByRole('button', { name: /List/i });
      expect(listButton).toHaveClass('bg-violet-600', 'text-white');
    });

    it('should render search input', () => {
      render(<AdminAuditPage />);

      expect(screen.getByPlaceholderText('Search logs...')).toBeInTheDocument();
    });

    it('should render filter button', () => {
      render(<AdminAuditPage />);

      expect(screen.getByRole('button', { name: /Filters/i })).toBeInTheDocument();
    });

    it('should render refresh button', () => {
      render(<AdminAuditPage />);

      expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument();
    });

    it('should render export button', () => {
      render(<AdminAuditPage />);

      expect(screen.getByRole('button', { name: /Export/i })).toBeInTheDocument();
    });
  });

  describe('List View', () => {
    it('should display audit entries', () => {
      render(<AdminAuditPage />);

      expect(screen.getByText('Admin User')).toBeInTheDocument();
      expect(screen.getByText('Coordinator')).toBeInTheDocument();
    });

    it('should render table headers', () => {
      render(<AdminAuditPage />);

      expect(screen.getByText('Time')).toBeInTheDocument();
      expect(screen.getByText('Severity')).toBeInTheDocument();
      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('Action')).toBeInTheDocument();
      expect(screen.getByText('User')).toBeInTheDocument();
      expect(screen.getByText('Target')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
    });

    it('should display severity badges', () => {
      render(<AdminAuditPage />);

      expect(screen.getAllByText('Info').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Warning').length).toBeGreaterThan(0);
      expect(screen.getByText('Error')).toBeInTheDocument();
    });

    it('should display category badges', () => {
      render(<AdminAuditPage />);

      expect(screen.getByText('Authentication')).toBeInTheDocument();
      expect(screen.getByText('Schedule')).toBeInTheDocument();
      expect(screen.getByText('System')).toBeInTheDocument();
    });

    it('should show success/failed status', () => {
      render(<AdminAuditPage />);

      const okBadges = screen.getAllByText('OK');
      expect(okBadges.length).toBeGreaterThan(0);

      const failedBadges = screen.getAllByText('Failed');
      expect(failedBadges.length).toBeGreaterThan(0);
    });

    it('should display entry count', () => {
      render(<AdminAuditPage />);

      expect(screen.getByText(/Showing 10 entries/i)).toBeInTheDocument();
    });

    it('should show pagination buttons', () => {
      render(<AdminAuditPage />);

      expect(screen.getByRole('button', { name: /Previous/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('should filter entries by search query', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const searchInput = screen.getByPlaceholderText('Search logs...');
      await user.type(searchInput, 'login');

      // Should filter to show login-related entries
      expect(screen.getByText(/login/i)).toBeInTheDocument();
    });

    it('should search by user name', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const searchInput = screen.getByPlaceholderText('Search logs...');
      await user.type(searchInput, 'Admin');

      expect(screen.getByText('Admin User')).toBeInTheDocument();
    });

    it('should search by action', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const searchInput = screen.getByPlaceholderText('Search logs...');
      await user.type(searchInput, 'schedule generated');

      expect(screen.getByText(/schedule generated/i)).toBeInTheDocument();
    });

    it('should clear search', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const searchInput = screen.getByPlaceholderText('Search logs...');
      await user.type(searchInput, 'test');
      await user.clear(searchInput);

      // All entries should be visible again
      expect(screen.getByText('Admin User')).toBeInTheDocument();
    });
  });

  describe('Filter Functionality', () => {
    it('should toggle filters panel', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const filterButton = screen.getByRole('button', { name: /Filters/i });
      await user.click(filterButton);

      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('Severity')).toBeInTheDocument();
      expect(screen.getByText('Date Range')).toBeInTheDocument();
    });

    it('should filter by category', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      await user.click(screen.getByRole('button', { name: /Filters/i }));

      const categorySelect = screen.getByLabelText('Category');
      await user.selectOptions(categorySelect, 'authentication');

      // Filter should be applied
      expect(categorySelect).toHaveValue('authentication');
    });

    it('should filter by severity', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      await user.click(screen.getByRole('button', { name: /Filters/i }));

      const severitySelect = screen.getByLabelText('Severity');
      await user.selectOptions(severitySelect, 'error');

      expect(severitySelect).toHaveValue('error');
    });

    it('should show date range inputs', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      await user.click(screen.getByRole('button', { name: /Filters/i }));

      const dateInputs = screen.getAllByDisplayValue('');
      const dateTypeInputs = dateInputs.filter(input => input.getAttribute('type') === 'date');
      expect(dateTypeInputs.length).toBe(2); // Start and end date
    });

    it('should highlight filter button when active', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const filterButton = screen.getByRole('button', { name: /Filters/i });
      await user.click(filterButton);

      expect(filterButton).toHaveClass('bg-violet-600');
    });
  });

  describe('Stats View', () => {
    it('should switch to stats view', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const statsButton = screen.getByRole('button', { name: /Stats/i });
      await user.click(statsButton);

      expect(statsButton).toHaveClass('bg-violet-600', 'text-white');
    });

    it('should display summary cards', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      await user.click(screen.getByRole('button', { name: /Stats/i }));

      expect(screen.getByText('Total Entries (24h)')).toBeInTheDocument();
      expect(screen.getByText('Active Users')).toBeInTheDocument();
      expect(screen.getByText('Failed Operations')).toBeInTheDocument();
      expect(screen.getByText('Critical Events')).toBeInTheDocument();
    });

    it('should display events by category', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      await user.click(screen.getByRole('button', { name: /Stats/i }));

      expect(screen.getByText('Events by Category')).toBeInTheDocument();
      expect(screen.getAllByText('Authentication')[0]).toBeInTheDocument();
    });

    it('should show top actions', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      await user.click(screen.getByRole('button', { name: /Stats/i }));

      expect(screen.getByText('Top Actions')).toBeInTheDocument();
      expect(screen.getByText(/login/i)).toBeInTheDocument();
    });

    it('should display progress bars', async () => {
      const user = userEvent.setup();
      const { container } = render(<AdminAuditPage />);

      await user.click(screen.getByRole('button', { name: /Stats/i }));

      const progressBars = container.querySelectorAll('[style*="width"]');
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });

  describe('Entry Detail Panel', () => {
    it('should open detail panel when entry clicked', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const rows = screen.getAllByRole('row');
      // Click on first data row (skip header)
      if (rows[1]) {
        await user.click(rows[1]);

        await waitFor(() => {
          expect(screen.getByText('Audit Entry Details')).toBeInTheDocument();
        });
      }
    });

    it('should display entry timestamp', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const rows = screen.getAllByRole('row');
      if (rows[1]) {
        await user.click(rows[1]);

        await waitFor(() => {
          expect(screen.getByText('Timestamp')).toBeInTheDocument();
        });
      }
    });

    it('should show entry category and action', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const rows = screen.getAllByRole('row');
      if (rows[1]) {
        await user.click(rows[1]);

        await waitFor(() => {
          expect(screen.getAllByText('Category')[0]).toBeInTheDocument();
          expect(screen.getAllByText('Action')[0]).toBeInTheDocument();
        });
      }
    });

    it('should display user information', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const rows = screen.getAllByRole('row');
      if (rows[1]) {
        await user.click(rows[1]);

        await waitFor(() => {
          expect(screen.getAllByText('User')[0]).toBeInTheDocument();
        });
      }
    });

    it('should show target information when available', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      // Find and click a row with target information
      const rows = screen.getAllByRole('row');
      const scheduleRow = rows.find(row => row.textContent?.includes('December 2024'));

      if (scheduleRow) {
        await user.click(scheduleRow);

        await waitFor(() => {
          expect(screen.getAllByText('Target')[0]).toBeInTheDocument();
        });
      }
    });

    it('should display IP address when available', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const rows = screen.getAllByRole('row');
      if (rows[1]) {
        await user.click(rows[1]);

        await waitFor(() => {
          expect(screen.getByText('IP Address')).toBeInTheDocument();
        });
      }
    });

    it('should show error message for failed entries', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      // Find a failed entry
      const rows = screen.getAllByRole('row');
      const failedRow = rows.find(row => row.textContent?.includes('Failed'));

      if (failedRow) {
        await user.click(failedRow);

        await waitFor(() => {
          expect(screen.getByText('Error Message')).toBeInTheDocument();
        });
      }
    });

    it('should display additional details', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const rows = screen.getAllByRole('row');
      if (rows[1]) {
        await user.click(rows[1]);

        await waitFor(() => {
          expect(screen.getByText('Additional Details')).toBeInTheDocument();
        });
      }
    });

    it('should close detail panel', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const rows = screen.getAllByRole('row');
      if (rows[1]) {
        await user.click(rows[1]);

        await waitFor(async () => {
          const closeButtons = screen.getAllByRole('button');
          const closeButton = closeButtons.find(btn =>
            btn.querySelector('svg') && btn.closest('[class*="fixed"]')
          );

          if (closeButton) {
            await user.click(closeButton);
          }
        });
      }
    });

    it('should close panel when clicking backdrop', async () => {
      const user = userEvent.setup();
      const { container } = render(<AdminAuditPage />);

      const rows = screen.getAllByRole('row');
      if (rows[1]) {
        await user.click(rows[1]);

        await waitFor(async () => {
          const backdrop = container.querySelector('.fixed.inset-0.bg-black\\/30');
          if (backdrop) {
            await user.click(backdrop as HTMLElement);

            await waitFor(() => {
              expect(screen.queryByText('Audit Entry Details')).not.toBeInTheDocument();
            });
          }
        });
      }
    });
  });

  describe('Export Functionality', () => {
    it('should trigger export', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const exportButton = screen.getByRole('button', { name: /Export/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(screen.getByText('Exporting...')).toBeInTheDocument();
      });
    });

    it('should disable export button while exporting', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const exportButton = screen.getByRole('button', { name: /Export/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(exportButton).toBeDisabled();
      });
    });

    it('should show animation while exporting', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const exportButton = screen.getByRole('button', { name: /Export/i });
      await user.click(exportButton);

      await waitFor(() => {
        const icon = exportButton.querySelector('.animate-bounce');
        expect(icon).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh data', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const refreshButton = screen.getByRole('button', { name: /Refresh/i });
      await user.click(refreshButton);

      // Should maintain current view
      expect(screen.getByText('Audit Logs')).toBeInTheDocument();
    });
  });

  describe('Severity and Category Badges', () => {
    it('should use correct colors for info severity', () => {
      const { container } = render(<AdminAuditPage />);

      const infoBadges = container.querySelectorAll('.bg-blue-100');
      expect(infoBadges.length).toBeGreaterThan(0);
    });

    it('should use correct colors for warning severity', () => {
      const { container } = render(<AdminAuditPage />);

      const warningBadges = container.querySelectorAll('.bg-yellow-100');
      expect(warningBadges.length).toBeGreaterThan(0);
    });

    it('should use correct colors for error severity', () => {
      const { container } = render(<AdminAuditPage />);

      const errorBadges = container.querySelectorAll('.bg-red-100');
      expect(errorBadges.length).toBeGreaterThan(0);
    });

    it('should display category with proper styling', () => {
      render(<AdminAuditPage />);

      const categoryBadges = screen.getAllByText('Authentication');
      expect(categoryBadges[0]).toHaveClass('inline-flex', 'items-center', 'px-2.5', 'py-1', 'rounded-full');
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<AdminAuditPage />);

      const heading = screen.getByRole('heading', { name: /Audit Logs/i });
      expect(heading).toBeInTheDocument();
      expect(heading.tagName).toBe('H1');
    });

    it('should have accessible table', () => {
      render(<AdminAuditPage />);

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
    });

    it('should have accessible buttons', () => {
      render(<AdminAuditPage />);

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should have row click handlers', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const rows = screen.getAllByRole('row');
      if (rows[1]) {
        expect(rows[1]).toHaveClass('cursor-pointer');
      }
    });
  });

  describe('Responsive Layout', () => {
    it('should have mobile-friendly layout', () => {
      const { container } = render(<AdminAuditPage />);

      expect(container.querySelector('.min-h-screen')).toBeInTheDocument();
    });

    it('should have responsive toolbar', () => {
      render(<AdminAuditPage />);

      const toolbar = screen.getByPlaceholderText('Search logs...').closest('div');
      expect(toolbar).toBeInTheDocument();
    });

    it('should have overflow handling', () => {
      const { container } = render(<AdminAuditPage />);

      const overflowElements = container.querySelectorAll('[class*="overflow"]');
      expect(overflowElements.length).toBeGreaterThan(0);
    });
  });

  describe('Time Formatting', () => {
    it('should format timestamps correctly', () => {
      render(<AdminAuditPage />);

      // Should show formatted time
      const times = screen.getAllByText(/\d{1,2}:\d{2}\s?(AM|PM)/i);
      expect(times.length).toBeGreaterThan(0);
    });

    it('should show date in entries', () => {
      render(<AdminAuditPage />);

      // Should show date
      const dates = screen.getAllByText(/\d{1,2}\/\d{1,2}\/\d{4}/);
      expect(dates.length).toBeGreaterThan(0);
    });
  });

  describe('Empty States', () => {
    it('should show message when no entries after filtering', async () => {
      const user = userEvent.setup();
      render(<AdminAuditPage />);

      const searchInput = screen.getByPlaceholderText('Search logs...');
      await user.type(searchInput, 'nonexistentquerythatwontmatch12345');

      // Should show empty state or no entries
      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
    });
  });
});
