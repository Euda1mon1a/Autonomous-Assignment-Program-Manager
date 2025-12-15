# File Ownership Matrix - .docker/

This document defines ownership and responsibilities for all files in the `.docker/` directory.

## Territory Boundaries

**Territory**: `.docker/*`
**Primary Responsibility**: DevOps / Infrastructure
**DO NOT overlap with**: `.github/workflows/*`, `monitoring/*`, `nginx/*` (root level)

## File Ownership Matrix

| File | Owner | Purpose | Dependencies |
|------|-------|---------|--------------|
| `backend.Dockerfile` | DevOps | Multi-stage production build for FastAPI backend | `backend/requirements.txt` |
| `frontend.Dockerfile` | DevOps | Multi-stage production build with nginx | `frontend/package.json`, `nginx/*.conf` |
| `docker-compose.prod.yml` | DevOps | Production orchestration with health checks | Both Dockerfiles, `.env.prod.example` |
| `.env.prod.example` | DevOps | Environment template for production | None |
| `README.md` | DevOps | Documentation for production deployment | None |
| `OWNERSHIP.md` | DevOps | This file - ownership documentation | None |
| `nginx/nginx.conf` | DevOps | Main nginx configuration with security | None |
| `nginx/default.conf` | DevOps | Server block with API proxy | Backend service |

## Dependency Graph

```
docker-compose.prod.yml
├── backend.Dockerfile
│   └── backend/
│       ├── requirements.txt
│       ├── app/
│       └── alembic/
├── frontend.Dockerfile
│   └── frontend/
│       ├── package.json
│       └── src/
├── nginx/nginx.conf
├── nginx/default.conf
└── .env.prod.example
```

## Modification Guidelines

### backend.Dockerfile
- Changes to Python dependencies require rebuild
- Security patches should be applied regularly
- Multi-stage build must strip dev dependencies

### frontend.Dockerfile
- Changes to Node version require testing
- Build-time environment variables for API URL
- nginx configs are copied at build time

### docker-compose.prod.yml
- Resource limits should be adjusted based on monitoring
- Health check intervals may need tuning
- Secrets management via Docker secrets

### nginx/*.conf
- Security headers must remain intact
- Rate limiting zones should match traffic patterns
- Upstream configuration tied to service names

## Security Checklist

- [ ] Non-root users in all containers
- [ ] Read-only root filesystems
- [ ] No secrets in environment variables
- [ ] Resource limits defined
- [ ] Health checks implemented
- [ ] Network segmentation (internal backend)
- [ ] Rate limiting on API endpoints
- [ ] Security headers in nginx

## Review Requirements

| Change Type | Required Review |
|-------------|-----------------|
| Dockerfile base image update | Security Team |
| Resource limit changes | DevOps Lead |
| nginx security config | Security Team |
| New environment variables | Backend Team |
| Network topology changes | DevOps Lead + Security |

## Version History

| Date | Author | Change |
|------|--------|--------|
| 2024-12-15 | DevOps | Initial production Docker configuration |
