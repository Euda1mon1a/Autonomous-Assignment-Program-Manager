/**
 * 3D Voxel Schedule Visualization Feature
 *
 * A novel approach to schedule visualization using 3D voxel space.
 * Includes both 2D canvas-based view and Three.js 3D view.
 */

// Components
export { VoxelScheduleView } from "./VoxelScheduleView";

// Note: VoxelScheduleView3D should be lazy-loaded due to Three.js bundle size
// Use: dynamic(() => import('@/features/voxel-schedule/VoxelScheduleView3D'), { ssr: false })

// Types
export type {
  Voxel,
  VoxelGridData,
  VoxelGridDimensions,
  VoxelGridStatistics,
  VoxelPosition,
  VoxelIdentity,
  VoxelVisual,
  VoxelState,
  VoxelMetadata,
  VoxelScheduleViewProps,
  VoxelConflict,
  CoverageGap,
} from "./types";
