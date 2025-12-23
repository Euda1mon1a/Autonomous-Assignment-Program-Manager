#!/usr/bin/env python3
"""
Export OpenAPI schema to JSON file.

Usage:
    python scripts/export_openapi.py [output_path]

Default output: ../frontend/openapi.json
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


def export_openapi(output_path: str | None = None) -> None:
    """Export the OpenAPI schema to a JSON file."""
    if output_path is None:
        output_path = str(
            Path(__file__).parent.parent.parent / "frontend" / "openapi.json"
        )

    schema = app.openapi()

    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"OpenAPI schema exported to: {output_path}")
    print(f"Endpoints: {len(schema.get('paths', {}))}")
    print(f"Schemas: {len(schema.get('components', {}).get('schemas', {}))}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else None
    export_openapi(output)
