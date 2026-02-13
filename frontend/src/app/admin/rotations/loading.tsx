export default function AdminRotationsLoading() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="h-8 w-32 bg-slate-700 rounded animate-pulse" />
        <div className="h-4 w-64 bg-slate-800 rounded animate-pulse mt-2" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 animate-pulse">
            <div className="h-5 w-32 bg-slate-700 rounded mb-3" />
            <div className="h-4 w-48 bg-slate-800 rounded mb-2" />
            <div className="h-4 w-40 bg-slate-800 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
