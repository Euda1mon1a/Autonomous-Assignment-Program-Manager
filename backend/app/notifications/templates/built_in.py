"""Built-in notification templates for the Residency Scheduler."""
from app.notifications.templates.registry import TemplateVersion, get_template_registry


def register_built_in_templates() -> None:
    """
    Register all built-in notification templates.

    This function creates and registers the default templates used by the system.
    Each template includes HTML and plain text versions with proper variable
    substitution using Jinja2.
    """
    registry = get_template_registry()

    # Schedule Published Template
    registry.register_template(
        TemplateVersion(
            template_id="schedule_published",
            version="1.0.0",
            name="Schedule Published",
            description="Notification sent when a new schedule is published",
            subject_template="New Schedule Published for {{ period }}",
            html_template="""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #003366;">New Schedule Published</h2>

    <p>A new schedule has been published for <strong>{{ period }}</strong>.</p>

    <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-left: 4px solid #003366;">
        <p><strong>Coverage Rate:</strong> {{ coverage_rate }}%</p>
        <p><strong>Total Assignments:</strong> {{ total_assignments }}</p>
        <p><strong>ACGME Violations:</strong> {{ violations_count }}</p>
    </div>

    <p>Please review your assignments at your earliest convenience.</p>

    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
        <p><strong>Published by:</strong> {{ publisher_name }}</p>
        <p><strong>Published at:</strong> {{ published_at }}</p>
    </div>
</div>
""",
            text_template="""New Schedule Published for {{ period }}

A new schedule has been published for {{ period }}.

Coverage Rate: {{ coverage_rate }}%
Total Assignments: {{ total_assignments }}
ACGME Violations: {{ violations_count }}

Please review your assignments at your earliest convenience.

Published by: {{ publisher_name }}
Published at: {{ published_at }}
""",
            variables=[
                "period",
                "coverage_rate",
                "total_assignments",
                "violations_count",
                "publisher_name",
                "published_at",
            ],
            tags=["schedule", "announcement", "high-priority"],
        )
    )

    # Assignment Changed Template
    registry.register_template(
        TemplateVersion(
            template_id="assignment_changed",
            version="1.0.0",
            name="Assignment Changed",
            description="Notification sent when an assignment is changed",
            subject_template="Assignment Change: {{ rotation_name }}",
            html_template="""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #856404; background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107;">
        Assignment Change Notice
    </h2>

    <p>Your assignment has been changed.</p>

    <div style="background-color: #f8f9fa; padding: 15px; margin: 20px 0;">
        <p><strong>Rotation:</strong> {{ rotation_name }}</p>
        <p><strong>Block:</strong> {{ block_name }}</p>
        <p><strong>Date Range:</strong> {{ start_date }} to {{ end_date }}</p>
    </div>

    <div style="background-color: #fff3cd; padding: 15px; margin: 20px 0;">
        <p><strong>Previous Assignment:</strong> {{ previous_rotation }}</p>
        <p><strong>New Assignment:</strong> {{ new_rotation }}</p>
    </div>

    <div style="background-color: #e7f3ff; padding: 15px; margin: 20px 0;">
        <p><strong>Reason:</strong> {{ change_reason }}</p>
    </div>

    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
        <p><strong>Changed by:</strong> {{ changed_by }}</p>
        <p><strong>Changed at:</strong> {{ changed_at }}</p>
    </div>
</div>
""",
            text_template="""Assignment Change: {{ rotation_name }}

Your assignment has been changed.

Rotation: {{ rotation_name }}
Block: {{ block_name }}
Date Range: {{ start_date }} to {{ end_date }}

Previous Assignment: {{ previous_rotation }}
New Assignment: {{ new_rotation }}

Reason: {{ change_reason }}

Changed by: {{ changed_by }}
Changed at: {{ changed_at }}
""",
            variables=[
                "rotation_name",
                "block_name",
                "start_date",
                "end_date",
                "previous_rotation",
                "new_rotation",
                "change_reason",
                "changed_by",
                "changed_at",
            ],
            tags=["assignment", "change", "high-priority"],
        )
    )

    # Shift Reminder 24H Template
    registry.register_template(
        TemplateVersion(
            template_id="shift_reminder_24h",
            version="1.0.0",
            name="24-Hour Shift Reminder",
            description="Reminder sent 24 hours before a shift",
            subject_template="Reminder: Shift Tomorrow - {{ rotation_name }}",
            html_template="""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #0056b3;">Upcoming Shift Reminder</h2>

    <p>This is a reminder that you have a shift starting tomorrow.</p>

    <div style="background-color: #e7f3ff; padding: 15px; margin: 20px 0; border-left: 4px solid #0056b3;">
        <p><strong>Rotation:</strong> {{ rotation_name }}</p>
        <p><strong>Location:</strong> {{ location }}</p>
        <p><strong>Start Date:</strong> {{ start_date }}</p>
        <p><strong>Duration:</strong> {{ duration_weeks }} {{ duration_weeks|pluralize('week', 'weeks') }}</p>
    </div>

    <p>Please ensure you are prepared and review any relevant materials.</p>

    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
        <p><strong>Questions?</strong> Contact {{ contact_person }} at {{ contact_email }}</p>
    </div>
</div>
""",
            text_template="""Reminder: Shift Tomorrow - {{ rotation_name }}

This is a reminder that you have a shift starting tomorrow.

Rotation: {{ rotation_name }}
Location: {{ location }}
Start Date: {{ start_date }}
Duration: {{ duration_weeks }} {{ duration_weeks|pluralize('week', 'weeks') }}

Please ensure you are prepared and review any relevant materials.

Questions? Contact {{ contact_person }} at {{ contact_email }}
""",
            variables=[
                "rotation_name",
                "location",
                "start_date",
                "duration_weeks",
                "contact_person",
                "contact_email",
            ],
            tags=["reminder", "shift", "normal-priority"],
        )
    )

    # Shift Reminder 1H Template
    registry.register_template(
        TemplateVersion(
            template_id="shift_reminder_1h",
            version="1.0.0",
            name="1-Hour Shift Reminder",
            description="Reminder sent 1 hour before a shift",
            subject_template="Starting Soon: {{ rotation_name }}",
            html_template="""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #dc3545; background-color: #f8d7da; padding: 10px; border-left: 4px solid #dc3545;">
        Shift Starting Soon
    </h2>

    <p>Your shift starts in approximately <strong>1 hour</strong>.</p>

    <div style="background-color: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107;">
        <p><strong>Rotation:</strong> {{ rotation_name }}</p>
        <p><strong>Location:</strong> {{ location }}</p>
        <p><strong>Start Time:</strong> {{ start_time }}</p>
    </div>

    <p style="font-size: 18px; text-align: center; margin: 30px 0;">Good luck!</p>
</div>
""",
            text_template="""Starting Soon: {{ rotation_name }}

Your shift starts in approximately 1 hour.

Rotation: {{ rotation_name }}
Location: {{ location }}
Start Time: {{ start_time }}

Good luck!
""",
            variables=["rotation_name", "location", "start_time"],
            tags=["reminder", "shift", "urgent", "high-priority"],
        )
    )

    # ACGME Warning Template
    registry.register_template(
        TemplateVersion(
            template_id="acgme_warning",
            version="1.0.0",
            name="ACGME Compliance Alert",
            description="Alert sent when ACGME compliance issue is detected",
            subject_template="ACGME Compliance Alert: {{ violation_type }}",
            html_template="""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background-color: #dc3545; color: white; padding: 15px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: white;">⚠️ ACGME Compliance Alert</h2>
    </div>

    <p><strong>An ACGME compliance issue has been detected and requires immediate attention.</strong></p>

    <div style="background-color: #f8d7da; padding: 15px; margin: 20px 0; border-left: 4px solid #dc3545;">
        <p><strong>Violation Type:</strong> {{ violation_type }}</p>
        <p><strong>Severity:</strong> <span style="color: #dc3545; font-weight: bold;">{{ severity }}</span></p>
        <p><strong>Affected Person:</strong> {{ person_name }}</p>
    </div>

    <div style="background-color: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107;">
        <p><strong>Details:</strong></p>
        <p>{{ violation_details }}</p>
    </div>

    <div style="background-color: #d1ecf1; padding: 15px; margin: 20px 0; border-left: 4px solid #17a2b8;">
        <p><strong>Recommended Action:</strong></p>
        <p>{{ recommended_action }}</p>
    </div>

    <p style="color: #dc3545; font-weight: bold;">
        This requires immediate attention. Please contact your program coordinator.
    </p>

    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
        <p><strong>Detected at:</strong> {{ detected_at }}</p>
    </div>
</div>
""",
            text_template="""⚠️ ACGME COMPLIANCE ALERT: {{ violation_type }}

An ACGME compliance issue has been detected and requires immediate attention.

VIOLATION TYPE: {{ violation_type }}
SEVERITY: {{ severity }}
AFFECTED PERSON: {{ person_name }}

DETAILS:
{{ violation_details }}

RECOMMENDED ACTION:
{{ recommended_action }}

This requires immediate attention. Please contact your program coordinator.

Detected at: {{ detected_at }}
""",
            variables=[
                "violation_type",
                "severity",
                "person_name",
                "violation_details",
                "recommended_action",
                "detected_at",
            ],
            tags=["acgme", "compliance", "alert", "critical", "high-priority"],
        )
    )

    # Absence Approved Template
    registry.register_template(
        TemplateVersion(
            template_id="absence_approved",
            version="1.0.0",
            name="Absence Request Approved",
            description="Notification sent when absence request is approved",
            subject_template="Absence Request Approved",
            html_template="""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background-color: #28a745; color: white; padding: 15px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: white;">✓ Absence Request Approved</h2>
    </div>

    <p>Your absence request has been approved.</p>

    <div style="background-color: #d4edda; padding: 15px; margin: 20px 0; border-left: 4px solid #28a745;">
        <p><strong>Type:</strong> {{ absence_type }}</p>
        <p><strong>Period:</strong> {{ start_date }} to {{ end_date }}</p>
        <p><strong>Duration:</strong> {{ duration_days }} {{ duration_days|pluralize('day', 'days') }}</p>
    </div>

    {% if approval_notes %}
    <div style="background-color: #e7f3ff; padding: 15px; margin: 20px 0;">
        <p><strong>Notes:</strong></p>
        <p>{{ approval_notes }}</p>
    </div>
    {% endif %}

    <p>This time has been blocked from scheduling.</p>

    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
        <p><strong>Approved by:</strong> {{ approver_name }}</p>
        <p><strong>Approved at:</strong> {{ approved_at }}</p>
    </div>
</div>
""",
            text_template="""✓ Absence Request Approved

Your absence request has been approved.

Type: {{ absence_type }}
Period: {{ start_date }} to {{ end_date }}
Duration: {{ duration_days }} {{ duration_days|pluralize('day', 'days') }}

{% if approval_notes %}Notes: {{ approval_notes }}{% endif %}

This time has been blocked from scheduling.

Approved by: {{ approver_name }}
Approved at: {{ approved_at }}
""",
            variables=[
                "absence_type",
                "start_date",
                "end_date",
                "duration_days",
                "approval_notes",
                "approver_name",
                "approved_at",
            ],
            tags=["absence", "approval", "normal-priority"],
        )
    )

    # Absence Rejected Template
    registry.register_template(
        TemplateVersion(
            template_id="absence_rejected",
            version="1.0.0",
            name="Absence Request Not Approved",
            description="Notification sent when absence request is rejected",
            subject_template="Absence Request Not Approved",
            html_template="""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background-color: #ffc107; color: #333; padding: 15px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #333;">Absence Request Not Approved</h2>
    </div>

    <p>Your absence request could not be approved at this time.</p>

    <div style="background-color: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107;">
        <p><strong>Type:</strong> {{ absence_type }}</p>
        <p><strong>Period:</strong> {{ start_date }} to {{ end_date }}</p>
        <p><strong>Duration:</strong> {{ duration_days }} {{ duration_days|pluralize('day', 'days') }}</p>
    </div>

    <div style="background-color: #f8d7da; padding: 15px; margin: 20px 0; border-left: 4px solid #dc3545;">
        <p><strong>Reason:</strong></p>
        <p>{{ rejection_reason }}</p>
    </div>

    <p>If you have questions or would like to discuss this, please contact your coordinator.</p>

    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
        <p><strong>Reviewed by:</strong> {{ reviewer_name }}</p>
        <p><strong>Reviewed at:</strong> {{ reviewed_at }}</p>
    </div>
</div>
""",
            text_template="""Absence Request Not Approved

Your absence request could not be approved at this time.

Type: {{ absence_type }}
Period: {{ start_date }} to {{ end_date }}
Duration: {{ duration_days }} {{ duration_days|pluralize('day', 'days') }}

Reason: {{ rejection_reason }}

If you have questions or would like to discuss this, please contact your coordinator.

Reviewed by: {{ reviewer_name }}
Reviewed at: {{ reviewed_at }}
""",
            variables=[
                "absence_type",
                "start_date",
                "end_date",
                "duration_days",
                "rejection_reason",
                "reviewer_name",
                "reviewed_at",
            ],
            tags=["absence", "rejection", "normal-priority"],
        )
    )


# Auto-register built-in templates when module is imported
register_built_in_templates()
