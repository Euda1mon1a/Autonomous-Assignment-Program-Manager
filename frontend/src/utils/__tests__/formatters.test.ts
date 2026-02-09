import { formatDuration, formatPercentage, truncateText, pluralize } from '../formatters';

describe('formatDuration', () => {
  it('returns minutes only when under 60', () => {
    expect(formatDuration(45)).toBe('45m');
  });

  it('returns hours only when no remainder', () => {
    expect(formatDuration(120)).toBe('2h');
  });

  it('returns hours and minutes', () => {
    expect(formatDuration(150)).toBe('2h 30m');
  });

  it('returns 0m for zero', () => {
    expect(formatDuration(0)).toBe('0m');
  });

  it('returns 0m for negative', () => {
    expect(formatDuration(-10)).toBe('0m');
  });

  it('handles exactly 60 minutes', () => {
    expect(formatDuration(60)).toBe('1h');
  });
});

describe('formatPercentage', () => {
  it('converts fraction to percentage', () => {
    expect(formatPercentage(0.755)).toBe('75.5%');
  });

  it('handles whole percentage input', () => {
    expect(formatPercentage(75.5, 1, false)).toBe('75.5%');
  });

  it('respects decimal places', () => {
    expect(formatPercentage(0.7555, 2)).toBe('75.55%');
  });

  it('handles zero', () => {
    expect(formatPercentage(0)).toBe('0.0%');
  });

  it('handles 100%', () => {
    expect(formatPercentage(1.0)).toBe('100.0%');
  });

  it('handles zero decimals', () => {
    expect(formatPercentage(0.756, 0)).toBe('76%');
  });
});

describe('truncateText', () => {
  it('returns short text unchanged', () => {
    expect(truncateText('hello', 10)).toBe('hello');
  });

  it('returns exact length text unchanged', () => {
    expect(truncateText('hello', 5)).toBe('hello');
  });

  it('adds ellipsis suffix', () => {
    expect(truncateText('hello world', 8)).toBe('hello...');
  });

  it('uses custom suffix', () => {
    expect(truncateText('hello world', 8, '~')).toBe('hello w~');
  });

  it('handles very short max length', () => {
    expect(truncateText('hello world', 3)).toBe('...');
  });

  it('handles max length shorter than suffix', () => {
    expect(truncateText('hello world', 2)).toBe('..');
  });

  it('handles empty suffix', () => {
    expect(truncateText('hello world', 5, '')).toBe('hello');
  });
});

describe('pluralize', () => {
  it('uses singular for count 1', () => {
    expect(pluralize(1, 'item')).toBe('1 item');
  });

  it('adds s for plural by default', () => {
    expect(pluralize(2, 'item')).toBe('2 items');
  });

  it('uses custom plural form', () => {
    expect(pluralize(2, 'person', 'people')).toBe('2 people');
  });

  it('uses plural for zero', () => {
    expect(pluralize(0, 'item')).toBe('0 items');
  });

  it('uses plural for large numbers', () => {
    expect(pluralize(100, 'error')).toBe('100 errors');
  });
});
