# OAuth2 PKCE Implementation

This module implements the OAuth2 Authorization Code Flow with PKCE (Proof Key for Code Exchange) extension as defined in [RFC 7636](https://tools.ietf.org/html/rfc7636).

## Overview

PKCE enhances the OAuth2 authorization code flow to make it secure for public clients (mobile apps, SPAs) that cannot securely store client secrets. It prevents authorization code interception attacks by introducing a code challenge/verifier mechanism.

## Architecture

### Components

1. **Models** (`models/oauth2_*.py`)
   - `PKCEClient`: OAuth2 public client registration
   - `OAuth2AuthorizationCode`: Short-lived authorization codes with PKCE challenges

2. **Schemas** (`schemas/oauth2.py`)
   - Request/response validation for OAuth2 endpoints
   - Type-safe data structures for PKCE parameters

3. **Service Layer** (`auth/oauth2_pkce.py`)
   - Core PKCE logic and token management
   - Code verifier/challenge generation and validation
   - State parameter handling for CSRF protection

4. **API Routes** (`api/routes/oauth2.py`)
   - `/oauth2/authorize` - Authorization endpoint
   - `/oauth2/token` - Token exchange endpoint
   - `/oauth2/introspect` - Token introspection (RFC 7662)
   - `/oauth2/revoke` - Token revocation
   - `/oauth2/clients` - Client registration (admin only)

## PKCE Flow

### 1. Client Registration (Admin Only)

```http
POST /api/oauth2/clients
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "client_name": "Mobile App",
  "redirect_uris": ["app://callback"],
  "client_uri": "https://myapp.com",
  "scope": "read write"
}
```

Response:
```json
{
  "id": "uuid",
  "client_id": "generated_client_id",
  "client_name": "Mobile App",
  "redirect_uris": ["app://callback"],
  "is_public": true,
  "is_active": true
}
```

### 2. Authorization Request

Client generates code verifier and challenge:

```python
import secrets
import hashlib
import base64

# Generate code verifier (43-128 chars)
code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

# Compute code challenge (SHA256)
digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
code_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
```

Request authorization:

```http
POST /api/oauth2/authorize
Authorization: Bearer <user_session_token>
Content-Type: application/json

{
  "response_type": "code",
  "client_id": "generated_client_id",
  "redirect_uri": "app://callback",
  "scope": "read",
  "state": "random_state_value",
  "code_challenge": "computed_challenge",
  "code_challenge_method": "S256"
}
```

Response:
```json
{
  "code": "authorization_code",
  "state": "random_state_value"
}
```

### 3. Token Exchange

Exchange authorization code for access token:

```http
POST /api/oauth2/token
Content-Type: application/json

{
  "grant_type": "authorization_code",
  "code": "authorization_code",
  "redirect_uri": "app://callback",
  "client_id": "generated_client_id",
  "code_verifier": "original_code_verifier"
}
```

Response:
```json
{
  "access_token": "jwt_access_token",
  "token_type": "Bearer",
  "expires_in": 86400,
  "scope": "read"
}
```

### 4. Token Usage

Use the access token to make authenticated requests:

```http
GET /api/schedule
Authorization: Bearer <access_token>
```

### 5. Token Introspection

Check token validity:

```http
POST /api/oauth2/introspect
Content-Type: application/json

{
  "token": "access_token"
}
```

Response:
```json
{
  "active": true,
  "scope": "read",
  "client_id": "generated_client_id",
  "username": "user",
  "token_type": "Bearer",
  "exp": 1234567890,
  "iat": 1234567890,
  "sub": "user_id"
}
```

### 6. Token Revocation

Revoke a token (requires authentication):

```http
POST /api/oauth2/revoke
Authorization: Bearer <user_session_token>
Content-Type: application/json

{
  "token": "access_token_to_revoke"
}
```

## Security Features

### PKCE Protection

- **Code Challenge**: SHA256 hash of random code verifier
- **Code Verifier Validation**: Server verifies verifier matches stored challenge
- **Prevents Interception**: Attacker cannot exchange stolen code without verifier

### Additional Security Layers

1. **State Parameter**: CSRF protection for authorization requests
2. **Redirect URI Validation**: Whitelist of allowed redirect URIs per client
3. **Single-Use Codes**: Authorization codes are invalidated after first use
4. **Time-Limited Codes**: Codes expire after 10 minutes
5. **Token Blacklisting**: Revoked tokens are blacklisted (via existing infrastructure)

### Code Challenge Methods

- **S256** (recommended): SHA256 hash of code verifier
- **plain** (not recommended): Code verifier sent in plain text

## Database Models

### PKCEClient

```sql
CREATE TABLE pkce_clients (
  id UUID PRIMARY KEY,
  client_id VARCHAR(255) UNIQUE NOT NULL,
  client_name VARCHAR(255) NOT NULL,
  client_uri VARCHAR(512),
  redirect_uris TEXT[] NOT NULL,  -- Array of allowed redirect URIs
  grant_types TEXT[] DEFAULT ['authorization_code'],
  response_types TEXT[] DEFAULT ['code'],
  scope TEXT,
  is_public BOOLEAN DEFAULT TRUE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### OAuth2AuthorizationCode

```sql
CREATE TABLE oauth2_authorization_codes (
  id UUID PRIMARY KEY,
  code VARCHAR(255) UNIQUE NOT NULL,
  client_id VARCHAR(255) NOT NULL,
  user_id UUID NOT NULL,
  redirect_uri VARCHAR(512) NOT NULL,
  scope TEXT,
  code_challenge VARCHAR(255) NOT NULL,
  code_challenge_method VARCHAR(10) DEFAULT 'S256',
  state VARCHAR(255),
  nonce VARCHAR(255),
  is_used VARCHAR(10) DEFAULT 'false',
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP NOT NULL,
  used_at TIMESTAMP
);
```

## Integration with Existing Auth

The PKCE implementation integrates seamlessly with the existing authentication system:

- Uses existing `create_access_token()` and `verify_token()` functions
- Leverages existing token blacklist infrastructure
- Compatible with existing user sessions and roles
- Shares the same JWT secret and token expiration settings

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_oauth2_pkce.py -v
```

Test coverage includes:
- Code verifier/challenge generation
- Client registration and validation
- Authorization code flow
- Token exchange with PKCE validation
- Token introspection and revocation
- State parameter validation
- Error handling and security checks

## Configuration

OAuth2 PKCE uses existing settings from `app.core.config`:

- `SECRET_KEY`: JWT signing key
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration (default: 24 hours)

Additional constants in `oauth2_pkce.py`:

- `CODE_VERIFIER_MIN_LENGTH`: 43 characters
- `CODE_VERIFIER_MAX_LENGTH`: 128 characters
- `AUTHORIZATION_CODE_EXPIRE_MINUTES`: 10 minutes

## Production Considerations

### Security Checklist

- ✅ Always use HTTPS in production
- ✅ Use S256 code challenge method (not plain)
- ✅ Validate all redirect URIs against whitelist
- ✅ Implement rate limiting on token endpoints
- ✅ Monitor for replay attacks (single-use codes)
- ✅ Rotate secrets regularly
- ✅ Use secure state parameters

### Performance

- Authorization codes are cleaned up automatically after expiration
- Token validation uses existing JWT verification (stateless)
- Blacklist check adds one database query per request
- Consider Redis caching for client lookups

### Monitoring

Track these metrics (if observability is enabled):

- `oauth2_authorization_granted`: Authorization codes issued
- `oauth2_token_issued`: Access tokens issued
- `oauth2_error`: OAuth2 errors by type
- `oauth2_client_registered`: New clients registered

## API Reference

### POST /oauth2/authorize

Create authorization code with PKCE.

**Authentication**: Required (user session)

**Request Body**:
```typescript
{
  response_type: "code",
  client_id: string,
  redirect_uri: string,
  scope?: string,
  state?: string,
  code_challenge: string,  // Base64url SHA256 hash
  code_challenge_method: "S256" | "plain"
}
```

**Response**: `{ code: string, state?: string }`

### POST /oauth2/token

Exchange authorization code for access token.

**Authentication**: None (public endpoint)

**Request Body**:
```typescript
{
  grant_type: "authorization_code",
  code: string,
  redirect_uri: string,
  client_id: string,
  code_verifier: string  // Original code verifier
}
```

**Response**:
```typescript
{
  access_token: string,
  token_type: "Bearer",
  expires_in: number,
  scope?: string
}
```

### POST /oauth2/introspect

Introspect access token.

**Authentication**: None (public endpoint)

**Request Body**: `{ token: string }`

**Response**:
```typescript
{
  active: boolean,
  scope?: string,
  client_id?: string,
  username?: string,
  token_type?: string,
  exp?: number,
  iat?: number,
  sub?: string,
  jti?: string
}
```

### POST /oauth2/revoke

Revoke access token.

**Authentication**: Required (user session)

**Request Body**: `{ token: string }`

**Response**: `{ message: "Token revoked successfully" }`

### POST /oauth2/clients

Register new OAuth2 client.

**Authentication**: Required (admin only)

**Request Body**:
```typescript
{
  client_name: string,
  redirect_uris: string[],
  client_uri?: string,
  scope?: string
}
```

**Response**: PKCEClient object with generated `client_id`

## References

- [RFC 7636 - PKCE](https://tools.ietf.org/html/rfc7636)
- [RFC 6749 - OAuth 2.0](https://tools.ietf.org/html/rfc6749)
- [RFC 7662 - Token Introspection](https://tools.ietf.org/html/rfc7662)
- [OAuth 2.0 Security Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)

## License

Part of the Residency Scheduler project. See main LICENSE file.
