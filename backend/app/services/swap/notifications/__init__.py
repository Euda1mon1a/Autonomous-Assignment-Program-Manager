"""
Swap notification subsystem.

Handles all notifications related to swap requests including
creation, approval, execution, and rollback notifications.
"""

from .swap_notifier import SwapNotifier
from .email_templates import SwapEmailTemplates

__all__ = [
    "SwapNotifier",
    "SwapEmailTemplates",
]
