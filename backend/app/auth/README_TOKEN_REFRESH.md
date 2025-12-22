# Token Refresh Service

## Overview

The token refresh service provides secure refresh token management with advanced security features including:

- **Token Rotation**: New refresh token issued on every use
- **Reuse Detection**: Detects and prevents token replay attacks
- **Device Binding**: Tokens bound to device fingerprints
- **Token Families**: Tracks token lineage for security
- **Concurrent Session Limits**: Enforces max tokens per user
- **Comprehensive Metrics**: Prometheus-compatible metrics

## Architecture

### Token Family Concept

Refresh tokens are organized into "families" for security:

```
Initial Token (Family: abc-123)
    └── Refresh → Token 2 (Family: abc-123, Parent: Token 1)
        └── Refresh → Token 3 (Family: abc-123, Parent: Token 2)
```

If Token 1 is reused after Token 2 is created, the **entire family is revoked**.

### Security Model

1. **Token Rotation**: Every refresh generates a new token and marks the old one as USED
2. **Reuse Detection**: If a USED token is presented, it triggers family revocation
3. **Device Binding**: Tokens are bound to device fingerprints (IP + User Agent hash)
4. **Expiration**: Time-based expiration with sliding window support
5. **Concurrent Limits**: Max tokens per user enforced automatically

## Usage

### Creating a Refresh Token

```python
from app.auth.token_refresh import (
    RefreshTokenService,
    RefreshTokenCreate,
    DeviceFingerprint,
    get_refresh_token_service,
)

# Get service instance
service = get_refresh_token_service(db)

# Create device fingerprint from request
device_fp = DeviceFingerprint(
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
)

# Create token
request_data = RefreshTokenCreate(
    user_id=user.id,
    username=user.username,
    expires_in_days=30,
)

token_data, token_string = await service.create_refresh_token(
    request_data,
    device_fingerprint=device_fp,
)

# Return token_string to client
return {"refresh_token": token_string}
```

### Validating and Rotating a Token

```python
# Validate and rotate token
device_fp = DeviceFingerprint(
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
)

new_token_data, new_token_string, status = await service.validate_and_rotate_token(
    refresh_token_from_client,
    device_fingerprint=device_fp,
)

if new_token_string:
    # Token was rotated - return new token
    return {
        "access_token": create_access_token(new_token_data),
        "refresh_token": new_token_string,
    }
elif new_token_data:
    # Token is valid but not rotated
    return {"access_token": create_access_token(new_token_data)}
else:
    # Token is invalid
    raise HTTPException(401, detail=status)
```

### Revoking Tokens

```python
# Revoke specific token
await service.revoke_token(token_id, reason="manual_revoke")

# Revoke all user tokens
await service.revoke_user_tokens(user_id)

# Revoke all user tokens except current (logout other devices)
await service.revoke_user_tokens(user_id, except_token_id=current_token_id)

# Revoke token family (reuse detected)
await service.revoke_token_family(family_id, reason="reuse_detected")
```

### Getting Metrics

```python
metrics = service.get_metrics()
print(f"Active tokens: {metrics.total_active_tokens}")
print(f"Created today: {metrics.tokens_created_24h}")
print(f"Refreshed today: {metrics.tokens_refreshed_24h}")
print(f"Reuse attempts: {metrics.reuse_attempts_detected_24h}")
```

## Configuration

Configure the service via constructor:

```python
service = RefreshTokenService(
    db=db,
    max_tokens_per_user=5,              # Max concurrent tokens
    default_expiry_days=30,             # Default token lifetime
    rotation_strategy=TokenRotationStrategy.ALWAYS,  # Rotation strategy
    rotation_threshold=0.5,             # For THRESHOLD strategy
    enable_device_binding=True,         # Enable device fingerprinting
    enable_reuse_detection=True,        # Enable reuse detection
)
```

### Rotation Strategies

- **ALWAYS**: Always issue new token on refresh (most secure, default)
- **THRESHOLD**: Issue new token if >X% of lifetime used (configurable)
- **NEVER**: Reuse same token (least secure, not recommended)

## Security Considerations

### Token Reuse Attack

If an attacker steals a refresh token and uses it after the legitimate user has already refreshed:

1. The old token is marked as USED
2. When the attacker tries to use it, reuse is detected
3. The entire token family is revoked
4. Both attacker and legitimate user must re-authenticate

### Device Binding

Tokens are bound to device fingerprints to prevent cross-device usage:

- IP address changes trigger validation failure
- User agent changes trigger validation failure
- Optional device_id can be provided by client

**Note**: This may cause issues with:
- VPN/proxy changes
- Mobile networks (changing IPs)
- Browser updates (changing user agents)

Adjust `enable_device_binding` based on your security requirements.

### Storage Backend

**Current Implementation**: In-memory dictionary (development only)

**Production**: Replace with Redis:

```python
# In production, implement Redis storage
class RedisRefreshTokenStorage:
    async def store(self, token_string: str, token_data: RefreshTokenData, ttl: int):
        # Store in Redis with TTL
        pass

    async def get(self, token_string: str) -> RefreshTokenData | None:
        # Retrieve from Redis
        pass
```

## Integration with Access Tokens

Typical OAuth 2.0 flow:

1. **Login**: Issue both access token (short-lived, 1hr) and refresh token (long-lived, 30 days)
2. **Access Protected Resource**: Use access token
3. **Access Token Expires**: Use refresh token to get new access token
4. **Refresh Token Rotates**: Receive new access + refresh tokens
5. **Logout**: Revoke refresh token

## Monitoring

The service integrates with the observability metrics:

- `auth_tokens_issued_total{token_type="refresh"}` - Refresh tokens created
- `auth_tokens_blacklisted_total{reason="*"}` - Tokens revoked by reason
- `auth_verification_failures_total{reason="refresh_token_reuse"}` - Reuse attempts
- `auth_verification_failures_total{reason="device_mismatch"}` - Device binding failures

## Testing

Run tests with:

```bash
cd backend
pytest tests/auth/test_token_refresh.py -v
```

Test coverage includes:
- Token creation and storage
- Token validation and rotation
- Reuse detection and family revocation
- Device binding enforcement
- Concurrent session limits
- Metrics collection
- All rotation strategies

## Production Deployment

Before deploying to production:

1. **Replace in-memory storage with Redis**:
   - Implement `RedisRefreshTokenStorage` backend
   - Use Redis TTL for automatic expiration
   - Enable Redis persistence for durability

2. **Configure secure defaults**:
   ```python
   max_tokens_per_user=3  # Limit concurrent sessions
   default_expiry_days=30  # Balance security vs UX
   rotation_strategy=TokenRotationStrategy.ALWAYS  # Maximum security
   enable_device_binding=True  # Prevent token theft
   enable_reuse_detection=True  # Detect attacks
   ```

3. **Set up monitoring**:
   - Alert on high `reuse_attempts_detected_24h`
   - Alert on high `device_mismatch_attempts_24h`
   - Monitor `average_token_age_hours` for anomalies

4. **Periodic cleanup**:
   ```python
   # Run as Celery task every hour
   @celery_app.task
   def cleanup_expired_refresh_tokens():
       service = get_refresh_token_service()
       cleaned = await service.cleanup_expired_tokens()
       logger.info(f"Cleaned up {cleaned} expired refresh tokens")
   ```

## References

- [RFC 6819: OAuth 2.0 Threat Model and Security Considerations](https://tools.ietf.org/html/rfc6819)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OAuth 2.0 Security Best Current Practice](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
