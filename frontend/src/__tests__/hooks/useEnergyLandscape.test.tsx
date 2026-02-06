/**
 * Tests for energy landscape hook.
 */
import { act, renderHook } from '@/test-utils';
import { TestProviders } from '@/test-utils';
import { useEnergyLandscape } from '@/hooks/useEnergyLandscape';
import * as api from '@/api/exotic-resilience';
import { ReactNode } from 'react';

jest.mock('@/api/exotic-resilience');

const mockedApi = api as jest.Mocked<typeof api>;

function createWrapper() {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <TestProviders>{children}</TestProviders>;
  };
}

describe('useEnergyLandscape', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('executes energy landscape analysis', async () => {
    mockedApi.analyzeEnergyLandscape.mockResolvedValueOnce({
      currentEnergy: 1,
      isLocalMinimum: true,
      estimatedBasinSize: 3,
      meanBarrierHeight: 0.5,
      meanGradient: 0.2,
      landscapeRuggedness: 0.4,
      numLocalMinima: 2,
      interpretation: 'ok',
      recommendations: [],
      computedAt: '2025-01-01T00:00:00Z',
      source: 'test',
    });

    const { result } = renderHook(() => useEnergyLandscape(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({ scheduleId: 'schedule-1' });
    });

    expect(mockedApi.analyzeEnergyLandscape).toHaveBeenCalledWith({
      scheduleId: 'schedule-1',
    });
  });
});
