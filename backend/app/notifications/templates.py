"""
Email template definitions and rendering.

Provides template rendering with Jinja2 for all notification types.
"""
from typing import Any, Dict
from datetime import date, datetime
from jinja2 import Environment, BaseLoader, TemplateNotFound


class NotificationTemplates:
    """Email template manager with Jinja2 rendering."""

    def __init__(self):
        """Initialize template environment."""
        # Use DictLoader for in-memory templates
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=True,
        )
        self._register_filters()

    def _register_filters(self):
        """Register custom Jinja2 filters."""
        self.env.filters["format_date"] = self._format_date
        self.env.filters["format_datetime"] = self._format_datetime

    @staticmethod
    def _format_date(value: date | str) -> str:
        """Format date as human-readable string."""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value).date()
            except ValueError:
                return value

        if isinstance(value, date):
            return value.strftime("%B %d, %Y")
        return str(value)

    @staticmethod
    def _format_datetime(value: datetime | str) -> str:
        """Format datetime as human-readable string."""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value

        if isinstance(value, datetime):
            return value.strftime("%B %d, %Y at %I:%M %p")
        return str(value)

    def render(
        self,
        template_name: str,
        variables: Dict[str, Any],
    ) -> tuple[str, str]:
        """
        Render email template with variables.

        Args:
            template_name: Name of template (e.g., 'schedule_change')
            variables: Dictionary of template variables

        Returns:
            Tuple of (subject, html_content)
        """
        template_method = getattr(self, f"_render_{template_name}", None)
        if not template_method:
            raise TemplateNotFound(f"Template '{template_name}' not found")

        return template_method(variables)

    def _render_schedule_change(self, vars: Dict[str, Any]) -> tuple[str, str]:
        """Render schedule change notification."""
        subject = f"Schedule Update: {vars.get('change_type', 'Change')} Notification"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin: 20px 0; }}
        .highlight {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }}
        .button {{ background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; display: inline-block; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Schedule Update</h1>
        </div>
        <div class="content">
            <p>Hello {vars.get('recipient_name', 'there')},</p>

            <p>Your schedule has been updated with the following changes:</p>

            <div class="highlight">
                <strong>Change Type:</strong> {vars.get('change_type', 'N/A')}<br>
                <strong>Effective Date:</strong> {self._format_date(vars.get('effective_date', 'N/A'))}<br>
                {f"<strong>Block:</strong> {vars.get('block_name', 'N/A')}<br>" if vars.get('block_name') else ""}
                {f"<strong>Rotation:</strong> {vars.get('rotation_name', 'N/A')}<br>" if vars.get('rotation_name') else ""}
            </div>

            {f"<p><strong>Details:</strong> {vars.get('details', '')}</p>" if vars.get('details') else ""}

            <p>Please review your updated schedule and contact the program coordinator if you have any questions.</p>

            {f'<a href="{vars.get("schedule_url", "#")}" class="button">View Schedule</a>' if vars.get('schedule_url') else ""}
        </div>
        <div class="footer">
            <p>This is an automated notification from the Residency Scheduler system.</p>
            <p>If you no longer wish to receive these notifications, please update your notification preferences.</p>
        </div>
    </div>
</body>
</html>
"""
        return subject, html

    def _render_absence_alert(self, vars: Dict[str, Any]) -> tuple[str, str]:
        """Render absence alert notification."""
        subject = f"Absence Alert: Coverage Needed for {vars.get('absent_person_name', 'Resident')}"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #e74c3c; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin: 20px 0; }}
        .alert {{ background-color: #ffebee; padding: 15px; margin: 10px 0; border-left: 4px solid #e74c3c; }}
        .info-box {{ background-color: #e3f2fd; padding: 15px; margin: 10px 0; border-left: 4px solid #2196f3; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }}
        .button {{ background-color: #e74c3c; color: white; padding: 10px 20px; text-decoration: none; display: inline-block; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Absence Alert</h1>
        </div>
        <div class="content">
            <p>Hello {vars.get('recipient_name', 'Coordinator')},</p>

            <div class="alert">
                <strong>COVERAGE NEEDED</strong><br>
                An absence has been reported that requires attention.
            </div>

            <div class="info-box">
                <strong>Absent Person:</strong> {vars.get('absent_person_name', 'N/A')}<br>
                <strong>Reason:</strong> {vars.get('absence_reason', 'Not specified')}<br>
                <strong>Start Date:</strong> {self._format_date(vars.get('start_date', 'N/A'))}<br>
                <strong>End Date:</strong> {self._format_date(vars.get('end_date', 'N/A'))}<br>
                {f"<strong>Affected Assignments:</strong> {vars.get('affected_count', 0)}<br>" if vars.get('affected_count') else ""}
            </div>

            {f"<p><strong>Critical Services Affected:</strong></p><ul>{''.join([f'<li>{svc}</li>' for svc in vars.get('critical_services', [])])}</ul>" if vars.get('critical_services') else ""}

            <p>Immediate action may be required to ensure adequate coverage. Please review the affected assignments and arrange for appropriate coverage.</p>

            {f'<a href="{vars.get("coverage_url", "#")}" class="button">Review Coverage</a>' if vars.get('coverage_url') else ""}
        </div>
        <div class="footer">
            <p>This is an automated notification from the Residency Scheduler system.</p>
        </div>
    </div>
</body>
</html>
"""
        return subject, html

    def _render_compliance_warning(self, vars: Dict[str, Any]) -> tuple[str, str]:
        """Render compliance warning notification."""
        subject = f"Compliance Alert: {vars.get('violation_type', 'Review Required')}"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin: 20px 0; }}
        .warning {{ background-color: #fff3e0; padding: 15px; margin: 10px 0; border-left: 4px solid #ff9800; }}
        .details {{ background-color: white; padding: 15px; margin: 10px 0; border: 1px solid #ddd; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }}
        .button {{ background-color: #ff9800; color: white; padding: 10px 20px; text-decoration: none; display: inline-block; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Compliance Warning</h1>
        </div>
        <div class="content">
            <p>Hello {vars.get('recipient_name', 'Administrator')},</p>

            <div class="warning">
                <strong>COMPLIANCE ISSUE DETECTED</strong><br>
                A potential compliance violation has been identified in the schedule.
            </div>

            <div class="details">
                <strong>Violation Type:</strong> {vars.get('violation_type', 'N/A')}<br>
                <strong>Severity:</strong> {vars.get('severity', 'Medium').upper()}<br>
                <strong>Affected Period:</strong> {self._format_date(vars.get('start_date', 'N/A'))} - {self._format_date(vars.get('end_date', 'N/A'))}<br>
                {f"<strong>Affected Person:</strong> {vars.get('affected_person', 'N/A')}<br>" if vars.get('affected_person') else ""}
            </div>

            <p><strong>Description:</strong></p>
            <p>{vars.get('description', 'No description provided.')}</p>

            {f"<p><strong>Recommended Action:</strong> {vars.get('recommended_action', 'Review and adjust schedule as needed.')}</p>" if vars.get('recommended_action') else ""}

            <p>Please review this issue and take appropriate action to ensure ACGME compliance.</p>

            {f'<a href="{vars.get("review_url", "#")}" class="button">Review Issue</a>' if vars.get('review_url') else ""}
        </div>
        <div class="footer">
            <p>This is an automated notification from the Residency Scheduler system.</p>
            <p>Compliance monitoring is active to help maintain ACGME standards.</p>
        </div>
    </div>
</body>
</html>
"""
        return subject, html

    def _render_assignment_reminder(self, vars: Dict[str, Any]) -> tuple[str, str]:
        """Render assignment reminder notification."""
        subject = f"Reminder: Upcoming Assignment on {self._format_date(vars.get('assignment_date', 'N/A'))}"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4caf50; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin: 20px 0; }}
        .reminder {{ background-color: #e8f5e9; padding: 15px; margin: 10px 0; border-left: 4px solid #4caf50; }}
        .assignment-details {{ background-color: white; padding: 15px; margin: 10px 0; border: 1px solid #ddd; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }}
        .button {{ background-color: #4caf50; color: white; padding: 10px 20px; text-decoration: none; display: inline-block; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Assignment Reminder</h1>
        </div>
        <div class="content">
            <p>Hello {vars.get('recipient_name', 'there')},</p>

            <div class="reminder">
                <strong>UPCOMING ASSIGNMENT</strong><br>
                This is a reminder about your upcoming assignment.
            </div>

            <div class="assignment-details">
                <strong>Date:</strong> {self._format_date(vars.get('assignment_date', 'N/A'))}<br>
                <strong>Rotation:</strong> {vars.get('rotation_name', 'N/A')}<br>
                {f"<strong>Location:</strong> {vars.get('location', 'N/A')}<br>" if vars.get('location') else ""}
                {f"<strong>Supervisor:</strong> {vars.get('supervisor', 'N/A')}<br>" if vars.get('supervisor') else ""}
                {f"<strong>Start Time:</strong> {vars.get('start_time', 'N/A')}<br>" if vars.get('start_time') else ""}
            </div>

            {f"<p><strong>Special Instructions:</strong></p><p>{vars.get('instructions', '')}</p>" if vars.get('instructions') else ""}

            {f"<p><strong>Requirements:</strong></p><ul>{''.join([f'<li>{req}</li>' for req in vars.get('requirements', [])])}</ul>" if vars.get('requirements') else ""}

            <p>Please ensure you are prepared for this assignment. Contact the program coordinator if you have any questions or concerns.</p>

            {f'<a href="{vars.get("schedule_url", "#")}" class="button">View Full Schedule</a>' if vars.get('schedule_url') else ""}
        </div>
        <div class="footer">
            <p>This is an automated reminder from the Residency Scheduler system.</p>
            <p>To adjust reminder settings, please update your notification preferences.</p>
        </div>
    </div>
</body>
</html>
"""
        return subject, html

    def get_available_templates(self) -> list[str]:
        """Get list of available template names."""
        return [
            "schedule_change",
            "absence_alert",
            "compliance_warning",
            "assignment_reminder",
        ]
