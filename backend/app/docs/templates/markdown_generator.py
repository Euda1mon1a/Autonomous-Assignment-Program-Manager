"""
Markdown documentation generator.

Generates comprehensive Markdown documentation from OpenAPI schemas.
"""

import json
from datetime import datetime
from typing import Any


class MarkdownGenerator:
    """Generates Markdown documentation from OpenAPI schemas."""

    def __init__(self, openapi_schema: dict[str, Any]) -> None:
        """
        Initialize the Markdown generator.

        Args:
            openapi_schema: Enhanced OpenAPI schema dictionary
        """
        self.schema = openapi_schema
        self.info = openapi_schema.get("info", {})
        self.paths = openapi_schema.get("paths", {})
        self.components = openapi_schema.get("components", {})

    def generate_full_documentation(self) -> str:
        """
        Generate complete Markdown documentation.

        Returns:
            Complete Markdown documentation as string
        """
        sections = [
            self._generate_header(),
            self._generate_toc(),
            self._generate_overview(),
            self._generate_authentication(),
            self._generate_rate_limits(),
            self._generate_endpoints(),
            self._generate_schemas(),
            self._generate_error_codes(),
            self._generate_changelog(),
            self._generate_footer(),
        ]

        return "\n\n".join(sections)

    def _generate_header(self) -> str:
        """Generate documentation header."""
        title = self.info.get("title", "API Documentation")
        version = self.info.get("version", "1.0.0")
        description = self.info.get("description", "")

        header = f"""# {title}

**Version:** {version}
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

{description}
"""
        return header

    def _generate_toc(self) -> str:
        """Generate table of contents."""
        toc = """## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limits](#rate-limits)
4. [Endpoints](#endpoints)
5. [Schemas](#schemas)
6. [Error Codes](#error-codes)
7. [Changelog](#changelog)
"""
        return toc

    def _generate_overview(self) -> str:
        """Generate overview section."""
        contact = self.info.get("contact", {})
        license_info = self.info.get("license", {})
        servers = self.schema.get("servers", [])

        overview = """## Overview

### Contact

"""
        if contact:
            overview += f"- **Name:** {contact.get('name', 'N/A')}\n"
            overview += f"- **Email:** {contact.get('email', 'N/A')}\n"

        if license_info:
            overview += "\n### License\n\n"
            overview += f"- **Name:** {license_info.get('name', 'N/A')}\n"
            if license_info.get("url"):
                overview += f"- **URL:** {license_info['url']}\n"

        if servers:
            overview += "\n### Servers\n\n"
            for server in servers:
                overview += f"- **{server.get('description', 'Server')}:** `{server.get('url', 'N/A')}`\n"

                # Add compliance information
        compliance = self.schema.get("x-compliance", {})
        if compliance:
            overview += "\n### Compliance\n\n"
            acgme = compliance.get("acgme", {})
            if acgme and acgme.get("enabled"):
                overview += "**ACGME Compliance:** Enabled\n\n"
                overview += "Rules enforced:\n"
                for rule in acgme.get("rules", []):
                    overview += f"- {rule}\n"

            security = compliance.get("security", {})
            if security:
                overview += "\n**Security:**\n"
                for key, value in security.items():
                    overview += f"- {key.title()}: {value}\n"

        return overview

    def _generate_authentication(self) -> str:
        """Generate authentication section."""
        security_schemes = self.components.get("securitySchemes", {})

        auth = """## Authentication

This API uses the following authentication methods:

"""
        for name, scheme in security_schemes.items():
            scheme_type = scheme.get("type", "unknown")
            description = scheme.get("description", "")

            auth += f"### {name}\n\n"
            auth += f"- **Type:** {scheme_type}\n"

            if scheme_type == "http":
                auth += f"- **Scheme:** {scheme.get('scheme', 'N/A')}\n"
                if scheme.get("bearerFormat"):
                    auth += f"- **Bearer Format:** {scheme['bearerFormat']}\n"

            if description:
                auth += f"\n{description}\n"

                # Add example
            if name == "bearerAuth":
                auth += """
**Example:**

```http
GET /api/v1/people HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Obtaining a Token:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \\
  -H 'Content-Type: application/json' \\
  -d '{
    "username": "user@example.com",
    "password": "your_password"
  }'
```
"""

            auth += "\n"

        return auth

    def _generate_rate_limits(self) -> str:
        """Generate rate limits section."""
        rate_limits = self.schema.get("x-rate-limits", {})

        limits = """## Rate Limits

The API enforces the following rate limits:

"""
        for endpoint, limit_info in rate_limits.items():
            limits += f"### {endpoint.title()}\n\n"
            limits += f"- **Limit:** {limit_info.get('limit', 'N/A')} requests\n"
            limits += f"- **Window:** {limit_info.get('window', 'N/A')}\n"
            limits += f"- **Scope:** {limit_info.get('scope', 'N/A')}\n\n"

        limits += """**Rate Limit Headers:**

When rate limits are enforced, the following headers are included in responses:

- `X-RateLimit-Limit`: Maximum number of requests allowed
- `X-RateLimit-Remaining`: Number of requests remaining in the current window
- `X-RateLimit-Reset`: Timestamp when the rate limit resets

**429 Too Many Requests:**

When the rate limit is exceeded, the API returns a `429 Too Many Requests` status code with a `Retry-After` header.
"""
        return limits

    def _generate_endpoints(self) -> str:
        """Generate endpoints section."""
        endpoints = """## Endpoints

"""
        # Group endpoints by tag
        endpoints_by_tag: dict[str, list[tuple]] = {}

        for path, path_item in self.paths.items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                tags = operation.get("tags", ["default"])
                tag = tags[0] if tags else "default"

                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []

                endpoints_by_tag[tag].append((path, method, operation))

                # Generate documentation for each tag
        for tag, operations in sorted(endpoints_by_tag.items()):
            endpoints += f"### {tag.title()}\n\n"

            for path, method, operation in operations:
                endpoints += self._generate_endpoint_doc(path, method, operation)
                endpoints += "\n---\n\n"

        return endpoints

    def _generate_endpoint_doc(
        self, path: str, method: str, operation: dict[str, Any]
    ) -> str:
        """
        Generate documentation for a single endpoint.

        Args:
            path: API path
            method: HTTP method
            operation: OpenAPI operation object

        Returns:
            Markdown documentation for the endpoint
        """
        summary = operation.get("summary", "")
        description = operation.get("description", "")
        operation_id = operation.get("operationId", "")

        doc = f"#### `{method.upper()} {path}`\n\n"

        if summary:
            doc += f"**{summary}**\n\n"

        if description:
            doc += f"{description}\n\n"

            # Parameters
        parameters = operation.get("parameters", [])
        if parameters:
            doc += "**Parameters:**\n\n"
            doc += "| Name | In | Type | Required | Description |\n"
            doc += "|------|----|----- |----------|-------------|\n"

            for param in parameters:
                name = param.get("name", "")
                param_in = param.get("in", "")
                required = "Yes" if param.get("required", False) else "No"
                schema = param.get("schema", {})
                param_type = schema.get("type", "string")
                param_desc = param.get("description", "")

                doc += f"| `{name}` | {param_in} | {param_type} | {required} | {param_desc} |\n"

            doc += "\n"

            # Request body
        request_body = operation.get("requestBody", {})
        if request_body:
            doc += "**Request Body:**\n\n"
            content = request_body.get("content", {})

            for content_type, content_schema in content.items():
                doc += f"*Content-Type: `{content_type}`*\n\n"

                example = content_schema.get("example")
                if example:
                    doc += "```json\n"
                    doc += json.dumps(example, indent=2)
                    doc += "\n```\n\n"

                    # Responses
        responses = operation.get("responses", {})
        if responses:
            doc += "**Responses:**\n\n"

            for status_code, response in responses.items():
                response_desc = response.get("description", "")
                doc += f"- **{status_code}** {response_desc}\n"

                content = response.get("content", {})
                for content_type, content_schema in content.items():
                    example = content_schema.get("example")
                    if example:
                        doc += "\n```json\n"
                        doc += json.dumps(example, indent=2)
                        doc += "\n```\n"

            doc += "\n"

            # Code examples
        doc += "**Code Examples:**\n\n"
        doc += self._generate_code_examples(path, method)

        return doc

    def _generate_code_examples(self, path: str, method: str) -> str:
        """
        Generate code examples for an endpoint.

        Args:
            path: API path
            method: HTTP method

        Returns:
            Markdown with code examples
        """
        examples = ""

        # cURL example
        examples += "**cURL:**\n\n"
        examples += "```bash\n"
        examples += f"curl -X {method.upper()} \\\n"
        examples += f"  'http://localhost:8000{path}' \\\n"
        examples += "  -H 'Authorization: Bearer YOUR_TOKEN_HERE' \\\n"
        examples += "  -H 'Content-Type: application/json'\n"
        examples += "```\n\n"

        # Python example
        examples += "**Python:**\n\n"
        examples += "```python\n"
        examples += "import requests\n\n"
        examples += f'url = "http://localhost:8000{path}"\n'
        examples += "headers = {\n"
        examples += '    "Authorization": "Bearer YOUR_TOKEN_HERE",\n'
        examples += '    "Content-Type": "application/json"\n'
        examples += "}\n\n"
        examples += f"response = requests.{method.lower()}(url, headers=headers)\n"
        examples += "print(response.json())\n"
        examples += "```\n\n"

        # JavaScript example
        examples += "**JavaScript (axios):**\n\n"
        examples += "```javascript\n"
        examples += "const axios = require('axios');\n\n"
        examples += f"const url = 'http://localhost:8000{path}';\n"
        examples += "const config = {\n"
        examples += "  headers: {\n"
        examples += "    'Authorization': 'Bearer YOUR_TOKEN_HERE',\n"
        examples += "    'Content-Type': 'application/json'\n"
        examples += "  }\n"
        examples += "};\n\n"
        examples += f"axios.{method.lower()}(url, config)\n"
        examples += "  .then(response => console.log(response.data))\n"
        examples += "  .catch(error => console.error(error));\n"
        examples += "```\n\n"

        return examples

    def _generate_schemas(self) -> str:
        """Generate schemas section."""
        schemas = self.components.get("schemas", {})

        doc = """## Schemas

Common data structures used throughout the API:

"""
        for schema_name, schema_def in sorted(schemas.items()):
            doc += f"### {schema_name}\n\n"

            description = schema_def.get("description", "")
            if description:
                doc += f"{description}\n\n"

            properties = schema_def.get("properties", {})
            required = schema_def.get("required", [])

            if properties:
                doc += "| Field | Type | Required | Description |\n"
                doc += "|-------|------|----------|-------------|\n"

                for prop_name, prop_def in properties.items():
                    prop_type = prop_def.get("type", "unknown")
                    prop_format = prop_def.get("format", "")
                    if prop_format:
                        prop_type = f"{prop_type} ({prop_format})"

                    is_required = "Yes" if prop_name in required else "No"
                    prop_desc = prop_def.get("description", "")

                    doc += f"| `{prop_name}` | {prop_type} | {is_required} | {prop_desc} |\n"

                doc += "\n"

        return doc

    def _generate_error_codes(self) -> str:
        """Generate error codes section."""
        error_codes = self.components.get("x-error-codes", {})

        doc = """## Error Codes

The API uses standard HTTP status codes to indicate success or failure:

"""
        for code, error_info in sorted(error_codes.items()):
            title = error_info.get("title", "")
            description = error_info.get("description", "")
            example = error_info.get("example", {})

            doc += f"### {code} {title}\n\n"
            doc += f"{description}\n\n"

            if example:
                doc += "**Example Response:**\n\n"
                doc += "```json\n"
                doc += json.dumps(example, indent=2)
                doc += "\n```\n\n"

        return doc

    def _generate_changelog(self) -> str:
        """Generate changelog section."""
        version_info = self.schema.get("x-api-version", {})

        changelog = """## Changelog

### API Versioning

"""
        if version_info:
            changelog += (
                f"- **Current Version:** {version_info.get('current', 'N/A')}\n"
            )
            changelog += f"- **Supported Versions:** {', '.join(version_info.get('supported', []))}\n"

            deprecated = version_info.get("deprecated", [])
            if deprecated:
                changelog += f"- **Deprecated Versions:** {', '.join(deprecated)}\n"

            sunset = version_info.get("sunset", [])
            if sunset:
                changelog += f"- **Sunset Versions:** {', '.join(sunset)}\n"

        changelog += """
### Version History

#### v1.0.0 (Current)

- Initial release
- Core scheduling functionality
- ACGME compliance validation
- Authentication and authorization
- Rate limiting
- Audit logging
- Resilience framework
- WebSocket support for real-time updates

**Breaking Changes:** None (initial release)

**New Features:**
- Complete CRUD operations for people, blocks, assignments
- Schedule generation with constraint satisfaction
- Swap management system
- Leave request handling
- Certification tracking
- Analytics and reporting
- Export functionality (PDF, Excel, iCal)
- GraphQL endpoint for flexible querying

**Bug Fixes:** None (initial release)

**Deprecations:** None

**Migration Guide:** N/A (initial release)
"""
        return changelog

    def _generate_footer(self) -> str:
        """Generate documentation footer."""
        footer = """---

## Support

For questions or issues with this API, please contact:

- **Email:** api-support@example.com
- **Documentation:** http://localhost:8000/docs
- **Status Page:** https://status.example.com

---

*This documentation was automatically generated from the OpenAPI schema.*
"""
        return footer

    def generate_endpoint_specific_doc(self, path: str, method: str) -> str:
        """
        Generate documentation for a specific endpoint.

        Args:
            path: API path
            method: HTTP method

        Returns:
            Markdown documentation for the endpoint
        """
        path_item = self.paths.get(path, {})
        operation = path_item.get(method.lower(), {})

        if not operation:
            return f"# Endpoint Not Found\n\nNo documentation available for `{method.upper()} {path}`"

        doc = f"# {method.upper()} {path}\n\n"
        doc += self._generate_endpoint_doc(path, method, operation)

        return doc
