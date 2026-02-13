export default function AdminImportDetailLoading() {
  return (
    <div className="p-6">
      <div className="flex items-center gap-4 mb-6">
        <div className="h-8 w-16 bg-slate-800 rounded animate-pulse" />
        <div className="h-8 w-48 bg-slate-700 rounded animate-pulse" />
      </div>
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 animate-pulse">
        <div className="h-5 w-40 bg-slate-700 rounded mb-4" />
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-4 bg-slate-800 rounded" style={{ width: `${60 + Math.random() * 40}%` }} />
          ))}
        </div>
      </div>
    </div>
  );
}
