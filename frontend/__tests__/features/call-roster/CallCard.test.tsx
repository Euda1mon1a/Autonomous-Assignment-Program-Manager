/**
 * Tests for CallCard Component
 *
 * Tests call assignment card display, expand/collapse functionality,
 * and different variants (full, compact, list).
 */

import { render, screen, fireEvent } from '@testing-library/react';
import {
  CallCard,
  CallCardCompact,
  CallListItem,
} from '@/features/call-roster/CallCard';
import type { CallAssignment } from '@/features/call-roster/types';

// Mock ContactInfo component
jest.mock('@/features/call-roster/ContactInfo', () => ({
  ContactInfo: ({ person, showLabel }: any) => (
    <div data-testid="contact-info">
      Contact: {person.name} (showLabel: {showLabel.toString()})
    </div>
  ),
}));

describe('CallCard', () => {
  const mockAssignment: CallAssignment = {
    id: 'assignment-1',
    date: '2025-01-15',
    shift: 'night',
    person: {
      id: 'person-1',
      name: 'Dr. John Doe',
      pgy_level: 2,
      role: 'senior',
      phone: '555-1234',
      pager: '555-5678',
      email: 'john.doe@example.com',
    },
    rotation_name: 'Night Call',
    notes: 'Available for consults',
  };

  describe('Basic Rendering', () => {
    it('should render person name', () => {
      render(<CallCard assignment={mockAssignment} />);

      expect(screen.getByText('Dr. John Doe')).toBeInTheDocument();
    });

    it('should render PGY level', () => {
      render(<CallCard assignment={mockAssignment} />);

      expect(screen.getByText('PGY-2')).toBeInTheDocument();
    });

    it('should render role badge', () => {
      render(<CallCard assignment={mockAssignment} />);

      expect(screen.getByText('Senior')).toBeInTheDocument();
    });

    it('should render shift label', () => {
      render(<CallCard assignment={mockAssignment} />);

      expect(screen.getByText('Night')).toBeInTheDocument();
    });

    it('should not render PGY level when undefined', () => {
      const assignmentNoPGY: CallAssignment = {
        ...mockAssignment,
        person: {
          ...mockAssignment.person,
          pgy_level: undefined,
        },
      };

      render(<CallCard assignment={assignmentNoPGY} />);

      expect(screen.queryByText(/PGY-/)).not.toBeInTheDocument();
    });
  });

  describe('Expand/Collapse', () => {
    it('should be collapsed by default', () => {
      render(<CallCard assignment={mockAssignment} />);

      // Expanded content should not be visible
      expect(screen.queryByText('Rotation:')).not.toBeInTheDocument();
      expect(screen.queryByTestId('contact-info')).not.toBeInTheDocument();
    });

    it('should expand when clicked', () => {
      render(<CallCard assignment={mockAssignment} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      // Expanded content should now be visible
      expect(screen.getByText('Rotation:')).toBeInTheDocument();
      expect(screen.getByTestId('contact-info')).toBeInTheDocument();
    });

    it('should collapse when clicked again', () => {
      render(<CallCard assignment={mockAssignment} />);

      const button = screen.getByRole('button');

      // Expand
      fireEvent.click(button);
      expect(screen.getByText('Rotation:')).toBeInTheDocument();

      // Collapse
      fireEvent.click(button);
      expect(screen.queryByText('Rotation:')).not.toBeInTheDocument();
    });

    it('should show ChevronDown icon when collapsed', () => {
      const { container } = render(<CallCard assignment={mockAssignment} />);

      const chevronDown = container.querySelector('.lucide-chevron-down');
      expect(chevronDown).toBeInTheDocument();
    });

    it('should show ChevronUp icon when expanded', () => {
      const { container } = render(<CallCard assignment={mockAssignment} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      const chevronUp = container.querySelector('.lucide-chevron-up');
      expect(chevronUp).toBeInTheDocument();
    });

    it('should be expanded by default when defaultExpanded is true', () => {
      render(<CallCard assignment={mockAssignment} defaultExpanded={true} />);

      // Expanded content should be visible immediately
      expect(screen.getByText('Rotation:')).toBeInTheDocument();
      expect(screen.getByTestId('contact-info')).toBeInTheDocument();
    });
  });

  describe('Expanded Content', () => {
    it('should render rotation name when expanded', () => {
      render(<CallCard assignment={mockAssignment} defaultExpanded={true} />);

      expect(screen.getByText('Rotation:')).toBeInTheDocument();
      expect(screen.getByText('Night Call')).toBeInTheDocument();
    });

    it('should render contact info when expanded', () => {
      render(<CallCard assignment={mockAssignment} defaultExpanded={true} />);

      const contactInfo = screen.getByTestId('contact-info');
      expect(contactInfo).toBeInTheDocument();
      expect(contactInfo).toHaveTextContent('showLabel: true');
    });

    it('should render notes when expanded', () => {
      render(<CallCard assignment={mockAssignment} defaultExpanded={true} />);

      expect(screen.getByText('Notes:')).toBeInTheDocument();
      expect(screen.getByText('Available for consults')).toBeInTheDocument();
    });

    it('should not render rotation when undefined', () => {
      const assignmentNoRotation: CallAssignment = {
        ...mockAssignment,
        rotation_name: undefined,
      };

      render(<CallCard assignment={assignmentNoRotation} defaultExpanded={true} />);

      expect(screen.queryByText('Rotation:')).not.toBeInTheDocument();
    });

    it('should not render notes when undefined', () => {
      const assignmentNoNotes: CallAssignment = {
        ...mockAssignment,
        notes: undefined,
      };

      render(<CallCard assignment={assignmentNoNotes} defaultExpanded={true} />);

      expect(screen.queryByText('Notes:')).not.toBeInTheDocument();
    });
  });

  describe('Date Display', () => {
    it('should not show date by default', () => {
      render(<CallCard assignment={mockAssignment} defaultExpanded={true} />);

      expect(screen.queryByText('Date:')).not.toBeInTheDocument();
    });

    it('should show date when showDate is true', () => {
      render(
        <CallCard assignment={mockAssignment} showDate={true} defaultExpanded={true} />
      );

      expect(screen.getByText('Date:')).toBeInTheDocument();
    });

    it('should format date correctly', () => {
      render(
        <CallCard assignment={mockAssignment} showDate={true} defaultExpanded={true} />
      );

      // Date should be formatted as "Wed, Jan 15, 2025" or similar
      const dateText = screen.getByText(/Jan 15, 2025/i);
      expect(dateText).toBeInTheDocument();
    });
  });

  describe('Shift Icons', () => {
    it('should show Moon icon for night shift', () => {
      const { container } = render(<CallCard assignment={mockAssignment} />);

      const moonIcon = container.querySelector('.lucide-moon');
      expect(moonIcon).toBeInTheDocument();
    });

    it('should show Sun icon for day shift', () => {
      const dayAssignment: CallAssignment = {
        ...mockAssignment,
        shift: 'day',
      };

      const { container } = render(<CallCard assignment={dayAssignment} />);

      const sunIcon = container.querySelector('.lucide-sun');
      expect(sunIcon).toBeInTheDocument();
    });

    it('should show Clock icon for 24hr shift', () => {
      const fullDayAssignment: CallAssignment = {
        ...mockAssignment,
        shift: '24hr',
      };

      const { container } = render(<CallCard assignment={fullDayAssignment} />);

      const clockIcon = container.querySelector('.lucide-clock');
      expect(clockIcon).toBeInTheDocument();
    });
  });

  describe('Role Styling', () => {
    it('should apply senior role styling', () => {
      const { container } = render(<CallCard assignment={mockAssignment} />);

      // Senior role should have blue styling
      const roleBadge = container.querySelector('.text-blue-800');
      expect(roleBadge).toBeInTheDocument();
    });

    it('should apply intern role styling', () => {
      const internAssignment: CallAssignment = {
        ...mockAssignment,
        person: {
          ...mockAssignment.person,
          role: 'intern',
        },
      };

      const { container } = render(<CallCard assignment={internAssignment} />);

      // Intern role should have green styling
      const roleBadge = container.querySelector('.text-green-800');
      expect(roleBadge).toBeInTheDocument();
    });

    it('should apply attending role styling', () => {
      const attendingAssignment: CallAssignment = {
        ...mockAssignment,
        person: {
          ...mockAssignment.person,
          role: 'attending',
        },
      };

      const { container } = render(<CallCard assignment={attendingAssignment} />);

      // Attending role should have red styling
      const roleBadge = container.querySelector('.text-red-800');
      expect(roleBadge).toBeInTheDocument();
    });

    it('should capitalize role name', () => {
      render(<CallCard assignment={mockAssignment} />);

      // Role should be capitalized
      expect(screen.getByText('Senior')).toBeInTheDocument();
      expect(screen.queryByText('senior')).not.toBeInTheDocument();
    });
  });
});

describe('CallCardCompact', () => {
  const mockAssignment: CallAssignment = {
    id: 'assignment-1',
    date: '2025-01-15',
    shift: 'night',
    person: {
      id: 'person-1',
      name: 'Dr. John Doe',
      pgy_level: 2,
      role: 'senior',
      phone: '555-1234',
    },
    rotation_name: 'Night Call',
  };

  it('should render person name', () => {
    render(<CallCardCompact assignment={mockAssignment} />);

    expect(screen.getByText('Dr. John Doe')).toBeInTheDocument();
  });

  it('should render PGY level', () => {
    render(<CallCardCompact assignment={mockAssignment} />);

    expect(screen.getByText('PGY-2')).toBeInTheDocument();
  });

  it('should not render PGY level when undefined', () => {
    const assignmentNoPGY: CallAssignment = {
      ...mockAssignment,
      person: {
        ...mockAssignment.person,
        pgy_level: undefined,
      },
    };

    render(<CallCardCompact assignment={assignmentNoPGY} />);

    expect(screen.queryByText(/PGY-/)).not.toBeInTheDocument();
  });

  it('should apply correct role styling', () => {
    const { container } = render(<CallCardCompact assignment={mockAssignment} />);

    // Senior role should have blue styling
    const card = container.querySelector('.text-blue-800');
    expect(card).toBeInTheDocument();
  });

  describe('Tooltip', () => {
    it('should not show tooltip initially', () => {
      render(<CallCardCompact assignment={mockAssignment} />);

      expect(screen.queryByTestId('contact-info')).not.toBeInTheDocument();
    });

    it('should show tooltip on mouse enter', () => {
      const { container } = render(<CallCardCompact assignment={mockAssignment} />);

      const card = container.querySelector('.relative');
      if (card) {
        fireEvent.mouseEnter(card);
      }

      // Tooltip should now be visible
      expect(screen.getByText('Night Call')).toBeInTheDocument();
    });

    it('should hide tooltip on mouse leave', () => {
      const { container } = render(<CallCardCompact assignment={mockAssignment} />);

      const card = container.querySelector('.relative');
      if (card) {
        fireEvent.mouseEnter(card);
        expect(screen.getByText('Night Call')).toBeInTheDocument();

        fireEvent.mouseLeave(card);
        expect(screen.queryByText('Night Call')).not.toBeInTheDocument();
      }
    });

    it('should show person info in tooltip', () => {
      const { container } = render(<CallCardCompact assignment={mockAssignment} />);

      const card = container.querySelector('.relative');
      if (card) {
        fireEvent.mouseEnter(card);
      }

      // Name appears twice - once in card, once in tooltip
      const names = screen.getAllByText('Dr. John Doe');
      expect(names).toHaveLength(2);
      expect(screen.getByText(/PGY-2 • senior/i)).toBeInTheDocument();
    });

    it('should show rotation in tooltip', () => {
      const { container } = render(<CallCardCompact assignment={mockAssignment} />);

      const card = container.querySelector('.relative');
      if (card) {
        fireEvent.mouseEnter(card);
      }

      expect(screen.getByText('Night Call')).toBeInTheDocument();
    });

    it('should show contact info in tooltip', () => {
      const { container } = render(<CallCardCompact assignment={mockAssignment} />);

      const card = container.querySelector('.relative');
      if (card) {
        fireEvent.mouseEnter(card);
      }

      expect(screen.getByTestId('contact-info')).toBeInTheDocument();
    });
  });
});

describe('CallListItem', () => {
  const mockAssignment: CallAssignment = {
    id: 'assignment-1',
    date: '2025-01-15',
    shift: 'night',
    person: {
      id: 'person-1',
      name: 'Dr. John Doe',
      pgy_level: 2,
      role: 'senior',
      phone: '555-1234',
    },
    rotation_name: 'Night Call',
  };

  it('should render person name', () => {
    render(<CallListItem assignment={mockAssignment} />);

    expect(screen.getByText('Dr. John Doe')).toBeInTheDocument();
  });

  it('should render PGY level', () => {
    render(<CallListItem assignment={mockAssignment} />);

    expect(screen.getByText('PGY-2')).toBeInTheDocument();
  });

  it('should render role badge', () => {
    render(<CallListItem assignment={mockAssignment} />);

    expect(screen.getByText('Senior')).toBeInTheDocument();
  });

  it('should render shift label and icon', () => {
    const { container } = render(<CallListItem assignment={mockAssignment} />);

    expect(screen.getByText('Night')).toBeInTheDocument();
    const moonIcon = container.querySelector('.lucide-moon');
    expect(moonIcon).toBeInTheDocument();
  });

  it('should render contact info', () => {
    render(<CallListItem assignment={mockAssignment} />);

    expect(screen.getByTestId('contact-info')).toBeInTheDocument();
  });

  describe('Date Display', () => {
    it('should not show date by default', () => {
      render(<CallListItem assignment={mockAssignment} />);

      expect(screen.queryByText(/Jan/)).not.toBeInTheDocument();
    });

    it('should show date when showDate is true', () => {
      render(<CallListItem assignment={mockAssignment} showDate={true} />);

      expect(screen.getByText(/Jan 15/)).toBeInTheDocument();
    });

    it('should format date correctly', () => {
      render(<CallListItem assignment={mockAssignment} showDate={true} />);

      // Date should be formatted as "Jan 15" or similar
      const dateText = screen.getByText(/Jan 15/i);
      expect(dateText).toBeInTheDocument();
    });
  });

  describe('Shift Icons', () => {
    it('should show Sun icon for day shift', () => {
      const dayAssignment: CallAssignment = {
        ...mockAssignment,
        shift: 'day',
      };

      const { container } = render(<CallListItem assignment={dayAssignment} />);

      const sunIcon = container.querySelector('.lucide-sun');
      expect(sunIcon).toBeInTheDocument();
    });

    it('should show Clock icon for 24hr shift', () => {
      const fullDayAssignment: CallAssignment = {
        ...mockAssignment,
        shift: '24hr',
      };

      const { container } = render(<CallListItem assignment={fullDayAssignment} />);

      const clockIcon = container.querySelector('.lucide-clock');
      expect(clockIcon).toBeInTheDocument();
    });
  });

  it('should not render PGY level when undefined', () => {
    const assignmentNoPGY: CallAssignment = {
      ...mockAssignment,
      person: {
        ...mockAssignment.person,
        pgy_level: undefined,
      },
    };

    render(<CallListItem assignment={assignmentNoPGY} />);

    expect(screen.queryByText(/PGY-/)).not.toBeInTheDocument();
  });
});
