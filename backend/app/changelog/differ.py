"""
API difference detection and breaking change analysis.

Compares OpenAPI schemas to detect:
- Breaking changes (removed/renamed endpoints, changed response types)
- Non-breaking changes (new endpoints, optional parameters)
- Deprecations
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Type of API change detected."""

    # Breaking changes (major version bump)
    ENDPOINT_REMOVED = "endpoint_removed"
    ENDPOINT_METHOD_REMOVED = "endpoint_method_removed"
    REQUIRED_PARAM_ADDED = "required_param_added"
    PARAM_REMOVED = "param_removed"
    PARAM_TYPE_CHANGED = "param_type_changed"
    RESPONSE_SCHEMA_CHANGED = "response_schema_changed"
    RESPONSE_STATUS_REMOVED = "response_status_removed"

    # Non-breaking changes (minor version bump)
    ENDPOINT_ADDED = "endpoint_added"
    ENDPOINT_METHOD_ADDED = "endpoint_method_added"
    OPTIONAL_PARAM_ADDED = "optional_param_added"
    RESPONSE_STATUS_ADDED = "response_status_added"
    RESPONSE_FIELD_ADDED = "response_field_added"

    # Patch changes (patch version bump)
    DESCRIPTION_CHANGED = "description_changed"
    EXAMPLE_CHANGED = "example_changed"
    DEPRECATED_ADDED = "deprecated_added"

    # Internal changes (no version bump needed)
    TAG_CHANGED = "tag_changed"
    INTERNAL_CHANGE = "internal_change"


@dataclass
class APIChange:
    """Represents a single API change."""

    change_type: ChangeType
    path: str
    method: str | None = None
    description: str = ""
    old_value: Any = None
    new_value: Any = None
    breaking: bool = False
    migration_guide: str | None = None

    def __post_init__(self) -> None:
        """Automatically determine if change is breaking."""
        self.breaking = self.change_type in {
            ChangeType.ENDPOINT_REMOVED,
            ChangeType.ENDPOINT_METHOD_REMOVED,
            ChangeType.REQUIRED_PARAM_ADDED,
            ChangeType.PARAM_REMOVED,
            ChangeType.PARAM_TYPE_CHANGED,
            ChangeType.RESPONSE_SCHEMA_CHANGED,
            ChangeType.RESPONSE_STATUS_REMOVED,
        }


@dataclass
class APIDiff:
    """Complete diff between two API versions."""

    old_version: str
    new_version: str
    changes: list[APIChange] = field(default_factory=list)

    @property
    def breaking_changes(self) -> list[APIChange]:
        """Get all breaking changes."""
        return [c for c in self.changes if c.breaking]

    @property
    def non_breaking_changes(self) -> list[APIChange]:
        """Get all non-breaking changes."""
        return [c for c in self.changes if not c.breaking]

    @property
    def has_breaking_changes(self) -> bool:
        """Check if any breaking changes exist."""
        return len(self.breaking_changes) > 0

    def suggest_version_bump(self, current_version: str = "1.0.0") -> str:
        """
        Suggest next version number based on semantic versioning.

        Args:
            current_version: Current version string (e.g., "1.0.0")

        Returns:
            Suggested next version
        """
        parts = current_version.split(".")
        if len(parts) != 3:
            logger.warning(f"Invalid version format: {current_version}, using 1.0.0")
            parts = ["1", "0", "0"]

        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        # Check for breaking changes (major bump)
        if self.has_breaking_changes:
            return f"{major + 1}.0.0"

            # Check for new features (minor bump)
        new_features = [
            c
            for c in self.changes
            if c.change_type
            in {
                ChangeType.ENDPOINT_ADDED,
                ChangeType.ENDPOINT_METHOD_ADDED,
                ChangeType.OPTIONAL_PARAM_ADDED,
                ChangeType.RESPONSE_STATUS_ADDED,
            }
        ]
        if new_features:
            return f"{major}.{minor + 1}.0"

            # Patch-level changes only
        if len(self.changes) > 0:
            return f"{major}.{minor}.{patch + 1}"

            # No changes
        return current_version


class APIDiffer:
    """
    Compares OpenAPI schemas and detects changes.

    Analyzes differences between two OpenAPI 3.x schemas to identify:
    - New, modified, and removed endpoints
    - Parameter changes
    - Response schema changes
    - Breaking vs non-breaking changes
    """

    def __init__(self) -> None:
        """Initialize the API differ."""
        self.changes: list[APIChange] = []

    def compare_schemas(
        self,
        old_schema: dict[str, Any],
        new_schema: dict[str, Any],
    ) -> APIDiff:
        """
        Compare two OpenAPI schemas.

        Args:
            old_schema: Previous OpenAPI schema
            new_schema: New OpenAPI schema

        Returns:
            APIDiff containing all detected changes
        """
        self.changes = []

        old_version = old_schema.get("info", {}).get("version", "unknown")
        new_version = new_schema.get("info", {}).get("version", "unknown")

        # Compare paths (endpoints)
        old_paths = old_schema.get("paths", {})
        new_paths = new_schema.get("paths", {})

        self._compare_paths(old_paths, new_paths)

        # Compare components (schemas, parameters, etc.)
        old_components = old_schema.get("components", {})
        new_components = new_schema.get("components", {})
        self._compare_components(old_components, new_components)

        return APIDiff(
            old_version=old_version,
            new_version=new_version,
            changes=self.changes,
        )

    def _compare_paths(
        self,
        old_paths: dict[str, Any],
        new_paths: dict[str, Any],
    ) -> None:
        """Compare API paths/endpoints."""
        all_paths = set(old_paths.keys()) | set(new_paths.keys())

        for path in sorted(all_paths):
            old_path_item = old_paths.get(path, {})
            new_path_item = new_paths.get(path, {})

            # Endpoint removed
            if path in old_paths and path not in new_paths:
                methods = [
                    m
                    for m in old_path_item.keys()
                    if m in {"get", "post", "put", "patch", "delete"}
                ]
                self.changes.append(
                    APIChange(
                        change_type=ChangeType.ENDPOINT_REMOVED,
                        path=path,
                        description=f"Endpoint {path} removed",
                        old_value=methods,
                        migration_guide="This endpoint has been removed. Please check the API documentation for alternative endpoints.",
                    )
                )
                continue

                # Endpoint added
            if path not in old_paths and path in new_paths:
                methods = [
                    m
                    for m in new_path_item.keys()
                    if m in {"get", "post", "put", "patch", "delete"}
                ]
                self.changes.append(
                    APIChange(
                        change_type=ChangeType.ENDPOINT_ADDED,
                        path=path,
                        description=f"New endpoint {path} added",
                        new_value=methods,
                    )
                )
                continue

                # Compare methods for this path
            self._compare_methods(path, old_path_item, new_path_item)

    def _compare_methods(
        self,
        path: str,
        old_path_item: dict[str, Any],
        new_path_item: dict[str, Any],
    ) -> None:
        """Compare HTTP methods for a specific path."""
        http_methods = {"get", "post", "put", "patch", "delete", "options", "head"}
        old_methods = set(old_path_item.keys()) & http_methods
        new_methods = set(new_path_item.keys()) & http_methods

        # Method removed (breaking)
        for method in old_methods - new_methods:
            self.changes.append(
                APIChange(
                    change_type=ChangeType.ENDPOINT_METHOD_REMOVED,
                    path=path,
                    method=method.upper(),
                    description=f"{method.upper()} {path} removed",
                    migration_guide=f"The {method.upper()} method for {path} is no longer available.",
                )
            )

            # Method added (non-breaking)
        for method in new_methods - old_methods:
            self.changes.append(
                APIChange(
                    change_type=ChangeType.ENDPOINT_METHOD_ADDED,
                    path=path,
                    method=method.upper(),
                    description=f"New {method.upper()} {path} endpoint",
                )
            )

            # Compare existing methods
        for method in old_methods & new_methods:
            old_operation = old_path_item[method]
            new_operation = new_path_item[method]
            self._compare_operation(path, method, old_operation, new_operation)

    def _compare_operation(
        self,
        path: str,
        method: str,
        old_op: dict[str, Any],
        new_op: dict[str, Any],
    ) -> None:
        """Compare a specific operation (method on a path)."""
        method_upper = method.upper()

        # Check deprecation
        if not old_op.get("deprecated") and new_op.get("deprecated"):
            self.changes.append(
                APIChange(
                    change_type=ChangeType.DEPRECATED_ADDED,
                    path=path,
                    method=method_upper,
                    description=f"{method_upper} {path} is now deprecated",
                )
            )

            # Compare parameters
        old_params = old_op.get("parameters", [])
        new_params = new_op.get("parameters", [])
        self._compare_parameters(path, method_upper, old_params, new_params)

        # Compare request body
        old_body = old_op.get("requestBody", {})
        new_body = new_op.get("requestBody", {})
        if old_body or new_body:
            self._compare_request_body(path, method_upper, old_body, new_body)

            # Compare responses
        old_responses = old_op.get("responses", {})
        new_responses = new_op.get("responses", {})
        self._compare_responses(path, method_upper, old_responses, new_responses)

        # Check description changes
        old_desc = old_op.get("description", "")
        new_desc = new_op.get("description", "")
        if old_desc != new_desc and old_desc and new_desc:
            self.changes.append(
                APIChange(
                    change_type=ChangeType.DESCRIPTION_CHANGED,
                    path=path,
                    method=method_upper,
                    description=f"Description updated for {method_upper} {path}",
                    old_value=old_desc[:100],
                    new_value=new_desc[:100],
                )
            )

    def _compare_parameters(
        self,
        path: str,
        method: str,
        old_params: list[dict[str, Any]],
        new_params: list[dict[str, Any]],
    ) -> None:
        """Compare operation parameters."""
        old_param_map = {p.get("name"): p for p in old_params}
        new_param_map = {p.get("name"): p for p in new_params}

        # Removed parameters (breaking)
        for name in set(old_param_map.keys()) - set(new_param_map.keys()):
            self.changes.append(
                APIChange(
                    change_type=ChangeType.PARAM_REMOVED,
                    path=path,
                    method=method,
                    description=f"Parameter '{name}' removed from {method} {path}",
                    old_value=old_param_map[name],
                    migration_guide=f"The parameter '{name}' is no longer accepted.",
                )
            )

            # Added parameters
        for name in set(new_param_map.keys()) - set(old_param_map.keys()):
            param = new_param_map[name]
            is_required = param.get("required", False)

            self.changes.append(
                APIChange(
                    change_type=(
                        ChangeType.REQUIRED_PARAM_ADDED
                        if is_required
                        else ChangeType.OPTIONAL_PARAM_ADDED
                    ),
                    path=path,
                    method=method,
                    description=f"{'Required' if is_required else 'Optional'} parameter '{name}' added to {method} {path}",
                    new_value=param,
                    migration_guide=(
                        f"You must now provide the '{name}' parameter."
                        if is_required
                        else None
                    ),
                )
            )

            # Changed parameters
        for name in set(old_param_map.keys()) & set(new_param_map.keys()):
            old_param = old_param_map[name]
            new_param = new_param_map[name]

            # Type changed (breaking)
            old_type = old_param.get("schema", {}).get("type")
            new_type = new_param.get("schema", {}).get("type")
            if old_type != new_type:
                self.changes.append(
                    APIChange(
                        change_type=ChangeType.PARAM_TYPE_CHANGED,
                        path=path,
                        method=method,
                        description=f"Parameter '{name}' type changed from {old_type} to {new_type}",
                        old_value=old_type,
                        new_value=new_type,
                        migration_guide=f"Update parameter '{name}' to use type {new_type}.",
                    )
                )

    def _compare_request_body(
        self,
        path: str,
        method: str,
        old_body: dict[str, Any],
        new_body: dict[str, Any],
    ) -> None:
        """Compare request body schemas."""
        old_required = old_body.get("required", False)
        new_required = new_body.get("required", False)

        # Body became required (breaking)
        if not old_required and new_required:
            self.changes.append(
                APIChange(
                    change_type=ChangeType.REQUIRED_PARAM_ADDED,
                    path=path,
                    method=method,
                    description=f"Request body is now required for {method} {path}",
                    migration_guide="You must now include a request body.",
                )
            )

    def _compare_responses(
        self,
        path: str,
        method: str,
        old_responses: dict[str, Any],
        new_responses: dict[str, Any],
    ) -> None:
        """Compare response definitions."""
        old_statuses = set(old_responses.keys())
        new_statuses = set(new_responses.keys())

        # Removed response status (breaking)
        for status in old_statuses - new_statuses:
            self.changes.append(
                APIChange(
                    change_type=ChangeType.RESPONSE_STATUS_REMOVED,
                    path=path,
                    method=method,
                    description=f"Response status {status} removed from {method} {path}",
                    old_value=status,
                    migration_guide=f"Status code {status} is no longer returned.",
                )
            )

            # Added response status (non-breaking)
        for status in new_statuses - old_statuses:
            self.changes.append(
                APIChange(
                    change_type=ChangeType.RESPONSE_STATUS_ADDED,
                    path=path,
                    method=method,
                    description=f"New response status {status} for {method} {path}",
                    new_value=status,
                )
            )

    def _compare_components(
        self,
        old_components: dict[str, Any],
        new_components: dict[str, Any],
    ) -> None:
        """Compare component schemas (models, parameters, etc.)."""
        # Compare schemas
        old_schemas = old_components.get("schemas", {})
        new_schemas = new_components.get("schemas", {})

        # This is a simplified comparison - could be expanded to check
        # for field removals, type changes, etc. within schemas
        removed_schemas = set(old_schemas.keys()) - set(new_schemas.keys())
        added_schemas = set(new_schemas.keys()) - set(old_schemas.keys())

        if removed_schemas:
            logger.debug(f"Removed schemas: {removed_schemas}")

        if added_schemas:
            logger.debug(f"Added schemas: {added_schemas}")
