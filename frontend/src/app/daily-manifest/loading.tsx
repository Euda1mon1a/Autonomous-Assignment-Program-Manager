import { TableLoader } from '@/components/LoadingStates';

export default function DailyManifestLoading() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <div className="h-8 w-44 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-64 bg-gray-200 rounded animate-pulse mt-2" />
      </div>
      {/* Date selector skeleton */}
      <div className="flex items-center gap-4 mb-6">
        <div className="h-8 w-8 bg-gray-200 rounded animate-pulse" />
        <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
        <div className="h-8 w-8 bg-gray-200 rounded animate-pulse" />
      </div>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <TableLoader rows={10} columns={4} />
      </div>
    </div>
  );
}
