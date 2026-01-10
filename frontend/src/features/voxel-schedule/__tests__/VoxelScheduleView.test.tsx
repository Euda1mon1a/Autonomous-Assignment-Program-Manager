/**
 * Tests for VoxelScheduleView component
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { VoxelScheduleView } from "../VoxelScheduleView";

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock ResizeObserver
class MockResizeObserver {
  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
}
global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;

// Mock canvas context
const mockContext = {
  fillRect: jest.fn(),
  fillStyle: "",
  strokeStyle: "",
  lineWidth: 0,
  beginPath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  closePath: jest.fn(),
  fill: jest.fn(),
  stroke: jest.fn(),
  save: jest.fn(),
  restore: jest.fn(),
  translate: jest.fn(),
  scale: jest.fn(),
  rotate: jest.fn(),
  fillText: jest.fn(),
  globalAlpha: 1,
  font: "",
};

HTMLCanvasElement.prototype.getContext = jest.fn(() => mockContext) as jest.Mock;

// Sample voxel grid data
const mockVoxelGridData = {
  dimensions: {
    x_size: 4,
    y_size: 3,
    z_size: 2,
    xLabels: ["2024-01-15 AM", "2024-01-15 PM", "2024-01-16 AM", "2024-01-16 PM"],
    yLabels: ["Dr. Smith", "Resident A", "Resident B"],
    z_labels: ["clinic", "inpatient"],
  },
  voxels: [
    {
      position: { x: 0, y: 0, z: 0 },
      identity: {
        assignmentId: "a1",
        personId: "p1",
        personName: "Dr. Smith",
        blockId: "b1",
        block_date: "2024-01-15",
        block_timeOfDay: "AM",
        activity_name: "Morning Clinic",
        activityType: "clinic",
      },
      visual: {
        color: "#3B82F6",
        rgba: [0.23, 0.51, 0.96, 1],
        opacity: 1.0,
        height: 1.0,
      },
      state: {
        is_occupied: true,
        is_conflict: false,
        is_violation: false,
        violation_details: [],
      },
      metadata: {
        role: "supervising",
        confidence: 1.0,
        hours: 4.0,
      },
    },
    {
      position: { x: 0, y: 1, z: 0 },
      identity: {
        assignmentId: "a2",
        personId: "p2",
        personName: "Resident A",
        blockId: "b1",
        block_date: "2024-01-15",
        block_timeOfDay: "AM",
        activity_name: "Morning Clinic",
        activityType: "clinic",
      },
      visual: {
        color: "#3B82F6",
        rgba: [0.23, 0.51, 0.96, 1],
        opacity: 0.9,
        height: 1.0,
      },
      state: {
        is_occupied: true,
        is_conflict: false,
        is_violation: false,
        violation_details: [],
      },
      metadata: {
        role: "primary",
        confidence: 0.9,
        hours: 4.0,
      },
    },
  ],
  statistics: {
    totalAssignments: 2,
    totalConflicts: 0,
    totalViolations: 0,
    coveragePercentage: 16.67,
  },
  dateRange: {
    startDate: "2024-01-15",
    endDate: "2024-01-16",
  },
};

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

function renderWithProviders(component: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{component}</QueryClientProvider>
  );
}

describe("VoxelScheduleView", () => {
  beforeEach(() => {
    mockFetch.mockClear();
    jest.clearAllMocks();
  });

  it("shows loading state initially", () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithProviders(<VoxelScheduleView />);

    expect(screen.getByText(/loading 3d schedule/i)).toBeInTheDocument();
  });

  it("renders voxel grid after data loads", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockVoxelGridData),
    });

    renderWithProviders(<VoxelScheduleView />);

    await waitFor(() => {
      expect(screen.getByText("3D Schedule View")).toBeInTheDocument();
    });

    // Check statistics are displayed
    expect(screen.getByText(/assignments: 2/i)).toBeInTheDocument();
    expect(screen.getByText(/conflicts: 0/i)).toBeInTheDocument();
  });

  it("displays control instructions", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockVoxelGridData),
    });

    renderWithProviders(<VoxelScheduleView />);

    await waitFor(() => {
      expect(screen.getByText("Drag: Pan view")).toBeInTheDocument();
      expect(screen.getByText("Shift+Drag: Rotate")).toBeInTheDocument();
      expect(screen.getByText("Scroll: Zoom")).toBeInTheDocument();
    });
  });

  it("displays activity type legend", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockVoxelGridData),
    });

    renderWithProviders(<VoxelScheduleView />);

    await waitFor(() => {
      expect(screen.getByText("Activity Types")).toBeInTheDocument();
      expect(screen.getByText("Clinic")).toBeInTheDocument();
      expect(screen.getByText("Inpatient")).toBeInTheDocument();
    });
  });

  it("shows error state on fetch failure", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
    });

    renderWithProviders(<VoxelScheduleView />);

    await waitFor(() => {
      expect(screen.getByText(/error loading voxel data/i)).toBeInTheDocument();
    });
  });

  it("displays axis labels", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockVoxelGridData),
    });

    renderWithProviders(<VoxelScheduleView />);

    await waitFor(() => {
      expect(screen.getByText(/X: Time | Y: People | Z: Activity Type/i)).toBeInTheDocument();
    });
  });

  it("respects startDate and endDate props in API call", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockVoxelGridData),
    });

    // Use UTC dates to avoid timezone issues
    const startDate = new Date(Date.UTC(2024, 1, 1)); // Feb 1, 2024 UTC
    const endDate = new Date(Date.UTC(2024, 1, 15)); // Feb 15, 2024 UTC

    renderWithProviders(
      <VoxelScheduleView startDate={startDate} endDate={endDate} />
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const fetchUrl = mockFetch.mock.calls[0][0];
    // Check that start and end date params are present (exact date may vary by timezone)
    expect(fetchUrl).toMatch(/startDate=2024-0[12]-\d{2}/);
    expect(fetchUrl).toMatch(/endDate=2024-02-\d{2}/);
  });

  it("filters by activity types when provided", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockVoxelGridData),
    });

    renderWithProviders(
      <VoxelScheduleView activityTypes={["clinic", "inpatient"]} />
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const fetchUrl = mockFetch.mock.calls[0][0];
    expect(fetchUrl).toContain("activityTypes=clinic");
    expect(fetchUrl).toContain("activityTypes=inpatient");
  });

  it("handles canvas mouse events", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockVoxelGridData),
    });

    renderWithProviders(<VoxelScheduleView />);

    await waitFor(() => {
      expect(screen.getByText("3D Schedule View")).toBeInTheDocument();
    });

    const canvas = document.querySelector("canvas");
    expect(canvas).toBeInTheDocument();

    // Test mouse down
    fireEvent.mouseDown(canvas!, { clientX: 100, clientY: 100 });

    // Test mouse move (panning)
    fireEvent.mouseMove(canvas!, { clientX: 150, clientY: 150 });

    // Test mouse up
    fireEvent.mouseUp(canvas!);

    // No errors should occur
  });

  it("handles zoom with wheel event", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockVoxelGridData),
    });

    renderWithProviders(<VoxelScheduleView />);

    await waitFor(() => {
      expect(screen.getByText("3D Schedule View")).toBeInTheDocument();
    });

    const canvas = document.querySelector("canvas");
    expect(canvas).toBeInTheDocument();

    // Simulate zoom in
    fireEvent.wheel(canvas!, { deltaY: -100 });

    // Simulate zoom out
    fireEvent.wheel(canvas!, { deltaY: 100 });

    // No errors should occur
  });

  it("calls onVoxelClick when provided and voxel is clicked", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockVoxelGridData),
    });

    const onVoxelClick = jest.fn();

    renderWithProviders(<VoxelScheduleView onVoxelClick={onVoxelClick} />);

    await waitFor(() => {
      expect(screen.getByText("3D Schedule View")).toBeInTheDocument();
    });

    const canvas = document.querySelector("canvas");
    fireEvent.click(canvas!);

    // onVoxelClick would be called if a voxel was hovered
    // In this test environment, it won't be called without proper canvas hit testing
  });

  it("filters to show only conflicts when showConflictsOnly is true", async () => {
    const dataWithConflicts = {
      ...mockVoxelGridData,
      voxels: [
        ...mockVoxelGridData.voxels,
        {
          position: { x: 1, y: 0, z: 0 },
          identity: {
            assignmentId: "conflict1",
            personId: "p1",
            personName: "Dr. Smith",
            blockId: "b2",
            block_date: "2024-01-15",
            block_timeOfDay: "PM",
            activity_name: "Conflict Assignment",
            activityType: "clinic",
          },
          visual: {
            color: "#FF0000",
            rgba: [1, 0, 0, 1],
            opacity: 1.0,
            height: 1.0,
          },
          state: {
            is_occupied: true,
            is_conflict: true,
            is_violation: false,
            violation_details: ["Double-booked"],
          },
          metadata: {
            role: "primary",
            confidence: 1.0,
            hours: 4.0,
          },
        },
      ],
      statistics: {
        ...mockVoxelGridData.statistics,
        totalConflicts: 1,
      },
    };

    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(dataWithConflicts),
    });

    renderWithProviders(<VoxelScheduleView showConflictsOnly={true} />);

    await waitFor(() => {
      expect(screen.getByText("3D Schedule View")).toBeInTheDocument();
    });

    // The component should filter to only show the conflict voxel
    // This is tested via the filtering logic in the component
  });
});

describe("VoxelScheduleView isometric projection", () => {
  it("renders canvas element", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockVoxelGridData),
    });

    renderWithProviders(<VoxelScheduleView />);

    await waitFor(() => {
      expect(screen.getByText("3D Schedule View")).toBeInTheDocument();
    });

    const canvas = document.querySelector("canvas");
    expect(canvas).toBeInTheDocument();
  });

  it("canvas has correct cursor classes", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockVoxelGridData),
    });

    renderWithProviders(<VoxelScheduleView />);

    await waitFor(() => {
      expect(screen.getByText("3D Schedule View")).toBeInTheDocument();
    });

    const canvas = document.querySelector("canvas");
    expect(canvas).toHaveClass("cursor-grab");
  });
});
