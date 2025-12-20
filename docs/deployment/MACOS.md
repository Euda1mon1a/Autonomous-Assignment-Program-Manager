***REMOVED*** MACOS.md - macOS Deployment Reference for Claude

> **Purpose:** Quick reference for deploying this repository on macOS via Terminal
> **Last Updated:** 2025-12-18

---

***REMOVED******REMOVED*** Prerequisites Check

Run these commands first to verify prerequisites:

```bash
***REMOVED*** Check if Homebrew is installed
brew --version || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

***REMOVED*** Check Docker
docker --version || brew install --cask docker

***REMOVED*** Check Git
git --version || brew install git
```

**Important:** Docker Desktop must be running before proceeding.

```bash
***REMOVED*** Start Docker Desktop
open -a Docker

***REMOVED*** Wait for Docker to be ready (run until no error)
docker info
```

---

***REMOVED******REMOVED*** Quick Deploy (Docker - Recommended)

```bash
***REMOVED*** 1. Navigate to project root
cd ~/Autonomous-Assignment-Program-Manager  ***REMOVED*** Or wherever the repo is cloned

***REMOVED*** 2. Copy environment file
cp .env.example .env

***REMOVED*** 3. Generate and set secrets
SECRET_KEY=$(openssl rand -hex 32)
WEBHOOK_SECRET=$(openssl rand -hex 16)
echo "Add these to .env:"
echo "SECRET_KEY=$SECRET_KEY"
echo "WEBHOOK_SECRET=$WEBHOOK_SECRET"

***REMOVED*** 4. Edit .env with required values
***REMOVED*** Required: DB_PASSWORD, SECRET_KEY, WEBHOOK_SECRET, NEXT_PUBLIC_API_URL=http://localhost:8000

***REMOVED*** 5. Start all services
docker-compose up -d

***REMOVED*** 6. Verify deployment
docker-compose ps
curl http://localhost:8000/health
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

***REMOVED******REMOVED*** Local Development Setup

***REMOVED******REMOVED******REMOVED*** Install Dependencies

```bash
brew install python@3.11 node@18 postgresql@15 redis k6
brew services start postgresql@15
brew services start redis
```

***REMOVED******REMOVED******REMOVED*** Backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
createdb residency_scheduler  ***REMOVED*** May need: brew services start postgresql@15
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

***REMOVED******REMOVED******REMOVED*** Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

***REMOVED******REMOVED******REMOVED*** Celery (new terminal, optional)

```bash
cd backend
source venv/bin/activate
../scripts/start-celery.sh both
```

---

***REMOVED******REMOVED*** Essential Commands

***REMOVED******REMOVED******REMOVED*** Docker

```bash
docker-compose up -d          ***REMOVED*** Start all services
docker-compose down           ***REMOVED*** Stop all services
docker-compose logs -f        ***REMOVED*** View all logs
docker-compose logs -f backend  ***REMOVED*** View backend logs
docker-compose restart backend  ***REMOVED*** Restart a service
docker-compose up -d --build  ***REMOVED*** Rebuild and start
docker-compose exec backend bash  ***REMOVED*** Shell into container
docker-compose exec db psql -U scheduler -d residency_scheduler  ***REMOVED*** Database shell
```

***REMOVED******REMOVED******REMOVED*** Testing

```bash
***REMOVED*** Backend
cd backend && source venv/bin/activate && pytest

***REMOVED*** Frontend
cd frontend && npm test

***REMOVED*** Load testing
cd load-tests && npm run test:smoke
```

***REMOVED******REMOVED******REMOVED*** Database

```bash
***REMOVED*** Migrations
cd backend && source venv/bin/activate
alembic upgrade head          ***REMOVED*** Apply migrations
alembic downgrade -1          ***REMOVED*** Rollback one
alembic revision --autogenerate -m "description"  ***REMOVED*** Create migration
```

***REMOVED******REMOVED******REMOVED*** Homebrew Services

```bash
brew services list            ***REMOVED*** Show all services
brew services start postgresql@15
brew services start redis
brew services stop postgresql@15
brew services stop redis
```

---

***REMOVED******REMOVED*** Common Issues & Fixes

***REMOVED******REMOVED******REMOVED*** Docker not running
```bash
open -a Docker && sleep 10 && docker info
```

***REMOVED******REMOVED******REMOVED*** Port in use
```bash
lsof -i :8000  ***REMOVED*** Find process
kill -9 <PID>  ***REMOVED*** Kill it
```

***REMOVED******REMOVED******REMOVED*** PostgreSQL connection refused
```bash
brew services restart postgresql@15
psql -h localhost -U postgres -l  ***REMOVED*** Test connection
```

***REMOVED******REMOVED******REMOVED*** Redis connection refused
```bash
brew services restart redis
redis-cli ping  ***REMOVED*** Should return PONG
```

***REMOVED******REMOVED******REMOVED*** Python version issues
```bash
python3.11 -m venv venv
source venv/bin/activate
which python  ***REMOVED*** Should show venv path
```

***REMOVED******REMOVED******REMOVED*** Permission denied
```bash
sudo chown -R $(whoami) ~/Autonomous-Assignment-Program-Manager
```

***REMOVED******REMOVED******REMOVED*** Docker memory issues
Open Docker Desktop → Settings → Resources → Set Memory to 4GB+

---

***REMOVED******REMOVED*** Environment Variables (.env)

**Required:**
```env
DB_PASSWORD=your_secure_password
SECRET_KEY=<64-char-from-openssl-rand-hex-32>
WEBHOOK_SECRET=<32-char-from-openssl-rand-hex-16>
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Optional:**
```env
DEBUG=false
CORS_ORIGINS=["http://localhost:3000"]
REDIS_URL=redis://localhost:6379/0
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

***REMOVED******REMOVED*** First-Time Setup After Deploy

```bash
***REMOVED*** Create admin user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "YourSecurePassword123!",
    "full_name": "Admin User",
    "role": "admin"
  }'
```

Then open http://localhost:3000 and log in.

---

***REMOVED******REMOVED*** Contributing Discoveries Back

**IMPORTANT:** If you encounter and solve a new issue, or discover something useful during deployment, commit it back to the repo so future sessions benefit.

***REMOVED******REMOVED******REMOVED*** When to Contribute

- Fixed an undocumented issue
- Found a better command or approach
- Encountered a new macOS-specific gotcha
- Updated a dependency version that matters

***REMOVED******REMOVED******REMOVED*** How to Contribute

```bash
***REMOVED*** 1. Create a branch (if not already on one)
git checkout -b fix/macos-<brief-description>

***REMOVED*** 2. Update the relevant file:
***REMOVED***    - New issue/fix → Add to "Common Issues & Fixes" section in this file
***REMOVED***    - New command → Add to "Essential Commands" section
***REMOVED***    - Major discovery → Update docs/getting-started/macos-deploy.md

***REMOVED*** 3. Commit with clear message
git add -A
git commit -m "docs(macos): Add fix for <issue description>"

***REMOVED*** 4. Push to remote
git push -u origin fix/macos-<brief-description>

***REMOVED*** 5. Tell the user the branch name so they can create a PR
```

***REMOVED******REMOVED******REMOVED*** What to Document

For each discovery, include:
1. **Symptom** - What error/problem did you see?
2. **Cause** - Why did it happen? (if known)
3. **Fix** - The command(s) that solved it

Example format for this file:
```markdown
***REMOVED******REMOVED******REMOVED*** <Issue name>
```bash
<fix command>
```
```

---

***REMOVED******REMOVED*** Full Documentation

For detailed instructions, see:
- [Full macOS Deploy Guide](docs/getting-started/macos-deploy.md)
- [Project Guidelines](CLAUDE.md)
- [Troubleshooting](wiki/Troubleshooting.md)
