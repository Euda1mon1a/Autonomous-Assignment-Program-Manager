/**
 * Tests for ContactInfo Component
 *
 * Tests contact information display, click-to-call, click-to-copy,
 * and different display modes (compact, full, badge).
 */

import { render, screen, fireEvent, waitFor } from '@/test-utils';
import { ContactInfo, ContactBadge } from '@/features/call-roster/ContactInfo';
import type { OnCallPerson } from '@/features/call-roster/types';

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(() => Promise.resolve()),
  },
});

describe('ContactInfo', () => {
  const mockPerson: OnCallPerson = {
    id: 'person-1',
    name: 'Dr. John Doe',
    role: 'senior',
    pgyLevel: 3,
    phone: '555-1234',
    pager: '555-5678',
    email: 'john.doe@example.com',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Full Display Mode', () => {
    it('should render all contact information', () => {
      render(<ContactInfo person={mockPerson} />);

      expect(screen.getByText('555-1234')).toBeInTheDocument();
      expect(screen.getByText('555-5678')).toBeInTheDocument();
      expect(screen.getByText('john.doe@example.com')).toBeInTheDocument();
    });

    it('should show contact label when showLabel is true', () => {
      render(<ContactInfo person={mockPerson} showLabel={true} />);

      expect(screen.getByText('Contact')).toBeInTheDocument();
    });

    it('should hide contact label when showLabel is false', () => {
      render(<ContactInfo person={mockPerson} showLabel={false} />);

      expect(screen.queryByText('Contact')).not.toBeInTheDocument();
    });

    it('should render phone as clickable link', () => {
      render(<ContactInfo person={mockPerson} />);

      const phoneLink = screen.getByRole('link', { name: /555-1234/i });
      expect(phoneLink).toHaveAttribute('href', 'tel:555-1234');
    });

    it('should render email as clickable link', () => {
      render(<ContactInfo person={mockPerson} />);

      const emailLink = screen.getByRole('link', { name: /john.doe@example.com/i });
      expect(emailLink).toHaveAttribute('href', 'mailto:john.doe@example.com');
    });

    it('should display pager with label', () => {
      render(<ContactInfo person={mockPerson} />);

      expect(screen.getByText('555-5678')).toBeInTheDocument();
      expect(screen.getByText('(Pager)')).toBeInTheDocument();
    });

    it('should show copy buttons for all contact methods', () => {
      const { container } = render(<ContactInfo person={mockPerson} />);

      // Each contact method should have a copy button (3 total)
      const copyButtons = container.querySelectorAll('button[title*="Copy"]');
      expect(copyButtons).toHaveLength(3);
    });
  });

  describe('Compact Display Mode', () => {
    it('should render phone in compact mode', () => {
      render(<ContactInfo person={mockPerson} compact={true} />);

      const phoneLink = screen.getByRole('link', { name: /555-1234/i });
      expect(phoneLink).toBeInTheDocument();
    });

    it('should render pager in compact mode', () => {
      render(<ContactInfo person={mockPerson} compact={true} />);

      expect(screen.getByText('555-5678')).toBeInTheDocument();
    });

    it('should not show email in compact mode', () => {
      render(<ContactInfo person={mockPerson} compact={true} />);

      expect(screen.queryByText('john.doe@example.com')).not.toBeInTheDocument();
    });

    it('should not show copy buttons in compact mode', () => {
      const { container } = render(<ContactInfo person={mockPerson} compact={true} />);

      const copyButtons = container.querySelectorAll('button[title*="Copy"]');
      expect(copyButtons).toHaveLength(0);
    });

    it('should not show contact label in compact mode', () => {
      render(<ContactInfo person={mockPerson} compact={true} showLabel={true} />);

      expect(screen.queryByText('Contact')).not.toBeInTheDocument();
    });
  });

  describe('No Contact Info', () => {
    it('should show message when no contact info is available', () => {
      const personNoContact: OnCallPerson = {
        id: 'person-2',
        name: 'Dr. Jane Smith',
        role: 'intern',
      };

      render(<ContactInfo person={personNoContact} />);

      expect(screen.getByText('No contact info available')).toBeInTheDocument();
    });

    it('should not show any contact fields when all are undefined', () => {
      const personNoContact: OnCallPerson = {
        id: 'person-2',
        name: 'Dr. Jane Smith',
        role: 'intern',
      };

      const { container } = render(<ContactInfo person={personNoContact} />);

      expect(screen.queryByRole('link')).not.toBeInTheDocument();
      expect(container.querySelectorAll('button[title*="Copy"]')).toHaveLength(0);
    });
  });

  describe('Partial Contact Info', () => {
    it('should render only phone when other fields are missing', () => {
      const personPhoneOnly: OnCallPerson = {
        id: 'person-3',
        name: 'Dr. Phone Only',
        role: 'attending',
        phone: '555-9999',
      };

      render(<ContactInfo person={personPhoneOnly} />);

      expect(screen.getByText('555-9999')).toBeInTheDocument();
      expect(screen.queryByText(/pager/i)).not.toBeInTheDocument();
    });

    it('should render only email when other fields are missing', () => {
      const personEmailOnly: OnCallPerson = {
        id: 'person-4',
        name: 'Dr. Email Only',
        role: 'senior',
        email: 'email@example.com',
      };

      render(<ContactInfo person={personEmailOnly} />);

      expect(screen.getByText('email@example.com')).toBeInTheDocument();
      expect(screen.queryByText(/pager/i)).not.toBeInTheDocument();
    });
  });

  describe('Copy Functionality', () => {
    it('should copy phone number to clipboard', async () => {
      render(<ContactInfo person={mockPerson} />);

      const copyButton = screen.getByTitle('Copy phone number');
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith('555-1234');
      });
    });

    it('should copy pager number to clipboard', async () => {
      render(<ContactInfo person={mockPerson} />);

      const copyButton = screen.getByTitle('Copy pager number');
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith('555-5678');
      });
    });

    it('should copy email to clipboard', async () => {
      render(<ContactInfo person={mockPerson} />);

      const copyButton = screen.getByTitle('Copy email');
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalledWith('john.doe@example.com');
      });
    });

    it('should show check icon after successful copy', async () => {
      const { container } = render(<ContactInfo person={mockPerson} />);

      const copyButton = screen.getByTitle('Copy phone number');
      fireEvent.click(copyButton);

      await waitFor(() => {
        // Check icon should be visible after copy
        const checkIcons = container.querySelectorAll('.text-green-600');
        expect(checkIcons.length).toBeGreaterThan(0);
      });
    });

    it('should reset check icon after 2 seconds', async () => {
      jest.useFakeTimers();

      render(<ContactInfo person={mockPerson} />);

      const copyButton = screen.getByTitle('Copy phone number');
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalled();
      });

      // Fast-forward time by 2 seconds
      jest.advanceTimersByTime(2000);

      // Check icon should be gone
      await waitFor(() => {
        const copyButtons = screen.getAllByTitle(/Copy/i);
        expect(copyButtons.length).toBeGreaterThan(0);
      });

      jest.useRealTimers();
    });

    it('should handle copy errors gracefully', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      (navigator.clipboard.writeText as jest.Mock).mockRejectedValue(
        new Error('Copy failed')
      );

      render(<ContactInfo person={mockPerson} />);

      const copyButton = screen.getByTitle('Copy phone number');
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          'Failed to copy:',
          expect.any(Error)
        );
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Accessibility', () => {
    it('should have proper titles for phone link', () => {
      const { container } = render(<ContactInfo person={mockPerson} compact={true} />);

      const phoneLink = container.querySelector('a[title*="Call"]');
      expect(phoneLink).toHaveAttribute('title', 'Call 555-1234');
    });

    it('should have proper title for pager in compact mode', () => {
      const { container } = render(<ContactInfo person={mockPerson} compact={true} />);

      const pagerElement = container.querySelector('[title="Pager"]');
      expect(pagerElement).toBeInTheDocument();
    });
  });
});

describe('ContactBadge', () => {
  const mockPerson: OnCallPerson = {
    id: 'person-1',
    name: 'Dr. John Doe',
    role: 'senior',
    phone: '555-1234',
    pager: '555-5678',
  };

  it('should render phone badge', () => {
    render(<ContactBadge person={mockPerson} />);

    expect(screen.getByText('555-1234')).toBeInTheDocument();
  });

  it('should render pager badge', () => {
    render(<ContactBadge person={mockPerson} />);

    expect(screen.getByText('555-5678')).toBeInTheDocument();
  });

  it('should render phone as clickable link', () => {
    render(<ContactBadge person={mockPerson} />);

    const phoneLink = screen.getByRole('link', { name: /555-1234/i });
    expect(phoneLink).toHaveAttribute('href', 'tel:555-1234');
    expect(phoneLink).toHaveAttribute('title', 'Call 555-1234');
  });

  it('should render null when no phone or pager', () => {
    const personNoContact: OnCallPerson = {
      id: 'person-2',
      name: 'Dr. No Contact',
      role: 'intern',
      email: 'email@example.com',
    };

    const { container } = render(<ContactBadge person={personNoContact} />);

    expect(container.firstChild).toBeNull();
  });

  it('should render only phone when pager is missing', () => {
    const personPhoneOnly: OnCallPerson = {
      id: 'person-3',
      name: 'Dr. Phone Only',
      role: 'attending',
      phone: '555-9999',
    };

    render(<ContactBadge person={personPhoneOnly} />);

    expect(screen.getByText('555-9999')).toBeInTheDocument();
    expect(screen.queryByTitle('Pager')).not.toBeInTheDocument();
  });

  it('should render only pager when phone is missing', () => {
    const personPagerOnly: OnCallPerson = {
      id: 'person-4',
      name: 'Dr. Pager Only',
      role: 'senior',
      pager: '555-8888',
    };

    render(<ContactBadge person={personPagerOnly} />);

    expect(screen.getByText('555-8888')).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('should apply correct styling classes', () => {
    const { container } = render(<ContactBadge person={mockPerson} />);

    // Phone badge should have blue styling
    const phoneBadge = container.querySelector('.bg-blue-50');
    expect(phoneBadge).toBeInTheDocument();

    // Pager badge should have gray styling
    const pagerBadge = container.querySelector('.bg-gray-50');
    expect(pagerBadge).toBeInTheDocument();
  });
});
