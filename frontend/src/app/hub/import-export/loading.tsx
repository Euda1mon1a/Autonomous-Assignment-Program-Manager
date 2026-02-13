import { CardLoader } from '@/components/LoadingStates';

export default function HubImportExportLoading() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <div className="h-8 w-44 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-64 bg-gray-200 rounded animate-pulse mt-2" />
      </div>
      <CardLoader count={4} className="grid-cols-1 md:grid-cols-2" />
    </div>
  );
}
