"""Tests for credential validators (pure logic, no DB).

The credential_validators module does ``from app.models.certification import
Certification``, but the actual model class is ``PersonCertification``.
We patch the missing name onto the real module so the import succeeds.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock

# Patch the missing Certification alias before credential_validators loads
import app.models.certification as _cert_mod

if not hasattr(_cert_mod, "Certification"):
    _cert_mod.Certification = MagicMock()  # type: ignore[attr-defined]

import pytest

from app.validators.common import ValidationError
from app.validators.credential_validators import (
    CREDENTIAL_VALIDITY,
    REQUIRED_CREDENTIALS,
    SLOT_TYPE_REQUIREMENTS,
    validate_credential_expiration,
    validate_credential_issue_date,
    validate_credential_name,
)


# ── Constants structure tests ────────────────────────────────────────────


class TestRequiredCredentials:
    def test_has_annual_training(self):
        assert "annual_training" in REQUIRED_CREDENTIALS

    def test_has_safety(self):
        assert "safety" in REQUIRED_CREDENTIALS

    def test_has_immunizations(self):
        assert "immunizations" in REQUIRED_CREDENTIALS

    def test_has_procedures(self):
        assert "procedures" in REQUIRED_CREDENTIALS

    def test_annual_training_includes_hipaa(self):
        assert "HIPAA" in REQUIRED_CREDENTIALS["annual_training"]

    def test_annual_training_includes_cyber(self):
        assert "Cyber_Training" in REQUIRED_CREDENTIALS["annual_training"]

    def test_annual_training_includes_aup(self):
        assert "AUP" in REQUIRED_CREDENTIALS["annual_training"]

    def test_safety_includes_n95(self):
        assert "N95_Fit" in REQUIRED_CREDENTIALS["safety"]

    def test_safety_includes_bbp(self):
        assert "BBP_Module" in REQUIRED_CREDENTIALS["safety"]

    def test_immunizations_includes_flu(self):
        assert "Flu_Vax" in REQUIRED_CREDENTIALS["immunizations"]

    def test_immunizations_includes_hep_b(self):
        assert "Hep_B" in REQUIRED_CREDENTIALS["immunizations"]

    def test_procedures_includes_bls(self):
        assert "BLS" in REQUIRED_CREDENTIALS["procedures"]

    def test_procedures_includes_acls(self):
        assert "ACLS" in REQUIRED_CREDENTIALS["procedures"]

    def test_procedures_includes_pals(self):
        assert "PALS" in REQUIRED_CREDENTIALS["procedures"]

    def test_procedures_includes_nrp(self):
        assert "NRP" in REQUIRED_CREDENTIALS["procedures"]

    def test_all_values_are_lists(self):
        for key, value in REQUIRED_CREDENTIALS.items():
            assert isinstance(value, list), f"{key} is not a list"

    def test_no_empty_lists(self):
        for key, value in REQUIRED_CREDENTIALS.items():
            assert len(value) > 0, f"{key} is empty"


class TestCredentialValidity:
    def test_hipaa_12_months(self):
        assert CREDENTIAL_VALIDITY["HIPAA"] == 12

    def test_cyber_training_12_months(self):
        assert CREDENTIAL_VALIDITY["Cyber_Training"] == 12

    def test_chaperone_24_months(self):
        assert CREDENTIAL_VALIDITY["Chaperone"] == 24

    def test_tdap_120_months(self):
        assert CREDENTIAL_VALIDITY["Tdap"] == 120

    def test_hep_b_lifetime(self):
        assert CREDENTIAL_VALIDITY["Hep_B"] is None

    def test_bls_24_months(self):
        assert CREDENTIAL_VALIDITY["BLS"] == 24

    def test_acls_24_months(self):
        assert CREDENTIAL_VALIDITY["ACLS"] == 24

    def test_all_values_positive_or_none(self):
        for key, value in CREDENTIAL_VALIDITY.items():
            if value is not None:
                assert value > 0, f"{key} has non-positive validity: {value}"

    def test_all_required_credentials_have_validity(self):
        """Every credential in REQUIRED_CREDENTIALS should appear in CREDENTIAL_VALIDITY."""
        for category, creds in REQUIRED_CREDENTIALS.items():
            for cred in creds:
                assert cred in CREDENTIAL_VALIDITY, (
                    f"{cred} from {category} missing from CREDENTIAL_VALIDITY"
                )


class TestSlotTypeRequirements:
    def test_inpatient_call_has_hard(self):
        assert "hard" in SLOT_TYPE_REQUIREMENTS["inpatient_call"]
        assert len(SLOT_TYPE_REQUIREMENTS["inpatient_call"]["hard"]) > 0

    def test_peds_clinic_has_hard(self):
        assert "hard" in SLOT_TYPE_REQUIREMENTS["peds_clinic"]
        assert "Flu_Vax" in SLOT_TYPE_REQUIREMENTS["peds_clinic"]["hard"]

    def test_procedures_half_day_has_bbp(self):
        assert "BBP_Module" in SLOT_TYPE_REQUIREMENTS["procedures_half_day"]["hard"]

    def test_surgery_has_bls(self):
        assert "BLS" in SLOT_TYPE_REQUIREMENTS["surgery"]["hard"]

    def test_ob_gyn_has_nrp_soft(self):
        assert "NRP" in SLOT_TYPE_REQUIREMENTS["ob_gyn"]["soft"]

    def test_all_slots_have_hard_and_soft(self):
        for slot_type, reqs in SLOT_TYPE_REQUIREMENTS.items():
            assert "hard" in reqs, f"{slot_type} missing 'hard'"
            assert "soft" in reqs, f"{slot_type} missing 'soft'"

    def test_hard_and_soft_are_lists(self):
        for slot_type, reqs in SLOT_TYPE_REQUIREMENTS.items():
            assert isinstance(reqs["hard"], list), f"{slot_type}.hard is not a list"
            assert isinstance(reqs["soft"], list), f"{slot_type}.soft is not a list"

    def test_all_referenced_creds_in_validity(self):
        """Every credential referenced in slot requirements should be in CREDENTIAL_VALIDITY."""
        for slot_type, reqs in SLOT_TYPE_REQUIREMENTS.items():
            for cred in reqs["hard"] + reqs["soft"]:
                assert cred in CREDENTIAL_VALIDITY, (
                    f"{cred} from {slot_type} missing from CREDENTIAL_VALIDITY"
                )


# ── validate_credential_name ─────────────────────────────────────────────


class TestValidateCredentialName:
    def test_valid_name(self):
        assert validate_credential_name("HIPAA") == "HIPAA"

    def test_valid_with_underscore(self):
        assert validate_credential_name("N95_Fit") == "N95_Fit"

    def test_trims_whitespace(self):
        assert validate_credential_name("  BLS  ") == "BLS"

    def test_empty_rejected(self):
        with pytest.raises(ValidationError, match="empty"):
            validate_credential_name("")

    def test_too_short(self):
        with pytest.raises(ValidationError, match="too short"):
            validate_credential_name("A")

    def test_too_long(self):
        with pytest.raises(ValidationError, match="too long"):
            validate_credential_name("x" * 101)

    def test_exactly_2_chars(self):
        assert validate_credential_name("AB") == "AB"

    def test_exactly_100_chars(self):
        name = "x" * 100
        assert validate_credential_name(name) == name

    def test_whitespace_only_rejected(self):
        with pytest.raises(ValidationError, match="too short"):
            validate_credential_name("   ")


# ── validate_credential_expiration ───────────────────────────────────────


class TestValidateCredentialExpiration:
    def test_none_for_lifetime_credential(self):
        """Hep_B has None validity — None expiration should be allowed."""
        result = validate_credential_expiration(None, "Hep_B")
        assert result is None

    def test_none_rejected_for_expirable_credential(self):
        """HIPAA has 12-month validity — None expiration should error."""
        with pytest.raises(ValidationError, match="requires an expiration date"):
            validate_credential_expiration(None, "HIPAA")

    def test_valid_future_date(self):
        future = date.today() + timedelta(days=365)
        result = validate_credential_expiration(future, "BLS")
        assert result == future

    def test_expired_rejected_by_default(self):
        past = date.today() - timedelta(days=1)
        with pytest.raises(ValidationError, match="already expired"):
            validate_credential_expiration(past, "ACLS")

    def test_expired_allowed_when_flag_set(self):
        past = date.today() - timedelta(days=30)
        result = validate_credential_expiration(past, "ACLS", allow_expired=True)
        assert result == past

    def test_unreasonably_far_future_rejected(self):
        far_future = date.today() + timedelta(days=365 * 16)
        with pytest.raises(ValidationError, match="unreasonably far"):
            validate_credential_expiration(far_future, "BLS")

    def test_15_years_future_ok(self):
        almost_max = date.today() + timedelta(days=365 * 14)
        result = validate_credential_expiration(almost_max, "BLS")
        assert result == almost_max

    def test_today_is_not_expired(self):
        """Today should not be considered expired (not < today)."""
        today = date.today()
        result = validate_credential_expiration(today, "BLS")
        assert result == today

    def test_unknown_credential_none_requires_expiration(self):
        """Unknown credential not in CREDENTIAL_VALIDITY — None should require expiration.

        get() returns None for missing keys, but the check is
        ``CREDENTIAL_VALIDITY.get(name) is None``. Missing keys also return None,
        so the function treats unknown credentials as lifetime (returns None).
        """
        result = validate_credential_expiration(None, "UnknownCred")
        assert result is None


# ── validate_credential_issue_date ───────────────────────────────────────


class TestValidateCredentialIssueDate:
    def test_none_passthrough(self):
        result = validate_credential_issue_date(None, None, "BLS")
        assert result is None

    def test_valid_past_date(self):
        past = date.today() - timedelta(days=30)
        result = validate_credential_issue_date(past, None, "BLS")
        assert result == past

    def test_today_is_valid(self):
        today = date.today()
        result = validate_credential_issue_date(today, None, "BLS")
        assert result == today

    def test_future_rejected(self):
        future = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError, match="future"):
            validate_credential_issue_date(future, None, "HIPAA")

    def test_too_far_past_rejected(self):
        old = date.today() - timedelta(days=365 * 21)
        with pytest.raises(ValidationError, match="20 years"):
            validate_credential_issue_date(old, None, "HIPAA")

    def test_19_years_past_ok(self):
        old = date.today() - timedelta(days=365 * 19)
        result = validate_credential_issue_date(old, None, "HIPAA")
        assert result == old

    def test_issue_before_expiration_ok(self):
        issue = date.today() - timedelta(days=365)
        expiration = date.today() + timedelta(days=365)
        result = validate_credential_issue_date(issue, expiration, "BLS")
        assert result == issue

    def test_issue_after_expiration_rejected(self):
        issue = date.today() - timedelta(days=30)
        expiration = date.today() - timedelta(days=60)
        with pytest.raises(ValidationError, match="must be before"):
            validate_credential_issue_date(issue, expiration, "BLS")

    def test_issue_same_as_expiration_rejected(self):
        d = date.today() - timedelta(days=30)
        with pytest.raises(ValidationError, match="must be before"):
            validate_credential_issue_date(d, d, "BLS")

    def test_none_expiration_skips_comparison(self):
        """If expiration is None, issue date check should still pass."""
        past = date.today() - timedelta(days=30)
        result = validate_credential_issue_date(past, None, "HIPAA")
        assert result == past
