# Load Testing Configuration - Implementation Checklist

## Pre-Deployment Steps

### 1. Generate and Configure Secret Key
- [ ] Generate secure key: `python -c 'import secrets; print(secrets.token_urlsafe(32))'`
- [ ] Edit `nginx/conf.d/load-testing.conf` (line 30)
- [ ] Replace `YOUR_LOAD_TEST_SECRET_KEY` with generated key
- [ ] Store key securely in environment variables or secret manager

### 2. Configure IP Whitelist
- [ ] Review default whitelist in `nginx/conf.d/load-testing.conf` (lines 33-51)
- [ ] Add CI/CD server IPs if needed
- [ ] Document which IPs are whitelisted and why

### 3. Enable Load Test Endpoints
- [ ] Edit `nginx/conf.d/default.conf`
- [ ] Add `include /etc/nginx/snippets/loadtest-locations.conf;` inside server block (around line 50)
- [ ] Verify placement (after logging config, before location blocks)

### 4. Test Configuration
- [ ] Run syntax check: `docker compose exec nginx nginx -t`
- [ ] Verify no errors in output
- [ ] Check for warnings that need addressing

### 5. Deploy and Reload
- [ ] Reload nginx: `docker compose exec nginx nginx -s reload`
- [ ] Monitor error logs: `docker compose logs -f nginx`
- [ ] Verify no startup errors

## Testing Steps

### 6. Basic Connectivity Test
- [ ] Test from whitelisted IP: `curl -H "X-Load-Test-Key: YOUR_KEY" http://localhost/api/loadtest/persons`
- [ ] Verify 200 OK response (or appropriate status if endpoint doesn't exist yet)
- [ ] Verify `X-Load-Test-Mode: active` header in response

### 7. Security Validation
- [ ] Test without key (should fail): `curl http://localhost/api/loadtest/persons`
- [ ] Expected: 403 Forbidden with error message
- [ ] Test with wrong key (should fail): `curl -H "X-Load-Test-Key: WRONG" http://localhost/api/loadtest/persons`
- [ ] Expected: 403 Forbidden with error message

### 8. Rate Limit Testing
- [ ] Test normal endpoint rate limit: `ab -n 100 -c 10 http://localhost/api/persons`
- [ ] Verify rate limiting kicks in (429 responses)
- [ ] Test load test endpoint: `ab -n 100 -c 10 -H "X-Load-Test-Key: YOUR_KEY" http://localhost/api/loadtest/persons`
- [ ] Verify higher throughput allowed

### 9. Monitoring Setup
- [ ] Verify nginx status accessible: `curl http://localhost/nginx_status`
- [ ] Check load test log file created: `ls -lh /var/log/nginx/loadtest.log`
- [ ] Verify JSON format: `tail -1 /var/log/nginx/loadtest.log | jq .`

### 10. Load Testing Tool Integration
- [ ] Install K6 or Locust
- [ ] Run sample load test (see LOAD_TESTING_SETUP.md)
- [ ] Monitor metrics during test
- [ ] Review logs for errors or warnings

## Post-Deployment Steps

### 11. Documentation
- [ ] Document the load test secret key location (NOT the key itself)
- [ ] Document whitelisted IPs and their purpose
- [ ] Share LOAD_TESTING_SETUP.md with QA/performance testing team
- [ ] Update runbook with load testing procedures

### 12. Security Hardening
- [ ] Verify load test key is NOT in version control
- [ ] Confirm firewall rules block external access to /api/loadtest/*
- [ ] Set up monitoring alerts for unauthorized load test attempts
- [ ] Schedule key rotation (recommended: quarterly)

### 13. Operational Setup
- [ ] Configure log rotation for loadtest.log
- [ ] Set up alerts for high error rates during load tests
- [ ] Document how to disable load testing when not in use
- [ ] Create runbook for troubleshooting common issues

## Cleanup After Load Testing (Optional)

### 14. Disable Load Test Endpoints
- [ ] Comment out include line in default.conf
- [ ] Reload nginx
- [ ] Verify load test endpoints return 404

### 15. Archive Logs
- [ ] Move loadtest.log to archive directory
- [ ] Compress old logs
- [ ] Clear active log file

## Files Created

1. **nginx/conf.d/load-testing.conf** (317 lines)
   - HTTP-level configuration (map, geo, rate limits, upstream)
   - Detailed comments and usage examples
   - Security controls and IP whitelisting

2. **nginx/snippets/loadtest-locations.conf** (114 lines)
   - Location blocks for load test endpoints
   - Ready to include in server block
   - Configured timeouts and buffers

3. **nginx/LOAD_TESTING_SETUP.md** (578 lines)
   - Comprehensive setup guide
   - Usage examples (curl, K6, Locust, Apache Bench)
   - Monitoring and troubleshooting
   - Security best practices

4. **nginx/README.md** (updated)
   - Added load testing section
   - Updated directory structure
   - Updated file ownership matrix

5. **nginx/LOAD_TESTING_CHECKLIST.md** (this file)
   - Step-by-step implementation guide
   - Testing procedures
   - Validation steps

## Support

If you encounter issues:

1. **Check nginx logs**: `docker compose logs -f nginx`
2. **Validate config**: `docker compose exec nginx nginx -t`
3. **Review setup guide**: `nginx/LOAD_TESTING_SETUP.md`
4. **Check security**: Verify IP whitelist and secret key

## Quick Reference

**Generated files:**
```
nginx/
├── conf.d/
│   └── load-testing.conf          (HTTP-level config)
├── snippets/
│   └── loadtest-locations.conf    (Location blocks)
├── LOAD_TESTING_SETUP.md          (Full guide)
└── LOAD_TESTING_CHECKLIST.md      (This file)
```

**Key configuration points:**
- Secret key: `nginx/conf.d/load-testing.conf:30`
- IP whitelist: `nginx/conf.d/load-testing.conf:33-51`
- Include location: Add to `nginx/conf.d/default.conf` server block

**Test commands:**
```bash
# Generate key
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Test config
docker compose exec nginx nginx -t

# Reload
docker compose exec nginx nginx -s reload

# Test endpoint
curl -H "X-Load-Test-Key: YOUR_KEY" http://localhost/api/loadtest/persons
```

---

**Status Tracking:**

Date: _______________
Completed by: _______________
Verified by: _______________
Issues encountered: _______________
