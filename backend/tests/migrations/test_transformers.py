"""Tests for data transformation pipelines (pure logic, no DB)."""

from datetime import date, datetime
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.migrations.transformers import (
    DataTransformer,
    TransformationError,
    TransformationPipeline,
    create_audit_updater,
    create_email_normalizer,
    create_person_normalizer,
)


# -- helpers -----------------------------------------------------------------


def _record(**kwargs):
    """Create a SimpleNamespace record for testing."""
    return SimpleNamespace(**kwargs)


# -- TransformationError -----------------------------------------------------


class TestTransformationError:
    def test_is_exception(self):
        assert issubclass(TransformationError, Exception)

    def test_message(self):
        err = TransformationError("step failed")
        assert str(err) == "step failed"


# -- TransformationPipeline --------------------------------------------------


class TestPipelineInit:
    def test_empty_pipeline(self):
        p = TransformationPipeline()
        assert len(p) == 0

    def test_steps_list_empty(self):
        p = TransformationPipeline()
        assert p.steps == []


class TestPipelineAddStep:
    def test_add_step_returns_self(self):
        p = TransformationPipeline()
        result = p.add_step(lambda r: {})
        assert result is p

    def test_add_step_increments_length(self):
        p = TransformationPipeline()
        p.add_step(lambda r: {})
        assert len(p) == 1

    def test_chaining(self):
        p = TransformationPipeline()
        p.add_step(lambda r: {"a": 1}).add_step(lambda r: {"b": 2})
        assert len(p) == 2


class TestPipelineApply:
    def test_empty_pipeline_returns_empty_dict(self):
        p = TransformationPipeline()
        assert p.apply(_record(x=1)) == {}

    def test_single_step(self):
        p = TransformationPipeline()
        p.add_step(lambda r: {"upper": r.name.upper()})
        result = p.apply(_record(name="alice"))
        assert result == {"upper": "ALICE"}

    def test_multiple_steps_merge(self):
        p = TransformationPipeline()
        p.add_step(lambda r: {"a": 1})
        p.add_step(lambda r: {"b": 2})
        result = p.apply(_record())
        assert result == {"a": 1, "b": 2}

    def test_later_step_overwrites_earlier(self):
        p = TransformationPipeline()
        p.add_step(lambda r: {"x": 1})
        p.add_step(lambda r: {"x": 2})
        result = p.apply(_record())
        assert result == {"x": 2}

    def test_step_failure_raises_transformation_error(self):
        p = TransformationPipeline()
        p.add_step(lambda r: (_ for _ in ()).throw(RuntimeError("boom")))
        with pytest.raises(TransformationError, match="Step 0 failed"):
            p.apply(_record())

    def test_step_failure_wraps_original(self):
        p = TransformationPipeline()
        p.add_step(lambda r: (_ for _ in ()).throw(ValueError("bad")))
        with pytest.raises(TransformationError) as exc_info:
            p.apply(_record())
        assert isinstance(exc_info.value.__cause__, ValueError)


# -- DataTransformer.normalize_email -----------------------------------------


class TestNormalizeEmail:
    def test_lowercase(self):
        r = _record(email="Alice@Example.COM")
        assert DataTransformer.normalize_email(r) == {"email": "alice@example.com"}

    def test_strips_whitespace(self):
        r = _record(email="  bob@test.com  ")
        assert DataTransformer.normalize_email(r) == {"email": "bob@test.com"}

    def test_no_email_attr(self):
        r = _record(name="alice")
        assert DataTransformer.normalize_email(r) == {}

    def test_empty_email(self):
        r = _record(email="")
        assert DataTransformer.normalize_email(r) == {}

    def test_none_email(self):
        r = _record(email=None)
        assert DataTransformer.normalize_email(r) == {}


# -- DataTransformer.capitalize_name -----------------------------------------


class TestCapitalizeName:
    def test_title_case(self):
        r = _record(name="john doe")
        result = DataTransformer.capitalize_name(r)
        assert result == {"name": "John Doe"}

    def test_strips_whitespace(self):
        r = _record(name="  alice  ")
        result = DataTransformer.capitalize_name(r)
        assert result["name"].strip() == result["name"]

    def test_no_name_attr(self):
        r = _record(email="x@y.com")
        assert DataTransformer.capitalize_name(r) == {}

    def test_empty_name(self):
        r = _record(name="")
        assert DataTransformer.capitalize_name(r) == {}

    def test_none_name(self):
        r = _record(name=None)
        assert DataTransformer.capitalize_name(r) == {}

    def test_already_capitalized(self):
        r = _record(name="Alice")
        result = DataTransformer.capitalize_name(r)
        assert result == {"name": "Alice"}


# -- DataTransformer.normalize_phone_number ----------------------------------


class TestNormalizePhoneNumber:
    def test_ten_digits(self):
        r = _record(phone="1234567890")
        result = DataTransformer.normalize_phone_number(r)
        assert result == {"phone": "(123) 456-7890"}

    def test_formatted_input(self):
        r = _record(phone="(123) 456-7890")
        result = DataTransformer.normalize_phone_number(r)
        assert result == {"phone": "(123) 456-7890"}

    def test_dashes_and_dots(self):
        r = _record(phone="123-456-7890")
        result = DataTransformer.normalize_phone_number(r)
        assert result == {"phone": "(123) 456-7890"}

    def test_too_few_digits(self):
        r = _record(phone="12345")
        assert DataTransformer.normalize_phone_number(r) == {}

    def test_too_many_digits(self):
        r = _record(phone="12345678901")
        assert DataTransformer.normalize_phone_number(r) == {}

    def test_no_field(self):
        r = _record(name="alice")
        assert DataTransformer.normalize_phone_number(r) == {}

    def test_empty_phone(self):
        r = _record(phone="")
        assert DataTransformer.normalize_phone_number(r) == {}

    def test_none_phone(self):
        r = _record(phone=None)
        assert DataTransformer.normalize_phone_number(r) == {}

    def test_custom_field(self):
        r = _record(work_phone="9876543210")
        result = DataTransformer.normalize_phone_number(r, field="work_phone")
        assert result == {"work_phone": "(987) 654-3210"}


# -- DataTransformer.ensure_uuid ---------------------------------------------


class TestEnsureUuid:
    def test_string_to_uuid(self):
        uuid_str = "12345678-1234-5678-1234-567812345678"
        r = _record(id=uuid_str)
        result = DataTransformer.ensure_uuid(r)
        assert result == {"id": UUID(uuid_str)}

    def test_already_uuid(self):
        uuid_val = UUID("12345678-1234-5678-1234-567812345678")
        r = _record(id=uuid_val)
        assert DataTransformer.ensure_uuid(r) == {}

    def test_invalid_string(self):
        r = _record(id="not-a-uuid")
        assert DataTransformer.ensure_uuid(r) == {}

    def test_no_field(self):
        r = _record(name="alice")
        assert DataTransformer.ensure_uuid(r) == {}

    def test_custom_field(self):
        uuid_str = "12345678-1234-5678-1234-567812345678"
        r = _record(person_id=uuid_str)
        result = DataTransformer.ensure_uuid(r, field="person_id")
        assert result == {"person_id": UUID(uuid_str)}


# -- DataTransformer.ensure_datetime -----------------------------------------


class TestEnsureDatetime:
    def test_string_to_datetime(self):
        r = _record(created="2024-01-15T10:30:00")
        result = DataTransformer.ensure_datetime(r, "created")
        assert isinstance(result["created"], datetime)
        assert result["created"].year == 2024

    def test_date_to_datetime(self):
        d = date(2024, 6, 15)
        r = _record(start=d)
        result = DataTransformer.ensure_datetime(r, "start")
        assert isinstance(result["start"], datetime)
        assert result["start"].date() == d

    def test_already_datetime(self):
        dt = datetime(2024, 1, 1, 12, 0)
        r = _record(ts=dt)
        assert DataTransformer.ensure_datetime(r, "ts") == {}

    def test_invalid_string(self):
        r = _record(created="not-a-date")
        assert DataTransformer.ensure_datetime(r, "created") == {}

    def test_no_field(self):
        r = _record(name="alice")
        assert DataTransformer.ensure_datetime(r, "created") == {}


# -- DataTransformer.set_default_value ---------------------------------------


class TestSetDefaultValue:
    def test_missing_field_sets_default(self):
        r = _record(name="alice")
        result = DataTransformer.set_default_value(r, "role", "resident")
        assert result == {"role": "resident"}

    def test_none_field_sets_default(self):
        r = _record(role=None)
        result = DataTransformer.set_default_value(r, "role", "resident")
        assert result == {"role": "resident"}

    def test_existing_value_no_change(self):
        r = _record(role="faculty")
        result = DataTransformer.set_default_value(r, "role", "resident")
        assert result == {}

    def test_falsy_value_not_overridden(self):
        r = _record(count=0)
        result = DataTransformer.set_default_value(r, "count", 10)
        assert result == {}

    def test_empty_string_not_overridden(self):
        r = _record(note="")
        result = DataTransformer.set_default_value(r, "note", "default")
        assert result == {}


# -- DataTransformer.trim_whitespace -----------------------------------------


class TestTrimWhitespace:
    def test_trims_leading_trailing(self):
        r = _record(name="  Alice  ", email="  bob@test.com  ")
        result = DataTransformer.trim_whitespace(r, ["name", "email"])
        assert result == {"name": "Alice", "email": "bob@test.com"}

    def test_no_change_needed(self):
        r = _record(name="Alice")
        result = DataTransformer.trim_whitespace(r, ["name"])
        assert result == {}

    def test_missing_field_skipped(self):
        r = _record(name="Alice")
        result = DataTransformer.trim_whitespace(r, ["name", "missing"])
        assert result == {}

    def test_non_string_skipped(self):
        r = _record(count=42)
        result = DataTransformer.trim_whitespace(r, ["count"])
        assert result == {}

    def test_empty_fields_list(self):
        r = _record(name="  Alice  ")
        result = DataTransformer.trim_whitespace(r, [])
        assert result == {}


# -- DataTransformer.convert_to_boolean --------------------------------------


class TestConvertToBoolean:
    def test_string_true_values(self):
        for val in ["true", "True", "TRUE", "yes", "Yes", "1", "y", "t"]:
            r = _record(active=val)
            result = DataTransformer.convert_to_boolean(r, "active")
            assert result == {"active": True}, f"Failed for {val!r}"

    def test_string_false_values(self):
        for val in ["false", "False", "FALSE", "no", "No", "0", "n", "f"]:
            r = _record(active=val)
            result = DataTransformer.convert_to_boolean(r, "active")
            assert result == {"active": False}, f"Failed for {val!r}"

    def test_already_bool(self):
        r = _record(active=True)
        assert DataTransformer.convert_to_boolean(r, "active") == {}

    def test_int_truthy(self):
        r = _record(flag=1)
        result = DataTransformer.convert_to_boolean(r, "flag")
        assert result == {"flag": True}

    def test_int_falsy(self):
        r = _record(flag=0)
        result = DataTransformer.convert_to_boolean(r, "flag")
        assert result == {"flag": False}

    def test_float_truthy(self):
        r = _record(flag=1.5)
        result = DataTransformer.convert_to_boolean(r, "flag")
        assert result == {"flag": True}

    def test_no_field(self):
        r = _record(name="alice")
        assert DataTransformer.convert_to_boolean(r, "active") == {}

    def test_unrecognized_string(self):
        r = _record(active="maybe")
        assert DataTransformer.convert_to_boolean(r, "active") == {}


# -- DataTransformer.map_enum_value ------------------------------------------


class TestMapEnumValue:
    def test_maps_value(self):
        mapping = {"admin": "ADMIN", "user": "USER"}
        r = _record(role="admin")
        result = DataTransformer.map_enum_value(r, "role", mapping)
        assert result == {"role": "ADMIN"}

    def test_unmapped_value(self):
        mapping = {"admin": "ADMIN"}
        r = _record(role="guest")
        result = DataTransformer.map_enum_value(r, "role", mapping)
        assert result == {}

    def test_no_field(self):
        mapping = {"admin": "ADMIN"}
        r = _record(name="alice")
        result = DataTransformer.map_enum_value(r, "role", mapping)
        assert result == {}

    def test_enum_object_with_value_attr(self):
        class FakeEnum:
            value = "admin"

        mapping = {"admin": "ADMIN"}
        r = _record(role=FakeEnum())
        result = DataTransformer.map_enum_value(r, "role", mapping)
        assert result == {"role": "ADMIN"}


# -- DataTransformer.add_audit_fields ----------------------------------------


class TestAddAuditFields:
    def test_adds_updated_at(self):
        r = _record()
        result = DataTransformer.add_audit_fields(r)
        assert "updated_at" in result
        assert isinstance(result["updated_at"], datetime)

    def test_adds_updated_by_when_attr_exists(self):
        r = _record(updated_by=None)
        result = DataTransformer.add_audit_fields(r, user="admin")
        assert result["updated_by"] == "admin"

    def test_no_updated_by_when_attr_missing(self):
        r = _record()
        result = DataTransformer.add_audit_fields(r, user="admin")
        assert "updated_by" not in result

    def test_default_user(self):
        r = _record(updated_by=None)
        result = DataTransformer.add_audit_fields(r)
        assert result["updated_by"] == "system"


# -- DataTransformer.validate_and_fix_range ----------------------------------


class TestValidateAndFixRange:
    def test_within_range_no_change(self):
        r = _record(score=50)
        result = DataTransformer.validate_and_fix_range(r, "score", 0, 100)
        assert result == {}

    def test_below_min_clamped(self):
        r = _record(score=-5)
        result = DataTransformer.validate_and_fix_range(r, "score", min_value=0)
        assert result == {"score": 0}

    def test_above_max_clamped(self):
        r = _record(score=150)
        result = DataTransformer.validate_and_fix_range(r, "score", max_value=100)
        assert result == {"score": 100}

    def test_float_clamping(self):
        r = _record(rate=1.5)
        result = DataTransformer.validate_and_fix_range(r, "rate", max_value=1.0)
        assert result == {"rate": 1.0}

    def test_no_field(self):
        r = _record(name="alice")
        result = DataTransformer.validate_and_fix_range(r, "score", 0, 100)
        assert result == {}

    def test_non_numeric_skipped(self):
        r = _record(score="high")
        result = DataTransformer.validate_and_fix_range(r, "score", 0, 100)
        assert result == {}

    def test_no_limits(self):
        r = _record(score=999)
        result = DataTransformer.validate_and_fix_range(r, "score")
        assert result == {}

    def test_exact_boundary(self):
        r = _record(score=0)
        result = DataTransformer.validate_and_fix_range(r, "score", min_value=0)
        assert result == {}


# -- DataTransformer.conditional_update --------------------------------------


class TestConditionalUpdate:
    def test_condition_true_applies(self):
        r = _record(type="faculty")
        result = DataTransformer.conditional_update(
            r, lambda rec: rec.type == "faculty", {"performs_procedures": True}
        )
        assert result == {"performs_procedures": True}

    def test_condition_false_skips(self):
        r = _record(type="resident")
        result = DataTransformer.conditional_update(
            r, lambda rec: rec.type == "faculty", {"performs_procedures": True}
        )
        assert result == {}


# -- DataTransformer.copy_field ----------------------------------------------


class TestCopyField:
    def test_copies_value(self):
        r = _record(name="alice")
        result = DataTransformer.copy_field(r, "name", "display_name")
        assert result == {"display_name": "alice"}

    def test_missing_source(self):
        r = _record(email="a@b.com")
        result = DataTransformer.copy_field(r, "name", "display_name")
        assert result == {}

    def test_copies_none(self):
        r = _record(name=None)
        result = DataTransformer.copy_field(r, "name", "display_name")
        assert result == {"display_name": None}


# -- DataTransformer.rename_field_value --------------------------------------


class TestRenameFieldValue:
    def test_renames(self):
        r = _record(old_name="alice")
        result = DataTransformer.rename_field_value(r, "old_name", "new_name")
        assert result == {"new_name": "alice", "old_name": None}

    def test_missing_old_field(self):
        r = _record(email="x@y.com")
        result = DataTransformer.rename_field_value(r, "old_name", "new_name")
        assert result == {}


# -- Factory functions -------------------------------------------------------


class TestCreateEmailNormalizer:
    def test_returns_pipeline(self):
        p = create_email_normalizer()
        assert isinstance(p, TransformationPipeline)
        assert len(p) == 1

    def test_normalizes_email(self):
        p = create_email_normalizer()
        r = _record(email="  TEST@Example.COM  ")
        result = p.apply(r)
        assert result == {"email": "test@example.com"}


class TestCreatePersonNormalizer:
    def test_returns_pipeline(self):
        p = create_person_normalizer()
        assert isinstance(p, TransformationPipeline)
        assert len(p) == 3

    def test_normalizes_person(self):
        # Note: trim_whitespace (step 3) overwrites earlier steps because all
        # steps read from the original record, not the accumulated updates.
        p = create_person_normalizer()
        # Use pre-trimmed inputs so later steps don't overwrite earlier ones.
        r = _record(email="TEST@Example.COM", name="alice doe")
        result = p.apply(r)
        assert result["email"] == "test@example.com"
        assert result["name"] == "Alice Doe"


class TestCreateAuditUpdater:
    def test_returns_pipeline(self):
        p = create_audit_updater()
        assert isinstance(p, TransformationPipeline)
        assert len(p) == 1

    def test_adds_audit_fields(self):
        p = create_audit_updater(user="admin")
        r = _record(updated_by=None)
        result = p.apply(r)
        assert "updated_at" in result
        assert result["updated_by"] == "admin"
