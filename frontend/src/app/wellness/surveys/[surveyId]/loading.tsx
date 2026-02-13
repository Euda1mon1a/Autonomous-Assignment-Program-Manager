import { PageSpinner } from '@/components/LoadingStates';

export default function SurveyLoading() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="mb-6">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-64 bg-gray-200 rounded animate-pulse mt-2" />
      </div>
      <PageSpinner message="Loading survey..." />
    </div>
  );
}
