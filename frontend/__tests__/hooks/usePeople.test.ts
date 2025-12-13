// __tests__/hooks/usePeople.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { usePeople } from '@/lib/hooks';

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

describe('usePeople', () => {
  it('should fetch people data', async () => {
    // TODO: Implement test
  });

  it('should handle errors', async () => {
    // TODO: Implement test
  });

  it('should refetch on filter change', async () => {
    // TODO: Implement test
  });
});
