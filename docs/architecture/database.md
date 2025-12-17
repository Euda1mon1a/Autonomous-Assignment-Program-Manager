***REMOVED*** Database Schema

Data models and relationships.

---

***REMOVED******REMOVED*** Overview

- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic

---

***REMOVED******REMOVED*** Core Tables

***REMOVED******REMOVED******REMOVED*** People & Assignments

```
Person
├── id (UUID)
├── name
├── email
├── type (resident/faculty)
├── pgy_level
└── specialty

Assignment
├── id (UUID)
├── block_id → Block
├── person_id → Person
├── role
└── created_at

Block
├── id (UUID)
├── date
├── period (AM/PM)
└── rotation_id → RotationTemplate
```

***REMOVED******REMOVED******REMOVED*** Schedule Management

```
RotationTemplate
├── id (UUID)
├── name
├── type
├── capacity
└── supervision_ratio

Absence
├── id (UUID)
├── person_id → Person
├── type
├── start_date
├── end_date
└── notes
```

---

***REMOVED******REMOVED*** Resilience Tables

```
ResilienceAlert
├── id (UUID)
├── level
├── message
├── resolved_at
└── created_at

ContingencyScenario
├── id (UUID)
├── description
├── impact_score
└── mitigation_plan
```

---

***REMOVED******REMOVED*** Migrations

```bash
***REMOVED*** Create migration
alembic revision --autogenerate -m "description"

***REMOVED*** Apply migrations
alembic upgrade head

***REMOVED*** Rollback
alembic downgrade -1
```
