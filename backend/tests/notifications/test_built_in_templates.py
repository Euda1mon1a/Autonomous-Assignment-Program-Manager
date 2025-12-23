"""Tests for built-in notification templates."""

from app.notifications.templates.registry import get_template_registry


class TestBuiltInTemplates:
    """Test suite for built-in templates."""

    def test_schedule_published_template_exists(self):
        """Test that schedule_published template is registered."""
        registry = get_template_registry()
        template = registry.get_template("schedule_published")

        assert template is not None
        assert template.template_id == "schedule_published"
        assert template.name == "Schedule Published"

    def test_schedule_published_template_renders(self):
        """Test rendering schedule_published template."""
        registry = get_template_registry()
        context = {
            "period": "January 2025",
            "coverage_rate": 95.5,
            "total_assignments": 150,
            "violations_count": 0,
            "publisher_name": "Dr. Smith",
            "published_at": "2025-01-15 10:30:00",
        }

        result = registry.render_template("schedule_published", context)

        assert result is not None
        assert "January 2025" in result["subject"]
        assert "95.5%" in result["html"]
        assert "150" in result["text"]
        assert "Dr. Smith" in result["html"]

    def test_assignment_changed_template_exists(self):
        """Test that assignment_changed template is registered."""
        registry = get_template_registry()
        template = registry.get_template("assignment_changed")

        assert template is not None
        assert template.template_id == "assignment_changed"

    def test_assignment_changed_template_renders(self):
        """Test rendering assignment_changed template."""
        registry = get_template_registry()
        context = {
            "rotation_name": "Cardiology",
            "block_name": "Block A",
            "start_date": "2025-02-01",
            "end_date": "2025-02-28",
            "previous_rotation": "Internal Medicine",
            "new_rotation": "Cardiology",
            "change_reason": "Schedule adjustment",
            "changed_by": "Dr. Johnson",
            "changed_at": "2025-01-20 14:00:00",
        }

        result = registry.render_template("assignment_changed", context)

        assert result is not None
        assert "Cardiology" in result["subject"]
        assert "Internal Medicine" in result["html"]
        assert "Schedule adjustment" in result["text"]

    def test_shift_reminder_24h_template_exists(self):
        """Test that shift_reminder_24h template is registered."""
        registry = get_template_registry()
        template = registry.get_template("shift_reminder_24h")

        assert template is not None
        assert template.template_id == "shift_reminder_24h"

    def test_shift_reminder_24h_template_renders(self):
        """Test rendering shift_reminder_24h template."""
        registry = get_template_registry()
        context = {
            "rotation_name": "Emergency Medicine",
            "location": "Main Hospital ER",
            "start_date": "2025-01-22",
            "duration_weeks": 2,
            "contact_person": "Dr. Williams",
            "contact_email": "williams@hospital.mil",
        }

        result = registry.render_template("shift_reminder_24h", context)

        assert result is not None
        assert "Emergency Medicine" in result["subject"]
        assert "Main Hospital ER" in result["html"]
        assert "2 weeks" in result["text"]  # Test pluralize filter
        assert "williams@hospital.mil" in result["html"]

    def test_shift_reminder_1h_template_exists(self):
        """Test that shift_reminder_1h template is registered."""
        registry = get_template_registry()
        template = registry.get_template("shift_reminder_1h")

        assert template is not None
        assert template.template_id == "shift_reminder_1h"

    def test_shift_reminder_1h_template_renders(self):
        """Test rendering shift_reminder_1h template."""
        registry = get_template_registry()
        context = {
            "rotation_name": "Surgery",
            "location": "Operating Room 3",
            "start_time": "07:00 AM",
        }

        result = registry.render_template("shift_reminder_1h", context)

        assert result is not None
        assert "Surgery" in result["subject"]
        assert "Operating Room 3" in result["html"]
        assert "07:00 AM" in result["text"]

    def test_acgme_warning_template_exists(self):
        """Test that acgme_warning template is registered."""
        registry = get_template_registry()
        template = registry.get_template("acgme_warning")

        assert template is not None
        assert template.template_id == "acgme_warning"
        assert "acgme" in template.tags
        assert "critical" in template.tags

    def test_acgme_warning_template_renders(self):
        """Test rendering acgme_warning template."""
        registry = get_template_registry()
        context = {
            "violation_type": "80-Hour Rule Violation",
            "severity": "CRITICAL",
            "person_name": "Dr. Anderson",
            "violation_details": "Resident scheduled for 85 hours in week 3",
            "recommended_action": "Reduce scheduled hours immediately",
            "detected_at": "2025-01-20 16:45:00",
        }

        result = registry.render_template("acgme_warning", context)

        assert result is not None
        assert "80-Hour Rule" in result["subject"]
        assert "CRITICAL" in result["html"]
        assert "Dr. Anderson" in result["text"]
        assert "85 hours" in result["html"]

    def test_absence_approved_template_exists(self):
        """Test that absence_approved template is registered."""
        registry = get_template_registry()
        template = registry.get_template("absence_approved")

        assert template is not None
        assert template.template_id == "absence_approved"

    def test_absence_approved_template_renders(self):
        """Test rendering absence_approved template."""
        registry = get_template_registry()
        context = {
            "absence_type": "Vacation",
            "start_date": "2025-03-01",
            "end_date": "2025-03-07",
            "duration_days": 7,
            "approval_notes": "Enjoy your time off!",
            "approver_name": "Dr. Martinez",
            "approved_at": "2025-02-15 09:30:00",
        }

        result = registry.render_template("absence_approved", context)

        assert result is not None
        assert "Approved" in result["subject"]
        assert "Vacation" in result["html"]
        assert "7 days" in result["text"]  # Test pluralize filter
        assert "Enjoy your time off" in result["html"]

    def test_absence_approved_template_renders_without_notes(self):
        """Test rendering absence_approved template without notes."""
        registry = get_template_registry()
        context = {
            "absence_type": "Medical Leave",
            "start_date": "2025-03-01",
            "end_date": "2025-03-01",
            "duration_days": 1,
            "approval_notes": "",
            "approver_name": "Dr. Martinez",
            "approved_at": "2025-02-15 09:30:00",
        }

        result = registry.render_template("absence_approved", context)

        assert result is not None
        assert "1 day" in result["text"]  # Test pluralize filter singular

    def test_absence_rejected_template_exists(self):
        """Test that absence_rejected template is registered."""
        registry = get_template_registry()
        template = registry.get_template("absence_rejected")

        assert template is not None
        assert template.template_id == "absence_rejected"

    def test_absence_rejected_template_renders(self):
        """Test rendering absence_rejected template."""
        registry = get_template_registry()
        context = {
            "absence_type": "Personal Leave",
            "start_date": "2025-04-01",
            "end_date": "2025-04-05",
            "duration_days": 5,
            "rejection_reason": "Insufficient coverage during requested period",
            "reviewer_name": "Dr. Thompson",
            "reviewed_at": "2025-03-15 11:00:00",
        }

        result = registry.render_template("absence_rejected", context)

        assert result is not None
        assert "Not Approved" in result["subject"]
        assert "Personal Leave" in result["html"]
        assert "Insufficient coverage" in result["text"]
        assert "Dr. Thompson" in result["html"]

    def test_all_templates_have_required_fields(self):
        """Test that all built-in templates have required fields."""
        registry = get_template_registry()
        template_ids = [
            "schedule_published",
            "assignment_changed",
            "shift_reminder_24h",
            "shift_reminder_1h",
            "acgme_warning",
            "absence_approved",
            "absence_rejected",
        ]

        for template_id in template_ids:
            template = registry.get_template(template_id)
            assert template is not None, f"Template {template_id} not found"
            assert template.subject_template, f"{template_id} missing subject"
            assert template.html_template, f"{template_id} missing HTML"
            assert template.text_template, f"{template_id} missing text"
            assert template.name, f"{template_id} missing name"
            assert template.version, f"{template_id} missing version"

    def test_all_templates_have_valid_syntax(self):
        """Test that all built-in templates have valid Jinja2 syntax."""
        from app.notifications.templates.engine import TemplateEngine

        registry = get_template_registry()
        engine = TemplateEngine()
        template_ids = [
            "schedule_published",
            "assignment_changed",
            "shift_reminder_24h",
            "shift_reminder_1h",
            "acgme_warning",
            "absence_approved",
            "absence_rejected",
        ]

        for template_id in template_ids:
            template = registry.get_template(template_id)
            assert template is not None

            # Validate syntax for all template parts
            assert engine.validate_syntax(template.subject_template)
            assert engine.validate_syntax(template.html_template)
            assert engine.validate_syntax(template.text_template)

    def test_templates_use_proper_html_structure(self):
        """Test that HTML templates have basic structure."""
        registry = get_template_registry()
        template_ids = [
            "schedule_published",
            "assignment_changed",
            "shift_reminder_24h",
            "shift_reminder_1h",
            "acgme_warning",
            "absence_approved",
            "absence_rejected",
        ]

        for template_id in template_ids:
            template = registry.get_template(template_id)
            html = template.html_template

            # Check for basic HTML elements
            assert "<" in html, f"{template_id} HTML should contain tags"
            assert ">" in html, f"{template_id} HTML should contain tags"

    def test_templates_include_variable_placeholders(self):
        """Test that templates include their declared variables."""
        registry = get_template_registry()
        template = registry.get_template("schedule_published")

        # Check that declared variables are actually used
        combined = (
            template.subject_template + template.html_template + template.text_template
        )

        for var in template.variables:
            assert f"{{{{ {var}" in combined or f"{{{{{var}" in combined, (
                f"Variable {var} not found in template"
            )
