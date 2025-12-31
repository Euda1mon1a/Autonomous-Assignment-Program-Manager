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

# Create wheelhouse directory if it doesn't exist
# This directory will contain all downloaded Python packages
mkdir -p "${WHEELHOUSE_DIR}"

# Download all packages from requirements.txt
# Packages are downloaded as .whl files for offline installation
# This avoids network dependency during Docker builds
python3 -m pip download -r "${REQ_FILE}" -d "${WHEELHOUSE_DIR}"

echo "Wheelhouse ready at ${WHEELHOUSE_DIR}"
