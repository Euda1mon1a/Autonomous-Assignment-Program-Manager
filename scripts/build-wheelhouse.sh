#!/usr/bin/env bash
set -euo pipefail

WHEELHOUSE_DIR="backend/vendor/wheels"
REQ_FILE="backend/requirements.txt"

mkdir -p "${WHEELHOUSE_DIR}"

python3 -m pip download -r "${REQ_FILE}" -d "${WHEELHOUSE_DIR}"

echo "Wheelhouse ready at ${WHEELHOUSE_DIR}"
