# Section 508 Accessibility Audit Upload

Upload folder for auditing frontend components against Section 508 / WCAG 2.1 Level AA requirements.

## Usage

1. Upload all files from this folder to Perplexity Computer
2. Paste the contents of `PROMPT.md` as the session prompt

## File Manifest

| Upload Path | Original Source Path | Size |
|-------------|---------------------|------|
| **components/** (core interactive) | | |
| `components/Navigation.tsx` | `frontend/src/components/Navigation.tsx` | 8K |
| `components/MobileNav.tsx` | `frontend/src/components/MobileNav.tsx` | 10K |
| `components/Modal.tsx` | `frontend/src/components/Modal.tsx` | 5K |
| `components/WeeklyGridEditor.tsx` | `frontend/src/components/WeeklyGridEditor.tsx` | 20K |
| `components/PeopleTable.tsx` | `frontend/src/components/admin/PeopleTable.tsx` | 10K |
| `components/CallAssignmentTable.tsx` | `frontend/src/components/admin/CallAssignmentTable.tsx` | 12K |
| `components/EditableCell.tsx` | `frontend/src/components/admin/EditableCell.tsx` | 8K |
| `components/LoginForm.tsx` | `frontend/src/components/LoginForm.tsx` | 7K |
| `components/Toast.tsx` | `frontend/src/components/Toast.tsx` | 9K |
| `components/ErrorBoundary.tsx` | `frontend/src/components/ErrorBoundary.tsx` | 16K |
| **schedule/** (main views) | | |
| `schedule/SchedulePage.tsx` | `frontend/src/app/schedule/page.tsx` | 18K |
| `schedule/VoxelScheduleView.tsx` | `frontend/src/features/voxel-schedule/VoxelScheduleView.tsx` | 18K |
| **resilience/** (dashboard) | | |
| `resilience/ResilienceHub.tsx` | `frontend/src/features/resilience/ResilienceHub.tsx` | 5K |
| `resilience/BurnoutDashboard.tsx` | `frontend/src/features/resilience/components/BurnoutDashboard.tsx` | 8K |
| **root** | | |
| `layout.tsx` | `frontend/src/app/layout.tsx` | 2K |

## Sections

| # | Section | Focus |
|---|---------|-------|
| 1 | Document Structure | Landmarks, headings, skip links, page titles |
| 2 | Keyboard Navigation | Tab order, focus indicators, escape, arrow keys |
| 3 | ARIA Patterns | Dialog, alert, table, grid roles per WAI-ARIA APG |
| 4 | Drag-and-Drop | WeeklyGridEditor keyboard alternative design |
| 5 | Data Visualization | 3D voxel view + burnout charts text alternatives |
| 6 | Color & Contrast | TailwindCSS class analysis for WCAG AA ratios |
| 7 | Forms & Errors | Label association, error announcement, validation |
| 8 | Remediation Priority | CRITICAL/HIGH/MEDIUM/LOW + testing plan |

## Notes

- No PII: all source code
- Military DoD system — Section 508 compliance is a legal requirement
- No existing a11y utility library — patterns are ad-hoc
- Tech stack: Next.js 14, React 18, TailwindCSS 3.4.1
