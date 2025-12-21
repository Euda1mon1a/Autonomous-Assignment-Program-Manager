"""Feature flag models for configuration and audit logging."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class FeatureFlag(Base):
    """
    Feature flag configuration.

    Supports:
    - Boolean flags (on/off)
    - Percentage rollouts (gradual releases)
    - User targeting (specific user IDs)
    - Environment-based flags (dev/staging/production)
    - A/B testing variants
    - Flag dependencies
    """
    __tablename__ = "feature_flags"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Flag type: 'boolean', 'percentage', 'variant'
    flag_type = Column(String(20), nullable=False, default='boolean')

    # Enabled status
    enabled = Column(Boolean, nullable=False, default=False)

    # Percentage rollout (0.0 - 1.0)
    rollout_percentage = Column(Float, nullable=True)

    # Environment targeting (null = all environments)
    # JSON array: ["development", "staging", "production"]
    environments = Column(JSON, nullable=True)

    # User targeting (null = all users)
    # JSON array of user IDs: ["user-uuid-1", "user-uuid-2"]
    target_user_ids = Column(JSON, nullable=True)

    # Role targeting (null = all roles)
    # JSON array: ["admin", "coordinator"]
    target_roles = Column(JSON, nullable=True)

    # A/B testing variants
    # JSON object: {"control": 0.5, "variant_a": 0.3, "variant_b": 0.2}
    variants = Column(JSON, nullable=True)

    # Dependencies: other flags that must be enabled
    # JSON array of flag keys: ["parent_feature", "prerequisite_feature"]
    dependencies = Column(JSON, nullable=True)

    # Custom attributes for advanced targeting
    # JSON object for arbitrary targeting rules
    custom_attributes = Column(JSON, nullable=True)

    # Metadata
    created_by = Column(GUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    evaluations = relationship("FeatureFlagEvaluation", back_populates="flag", cascade="all, delete-orphan")
    audit_logs = relationship("FeatureFlagAudit", back_populates="flag", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "flag_type IN ('boolean', 'percentage', 'variant')",
            name="check_flag_type"
        ),
        CheckConstraint(
            "rollout_percentage IS NULL OR (rollout_percentage >= 0.0 AND rollout_percentage <= 1.0)",
            name="check_rollout_percentage_range"
        ),
        Index('idx_feature_flag_enabled', 'enabled'),
        Index('idx_feature_flag_type', 'flag_type'),
    )

    def __repr__(self):
        return f"<FeatureFlag(key='{self.key}', enabled={self.enabled}, type='{self.flag_type}')>"


class FeatureFlagEvaluation(Base):
    """
    Feature flag evaluation history for analytics and debugging.

    Tracks every time a feature flag is evaluated for a user.
    """
    __tablename__ = "feature_flag_evaluations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    flag_id = Column(GUID(), ForeignKey('feature_flags.id', ondelete='CASCADE'), nullable=False, index=True)

    # User context
    user_id = Column(GUID(), nullable=True, index=True)
    user_role = Column(String(50), nullable=True)

    # Evaluation result
    enabled = Column(Boolean, nullable=False)
    variant = Column(String(50), nullable=True)  # For A/B testing

    # Context at evaluation time
    environment = Column(String(50), nullable=True)
    rollout_percentage = Column(Float, nullable=True)

    # Additional context (for debugging)
    context = Column(JSON, nullable=True)

    # Timestamp
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    flag = relationship("FeatureFlag", back_populates="evaluations")

    __table_args__ = (
        Index('idx_flag_eval_flag_user', 'flag_id', 'user_id'),
        Index('idx_flag_eval_timestamp', 'evaluated_at'),
    )

    def __repr__(self):
        return f"<FeatureFlagEvaluation(flag_id='{self.flag_id}', enabled={self.enabled})>"


class FeatureFlagAudit(Base):
    """
    Audit log for feature flag changes.

    Tracks all modifications to feature flags for compliance and debugging.
    """
    __tablename__ = "feature_flag_audit"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    flag_id = Column(GUID(), ForeignKey('feature_flags.id', ondelete='CASCADE'), nullable=False, index=True)

    # Who made the change
    user_id = Column(GUID(), nullable=True, index=True)
    username = Column(String(100), nullable=True)

    # What changed
    action = Column(String(50), nullable=False)  # 'created', 'updated', 'deleted', 'enabled', 'disabled'
    changes = Column(JSON, nullable=True)  # Before/after values

    # Why (optional)
    reason = Column(Text, nullable=True)

    # When
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    flag = relationship("FeatureFlag", back_populates="audit_logs")

    __table_args__ = (
        CheckConstraint(
            "action IN ('created', 'updated', 'deleted', 'enabled', 'disabled')",
            name="check_audit_action"
        ),
        Index('idx_flag_audit_timestamp', 'created_at'),
        Index('idx_flag_audit_user', 'user_id'),
    )

    def __repr__(self):
        return f"<FeatureFlagAudit(flag_id='{self.flag_id}', action='{self.action}')>"
