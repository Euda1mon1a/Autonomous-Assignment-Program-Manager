"""Notification templates for schedule alerts and updates."""
from dataclasses import dataclass
from enum import Enum
from string import Template


class NotificationType(str, Enum):
    """Available notification types."""
    SCHEDULE_PUBLISHED = "schedule_published"
    ASSIGNMENT_CHANGED = "assignment_changed"
    SHIFT_REMINDER_24H = "shift_reminder_24h"
    SHIFT_REMINDER_1H = "shift_reminder_1h"
    ACGME_WARNING = "acgme_warning"
    ABSENCE_APPROVED = "absence_approved"
    ABSENCE_REJECTED = "absence_rejected"


@dataclass
class NotificationTemplate:
    """
    Template for a notification.

    Attributes:
        type: The notification type
        subject_template: Template string for subject line
        body_template: Template string for message body
        channels: List of delivery channels to use
        priority: Priority level (high, normal, low)
    """
    type: NotificationType
    subject_template: str
    body_template: str
    channels: list[str]  # e.g., ['in_app', 'email', 'webhook']
    priority: str = "normal"  # high, normal, low

    def render_subject(self, data: dict) -> str:
        """
        Render subject template with provided data.

        Args:
            data: Dictionary of variables to substitute

        Returns:
            Rendered subject string
        """
        template = Template(self.subject_template)
        return template.safe_substitute(data)

    def render_body(self, data: dict) -> str:
        """
        Render body template with provided data.

        Args:
            data: Dictionary of variables to substitute

        Returns:
            Rendered body string
        """
        template = Template(self.body_template)
        return template.safe_substitute(data)


# Template Registry
NOTIFICATION_TEMPLATES: dict[NotificationType, NotificationTemplate] = {
    NotificationType.SCHEDULE_PUBLISHED: NotificationTemplate(
        type=NotificationType.SCHEDULE_PUBLISHED,
        subject_template="New Schedule Published for $period",
        body_template="""A new schedule has been published for $period.

Coverage Rate: $coverage_rate%
Total Assignments: $total_assignments
ACGME Violations: $violations_count

Please review your assignments at your earliest convenience.

Published by: $publisher_name
Published at: $published_at""",
        channels=["in_app", "email"],
        priority="high"
    ),

    NotificationType.ASSIGNMENT_CHANGED: NotificationTemplate(
        type=NotificationType.ASSIGNMENT_CHANGED,
        subject_template="Assignment Change: $rotation_name",
        body_template="""Your assignment has been changed.

Rotation: $rotation_name
Block: $block_name
Date Range: $start_date to $end_date

Previous Assignment: $previous_rotation
New Assignment: $new_rotation

Reason: $change_reason

Changed by: $changed_by
Changed at: $changed_at""",
        channels=["in_app", "email"],
        priority="high"
    ),

    NotificationType.SHIFT_REMINDER_24H: NotificationTemplate(
        type=NotificationType.SHIFT_REMINDER_24H,
        subject_template="Reminder: Shift Tomorrow - $rotation_name",
        body_template="""This is a reminder that you have a shift starting tomorrow.

Rotation: $rotation_name
Location: $location
Start Date: $start_date
Duration: $duration_weeks weeks

Please ensure you are prepared and review any relevant materials.

Questions? Contact $contact_person at $contact_email""",
        channels=["in_app", "email"],
        priority="normal"
    ),

    NotificationType.SHIFT_REMINDER_1H: NotificationTemplate(
        type=NotificationType.SHIFT_REMINDER_1H,
        subject_template="Starting Soon: $rotation_name",
        body_template="""Your shift starts in approximately 1 hour.

Rotation: $rotation_name
Location: $location
Start Time: $start_time

Good luck!""",
        channels=["in_app"],
        priority="high"
    ),

    NotificationType.ACGME_WARNING: NotificationTemplate(
        type=NotificationType.ACGME_WARNING,
        subject_template="ACGME Compliance Alert: $violation_type",
        body_template="""An ACGME compliance issue has been detected.

Violation Type: $violation_type
Severity: $severity
Affected Person: $person_name

Details: $violation_details

Recommended Action: $recommended_action

This requires immediate attention. Please contact your program coordinator.

Detected at: $detected_at""",
        channels=["in_app", "email", "webhook"],
        priority="high"
    ),

    NotificationType.ABSENCE_APPROVED: NotificationTemplate(
        type=NotificationType.ABSENCE_APPROVED,
        subject_template="Absence Request Approved",
        body_template="""Your absence request has been approved.

Type: $absence_type
Period: $start_date to $end_date
Duration: $duration_days days

Notes: $approval_notes

Approved by: $approver_name
Approved at: $approved_at

This time has been blocked from scheduling.""",
        channels=["in_app", "email"],
        priority="normal"
    ),

    NotificationType.ABSENCE_REJECTED: NotificationTemplate(
        type=NotificationType.ABSENCE_REJECTED,
        subject_template="Absence Request Not Approved",
        body_template="""Your absence request could not be approved at this time.

Type: $absence_type
Period: $start_date to $end_date
Duration: $duration_days days

Reason: $rejection_reason

Reviewed by: $reviewer_name
Reviewed at: $reviewed_at

If you have questions or would like to discuss this, please contact your coordinator.""",
        channels=["in_app", "email"],
        priority="normal"
    ),
}


def get_template(notification_type: NotificationType) -> NotificationTemplate | None:
    """
    Retrieve a notification template by type.

    Args:
        notification_type: The type of notification

    Returns:
        NotificationTemplate if found, None otherwise
    """
    return NOTIFICATION_TEMPLATES.get(notification_type)


def render_notification(
    notification_type: NotificationType,
    data: dict
) -> dict[str, str] | None:
    """
    Render a notification with provided data.

    Args:
        notification_type: The type of notification
        data: Dictionary of variables for substitution

    Returns:
        Dictionary with 'subject' and 'body' keys, or None if template not found
    """
    template = get_template(notification_type)
    if not template:
        return None

    return {
        "subject": template.render_subject(data),
        "body": template.render_body(data),
        "priority": template.priority,
        "channels": template.channels,
    }
