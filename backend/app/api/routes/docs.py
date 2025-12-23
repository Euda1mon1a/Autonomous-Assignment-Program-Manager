"""
Documentation API routes.

Provides endpoints for accessing enhanced API documentation, code examples,
and metadata about the API.
"""

import logging

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from app.docs import DocumentationGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_doc_generator(request: Request) -> DocumentationGenerator:
    """
    Get or create documentation generator instance.

    Args:
        request: FastAPI request object

    Returns:
        DocumentationGenerator instance
    """
    # Cache the generator in the app state to avoid recreating it
    if not hasattr(request.app.state, "doc_generator"):
        request.app.state.doc_generator = DocumentationGenerator(request.app)

    return request.app.state.doc_generator


@router.get("/openapi-enhanced.json")
async def get_enhanced_openapi(request: Request) -> JSONResponse:
    """
    Get enhanced OpenAPI schema with examples and metadata.

    Returns:
        Enhanced OpenAPI 3.0 schema in JSON format

    Example:
        ```bash
        curl http://localhost:8000/api/v1/docs/openapi-enhanced.json
        ```
    """
    try:
        generator = _get_doc_generator(request)
        schema = generator.get_enhanced_openapi_schema()

        return JSONResponse(content=schema)
    except Exception as e:
        logger.error(f"Failed to generate enhanced OpenAPI schema: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate enhanced OpenAPI schema"
        )


@router.get("/markdown")
async def get_markdown_docs(request: Request) -> PlainTextResponse:
    """
    Get complete API documentation in Markdown format.

    Returns:
        Complete API documentation as Markdown

    Example:
        ```bash
        curl http://localhost:8000/api/v1/docs/markdown > api-docs.md
        ```
    """
    try:
        generator = _get_doc_generator(request)
        markdown = generator.get_markdown_documentation()

        return PlainTextResponse(content=markdown)
    except Exception as e:
        logger.error(f"Failed to generate Markdown documentation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate Markdown documentation"
        )


@router.get("/endpoint")
async def get_endpoint_documentation(
    request: Request,
    path: str = Query(..., description="API path (e.g., /api/v1/people)"),
    method: str = Query(..., description="HTTP method (e.g., GET, POST)"),
    format: str = Query("markdown", description="Output format (markdown or json)"),
) -> Response:
    """
    Get documentation for a specific endpoint.

    Args:
        path: API path (e.g., "/api/v1/people")
        method: HTTP method (e.g., "GET", "POST")
        format: Output format ("markdown" or "json")

    Returns:
        Endpoint documentation in the requested format

    Example:
        ```bash
        # Get Markdown documentation for GET /api/v1/people
        curl "http://localhost:8000/api/v1/docs/endpoint?path=/api/v1/people&method=GET"

        # Get JSON documentation for POST /api/v1/assignments
        curl "http://localhost:8000/api/v1/docs/endpoint?path=/api/v1/assignments&method=POST&format=json"
        ```
    """
    try:
        generator = _get_doc_generator(request)
        docs = generator.get_endpoint_documentation(
            path=path, method=method.lower(), format=format.lower()
        )

        if format.lower() == "json":
            return JSONResponse(content={"documentation": docs})
        else:
            return PlainTextResponse(content=docs)

    except Exception as e:
        logger.error(f"Failed to generate endpoint documentation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate endpoint documentation"
        )


@router.get("/examples")
async def get_code_examples(
    request: Request,
    path: str = Query(..., description="API path (e.g., /api/v1/people)"),
    method: str = Query(..., description="HTTP method (e.g., GET, POST)"),
    language: str | None = Query(
        None, description="Programming language (python, javascript, curl, typescript)"
    ),
) -> JSONResponse:
    """
    Get code examples for a specific endpoint.

    Args:
        path: API path
        method: HTTP method
        language: Optional specific language filter

    Returns:
        Dictionary of code examples by language

    Example:
        ```bash
        # Get all code examples for GET /api/v1/people
        curl "http://localhost:8000/api/v1/docs/examples?path=/api/v1/people&method=GET"

        # Get only Python example
        curl "http://localhost:8000/api/v1/docs/examples?path=/api/v1/people&method=GET&language=python"
        ```
    """
    try:
        generator = _get_doc_generator(request)
        examples = generator.get_code_examples(
            path=path, method=method.lower(), language=language
        )

        return JSONResponse(content=examples)

    except Exception as e:
        logger.error(f"Failed to generate code examples: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate code examples")


@router.get("/errors")
async def get_error_documentation(request: Request) -> JSONResponse:
    """
    Get comprehensive error code documentation.

    Returns:
        Dictionary of error codes with descriptions and examples

    Example:
        ```bash
        curl http://localhost:8000/api/v1/docs/errors
        ```
    """
    try:
        generator = _get_doc_generator(request)
        errors = generator.get_error_documentation()

        return JSONResponse(content=errors)

    except Exception as e:
        logger.error(f"Failed to generate error documentation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate error documentation"
        )


@router.get("/changelog")
async def get_changelog(request: Request) -> PlainTextResponse:
    """
    Get API changelog in Markdown format.

    Returns:
        API changelog as Markdown

    Example:
        ```bash
        curl http://localhost:8000/api/v1/docs/changelog
        ```
    """
    try:
        generator = _get_doc_generator(request)
        changelog = generator.get_changelog()

        return PlainTextResponse(content=changelog)

    except Exception as e:
        logger.error(f"Failed to generate changelog: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate changelog")


@router.get("/version")
async def get_version_info(request: Request) -> JSONResponse:
    """
    Get API versioning information.

    Returns:
        Dictionary with current version, supported versions, and deprecated versions

    Example:
        ```bash
        curl http://localhost:8000/api/v1/docs/version
        ```

    Response:
        ```json
        {
          "current": "v1",
          "supported": ["v1"],
          "deprecated": [],
          "sunset": []
        }
        ```
    """
    try:
        generator = _get_doc_generator(request)
        version_info = generator.get_version_info()

        return JSONResponse(content=version_info)

    except Exception as e:
        logger.error(f"Failed to get version info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get version information")


@router.get("/stats")
async def get_documentation_stats(request: Request) -> JSONResponse:
    """
    Get statistics about the API documentation.

    Returns:
        Dictionary with statistics including endpoint counts, tags, schemas, etc.

    Example:
        ```bash
        curl http://localhost:8000/api/v1/docs/stats
        ```

    Response:
        ```json
        {
          "total_endpoints": 150,
          "methods": {
            "get": 80,
            "post": 40,
            "put": 15,
            "patch": 10,
            "delete": 5
          },
          "tags": ["people", "assignments", "schedule", ...],
          "total_tags": 25,
          "schemas": 50,
          "error_codes": 8,
          "security_schemes": 1
        }
        ```
    """
    try:
        generator = _get_doc_generator(request)
        stats = generator.get_stats()

        return JSONResponse(content=stats)

    except Exception as e:
        logger.error(f"Failed to generate documentation stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate documentation statistics"
        )


@router.get("/export/openapi")
async def export_openapi_schema(
    request: Request,
    filepath: str = Query("openapi-enhanced.json", description="Output file path"),
) -> JSONResponse:
    """
    Export enhanced OpenAPI schema to a file.

    Note: This endpoint is primarily for administrative use and may require
    special permissions in production environments.

    Args:
        filepath: Path to the output file

    Returns:
        Success message with file path

    Example:
        ```bash
        curl "http://localhost:8000/api/v1/docs/export/openapi?filepath=/tmp/openapi.json"
        ```
    """
    try:
        generator = _get_doc_generator(request)
        generator.export_openapi_json(filepath)

        return JSONResponse(
            content={
                "status": "success",
                "message": f"OpenAPI schema exported to {filepath}",
                "filepath": filepath,
            }
        )

    except Exception as e:
        logger.error(f"Failed to export OpenAPI schema: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to export OpenAPI schema: {str(e)}"
        )


@router.get("/export/markdown")
async def export_markdown_documentation(
    request: Request,
    filepath: str = Query("api-documentation.md", description="Output file path"),
) -> JSONResponse:
    """
    Export complete Markdown documentation to a file.

    Note: This endpoint is primarily for administrative use and may require
    special permissions in production environments.

    Args:
        filepath: Path to the output file

    Returns:
        Success message with file path

    Example:
        ```bash
        curl "http://localhost:8000/api/v1/docs/export/markdown?filepath=/tmp/api-docs.md"
        ```
    """
    try:
        generator = _get_doc_generator(request)
        generator.export_markdown_docs(filepath)

        return JSONResponse(
            content={
                "status": "success",
                "message": f"Markdown documentation exported to {filepath}",
                "filepath": filepath,
            }
        )

    except Exception as e:
        logger.error(f"Failed to export Markdown documentation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to export Markdown documentation: {str(e)}"
        )


@router.get("/")
async def documentation_index(request: Request) -> JSONResponse:
    """
    Get an index of available documentation endpoints.

    Returns:
        Dictionary listing all available documentation endpoints with descriptions

    Example:
        ```bash
        curl http://localhost:8000/api/v1/docs/
        ```
    """
    return JSONResponse(
        content={
            "title": "API Documentation Endpoints",
            "description": "Enhanced API documentation generator for the Residency Scheduler API",
            "endpoints": {
                "/openapi-enhanced.json": {
                    "description": "Enhanced OpenAPI 3.0 schema with examples and metadata",
                    "method": "GET",
                },
                "/markdown": {
                    "description": "Complete API documentation in Markdown format",
                    "method": "GET",
                },
                "/endpoint": {
                    "description": "Documentation for a specific endpoint",
                    "method": "GET",
                    "parameters": ["path", "method", "format"],
                },
                "/examples": {
                    "description": "Code examples for a specific endpoint",
                    "method": "GET",
                    "parameters": ["path", "method", "language"],
                },
                "/errors": {
                    "description": "Comprehensive error code documentation",
                    "method": "GET",
                },
                "/changelog": {
                    "description": "API changelog in Markdown format",
                    "method": "GET",
                },
                "/version": {
                    "description": "API versioning information",
                    "method": "GET",
                },
                "/stats": {
                    "description": "Statistics about the API documentation",
                    "method": "GET",
                },
                "/export/openapi": {
                    "description": "Export enhanced OpenAPI schema to file",
                    "method": "GET",
                    "parameters": ["filepath"],
                },
                "/export/markdown": {
                    "description": "Export Markdown documentation to file",
                    "method": "GET",
                    "parameters": ["filepath"],
                },
            },
            "usage": {
                "interactive_docs": "http://localhost:8000/docs",
                "redoc": "http://localhost:8000/redoc",
                "enhanced_openapi": "http://localhost:8000/api/v1/docs/openapi-enhanced.json",
                "markdown_docs": "http://localhost:8000/api/v1/docs/markdown",
            },
        }
    )
