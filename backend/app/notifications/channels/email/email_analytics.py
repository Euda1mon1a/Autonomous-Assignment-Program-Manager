"""Email analytics and reporting."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailAnalytics:
    """
    Provides analytics for email campaigns.

    Metrics:
    - Delivery rate
    - Open rate
    - Click-through rate
    - Bounce rate
    - Unsubscribe rate
    """

    def __init__(self) -> None:
        """Initialize analytics."""
        self._metrics: dict[str, Any] = defaultdict(int)
        self._campaigns: dict[str, dict[str, Any]] = {}

    def record_sent(self, campaign: str | None = None) -> None:
        """Record an email sent."""
        self._metrics["sent"] += 1

        if campaign:
            if campaign not in self._campaigns:
                self._campaigns[campaign] = defaultdict(int)
            self._campaigns[campaign]["sent"] += 1

    def record_delivered(self, campaign: str | None = None) -> None:
        """Record an email delivered."""
        self._metrics["delivered"] += 1

        if campaign:
            if campaign in self._campaigns:
                self._campaigns[campaign]["delivered"] += 1

    def record_opened(self, campaign: str | None = None) -> None:
        """Record an email opened."""
        self._metrics["opened"] += 1

        if campaign:
            if campaign in self._campaigns:
                self._campaigns[campaign]["opened"] += 1

    def record_clicked(self, campaign: str | None = None) -> None:
        """Record a link clicked."""
        self._metrics["clicked"] += 1

        if campaign:
            if campaign in self._campaigns:
                self._campaigns[campaign]["clicked"] += 1

    def record_bounced(self, campaign: str | None = None) -> None:
        """Record an email bounced."""
        self._metrics["bounced"] += 1

        if campaign:
            if campaign in self._campaigns:
                self._campaigns[campaign]["bounced"] += 1

    def record_unsubscribed(self, campaign: str | None = None) -> None:
        """Record an unsubscribe."""
        self._metrics["unsubscribed"] += 1

        if campaign:
            if campaign in self._campaigns:
                self._campaigns[campaign]["unsubscribed"] += 1

    def get_overall_metrics(self) -> dict[str, Any]:
        """Get overall email metrics."""
        sent = self._metrics["sent"]
        delivered = self._metrics["delivered"]
        opened = self._metrics["opened"]
        clicked = self._metrics["clicked"]
        bounced = self._metrics["bounced"]

        return {
            "sent": sent,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "bounced": bounced,
            "delivery_rate": round(delivered / sent * 100, 2) if sent > 0 else 0,
            "open_rate": round(opened / delivered * 100, 2) if delivered > 0 else 0,
            "click_rate": round(clicked / opened * 100, 2) if opened > 0 else 0,
            "bounce_rate": round(bounced / sent * 100, 2) if sent > 0 else 0,
        }

    def get_campaign_metrics(self, campaign: str) -> dict[str, Any]:
        """Get metrics for a specific campaign."""
        if campaign not in self._campaigns:
            return {}

        metrics = self._campaigns[campaign]
        sent = metrics.get("sent", 0)
        delivered = metrics.get("delivered", 0)
        opened = metrics.get("opened", 0)
        clicked = metrics.get("clicked", 0)

        return {
            "sent": sent,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "delivery_rate": round(delivered / sent * 100, 2) if sent > 0 else 0,
            "open_rate": round(opened / delivered * 100, 2) if delivered > 0 else 0,
            "click_rate": round(clicked / opened * 100, 2) if opened > 0 else 0,
        }

    def get_all_campaigns(self) -> list[str]:
        """Get list of all campaigns."""
        return list(self._campaigns.keys())
