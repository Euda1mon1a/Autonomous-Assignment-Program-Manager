"""
Request/response transformation for API gateway.

Provides transformation pipelines for modifying requests and responses.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from fastapi import Request, Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TransformationType(str, Enum):
    """Transformation type."""

    HEADER = "header"
    BODY = "body"
    QUERY = "query"
    PATH = "path"
    CUSTOM = "custom"


class TransformationOperation(str, Enum):
    """Transformation operation."""

    ADD = "add"
    REMOVE = "remove"
    RENAME = "rename"
    MAP = "map"
    FILTER = "filter"
    TRANSFORM = "transform"


class TransformationRule(BaseModel):
    """Configuration for a transformation rule."""

    name: str = Field(..., description="Unique name for the rule")
    type: TransformationType = Field(..., description="Type of transformation")
    operation: TransformationOperation = Field(..., description="Operation to perform")
    source_field: str | None = Field(
        default=None,
        description="Source field path (dot notation)",
    )
    target_field: str | None = Field(
        default=None,
        description="Target field path (dot notation)",
    )
    value: Any | None = Field(
        default=None,
        description="Value for add operation",
    )
    mapping: dict[str, str] | None = Field(
        default=None,
        description="Field mapping for rename/map operations",
    )
    filter_condition: str | None = Field(
        default=None,
        description="Filter condition (Python expression)",
    )
    enabled: bool = Field(default=True, description="Whether rule is enabled")

    class Config:
        use_enum_values = True


@dataclass
class TransformationContext:
    """Context for transformation operations."""

    request: Request | None = None
    response: Response | None = None
    metadata: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


class Transformer(ABC):
    """Base class for transformers."""

    @abstractmethod
    async def transform(self, data: Any, context: TransformationContext) -> Any:
        """
        Transform data.

        Args:
            data: Data to transform
            context: Transformation context

        Returns:
            Any: Transformed data
        """
        pass


class HeaderTransformer(Transformer):
    """Transformer for HTTP headers."""

    def __init__(self, rules: list[TransformationRule]) -> None:
        """
        Initialize header transformer.

        Args:
            rules: List of transformation rules
        """
        self.rules = [r for r in rules if r.type == TransformationType.HEADER]

    async def transform(
        self, headers: dict[str, str], context: TransformationContext
    ) -> dict[str, str]:
        """
        Transform headers.

        Args:
            headers: Headers to transform
            context: Transformation context

        Returns:
            dict: Transformed headers
        """
        result = headers.copy()

        for rule in self.rules:
            if not rule.enabled:
                continue

            if rule.operation == TransformationOperation.ADD:
                if rule.target_field and rule.value is not None:
                    result[rule.target_field] = str(rule.value)

            elif rule.operation == TransformationOperation.REMOVE:
                if rule.source_field:
                    result.pop(rule.source_field, None)

            elif rule.operation == TransformationOperation.RENAME:
                if rule.source_field and rule.target_field:
                    if rule.source_field in result:
                        result[rule.target_field] = result.pop(rule.source_field)

            elif rule.operation == TransformationOperation.MAP:
                if rule.mapping:
                    for old_key, new_key in rule.mapping.items():
                        if old_key in result:
                            result[new_key] = result.pop(old_key)

        return result


class BodyTransformer(Transformer):
    """Transformer for request/response body."""

    def __init__(self, rules: list[TransformationRule]) -> None:
        """
        Initialize body transformer.

        Args:
            rules: List of transformation rules
        """
        self.rules = [r for r in rules if r.type == TransformationType.BODY]

    async def transform(self, body: Any, context: TransformationContext) -> Any:
        """
        Transform body.

        Args:
            body: Body to transform
            context: Transformation context

        Returns:
            Any: Transformed body
        """
        if not isinstance(body, dict):
            return body

        result = body.copy()

        for rule in self.rules:
            if not rule.enabled:
                continue

            if rule.operation == TransformationOperation.ADD:
                if rule.target_field and rule.value is not None:
                    self._set_nested_value(result, rule.target_field, rule.value)

            elif rule.operation == TransformationOperation.REMOVE:
                if rule.source_field:
                    self._delete_nested_value(result, rule.source_field)

            elif rule.operation == TransformationOperation.RENAME:
                if rule.source_field and rule.target_field:
                    value = self._get_nested_value(result, rule.source_field)
                    if value is not None:
                        self._set_nested_value(result, rule.target_field, value)
                        self._delete_nested_value(result, rule.source_field)

            elif rule.operation == TransformationOperation.MAP:
                if rule.mapping:
                    for old_field, new_field in rule.mapping.items():
                        value = self._get_nested_value(result, old_field)
                        if value is not None:
                            self._set_nested_value(result, new_field, value)
                            self._delete_nested_value(result, old_field)

            elif rule.operation == TransformationOperation.FILTER:
                if rule.filter_condition and isinstance(result, list):
                    result = self._filter_list(result, rule.filter_condition)

        return result

    def _get_nested_value(self, obj: dict, path: str) -> Any:
        """
        Get nested value using dot notation.

        Args:
            obj: Object to search
            path: Dot-separated path

        Returns:
            Any: Value if found, None otherwise
        """
        keys = path.split(".")
        current = obj

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _set_nested_value(self, obj: dict, path: str, value: Any) -> None:
        """
        Set nested value using dot notation.

        Args:
            obj: Object to modify
            path: Dot-separated path
            value: Value to set
        """
        keys = path.split(".")
        current = obj

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _delete_nested_value(self, obj: dict, path: str) -> None:
        """
        Delete nested value using dot notation.

        Args:
            obj: Object to modify
            path: Dot-separated path
        """
        keys = path.split(".")
        current = obj

        for key in keys[:-1]:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return

        if isinstance(current, dict):
            current.pop(keys[-1], None)

    def _filter_list(self, items: list, condition: str) -> list:
        """
        Filter list using condition.

        Args:
            items: List to filter
            condition: Python expression (item variable available)

        Returns:
            list: Filtered list
        """
        try:
            return [item for item in items if eval(condition, {"item": item})]
        except Exception as e:
            logger.error(f"Error filtering list: {e}", exc_info=True)
            return items


class CustomTransformer(Transformer):
    """Custom transformer using user-defined function."""

    def __init__(
        self, transform_fn: Callable[[Any, TransformationContext], Any]
    ) -> None:
        """
        Initialize custom transformer.

        Args:
            transform_fn: Custom transformation function
        """
        self.transform_fn = transform_fn

    async def transform(self, data: Any, context: TransformationContext) -> Any:
        """
        Transform data using custom function.

        Args:
            data: Data to transform
            context: Transformation context

        Returns:
            Any: Transformed data
        """
        try:
            return await self.transform_fn(data, context)
        except Exception as e:
            logger.error(f"Error in custom transformation: {e}", exc_info=True)
            return data


class RequestTransformer:
    """
    Request transformer for API gateway.

    Transforms incoming requests before routing to services.
    """

    def __init__(self, rules: list[TransformationRule] | None = None) -> None:
        """
        Initialize request transformer.

        Args:
            rules: List of transformation rules
        """
        self.rules = rules or []
        self.header_transformer = HeaderTransformer(self.rules)
        self.body_transformer = BodyTransformer(self.rules)
        self.custom_transformers: list[CustomTransformer] = []
        logger.info(f"Request transformer initialized with {len(self.rules)} rules")

    def add_custom_transformer(
        self, transform_fn: Callable[[Any, TransformationContext], Any]
    ) -> None:
        """
        Add custom transformer.

        Args:
            transform_fn: Custom transformation function
        """
        self.custom_transformers.append(CustomTransformer(transform_fn))

    async def transform_request(
        self,
        request: Request,
        body: dict | None = None,
    ) -> tuple[dict[str, str], dict | None]:
        """
        Transform request.

        Args:
            request: FastAPI request object
            body: Request body (if already parsed)

        Returns:
            tuple: (transformed_headers, transformed_body)
        """
        context = TransformationContext(request=request)

        # Transform headers
        headers = dict(request.headers)
        transformed_headers = await self.header_transformer.transform(headers, context)

        # Transform body
        transformed_body = body
        if body is not None:
            transformed_body = await self.body_transformer.transform(body, context)

            # Apply custom transformers
            for transformer in self.custom_transformers:
                transformed_body = await transformer.transform(
                    transformed_body, context
                )

        return transformed_headers, transformed_body


class ResponseTransformer:
    """
    Response transformer for API gateway.

    Transforms responses from services before returning to client.
    """

    def __init__(self, rules: list[TransformationRule] | None = None) -> None:
        """
        Initialize response transformer.

        Args:
            rules: List of transformation rules
        """
        self.rules = rules or []
        self.header_transformer = HeaderTransformer(self.rules)
        self.body_transformer = BodyTransformer(self.rules)
        self.custom_transformers: list[CustomTransformer] = []
        logger.info(f"Response transformer initialized with {len(self.rules)} rules")

    def add_custom_transformer(
        self, transform_fn: Callable[[Any, TransformationContext], Any]
    ) -> None:
        """
        Add custom transformer.

        Args:
            transform_fn: Custom transformation function
        """
        self.custom_transformers.append(CustomTransformer(transform_fn))

    async def transform_response(
        self,
        headers: dict[str, str],
        body: Any,
        request: Request | None = None,
    ) -> tuple[dict[str, str], Any]:
        """
        Transform response.

        Args:
            headers: Response headers
            body: Response body
            request: Original request (for context)

        Returns:
            tuple: (transformed_headers, transformed_body)
        """
        context = TransformationContext(request=request)

        # Transform headers
        transformed_headers = await self.header_transformer.transform(headers, context)

        # Transform body
        transformed_body = body
        if body is not None:
            transformed_body = await self.body_transformer.transform(body, context)

            # Apply custom transformers
            for transformer in self.custom_transformers:
                transformed_body = await transformer.transform(
                    transformed_body, context
                )

        return transformed_headers, transformed_body


class TransformationPipeline:
    """
    Pipeline of transformations.

    Executes multiple transformations in sequence.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize transformation pipeline.

        Args:
            name: Pipeline name
        """
        self.name = name
        self.transformers: list[Transformer] = []
        logger.info(f"Transformation pipeline '{name}' initialized")

    def add_transformer(self, transformer: Transformer) -> None:
        """
        Add transformer to pipeline.

        Args:
            transformer: Transformer to add
        """
        self.transformers.append(transformer)

    async def execute(self, data: Any, context: TransformationContext) -> Any:
        """
        Execute pipeline on data.

        Args:
            data: Data to transform
            context: Transformation context

        Returns:
            Any: Transformed data
        """
        result = data

        for transformer in self.transformers:
            try:
                result = await transformer.transform(result, context)
            except Exception as e:
                logger.error(
                    f"Error in pipeline '{self.name}' transformer: {e}",
                    exc_info=True,
                )
                # Continue with other transformers

        return result
