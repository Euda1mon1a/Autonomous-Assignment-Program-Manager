export default function AdminPeopleLoading() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="h-8 w-32 bg-slate-700 rounded animate-pulse" />
        <div className="h-4 w-64 bg-slate-800 rounded animate-pulse mt-2" />
      </div>
      {/* Filter bar */}
      <div className="flex gap-4 mb-6">
        <div className="h-10 w-48 bg-slate-800 rounded animate-pulse" />
        <div className="h-10 w-32 bg-slate-800 rounded animate-pulse" />
      </div>
      {/* Table skeleton */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
        <div className="bg-slate-800/50 p-4 border-b border-slate-700">
          <div className="grid grid-cols-5 gap-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-4 bg-slate-700 rounded" />
            ))}
          </div>
        </div>
        {Array.from({ length: 8 }).map((_, row) => (
          <div key={row} className="p-4 border-b border-slate-800">
            <div className="grid grid-cols-5 gap-4">
              {Array.from({ length: 5 }).map((_, col) => (
                <div key={col} className="h-4 bg-slate-800 rounded animate-pulse" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
