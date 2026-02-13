export default function ProceduresLoading() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="h-8 w-36 bg-slate-700 rounded animate-pulse" />
        <div className="h-4 w-64 bg-slate-800 rounded animate-pulse mt-2" />
      </div>
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
        <div className="bg-slate-800/50 p-4 border-b border-slate-700">
          <div className="grid grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-4 bg-slate-700 rounded" />
            ))}
          </div>
        </div>
        {Array.from({ length: 6 }).map((_, row) => (
          <div key={row} className="p-4 border-b border-slate-800">
            <div className="grid grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, col) => (
                <div key={col} className="h-4 bg-slate-800 rounded animate-pulse" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
