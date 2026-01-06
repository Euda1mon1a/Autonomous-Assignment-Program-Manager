#!/usr/bin/env bash
# ============================================================
# Script: build-wheelhouse.sh
# Purpose: Pre-download Python packages for offline installation
# Usage: ./scripts/build-wheelhouse.sh
#
# Description:
#   Downloads all Python packages from requirements.txt into
#   a local wheelhouse directory for offline deployments.
#   Useful for air-gapped environments or faster Docker builds.
#
# Output:
#   backend/vendor/wheels/ - Downloaded wheel files
#
# Requirements:
#   - Python 3.11+
#   - pip with wheel support
# ============================================================

set -euo pipefail

WHEELHOUSE_DIR="backend/vendor/wheels"
REQ_FILE="backend/requirements.txt"

# Validate requirements file exists
if [ ! -f "${REQ_FILE}" ]; then
    echo "ERROR: Requirements file not found: ${REQ_FILE}" >&2
    exit 1
fi

# Check if pip is available
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 command not found" >&2
    exit 1
fi

# Create wheelhouse directory if it doesn't exist
# This directory will contain all downloaded Python packages
mkdir -p "${WHEELHOUSE_DIR}" || {
    echo "ERROR: Failed to create directory: ${WHEELHOUSE_DIR}" >&2
    exit 1
}

# Download all packages from requirements.txt
# Packages are downloaded as .whl files for offline installation
# This avoids network dependency during Docker builds
if ! python3 -m pip download -r "${REQ_FILE}" -d "${WHEELHOUSE_DIR}"; then
    echo "ERROR: Package download failed" >&2
    exit 1
fi

echo "✓ Wheelhouse ready at ${WHEELHOUSE_DIR}"
echo "✓ Downloaded $(find "${WHEELHOUSE_DIR}" -name "*.whl" | wc -l) packages"
