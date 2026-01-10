import { useSystemHealth, useUtilizationThreshold } from "@/hooks/useResilience";
import { OverallStatus, UtilizationLevel } from "@/types/resilience";
import { render, screen } from "@testing-library/react";
import { UtilizationChart } from "../components/UtilizationChart";

jest.mock("@/hooks/useResilience", () => ({
  useSystemHealth: jest.fn(),
  useUtilizationThreshold: jest.fn(),
}));

describe("UtilizationChart", () => {
  const mockHealthData = {
    timestamp: new Date().toISOString(),
    overall_status: OverallStatus.HEALTHY,
    defenseLevel: "PREVENTION" as any,
    utilization: {
      utilizationRate: 0.65,
      level: UtilizationLevel.YELLOW,
      buffer_remaining: 3.5,
      wait_time_multiplier: 1.5,
      safe_capacity: 100,
      current_demand: 65,
      theoretical_capacity: 100,
    },
    active_fallbacks: [],
    n1Pass: true,
    n2Pass: true,
    phaseTransitionRisk: "low",
    redundancy_status: [],
    load_shedding_level: "NORMAL" as any,
    crisisMode: false,
    immediate_actions: [],
    watch_items: [],
  };

  const mockThresholdData = {
    utilizationRate: 0.65,
    level: "YELLOW",
    message: "Approaching threshold",
    recommendations: [
      "Consider adding capacity",
      "Review workload distribution",
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders system utilization title", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useUtilizationThreshold as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<UtilizationChart />);

    expect(screen.getByText("System Utilization")).toBeInTheDocument();
    expect(screen.getByText("Current load vs safe capacity limits")).toBeInTheDocument();
  });

  it("displays utilization percentage", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useUtilizationThreshold as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<UtilizationChart />);

    expect(screen.getByText("Total Utilization")).toBeInTheDocument();
    expect(screen.getByText("65.0%")).toBeInTheDocument();
  });

  it("displays safety buffer", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useUtilizationThreshold as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<UtilizationChart />);

    expect(screen.getByText("Safety Buffer")).toBeInTheDocument();
    expect(screen.getByText("3.5 FTE")).toBeInTheDocument();
  });

  it("displays metrics grid with demand, capacity, and wait time", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useUtilizationThreshold as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<UtilizationChart />);

    expect(screen.getByText("Demand")).toBeInTheDocument();
    expect(screen.getByText("Safe Capacity")).toBeInTheDocument();
    expect(screen.getByText("Wait Time")).toBeInTheDocument();
    expect(screen.getByText("65")).toBeInTheDocument(); // Demand
    expect(screen.getByText("100")).toBeInTheDocument(); // Safe Capacity
    expect(screen.getByText("1.5x")).toBeInTheDocument(); // Wait time multiplier
  });

  it("displays threshold analysis recommendations", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useUtilizationThreshold as jest.Mock).mockReturnValue({
      data: mockThresholdData,
      isLoading: false,
      error: null,
    });

    render(<UtilizationChart />);

    expect(screen.getByText("Threshold Analysis")).toBeInTheDocument();
    expect(screen.getByText("Approaching threshold")).toBeInTheDocument();
    expect(screen.getByText("Consider adding capacity")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });
    (useUtilizationThreshold as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<UtilizationChart />);

    expect(screen.getByText("Loading visualization...")).toBeInTheDocument();
  });

  it("shows error state", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error("Failed to load utilization data"),
    });
    (useUtilizationThreshold as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<UtilizationChart />);

    expect(screen.getByText("Unable to load utilization data")).toBeInTheDocument();
    expect(screen.getByText("Failed to load utilization data")).toBeInTheDocument();
  });

  it("handles green utilization (low)", () => {
    const greenData = {
      ...mockHealthData,
      utilization: {
        ...mockHealthData.utilization,
        utilizationRate: 0.5,
        level: UtilizationLevel.GREEN,
      },
    };

    (useSystemHealth as jest.Mock).mockReturnValue({
      data: greenData,
      isLoading: false,
      error: null,
    });
    (useUtilizationThreshold as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<UtilizationChart />);

    expect(screen.getByText("50.0%")).toBeInTheDocument();
  });

  it("handles red utilization (high)", () => {
    const redData = {
      ...mockHealthData,
      utilization: {
        ...mockHealthData.utilization,
        utilizationRate: 0.92,
        level: UtilizationLevel.RED,
        wait_time_multiplier: 3.5,
      },
    };

    (useSystemHealth as jest.Mock).mockReturnValue({
      data: redData,
      isLoading: false,
      error: null,
    });
    (useUtilizationThreshold as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<UtilizationChart />);

    expect(screen.getByText("92.0%")).toBeInTheDocument();
    expect(screen.getByText("3.5x")).toBeInTheDocument();
  });

  it("passes correct parameters to utilization threshold hook", () => {
    (useSystemHealth as jest.Mock).mockReturnValue({
      data: mockHealthData,
      isLoading: false,
      error: null,
    });
    (useUtilizationThreshold as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<UtilizationChart />);

    // Verify the hook was called with correct params
    expect(useUtilizationThreshold).toHaveBeenCalledWith(
      {
        available_faculty: 100,
        required_blocks: 65,
      },
      expect.objectContaining({
        enabled: true,
      })
    );
  });

  it("disables threshold hook when utilization data missing", () => {
    const noCapacityData = {
      ...mockHealthData,
      utilization: {
        ...mockHealthData.utilization,
        safe_capacity: 0,
      },
    };

    (useSystemHealth as jest.Mock).mockReturnValue({
      data: noCapacityData,
      isLoading: false,
      error: null,
    });
    (useUtilizationThreshold as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
    });

    render(<UtilizationChart />);

    // Verify hook was called with enabled: false
    expect(useUtilizationThreshold).toHaveBeenCalledWith(
      expect.any(Object),
      expect.objectContaining({
        enabled: false,
      })
    );
  });
});
