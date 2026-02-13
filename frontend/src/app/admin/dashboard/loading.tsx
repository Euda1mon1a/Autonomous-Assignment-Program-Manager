export default function AdminDashboardLoading() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">Dashboard</h1>
      <div className="animate-pulse space-y-6">
        {[1, 2, 3].map((group) => (
          <div key={group} className="space-y-3">
            <div className="h-4 w-24 bg-slate-700 rounded" />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map((card) => (
                <div key={card} className="h-24 bg-slate-800/50 rounded-lg border border-slate-700" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
