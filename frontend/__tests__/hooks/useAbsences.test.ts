// __tests__/hooks/useAbsences.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAbsences } from '@/lib/hooks';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useAbsences', () => {
  it('should fetch absences data', async () => {
    // TODO: Implement test
  });

  it('should handle errors', async () => {
    // TODO: Implement test
  });

  it('should refetch on date range change', async () => {
    // TODO: Implement test
  });
});
