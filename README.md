***REMOVED*** Residency Scheduler

A standalone, production-ready residency scheduling application with ACGME compliance validation.

***REMOVED******REMOVED*** Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: Next.js (React) + TailwindCSS
- **Database**: PostgreSQL

***REMOVED******REMOVED*** Features

- **Rotation Templates**: Reusable activity patterns with constraints (clinic capacity, specialty requirements, ACGME supervision ratios)
- **Scheduling Engine**: Greedy algorithm with constraint-based assignment
- **ACGME Validation**: 80-hour rule, 1-in-7 days off, supervision ratios
- **Emergency Coverage**: Handle deployments, TDY, medical emergencies with automatic replacement finding
- **Calendar-First UI**: Clean, intuitive interface designed for clinicians

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

***REMOVED******REMOVED******REMOVED*** Running with Docker

```bash
***REMOVED*** Clone the repository
git clone <repository-url>
cd residency-scheduler

***REMOVED*** Copy environment file
cp .env.example .env

***REMOVED*** Start all services
docker-compose up -d

***REMOVED*** Access the application
***REMOVED*** Frontend: http://localhost:3000
***REMOVED*** Backend API: http://localhost:8000
***REMOVED*** API Docs: http://localhost:8000/docs
```

***REMOVED******REMOVED******REMOVED*** Local Development

***REMOVED******REMOVED******REMOVED******REMOVED*** Backend

```bash
cd backend

***REMOVED*** Create virtual environment
python -m venv venv
source venv/bin/activate  ***REMOVED*** On Windows: venv\Scripts\activate

***REMOVED*** Install dependencies
pip install -r requirements.txt

***REMOVED*** Run migrations
alembic upgrade head

***REMOVED*** Start the server
uvicorn app.main:app --reload
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Frontend

```bash
cd frontend

***REMOVED*** Install dependencies
npm install

***REMOVED*** Start development server
npm run dev
```

***REMOVED******REMOVED*** Project Structure

```
residency-scheduler/
├── backend/
│   ├── app/
│   │   ├── api/routes/       ***REMOVED*** API endpoints
│   │   ├── core/             ***REMOVED*** Configuration
│   │   ├── db/               ***REMOVED*** Database connection
│   │   ├── models/           ***REMOVED*** SQLAlchemy models
│   │   ├── schemas/          ***REMOVED*** Pydantic schemas
│   │   ├── scheduling/       ***REMOVED*** Scheduling engine
│   │   └── services/         ***REMOVED*** Business logic
│   ├── alembic/              ***REMOVED*** Database migrations
│   └── tests/                ***REMOVED*** Backend tests
├── frontend/
│   └── src/
│       ├── app/              ***REMOVED*** Next.js pages
│       ├── components/       ***REMOVED*** React components
│       ├── lib/              ***REMOVED*** API client & hooks
│       └── types/            ***REMOVED*** TypeScript types
├── docker-compose.yml        ***REMOVED*** Docker configuration
└── README.md
```

***REMOVED******REMOVED*** API Endpoints

***REMOVED******REMOVED******REMOVED*** People
- `GET /api/people` - List all people
- `GET /api/people/residents` - List residents
- `GET /api/people/faculty` - List faculty
- `POST /api/people` - Create person
- `PUT /api/people/{id}` - Update person
- `DELETE /api/people/{id}` - Delete person

***REMOVED******REMOVED******REMOVED*** Rotation Templates
- `GET /api/rotation-templates` - List templates
- `POST /api/rotation-templates` - Create template
- `PUT /api/rotation-templates/{id}` - Update template
- `DELETE /api/rotation-templates/{id}` - Delete template

***REMOVED******REMOVED******REMOVED*** Schedule
- `GET /api/schedule/{start_date}/{end_date}` - Get schedule
- `POST /api/schedule/generate` - Generate schedule
- `GET /api/schedule/validate` - Validate ACGME compliance
- `POST /api/schedule/emergency-coverage` - Handle emergency absence

***REMOVED******REMOVED******REMOVED*** Absences
- `GET /api/absences` - List absences
- `POST /api/absences` - Create absence
- `PUT /api/absences/{id}` - Update absence
- `DELETE /api/absences/{id}` - Delete absence

***REMOVED******REMOVED*** ACGME Compliance

The scheduler validates against ACGME requirements:

- **80-Hour Rule**: Maximum 80 hours/week averaged over 4 weeks
- **1-in-7 Rule**: One 24-hour period off every 7 days
- **Supervision Ratios**:
  - PGY-1: 1 faculty per 2 residents
  - PGY-2/3: 1 faculty per 4 residents

***REMOVED******REMOVED*** Database Schema

- `people`: Residents and faculty members
- `blocks`: Half-day scheduling blocks (730/year: 365 days × AM/PM)
- `rotation_templates`: Reusable activity patterns with constraints
- `assignments`: The actual schedule
- `absences`: Leave, deployments, TDY
- `call_assignments`: Overnight and weekend call
- `schedule_runs`: Audit trail for generated schedules

***REMOVED******REMOVED*** Development Timeline

- **Week 1**: Backend foundation (done)
- **Week 2**: Frontend foundation (done)
- **Week 3**: Advanced features
- **Weeks 4-8**: Security, testing, deployment
- **Weeks 9-13**: Polish, documentation, production

***REMOVED******REMOVED*** License

MIT
