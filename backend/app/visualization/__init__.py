"""
Visualization module for 3D schedule exploration.

This module provides novel 3D visualization capabilities for schedule data,
transforming traditional 2D grids into interactive voxel-based representations.
"""

from app.visualization.schedule_voxel import (
    RotationLayer,
    ScheduleVoxel,
    ScheduleVoxelGrid,
    ScheduleVoxelTransformer,
    VoxelColor,
    VoxelGridDimensions,
    transform_schedule_to_voxels,
    ROTATION_COLORS,
    COMPLIANCE_COLORS,
)

__all__ = [
    "RotationLayer",
    "ScheduleVoxel",
    "ScheduleVoxelGrid",
    "ScheduleVoxelTransformer",
    "VoxelColor",
    "VoxelGridDimensions",
    "transform_schedule_to_voxels",
    "ROTATION_COLORS",
    "COMPLIANCE_COLORS",
]
