export interface ValidationWarning {
  row: number;
  personName: string;
  message: string;
}

// Minimal placeholder logic for local ACGME pre-flight
export function validateScheduleLocal(grid: any[][], refs: {rotations: string[], activities: string[]}): ValidationWarning[] {
  const warnings: ValidationWarning[] = [];

  // Assuming grid has headers on row 0 and 1, data starts at row 2
  // Usually the real visible grid starts data around row 9 based on python code,
  // but `grid` here is the `usedRange.values` which might be offset.
  // For the sake of this local rule engine, we will do a simple heuristic scan:
  // Look for rows that have a person name in column 4 (index 4) and days in following columns.

  // Note: 1-in-7 rule: no more than 6 consecutive days of work.
  // Work = any activity that isn't DO (Day Off), LV (Leave), or empty.

  for (let r = 0; r < grid.length; r++) {
    const row = grid[r];
    if (!row) continue;

    // Simple heuristic to find a person row: Name is usually a string and not "Name"
    const nameCol = 5; // Column F in Excel is index 5
    const name = row[nameCol];
    if (typeof name === 'string' && name.trim() !== '' && name.trim() !== 'Name' && name.trim() !== 'Resident') {

      let consecutiveWorkDays = 0;
      // Schedule usually starts around column 6 (G) or later depending on exact layout
      // Let's just scan all columns for activity codes.
      // Since days are AM/PM, 2 columns per day.
      let dailyWorkHalfDays = 0;

      for (let c = 6; c < row.length; c+=2) {
        const am = row[c];
        const pm = row[c+1];

        const isAmWork = am && am !== 'DO' && am !== 'LV' && refs.activities.includes(am);
        const isPmWork = pm && pm !== 'DO' && pm !== 'LV' && refs.activities.includes(pm);

        if (isAmWork || isPmWork) {
          consecutiveWorkDays++;
          if (consecutiveWorkDays === 7) {
            warnings.push({
              row: r + 1, // 1-indexed
              personName: name,
              message: `Potential 1-in-7 violation: ${consecutiveWorkDays}+ consecutive days worked.`
            });
          }
        } else {
          consecutiveWorkDays = 0; // Got a day off
        }
      }
    }
  }

  return warnings;
}
