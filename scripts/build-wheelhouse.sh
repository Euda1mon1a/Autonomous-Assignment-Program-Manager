***REMOVED***!/usr/bin/env bash
***REMOVED*** ============================================================
***REMOVED*** Script: build-wheelhouse.sh
***REMOVED*** Purpose: Pre-download Python packages for offline installation
***REMOVED*** Usage: ./scripts/build-wheelhouse.sh
***REMOVED***
***REMOVED*** Description:
***REMOVED***   Downloads all Python packages from requirements.txt into
***REMOVED***   a local wheelhouse directory for offline deployments.
***REMOVED***   Useful for air-gapped environments or faster Docker builds.
***REMOVED***
***REMOVED*** Output:
***REMOVED***   backend/vendor/wheels/ - Downloaded wheel files
***REMOVED***
***REMOVED*** Requirements:
***REMOVED***   - Python 3.11+
***REMOVED***   - pip with wheel support
***REMOVED*** ============================================================

set -euo pipefail

WHEELHOUSE_DIR="backend/vendor/wheels"
REQ_FILE="backend/requirements.txt"

***REMOVED*** Validate requirements file exists
if [ ! -f "${REQ_FILE}" ]; then
    echo "ERROR: Requirements file not found: ${REQ_FILE}" >&2
    exit 1
fi

***REMOVED*** Check if pip is available
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 command not found" >&2
    exit 1
fi

***REMOVED*** Create wheelhouse directory if it doesn't exist
***REMOVED*** This directory will contain all downloaded Python packages
mkdir -p "${WHEELHOUSE_DIR}" || {
    echo "ERROR: Failed to create directory: ${WHEELHOUSE_DIR}" >&2
    exit 1
}

***REMOVED*** Download all packages from requirements.txt
***REMOVED*** Packages are downloaded as .whl files for offline installation
***REMOVED*** This avoids network dependency during Docker builds
if ! python3 -m pip download -r "${REQ_FILE}" -d "${WHEELHOUSE_DIR}"; then
    echo "ERROR: Package download failed" >&2
    exit 1
fi

echo "✓ Wheelhouse ready at ${WHEELHOUSE_DIR}"
echo "✓ Downloaded $(find "${WHEELHOUSE_DIR}" -name "*.whl" | wc -l) packages"
