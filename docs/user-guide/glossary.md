***REMOVED*** Glossary

This glossary defines key terms used throughout the Residency Scheduler application and documentation.

---

***REMOVED******REMOVED*** A

***REMOVED******REMOVED******REMOVED*** ACGME
**Accreditation Council for Graduate Medical Education** - The organization that accredits residency and fellowship programs in the United States. Sets standards for work hours, supervision, and educational requirements.

***REMOVED******REMOVED******REMOVED*** Academic Year
The annual cycle for residency programs, typically running from July 1 to June 30. Used for scheduling, promotions, and compliance tracking.

***REMOVED******REMOVED******REMOVED*** Admin
The highest-level user role with full system access, including Settings configuration, user management, and all scheduling capabilities.

***REMOVED******REMOVED******REMOVED*** Algorithm
A set of rules and calculations used to generate schedules automatically. The system offers three algorithms: Greedy, Min Conflicts, and CP-SAT.

***REMOVED******REMOVED******REMOVED*** AM/PM
Morning and afternoon sessions used in block-based scheduling. Each day is divided into AM and PM blocks for scheduling purposes.

***REMOVED******REMOVED******REMOVED*** Assignment
A scheduled duty linking a person (resident or faculty) to a specific block of time and rotation/activity.

---

***REMOVED******REMOVED*** B

***REMOVED******REMOVED******REMOVED*** Block
A unit of time in the scheduling system. Can refer to:
- **Scheduling Block**: A 4-week (28-day) period for scheduling purposes
- **Time Block**: A single AM or PM session within a day

***REMOVED******REMOVED******REMOVED*** Block Duration
The length of each scheduling period, typically 28 days (4 weeks). Configurable in Settings.

---

***REMOVED******REMOVED*** C

***REMOVED******REMOVED******REMOVED*** Call
On-call duty, typically overnight or weekend coverage requiring presence at the hospital.

***REMOVED******REMOVED******REMOVED*** CME
**Continuing Medical Education** - Required ongoing education for physicians to maintain licensure and certification.

***REMOVED******REMOVED******REMOVED*** Compliance
Adherence to ACGME rules and regulations. The system monitors 80-hour, 1-in-7, and supervision ratio compliance.

***REMOVED******REMOVED******REMOVED*** Coordinator
User role with schedule management capabilities. Can manage people, templates, absences, and generate schedules, but cannot access Settings.

***REMOVED******REMOVED******REMOVED*** Coverage Rate
The percentage of required positions that are filled in a schedule. Calculated as: (Filled positions / Required positions) × 100.

***REMOVED******REMOVED******REMOVED*** CP-SAT
**Constraint Programming - SATisfiability** - The most thorough scheduling algorithm. Uses Google OR-Tools to find optimal solutions that guarantee ACGME compliance when possible.

***REMOVED******REMOVED******REMOVED*** Critical Violation
The most severe compliance violation level, typically for 80-hour rule breaches. Requires immediate attention.

---

***REMOVED******REMOVED*** D

***REMOVED******REMOVED******REMOVED*** Dashboard
The main landing page after login, showing schedule summary, compliance status, upcoming absences, and quick action buttons.

***REMOVED******REMOVED******REMOVED*** Deployment
Extended military assignment, typically involving active duty away from the training program. May last months.

---

***REMOVED******REMOVED*** E

***REMOVED******REMOVED******REMOVED*** Elective
Optional rotation chosen by the resident, often for subspecialty exposure or research.

***REMOVED******REMOVED******REMOVED*** Export
The process of downloading data from the system in various formats (Excel, CSV, JSON) for external use.

---

***REMOVED******REMOVED*** F

***REMOVED******REMOVED******REMOVED*** Faculty
Attending physicians who supervise residents. Must be present at specific ratios depending on PGY level of residents.

***REMOVED******REMOVED******REMOVED*** Federal Holiday
Government-recognized holidays that may affect scheduling. Configurable in Settings.

---

***REMOVED******REMOVED*** G

***REMOVED******REMOVED******REMOVED*** Greedy Algorithm
The fastest scheduling algorithm. Assigns slots one at a time using simple rules. Good for quick drafts but may not optimize fully.

---

***REMOVED******REMOVED*** H

***REMOVED******REMOVED******REMOVED*** 80-Hour Rule
ACGME requirement limiting residents to maximum 80 work hours per week, averaged over a 4-week period.

---

***REMOVED******REMOVED*** I

***REMOVED******REMOVED******REMOVED*** Inpatient
Hospital-based patient care, typically on wards or in intensive care units. A type of rotation.

---

***REMOVED******REMOVED*** J

***REMOVED******REMOVED******REMOVED*** JSON
**JavaScript Object Notation** - A data format used for exporting system data for programmatic access or backup.

***REMOVED******REMOVED******REMOVED*** JWT
**JSON Web Token** - The authentication method used for secure user sessions.

---

***REMOVED******REMOVED*** M

***REMOVED******REMOVED******REMOVED*** Min Conflicts
A balanced scheduling algorithm that iteratively improves assignments by resolving conflicts. Moderate speed with good results.

---

***REMOVED******REMOVED*** O

***REMOVED******REMOVED******REMOVED*** 1-in-7 Rule
ACGME requirement ensuring residents have at least one 24-hour period free from all clinical duties every 7 days.

---

***REMOVED******REMOVED*** P

***REMOVED******REMOVED******REMOVED*** PGY
**Post-Graduate Year** - Indicates the year of residency training:
- PGY-1: First year (intern)
- PGY-2: Second year
- PGY-3: Third year

***REMOVED******REMOVED******REMOVED*** Procedure
Hands-on medical procedures, often requiring one-on-one supervision. A type of rotation.

---

***REMOVED******REMOVED*** R

***REMOVED******REMOVED******REMOVED*** Resident
A physician in training who has completed medical school and is completing specialty training in a residency program.

***REMOVED******REMOVED******REMOVED*** Rotation
A clinical assignment or activity type (e.g., Clinic, Inpatient, Procedure). Defined by templates.

***REMOVED******REMOVED******REMOVED*** Rotation Template
A reusable definition of a rotation type including name, capacity, supervision requirements, and other constraints.

---

***REMOVED******REMOVED*** S

***REMOVED******REMOVED******REMOVED*** Scheduling Block
See [Block](***REMOVED***block).

***REMOVED******REMOVED******REMOVED*** Supervision Ratio
The required number of faculty to residents during clinical activities:
- PGY-1: 1 faculty per 2 residents (1:2)
- PGY-2/3: 1 faculty per 4 residents (1:4)

---

***REMOVED******REMOVED*** T

***REMOVED******REMOVED******REMOVED*** TDY
**Temporary Duty** - Military term for short-term assignment away from primary duty station. Typically days to weeks for training or temporary work.

***REMOVED******REMOVED******REMOVED*** Template
See [Rotation Template](***REMOVED***rotation-template).

---

***REMOVED******REMOVED*** V

***REMOVED******REMOVED******REMOVED*** Validation
The process of checking a schedule against ACGME rules to identify violations.

***REMOVED******REMOVED******REMOVED*** Violation
When a schedule breaks an ACGME rule. Categorized by severity:
- **Critical**: Most severe (e.g., 80-hour breach)
- **High**: Important (e.g., 1-in-7 breach)
- **Medium**: Moderate (e.g., supervision ratio)
- **Low**: Minor issues

---

***REMOVED******REMOVED*** Quick Reference Table

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

***REMOVED******REMOVED*** Related Guides

- [Getting Started](getting-started.md) - Basic usage
- [FAQ](faq.md) - Common questions
- [Compliance](compliance.md) - ACGME monitoring details

---

*Understanding these terms helps you use the Residency Scheduler effectively.*
