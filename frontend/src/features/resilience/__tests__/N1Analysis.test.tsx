import { useVulnerabilityReport } from "@/hooks/useResilience";
import { render, screen } from "@testing-library/react";
import { N1Analysis } from "../components/N1Analysis";

jest.mock("@/hooks/useResilience", () => ({
  useVulnerabilityReport: jest.fn(),
}));

describe("N1Analysis", () => {
  const mockVulnerabilityData = {
    analyzed_at: new Date().toISOString(),
    period_start: "2025-01-01",
    period_end: "2025-01-31",
    n1_pass: true,
    n2_pass: true,
    phase_transition_risk: "low",
    n1_vulnerabilities: [],
    n2_fatal_pairs: [],
    most_critical_faculty: [
      {
        faculty_id: "fac-001",
        faculty_name: "Dr. Smith",
        centrality_score: 0.85,
        services_covered: 12,
        unique_coverage_slots: 3,
        replacement_difficulty: 0.9,
        risk_level: "HIGH",
      },
      {
        faculty_id: "fac-002",
        faculty_name: "Dr. Jones",
        centrality_score: 0.72,
        services_covered: 8,
        unique_coverage_slots: 1,
        replacement_difficulty: 0.7,
        risk_level: "MEDIUM",
      },
    ],
    recommended_actions: [
      "Cross-train resident backup for critical rotations",
      "Develop contingency plan for Dr. Smith absence",
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders N-1 analysis component", () => {
    (useVulnerabilityReport as jest.Mock).mockReturnValue({
      data: mockVulnerabilityData,
      isLoading: false,
      error: null,
    });

    render(<N1Analysis />);

    expect(screen.getByText("N-1 Analysis")).toBeInTheDocument();
    expect(screen.getByText("Single Point of Failure Detection")).toBeInTheDocument();
  });

  it("displays PASSED status when n1_pass is true", () => {
    (useVulnerabilityReport as jest.Mock).mockReturnValue({
      data: mockVulnerabilityData,
      isLoading: false,
      error: null,
    });

    render(<N1Analysis />);

    expect(screen.getByText("PASSED")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
  });

  it("displays critical faculty members", () => {
    (useVulnerabilityReport as jest.Mock).mockReturnValue({
      data: mockVulnerabilityData,
      isLoading: false,
      error: null,
    });

    render(<N1Analysis />);

    expect(screen.getByText("Dr. Smith")).toBeInTheDocument();
    expect(screen.getByText("Dr. Jones")).toBeInTheDocument();
    expect(screen.getByText("Critical Redundancy Risks")).toBeInTheDocument();
  });

  it("displays centrality scores for critical faculty", () => {
    (useVulnerabilityReport as jest.Mock).mockReturnValue({
      data: mockVulnerabilityData,
      isLoading: false,
      error: null,
    });

    render(<N1Analysis />);

    expect(screen.getByText(/Score: 0.85/)).toBeInTheDocument();
    expect(screen.getByText(/Score: 0.72/)).toBeInTheDocument();
  });

  it("displays mitigation strategies", () => {
    (useVulnerabilityReport as jest.Mock).mockReturnValue({
      data: mockVulnerabilityData,
      isLoading: false,
      error: null,
    });

    render(<N1Analysis />);

    expect(screen.getByText("Mitigation Strategies")).toBeInTheDocument();
    expect(
      screen.getByText("Cross-train resident backup for critical rotations")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Develop contingency plan for Dr. Smith absence")
    ).toBeInTheDocument();
  });

  it("shows loading state", () => {
    (useVulnerabilityReport as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(<N1Analysis />);

    expect(screen.getByText("Analyzing N-1 Topology...")).toBeInTheDocument();
  });

  it("shows error state", () => {
    (useVulnerabilityReport as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error("Failed to fetch"),
    });

    render(<N1Analysis />);

    expect(screen.getByText("Vulnerability Data Unavailable")).toBeInTheDocument();
    expect(screen.getByText("Unable to compute N-1 status")).toBeInTheDocument();
  });

  it("displays resilience optimal when no critical faculty", () => {
    const optimizedData = {
      ...mockVulnerabilityData,
      most_critical_faculty: [],
    };

    (useVulnerabilityReport as jest.Mock).mockReturnValue({
      data: optimizedData,
      isLoading: false,
      error: null,
    });

    render(<N1Analysis />);

    expect(screen.getByText("Resilience Optimal")).toBeInTheDocument();
    expect(screen.getByText("No single points of failure detected.")).toBeInTheDocument();
  });

  it("displays FAILED status when n1_pass is false", () => {
    const failedData = {
      ...mockVulnerabilityData,
      n1_pass: false,
    };

    (useVulnerabilityReport as jest.Mock).mockReturnValue({
      data: failedData,
      isLoading: false,
      error: null,
    });

    render(<N1Analysis />);

    expect(screen.getByText("FAILED")).toBeInTheDocument();
  });

  it("limits critical faculty display to 3 items", () => {
    const manyFacultyData = {
      ...mockVulnerabilityData,
      most_critical_faculty: Array.from({ length: 5 }, (_, i) => ({
        faculty_id: `fac-${i}`,
        faculty_name: `Dr. Faculty ${i}`,
        centrality_score: 0.8 - i * 0.1,
        services_covered: 10,
        unique_coverage_slots: 2,
        replacement_difficulty: 0.8,
        risk_level: "HIGH",
      })),
    };

    (useVulnerabilityReport as jest.Mock).mockReturnValue({
      data: manyFacultyData,
      isLoading: false,
      error: null,
    });

    render(<N1Analysis />);

    // Should only show first 3 faculty
    expect(screen.getByText("Dr. Faculty 0")).toBeInTheDocument();
    expect(screen.getByText("Dr. Faculty 1")).toBeInTheDocument();
    expect(screen.getByText("Dr. Faculty 2")).toBeInTheDocument();
    expect(screen.queryByText("Dr. Faculty 3")).not.toBeInTheDocument();
  });
});
