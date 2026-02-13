import { TableLoader } from '@/components/LoadingStates';

export default function ProxyCoverageLoading() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <div className="h-8 w-44 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-64 bg-gray-200 rounded animate-pulse mt-2" />
      </div>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <TableLoader rows={6} columns={5} />
      </div>
    </div>
  );
}
