import { render, screen } from '@testing-library/react';
import { RotationBadge, RotationLegend, RotationType } from '@/components/scheduling/RotationBadge';

describe('RotationBadge', () => {
  const rotationTypes: RotationType[] = [
    'clinic',
    'inpatient',
    'call',
    'leave',
    'procedure',
    'conference',
    'admin',
    'research',
    'vacation',
    'sick',
  ];

  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(<RotationBadge type="clinic" />);

      expect(screen.getByText('Clinic')).toBeInTheDocument();
    });

    it('displays rotation type with capitalized first letter', () => {
      render(<RotationBadge type="clinic" />);

      expect(screen.getByText('Clinic')).toBeInTheDocument();
    });

    it('displays custom label when provided', () => {
      render(<RotationBadge type="clinic" label="Outpatient Clinic" />);

      expect(screen.getByText('Outpatient Clinic')).toBeInTheDocument();
      expect(screen.queryByText('Clinic')).not.toBeInTheDocument();
    });

    it('uses default label when label prop is empty', () => {
      render(<RotationBadge type="inpatient" label="" />);

      expect(screen.getByText('Inpatient')).toBeInTheDocument();
    });
  });

  describe('All Rotation Types', () => {
    rotationTypes.forEach((type) => {
      it(`renders ${type} badge correctly`, () => {
        const { container } = render(<RotationBadge type={type} />);

        const expectedLabel = type.charAt(0).toUpperCase() + type.slice(1);
        expect(screen.getByText(expectedLabel)).toBeInTheDocument();

        // Verify styling classes are applied
        const badge = container.querySelector('span');
        expect(badge).toHaveClass('inline-flex');
        expect(badge).toHaveClass('items-center');
      });
    });
  });

  describe('Size Variants', () => {
    it('applies small size classes', () => {
      const { container } = render(<RotationBadge type="clinic" size="sm" />);

      const badge = container.querySelector('span');
      expect(badge).toHaveClass('px-2');
      expect(badge).toHaveClass('py-0.5');
      expect(badge).toHaveClass('text-xs');
    });

    it('applies medium size classes (default)', () => {
      const { container } = render(<RotationBadge type="clinic" size="md" />);

      const badge = container.querySelector('span');
      expect(badge).toHaveClass('px-2.5');
      expect(badge).toHaveClass('py-1');
      expect(badge).toHaveClass('text-sm');
    });

    it('applies large size classes', () => {
      const { container } = render(<RotationBadge type="clinic" size="lg" />);

      const badge = container.querySelector('span');
      expect(badge).toHaveClass('px-3');
      expect(badge).toHaveClass('py-1.5');
      expect(badge).toHaveClass('text-base');
    });

    it('uses medium size when size not specified', () => {
      const { container } = render(<RotationBadge type="clinic" />);

      const badge = container.querySelector('span');
      expect(badge).toHaveClass('text-sm');
    });
  });

  describe('Dot Indicator', () => {
    it('shows dot when showDot is true', () => {
      const { container } = render(<RotationBadge type="clinic" showDot={true} />);

      const dot = container.querySelector('.w-1\\.5.h-1\\.5.rounded-full');
      expect(dot).toBeInTheDocument();
    });

    it('does not show dot when showDot is false', () => {
      const { container } = render(<RotationBadge type="clinic" showDot={false} />);

      const dot = container.querySelector('.w-1\\.5.h-1\\.5.rounded-full');
      expect(dot).not.toBeInTheDocument();
    });

    it('does not show dot by default', () => {
      const { container } = render(<RotationBadge type="clinic" />);

      const dot = container.querySelector('.w-1\\.5.h-1\\.5.rounded-full');
      expect(dot).not.toBeInTheDocument();
    });

    it('applies correct color to dot for clinic type', () => {
      const { container } = render(<RotationBadge type="clinic" showDot={true} />);

      const dot = container.querySelector('.bg-clinic');
      expect(dot).toBeInTheDocument();
    });
  });

  describe('Color Styling', () => {
    it('applies clinic colors', () => {
      const { container } = render(<RotationBadge type="clinic" />);

      const badge = container.querySelector('.bg-clinic-light');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-clinic-dark');
    });

    it('applies inpatient colors', () => {
      const { container } = render(<RotationBadge type="inpatient" />);

      const badge = container.querySelector('.bg-inpatient-light');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-inpatient-dark');
    });

    it('applies call colors', () => {
      const { container } = render(<RotationBadge type="call" />);

      const badge = container.querySelector('.bg-call-light');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-call-dark');
    });

    it('applies leave colors', () => {
      const { container } = render(<RotationBadge type="leave" />);

      const badge = container.querySelector('.bg-leave-light');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-leave-dark');
    });

    it('applies procedure colors', () => {
      const { container } = render(<RotationBadge type="procedure" />);

      const badge = container.querySelector('.bg-purple-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-purple-800');
    });

    it('applies conference colors', () => {
      const { container } = render(<RotationBadge type="conference" />);

      const badge = container.querySelector('.bg-cyan-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-cyan-800');
    });

    it('applies admin colors', () => {
      const { container } = render(<RotationBadge type="admin" />);

      const badge = container.querySelector('.bg-gray-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-gray-800');
    });

    it('applies research colors', () => {
      const { container } = render(<RotationBadge type="research" />);

      const badge = container.querySelector('.bg-indigo-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-indigo-800');
    });

    it('applies vacation colors', () => {
      const { container } = render(<RotationBadge type="vacation" />);

      const badge = container.querySelector('.bg-emerald-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-emerald-800');
    });

    it('applies sick colors', () => {
      const { container } = render(<RotationBadge type="sick" />);

      const badge = container.querySelector('.bg-orange-100');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass('text-orange-800');
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(<RotationBadge type="clinic" className="custom-class" />);

      const badge = container.querySelector('.custom-class');
      expect(badge).toBeInTheDocument();
    });

    it('preserves base classes with custom className', () => {
      const { container } = render(<RotationBadge type="clinic" className="custom-class" />);

      const badge = container.querySelector('.custom-class');
      expect(badge).toHaveClass('inline-flex');
      expect(badge).toHaveClass('rounded');
    });
  });

  describe('Accessibility', () => {
    it('applies rounded corners for visual appeal', () => {
      const { container } = render(<RotationBadge type="clinic" />);

      const badge = container.querySelector('span');
      expect(badge).toHaveClass('rounded');
    });

    it('uses font-medium for readability', () => {
      const { container } = render(<RotationBadge type="clinic" />);

      const badge = container.querySelector('span');
      expect(badge).toHaveClass('font-medium');
    });
  });

  describe('Combined Props', () => {
    it('renders with all props together', () => {
      const { container } = render(
        <RotationBadge
          type="clinic"
          label="Primary Care Clinic"
          size="lg"
          showDot={true}
          className="my-custom-class"
        />
      );

      expect(screen.getByText('Primary Care Clinic')).toBeInTheDocument();

      const badge = container.querySelector('.my-custom-class');
      expect(badge).toHaveClass('text-base'); // lg size
      expect(badge).toHaveClass('bg-clinic-light');

      const dot = container.querySelector('.w-1\\.5.h-1\\.5');
      expect(dot).toBeInTheDocument();
    });
  });
});

describe('RotationLegend', () => {
  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(<RotationLegend />);

      // Should render default types
      expect(screen.getByText('Clinic')).toBeInTheDocument();
      expect(screen.getByText('Inpatient')).toBeInTheDocument();
    });

    it('renders all default rotation types', () => {
      render(<RotationLegend />);

      const defaultTypes = ['Clinic', 'Inpatient', 'Call', 'Leave', 'Procedure', 'Conference'];

      defaultTypes.forEach((type) => {
        expect(screen.getByText(type)).toBeInTheDocument();
      });
    });

    it('renders all badges with dots', () => {
      const { container } = render(<RotationLegend />);

      const dots = container.querySelectorAll('.w-1\\.5.h-1\\.5.rounded-full');
      expect(dots.length).toBeGreaterThan(0);
    });

    it('renders all badges with small size', () => {
      const { container } = render(<RotationLegend />);

      const badges = container.querySelectorAll('.text-xs');
      expect(badges.length).toBeGreaterThan(0);
    });
  });

  describe('Custom Types', () => {
    it('renders custom rotation types when provided', () => {
      const customTypes: RotationType[] = ['clinic', 'vacation', 'sick'];
      render(<RotationLegend types={customTypes} />);

      expect(screen.getByText('Clinic')).toBeInTheDocument();
      expect(screen.getByText('Vacation')).toBeInTheDocument();
      expect(screen.getByText('Sick')).toBeInTheDocument();

      // Default types that are not in custom list should not be present
      expect(screen.queryByText('Inpatient')).not.toBeInTheDocument();
      expect(screen.queryByText('Call')).not.toBeInTheDocument();
    });

    it('renders single custom type', () => {
      const customTypes: RotationType[] = ['admin'];
      render(<RotationLegend types={customTypes} />);

      expect(screen.getByText('Admin')).toBeInTheDocument();
      expect(screen.queryByText('Clinic')).not.toBeInTheDocument();
    });

    it('handles empty custom types array', () => {
      const { container } = render(<RotationLegend types={[]} />);

      const badges = container.querySelectorAll('.inline-flex');
      expect(badges.length).toBe(0);
    });
  });

  describe('Layout', () => {
    it('applies flex wrap layout', () => {
      const { container } = render(<RotationLegend />);

      const legend = container.querySelector('.flex.flex-wrap');
      expect(legend).toBeInTheDocument();
    });

    it('applies gap between badges', () => {
      const { container } = render(<RotationLegend />);

      const legend = container.querySelector('.gap-2');
      expect(legend).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<RotationLegend className="custom-legend" />);

      const legend = container.querySelector('.custom-legend');
      expect(legend).toBeInTheDocument();
      expect(legend).toHaveClass('flex');
      expect(legend).toHaveClass('flex-wrap');
    });
  });

  describe('Badge Properties', () => {
    it('all badges have small size', () => {
      const { container } = render(<RotationLegend />);

      const badges = container.querySelectorAll('.px-2.py-0\\.5.text-xs');
      expect(badges.length).toBeGreaterThan(0);
    });

    it('all badges show dots', () => {
      const { container } = render(<RotationLegend />);

      // Count badges
      const badges = container.querySelectorAll('.inline-flex.items-center.gap-1\\.5');
      const dots = container.querySelectorAll('.w-1\\.5.h-1\\.5.rounded-full');

      expect(dots.length).toBe(badges.length);
    });
  });

  describe('Complete Legend', () => {
    it('renders all rotation types when specified', () => {
      const allTypes: RotationType[] = [
        'clinic',
        'inpatient',
        'call',
        'leave',
        'procedure',
        'conference',
        'admin',
        'research',
        'vacation',
        'sick',
      ];

      render(<RotationLegend types={allTypes} />);

      allTypes.forEach((type) => {
        const label = type.charAt(0).toUpperCase() + type.slice(1);
        expect(screen.getByText(label)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('uses semantic flexbox layout', () => {
      const { container } = render(<RotationLegend />);

      const legend = container.firstChild;
      expect(legend).toHaveClass('flex');
    });

    it('provides visual indicators with colored dots', () => {
      const { container } = render(<RotationLegend />);

      const dots = container.querySelectorAll('.rounded-full');
      expect(dots.length).toBeGreaterThan(0);
    });
  });
});
