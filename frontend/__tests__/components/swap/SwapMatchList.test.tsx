import { render, screen, fireEvent } from '@/test-utils';
import { SwapMatchList, SwapMatch } from '@/components/swap/SwapMatchList';

jest.mock('@/components/schedule/ShiftIndicator', () => ({
  ShiftIndicator: ({ shift }: any) => <span>{shift}</span>,
}));

jest.mock('@/components/schedule/RotationBadge', () => ({
  RotationBadge: ({ rotationType }: any) => <span>{rotationType}</span>,
}));

describe('SwapMatchList', () => {
  const mockMatches: SwapMatch[] = [
    {
      personId: 'person-1',
      personName: 'Dr. Alice',
      pgyLevel: 'PGY-2',
      blockId: 'block-1',
      date: '2025-01-15',
      shift: 'AM',
      rotationType: 'Inpatient',
      compatibilityScore: 95,
      reasons: ['Same PGY level', 'Compatible rotations', 'Matching availability'],
    },
    {
      personId: 'person-2',
      personName: 'Dr. Bob',
      pgyLevel: 'PGY-3',
      blockId: 'block-2',
      date: '2025-01-20',
      shift: 'PM',
      rotationType: 'Clinic',
      compatibilityScore: 70,
      reasons: ['Compatible rotations'],
      warnings: ['Different PGY levels'],
    },
    {
      personId: 'person-3',
      personName: 'Dr. Carol',
      pgyLevel: 'PGY-1',
      blockId: 'block-3',
      date: '2025-01-25',
      shift: 'Night',
      rotationType: 'Call',
      compatibilityScore: 50,
      reasons: ['Available during requested time'],
      warnings: ['Major PGY difference', 'Different rotation type'],
    },
  ];

  const mockOnSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText('Compatible Swap Matches')).toBeInTheDocument();
    });

    it('displays all matches', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText('Dr. Alice')).toBeInTheDocument();
      expect(screen.getByText('Dr. Bob')).toBeInTheDocument();
      expect(screen.getByText('Dr. Carol')).toBeInTheDocument();
    });

    it('shows match count', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText(/Found 3 potential matches/i)).toBeInTheDocument();
    });

    it('uses singular form for single match', () => {
      render(<SwapMatchList matches={[mockMatches[0]]} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText(/Found 1 potential match$/i)).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no matches', () => {
      render(<SwapMatchList matches={[]} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText('No Compatible Matches Found')).toBeInTheDocument();
    });

    it('shows helpful message in empty state', () => {
      render(<SwapMatchList matches={[]} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText(/Try selecting a different block/i)).toBeInTheDocument();
    });
  });

  describe('Compatibility Scores', () => {
    it('displays compatibility scores', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText('95')).toBeInTheDocument();
      expect(screen.getByText('70')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
    });

    it('shows "Excellent Match" for scores >= 80', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText('Excellent Match')).toBeInTheDocument();
    });

    it('shows "Good Match" for scores 60-79', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText('Good Match')).toBeInTheDocument();
    });

    it('shows "Fair Match" for scores < 60', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText('Fair Match')).toBeInTheDocument();
    });

    it('sorts matches by compatibility score descending', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      const scores = screen.getAllByText(/^\d+$/).map(el => parseInt(el.textContent || '0'));
      expect(scores).toEqual([95, 70, 50]); // Descending order
    });
  });

  describe('Match Reasons', () => {
    it('displays first two reasons by default', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText(/Same PGY level/i)).toBeInTheDocument();
      expect(screen.getByText(/Compatible rotations/i)).toBeInTheDocument();
    });

    it('shows "more reasons" button when > 2 reasons', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText('+1 more reasons')).toBeInTheDocument();
    });

    it('expands to show all reasons when clicked', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      fireEvent.click(screen.getByText('+1 more reasons'));
      expect(screen.getByText('Matching availability')).toBeInTheDocument();
      expect(screen.getByText('Show less')).toBeInTheDocument();
    });

    it('collapses when "Show less" clicked', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      fireEvent.click(screen.getByText('+1 more reasons'));
      fireEvent.click(screen.getByText('Show less'));
      expect(screen.queryByText('Matching availability')).not.toBeInTheDocument();
    });
  });

  describe('Warnings', () => {
    it('displays warnings when present', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText(/Different PGY levels/i)).toBeInTheDocument();
    });

    it('shows additional warnings button when multiple warnings', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText('+1 more warnings')).toBeInTheDocument();
    });

    it('expands warnings when clicked', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      const moreWarningsButton = screen.getByText('+1 more warnings');
      fireEvent.click(moreWarningsButton);
      expect(screen.getByText('Different rotation type')).toBeInTheDocument();
    });

    it('does not show warnings section when no warnings', () => {
      const noWarningMatches = mockMatches.filter(m => !m.warnings || m.warnings.length === 0);
      render(<SwapMatchList matches={noWarningMatches} onSelectMatch={mockOnSelect} />);
      // Should not have warning emoji
      const warningEmojis = screen.queryAllByText('⚠️');
      expect(warningEmojis.length).toBe(0);
    });
  });

  describe('Match Selection', () => {
    it('renders select button for each match', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      const selectButtons = screen.getAllByText('Select This Match');
      expect(selectButtons).toHaveLength(3);
    });

    it('calls onSelectMatch when button clicked', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      const selectButtons = screen.getAllByText('Select This Match');
      fireEvent.click(selectButtons[0]);
      expect(mockOnSelect).toHaveBeenCalledWith(mockMatches[0]);
    });

    it('calls onSelectMatch with correct match', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      const selectButtons = screen.getAllByText('Select This Match');
      fireEvent.click(selectButtons[1]);
      expect(mockOnSelect).toHaveBeenCalledWith(
        expect.objectContaining({ personName: 'Dr. Bob' })
      );
    });
  });

  describe('Score Legend', () => {
    it('displays score legend in footer', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText(/80-100: Excellent/i)).toBeInTheDocument();
      expect(screen.getByText(/60-79: Good/i)).toBeInTheDocument();
      expect(screen.getByText(/<60: Fair/i)).toBeInTheDocument();
    });

    it('shows color indicators in legend', () => {
      const { container } = render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(container.querySelector('.bg-green-100')).toBeInTheDocument();
      expect(container.querySelector('.bg-yellow-100')).toBeInTheDocument();
      expect(container.querySelector('.bg-orange-100')).toBeInTheDocument();
    });
  });

  describe('Match Details', () => {
    it('displays person name and PGY level', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText('Dr. Alice')).toBeInTheDocument();
      expect(screen.getByText('PGY-2')).toBeInTheDocument();
    });

    it('displays block date', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      // Date formatting may vary, just check it renders
      expect(screen.getByText(/Jan.*15/i)).toBeInTheDocument();
    });

    it('displays shift and rotation type', () => {
      render(<SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} />);
      expect(screen.getByText('AM')).toBeInTheDocument();
      expect(screen.getByText('Inpatient')).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <SwapMatchList matches={mockMatches} onSelectMatch={mockOnSelect} className="custom-list" />
      );
      expect(container.querySelector('.custom-list')).toBeInTheDocument();
    });
  });
});
