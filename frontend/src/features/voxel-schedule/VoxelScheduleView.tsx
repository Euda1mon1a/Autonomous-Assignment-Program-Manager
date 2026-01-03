/**
 * 3D Voxel Schedule Visualization
 *
 * A novel visualization approach that represents the schedule as a 3D voxel space:
 * - X-axis: Time (dates/blocks)
 * - Y-axis: People (residents, faculty)
 * - Z-axis: Activity type (clinic, inpatient, procedures, etc.)
 *
 * This enables spatial reasoning about scheduling:
 * - Collision detection = double-booking
 * - Empty space = coverage gaps
 * - Layer overlap = supervision compliance
 * - Volume distribution = workload balance
 */

"use client";

import React, { useRef, useEffect, useState, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, addDays } from "date-fns";

// Types for the 3D voxel data from API
interface VoxelPosition {
  x: number;
  y: number;
  z: number;
}

interface VoxelIdentity {
  assignment_id: string | null;
  person_id: string | null;
  person_name: string | null;
  block_id: string | null;
  block_date: string | null;
  block_time_of_day: string | null;
  activity_name: string | null;
  activity_type: string | null;
}

interface VoxelVisual {
  color: string;
  rgba: [number, number, number, number];
  opacity: number;
  height: number;
}

interface VoxelState {
  is_occupied: boolean;
  is_conflict: boolean;
  is_violation: boolean;
  violation_details: string[];
}

interface VoxelMetadata {
  role: string | null;
  confidence: number;
  hours: number;
}

interface Voxel {
  position: VoxelPosition;
  identity: VoxelIdentity;
  visual: VoxelVisual;
  state: VoxelState;
  metadata: VoxelMetadata;
}

interface VoxelGridDimensions {
  x_size: number;
  y_size: number;
  z_size: number;
  x_labels: string[];
  y_labels: string[];
  z_labels: string[];
}

interface VoxelGridStatistics {
  total_assignments: number;
  total_conflicts: number;
  total_violations: number;
  coverage_percentage: number;
}

interface VoxelGridData {
  dimensions: VoxelGridDimensions;
  voxels: Voxel[];
  statistics: VoxelGridStatistics;
  date_range: {
    start_date: string | null;
    end_date: string | null;
  };
  error?: string;
}

interface VoxelScheduleViewProps {
  startDate?: Date;
  endDate?: Date;
  personIds?: string[];
  activityTypes?: string[];
  onVoxelClick?: (voxel: Voxel) => void;
  onVoxelHover?: (voxel: Voxel | null) => void;
  showConflictsOnly?: boolean;
  colorMode?: "activity" | "compliance" | "workload";
}

// Canvas-based 3D renderer (no Three.js dependency for initial prototype)
// This uses an isometric projection for a pseudo-3D effect
const VOXEL_SIZE = 20;
const ISO_ANGLE = Math.PI / 6; // 30 degrees for isometric

function isoProject(
  x: number,
  y: number,
  z: number,
  offsetX: number,
  offsetY: number
): { screenX: number; screenY: number } {
  // Isometric projection
  const isoX = (x - z) * Math.cos(ISO_ANGLE);
  const isoY = (x + z) * Math.sin(ISO_ANGLE) - y;
  return {
    screenX: isoX * VOXEL_SIZE + offsetX,
    screenY: isoY * VOXEL_SIZE + offsetY,
  };
}

function drawVoxel(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  z: number,
  color: string,
  opacity: number,
  isConflict: boolean,
  isHovered: boolean,
  offsetX: number,
  offsetY: number
): void {
  // Get the four corners of the top face
  const topLeft = isoProject(x - 0.5, y, z - 0.5, offsetX, offsetY);
  const topRight = isoProject(x + 0.5, y, z - 0.5, offsetX, offsetY);
  const topFront = isoProject(x + 0.5, y, z + 0.5, offsetX, offsetY);
  const topBack = isoProject(x - 0.5, y, z + 0.5, offsetX, offsetY);

  // Bottom corners (y + 1 for height)
  const height = 0.8;
  const botLeft = isoProject(x - 0.5, y + height, z - 0.5, offsetX, offsetY);
  const botRight = isoProject(x + 0.5, y + height, z - 0.5, offsetX, offsetY);
  const botBack = isoProject(x - 0.5, y + height, z + 0.5, offsetX, offsetY);

  ctx.globalAlpha = opacity;

  // Parse color
  const baseColor = color;

  // Draw left face (darker)
  ctx.beginPath();
  ctx.moveTo(topBack.screenX, topBack.screenY);
  ctx.lineTo(topLeft.screenX, topLeft.screenY);
  ctx.lineTo(botLeft.screenX, botLeft.screenY);
  ctx.lineTo(botBack.screenX, botBack.screenY);
  ctx.closePath();
  ctx.fillStyle = adjustBrightness(baseColor, -30);
  ctx.fill();
  ctx.strokeStyle = isHovered ? "#fff" : "#333";
  ctx.lineWidth = isHovered ? 2 : 0.5;
  ctx.stroke();

  // Draw right face (medium)
  ctx.beginPath();
  ctx.moveTo(topLeft.screenX, topLeft.screenY);
  ctx.lineTo(topRight.screenX, topRight.screenY);
  ctx.lineTo(botRight.screenX, botRight.screenY);
  ctx.lineTo(botLeft.screenX, botLeft.screenY);
  ctx.closePath();
  ctx.fillStyle = adjustBrightness(baseColor, -15);
  ctx.fill();
  ctx.stroke();

  // Draw top face (lightest)
  ctx.beginPath();
  ctx.moveTo(topBack.screenX, topBack.screenY);
  ctx.lineTo(topLeft.screenX, topLeft.screenY);
  ctx.lineTo(topRight.screenX, topRight.screenY);
  ctx.lineTo(topFront.screenX, topFront.screenY);
  ctx.closePath();
  ctx.fillStyle = baseColor;
  ctx.fill();
  ctx.stroke();

  // Draw conflict indicator (red X on top)
  if (isConflict) {
    ctx.globalAlpha = 1;
    ctx.strokeStyle = "#ff0000";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(topBack.screenX, topBack.screenY);
    ctx.lineTo(topFront.screenX, topFront.screenY);
    ctx.moveTo(topLeft.screenX, topLeft.screenY);
    ctx.lineTo(topRight.screenX, topRight.screenY);
    ctx.stroke();
  }

  ctx.globalAlpha = 1;
}

function adjustBrightness(hex: string, amount: number): string {
  // Remove # if present
  hex = hex.replace("#", "");

  // Parse RGB
  let r = parseInt(hex.substring(0, 2), 16);
  let g = parseInt(hex.substring(2, 4), 16);
  let b = parseInt(hex.substring(4, 6), 16);

  // Adjust
  r = Math.max(0, Math.min(255, r + amount));
  g = Math.max(0, Math.min(255, g + amount));
  b = Math.max(0, Math.min(255, b + amount));

  // Convert back to hex
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

// API fetch function
async function fetchVoxelGrid(
  startDate: Date,
  endDate: Date,
  personIds?: string[],
  activityTypes?: string[]
): Promise<VoxelGridData> {
  const params = new URLSearchParams();
  params.append("start_date", format(startDate, "yyyy-MM-dd"));
  params.append("end_date", format(endDate, "yyyy-MM-dd"));

  if (personIds && personIds.length > 0) {
    personIds.forEach((id) => params.append("person_ids", id));
  }

  if (activityTypes && activityTypes.length > 0) {
    activityTypes.forEach((type) => params.append("activity_types", type));
  }

  const response = await fetch(`/api/visualization/voxel-grid?${params.toString()}`);
  if (!response.ok) {
    throw new Error("Failed to fetch voxel grid data");
  }
  return response.json();
}

export function VoxelScheduleView({
  startDate = new Date(),
  endDate = addDays(new Date(), 14),
  personIds,
  activityTypes,
  onVoxelClick,
  onVoxelHover,
  showConflictsOnly = false,
  colorMode: _colorMode = "activity",
}: VoxelScheduleViewProps): JSX.Element {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredVoxel, setHoveredVoxel] = useState<Voxel | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });

  // Fetch voxel data
  const { data, isLoading, error } = useQuery<VoxelGridData>({
    queryKey: ["voxel-grid", startDate, endDate, personIds, activityTypes],
    queryFn: () => fetchVoxelGrid(startDate, endDate, personIds, activityTypes),
    staleTime: 60000,
    gcTime: 300000,
  });

  // Filter voxels if needed
  const displayVoxels = useMemo(() => {
    if (!data?.voxels) return [];
    if (showConflictsOnly) {
      return data.voxels.filter((v) => v.state.is_conflict || v.state.is_violation);
    }
    return data.voxels;
  }, [data?.voxels, showConflictsOnly]);

  // Mouse event handlers
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setLastMousePos({ x: e.clientX, y: e.clientY });
  }, []);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (isDragging) {
        const dx = e.clientX - lastMousePos.x;
        const dy = e.clientY - lastMousePos.y;

        if (e.shiftKey) {
          // Rotate with shift+drag
          // Not implemented yet
        } else {
          // Pan without shift
          setPan((prev) => ({
            x: prev.x + dx,
            y: prev.y + dy,
          }));
        }

        setLastMousePos({ x: e.clientX, y: e.clientY });
      } else {
        // Hit testing for hover
        const canvas = canvasRef.current;
        if (!canvas || !data) return;

        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        // Find closest voxel to mouse position
        let closestVoxel: Voxel | null = null;
        let closestDist = Infinity;

        const offsetX = canvas.width / 2 + pan.x;
        const offsetY = canvas.height / 2 + pan.y;

        for (const voxel of displayVoxels) {
          const { screenX, screenY } = isoProject(
            voxel.position.x,
            voxel.position.y,
            voxel.position.z,
            offsetX,
            offsetY
          );

          const dist = Math.sqrt(
            Math.pow(mouseX - screenX, 2) + Math.pow(mouseY - screenY, 2)
          );

          if (dist < VOXEL_SIZE && dist < closestDist) {
            closestDist = dist;
            closestVoxel = voxel;
          }
        }

        if (closestVoxel !== hoveredVoxel) {
          setHoveredVoxel(closestVoxel);
          onVoxelHover?.(closestVoxel);
        }
      }
    },
    [isDragging, lastMousePos, data, displayVoxels, pan, hoveredVoxel, onVoxelHover]
  );

  const handleWheel = useCallback((e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((prev) => Math.max(0.2, Math.min(3, prev * delta)));
  }, []);

  const handleClick = useCallback(() => {
    if (hoveredVoxel && onVoxelClick) {
      onVoxelClick(hoveredVoxel);
    }
  }, [hoveredVoxel, onVoxelClick]);

  // Render the voxel grid
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Calculate offset to center the grid
    const offsetX = canvas.width / 2 + pan.x;
    const offsetY = canvas.height / 2 + pan.y;

    // Apply zoom
    ctx.save();
    ctx.translate(offsetX, offsetY);
    ctx.scale(zoom, zoom);
    ctx.translate(-offsetX, -offsetY);

    // Draw grid floor
    const { x_size, y_size, z_size } = data.dimensions;
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 0.5;

    // Draw x-z plane grid lines
    for (let x = 0; x <= x_size; x++) {
      const start = isoProject(x, y_size, 0, offsetX, offsetY);
      const end = isoProject(x, y_size, z_size, offsetX, offsetY);
      ctx.beginPath();
      ctx.moveTo(start.screenX, start.screenY);
      ctx.lineTo(end.screenX, end.screenY);
      ctx.stroke();
    }

    for (let z = 0; z <= z_size; z++) {
      const start = isoProject(0, y_size, z, offsetX, offsetY);
      const end = isoProject(x_size, y_size, z, offsetX, offsetY);
      ctx.beginPath();
      ctx.moveTo(start.screenX, start.screenY);
      ctx.lineTo(end.screenX, end.screenY);
      ctx.stroke();
    }

    // Sort voxels by depth for proper z-ordering (painter's algorithm)
    const sortedVoxels = [...displayVoxels].sort((a, b) => {
      // Sort by combined depth (back to front)
      const depthA = a.position.x + a.position.z - a.position.y;
      const depthB = b.position.x + b.position.z - b.position.y;
      return depthA - depthB;
    });

    // Draw each voxel
    for (const voxel of sortedVoxels) {
      const isHovered = voxel === hoveredVoxel;
      drawVoxel(
        ctx,
        voxel.position.x,
        voxel.position.y,
        voxel.position.z,
        voxel.visual.color,
        voxel.visual.opacity,
        voxel.state.is_conflict,
        isHovered,
        offsetX,
        offsetY
      );
    }

    // Draw axis labels
    ctx.fillStyle = "#888";
    ctx.font = "12px monospace";

    // X-axis labels (time)
    const xLabelCount = Math.min(data.dimensions.x_labels.length, 10);
    const xStep = Math.ceil(data.dimensions.x_labels.length / xLabelCount);
    for (let i = 0; i < data.dimensions.x_labels.length; i += xStep) {
      const pos = isoProject(i, y_size + 1, 0, offsetX, offsetY);
      ctx.save();
      ctx.translate(pos.screenX, pos.screenY);
      ctx.rotate(-Math.PI / 6);
      ctx.fillText(data.dimensions.x_labels[i]?.slice(5) || "", 0, 0);
      ctx.restore();
    }

    // Y-axis labels (people)
    const yLabelCount = Math.min(data.dimensions.y_labels.length, 10);
    const yStep = Math.ceil(data.dimensions.y_labels.length / yLabelCount);
    for (let i = 0; i < data.dimensions.y_labels.length; i += yStep) {
      const pos = isoProject(-1, i, 0, offsetX, offsetY);
      ctx.fillText(data.dimensions.y_labels[i]?.slice(0, 10) || "", pos.screenX - 80, pos.screenY);
    }

    // Z-axis labels (activity types)
    for (let i = 0; i < data.dimensions.z_labels.length; i++) {
      const pos = isoProject(-1, y_size, i, offsetX, offsetY);
      ctx.fillText(data.dimensions.z_labels[i] || "", pos.screenX - 80, pos.screenY);
    }

    ctx.restore();
  }, [data, displayVoxels, hoveredVoxel, zoom, pan]);

  // Handle canvas resize
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        canvas.width = width;
        canvas.height = height;
      }
    });

    resizeObserver.observe(canvas.parentElement!);
    return () => resizeObserver.disconnect();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-900 rounded-lg">
        <div className="text-white">Loading 3D schedule...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-900 rounded-lg">
        <div className="text-red-500">Error loading voxel data</div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-[600px] bg-gray-900 rounded-lg overflow-hidden">
      {/* Controls overlay */}
      <div className="absolute top-4 left-4 z-10 bg-gray-800/80 p-4 rounded-lg text-white text-sm">
        <h3 className="font-bold mb-2">3D Schedule View</h3>
        <div className="space-y-1 text-gray-300">
          <p>Drag: Pan view</p>
          <p>Shift+Drag: Rotate</p>
          <p>Scroll: Zoom</p>
        </div>
        {data && (
          <div className="mt-4 pt-4 border-t border-gray-600">
            <p>Assignments: {data.statistics.total_assignments}</p>
            <p>Conflicts: {data.statistics.total_conflicts}</p>
            <p>Coverage: {data.statistics.coverage_percentage.toFixed(1)}%</p>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="absolute top-4 right-4 z-10 bg-gray-800/80 p-4 rounded-lg text-white text-sm">
        <h4 className="font-bold mb-2">Activity Types</h4>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: "#3B82F6" }} />
            <span>Clinic</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: "#8B5CF6" }} />
            <span>Inpatient</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: "#EF4444" }} />
            <span>Procedures</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: "#F97316" }} />
            <span>Call</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: "#F59E0B" }} />
            <span>Leave</span>
          </div>
        </div>
      </div>

      {/* Hover tooltip */}
      {hoveredVoxel && (
        <div
          className="absolute z-20 bg-gray-800 text-white p-3 rounded-lg shadow-lg text-sm pointer-events-none"
          style={{ top: "50%", left: "50%" }}
        >
          <div className="font-bold">{hoveredVoxel.identity.person_name}</div>
          <div className="text-gray-300">{hoveredVoxel.identity.activity_name}</div>
          <div className="text-gray-400">
            {hoveredVoxel.identity.block_date} {hoveredVoxel.identity.block_time_of_day}
          </div>
          {hoveredVoxel.state.is_conflict && (
            <div className="text-red-400 mt-1">CONFLICT</div>
          )}
        </div>
      )}

      {/* Main canvas */}
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        onClick={handleClick}
      />

      {/* Axis labels */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-gray-400 text-sm">
        X: Time | Y: People | Z: Activity Type
      </div>
    </div>
  );
}

export default VoxelScheduleView;
