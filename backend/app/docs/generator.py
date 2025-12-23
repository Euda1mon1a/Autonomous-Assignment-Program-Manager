"""
Main documentation generator.

Orchestrates the generation of comprehensive API documentation including
enhanced OpenAPI schemas, Markdown documentation, and code examples.
"""

import json
from typing import Any

from fastapi import FastAPI

from app.docs.templates.markdown_generator import MarkdownGenerator
from app.docs.templates.openapi_enhancements import OpenAPIEnhancer


class DocumentationGenerator:
    """
    Main documentation generator for the Residency Scheduler API.

    Coordinates OpenAPI enhancement and Markdown generation to produce
    comprehensive, developer-friendly API documentation.
    """

    def __init__(self, app: FastAPI):
        """
        Initialize the documentation generator.

        Args:
            app: FastAPI application instance
        """
        self.app = app
        self.enhancer = OpenAPIEnhancer()
        self._initialize_enhancer()

    def _initialize_enhancer(self) -> None:
        """Initialize the OpenAPI enhancer with default examples and settings."""
        self.enhancer.initialize_default_examples()

        # Add additional custom examples for key endpoints
        self._add_schedule_examples()
        self._add_assignment_examples()
        self._add_swap_examples()
        self._add_leave_examples()

    def _add_schedule_examples(self) -> None:
        """Add examples for schedule-related endpoints."""
        # Schedule generation request
        self.enhancer.add_example(
            "/api/v1/schedule/generate",
            "post",
            "request",
            {
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "constraints": {
                    "enforce_acgme": True,
                    "max_consecutive_days": 6,
                    "min_faculty_per_block": 2,
                },
                "preferences": {"balance_workload": True, "respect_time_off": True},
            },
        )

        # Schedule generation response
        self.enhancer.add_example(
            "/api/v1/schedule/generate",
            "post",
            "response",
            {
                "schedule_id": "550e8400-e29b-41d4-a716-446655440001",
                "status": "completed",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "assignments_created": 1460,
                "acgme_compliant": True,
                "conflicts": [],
                "warnings": [],
                "generated_at": "2025-12-20T10:00:00Z",
            },
        )

    def _add_assignment_examples(self) -> None:
        """Add examples for assignment-related endpoints."""
        # Create assignment
        self.enhancer.add_example(
            "/api/v1/assignments",
            "post",
            "request",
            {
                "person_id": "550e8400-e29b-41d4-a716-446655440000",
                "block_id": "550e8400-e29b-41d4-a716-446655440002",
                "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
                "notes": "Primary assignment for clinic rotation",
            },
        )

        self.enhancer.add_example(
            "/api/v1/assignments",
            "post",
            "response",
            {
                "id": "550e8400-e29b-41d4-a716-446655440004",
                "person_id": "550e8400-e29b-41d4-a716-446655440000",
                "block_id": "550e8400-e29b-41d4-a716-446655440002",
                "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
                "notes": "Primary assignment for clinic rotation",
                "created_at": "2025-12-20T10:00:00Z",
                "updated_at": "2025-12-20T10:00:00Z",
            },
        )

    def _add_swap_examples(self) -> None:
        """Add examples for swap-related endpoints."""
        # Create swap request
        self.enhancer.add_example(
            "/api/v1/swaps",
            "post",
            "request",
            {
                "requester_assignment_id": "550e8400-e29b-41d4-a716-446655440005",
                "target_assignment_id": "550e8400-e29b-41d4-a716-446655440006",
                "swap_type": "ONE_TO_ONE",
                "reason": "Personal commitment on original date",
                "notes": "Willing to take any equivalent shift in exchange",
            },
        )

        self.enhancer.add_example(
            "/api/v1/swaps",
            "post",
            "response",
            {
                "id": "550e8400-e29b-41d4-a716-446655440007",
                "requester_assignment_id": "550e8400-e29b-41d4-a716-446655440005",
                "target_assignment_id": "550e8400-e29b-41d4-a716-446655440006",
                "swap_type": "ONE_TO_ONE",
                "status": "PENDING",
                "reason": "Personal commitment on original date",
                "notes": "Willing to take any equivalent shift in exchange",
                "created_at": "2025-12-20T10:00:00Z",
                "expires_at": "2025-12-27T10:00:00Z",
            },
        )

    def _add_leave_examples(self) -> None:
        """Add examples for leave-related endpoints."""
        # Create leave request
        self.enhancer.add_example(
            "/api/v1/leave",
            "post",
            "request",
            {
                "person_id": "550e8400-e29b-41d4-a716-446655440000",
                "leave_type": "VACATION",
                "start_date": "2025-03-15",
                "end_date": "2025-03-22",
                "reason": "Family vacation",
                "emergency": False,
            },
        )

        self.enhancer.add_example(
            "/api/v1/leave",
            "post",
            "response",
            {
                "id": "550e8400-e29b-41d4-a716-446655440008",
                "person_id": "550e8400-e29b-41d4-a716-446655440000",
                "leave_type": "VACATION",
                "start_date": "2025-03-15",
                "end_date": "2025-03-22",
                "reason": "Family vacation",
                "emergency": False,
                "status": "PENDING",
                "created_at": "2025-12-20T10:00:00Z",
                "coverage_assignments": [],
            },
        )

    def get_enhanced_openapi_schema(self) -> dict[str, Any]:
        """
        Get enhanced OpenAPI schema with examples and metadata.

        Returns:
            Enhanced OpenAPI schema dictionary
        """
        return self.enhancer.enhance_schema(self.app)

    def get_markdown_documentation(self) -> str:
        """
        Get complete Markdown documentation.

        Returns:
            Complete Markdown documentation as string
        """
        schema = self.get_enhanced_openapi_schema()
        generator = MarkdownGenerator(schema)
        return generator.generate_full_documentation()

    def get_endpoint_documentation(
        self, path: str, method: str, format: str = "markdown"
    ) -> str:
        """
        Get documentation for a specific endpoint.

        Args:
            path: API path (e.g., "/api/v1/people")
            method: HTTP method (e.g., "get", "post")
            format: Output format ("markdown" or "json")

        Returns:
            Documentation in the requested format
        """
        schema = self.get_enhanced_openapi_schema()

        if format == "json":
            # Return raw OpenAPI operation
            path_item = schema.get("paths", {}).get(path, {})
            operation = path_item.get(method.lower(), {})
            return json.dumps(operation, indent=2)
        else:
            # Return Markdown documentation
            generator = MarkdownGenerator(schema)
            return generator.generate_endpoint_specific_doc(path, method)

    def get_code_examples(
        self, path: str, method: str, language: str | None = None
    ) -> dict[str, str]:
        """
        Get code examples for an endpoint.

        Args:
            path: API path
            method: HTTP method
            language: Specific language to return (None for all)

        Returns:
            Dictionary of language -> code example
        """
        examples = self.enhancer.get_code_examples(path, method)

        if language:
            return {language: examples.get(language, "")}

        return examples

    def get_error_documentation(self) -> dict[str, Any]:
        """
        Get comprehensive error code documentation.

        Returns:
            Dictionary of error codes and their documentation
        """
        schema = self.get_enhanced_openapi_schema()
        return schema.get("components", {}).get("x-error-codes", {})

    def get_changelog(self) -> str:
        """
        Get API changelog in Markdown format.

        Returns:
            Changelog as Markdown string
        """
        schema = self.get_enhanced_openapi_schema()
        generator = MarkdownGenerator(schema)
        return generator._generate_changelog()

    def get_version_info(self) -> dict[str, Any]:
        """
        Get API versioning information.

        Returns:
            Dictionary with versioning details
        """
        schema = self.get_enhanced_openapi_schema()
        return schema.get("x-api-version", {})

    def export_openapi_json(self, filepath: str) -> None:
        """
        Export enhanced OpenAPI schema to JSON file.

        Args:
            filepath: Path to output file
        """
        schema = self.get_enhanced_openapi_schema()
        with open(filepath, "w") as f:
            json.dump(schema, f, indent=2)

    def export_markdown_docs(self, filepath: str) -> None:
        """
        Export complete Markdown documentation to file.

        Args:
            filepath: Path to output file
        """
        docs = self.get_markdown_documentation()
        with open(filepath, "w") as f:
            f.write(docs)

    def get_stats(self) -> dict[str, Any]:
        """
        Get documentation statistics.

        Returns:
            Dictionary with statistics about the API documentation
        """
        schema = self.get_enhanced_openapi_schema()
        paths = schema.get("paths", {})

        total_endpoints = 0
        methods_count = {"get": 0, "post": 0, "put": 0, "patch": 0, "delete": 0}
        tags = set()

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method in path_item:
                    total_endpoints += 1
                    methods_count[method] += 1

                    operation = path_item[method]
                    operation_tags = operation.get("tags", [])
                    tags.update(operation_tags)

        return {
            "total_endpoints": total_endpoints,
            "methods": methods_count,
            "tags": sorted(list(tags)),
            "total_tags": len(tags),
            "schemas": len(schema.get("components", {}).get("schemas", {})),
            "error_codes": len(schema.get("components", {}).get("x-error-codes", {})),
            "security_schemes": len(
                schema.get("components", {}).get("securitySchemes", {})
            ),
        }
