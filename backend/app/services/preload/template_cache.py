"""Rotation template lookup with multi-candidate search and caching."""

from __future__ import annotations

from sqlalchemy import select, or_, case
from sqlalchemy.orm import Session, selectinload

from app.models.rotation_template import RotationTemplate


class TemplateCache:
    """Cached rotation-template lookup with 9-candidate search.

    Candidates are tried in priority order:
    1. PGY-specific variant (e.g. ``FMIT-PGY2``)
    2. Alias variants (e.g. ``PEDSW`` for ``PEDW``)
    3. Exact abbreviation
    4. Wildcard fallback (e.g. ``FMIT-%``)
    """

    # Alias variants for common abbreviations
    _ALIAS_MAP: dict[str, list[str]] = {
        "PEDW": ["PEDSW", "PEDS-W"],
        "PEDNF": ["PNF"],
        "LDNF": ["NF-LD"],
        "KAP": ["KAP-LD"],
    }

    # Wildcard patterns for PGY-agnostic fallback
    _WILDCARD_MAP: dict[str, str] = {
        "FMIT": "FMIT-%",
        "IM": "IM-PGY%",
        "PEDW": "PEDS-WARD-%",
        "PEDNF": "NF-PEDS-%",
        "KAP": "KAPI-LD-%",
    }

    def __init__(self, session: Session) -> None:
        self.session = session
        self._cache: dict[str, RotationTemplate | None] = {}

    def get(
        self,
        rotation_type: object,
        person: object = None,
    ) -> RotationTemplate | None:
        """Look up RotationTemplate by rotation_type abbreviation (cached)."""
        if rotation_type is None:
            return None

        abbrev = (
            (
                rotation_type.value
                if hasattr(rotation_type, "value")
                else (rotation_type or "")
            )
            .strip()
            .upper()
        )
        if not abbrev:
            return None

        pgy_level = (
            getattr(person, "pgy_level", None)
            if getattr(person, "type", None) == "resident"
            else None
        )
        cache_key = f"{abbrev}:{pgy_level}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        candidates: list[str] = []

        # PGY-specific variants
        if pgy_level:
            if abbrev == "FMIT":
                candidates.append(f"FMIT-PGY{pgy_level}")
            if abbrev == "IM":
                candidates.append(f"IM-PGY{pgy_level}")
            if abbrev == "PEDW":
                candidates.append(f"PEDS-WARD-PGY{pgy_level}")
            if abbrev == "PEDNF":
                candidates.append(f"NF-PEDS-PGY{pgy_level}")
            if abbrev == "KAP" and pgy_level == 1:
                candidates.append("KAPI-LD-PGY1")

        # Alias variants
        candidates.extend(self._ALIAS_MAP.get(abbrev, []))
        # Exact abbreviation
        candidates.append(abbrev)
        # Wildcard fallback
        if abbrev in self._WILDCARD_MAP:
            candidates.append(self._WILDCARD_MAP[abbrev])

        template = None
        for candidate in candidates:
            stmt = (
                select(RotationTemplate)
                .options(selectinload(RotationTemplate.weekly_patterns))
                .where(
                    or_(
                        RotationTemplate.abbreviation.ilike(candidate),
                        RotationTemplate.display_abbreviation.ilike(candidate),
                    )
                )
                .order_by(
                    case(
                        (RotationTemplate.abbreviation.ilike(candidate), 0),
                        else_=1,
                    )
                )
                .limit(1)
            )
            result = self.session.execute(stmt)
            template = result.scalars().first()
            if template:
                break

        self._cache[cache_key] = template
        return template
