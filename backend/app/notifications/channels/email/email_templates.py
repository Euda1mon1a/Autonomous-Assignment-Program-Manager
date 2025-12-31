"""Pre-built email templates."""

from typing import Any

EMAIL_TEMPLATES = {
    "acgme_warning": {
        "subject": "ACGME Compliance Alert: {{violation_type}}",
        "html": """
<h2 style="color: #dc3545;">ACGME Compliance Alert</h2>
<p><strong>Violation Type:</strong> {{violation_type}}</p>
<p><strong>Severity:</strong> {{severity}}</p>
<p><strong>Affected Person:</strong> {{person_name}}</p>
<p><strong>Details:</strong></p>
<pre>{{violation_details}}</pre>
<p><strong>Recommended Action:</strong></p>
<p>{{recommended_action}}</p>
<p style="margin-top: 20px;">
    <a href="{{action_url}}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
        Review Details
    </a>
</p>
        """,
    },
    "schedule_published": {
        "subject": "New Schedule Published: {{period}}",
        "html": """
<h2>Schedule Published</h2>
<p>A new schedule has been published for <strong>{{period}}</strong>.</p>
<table style="width: 100%; margin: 20px 0;">
    <tr>
        <td><strong>Coverage Rate:</strong></td>
        <td>{{coverage_rate}}%</td>
    </tr>
    <tr>
        <td><strong>Total Assignments:</strong></td>
        <td>{{total_assignments}}</td>
    </tr>
    <tr>
        <td><strong>ACGME Violations:</strong></td>
        <td>{{violations_count}}</td>
    </tr>
</table>
<p style="margin-top: 20px;">
    <a href="{{schedule_url}}" style="background-color: #003366; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
        View Schedule
    </a>
</p>
        """,
    },
    "shift_reminder": {
        "subject": "Shift Reminder: {{rotation_name}}",
        "html": """
<h2>Upcoming Shift Reminder</h2>
<p>This is a reminder that you have an upcoming shift.</p>
<table style="width: 100%; margin: 20px 0;">
    <tr>
        <td><strong>Rotation:</strong></td>
        <td>{{rotation_name}}</td>
    </tr>
    <tr>
        <td><strong>Location:</strong></td>
        <td>{{location}}</td>
    </tr>
    <tr>
        <td><strong>Start:</strong></td>
        <td>{{start_date}}</td>
    </tr>
    <tr>
        <td><strong>Duration:</strong></td>
        <td>{{duration_weeks}} weeks</td>
    </tr>
</table>
<p>Please ensure you are prepared and review any relevant materials.</p>
        """,
    },
}


def get_email_template(template_name: str) -> dict[str, str] | None:
    """
    Get email template by name.

    Args:
        template_name: Name of template

    Returns:
        Template dictionary or None
    """
    return EMAIL_TEMPLATES.get(template_name)


def render_email_template(
    template_name: str, data: dict[str, Any]
) -> dict[str, str] | None:
    """
    Render email template with data.

    Args:
        template_name: Name of template
        data: Template data

    Returns:
        Dictionary with rendered subject and html
    """
    template = get_email_template(template_name)
    if not template:
        return None

    # Simple string replacement
    subject = template["subject"]
    html = template["html"]

    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"
        subject = subject.replace(placeholder, str(value))
        html = html.replace(placeholder, str(value))

    return {
        "subject": subject,
        "html": html,
    }
