export default function ScheduleLoading() {
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header skeleton */}
      <div className="flex-shrink-0 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-full px-4 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="h-8 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 w-64 bg-gray-200 rounded animate-pulse mt-2" />
            </div>
            <div className="flex gap-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-9 w-20 bg-gray-200 rounded animate-pulse" />
              ))}
            </div>
          </div>
          {/* Navigation skeleton */}
          <div className="flex items-center gap-4">
            <div className="h-8 w-8 bg-gray-200 rounded animate-pulse" />
            <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
            <div className="h-8 w-8 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
      </div>

      {/* Grid skeleton */}
      <div className="flex-1 overflow-auto p-4">
        <div className="animate-pulse">
          <div className="grid grid-cols-8 gap-1">
            {/* Header row */}
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={`h-${i}`} className="h-10 bg-gray-200 rounded" />
            ))}
            {/* Data rows */}
            {Array.from({ length: 12 }).map((_, row) =>
              Array.from({ length: 8 }).map((_, col) => (
                <div key={`${row}-${col}`} className="h-8 bg-gray-100 rounded" />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
