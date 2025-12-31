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

mkdir -p "${WHEELHOUSE_DIR}"

python3 -m pip download -r "${REQ_FILE}" -d "${WHEELHOUSE_DIR}"

echo "Wheelhouse ready at ${WHEELHOUSE_DIR}"
