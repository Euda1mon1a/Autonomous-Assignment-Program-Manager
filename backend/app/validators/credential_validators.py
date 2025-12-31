"""
Credential and certification validation functions.

Validates credentials, certifications, and qualifications:
- Credential expiration dates
- Required credentials for specific activities
- Certification renewals
- Procedural qualifications
- Training completions
"""

from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certification import Certification
from app.models.person import Person
from app.validators.common import ValidationError
from app.validators.date_validators import validate_date_not_null, validate_future_date

# Common credential types
REQUIRED_CREDENTIALS = {
    "annual_training": [
        "HIPAA",
        "Cyber_Training",
        "AUP",  # Acceptable Use Policy
    ],
    "safety": [
        "N95_Fit",
        "Chaperone",
        "BBP_Module",  # Bloodborne Pathogens
        "Sharps_Safety",
    ],
    "immunizations": [
        "Flu_Vax",
        "Tdap",
        "Hep_B",
    ],
    "procedures": [
        "BLS",  # Basic Life Support
        "ACLS",  # Advanced Cardiac Life Support
        "PALS",  # Pediatric Advanced Life Support
        "NRP",  # Neonatal Resuscitation Program
    ],
}

# Credential validity periods (in months)
CREDENTIAL_VALIDITY = {
    "HIPAA": 12,
    "Cyber_Training": 12,
    "AUP": 12,
    "N95_Fit": 12,
    "Chaperone": 24,
    "BBP_Module": 12,
    "Sharps_Safety": 12,
    "Flu_Vax": 12,
    "Tdap": 120,  # 10 years
    "Hep_B": None,  # Lifetime
    "BLS": 24,
    "ACLS": 24,
    "PALS": 24,
    "NRP": 24,
}

# Slot type credential requirements
SLOT_TYPE_REQUIREMENTS = {
    "inpatient_call": {
        "hard": ["HIPAA", "Cyber_Training", "AUP", "Chaperone", "N95_Fit"],
        "soft": [],
    },
    "peds_clinic": {
        "hard": ["Flu_Vax", "Tdap"],
        "soft": ["PALS"],
    },
    "procedures_half_day": {
        "hard": ["BBP_Module", "Sharps_Safety"],
        "soft": ["BLS", "ACLS"],
    },
    "surgery": {
        "hard": ["BBP_Module", "Sharps_Safety", "BLS"],
        "soft": ["ACLS"],
    },
    "ob_gyn": {
        "hard": ["BBP_Module", "Sharps_Safety", "BLS"],
        "soft": ["ACLS", "NRP"],
    },
}


def validate_credential_name(credential_name: str) -> str:
    """
    Validate credential name format.

    Args:
        credential_name: Credential name to validate

    Returns:
        str: Validated credential name

    Raises:
        ValidationError: If credential name is invalid
    """
    if not credential_name:
        raise ValidationError("Credential name cannot be empty")

    # Trim and check length
    name = credential_name.strip()
    if len(name) < 2:
        raise ValidationError(f"Credential name too short: '{name}'")

    if len(name) > 100:
        raise ValidationError(f"Credential name too long: '{name}' (max 100 characters)")

    return name


def validate_credential_expiration(
    expiration_date: date | None,
    credential_name: str,
    allow_expired: bool = False,
) -> date | None:
    """
    Validate credential expiration date.

    Args:
        expiration_date: Expiration date to validate
        credential_name: Name of credential (for context)
        allow_expired: Allow already-expired credentials

    Returns:
        date | None: Validated expiration date (None for lifetime credentials)

    Raises:
        ValidationError: If expiration date is invalid
    """
    # Some credentials don't expire (e.g., Hep B)
    if expiration_date is None:
        if CREDENTIAL_VALIDITY.get(credential_name) is None:
            return None
        # If credential should have expiration but doesn't, that's an error
        raise ValidationError(
            f"Credential '{credential_name}' requires an expiration date"
        )

    # Validate date format
    validated_date = validate_date_not_null(expiration_date, "Credential expiration date")

    # Check if already expired
    if not allow_expired:
        today = date.today()
        if validated_date < today:
            raise ValidationError(
                f"Credential '{credential_name}' is already expired: {validated_date}"
            )

    # Check if expiration is unreasonably far in the future
    max_future = date.today() + timedelta(days=365 * 15)  # 15 years max
    if validated_date > max_future:
        raise ValidationError(
            f"Credential expiration date ({validated_date}) is unreasonably far in the future"
        )

    return validated_date


def validate_credential_issue_date(
    issue_date: date | None,
    expiration_date: date | None,
    credential_name: str,
) -> date | None:
    """
    Validate credential issue date.

    Args:
        issue_date: Issue date to validate
        expiration_date: Expiration date (must be after issue date)
        credential_name: Name of credential

    Returns:
        date | None: Validated issue date

    Raises:
        ValidationError: If issue date is invalid
    """
    if issue_date is None:
        return None

    validated_date = validate_date_not_null(issue_date, "Credential issue date")

    # Issue date should not be in the future
    today = date.today()
    if validated_date > today:
        raise ValidationError(
            f"Credential issue date ({validated_date}) cannot be in the future"
        )

    # Issue date should not be too far in the past (> 20 years)
    min_date = today - timedelta(days=365 * 20)
    if validated_date < min_date:
        raise ValidationError(
            f"Credential issue date ({validated_date}) is more than 20 years in the past"
        )

    # If expiration date provided, issue date must be before it
    if expiration_date is not None:
        if validated_date >= expiration_date:
            raise ValidationError(
                f"Credential issue date ({validated_date}) must be before "
                f"expiration date ({expiration_date})"
            )

    return validated_date


async def validate_person_has_credential(
    db: AsyncSession,
    person_id: UUID,
    credential_name: str,
    check_expiration: bool = True,
    grace_period_days: int = 0,
) -> dict:
    """
    Validate that a person has a specific credential.

    Args:
        db: Database session
        person_id: Person ID to check
        credential_name: Name of required credential
        check_expiration: Check if credential is expired
        grace_period_days: Allow credentials expiring within this many days

    Returns:
        dict: Validation result with credential status

    Raises:
        ValidationError: If person not found
    """
    # Get person
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    if not person:
        raise ValidationError(f"Person not found: {person_id}")

    # Get credential
    result = await db.execute(
        select(Certification).where(
            Certification.person_id == person_id,
            Certification.certification_type == credential_name,
        )
    )
    credential = result.scalar_one_or_none()

    # Check if credential exists
    if not credential:
        return {
            "has_credential": False,
            "is_valid": False,
            "credential_name": credential_name,
            "person_id": str(person_id),
            "person_name": person.name,
            "message": f"{person.name} does not have required credential: {credential_name}",
        }

    # Check expiration if requested
    if check_expiration and credential.expires_at is not None:
        today = date.today()
        grace_date = today + timedelta(days=grace_period_days)

        if credential.expires_at < today:
            return {
                "has_credential": True,
                "is_valid": False,
                "credential_name": credential_name,
                "person_id": str(person_id),
                "person_name": person.name,
                "expires_at": credential.expires_at.isoformat(),
                "days_expired": (today - credential.expires_at).days,
                "message": f"{person.name}: {credential_name} expired on {credential.expires_at}",
            }

        if credential.expires_at < grace_date:
            days_until_expiration = (credential.expires_at - today).days
            return {
                "has_credential": True,
                "is_valid": True,
                "is_expiring_soon": True,
                "credential_name": credential_name,
                "person_id": str(person_id),
                "person_name": person.name,
                "expires_at": credential.expires_at.isoformat(),
                "days_until_expiration": days_until_expiration,
                "message": f"{person.name}: {credential_name} expires in {days_until_expiration} days",
            }

    # Credential is valid
    return {
        "has_credential": True,
        "is_valid": True,
        "is_expiring_soon": False,
        "credential_name": credential_name,
        "person_id": str(person_id),
        "person_name": person.name,
        "expires_at": credential.expires_at.isoformat() if credential.expires_at else None,
    }


async def validate_slot_type_credentials(
    db: AsyncSession,
    person_id: UUID,
    slot_type: str,
    check_date: date,
) -> dict:
    """
    Validate that a person has all required credentials for a slot type.

    Args:
        db: Database session
        person_id: Person ID to check
        slot_type: Slot type (e.g., 'inpatient_call', 'peds_clinic')
        check_date: Date to check credentials validity

    Returns:
        dict: Validation result with credential status
    """
    requirements = SLOT_TYPE_REQUIREMENTS.get(slot_type, {"hard": [], "soft": []})
    hard_requirements = requirements["hard"]
    soft_requirements = requirements["soft"]

    hard_violations = []
    soft_warnings = []

    # Check hard requirements
    for credential_name in hard_requirements:
        result = await validate_person_has_credential(
            db, person_id, credential_name, check_expiration=True
        )
        if not result["is_valid"]:
            hard_violations.append(result)

    # Check soft requirements (warnings only)
    for credential_name in soft_requirements:
        result = await validate_person_has_credential(
            db, person_id, credential_name, check_expiration=True
        )
        if not result["is_valid"]:
            soft_warnings.append(result)

    # Get person
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()

    return {
        "person_id": str(person_id),
        "person_name": person.name if person else "Unknown",
        "slot_type": slot_type,
        "check_date": check_date.isoformat(),
        "is_eligible": len(hard_violations) == 0,
        "hard_requirements_met": len(hard_requirements) - len(hard_violations),
        "hard_requirements_total": len(hard_requirements),
        "hard_violations": hard_violations,
        "soft_warnings": soft_warnings,
        "penalty_score": len(soft_warnings) * 3,  # 3 points per missing soft requirement
    }


async def get_expiring_credentials(
    db: AsyncSession,
    person_id: UUID | None = None,
    days_threshold: int = 30,
) -> list[dict]:
    """
    Get list of credentials expiring within threshold.

    Args:
        db: Database session
        person_id: Optional person ID (None for all people)
        days_threshold: Number of days to look ahead (default: 30)

    Returns:
        list[dict]: List of expiring credentials
    """
    today = date.today()
    threshold_date = today + timedelta(days=days_threshold)

    # Build query
    query = select(Certification).join(Person).where(
        Certification.expires_at.isnot(None),
        Certification.expires_at >= today,
        Certification.expires_at <= threshold_date,
    )

    if person_id is not None:
        query = query.where(Certification.person_id == person_id)

    result = await db.execute(query)
    certifications = result.scalars().all()

    expiring = []
    for cert in certifications:
        days_remaining = (cert.expires_at - today).days
        expiring.append(
            {
                "person_id": str(cert.person_id),
                "person_name": cert.person.name,
                "credential_name": cert.certification_type,
                "expires_at": cert.expires_at.isoformat(),
                "days_remaining": days_remaining,
                "urgency": "critical" if days_remaining <= 7 else "warning",
            }
        )

    return expiring


async def validate_credential_update(
    db: AsyncSession,
    person_id: UUID,
    credential_name: str,
    new_expiration_date: date,
    issue_date: date | None = None,
) -> dict:
    """
    Validate credential update/renewal.

    Args:
        db: Database session
        person_id: Person ID
        credential_name: Credential being updated
        new_expiration_date: New expiration date
        issue_date: Optional new issue date

    Returns:
        dict: Validation result

    Raises:
        ValidationError: If update is invalid
    """
    # Validate dates
    validated_name = validate_credential_name(credential_name)
    validated_expiration = validate_credential_expiration(
        new_expiration_date, validated_name, allow_expired=False
    )
    validated_issue = validate_credential_issue_date(
        issue_date, validated_expiration, validated_name
    )

    # Get existing credential
    result = await db.execute(
        select(Certification).where(
            Certification.person_id == person_id,
            Certification.certification_type == validated_name,
        )
    )
    existing = result.scalar_one_or_none()

    # Check if this is an extension of existing credential
    is_renewal = False
    if existing and existing.expires_at:
        # Should be close to expiration or within renewal window
        renewal_window_start = existing.expires_at - timedelta(days=90)  # 90 days before
        today = date.today()

        if today >= renewal_window_start:
            is_renewal = True

    return {
        "person_id": str(person_id),
        "credential_name": validated_name,
        "new_expiration_date": validated_expiration.isoformat(),
        "issue_date": validated_issue.isoformat() if validated_issue else None,
        "is_renewal": is_renewal,
        "is_valid": True,
    }
