/**
 * Supervision Matrix Component
 *
 * Visualizes the supervision relationships between faculty and trainees.
 * Lines connect available faculty to the trainees they supervise.
 * Lines turn red when faculty availability drops below requirements.
 */

"use client";

import React, { useMemo } from "react";
import { Line } from "@react-three/drei";

import { SupervisionMatrixProps } from "../types";
import { generateUnitSpecs, getUnitPosition, DEFAULT_DATA } from "../constants";

export const SupervisionMatrix: React.FC<SupervisionMatrixProps> = ({
  entropy,
  availableFaculty,
}) => {
  const unitSpecs = useMemo(() => generateUnitSpecs(DEFAULT_DATA), []);

  // Calculate supervision lines
  const lines = useMemo(() => {
    // Get available faculty (based on attrition from entropy)
    const faculty = unitSpecs
      .filter((u) => u.type === "FACULTY")
      .slice(0, availableFaculty);

    // Get all trainees
    const trainees = unitSpecs.filter((u) => u.type !== "FACULTY");

    if (faculty.length === 0) return [];

    // Map trainees to faculty in round-robin fashion
    return trainees.map((trainee, i) => {
      const assignedFaculty = faculty[i % faculty.length];

      // Find indices for position calculation
      const traineeIdx = unitSpecs.findIndex((u) => u.id === trainee.id);
      const facultyIdx = unitSpecs.findIndex((u) => u.id === assignedFaculty.id);

      // Calculate positions on the real-time brane (offset 0)
      const start = getUnitPosition(
        trainee,
        traineeIdx,
        unitSpecs.length,
        entropy,
        0
      );
      const end = getUnitPosition(
        assignedFaculty,
        facultyIdx,
        unitSpecs.length,
        entropy,
        0
      );

      return { start, end, id: `line-${trainee.id}-${assignedFaculty.id}` };
    });
  }, [unitSpecs, availableFaculty, entropy]);

  // Determine line color based on faculty availability
  const isCritical = availableFaculty < 7;
  const lineColor = isCritical ? "#ff3131" : "#00d4ff";
  const lineOpacity = isCritical ? 0.3 : 0.15 * (1 - entropy);

  return (
    <group>
      {lines.map((line) => (
        <Line
          key={line.id}
          points={[line.start, line.end]}
          color={lineColor}
          lineWidth={0.5}
          transparent
          opacity={lineOpacity}
        />
      ))}
    </group>
  );
};

export default SupervisionMatrix;
