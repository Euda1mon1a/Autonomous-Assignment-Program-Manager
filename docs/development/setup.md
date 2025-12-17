***REMOVED*** Development Setup

Set up your development environment.

---

***REMOVED******REMOVED*** Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git
- PostgreSQL 15 (for local dev)
- Redis 7 (for local dev)

---

***REMOVED******REMOVED*** Backend Setup

```bash
cd backend

***REMOVED*** Create virtual environment
python -m venv venv
source venv/bin/activate  ***REMOVED*** Windows: venv\Scripts\activate

***REMOVED*** Install dependencies
pip install -r requirements.txt

***REMOVED*** Set up database
createdb residency_scheduler

***REMOVED*** Run migrations
alembic upgrade head

***REMOVED*** Start development server
uvicorn app.main:app --reload
```

---

***REMOVED******REMOVED*** Frontend Setup

```bash
cd frontend

***REMOVED*** Install dependencies
npm install

***REMOVED*** Start development server
npm run dev
```

---

***REMOVED******REMOVED*** Docker Development

For full-stack development with Docker:

```bash
***REMOVED*** Start all services with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

***REMOVED*** View logs
docker-compose logs -f backend
```

---

***REMOVED******REMOVED*** IDE Setup

***REMOVED******REMOVED******REMOVED*** VS Code

Recommended extensions:
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense

***REMOVED******REMOVED******REMOVED*** PyCharm

Configure:
- Python interpreter (venv)
- Django/FastAPI support
- Database tools
