import { CardLoader } from '@/components/LoadingStates';

export default function SwapsLoading() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header skeleton */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-200 rounded-lg animate-pulse w-10 h-10" />
            <div>
              <div className="h-7 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 w-64 bg-gray-200 rounded animate-pulse mt-1" />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <CardLoader count={4} />
      </main>
    </div>
  );
}
