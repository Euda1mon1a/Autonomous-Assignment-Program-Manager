---
description: Deploy locally and validate the scheduling system
---

# Local Deployment & Testing Workflow

This workflow helps you deploy the residency scheduling system locally and validate it's working correctly.

---

## 🚀 Quick Start (Full Stack)

### 1. Pull latest changes
// turbo
```bash
git pull
```

> **Note:** This pulls the current branch. Use `git checkout main && git pull` if you need to switch to main first.

### 2. Start all services with Docker
```bash
docker compose -f docker-compose.local.yml up --build -d
```

> **Note:** The `-d` flag runs in detached mode (background). Omit it to see logs in foreground (requires a second terminal for other commands).

> **Wait for:** All services to show "healthy" status (usually 1-2 minutes)

### 3. Verify services are running
// turbo
```bash
docker compose -f docker-compose.local.yml ps
```

---

## 🌐 Access Points

Once running, open these in your browser:

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main UI - schedules, calendar, dashboards |
| **API Docs** | http://localhost:8000/docs | Swagger UI - test API endpoints directly |
| **Health Check** | http://localhost:8000/health | Quick status check |
| **n8n Workflows** | http://localhost:5679 | Automation workflows (default: admin / local_dev_n8n_password — change in `docker-compose.local.yml`) |

---

## ✅ Validation Checklist

### Basic Health Check
// turbo
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

### Check Logs for Errors
// turbo
```bash
docker compose -f docker-compose.local.yml logs --tail=20 backend
```

### Manual Validation Steps
1. [ ] Frontend loads at http://localhost:3000
2. [ ] Can log in (if auth is enabled)
3. [ ] Schedule calendar displays correctly
4. [ ] Can view/edit assignments
5. [ ] No console errors in browser DevTools (F12)

---

## 🔧 Common Operations

### View live logs (all services)
// turbo
```bash
docker compose -f docker-compose.local.yml logs -f
```

### View logs for specific service
// turbo
```bash
docker compose -f docker-compose.local.yml logs -f backend
```

### Restart a single service
```bash
docker compose -f docker-compose.local.yml restart backend
```

### Stop everything
```bash
docker compose -f docker-compose.local.yml down
```

### Nuclear reset (rebuild from scratch)

> ⚠️ **WARNING:** This deletes all local data (database, volumes). Only use if you need a completely fresh start.

```bash
docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up --build -d
```

---

## 🐛 Troubleshooting

### "Port already in use"
```bash
# Find what's using the port (e.g., 3000)
lsof -i :3000

# Gracefully stop the process first
kill <PID>

# If it doesn't stop, force kill (may cause data loss)
kill -9 <PID>
```

### Database connection errors
// turbo
```bash
docker compose -f docker-compose.local.yml logs db
```

### Backend won't start
// turbo
```bash
docker compose -f docker-compose.local.yml logs backend --tail=50
```

### Frontend blank/errors
// turbo
```bash
docker compose -f docker-compose.local.yml logs frontend --tail=50
```

---

## 🧪 Running Tests

### Backend tests (in container)
```bash
docker compose -f docker-compose.local.yml exec backend pytest -v
```

### Frontend tests (in container)
```bash
docker compose -f docker-compose.local.yml exec frontend npm test
```

---

## 💡 Tips for Physicians

- **Think of Docker as a hospital simulator** — it creates an isolated environment where all your "departments" (services) can communicate
- **Logs are your chart review** — always check logs when something seems off
- **The `/docs` endpoint is your best friend** — you can test any API call without writing code
- **When in doubt, restart** — `docker compose restart` fixes many transient issues
