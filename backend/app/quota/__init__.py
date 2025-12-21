"""
API Quota Management Package.

This package provides comprehensive quota management for API usage:
- Daily and monthly quota limits
- Real-time usage tracking
- Overage handling and alerts
- Quota reset automation
- Usage reports and analytics

Components:
- policies: Quota policy definitions and role-based limits
- tracking: Redis-based usage tracking
- manager: Main quota management service
"""

from app.quota.manager import QuotaManager
from app.quota.policies import QuotaPolicy, QuotaPolicyType, get_policy_for_role
from app.quota.tracking import QuotaTracker

__all__ = [
    "QuotaManager",
    "QuotaPolicy",
    "QuotaPolicyType",
    "QuotaTracker",
    "get_policy_for_role",
]
