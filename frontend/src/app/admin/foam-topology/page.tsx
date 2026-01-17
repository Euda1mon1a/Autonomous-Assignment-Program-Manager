'use client';

import dynamic from 'next/dynamic';
import { ProtectedRoute } from '@/components/ProtectedRoute';

const FoamTopologyVisualizer = dynamic(
  () => import('@/components/scheduling/FoamTopologyVisualizer'),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-screen bg-black text-white">
        Loading 3D Foam Topology...
      </div>
    ),
  }
);

export default function FoamTopologyPage() {
  return (
    <ProtectedRoute requireAdmin={true}>
      <FoamTopologyVisualizer />
    </ProtectedRoute>
  );
}
