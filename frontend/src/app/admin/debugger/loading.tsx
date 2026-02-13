export default function DebuggerLoading() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="h-8 w-32 bg-slate-700 rounded animate-pulse" />
        <div className="h-4 w-64 bg-slate-800 rounded animate-pulse mt-2" />
      </div>
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 animate-pulse">
            <div className="h-5 w-40 bg-slate-700 rounded mb-3" />
            <div className="h-4 w-full bg-slate-800 rounded mb-2" />
            <div className="h-4 w-2/3 bg-slate-800 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
