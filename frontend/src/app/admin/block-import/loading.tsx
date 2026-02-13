export default function BlockImportLoading() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="h-8 w-40 bg-slate-700 rounded animate-pulse" />
        <div className="h-4 w-64 bg-slate-800 rounded animate-pulse mt-2" />
      </div>
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 animate-pulse">
        <div className="h-5 w-40 bg-slate-700 rounded mb-4" />
        <div className="h-32 w-full bg-slate-800 rounded-lg border-2 border-dashed border-slate-700 mb-4" />
        <div className="h-10 w-32 bg-slate-700 rounded" />
      </div>
    </div>
  );
}
