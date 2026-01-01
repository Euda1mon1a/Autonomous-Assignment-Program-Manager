/**
 * Tests for LayerControlPanel Component
 *
 * Tests layer visibility controls, constraint type toggles,
 * show/hide all functionality, and statistics display.
 */

import { render, screen, fireEvent } from '@/test-utils';
import { LayerControlPanel } from '@/features/holographic-hub/LayerControlPanel';
import type {
  LayerVisibility,
  ConstraintVisibility,
  SpectralLayer,
  ConstraintType,
  HolographicDataset,
} from '@/features/holographic-hub/types';

describe('LayerControlPanel', () => {
  const mockLayerVisibility: LayerVisibility = {
    quantum: true,
    temporal: true,
    topological: false,
    spectral: false,
    evolutionary: false,
    gravitational: false,
    phase: false,
    thermodynamic: false,
  };

  const mockConstraintVisibility: ConstraintVisibility = {
    acgme: true,
    fairness: true,
    fatigue: false,
    temporal: false,
    preference: false,
    coverage: false,
    skill: false,
    custom: false,
  };

  const mockData: HolographicDataset = {
    timestamp: '2025-01-15T12:00:00Z',
    sessions: [],
    allConstraints: [],
    manifoldPoints: [],
    globalStats: {
      totalUniqueConstraints: 150,
      constraintsByType: {
        acgme: 45,
        fairness: 30,
        fatigue: 25,
        temporal: 20,
        preference: 15,
        coverage: 10,
        skill: 5,
        custom: 0,
      },
      constraintsByLayer: {
        quantum: 40,
        temporal: 35,
        topological: 25,
        spectral: 15,
        evolutionary: 10,
        gravitational: 10,
        phase: 10,
        thermodynamic: 5,
      },
      overallHealth: 0.85,
      projectionMethod: 'umap',
      projectionQuality: 0.92,
    },
  };

  const mockOnToggleLayer = jest.fn();
  const mockOnToggleConstraint = jest.fn();
  const mockOnSetAllLayersVisible = jest.fn();
  const mockOnSetAllConstraintsVisible = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render spectral layers section', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      expect(screen.getByText('Spectral Layers')).toBeInTheDocument();
    });

    it('should render constraint types section', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      expect(screen.getByText('Constraint Types')).toBeInTheDocument();
    });

    it('should render all 8 spectral layers', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      const layers: SpectralLayer[] = [
        'quantum',
        'temporal',
        'topological',
        'spectral',
        'evolutionary',
        'gravitational',
        'phase',
        'thermodynamic',
      ];

      layers.forEach((layer) => {
        // Capitalize first letter for display
        const displayName = layer.charAt(0).toUpperCase() + layer.slice(1);
        expect(screen.getByText(displayName)).toBeInTheDocument();
      });
    });

    it('should render all 8 constraint types', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      const constraints: ConstraintType[] = [
        'acgme',
        'fairness',
        'fatigue',
        'temporal',
        'preference',
        'coverage',
        'skill',
        'custom',
      ];

      constraints.forEach((constraint) => {
        // Capitalize first letter for display
        const displayName = constraint.charAt(0).toUpperCase() + constraint.slice(1);
        expect(screen.getByText(displayName)).toBeInTheDocument();
      });
    });

    it('should apply custom className', () => {
      const { container } = render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          className="custom-class"
        />
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Layer Visibility Count', () => {
    it('should show correct visible layer count', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      // 2 visible out of 8 in mockLayerVisibility
      expect(screen.getByText('(2/8)')).toBeInTheDocument();
    });

    it('should update count when all layers visible', () => {
      const allVisible: LayerVisibility = {
        quantum: true,
        temporal: true,
        topological: true,
        spectral: true,
        evolutionary: true,
        gravitational: true,
        phase: true,
        thermodynamic: true,
      };

      render(
        <LayerControlPanel
          layerVisibility={allVisible}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      expect(screen.getByText('(8/8)')).toBeInTheDocument();
    });

    it('should show correct visible constraint count', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      // 2 visible out of 8 in mockConstraintVisibility
      expect(screen.getByText('(2/8)')).toBeInTheDocument();
    });
  });

  describe('Layer Toggle Interaction', () => {
    it('should call onToggleLayer when layer clicked', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      const quantumButton = screen.getByRole('button', { name: /quantum/i });
      fireEvent.click(quantumButton);

      expect(mockOnToggleLayer).toHaveBeenCalledWith('quantum');
    });

    it('should call onToggleLayer for each layer', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      const layers: SpectralLayer[] = ['quantum', 'temporal', 'topological'];

      layers.forEach((layer) => {
        const button = screen.getByRole('button', { name: new RegExp(layer, 'i') });
        fireEvent.click(button);
      });

      expect(mockOnToggleLayer).toHaveBeenCalledTimes(3);
      expect(mockOnToggleLayer).toHaveBeenCalledWith('quantum');
      expect(mockOnToggleLayer).toHaveBeenCalledWith('temporal');
      expect(mockOnToggleLayer).toHaveBeenCalledWith('topological');
    });
  });

  describe('Constraint Toggle Interaction', () => {
    it('should call onToggleConstraint when constraint clicked', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      const acgmeButton = screen.getByRole('button', { name: /acgme/i });
      fireEvent.click(acgmeButton);

      expect(mockOnToggleConstraint).toHaveBeenCalledWith('acgme');
    });

    it('should call onToggleConstraint for each constraint', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      const constraints: ConstraintType[] = ['acgme', 'fairness', 'fatigue'];

      constraints.forEach((constraint) => {
        const button = screen.getByRole('button', { name: new RegExp(constraint, 'i') });
        fireEvent.click(button);
      });

      expect(mockOnToggleConstraint).toHaveBeenCalledTimes(3);
    });
  });

  describe('Show/Hide All Layers', () => {
    it('should render Show All Layers button', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      const showAllButtons = screen.getAllByRole('button', { name: /show all/i });
      expect(showAllButtons.length).toBeGreaterThan(0);
    });

    it('should call onSetAllLayersVisible(true) when Show All clicked', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      const showAllButtons = screen.getAllByRole('button', { name: /show all/i });
      // First Show All button is for layers
      fireEvent.click(showAllButtons[0]);

      expect(mockOnSetAllLayersVisible).toHaveBeenCalledWith(true);
    });

    it('should call onSetAllLayersVisible(false) when Hide All clicked', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      const hideAllButtons = screen.getAllByRole('button', { name: /hide all/i });
      // First Hide All button is for layers
      fireEvent.click(hideAllButtons[0]);

      expect(mockOnSetAllLayersVisible).toHaveBeenCalledWith(false);
    });
  });

  describe('Show/Hide All Constraints', () => {
    it('should call onSetAllConstraintsVisible(true) when Show All clicked', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      const showAllButtons = screen.getAllByRole('button', { name: /show all/i });
      // Second Show All button is for constraints
      fireEvent.click(showAllButtons[1]);

      expect(mockOnSetAllConstraintsVisible).toHaveBeenCalledWith(true);
    });

    it('should call onSetAllConstraintsVisible(false) when Hide All clicked', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      const hideAllButtons = screen.getAllByRole('button', { name: /hide all/i });
      // Second Hide All button is for constraints
      fireEvent.click(hideAllButtons[1]);

      expect(mockOnSetAllConstraintsVisible).toHaveBeenCalledWith(false);
    });
  });

  describe('Statistics Display', () => {
    it('should not show statistics when data not provided', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
        />
      );

      expect(screen.queryByText('Dataset Summary')).not.toBeInTheDocument();
    });

    it('should show statistics when data provided', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          data={mockData}
        />
      );

      expect(screen.getByText('Dataset Summary')).toBeInTheDocument();
    });

    it('should show total unique constraints', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          data={mockData}
        />
      );

      expect(screen.getByText('Total')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
    });

    it('should show health percentage', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          data={mockData}
        />
      );

      expect(screen.getByText('Health')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('should show projection method', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          data={mockData}
        />
      );

      expect(screen.getByText('Projection')).toBeInTheDocument();
      expect(screen.getByText('UMAP')).toBeInTheDocument();
    });

    it('should show projection quality percentage', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          data={mockData}
        />
      );

      expect(screen.getByText('Quality')).toBeInTheDocument();
      expect(screen.getByText('92%')).toBeInTheDocument();
    });

    it('should apply green color for high health', () => {
      const { container } = render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          data={mockData}
        />
      );

      const healthValue = screen.getByText('85%');
      expect(healthValue).toHaveClass('text-green-400');
    });

    it('should apply yellow color for medium health', () => {
      const mediumHealthData = {
        ...mockData,
        globalStats: {
          ...mockData.globalStats,
          overallHealth: 0.5,
        },
      };

      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          data={mediumHealthData}
        />
      );

      const healthValue = screen.getByText('50%');
      expect(healthValue).toHaveClass('text-yellow-400');
    });

    it('should apply red color for low health', () => {
      const lowHealthData = {
        ...mockData,
        globalStats: {
          ...mockData.globalStats,
          overallHealth: 0.3,
        },
      };

      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          data={lowHealthData}
        />
      );

      const healthValue = screen.getByText('30%');
      expect(healthValue).toHaveClass('text-red-400');
    });
  });

  describe('Constraint Counts Display', () => {
    it('should show constraint counts when data provided', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          data={mockData}
        />
      );

      // Check some constraint counts
      expect(screen.getByText('45')).toBeInTheDocument(); // ACGME
      expect(screen.getByText('30')).toBeInTheDocument(); // Fairness
      expect(screen.getByText('25')).toBeInTheDocument(); // Fatigue
    });

    it('should show layer counts when data provided', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          data={mockData}
        />
      );

      // Check some layer counts
      expect(screen.getByText('40')).toBeInTheDocument(); // Quantum
      expect(screen.getByText('35')).toBeInTheDocument(); // Temporal
    });

    it('should not show counts for zero-value constraints', () => {
      render(
        <LayerControlPanel
          layerVisibility={mockLayerVisibility}
          constraintVisibility={mockConstraintVisibility}
          onToggleLayer={mockOnToggleLayer}
          onToggleConstraint={mockOnToggleConstraint}
          onSetAllLayersVisible={mockOnSetAllLayersVisible}
          onSetAllConstraintsVisible={mockOnSetAllConstraintsVisible}
          data={mockData}
        />
      );

      // Custom has 0 count and should not display
      const customButtons = screen.getAllByRole('button', { name: /custom/i });
      customButtons.forEach((button) => {
        expect(button.textContent).not.toMatch(/\b0\b/);
      });
    });
  });
});
