/**
 * Tests for CalendarExportButton Component
 * Component: CalendarExportButton - ICS calendar export
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { CalendarExportButton, SimpleCalendarExportButton } from '../CalendarExportButton';

// Mock fetch
global.fetch = jest.fn();

// Mock toast context
jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
    },
  }),
}));

// Mock clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(),
  },
});

describe('CalendarExportButton', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockReset();
  });

  describe('Rendering', () => {
    it('renders export button', () => {
      render(<CalendarExportButton personId="person-1" />);
      expect(screen.getByText('Export Calendar')).toBeInTheDocument();
    });

    it('opens dropdown when clicked', () => {
      render(<CalendarExportButton personId="person-1" />);

      fireEvent.click(screen.getByText('Export Calendar'));

      expect(screen.getByText('Download ICS')).toBeInTheDocument();
    });

    it('shows subscription option for person calendars', () => {
      render(<CalendarExportButton personId="person-1" />);

      fireEvent.click(screen.getByText('Export Calendar'));

      expect(screen.getByText('Create Subscription')).toBeInTheDocument();
    });

    it('does not show subscription option for rotation calendars', () => {
      render(<CalendarExportButton rotationId="rotation-1" />);

      fireEvent.click(screen.getByText('Export Calendar'));

      expect(screen.queryByText('Create Subscription')).not.toBeInTheDocument();
    });

    it('closes dropdown when backdrop clicked', () => {
      const { container } = render(<CalendarExportButton personId="person-1" />);

      fireEvent.click(screen.getByText('Export Calendar'));
      expect(screen.getByText('Download ICS')).toBeInTheDocument();

      const backdrop = container.querySelector('.fixed.inset-0');
      fireEvent.click(backdrop!);

      expect(screen.queryByText('Download ICS')).not.toBeInTheDocument();
    });
  });

  describe('Download functionality', () => {
    it('downloads ICS file on download button click', async () => {
      const mockBlob = new Blob(['calendar data'], { type: 'text/calendar' });
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob,
      });

      // Mock URL.createObjectURL
      global.URL.createObjectURL = jest.fn(() => 'blob:url');
      global.URL.revokeObjectURL = jest.fn();

      // Mock document methods
      const mockLink = document.createElement('a');
      const clickSpy = jest.spyOn(mockLink, 'click');
      jest.spyOn(document, 'createElement').mockReturnValue(mockLink);
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink);
      jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink);

      render(<CalendarExportButton personId="person-1" />);

      fireEvent.click(screen.getByText('Export Calendar'));
      fireEvent.click(screen.getByText('Download ICS'));

      await waitFor(() => {
        expect(clickSpy).toHaveBeenCalled();
      });
    });

    it('shows loading state while downloading', async () => {
      (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));

      render(<CalendarExportButton personId="person-1" />);

      fireEvent.click(screen.getByText('Export Calendar'));
      fireEvent.click(screen.getByText('Download ICS'));

      await waitFor(() => {
        expect(screen.getByText('Exporting...')).toBeInTheDocument();
      });
    });
  });

  describe('Subscription functionality', () => {
    it('creates subscription URL', async () => {
      const mockUrl = 'https://example.com/subscribe/abc123';
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subscription_url: mockUrl }),
      });

      render(<CalendarExportButton personId="person-1" />);

      fireEvent.click(screen.getByText('Export Calendar'));
      fireEvent.click(screen.getByText('Create Subscription'));

      await waitFor(() => {
        expect(screen.getByText(mockUrl)).toBeInTheDocument();
      });
    });

    it('copies subscription URL to clipboard', async () => {
      const mockUrl = 'https://example.com/subscribe/abc123';
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ subscription_url: mockUrl }),
      });
      (navigator.clipboard.writeText as jest.Mock).mockResolvedValue(undefined);

      render(<CalendarExportButton personId="person-1" />);

      fireEvent.click(screen.getByText('Export Calendar'));
      fireEvent.click(screen.getByText('Create Subscription'));

      await waitFor(() => {
        expect(screen.getByText('Copy URL')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Copy URL'));

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockUrl);
        expect(screen.getByText('Copied!')).toBeInTheDocument();
      });
    });
  });
});

describe('SimpleCalendarExportButton', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders simple export button', () => {
    render(<SimpleCalendarExportButton personId="person-1" />);
    expect(screen.getByText('Export to Calendar')).toBeInTheDocument();
  });

  it('exports directly without dropdown', async () => {
    const mockBlob = new Blob(['calendar data']);
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      blob: async () => mockBlob,
    });

    global.URL.createObjectURL = jest.fn(() => 'blob:url');

    render(<SimpleCalendarExportButton personId="person-1" />);

    fireEvent.click(screen.getByText('Export to Calendar'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
  });

  it('shows loading state', async () => {
    (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));

    render(<SimpleCalendarExportButton personId="person-1" />);

    fireEvent.click(screen.getByText('Export to Calendar'));

    await waitFor(() => {
      expect(screen.getByText('Exporting...')).toBeInTheDocument();
    });
  });

  it('disables button while exporting', async () => {
    (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));

    render(<SimpleCalendarExportButton personId="person-1" />);

    const button = screen.getByText('Export to Calendar');
    fireEvent.click(button);

    await waitFor(() => {
      expect(button).toBeDisabled();
    });
  });
});
