export default function LoginLoading() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      {/* Logo skeleton */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-12 h-12 bg-gray-200 rounded animate-pulse" />
        <div>
          <div className="h-7 w-44 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-28 bg-gray-200 rounded animate-pulse mt-1" />
        </div>
      </div>

      {/* Login card skeleton */}
      <div className="w-full max-w-md bg-white rounded-lg shadow-sm border border-gray-200 p-8 animate-pulse">
        <div className="h-6 w-32 bg-gray-200 rounded mx-auto mb-6" />
        <div className="space-y-4">
          <div>
            <div className="h-4 w-16 bg-gray-200 rounded mb-1" />
            <div className="h-10 w-full bg-gray-200 rounded" />
          </div>
          <div>
            <div className="h-4 w-20 bg-gray-200 rounded mb-1" />
            <div className="h-10 w-full bg-gray-200 rounded" />
          </div>
          <div className="h-10 w-full bg-gray-200 rounded mt-2" />
        </div>
      </div>

      {/* Footer skeleton */}
      <div className="h-4 w-64 bg-gray-200 rounded animate-pulse mt-8" />
    </div>
  );
}
