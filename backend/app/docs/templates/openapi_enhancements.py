"""
OpenAPI schema enhancements.

Provides utilities for enhancing OpenAPI schemas with additional metadata,
examples, and documentation.
"""

from typing import Any

from fastapi.openapi.utils import get_openapi


class OpenAPIEnhancer:
    """Enhances OpenAPI schemas with additional documentation and examples."""

    def __init__(self) -> None:
        """Initialize the OpenAPI enhancer."""
        self.custom_examples: dict[str, dict[str, Any]] = {}
        self.error_codes: dict[str, dict[str, str]] = {}
        self.security_schemes: dict[str, dict[str, Any]] = {}

    def add_example(
        self, path: str, method: str, example_type: str, example_data: dict[str, Any]
    ) -> None:
        """
        Add a custom example for a specific endpoint.

        Args:
            path: API path (e.g., "/api/v1/people")
            method: HTTP method (e.g., "get", "post")
            example_type: Type of example ("request" or "response")
            example_data: Example data dictionary
        """
        key = f"{method.upper()}:{path}"
        if key not in self.custom_examples:
            self.custom_examples[key] = {}
        self.custom_examples[key][example_type] = example_data

    def add_error_code(
        self,
        code: str,
        title: str,
        description: str,
        example: dict[str, Any] | None = None,
    ) -> None:
        """
        Add documentation for an error code.

        Args:
            code: HTTP status code or custom error code
            title: Short title for the error
            description: Detailed description
            example: Optional example error response
        """
        self.error_codes[code] = {
            "title": title,
            "description": description,
            "example": example or {},
        }

    def add_security_scheme(
        self, name: str, scheme_type: str, description: str, **kwargs
    ) -> None:
        """
        Add a custom security scheme.

        Args:
            name: Name of the security scheme
            scheme_type: Type (e.g., "http", "apiKey", "oauth2")
            description: Description of the scheme
            **kwargs: Additional scheme parameters
        """
        self.security_schemes[name] = {
            "type": scheme_type,
            "description": description,
            **kwargs,
        }

    def enhance_schema(self, app) -> dict[str, Any]:
        """
        Generate enhanced OpenAPI schema.

        Args:
            app: FastAPI application instance

        Returns:
            Enhanced OpenAPI schema dictionary
        """
        # Get base OpenAPI schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add custom information
        openapi_schema["info"]["x-api-id"] = "residency-scheduler-api"
        openapi_schema["info"]["x-audience"] = "internal"
        openapi_schema["info"]["contact"] = {
            "name": "API Support",
            "email": "api-support@example.com",
        }
        openapi_schema["info"]["license"] = {
            "name": "Proprietary",
            "url": "https://example.com/license",
        }

        # Add server information
        openapi_schema["servers"] = [
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.example.com", "description": "Production server"},
        ]

        # Add custom security schemes
        if self.security_schemes:
            if "components" not in openapi_schema:
                openapi_schema["components"] = {}
            if "securitySchemes" not in openapi_schema["components"]:
                openapi_schema["components"]["securitySchemes"] = {}
            openapi_schema["components"]["securitySchemes"].update(
                self.security_schemes
            )

            # Add JWT bearer auth by default
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "securitySchemes" not in openapi_schema["components"]:
            openapi_schema["components"]["securitySchemes"] = {}

        openapi_schema["components"]["securitySchemes"]["bearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /api/v1/auth/login endpoint",
        }

        # Enhance paths with custom examples
        if "paths" in openapi_schema:
            for path, path_item in openapi_schema["paths"].items():
                for method, operation in path_item.items():
                    if method not in ["get", "post", "put", "patch", "delete"]:
                        continue

                    key = f"{method.upper()}:{path}"
                    if key in self.custom_examples:
                        # Add request examples
                        if "request" in self.custom_examples[key]:
                            if "requestBody" in operation:
                                if "content" in operation["requestBody"]:
                                    for content_type in operation["requestBody"][
                                        "content"
                                    ]:
                                        operation["requestBody"]["content"][
                                            content_type
                                        ]["example"] = self.custom_examples[key][
                                            "request"
                                        ]

                                        # Add response examples
                        if "response" in self.custom_examples[key]:
                            if "responses" in operation:
                                for status_code in operation["responses"]:
                                    if "content" in operation["responses"][status_code]:
                                        for content_type in operation["responses"][
                                            status_code
                                        ]["content"]:
                                            operation["responses"][status_code][
                                                "content"
                                            ][content_type][
                                                "example"
                                            ] = self.custom_examples[key]["response"]

                                            # Add error codes documentation
        if self.error_codes:
            if "components" not in openapi_schema:
                openapi_schema["components"] = {}
            openapi_schema["components"]["x-error-codes"] = self.error_codes

            # Add API versioning information
        openapi_schema["x-api-version"] = {
            "current": "v1",
            "supported": ["v1"],
            "deprecated": [],
            "sunset": [],
        }

        # Add rate limiting information
        openapi_schema["x-rate-limits"] = {
            "login": {"limit": 5, "window": "60 seconds", "scope": "per IP address"},
            "registration": {
                "limit": 3,
                "window": "60 seconds",
                "scope": "per IP address",
            },
            "default": {"limit": 100, "window": "60 seconds", "scope": "per user"},
        }

        # Add compliance information
        openapi_schema["x-compliance"] = {
            "acgme": {
                "enabled": True,
                "rules": ["80-hour work week", "1-in-7 day off", "Supervision ratios"],
            },
            "security": {
                "authentication": "JWT",
                "authorization": "RBAC",
                "encryption": "TLS 1.2+",
            },
        }

        return openapi_schema

    def get_code_examples(self, path: str, method: str) -> dict[str, str]:
        """
        Generate code examples for an endpoint in multiple languages.

        Args:
            path: API path
            method: HTTP method

        Returns:
            Dictionary of language -> code example
        """
        examples = {}

        # Python example
        examples["python"] = f"""import requests

url = "http://localhost:8000{path}"
headers = {{
    "Authorization": "Bearer YOUR_TOKEN_HERE",
    "Content-Type": "application/json"
}}

response = requests.{method.lower()}(url, headers=headers)
print(response.json())
"""

        # JavaScript/Node.js example
        examples["javascript"] = f"""const axios = require('axios');

const url = 'http://localhost:8000{path}';
const config = {{
  headers: {{
    'Authorization': 'Bearer YOUR_TOKEN_HERE',
    'Content-Type': 'application/json'
  }}
}};

axios.{method.lower()}(url, config)
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
"""

        # cURL example
        examples["curl"] = f"""curl -X {method.upper()} \\
  'http://localhost:8000{path}' \\
  -H 'Authorization: Bearer YOUR_TOKEN_HERE' \\
  -H 'Content-Type: application/json'
"""

        # TypeScript example
        examples["typescript"] = f"""import axios from 'axios';

interface ApiResponse {{
  // Define your response type here
}}

const url = 'http://localhost:8000{path}';
const config = {{
  headers: {{
    'Authorization': 'Bearer YOUR_TOKEN_HERE',
    'Content-Type': 'application/json'
  }}
}};

const response = await axios.{method.lower()}<ApiResponse>(url, config);
console.log(response.data);
"""

        return examples

    def initialize_default_examples(self) -> None:
        """Initialize default examples for common endpoints."""
        # Person creation example
        self.add_example(
            "/api/v1/people",
            "post",
            "request",
            {
                "name": "Dr. Jane Smith",
                "role": "FACULTY",
                "email": "jane.smith@example.com",
                "rank": "CAPTAIN",
                "pgy_level": None,
            },
        )

        self.add_example(
            "/api/v1/people",
            "post",
            "response",
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Dr. Jane Smith",
                "role": "FACULTY",
                "email": "jane.smith@example.com",
                "rank": "CAPTAIN",
                "pgy_level": None,
                "created_at": "2025-12-20T10:00:00Z",
            },
        )

        # Authentication example
        self.add_example(
            "/api/v1/auth/login",
            "post",
            "request",
            {"username": "user@example.com", "password": "SecurePassword123!"},
        )

        self.add_example(
            "/api/v1/auth/login",
            "post",
            "response",
            {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
            },
        )

        # Error code examples
        self.add_error_code(
            "400",
            "Bad Request",
            "The request was malformed or contained invalid parameters",
            {"detail": "Validation error", "errors": []},
        )

        self.add_error_code(
            "401",
            "Unauthorized",
            "Authentication credentials were missing or invalid",
            {"detail": "Could not validate credentials"},
        )

        self.add_error_code(
            "403",
            "Forbidden",
            "The authenticated user does not have permission to access this resource",
            {"detail": "Insufficient permissions"},
        )

        self.add_error_code(
            "404",
            "Not Found",
            "The requested resource was not found",
            {"detail": "Resource not found"},
        )

        self.add_error_code(
            "409",
            "Conflict",
            "The request conflicts with the current state of the resource",
            {"detail": "Resource already exists"},
        )

        self.add_error_code(
            "422",
            "Unprocessable Entity",
            "The request was well-formed but contained semantic errors",
            {
                "detail": [
                    {
                        "loc": ["body", "field"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ]
            },
        )

        self.add_error_code(
            "429",
            "Too Many Requests",
            "Rate limit exceeded",
            {"detail": "Too many requests. Please try again later."},
        )

        self.add_error_code(
            "500",
            "Internal Server Error",
            "An unexpected error occurred on the server",
            {"detail": "An internal error occurred. Please try again later."},
        )
