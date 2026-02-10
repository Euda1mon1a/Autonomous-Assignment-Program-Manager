"""PHI sanitization filter for Python logging.

Provides both a loguru patcher (primary) and a stdlib logging.Filter (for
any stdlib loggers that bypass the InterceptHandler bridge).

Patterns redacted: email addresses, SSNs, US phone numbers.
"""

import logging
import re

# Patterns to sanitize
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE_PATTERN = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")


def sanitize_text(text: str) -> str:
    """Redact PHI patterns from a string."""
    text = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)
    text = SSN_PATTERN.sub("[SSN_REDACTED]", text)
    text = PHONE_PATTERN.sub("[PHONE_REDACTED]", text)
    return text


def phi_patcher(record: dict) -> None:
    """Loguru patcher that sanitizes PHI from log messages.

    Applied via ``logger.patch(phi_patcher)`` so every message flowing
    through loguru is scrubbed before it reaches any sink.
    """
    msg = record.get("message")
    if isinstance(msg, str):
        record["message"] = sanitize_text(msg)


class PHIFilter(logging.Filter):
    """Stdlib logging.Filter that redacts PHI patterns from log records.

    Attach to any stdlib logger or handler that might bypass the loguru
    InterceptHandler bridge.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = sanitize_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: sanitize_text(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    sanitize_text(a) if isinstance(a, str) else a for a in record.args
                )
        return True
