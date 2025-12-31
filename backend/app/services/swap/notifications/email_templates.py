"""
Email templates for swap notifications.

Provides formatted email templates for various swap events.
"""

from datetime import date, datetime


class SwapEmailTemplates:
    """Email templates for swap notifications."""

    @staticmethod
    def swap_request_email(
        source_name: str,
        target_name: str,
        source_week: date,
        target_week: date | None,
        reason: str | None = None,
    ) -> str:
        """
        Template for new swap request notification.

        Args:
            source_name: Name of requesting faculty
            target_name: Name of target faculty
            source_week: Week being offered
            target_week: Week being requested
            reason: Reason for swap

        Returns:
            Formatted email body
        """
        email = f"""
Dear {target_name},

{source_name} has requested a swap with you.

Details:
- {source_name} offers: Week of {source_week.strftime('%B %d, %Y')}
"""

        if target_week:
            email += f"- {source_name} requests: Week of {target_week.strftime('%B %d, %Y')}\n"
        else:
            email += "- Type: Absorb (they're giving away their week)\n"

        if reason:
            email += f"\nReason: {reason}\n"

        email += """
Please review this request in the scheduling system and respond at your
earliest convenience.

Best regards,
Residency Scheduling System
"""

        return email

    @staticmethod
    def swap_executed_email(
        faculty_name: str,
        source_week: date,
        target_week: date | None,
        executed_at: datetime | None,
    ) -> str:
        """
        Template for swap execution notification.

        Args:
            faculty_name: Name of faculty member
            source_week: Week swapped away
            target_week: Week received
            executed_at: Execution timestamp

        Returns:
            Formatted email body
        """
        exec_time = executed_at.strftime('%B %d, %Y at %I:%M %p') if executed_at else "recently"

        email = f"""
Dear {faculty_name},

Your swap has been executed ({exec_time}).

Your schedule has been updated:
- You gave: Week of {source_week.strftime('%B %d, %Y')}
"""

        if target_week:
            email += f"- You received: Week of {target_week.strftime('%B %d, %Y')}\n"

        email += """
Please review your updated schedule in the scheduling system.

You have 24 hours to request a rollback if there are any issues.

Best regards,
Residency Scheduling System
"""

        return email

    @staticmethod
    def swap_rollback_email(
        faculty_name: str,
        source_week: date,
        reason: str | None,
    ) -> str:
        """
        Template for swap rollback notification.

        Args:
            faculty_name: Name of faculty member
            source_week: Week that was swapped
            reason: Reason for rollback

        Returns:
            Formatted email body
        """
        email = f"""
URGENT: Swap Rollback

Dear {faculty_name},

A swap involving your schedule has been rolled back.

Week affected: {source_week.strftime('%B %d, %Y')}
"""

        if reason:
            email += f"Reason: {reason}\n"

        email += """
Your schedule has been reverted to the original assignments.

Please review your schedule immediately and contact the scheduling
coordinator if you have any questions.

Best regards,
Residency Scheduling System
"""

        return email

    @staticmethod
    def swap_match_email(
        faculty_name: str,
        match_name: str,
        match_week: date,
        compatibility_score: float,
    ) -> str:
        """
        Template for swap match notification.

        Args:
            faculty_name: Name of faculty member
            match_name: Name of matched faculty
            match_week: Week of match
            compatibility_score: Compatibility score (0-1)

        Returns:
            Formatted email body
        """
        score_pct = int(compatibility_score * 100)

        email = f"""
Dear {faculty_name},

We found a compatible swap match for your request!

Match details:
- Faculty: {match_name}
- Week: {match_week.strftime('%B %d, %Y')}
- Compatibility: {score_pct}% match

This appears to be a good match based on your preferences and schedules.

Please review this match in the scheduling system and decide if you'd
like to proceed with the swap.

Best regards,
Residency Scheduling System
"""

        return email

    @staticmethod
    def swap_reminder_email(
        faculty_name: str,
        pending_requests: int,
        days_pending: int,
    ) -> str:
        """
        Template for pending swap reminder.

        Args:
            faculty_name: Name of faculty member
            pending_requests: Number of pending requests
            days_pending: Days since oldest request

        Returns:
            Formatted email body
        """
        email = f"""
Dear {faculty_name},

This is a reminder that you have {pending_requests} pending swap
"""

        if pending_requests == 1:
            email += "request.\n"
        else:
            email += "requests.\n"

        email += f"""
Your oldest request has been pending for {days_pending} days.

Please log into the scheduling system to review and take action on
your pending requests.

Best regards,
Residency Scheduling System
"""

        return email

    @staticmethod
    def swap_expired_email(
        faculty_name: str,
        week: date,
    ) -> str:
        """
        Template for expired swap notification.

        Args:
            faculty_name: Name of faculty member
            week: Week that expired

        Returns:
            Formatted email body
        """
        email = f"""
Dear {faculty_name},

Your swap request for the week of {week.strftime('%B %d, %Y')} has
expired because the week has passed.

If you still need schedule changes, please create a new swap request
or contact the scheduling coordinator.

Best regards,
Residency Scheduling System
"""

        return email
