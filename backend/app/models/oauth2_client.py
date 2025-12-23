"""OAuth2 PKCE client model for public client registration."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text

from app.db.base import Base
from app.db.types import GUID, StringArrayType


class PKCEClient(Base):
    """
    OAuth2 PKCE client registration for public clients.

    Public clients (mobile apps, SPAs) don't have client secrets.
    They use PKCE for security instead. This is separate from
    the OAuth2Client model which is for confidential clients
    using client_credentials flow.
    """

    __tablename__ = "pkce_clients"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Client identifier (public)
    client_id = Column(String(255), unique=True, nullable=False, index=True)

    # Client name and description
    client_name = Column(String(255), nullable=False)
    client_uri = Column(String(512), nullable=True)

    # Allowed redirect URIs (whitelist)
    redirect_uris = Column(StringArrayType, nullable=False, default=list)

    # Grant types allowed for this client
    grant_types = Column(
        StringArrayType, nullable=False, default=["authorization_code"]
    )

    # Response types (code, token, etc.)
    response_types = Column(StringArrayType, nullable=False, default=["code"])

    # Scope (space-separated list of allowed scopes)
    scope = Column(Text, nullable=True)

    # Client type: public (no secret) or confidential (has secret)
    # PKCE clients are always public
    is_public = Column(Boolean, default=True, nullable=False)

    # Whether this client is active
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("idx_oauth2_client_id_active", "client_id", "is_active"),)

    def __repr__(self):
        return f"<PKCEClient(client_id='{self.client_id}', name='{self.client_name}')>"

    def is_redirect_uri_allowed(self, redirect_uri: str) -> bool:
        """
        Check if a redirect URI is allowed for this client.

        Args:
            redirect_uri: The redirect URI to check

        Returns:
            True if allowed, False otherwise
        """
        if not self.redirect_uris:
            return False
        return redirect_uri in self.redirect_uris

    def is_grant_type_allowed(self, grant_type: str) -> bool:
        """
        Check if a grant type is allowed for this client.

        Args:
            grant_type: The grant type to check

        Returns:
            True if allowed, False otherwise
        """
        if not self.grant_types:
            return False
        return grant_type in self.grant_types
