export default function ScheduleDraftDetailLoading() {
  return (
    <div className="container mx-auto py-8 px-4 space-y-6">
      <div className="flex items-center gap-4 mb-2">
        <div className="h-8 w-16 bg-slate-800 rounded animate-pulse" />
        <div className="h-8 w-64 bg-slate-700 rounded animate-pulse" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 animate-pulse">
            <div className="h-6 w-32 bg-slate-700 rounded mb-4" />
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex justify-between">
                  <div className="h-4 w-20 bg-slate-800 rounded" />
                  <div className="h-4 w-32 bg-slate-800 rounded" />
                </div>
              ))}
            </div>
          </div>
        </div>
        {/* Right column */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 animate-pulse">
            <div className="h-6 w-40 bg-slate-700 rounded mb-4" />
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-16 bg-slate-800/50 rounded-lg border border-slate-700" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
