***REMOVED*** Nginx Directory - File Ownership Matrix

This document defines ownership and responsibility for all files in the `nginx/` directory.

***REMOVED******REMOVED*** Ownership Definitions

| Role | Responsibilities |
|------|------------------|
| **DevOps** | Infrastructure, deployment, scaling, monitoring |
| **Security** | Security headers, TLS configuration, rate limiting |
| **Backend** | API routing, upstream configuration changes |
| **Frontend** | Static file serving, cache rules for frontend assets |

***REMOVED******REMOVED*** File Ownership

***REMOVED******REMOVED******REMOVED*** Core Configuration

| File | Primary Owner | Secondary Owner | Change Frequency | Review Required |
|------|---------------|-----------------|------------------|-----------------|
| `nginx.conf` | DevOps | Security | Low | Yes |
| `Dockerfile` | DevOps | - | Low | Yes |
| `docker-compose.nginx.yml` | DevOps | - | Low | Yes |
| `README.md` | DevOps | All | Medium | No |

***REMOVED******REMOVED******REMOVED*** Server Configuration (`conf.d/`)

| File | Primary Owner | Secondary Owner | Change Frequency | Review Required |
|------|---------------|-----------------|------------------|-----------------|
| `upstreams.conf` | DevOps | Backend | Medium | Yes |
| `default.conf` | DevOps | Security | Medium | Yes |
| `default-dev.conf.example` | DevOps | - | Low | No |

***REMOVED******REMOVED******REMOVED*** Configuration Snippets (`snippets/`)

| File | Primary Owner | Secondary Owner | Change Frequency | Review Required |
|------|---------------|-----------------|------------------|-----------------|
| `ssl-params.conf` | Security | DevOps | Low | Yes |
| `security-headers.conf` | Security | DevOps | Medium | Yes |
| `proxy-params.conf` | DevOps | Backend | Low | No |
| `websocket-params.conf` | DevOps | Backend | Low | No |
| `static-cache.conf` | DevOps | Frontend | Low | No |

***REMOVED******REMOVED******REMOVED*** Scripts (`scripts/`)

| File | Primary Owner | Secondary Owner | Change Frequency | Review Required |
|------|---------------|-----------------|------------------|-----------------|
| `init-letsencrypt.sh` | DevOps | Security | Low | Yes |
| `renew-certificates.sh` | DevOps | - | Low | No |
| `generate-dhparam.sh` | DevOps | Security | Low | No |

***REMOVED******REMOVED******REMOVED*** SSL Directory (`ssl/`)

| File | Primary Owner | Secondary Owner | Change Frequency | Review Required |
|------|---------------|-----------------|------------------|-----------------|
| `.gitkeep` | DevOps | - | Never | No |
| `dhparam.pem` (generated) | DevOps | Security | Yearly | No |

***REMOVED******REMOVED*** Change Procedures

***REMOVED******REMOVED******REMOVED*** High-Risk Changes (Review Required)

1. **TLS/SSL Configuration** (`ssl-params.conf`)
   - Requires Security team review
   - Test with SSL Labs before deployment
   - Document cipher suite changes

2. **Security Headers** (`security-headers.conf`)
   - Requires Security team review
   - Test CSP changes in staging
   - Verify no functionality breakage

3. **Rate Limiting** (in `default.conf`)
   - Document business justification
   - Monitor after deployment
   - Have rollback plan ready

4. **Upstream Changes** (`upstreams.conf`)
   - Coordinate with Backend team
   - Test load balancing behavior
   - Verify health check functionality

***REMOVED******REMOVED******REMOVED*** Standard Changes (No Review Required)

1. **Documentation updates**
2. **Development configuration changes**
3. **Log format adjustments**
4. **Cache TTL modifications**

***REMOVED******REMOVED*** Approval Matrix

| Change Type | Approvers | SLA |
|-------------|-----------|-----|
| Security-critical | Security Lead + DevOps Lead | 24 hours |
| Infrastructure | DevOps Lead | 4 hours |
| Routing changes | DevOps + Backend Lead | 4 hours |
| Documentation | Any team member | Immediate |

***REMOVED******REMOVED*** Monitoring Responsibilities

| Metric | Owner | Alert Threshold |
|--------|-------|-----------------|
| SSL certificate expiry | DevOps | 30 days before expiry |
| Rate limit hits | Security | >1000/hour |
| 5xx error rate | DevOps | >1% |
| Upstream failures | DevOps | Any |
| Request latency (p99) | DevOps | >2 seconds |

***REMOVED******REMOVED*** Emergency Contacts

For production nginx issues:
1. Primary: DevOps On-Call
2. Secondary: Backend On-Call
3. Security issues: Security Team Lead

***REMOVED******REMOVED*** Version History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-12-15 | 1.0.0 | Initial nginx configuration | DevOps |
