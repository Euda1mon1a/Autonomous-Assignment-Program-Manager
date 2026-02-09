"""Tests for structured error codes."""

from app.core.error_codes import (
    ERROR_CODE_DESCRIPTIONS,
    ErrorCode,
    get_error_code_from_message,
    get_error_description,
)


# ==================== ErrorCode Enum ====================


class TestErrorCodeEnum:
    def test_is_str(self):
        assert isinstance(ErrorCode.NOT_FOUND, str)

    def test_not_found_value(self):
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"

    def test_all_values_unique(self):
        values = [e.value for e in ErrorCode]
        assert len(values) == len(set(values))

    def test_resource_errors_exist(self):
        assert ErrorCode.NOT_FOUND
        assert ErrorCode.ALREADY_EXISTS
        assert ErrorCode.RECORD_NOT_FOUND
        assert ErrorCode.DUPLICATE_RECORD

    def test_validation_errors_exist(self):
        assert ErrorCode.VALIDATION_ERROR
        assert ErrorCode.INVALID_STATE
        assert ErrorCode.REQUIRED_FIELD

    def test_auth_errors_exist(self):
        assert ErrorCode.UNAUTHORIZED
        assert ErrorCode.FORBIDDEN
        assert ErrorCode.TOKEN_EXPIRED
        assert ErrorCode.INVALID_TOKEN

    def test_scheduling_errors_exist(self):
        assert ErrorCode.SCHEDULING_ERROR
        assert ErrorCode.SCHEDULE_CONFLICT
        assert ErrorCode.SOLVER_TIMEOUT
        assert ErrorCode.INFEASIBLE_SCHEDULE

    def test_acgme_errors_exist(self):
        assert ErrorCode.ACGME_COMPLIANCE_ERROR
        assert ErrorCode.WORK_HOUR_VIOLATION
        assert ErrorCode.REST_REQUIREMENT_VIOLATION
        assert ErrorCode.SUPERVISION_VIOLATION

    def test_database_errors_exist(self):
        assert ErrorCode.DATABASE_ERROR
        assert ErrorCode.DATABASE_CONNECTION_ERROR
        assert ErrorCode.INTEGRITY_CONSTRAINT_ERROR

    def test_rate_limit_errors_exist(self):
        assert ErrorCode.RATE_LIMIT_EXCEEDED
        assert ErrorCode.QUOTA_EXCEEDED

    def test_internal_error(self):
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"


# ==================== ERROR_CODE_DESCRIPTIONS ====================


class TestErrorCodeDescriptions:
    def test_all_codes_have_descriptions(self):
        for code in ErrorCode:
            assert code in ERROR_CODE_DESCRIPTIONS, f"{code.name} missing description"

    def test_descriptions_are_strings(self):
        for code, desc in ERROR_CODE_DESCRIPTIONS.items():
            assert isinstance(desc, str)
            assert len(desc) > 0

    def test_not_found_description(self):
        assert "not found" in ERROR_CODE_DESCRIPTIONS[ErrorCode.NOT_FOUND].lower()

    def test_work_hour_description(self):
        assert "80" in ERROR_CODE_DESCRIPTIONS[ErrorCode.WORK_HOUR_VIOLATION]


# ==================== get_error_description ====================


class TestGetErrorDescription:
    def test_known_code(self):
        desc = get_error_description(ErrorCode.NOT_FOUND)
        assert "not found" in desc.lower()

    def test_all_codes_return_description(self):
        for code in ErrorCode:
            desc = get_error_description(code)
            assert isinstance(desc, str)
            assert len(desc) > 0


# ==================== get_error_code_from_message ====================


class TestGetErrorCodeFromMessage:
    def test_empty_message(self):
        assert get_error_code_from_message("") == ErrorCode.INTERNAL_ERROR

    def test_not_found(self):
        assert get_error_code_from_message("User not found") == ErrorCode.NOT_FOUND

    def test_already_exists(self):
        assert (
            get_error_code_from_message("Record already exists")
            == ErrorCode.ALREADY_EXISTS
        )

    def test_duplicate(self):
        assert (
            get_error_code_from_message("Duplicate entry") == ErrorCode.ALREADY_EXISTS
        )

    def test_work_hour_violation(self):
        result = get_error_code_from_message("ACGME 80-hour work hour violation")
        assert result == ErrorCode.WORK_HOUR_VIOLATION

    def test_rest_requirement(self):
        result = get_error_code_from_message("ACGME rest requirement 1-in-7 violated")
        assert result == ErrorCode.REST_REQUIREMENT_VIOLATION

    def test_supervision(self):
        result = get_error_code_from_message("ACGME supervision ratio too low")
        assert result == ErrorCode.SUPERVISION_VIOLATION

    def test_acgme_generic(self):
        result = get_error_code_from_message("ACGME compliance issue")
        assert result == ErrorCode.ACGME_COMPLIANCE_ERROR

    def test_schedule_conflict(self):
        result = get_error_code_from_message("Schedule conflict detected")
        assert result == ErrorCode.SCHEDULE_CONFLICT

    def test_solver_timeout(self):
        result = get_error_code_from_message("Schedule solver timeout")
        assert result == ErrorCode.SOLVER_TIMEOUT

    def test_schedule_generation(self):
        result = get_error_code_from_message("Schedule generation failed")
        assert result == ErrorCode.SCHEDULE_GENERATION_FAILED

    def test_schedule_generic(self):
        result = get_error_code_from_message("Schedule error")
        assert result == ErrorCode.SCHEDULING_ERROR

    def test_concurrent_modification(self):
        result = get_error_code_from_message("Record modified by another user")
        assert result == ErrorCode.CONCURRENT_MODIFICATION

    def test_conflict(self):
        result = get_error_code_from_message("Concurrent write conflict")
        assert result == ErrorCode.CONFLICT

    def test_token_expired(self):
        result = get_error_code_from_message("Token expired")
        assert result == ErrorCode.TOKEN_EXPIRED

    def test_invalid_token(self):
        result = get_error_code_from_message("Invalid token provided")
        assert result == ErrorCode.INVALID_TOKEN

    def test_invalid_credentials(self):
        result = get_error_code_from_message("Invalid credentials")
        assert result == ErrorCode.INVALID_CREDENTIALS

    def test_unauthorized(self):
        result = get_error_code_from_message("Unauthorized access")
        assert result == ErrorCode.UNAUTHORIZED

    def test_forbidden(self):
        result = get_error_code_from_message("Access forbidden")
        assert result == ErrorCode.FORBIDDEN

    def test_permission_denied(self):
        result = get_error_code_from_message("Permission denied")
        assert result == ErrorCode.PERMISSION_DENIED

    def test_rate_limit(self):
        result = get_error_code_from_message("Rate limit exceeded")
        assert result == ErrorCode.RATE_LIMIT_EXCEEDED

    def test_quota(self):
        result = get_error_code_from_message("Quota exceeded")
        assert result == ErrorCode.QUOTA_EXCEEDED

    def test_database_timeout(self):
        result = get_error_code_from_message("Database timeout")
        assert result == ErrorCode.DATABASE_TIMEOUT

    def test_database_connection(self):
        result = get_error_code_from_message("Database connection error")
        assert result == ErrorCode.DATABASE_CONNECTION_ERROR

    def test_database_constraint(self):
        result = get_error_code_from_message("Database constraint violation")
        assert result == ErrorCode.INTEGRITY_CONSTRAINT_ERROR

    def test_database_generic(self):
        result = get_error_code_from_message("Database error occurred")
        assert result == ErrorCode.DATABASE_ERROR

    def test_required_field(self):
        result = get_error_code_from_message("Field name is required")
        assert result == ErrorCode.REQUIRED_FIELD

    def test_validation_error(self):
        result = get_error_code_from_message("Invalid email format")
        assert result == ErrorCode.VALIDATION_ERROR

    def test_unknown_message(self):
        result = get_error_code_from_message("Something completely unrecognized")
        assert result == ErrorCode.INTERNAL_ERROR

    def test_case_insensitive(self):
        assert get_error_code_from_message("NOT FOUND") == ErrorCode.NOT_FOUND
        assert get_error_code_from_message("not found") == ErrorCode.NOT_FOUND
