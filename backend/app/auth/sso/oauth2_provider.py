"""
OAuth2 / OpenID Connect authentication provider.

Provides OAuth2 and OIDC authentication flow including:
- Authorization code flow
- Token exchange
- ID token validation
- UserInfo endpoint calls
- JWKS-based token verification
"""

import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwk, jwt
from jose.exceptions import JWKError

from app.auth.sso.config import OAuth2Config


class OAuth2Provider:
    """
    OAuth2 / OpenID Connect authentication provider.

    Implements the OAuth2 authorization code flow with PKCE support
    and OpenID Connect ID token validation.
    """

    def __init__(self, config: OAuth2Config) -> None:
        """
        Initialize OAuth2 provider.

        Args:
            config: OAuth2 configuration
        """
        self.config = config
        self._jwks_cache: dict | None = None
        self._jwks_cache_time: datetime | None = None
        self._jwks_cache_ttl = timedelta(hours=24)  # Cache JWKS for 24 hours

    def generate_authorization_url(
        self, state: str | None = None, use_pkce: bool = True
    ) -> dict[str, str]:
        """
        Generate OAuth2 authorization URL.

        Args:
            state: Optional state parameter for CSRF protection
            use_pkce: Whether to use PKCE (Proof Key for Code Exchange)

        Returns:
            Dict containing authorization_url, state, and optional code_verifier
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "scope": self.config.scope,
            "state": state,
        }

        result = {
            "state": state,
        }

        # Add PKCE parameters
        if use_pkce:
            code_verifier = secrets.token_urlsafe(64)
            code_challenge = self._generate_code_challenge(code_verifier)

            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

            result["code_verifier"] = code_verifier

        authorization_url = f"{self.config.authorization_endpoint}?{urlencode(params)}"
        result["authorization_url"] = authorization_url

        return result

    async def exchange_code_for_token(
        self, code: str, code_verifier: str | None = None
    ) -> dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback
            code_verifier: PKCE code verifier (if PKCE was used)

        Returns:
            Dict containing access_token, id_token, refresh_token, etc.

        Raises:
            ValueError: If token exchange fails
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.config.token_endpoint,
                    data=data,
                    headers={"Accept": "application/json"},
                    timeout=30.0,
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise ValueError(f"Token exchange failed: {e}")

            token_response = response.json()

            if "error" in token_response:
                error_desc = token_response.get(
                    "error_description", token_response["error"]
                )
                raise ValueError(f"Token exchange error: {error_desc}")

            result: dict[str, Any] = token_response
            return result

    async def validate_id_token(self, id_token: str) -> dict[str, Any]:
        """
        Validate OpenID Connect ID token.

        Validates signature, issuer, audience, and expiration.

        Args:
            id_token: JWT ID token string

        Returns:
            Dict containing validated token claims

        Raises:
            ValueError: If token validation fails
        """
        # Decode header to get key ID (kid)
        try:
            unverified_header = jwt.get_unverified_header(id_token)
            kid = unverified_header.get("kid")
        except JWTError as e:
            raise ValueError(f"Invalid ID token header: {e}")

            # Get signing key from JWKS
        signing_key = await self._get_signing_key(kid)

        # Verify and decode token
        try:
            claims = jwt.decode(
                id_token,
                signing_key,
                algorithms=["RS256", "HS256"],
                audience=self.config.client_id,
                issuer=self.config.issuer,
            )
        except JWTError as e:
            raise ValueError(f"ID token validation failed: {e}")

            # Additional validation
        now = datetime.utcnow().timestamp()

        # Check expiration
        exp = claims.get("exp")
        if exp and now >= exp:
            raise ValueError("ID token has expired")

            # Check not before
        nbf = claims.get("nbf")
        if nbf and now < nbf:
            raise ValueError("ID token not yet valid")

            # Check email verification if required
        if self.config.require_email_verified:
            email_verified = claims.get("email_verified", False)
            if not email_verified:
                raise ValueError("Email not verified")

        result: dict[str, Any] = claims
        return result

    async def get_userinfo(self, access_token: str) -> dict[str, Any]:
        """
        Fetch user information from UserInfo endpoint.

        Args:
            access_token: OAuth2 access token

        Returns:
            Dict containing user information

        Raises:
            ValueError: If UserInfo request fails
        """
        if not self.config.userinfo_endpoint:
            raise ValueError("UserInfo endpoint not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.config.userinfo_endpoint,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise ValueError(f"UserInfo request failed: {e}")

            result: dict[str, Any] = response.json()
            return result

    def map_claims_to_user(self, claims: dict[str, Any]) -> dict[str, str]:
        """
        Map OAuth2/OIDC claims to user attributes.

        Args:
            claims: Token claims or UserInfo response

        Returns:
            Dict of mapped user attributes
        """
        mapped = {}

        for claim_name, user_field in self.config.attribute_map.items():
            if claim_name in claims:
                value = claims[claim_name]

                # Handle nested claims (e.g., address.country)
                if isinstance(value, dict) and "." in claim_name:
                    parts = claim_name.split(".")
                    for part in parts[1:]:
                        value = value.get(part, "")
                        if not isinstance(value, dict):
                            break

                mapped[user_field] = str(value) if value else ""

        return mapped

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: OAuth2 refresh token

        Returns:
            Dict containing new access_token and optional new refresh_token

        Raises:
            ValueError: If token refresh fails
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.config.token_endpoint,
                    data=data,
                    headers={"Accept": "application/json"},
                    timeout=30.0,
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise ValueError(f"Token refresh failed: {e}")

            token_response = response.json()

            if "error" in token_response:
                error_desc = token_response.get(
                    "error_description", token_response["error"]
                )
                raise ValueError(f"Token refresh error: {error_desc}")

            result: dict[str, Any] = token_response
            return result

    async def revoke_token(
        self, token: str, token_type_hint: str = "access_token"
    ) -> bool:
        """
        Revoke an access or refresh token.

        Args:
            token: Token to revoke
            token_type_hint: Type hint ("access_token" or "refresh_token")

        Returns:
            True if revocation succeeded

        Raises:
            ValueError: If revocation fails
        """
        # Note: Not all OAuth2 providers support token revocation
        # This is a best-effort implementation

        # Construct revocation endpoint URL (common pattern)
        revocation_endpoint = self.config.token_endpoint.replace("/token", "/revoke")

        data = {
            "token": token,
            "token_type_hint": token_type_hint,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    revocation_endpoint,
                    data=data,
                    timeout=30.0,
                )

                # RFC 7009: Successful revocation returns 200
                return response.status_code == 200
            except httpx.HTTPError as e:
                raise ValueError(f"Token revocation failed: {e}")

    async def _get_signing_key(self, kid: str | None = None) -> str:
        """
        Get signing key from JWKS endpoint.

        Args:
            kid: Key ID to retrieve

        Returns:
            Signing key as PEM string

        Raises:
            ValueError: If key cannot be retrieved
        """
        # Check cache
        if (
            self._jwks_cache
            and self._jwks_cache_time
            and datetime.utcnow() - self._jwks_cache_time < self._jwks_cache_ttl
        ):
            jwks = self._jwks_cache
        else:
            # Fetch JWKS
            jwks = await self._fetch_jwks()
            self._jwks_cache = jwks
            self._jwks_cache_time = datetime.utcnow()

            # Find matching key
        keys = jwks.get("keys", [])
        matching_key = None

        for key in keys:
            if kid is None or key.get("kid") == kid:
                matching_key = key
                break

        if not matching_key:
            raise ValueError(f"Signing key not found for kid: {kid}")

            # Convert JWK to PEM
        try:
            key_obj = jwk.construct(matching_key)
            return str(key_obj)
        except JWKError as e:
            raise ValueError(f"Failed to construct signing key: {e}")

    async def _fetch_jwks(self) -> dict:
        """
        Fetch JSON Web Key Set from JWKS endpoint.

        Returns:
            JWKS as dict

        Raises:
            ValueError: If JWKS fetch fails
        """
        if not self.config.jwks_uri:
            raise ValueError("JWKS URI not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.config.jwks_uri,
                    headers={"Accept": "application/json"},
                    timeout=30.0,
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise ValueError(f"JWKS fetch failed: {e}")

            result: dict[str, Any] = response.json()
            return result

    def _generate_code_challenge(self, code_verifier: str) -> str:
        """
        Generate PKCE code challenge from verifier.

        Args:
            code_verifier: Random string (43-128 characters)

        Returns:
            Base64-URL-encoded SHA256 hash of verifier
        """
        challenge_bytes = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        challenge = base64.urlsafe_b64encode(challenge_bytes).decode("utf-8")
        # Remove padding
        return challenge.rstrip("=")

    async def discover_endpoints(self, discovery_url: str) -> dict[str, str]:
        """
        Discover OAuth2/OIDC endpoints from discovery document.

        Fetches the .well-known/openid-configuration endpoint.

        Args:
            discovery_url: OpenID Connect discovery URL

        Returns:
            Dict containing discovered endpoints

        Raises:
            ValueError: If discovery fails
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    discovery_url,
                    headers={"Accept": "application/json"},
                    timeout=30.0,
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                raise ValueError(f"Discovery failed: {e}")

            discovery_doc = response.json()

            return {
                "issuer": discovery_doc.get("issuer", ""),
                "authorization_endpoint": discovery_doc.get(
                    "authorization_endpoint", ""
                ),
                "token_endpoint": discovery_doc.get("token_endpoint", ""),
                "userinfo_endpoint": discovery_doc.get("userinfo_endpoint", ""),
                "jwks_uri": discovery_doc.get("jwks_uri", ""),
                "end_session_endpoint": discovery_doc.get("end_session_endpoint", ""),
            }
