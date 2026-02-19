export default function RotationsLoading() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Risk Bar skeleton */}
      <div className="h-8 bg-gray-200 animate-pulse" />

      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-200 rounded-lg animate-pulse w-10 h-10" />
            <div>
              <div className="h-7 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 w-64 bg-gray-200 rounded animate-pulse mt-2" />
            </div>
          </div>

          {/* Tab navigation skeleton */}
          <div className="mt-4 -mb-px flex space-x-8">
            <div className="h-10 w-40 bg-gray-200 rounded animate-pulse" />
            <div className="h-10 w-40 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
      </header>

      {/* Main content skeleton */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <div className="flex justify-center py-12">
          <div className="h-10 w-10 border-4 border-gray-200 border-t-gray-400 rounded-full animate-spin" />
        </div>
      </main>
    </div>
  );
}
