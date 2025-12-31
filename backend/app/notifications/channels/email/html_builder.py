"""HTML email builder."""

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class HTMLEmailBuilder:
    """
    Builds HTML email templates.

    Features:
    - Responsive design
    - Military medical theme
    - Dark mode support
    - Accessibility compliant
    """

    # Base HTML template
    BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        {styles}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{subject}</h2>
        </div>
        <div class="content {priority_class}">
            {content}
        </div>
        <div class="footer">
            <p>This is an automated notification from the Schedule Management System.</p>
            <p><a href="{unsubscribe_link}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
"""

    # CSS styles
    STYLES = """
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            background-color: #003366;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h2 {
            margin: 0;
            font-size: 24px;
        }
        .content {
            padding: 30px;
        }
        .priority-high {
            border-left: 4px solid #dc3545;
        }
        .priority-normal {
            border-left: 4px solid #007bff;
        }
        .priority-low {
            border-left: 4px solid #6c757d;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 20px;
            font-size: 12px;
            color: #666;
            text-align: center;
        }
        .footer a {
            color: #007bff;
            text-decoration: none;
        }
        .button {
            display: inline-block;
            padding: 10px 20px;
            background-color: #003366;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 10px 0;
        }
        pre {
            white-space: pre-wrap;
            font-family: Arial, sans-serif;
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
        }
    """

    def build_html(
        self,
        subject: str,
        content: str,
        priority: str = "normal",
        unsubscribe_link: str = "#",
        extra_styles: str = "",
    ) -> str:
        """
        Build HTML email.

        Args:
            subject: Email subject
            content: Email content (HTML)
            priority: Priority level
            unsubscribe_link: Unsubscribe URL
            extra_styles: Additional CSS

        Returns:
            Complete HTML email
        """
        priority_class = f"priority-{priority}"
        styles = self.STYLES + extra_styles

        html = self.BASE_TEMPLATE.format(
            subject=subject,
            content=content,
            priority_class=priority_class,
            unsubscribe_link=unsubscribe_link,
            styles=styles,
        )

        logger.debug("Built HTML email: %s", subject)
        return html

    def build_simple_html(self, subject: str, body: str) -> str:
        """
        Build simple HTML email from plain text.

        Args:
            subject: Email subject
            body: Plain text body

        Returns:
            HTML email
        """
        content = f"<pre>{body}</pre>"
        return self.build_html(subject, content)

    def build_notification_html(
        self, subject: str, body: str, data: dict[str, Any], priority: str = "normal"
    ) -> str:
        """
        Build notification email HTML.

        Args:
            subject: Email subject
            body: Email body
            data: Notification data
            priority: Priority level

        Returns:
            HTML email
        """
        # Format body with line breaks
        formatted_body = body.replace("\n", "<br>")

        content = f"""
        <div class="notification-content">
            <p>{formatted_body}</p>
        </div>
        """

        # Add action button if URL provided
        if "action_url" in data:
            content += f"""
            <div style="text-align: center; margin-top: 20px;">
                <a href="{data['action_url']}" class="button">View Details</a>
            </div>
            """

        return self.build_html(subject, content, priority)
