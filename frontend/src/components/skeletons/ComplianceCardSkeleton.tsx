export function ComplianceCardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow p-4 animate-pulse">
      <div className="flex items-center justify-between mb-4">
        {/* Title */}
        <div className="h-5 bg-gray-200 rounded w-32"></div>
        {/* Status badge */}
        <div className="h-6 bg-gray-200 rounded w-16"></div>
      </div>
      {/* Progress bar */}
      <div className="h-2 bg-gray-200 rounded w-full mb-4"></div>
      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="h-3 bg-gray-200 rounded w-16 mb-1"></div>
          <div className="h-6 bg-gray-200 rounded w-12"></div>
        </div>
        <div>
          <div className="h-3 bg-gray-200 rounded w-20 mb-1"></div>
          <div className="h-6 bg-gray-200 rounded w-12"></div>
        </div>
      </div>
      {/* Violation list placeholder */}
      <div className="mt-4 space-y-2">
        <div className="h-3 bg-gray-200 rounded w-full"></div>
        <div className="h-3 bg-gray-200 rounded w-5/6"></div>
      </div>
    </div>
  );
}
