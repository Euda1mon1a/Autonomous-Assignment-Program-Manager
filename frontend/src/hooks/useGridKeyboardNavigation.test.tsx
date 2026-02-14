/**
 * Tests for useGridKeyboardNavigation Hook
 */
import { fireEvent, render } from '@testing-library/react';
import { useGridKeyboardNavigation } from './useGridKeyboardNavigation';

type GridProps = {
  rowCount: number;
  colCount: number;
  onCellActivate: (position: { row: number; col: number }) => void;
};

const Grid = ({ rowCount, colCount, onCellActivate }: GridProps) => {
  const { gridProps, getCellProps } = useGridKeyboardNavigation({
    rowCount,
    colCount,
    onCellActivate,
  });

  return (
    <div data-testid="grid" {...gridProps}>
      {Array.from({ length: rowCount }).map((_, row) => (
        <div key={`row-${row}`}>
          {Array.from({ length: colCount }).map((_, col) => (
            <button
              key={`cell-${row}-${col}`}
              data-testid={`cell-${row}-${col}`}
              type="button"
              {...getCellProps(row, col)}
            >
              {row},{col}
            </button>
          ))}
        </div>
      ))}
    </div>
  );
};

const originalRaf = global.requestAnimationFrame;

describe('useGridKeyboardNavigation', () => {
  beforeEach(() => {
    global.requestAnimationFrame = (callback: FrameRequestCallback) => {
      callback(0);
      return 0;
    };
  });

  afterEach(() => {
    global.requestAnimationFrame = originalRaf;
  });

  it('moves focus with arrow keys and activates cells', () => {
    const onCellActivate = jest.fn();
    const { getByTestId } = render(
      <Grid rowCount={2} colCount={2} onCellActivate={onCellActivate} />
    );

    const grid = getByTestId('grid');
    const cell00 = getByTestId('cell-0-0');
    const cell01 = getByTestId('cell-0-1');
    const cell10 = getByTestId('cell-1-0');
    const cell11 = getByTestId('cell-1-1');

    expect(cell00.getAttribute('tabindex')).toBe('0');

    fireEvent.focus(cell00);
    fireEvent.keyDown(grid, { key: 'ArrowRight' });
    expect(document.activeElement).toBe(cell01);

    fireEvent.keyDown(grid, { key: 'ArrowDown' });
    expect(document.activeElement).toBe(cell11);

    fireEvent.keyDown(grid, { key: 'Home' });
    expect(document.activeElement).toBe(cell10);

    fireEvent.keyDown(grid, { key: 'Enter' });
    expect(onCellActivate).toHaveBeenCalledWith({ row: 1, col: 0 });
  });
});
