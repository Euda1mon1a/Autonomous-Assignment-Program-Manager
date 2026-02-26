import { format } from 'date-fns'
import { buildTSV } from '@/hooks/useCopyGridClipboard'
import type { SelectionBounds } from '@/hooks/useCopyGridSelection'

const days = [new Date(2026, 1, 1), new Date(2026, 1, 2)]

const gridData = {
  people: [
    { id: 'r1', name: 'Dr. Alpha' },
    { id: 'r2', name: 'Dr. Beta' },
  ],
  days,
  getAbbreviation: (personId: string, dateStr: string) =>
    `${personId}-${dateStr}`,
}

describe('buildTSV', () => {
  it('builds a TSV with headers and selected rows/cols', () => {
    const bounds: SelectionBounds = {
      startRow: 0,
      endRow: 1,
      startCol: 0,
      endCol: 1,
    }

    const expected = [
      ['', format(days[0], 'EEE M/d'), format(days[1], 'EEE M/d')].join('\t'),
      ['Dr. Alpha', 'r1-2026-02-01', 'r1-2026-02-02'].join('\t'),
      ['Dr. Beta', 'r2-2026-02-01', 'r2-2026-02-02'].join('\t'),
    ].join('\n')

    expect(buildTSV(gridData, bounds)).toBe(expected)
  })
})
