"""
API Response Transformers.

Handles transformation of API responses between different versions
to maintain backward compatibility while evolving the API.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.middleware.versioning.middleware import APIVersion, get_api_version

logger = logging.getLogger(__name__)


class ResponseTransformer(ABC):
    """
    Base class for API response transformers.

    Transformers convert response data from one API version format
    to another, enabling backward compatibility.
    """

    @abstractmethod
    def transform(self, data: Any, target_version: APIVersion) -> Any:
        """
        Transform response data to target version format.

        Args:
            data: Original response data
            target_version: Target API version

        Returns:
            Transformed data in target version format
        """
        pass

    @abstractmethod
    def supports_version(self, version: APIVersion) -> bool:
        """
        Check if this transformer supports a version.

        Args:
            version: API version to check

        Returns:
            True if version is supported
        """
        pass


class DateFormatTransformer(ResponseTransformer):
    """
    Transformer for date format changes between versions.

    V1: YYYY-MM-DD format
    V2+: ISO 8601 with timezone (YYYY-MM-DDTHH:MM:SSZ)
    """

    def transform(self, data: Any, target_version: APIVersion) -> Any:
        """
        Transform date formats based on version.

        Args:
            data: Response data (dict, list, or primitive)
            target_version: Target API version

        Returns:
            Data with transformed date formats
        """
        if isinstance(data, dict):
            return {
                key: self.transform(value, target_version)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self.transform(item, target_version) for item in data]
        elif isinstance(data, datetime):
            return self._transform_datetime(data, target_version)
        elif isinstance(data, date):
            return self._transform_date(data, target_version)
        else:
            return data

    def _transform_datetime(
        self,
        dt: datetime,
        target_version: APIVersion,
    ) -> str:
        """Transform datetime to version-appropriate format."""
        if target_version == APIVersion.V1:
            # V1: Simple date string
            return dt.strftime("%Y-%m-%d")
        else:
            # V2+: ISO 8601 with timezone
            return dt.isoformat()

    def _transform_date(self, d: date, target_version: APIVersion) -> str:
        """Transform date to version-appropriate format."""
        if target_version == APIVersion.V1:
            return d.strftime("%Y-%m-%d")
        else:
            # V2+: ISO 8601 date
            return d.isoformat()

    def supports_version(self, version: APIVersion) -> bool:
        """All versions supported."""
        return True


class PaginationTransformer(ResponseTransformer):
    """
    Transformer for pagination format changes.

    V1: Flat list response
    V2+: Wrapped response with metadata
    {
        "data": [...],
        "metadata": {
            "total": 100,
            "page": 1,
            "per_page": 20,
            "total_pages": 5
        }
    }
    """

    def transform(self, data: Any, target_version: APIVersion) -> Any:
        """
        Transform pagination format.

        Args:
            data: Response data
            target_version: Target API version

        Returns:
            Transformed pagination format
        """
        if target_version == APIVersion.V1:
            # V1: Return just the data array
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            return data
        else:
            # V2+: Wrap in metadata structure
            if isinstance(data, list):
                return {
                    "data": data,
                    "metadata": {
                        "total": len(data),
                        "page": 1,
                        "per_page": len(data),
                        "total_pages": 1,
                    },
                }
            return data

    def supports_version(self, version: APIVersion) -> bool:
        """All versions supported."""
        return True


class FieldRenameTransformer(ResponseTransformer):
    """
    Transformer for field name changes between versions.

    Handles field renames and deprecations while maintaining
    backward compatibility.
    """

    def __init__(self, field_mappings: dict[APIVersion, dict[str, str]]):
        """
        Initialize field rename transformer.

        Args:
            field_mappings: Mapping of version to field renames
                Example: {
                    APIVersion.V1: {"new_field": "old_field"},
                    APIVersion.V2: {"new_field": "new_field"},
                }
        """
        self.field_mappings = field_mappings

    def transform(self, data: Any, target_version: APIVersion) -> Any:
        """
        Transform field names based on version.

        Args:
            data: Response data
            target_version: Target API version

        Returns:
            Data with renamed fields
        """
        if not isinstance(data, dict):
            return data

        # Get field mapping for target version
        mapping = self.field_mappings.get(target_version, {})

        if not mapping:
            return data

        # Apply field renames
        transformed = {}
        for key, value in data.items():
            # Get target field name (or use original)
            target_key = mapping.get(key, key)

            # Recursively transform nested objects
            if isinstance(value, dict):
                transformed[target_key] = self.transform(value, target_version)
            elif isinstance(value, list):
                transformed[target_key] = [
                    self.transform(item, target_version)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                transformed[target_key] = value

        return transformed

    def supports_version(self, version: APIVersion) -> bool:
        """Check if version has field mappings."""
        return version in self.field_mappings


class TransformRegistry:
    """
    Registry for managing response transformers.

    Maintains a collection of transformers and applies them
    automatically based on API version.
    """

    def __init__(self):
        """Initialize transform registry."""
        self._transformers: dict[str, ResponseTransformer] = {}
        self._global_transformers: list[ResponseTransformer] = []

        # Register default transformers
        self._register_defaults()

    def _register_defaults(self):
        """Register default transformers."""
        # Date format transformer (global)
        self.register_global(DateFormatTransformer())

        # Pagination transformer (global)
        self.register_global(PaginationTransformer())

        # Example field renames
        assignment_field_mapping = {
            APIVersion.V1: {
                "person_id": "personId",  # V1 uses camelCase
                "block_id": "blockId",
                "rotation_id": "rotationId",
            },
            APIVersion.V2: {
                "person_id": "person_id",  # V2 uses snake_case
                "block_id": "block_id",
                "rotation_id": "rotation_id",
            },
        }
        self.register(
            "assignment",
            FieldRenameTransformer(assignment_field_mapping),
        )

    def register(self, name: str, transformer: ResponseTransformer):
        """
        Register a named transformer.

        Args:
            name: Transformer name (e.g., "assignment", "schedule")
            transformer: ResponseTransformer instance
        """
        self._transformers[name] = transformer
        logger.debug(f"Registered transformer: {name}")

    def register_global(self, transformer: ResponseTransformer):
        """
        Register a global transformer applied to all responses.

        Args:
            transformer: ResponseTransformer instance
        """
        self._global_transformers.append(transformer)
        logger.debug(f"Registered global transformer: {transformer.__class__.__name__}")

    def get(self, name: str) -> ResponseTransformer | None:
        """
        Get a named transformer.

        Args:
            name: Transformer name

        Returns:
            ResponseTransformer or None
        """
        return self._transformers.get(name)

    def transform(
        self,
        data: Any,
        target_version: APIVersion | None = None,
        transformer_name: str | None = None,
    ) -> Any:
        """
        Transform response data.

        Args:
            data: Response data to transform
            target_version: Target API version (defaults to current)
            transformer_name: Specific transformer to use (None = all global)

        Returns:
            Transformed data
        """
        if target_version is None:
            target_version = get_api_version()

        result = data

        # Apply specific transformer if requested
        if transformer_name:
            transformer = self.get(transformer_name)
            if transformer and transformer.supports_version(target_version):
                result = transformer.transform(result, target_version)
        else:
            # Apply all global transformers
            for transformer in self._global_transformers:
                if transformer.supports_version(target_version):
                    result = transformer.transform(result, target_version)

        return result

    def transform_pydantic(
        self,
        model: BaseModel,
        target_version: APIVersion | None = None,
        transformer_name: str | None = None,
    ) -> dict:
        """
        Transform Pydantic model to dict with version transformations.

        Args:
            model: Pydantic model instance
            target_version: Target API version
            transformer_name: Specific transformer to use

        Returns:
            Transformed dict representation
        """
        # Convert to dict
        data = model.model_dump()

        # Apply transformations
        return self.transform(data, target_version, transformer_name)


# Global transform registry instance
_transform_registry: TransformRegistry | None = None


def get_transform_registry() -> TransformRegistry:
    """
    Get global transform registry instance.

    Returns:
        Singleton TransformRegistry instance
    """
    global _transform_registry
    if _transform_registry is None:
        _transform_registry = TransformRegistry()
    return _transform_registry


def register_transformer(
    name: str,
    transformer: ResponseTransformer | None = None,
) -> Callable:
    """
    Decorator to register a transformer.

    Args:
        name: Transformer name
        transformer: ResponseTransformer instance (or use decorated class)

    Returns:
        Decorator function

    Usage:
        @register_transformer("custom")
        class CustomTransformer(ResponseTransformer):
            def transform(self, data, target_version):
                return data

            def supports_version(self, version):
                return True
    """

    def decorator(cls):
        if transformer is not None:
            instance = transformer
        else:
            instance = cls()

        registry = get_transform_registry()
        registry.register(name, instance)

        return cls

    return decorator


def transform_response(
    data: Any,
    version: APIVersion | None = None,
    transformer: str | None = None,
) -> Any:
    """
    Convenience function to transform response data.

    Args:
        data: Response data
        version: Target API version (defaults to current)
        transformer: Specific transformer name (None = global)

    Returns:
        Transformed data

    Usage:
        # Transform assignment data to current API version
        response_data = transform_response(assignment.model_dump())

        # Transform to specific version
        v1_data = transform_response(
            assignment.model_dump(),
            version=APIVersion.V1
        )

        # Use specific transformer
        custom_data = transform_response(
            data,
            transformer="custom"
        )
    """
    registry = get_transform_registry()
    return registry.transform(data, version, transformer)


# Version-aware response helpers


def version_aware_response(
    data: Any,
    transformer: str | None = None,
) -> Any:
    """
    Create version-aware response that auto-transforms based on request version.

    Args:
        data: Response data
        transformer: Optional specific transformer to use

    Returns:
        Transformed response data

    Usage:
        @app.get("/users")
        async def get_users():
            users = get_users_from_db()
            return version_aware_response(users)
    """
    return transform_response(data, transformer=transformer)


def backward_compatible_field(
    old_name: str,
    new_name: str,
    value: Any,
    min_version: APIVersion = APIVersion.V2,
) -> dict:
    """
    Create backward compatible field mapping.

    Returns dict with both old and new field names for transition period.

    Args:
        old_name: Old field name (V1)
        new_name: New field name (V2+)
        value: Field value
        min_version: Version where new name was introduced

    Returns:
        Dict with appropriate field name(s)

    Usage:
        current_version = get_api_version()
        response = {
            "id": user.id,
            **backward_compatible_field(
                "userName",
                "username",
                user.username,
                APIVersion.V2
            )
        }
    """
    current_version = get_api_version()

    if current_version < min_version:
        # Use old field name for older versions
        return {old_name: value}
    else:
        # Use new field name for newer versions
        # Optionally include old name during transition
        return {new_name: value}
