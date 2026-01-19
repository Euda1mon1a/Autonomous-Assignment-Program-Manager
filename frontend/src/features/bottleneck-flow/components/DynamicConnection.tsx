/**
 * Dynamic Connection Component
 *
 * Line connecting a trainee to their supervising faculty.
 * Updates every frame to track moving trainee positions.
 * Color and opacity vary by trainee status.
 */

'use client';

import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { THREE_COLORS } from '../constants';
import type { DynamicConnectionProps } from '../types';

export function DynamicConnection({
  traineeRef,
  targetPos,
  status,
}: DynamicConnectionProps) {
  // Track current points for the line
  const [points, setPoints] = useState<[number, number, number][]>([
    [0, 0, 0],
    [targetPos.x, targetPos.y, targetPos.z],
  ]);

  // Frame counter to throttle updates
  const frameCount = useRef(0);

  useFrame(() => {
    if (traineeRef.current) {
      // Throttle updates to every 3rd frame for performance
      frameCount.current++;
      if (frameCount.current % 3 !== 0) return;

      const start = traineeRef.current.position;
      setPoints([
        [start.x, start.y, start.z],
        [targetPos.x, targetPos.y, targetPos.z],
      ]);
    }
  });

  // Color based on status
  const color =
    status === 'nominal'
      ? THREE_COLORS.nominal
      : status === 'rerouted'
        ? THREE_COLORS.degraded
        : THREE_COLORS.critical;

  // Opacity based on status
  const opacity =
    status === 'orphaned' ? 0.05 : status === 'nominal' ? 0.2 : 0.4;

  return (
    <Line
      points={points}
      color={color}
      transparent
      opacity={opacity}
      lineWidth={1}
    />
  );
}

export default DynamicConnection;
