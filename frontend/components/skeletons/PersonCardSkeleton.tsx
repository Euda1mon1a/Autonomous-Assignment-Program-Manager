export function PersonCardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow p-4 animate-pulse">
      <div className="flex items-center gap-3 mb-3">
        {/* Avatar placeholder */}
        <div className="h-10 w-10 bg-gray-200 rounded-full"></div>
        <div className="flex-1">
          {/* Name */}
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          {/* Email */}
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
      <div className="space-y-2">
        {/* Type badge */}
        <div className="h-5 bg-gray-200 rounded w-20"></div>
        {/* Details row */}
        <div className="flex gap-2">
          <div className="h-3 bg-gray-200 rounded w-16"></div>
          <div className="h-3 bg-gray-200 rounded w-24"></div>
        </div>
      </div>
    </div>
  );
}
