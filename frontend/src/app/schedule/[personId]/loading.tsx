import { PageSpinner } from '@/components/LoadingStates';

export default function PersonScheduleLoading() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <div className="h-5 w-24 bg-gray-200 rounded animate-pulse mb-2" />
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-64 bg-gray-200 rounded animate-pulse mt-2" />
      </div>
      <PageSpinner message="Loading schedule..." />
    </div>
  );
}
