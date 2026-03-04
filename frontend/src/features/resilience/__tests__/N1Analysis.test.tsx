import { useVulnerabilityReport } from "@/hooks/useResilience";
import { render, screen } from "@testing-library/react";
import { N1Analysis } from "../components/N1Analysis";

jest.mock("@/hooks/useResilience", () => ({
  useVulnerabilityReport: jest.fn(),
}));

describe("N1Analysis", () => {
  const mockVulnerabilityData = {
    analyzedAt: new Date().toISOString(),
    periodStart: "2025-01-01",
    periodEnd: "2025-01-31",
    n1Pass: true,
    n2Pass: true,
    phaseTransitionRisk: "low",
    n1Vulnerabilities: [],
    n2FatalPairs: [],
    mostCriticalFaculty: [
      {
        facultyId: "fac-001",
        facultyName: "Dr. Smith",
        centralityScore: 0.85,
        servicesCovered: 12,
        uniqueCoverageSlots: 3,
        replacementDifficulty: 0.9,
        riskLevel: "HIGH",
      },
      {
        facultyId: "fac-002",
        facultyName: "Dr. Jones",
        centralityScore: 0.72,
        servicesCovered: 8,
        uniqueCoverageSlots: 1,
        replacementDifficulty: 0.7,
        riskLevel: "MEDIUM",
      },
    ],
    recommendedActions: [
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

  it("displays PASSED status when n1Pass is true", () => {
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
      mostCriticalFaculty: [],
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

  it("displays FAILED status when n1Pass is false", () => {
    const failedData = {
      ...mockVulnerabilityData,
      n1Pass: false,
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
      mostCriticalFaculty: Array.from({ length: 5 }, (_, i) => ({
        facultyId: `fac-${i}`,
        facultyName: `Dr. Faculty ${i}`,
        centralityScore: 0.8 - i * 0.1,
        servicesCovered: 10,
        uniqueCoverageSlots: 2,
        replacementDifficulty: 0.8,
        riskLevel: "HIGH",
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
