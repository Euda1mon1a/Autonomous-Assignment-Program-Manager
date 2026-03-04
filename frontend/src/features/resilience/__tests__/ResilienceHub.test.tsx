import { useSystemHealth } from "@/hooks/useResilience";
import { OverallStatus, UtilizationLevel } from "@/types/resilience";
import { fireEvent, render, screen } from "@testing-library/react";
import { ResilienceHub } from "../ResilienceHub";

// Mock the hook
jest.mock("@/hooks/useResilience", () => ({
  useSystemHealth: jest.fn(),
  useVulnerabilityReport: jest.fn(),
  useBurnoutRt: jest.fn(),
  useUtilizationThreshold: jest.fn(),
}));

// Mock child components to isolate Hub testing
jest.mock("../components/ResilienceMetrics", () => ({
  ResilienceMetrics: () => <div data-testid="metrics-component">Metrics</div>,
}));
jest.mock("../components/UtilizationChart", () => ({
  UtilizationChart: () => <div data-testid="chart-component">Chart</div>,
}));
jest.mock("../components/BurnoutDashboard", () => ({
  BurnoutDashboard: () => <div data-testid="burnout-component">Burnout</div>,
}));
jest.mock("../components/N1Analysis", () => ({
  N1Analysis: () => <div data-testid="n1-component">N1 Analysis</div>,
}));
jest.mock("../components/NaturalSwapsPanel", () => ({
  NaturalSwapsPanel: () => <div data-testid="natural-swaps-component">Natural Swaps</div>,
}));

describe("ResilienceHub", () => {
  const mockHealthData = {
    timestamp: new Date().toISOString(),
    overallStatus: OverallStatus.HEALTHY,
    defenseLevel: "CONTROL",
    utilization: {
      utilizationRate: 0.5,
      level: UtilizationLevel.GREEN,
      currentDemand: 50,
      safeCapacity: 100,
    },
    activeFallbacks: [],
    n1Pass: true,
    n2Pass: true,
    immediateActions: [],
    watchItems: [],
  };

  beforeEach(() => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      refetch: jest.fn(),
      isRefetching: false,
    });
  });

  it("renders key components", () => {
    render(<ResilienceHub />);

    expect(screen.getByText("Resilience Command")).toBeInTheDocument();
    expect(screen.getByTestId("metrics-component")).toBeInTheDocument();
    expect(screen.getByTestId("chart-component")).toBeInTheDocument();
    expect(screen.getByTestId("burnout-component")).toBeInTheDocument();
    expect(screen.getByTestId("n1-component")).toBeInTheDocument();
  });

  it("refreshes data when refresh button is clicked", () => {
    const mockRefetch = jest.fn();
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      refetch: mockRefetch,
      isRefetching: false,
    });

    render(<ResilienceHub />);

    // Find the refresh button by logic: standard button, usually first/icon
    const buttons = screen.getAllByRole("button");
    const refreshBtn = buttons[0];

    fireEvent.click(refreshBtn);
    expect(mockRefetch).toHaveBeenCalled();
  });

  it("toggles simulation mode", () => {
    render(<ResilienceHub />);

    const simulateBtn = screen.getByText("Simulate Crisis");
    fireEvent.click(simulateBtn);

    expect(screen.getByText("Deactivate Sims")).toBeInTheDocument();
    expect(screen.getByText("EMERGENCY PROTOCOLS ACTIVE")).toBeInTheDocument();
  });
});
