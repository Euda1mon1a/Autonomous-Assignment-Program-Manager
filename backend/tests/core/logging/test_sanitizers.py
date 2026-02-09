"""Tests for data sanitizers (PII redaction and sensitive field masking)."""

from app.core.logging.sanitizers import (
    CREDIT_CARD_PATTERN,
    EMAIL_PATTERN,
    IP_ADDRESS_PATTERN,
    PHONE_PATTERN,
    SENSITIVE_FIELDS,
    SSN_PATTERN,
    DataSanitizer,
    SanitizationRule,
    create_custom_rule,
    get_global_sanitizer,
    sanitize,
    set_global_sanitizer,
)


# ==================== Pattern Constants ====================


class TestPatternConstants:
    def test_email_matches(self):
        assert EMAIL_PATTERN.search("user@example.com")

    def test_email_no_match(self):
        assert EMAIL_PATTERN.search("not-an-email") is None

    def test_phone_matches(self):
        assert PHONE_PATTERN.search("555-123-4567")

    def test_phone_matches_parens(self):
        # Pattern requires [-.]? between groups, space not matched
        assert PHONE_PATTERN.search("(555)123-4567")

    def test_phone_no_match(self):
        assert PHONE_PATTERN.search("12345") is None

    def test_ssn_matches(self):
        assert SSN_PATTERN.search("123-45-6789")

    def test_ssn_no_match(self):
        assert SSN_PATTERN.search("12345") is None

    def test_credit_card_matches(self):
        assert CREDIT_CARD_PATTERN.search("4111 1111 1111 1111")

    def test_credit_card_dashes(self):
        assert CREDIT_CARD_PATTERN.search("4111-1111-1111-1111")

    def test_ip_address_matches(self):
        assert IP_ADDRESS_PATTERN.search("192.168.1.1")

    def test_ip_address_no_match(self):
        assert IP_ADDRESS_PATTERN.search("no-ip-here") is None


# ==================== SENSITIVE_FIELDS set ====================


class TestSensitiveFields:
    def test_is_set(self):
        assert isinstance(SENSITIVE_FIELDS, set)

    def test_password_included(self):
        assert "password" in SENSITIVE_FIELDS

    def test_token_included(self):
        assert "token" in SENSITIVE_FIELDS

    def test_api_key_included(self):
        assert "api_key" in SENSITIVE_FIELDS

    def test_ssn_included(self):
        assert "ssn" in SENSITIVE_FIELDS

    def test_credit_card_included(self):
        assert "credit_card" in SENSITIVE_FIELDS

    def test_all_lowercase(self):
        for field in SENSITIVE_FIELDS:
            assert field == field.lower()


# ==================== SanitizationRule ====================


class TestSanitizationRule:
    def test_init_defaults(self):
        rule = SanitizationRule(name="test")
        assert rule.name == "test"
        assert rule.pattern is None
        assert rule.field_matcher is None
        assert rule.replacement == "[REDACTED]"
        assert rule.enabled is True

    def test_init_custom(self):
        rule = SanitizationRule(
            name="custom",
            pattern=EMAIL_PATTERN,
            replacement="[EMAIL]",
            enabled=False,
        )
        assert rule.pattern is EMAIL_PATTERN
        assert rule.replacement == "[EMAIL]"
        assert rule.enabled is False

    def test_should_redact_field_with_matcher(self):
        rule = SanitizationRule(name="test", field_matcher=lambda f: f == "secret")
        assert rule.should_redact_field("secret") is True
        assert rule.should_redact_field("public") is False

    def test_should_redact_field_no_matcher(self):
        rule = SanitizationRule(name="test")
        assert rule.should_redact_field("anything") is False

    def test_should_redact_field_disabled(self):
        rule = SanitizationRule(
            name="test",
            field_matcher=lambda f: True,
            enabled=False,
        )
        assert rule.should_redact_field("anything") is False

    def test_sanitize_value_with_pattern(self):
        rule = SanitizationRule(
            name="email", pattern=EMAIL_PATTERN, replacement="[EMAIL]"
        )
        result = rule.sanitize_value("contact user@example.com please")
        assert "[EMAIL]" in result
        assert "user@example.com" not in result

    def test_sanitize_value_no_pattern(self):
        rule = SanitizationRule(name="test")
        assert rule.sanitize_value("hello") == "hello"

    def test_sanitize_value_disabled(self):
        rule = SanitizationRule(name="test", pattern=EMAIL_PATTERN, enabled=False)
        assert rule.sanitize_value("user@example.com") == "user@example.com"

    def test_sanitize_value_non_string(self):
        rule = SanitizationRule(name="test", pattern=EMAIL_PATTERN)
        assert rule.sanitize_value(42) == 42


# ==================== DataSanitizer init ====================


class TestDataSanitizerInit:
    def test_default_fields(self):
        sanitizer = DataSanitizer()
        assert "password" in sanitizer.sensitive_fields
        assert "token" in sanitizer.sensitive_fields

    def test_custom_fields_extend(self):
        sanitizer = DataSanitizer(sensitive_fields={"my_secret"})
        assert "my_secret" in sanitizer.sensitive_fields
        assert "password" in sanitizer.sensitive_fields  # defaults preserved

    def test_custom_fields_lowercase(self):
        sanitizer = DataSanitizer(sensitive_fields={"MyField"})
        assert "myfield" in sanitizer.sensitive_fields

    def test_pii_detection_default(self):
        sanitizer = DataSanitizer()
        assert sanitizer.enable_pii_detection is True

    def test_pii_detection_disabled(self):
        sanitizer = DataSanitizer(enable_pii_detection=False)
        assert sanitizer.enable_pii_detection is False

    def test_partial_mask_default(self):
        sanitizer = DataSanitizer()
        assert sanitizer.partial_mask is False

    def test_rules_created(self):
        sanitizer = DataSanitizer()
        assert len(sanitizer.rules) >= 5  # email, phone, ssn, cc, sensitive_field

    def test_custom_rules_appended(self):
        custom = SanitizationRule(name="custom")
        sanitizer = DataSanitizer(custom_rules=[custom])
        assert any(r.name == "custom" for r in sanitizer.rules)


# ==================== DataSanitizer.sanitize_dict ====================


class TestSanitizeDict:
    def test_redacts_password(self):
        sanitizer = DataSanitizer()
        result = sanitizer.sanitize_dict({"password": "secret123"})
        assert result["password"] != "secret123"

    def test_redacts_token(self):
        sanitizer = DataSanitizer()
        result = sanitizer.sanitize_dict({"token": "abc.def.ghi"})
        assert result["token"] != "abc.def.ghi"

    def test_preserves_safe_field(self):
        sanitizer = DataSanitizer()
        result = sanitizer.sanitize_dict({"name": "Alice"})
        assert result["name"] == "Alice"

    def test_non_string_sensitive_redacted(self):
        sanitizer = DataSanitizer()
        result = sanitizer.sanitize_dict({"password": 12345})
        assert result["password"] == "[REDACTED]"

    def test_recursive_nested_dict(self):
        sanitizer = DataSanitizer()
        data = {"user": {"password": "secret", "name": "Bob"}}
        result = sanitizer.sanitize_dict(data)
        assert result["user"]["password"] != "secret"
        assert result["user"]["name"] == "Bob"

    def test_recursive_list(self):
        sanitizer = DataSanitizer()
        data = {"items": [{"password": "secret"}]}
        result = sanitizer.sanitize_dict(data)
        assert result["items"][0]["password"] != "secret"

    def test_non_recursive(self):
        sanitizer = DataSanitizer()
        data = {"user": {"password": "secret"}}
        result = sanitizer.sanitize_dict(data, recursive=False)
        # Nested dict not sanitized when recursive=False
        assert result["user"]["password"] == "secret"

    def test_pii_in_string_value(self):
        sanitizer = DataSanitizer()
        data = {"message": "Contact user@example.com for help"}
        result = sanitizer.sanitize_dict(data)
        assert "user@example.com" not in result["message"]
        assert "[REDACTED-EMAIL]" in result["message"]

    def test_non_dict_returns_as_is(self):
        sanitizer = DataSanitizer()
        assert sanitizer.sanitize_dict("not a dict") == "not a dict"

    def test_ssn_in_value_redacted(self):
        sanitizer = DataSanitizer()
        data = {"info": "SSN is 123-45-6789"}
        result = sanitizer.sanitize_dict(data)
        assert "123-45-6789" not in result["info"]


# ==================== DataSanitizer._mask_value ====================


class TestMaskValue:
    def test_full_mask_short(self):
        sanitizer = DataSanitizer()
        result = sanitizer._mask_value("abc")
        assert result == "***"

    def test_full_mask_long(self):
        sanitizer = DataSanitizer()
        result = sanitizer._mask_value("a" * 20)
        assert result == "*" * 8  # Capped at 8

    def test_empty_string(self):
        sanitizer = DataSanitizer()
        assert sanitizer._mask_value("") == ""

    def test_partial_mask(self):
        sanitizer = DataSanitizer(partial_mask=True)
        result = sanitizer._mask_value("123456789")
        # Shows last 4: "6789", mask_length = min(9-4, 8) = 5
        assert result.endswith("6789")
        assert result.startswith("*")

    def test_partial_mask_short_value(self):
        sanitizer = DataSanitizer(partial_mask=True)
        result = sanitizer._mask_value("ab")
        # len <= 4, so full mask
        assert result == "**"

    def test_custom_mask_char(self):
        sanitizer = DataSanitizer(mask_char="#")
        result = sanitizer._mask_value("secret")
        assert "#" in result
        assert "*" not in result


# ==================== DataSanitizer.sanitize_exception ====================


class TestSanitizeException:
    def test_redacts_email_in_exception(self):
        sanitizer = DataSanitizer()
        exc = ValueError("Failed for user@example.com")
        result = sanitizer.sanitize_exception(exc)
        assert "user@example.com" not in result
        assert "[REDACTED-EMAIL]" in result

    def test_clean_exception_unchanged(self):
        sanitizer = DataSanitizer()
        exc = ValueError("Something went wrong")
        result = sanitizer.sanitize_exception(exc)
        assert result == "Something went wrong"


# ==================== DataSanitizer.sanitize_log_record ====================


class TestSanitizeLogRecord:
    def test_sanitizes_message(self):
        sanitizer = DataSanitizer()
        record = {"message": "User user@example.com logged in"}
        result = sanitizer.sanitize_log_record(record)
        assert "user@example.com" not in result["message"]

    def test_sanitizes_extra(self):
        sanitizer = DataSanitizer()
        record = {"extra": {"password": "secret"}}
        result = sanitizer.sanitize_log_record(record)
        assert result["extra"]["password"] != "secret"

    def test_sanitizes_exception_value(self):
        sanitizer = DataSanitizer()
        record = {"exception": {"value": "Error for user@example.com"}}
        result = sanitizer.sanitize_log_record(record)
        assert "user@example.com" not in result["exception"]["value"]

    def test_preserves_other_fields(self):
        sanitizer = DataSanitizer()
        record = {"level": "INFO", "timestamp": "2024-01-01"}
        result = sanitizer.sanitize_log_record(record)
        assert result["level"] == "INFO"
        assert result["timestamp"] == "2024-01-01"

    def test_none_exception_ok(self):
        sanitizer = DataSanitizer()
        record = {"exception": None}
        result = sanitizer.sanitize_log_record(record)
        assert result["exception"] is None


# ==================== Global sanitizer ====================


class TestGlobalSanitizer:
    def test_get_creates_default(self):
        # Reset global state
        set_global_sanitizer(None)
        sanitizer = get_global_sanitizer()
        assert isinstance(sanitizer, DataSanitizer)

    def test_set_and_get(self):
        custom = DataSanitizer(partial_mask=True)
        set_global_sanitizer(custom)
        assert get_global_sanitizer() is custom
        # Clean up
        set_global_sanitizer(None)

    def test_get_returns_same_instance(self):
        set_global_sanitizer(None)
        s1 = get_global_sanitizer()
        s2 = get_global_sanitizer()
        assert s1 is s2
        set_global_sanitizer(None)


# ==================== sanitize() convenience function ====================


class TestSanitizeFunction:
    def test_dict(self):
        set_global_sanitizer(None)
        result = sanitize({"password": "secret"})
        assert result["password"] != "secret"

    def test_string(self):
        set_global_sanitizer(None)
        result = sanitize("Contact user@example.com")
        assert "user@example.com" not in result

    def test_list(self):
        set_global_sanitizer(None)
        result = sanitize(["user@example.com", "clean text"])
        assert "user@example.com" not in result[0]
        assert result[1] == "clean text"

    def test_other_types_passthrough(self):
        set_global_sanitizer(None)
        assert sanitize(42) == 42
        assert sanitize(None) is None
        assert sanitize(True) is True


# ==================== create_custom_rule ====================


class TestCreateCustomRule:
    def test_returns_rule(self):
        rule = create_custom_rule("test", r"\d{3}")
        assert isinstance(rule, SanitizationRule)

    def test_rule_name(self):
        rule = create_custom_rule("military_id", r"M\d{8}")
        assert rule.name == "military_id"

    def test_rule_has_compiled_pattern(self):
        rule = create_custom_rule("test", r"\d+")
        assert rule.pattern is not None
        assert rule.pattern.search("abc123")

    def test_custom_replacement(self):
        rule = create_custom_rule("test", r"\d+", replacement="[NUM]")
        assert rule.replacement == "[NUM]"

    def test_default_replacement(self):
        rule = create_custom_rule("test", r"\d+")
        assert rule.replacement == "[REDACTED]"

    def test_rule_works(self):
        rule = create_custom_rule("mil_id", r"M\d{8}", "[REDACTED-MIL-ID]")
        result = rule.sanitize_value("ID: M12345678")
        assert "M12345678" not in result
        assert "[REDACTED-MIL-ID]" in result
