export default function BoardReviewLoading() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-slate-600 border-t-indigo-400 rounded-full animate-spin mx-auto mb-4" />
        <p className="text-slate-400 text-sm">Loading Board Review...</p>
      </div>
    </div>
  );
}
