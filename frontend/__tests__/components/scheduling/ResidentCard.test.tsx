import { render, screen, fireEvent } from '@/test-utils';
import { ResidentCard, ResidentListItem, ResidentCardProps } from '@/components/scheduling/ResidentCard';

describe('ResidentCard', () => {
  const defaultProps: ResidentCardProps = {
    id: 'resident-123',
    name: 'Dr. Jane Smith',
    role: 'RESIDENT',
    pgyLevel: 2,
    currentRotation: 'Inpatient',
    hoursThisWeek: 65,
    maxHours: 80,
    complianceStatus: 'compliant',
  };

  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(<ResidentCard {...defaultProps} />);

      expect(screen.getByText('Dr. Jane Smith')).toBeInTheDocument();
    });

    it('displays resident name', () => {
      render(<ResidentCard {...defaultProps} />);

      expect(screen.getByText('Dr. Jane Smith')).toBeInTheDocument();
    });

    it('displays role', () => {
      render(<ResidentCard {...defaultProps} />);

      expect(screen.getByText(/RESIDENT/)).toBeInTheDocument();
    });

    it('displays PGY level when provided', () => {
      render(<ResidentCard {...defaultProps} />);

      expect(screen.getByText(/PGY-2/)).toBeInTheDocument();
    });

    it('renders without PGY level when not provided', () => {
      const { container } = render(<ResidentCard {...defaultProps} pgyLevel={undefined} />);

      expect(container.textContent).not.toContain('PGY-');
    });
  });

  describe('Current Rotation', () => {
    it('displays current rotation badge when provided', () => {
      render(<ResidentCard {...defaultProps} />);

      expect(screen.getByText('Inpatient')).toBeInTheDocument();
    });

    it('does not display rotation badge when not provided', () => {
      render(<ResidentCard {...defaultProps} currentRotation={undefined} />);

      expect(screen.queryByText('Inpatient')).not.toBeInTheDocument();
    });
  });

  describe('Hours Tracking', () => {
    it('displays hours this week when provided', () => {
      render(<ResidentCard {...defaultProps} />);

      expect(screen.getByText(/Hours this week/)).toBeInTheDocument();
      expect(screen.getByText('65 / 80')).toBeInTheDocument();
    });

    it('displays progress bar for hours', () => {
      const { container } = render(<ResidentCard {...defaultProps} />);

      const progressBar = container.querySelector('.h-1\\.5');
      expect(progressBar).toBeInTheDocument();
    });

    it('shows green progress when under 80% of max hours', () => {
      const { container } = render(
        <ResidentCard {...defaultProps} hoursThisWeek={60} />
      );

      const progressFill = container.querySelector('.bg-green-500');
      expect(progressFill).toBeInTheDocument();
    });

    it('shows amber progress when between 80% and 100% of max hours', () => {
      const { container } = render(
        <ResidentCard {...defaultProps} hoursThisWeek={70} />
      );

      const progressFill = container.querySelector('.bg-amber-500');
      expect(progressFill).toBeInTheDocument();
    });

    it('shows red progress when at or over max hours', () => {
      const { container } = render(
        <ResidentCard {...defaultProps} hoursThisWeek={80} />
      );

      const progressFill = container.querySelector('.bg-red-500');
      expect(progressFill).toBeInTheDocument();
    });

    it('caps progress bar at 100% even if hours exceed max', () => {
      const { container } = render(
        <ResidentCard {...defaultProps} hoursThisWeek={90} />
      );

      const progressFill = container.querySelector('[style*="width"]');
      expect(progressFill).toHaveStyle({ width: '100%' });
    });

    it('does not display hours section when hoursThisWeek is undefined', () => {
      render(<ResidentCard {...defaultProps} hoursThisWeek={undefined} />);

      expect(screen.queryByText(/Hours this week/)).not.toBeInTheDocument();
    });

    it('uses default maxHours of 80 when not provided', () => {
      render(
        <ResidentCard
          {...defaultProps}
          hoursThisWeek={40}
          maxHours={undefined}
        />
      );

      expect(screen.getByText('40 / 80')).toBeInTheDocument();
    });
  });

  describe('Compliance Status', () => {
    it('does not show alert icon for compliant status', () => {
      const { container } = render(
        <ResidentCard {...defaultProps} complianceStatus="compliant" />
      );

      expect(container.querySelector('.text-amber-500')).not.toBeInTheDocument();
      expect(container.querySelector('.text-red-500')).not.toBeInTheDocument();
    });

    it('shows amber alert icon for warning status', () => {
      const { container } = render(
        <ResidentCard {...defaultProps} complianceStatus="warning" />
      );

      const alertIcon = container.querySelector('.text-amber-500');
      expect(alertIcon).toBeInTheDocument();
    });

    it('shows red alert icon for violation status', () => {
      const { container } = render(
        <ResidentCard {...defaultProps} complianceStatus="violation" />
      );

      const alertIcon = container.querySelector('.text-red-500');
      expect(alertIcon).toBeInTheDocument();
    });

    it('displays hours in red for violation status', () => {
      render(
        <ResidentCard {...defaultProps} complianceStatus="violation" hoursThisWeek={85} />
      );

      const hoursText = screen.getByText('85 / 80');
      expect(hoursText).toHaveClass('text-red-600');
    });

    it('displays hours in amber for warning status', () => {
      render(
        <ResidentCard {...defaultProps} complianceStatus="warning" hoursThisWeek={75} />
      );

      const hoursText = screen.getByText('75 / 80');
      expect(hoursText).toHaveClass('text-amber-600');
    });

    it('displays hours normally for compliant status', () => {
      render(
        <ResidentCard {...defaultProps} complianceStatus="compliant" hoursThisWeek={60} />
      );

      const hoursText = screen.getByText('60 / 80');
      expect(hoursText).toHaveClass('text-gray-900');
    });
  });

  describe('Avatar Display', () => {
    it('renders avatar with provided image', () => {
      render(<ResidentCard {...defaultProps} avatar="https://example.com/avatar.jpg" />);

      // Avatar component should be rendered
      expect(screen.getByText('Dr. Jane Smith')).toBeInTheDocument();
    });

    it('renders avatar without image when not provided', () => {
      render(<ResidentCard {...defaultProps} avatar={undefined} />);

      // Avatar component should still be rendered (with initials)
      expect(screen.getByText('Dr. Jane Smith')).toBeInTheDocument();
    });
  });

  describe('Click Handling', () => {
    it('calls onClick when card is clicked', () => {
      const handleClick = jest.fn();
      render(<ResidentCard {...defaultProps} onClick={handleClick} />);

      const card = screen.getByText('Dr. Jane Smith').closest('div');
      fireEvent.click(card!);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('applies cursor-pointer class when onClick is provided', () => {
      const handleClick = jest.fn();
      const { container } = render(<ResidentCard {...defaultProps} onClick={handleClick} />);

      const card = container.querySelector('.cursor-pointer');
      expect(card).toBeInTheDocument();
    });

    it('does not apply cursor-pointer when onClick is not provided', () => {
      const { container } = render(<ResidentCard {...defaultProps} onClick={undefined} />);

      const card = container.querySelector('.cursor-pointer');
      expect(card).not.toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(<ResidentCard {...defaultProps} className="custom-class" />);

      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });

    it('applies hover shadow effect', () => {
      const { container } = render(<ResidentCard {...defaultProps} />);

      const card = container.querySelector('.hover\\:shadow-md');
      expect(card).toBeInTheDocument();
    });
  });
});

describe('ResidentListItem', () => {
  const defaultProps = {
    name: 'Dr. John Doe',
    role: 'RESIDENT',
    pgyLevel: 1,
  };

  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(<ResidentListItem {...defaultProps} />);

      expect(screen.getByText('Dr. John Doe')).toBeInTheDocument();
    });

    it('displays resident name', () => {
      render(<ResidentListItem {...defaultProps} />);

      expect(screen.getByText('Dr. John Doe')).toBeInTheDocument();
    });

    it('displays role and PGY level', () => {
      render(<ResidentListItem {...defaultProps} />);

      expect(screen.getByText(/RESIDENT • PGY-1/)).toBeInTheDocument();
    });

    it('displays only role when PGY level not provided', () => {
      render(<ResidentListItem {...defaultProps} pgyLevel={undefined} />);

      expect(screen.getByText('RESIDENT')).toBeInTheDocument();
      expect(screen.queryByText(/PGY-/)).not.toBeInTheDocument();
    });
  });

  describe('Avatar Display', () => {
    it('renders avatar', () => {
      render(<ResidentListItem {...defaultProps} />);

      // Avatar should be rendered
      expect(screen.getByText('Dr. John Doe')).toBeInTheDocument();
    });

    it('renders avatar with provided image', () => {
      render(<ResidentListItem {...defaultProps} avatar="https://example.com/avatar.jpg" />);

      expect(screen.getByText('Dr. John Doe')).toBeInTheDocument();
    });
  });

  describe('Click Handling', () => {
    it('calls onClick when item is clicked', () => {
      const handleClick = jest.fn();
      render(<ResidentListItem {...defaultProps} onClick={handleClick} />);

      const item = screen.getByText('Dr. John Doe').closest('div');
      fireEvent.click(item!);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('applies cursor-pointer when onClick is provided', () => {
      const handleClick = jest.fn();
      const { container } = render(<ResidentListItem {...defaultProps} onClick={handleClick} />);

      const item = container.querySelector('.cursor-pointer');
      expect(item).toBeInTheDocument();
    });

    it('does not apply cursor-pointer when onClick is not provided', () => {
      const { container } = render(<ResidentListItem {...defaultProps} onClick={undefined} />);

      const item = container.querySelector('.cursor-pointer');
      expect(item).not.toBeInTheDocument();
    });
  });

  describe('Hover Effects', () => {
    it('applies hover background effect', () => {
      const { container } = render(<ResidentListItem {...defaultProps} />);

      const item = container.querySelector('.hover\\:bg-gray-50');
      expect(item).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(<ResidentListItem {...defaultProps} className="custom-class" />);

      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });
  });

  describe('Truncation', () => {
    it('applies truncate class to name', () => {
      const { container } = render(<ResidentListItem {...defaultProps} />);

      const nameElement = screen.getByText('Dr. John Doe');
      expect(nameElement).toHaveClass('truncate');
    });

    it('applies min-width to prevent overflow', () => {
      const { container } = render(<ResidentListItem {...defaultProps} />);

      const nameContainer = screen.getByText('Dr. John Doe').parentElement;
      expect(nameContainer).toHaveClass('min-w-0');
    });
  });
});
