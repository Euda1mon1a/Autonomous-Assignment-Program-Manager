"""Add gateway authentication tables

Revision ID: 20251220_add_gateway_auth_tables
Revises: 20251220_add_scheduled_jobs_tables
Create Date: 2025-12-20 18:30:00.000000

Creates tables for API gateway authentication:
- api_keys: API key authentication for external services
- oauth2_clients: OAuth2 client credentials flow
- ip_whitelists: IP whitelist for access control
- ip_blacklists: IP blacklist for blocking malicious IPs
- request_signatures: Request signature verification log (HMAC)

Features:
- API key validation with hashing and rotation support
- OAuth2 client credentials authentication
- IP-based access control (whitelist/blacklist)
- Rate limiting per API key/client
- Request signature verification (HMAC)
- Comprehensive audit trails
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251220_add_gateway_auth_tables'
down_revision: Union[str, None] = '20251220_add_scheduled_jobs_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create gateway authentication tables."""

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('key_prefix', sa.String(16), nullable=False),

        # Ownership and permissions
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scopes', sa.Text(), nullable=True),
        sa.Column('allowed_ips', sa.Text(), nullable=True),

        # Rate limiting
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=True, server_default='5000'),

        # Status and lifecycle
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('revoked_reason', sa.String(500), nullable=True),

        # Key rotation support
        sa.Column('rotated_from_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rotated_to_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Usage tracking
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_ip', sa.String(45), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Foreign keys
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['revoked_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rotated_from_id'], ['api_keys.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rotated_to_id'], ['api_keys.id'], ondelete='SET NULL'),
    )

    # Create indexes for api_keys
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index('ix_api_keys_key_prefix', 'api_keys', ['key_prefix'])
    op.create_index('idx_api_key_active', 'api_keys', ['is_active', 'expires_at'])
    op.create_index('idx_api_key_owner', 'api_keys', ['owner_id', 'is_active'])

    # Create oauth2_clients table
    op.create_table(
        'oauth2_clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', sa.String(255), nullable=False, unique=True),
        sa.Column('client_secret_hash', sa.String(255), nullable=False),

        # Client metadata
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Permissions and scopes
        sa.Column('scopes', sa.Text(), nullable=False, server_default='read'),
        sa.Column('grant_types', sa.String(255), nullable=False, server_default='client_credentials'),

        # Ownership
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_confidential', sa.Boolean(), nullable=False, server_default='true'),

        # Rate limiting
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=True, server_default='5000'),

        # Token settings
        sa.Column('access_token_lifetime_seconds', sa.Integer(), nullable=False, server_default='3600'),

        # Usage tracking
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('total_tokens_issued', sa.Integer(), nullable=False, server_default='0'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Foreign keys
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes for oauth2_clients
    op.create_index('ix_oauth2_clients_client_id', 'oauth2_clients', ['client_id'])
    op.create_index('idx_oauth2_client_active', 'oauth2_clients', ['is_active'])
    op.create_index('idx_oauth2_client_owner', 'oauth2_clients', ['owner_id', 'is_active'])

    # Create ip_whitelists table
    op.create_table(
        'ip_whitelists',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('applies_to', sa.String(50), nullable=False, server_default='all'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Foreign keys
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes for ip_whitelists
    op.create_index('ix_ip_whitelists_ip_address', 'ip_whitelists', ['ip_address'])
    op.create_index('idx_ip_whitelist_active', 'ip_whitelists', ['is_active', 'expires_at'])
    op.create_index('idx_ip_whitelist_applies_to', 'ip_whitelists', ['applies_to', 'is_active'])

    # Create ip_blacklists table
    op.create_table(
        'ip_blacklists',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('reason', sa.String(500), nullable=False),
        sa.Column('added_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('detection_method', sa.String(100), nullable=True),
        sa.Column('incident_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_hit_at', sa.DateTime(), nullable=True),

        # Foreign keys
        sa.ForeignKeyConstraint(['added_by_id'], ['users.id'], ondelete='SET NULL'),
    )

    # Create indexes for ip_blacklists
    op.create_index('ix_ip_blacklists_ip_address', 'ip_blacklists', ['ip_address'])
    op.create_index('idx_ip_blacklist_active', 'ip_blacklists', ['is_active', 'expires_at'])
    op.create_index('idx_ip_blacklist_detection', 'ip_blacklists', ['detection_method', 'is_active'])

    # Create request_signatures table
    op.create_table(
        'request_signatures',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('signature_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('request_method', sa.String(10), nullable=False),
        sa.Column('request_path', sa.String(2000), nullable=False),
        sa.Column('request_timestamp', sa.DateTime(), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.Column('failure_reason', sa.String(255), nullable=True),
        sa.Column('client_ip', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Foreign keys
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='CASCADE'),
    )

    # Create indexes for request_signatures
    op.create_index('ix_request_signatures_signature_hash', 'request_signatures', ['signature_hash'])
    op.create_index('idx_request_signature_timestamp', 'request_signatures', ['request_timestamp', 'verified_at'])
    op.create_index('idx_request_signature_api_key', 'request_signatures', ['api_key_id', 'verified_at'])


def downgrade() -> None:
    """Drop gateway authentication tables."""

    # Drop tables in reverse order (to respect foreign keys)
    op.drop_table('request_signatures')
    op.drop_table('ip_blacklists')
    op.drop_table('ip_whitelists')
    op.drop_table('oauth2_clients')
    op.drop_table('api_keys')
