import { AdaptiveDebouncer, DebounceMonitor } from '../debounce';

// Note: debounce, debounceLeading, throttle use setTimeout which is tricky
// to test without jest.useFakeTimers. Focus on the class-based utilities
// which have deterministic behavior.

describe('DebounceMonitor', () => {
  let monitor: DebounceMonitor;

  beforeEach(() => {
    monitor = new DebounceMonitor();
  });

  it('starts with zero stats', () => {
    const stats = monitor.getStats();
    expect(stats.totalCalls).toBe(0);
    expect(stats.executedCalls).toBe(0);
    expect(stats.skippedCalls).toBe(0);
    expect(stats.reductionRate).toBe(0);
  });

  it('records executed calls', () => {
    monitor.recordCall(true);
    const stats = monitor.getStats();
    expect(stats.totalCalls).toBe(1);
    expect(stats.executedCalls).toBe(1);
    expect(stats.skippedCalls).toBe(0);
  });

  it('records skipped calls', () => {
    monitor.recordCall(false);
    const stats = monitor.getStats();
    expect(stats.totalCalls).toBe(1);
    expect(stats.executedCalls).toBe(0);
    expect(stats.skippedCalls).toBe(1);
  });

  it('calculates reduction rate', () => {
    monitor.recordCall(false); // skipped
    monitor.recordCall(false); // skipped
    monitor.recordCall(true); // executed
    monitor.recordCall(false); // skipped

    expect(monitor.getReductionRate()).toBe(75); // 3/4 = 75%
  });

  it('returns 0 reduction rate with no calls', () => {
    expect(monitor.getReductionRate()).toBe(0);
  });

  it('resets stats', () => {
    monitor.recordCall(true);
    monitor.recordCall(false);
    monitor.reset();

    const stats = monitor.getStats();
    expect(stats.totalCalls).toBe(0);
    expect(stats.executedCalls).toBe(0);
    expect(stats.skippedCalls).toBe(0);
  });
});

describe('AdaptiveDebouncer', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('calls the function after delay', () => {
    const fn = jest.fn();
    const debouncer = new AdaptiveDebouncer(fn, 100, 1000);

    debouncer.call();
    expect(fn).not.toHaveBeenCalled();

    jest.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('resets timer on subsequent calls', () => {
    const fn = jest.fn();
    const debouncer = new AdaptiveDebouncer(fn, 100, 1000);

    debouncer.call();
    jest.advanceTimersByTime(50);
    debouncer.call(); // Reset the timer
    jest.advanceTimersByTime(50);
    expect(fn).not.toHaveBeenCalled(); // Still waiting

    jest.advanceTimersByTime(1000); // Wait for adaptive delay
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('passes arguments to the function', () => {
    const fn = jest.fn();
    const debouncer = new AdaptiveDebouncer(fn, 100, 1000);

    debouncer.call('arg1', 'arg2');
    jest.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledWith('arg1', 'arg2');
  });
});
