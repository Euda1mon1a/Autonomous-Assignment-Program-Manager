# Glossary

This glossary defines key terms used throughout the Residency Scheduler application and documentation.

---

## A

### ACGME
**Accreditation Council for Graduate Medical Education** - The organization that accredits residency and fellowship programs in the United States. Sets standards for work hours, supervision, and educational requirements.

### Academic Year
The annual cycle for residency programs, typically running from July 1 to June 30. Used for scheduling, promotions, and compliance tracking.

### Admin
The highest-level user role with full system access, including Settings configuration, user management, and all scheduling capabilities.

### Algorithm
A set of rules and calculations used to generate schedules automatically. The system offers three algorithms: Greedy, Min Conflicts, and CP-SAT.

### AM/PM
Morning and afternoon sessions used in block-based scheduling. Each day is divided into AM and PM blocks for scheduling purposes.

### Assignment
A scheduled duty linking a person (resident or faculty) to a specific block of time and rotation/activity.

---

## B

### Block
A unit of time in the scheduling system. Can refer to:
- **Scheduling Block**: A 4-week (28-day) period for scheduling purposes
- **Time Block**: A single AM or PM session within a day

### Block Duration
The length of each scheduling period, typically 28 days (4 weeks). Configurable in Settings.

---

## C

### Call
On-call duty, typically overnight or weekend coverage requiring presence at the hospital.

### CME
**Continuing Medical Education** - Required ongoing education for physicians to maintain licensure and certification.

### Compliance
Adherence to ACGME rules and regulations. The system monitors 80-hour, 1-in-7, and supervision ratio compliance.

### Coordinator
User role with schedule management capabilities. Can manage people, templates, absences, and generate schedules, but cannot access Settings.

### Coverage Rate
The percentage of required positions that are filled in a schedule. Calculated as: (Filled positions / Required positions) × 100.

### CP-SAT
**Constraint Programming - SATisfiability** - The most thorough scheduling algorithm. Uses Google OR-Tools to find optimal solutions that guarantee ACGME compliance when possible.

### Critical Violation
The most severe compliance violation level, typically for 80-hour rule breaches. Requires immediate attention.

---

## D

### Dashboard
The main landing page after login, showing schedule summary, compliance status, upcoming absences, and quick action buttons.

### Deployment
Extended military assignment, typically involving active duty away from the training program. May last months.

---

## E

### Elective
Optional rotation chosen by the resident, often for subspecialty exposure or research.

### Export
The process of downloading data from the system in various formats (Excel, CSV, JSON) for external use.

---

## F

### Faculty
Attending physicians who supervise residents. Must be present at specific ratios depending on PGY level of residents.

### Federal Holiday
Government-recognized holidays that may affect scheduling. Configurable in Settings.

---

## G

### Greedy Algorithm
The fastest scheduling algorithm. Assigns slots one at a time using simple rules. Good for quick drafts but may not optimize fully.

---

## H

### 80-Hour Rule
ACGME requirement limiting residents to maximum 80 work hours per week, averaged over a 4-week period.

---

## I

### Inpatient
Hospital-based patient care, typically on wards or in intensive care units. A type of rotation.

---

## J

### JSON
**JavaScript Object Notation** - A data format used for exporting system data for programmatic access or backup.

### JWT
**JSON Web Token** - The authentication method used for secure user sessions.

---

## M

### Min Conflicts
A balanced scheduling algorithm that iteratively improves assignments by resolving conflicts. Moderate speed with good results.

---

## O

### 1-in-7 Rule
ACGME requirement ensuring residents have at least one 24-hour period free from all clinical duties every 7 days.

---

## P

### PGY
**Post-Graduate Year** - Indicates the year of residency training:
- PGY-1: First year (intern)
- PGY-2: Second year
- PGY-3: Third year

### Procedure
Hands-on medical procedures, often requiring one-on-one supervision. A type of rotation.

---

## R

### Resident
A physician in training who has completed medical school and is completing specialty training in a residency program.

### Rotation
A clinical assignment or activity type (e.g., Clinic, Inpatient, Procedure). Defined by templates.

### Rotation Template
A reusable definition of a rotation type including name, capacity, supervision requirements, and other constraints.

---

## S

### Scheduling Block
See [Block](#block).

### Supervision Ratio
The required number of faculty to residents during clinical activities:
- PGY-1: 1 faculty per 2 residents (1:2)
- PGY-2/3: 1 faculty per 4 residents (1:4)

---

## T

### TDY
**Temporary Duty** - Military term for short-term assignment away from primary duty station. Typically days to weeks for training or temporary work.

### Template
See [Rotation Template](#rotation-template).

---

## V

### Validation
The process of checking a schedule against ACGME rules to identify violations.

### Violation
When a schedule breaks an ACGME rule. Categorized by severity:
- **Critical**: Most severe (e.g., 80-hour breach)
- **High**: Important (e.g., 1-in-7 breach)
- **Medium**: Moderate (e.g., supervision ratio)
- **Low**: Minor issues

---

## Quick Reference Table

| Term | Quick Definition |
|------|------------------|
| ACGME | Medical education accrediting body |
| Block | 4-week scheduling period |
| CP-SAT | Optimal scheduling algorithm |
| Coverage Rate | Percentage of positions filled |
| Greedy | Fast scheduling algorithm |
| Min Conflicts | Balanced scheduling algorithm |
| PGY | Year of residency training |
| TDY | Temporary military duty |
| 80-Hour Rule | Max 80 hrs/week average |
| 1-in-7 Rule | One day off per 7 days |

---

## Related Guides

- [Getting Started](getting-started.md) - Basic usage
- [FAQ](faq.md) - Common questions
- [Compliance](compliance.md) - ACGME monitoring details

---

*Understanding these terms helps you use the Residency Scheduler effectively.*
