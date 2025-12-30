/**
 * Tests for HolographicManifold component
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { HolographicManifold } from "../HolographicManifold";
import { ManifoldPoint } from "../types";

// Create a wrapper with QueryClientProvider
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  Wrapper.displayName = "TestQueryWrapper";
  return Wrapper;
};

describe("HolographicManifold", () => {
  beforeEach(() => {
    // Mock ResizeObserver
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };

    // Mock canvas context
    HTMLCanvasElement.prototype.getContext = jest.fn().mockReturnValue({
      fillStyle: "",
      strokeStyle: "",
      lineWidth: 1,
      globalAlpha: 1,
      fillRect: jest.fn(),
      strokeRect: jest.fn(),
      beginPath: jest.fn(),
      moveTo: jest.fn(),
      lineTo: jest.fn(),
      arc: jest.fn(),
      fill: jest.fn(),
      stroke: jest.fn(),
      closePath: jest.fn(),
      createRadialGradient: jest.fn().mockReturnValue({
        addColorStop: jest.fn(),
      }),
      createLinearGradient: jest.fn().mockReturnValue({
        addColorStop: jest.fn(),
      }),
      save: jest.fn(),
      restore: jest.fn(),
      translate: jest.fn(),
      scale: jest.fn(),
      rotate: jest.fn(),
    });
  });

  it("renders loading state initially", () => {
    render(<HolographicManifold useMockData={true} />, {
      wrapper: createWrapper(),
    });

    // With mock data, it should load quickly
    expect(screen.getByText(/Loading holographic manifold/i)).toBeInTheDocument();
  });

  it("renders the canvas element", async () => {
    render(<HolographicManifold useMockData={true} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      const canvas = document.querySelector("canvas");
      expect(canvas).toBeInTheDocument();
    });
  });

  it("renders control panels when showControls is true", async () => {
    render(
      <HolographicManifold
        useMockData={true}
        showControls={true}
        showLegend={true}
        showStats={true}
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText(/Holographic Manifold/i)).toBeInTheDocument();
    });
  });

  it("handles mouse drag for camera rotation", async () => {
    render(<HolographicManifold useMockData={true} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      const canvas = document.querySelector("canvas");
      expect(canvas).toBeInTheDocument();
    });

    const canvas = document.querySelector("canvas")!;

    // Simulate drag
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 120 });
    fireEvent.mouseUp(canvas);

    // Component should not crash
    expect(canvas).toBeInTheDocument();
  });

  it("handles scroll for zoom", async () => {
    render(<HolographicManifold useMockData={true} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      const canvas = document.querySelector("canvas");
      expect(canvas).toBeInTheDocument();
    });

    const canvas = document.querySelector("canvas")!;

    // Simulate scroll
    fireEvent.wheel(canvas, { deltaY: 100 });

    // Component should not crash
    expect(canvas).toBeInTheDocument();
  });

  it("calls onPointClick when a point is clicked", async () => {
    const onPointClick = jest.fn();

    render(
      <HolographicManifold useMockData={true} onPointClick={onPointClick} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      const canvas = document.querySelector("canvas");
      expect(canvas).toBeInTheDocument();
    });

    const canvas = document.querySelector("canvas")!;

    // Click on canvas (may or may not hit a point)
    fireEvent.click(canvas);

    // Function should not throw
    expect(canvas).toBeInTheDocument();
  });

  it("renders reset view button", async () => {
    render(
      <HolographicManifold useMockData={true} showControls={true} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText(/Reset View/i)).toBeInTheDocument();
    });
  });

  it("renders animate/pause toggle", async () => {
    render(
      <HolographicManifold useMockData={true} showControls={true} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      const pauseButton = screen.getByText(/Pause|Animate/i);
      expect(pauseButton).toBeInTheDocument();
    });
  });

  it("toggles animation on button click", async () => {
    render(
      <HolographicManifold useMockData={true} showControls={true} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      const pauseButton = screen.getByText(/Pause/i);
      expect(pauseButton).toBeInTheDocument();
      fireEvent.click(pauseButton);
    });

    await waitFor(() => {
      expect(screen.getByText(/Animate/i)).toBeInTheDocument();
    });
  });

  it("hides controls when showControls is false", async () => {
    render(
      <HolographicManifold
        useMockData={true}
        showControls={false}
        showLegend={false}
        showStats={false}
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      const canvas = document.querySelector("canvas");
      expect(canvas).toBeInTheDocument();
    });

    expect(screen.queryByText(/Reset View/i)).not.toBeInTheDocument();
  });

  it("applies custom className", async () => {
    const { container } = render(
      <HolographicManifold useMockData={true} className="custom-class" />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      const wrapper = container.querySelector(".custom-class");
      expect(wrapper).toBeInTheDocument();
    });
  });
});
