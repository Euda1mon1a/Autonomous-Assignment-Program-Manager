#!/bin/bash
# Diagnose if container code matches local code
# Usage: ./scripts/diagnose-container-staleness.sh [container_name] [file_path]
#
# Purpose: Detect when Docker container is running stale code that differs
# from local source files. This catches cases where code changes exist in
# the working directory but the container hasn't been rebuilt yet.
#
# Examples:
#   ./scripts/diagnose-container-staleness.sh
#   ./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/db/session.py
#   ./scripts/diagnose-container-staleness.sh residency-scheduler-backend app/api/routes/__init__.py

CONTAINER=${1:-residency-scheduler-backend}
FILE_PATH=${2:-app/db/session.py}

echo "=== Container Staleness Diagnostic ==="
echo "Container: $CONTAINER"
echo "File: $FILE_PATH"
echo ""

# Verify container is running
if ! docker ps --filter "name=$CONTAINER" --quiet | grep -q .; then
    echo "ERROR: Container '$CONTAINER' is not running"
    echo "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

# Check if file exists in container
echo "--- Container file check ---"
if docker exec "$CONTAINER" ls -la "/app/$FILE_PATH" 2>/dev/null; then
    echo "✅ File exists in container"
else
    echo "❌ FILE NOT FOUND IN CONTAINER"
    echo "This could mean:"
    echo "  - Container is missing the file entirely"
    echo "  - File path is incorrect"
    echo "  - Container image was built before file was added"
    exit 1
fi

# Compare checksums
echo ""
echo "--- Checksum comparison ---"

# Get local file hash
LOCAL_MD5=$(md5sum "backend/$FILE_PATH" 2>/dev/null | cut -d' ' -f1)
if [ -z "$LOCAL_MD5" ]; then
    echo "ERROR: Local file not found: backend/$FILE_PATH"
    exit 1
fi

# Get container file hash
CONTAINER_MD5=$(docker exec "$CONTAINER" md5sum "/app/$FILE_PATH" 2>/dev/null | cut -d' ' -f1)
if [ -z "$CONTAINER_MD5" ]; then
    echo "ERROR: Could not read container file hash"
    exit 1
fi

echo "Local:     $LOCAL_MD5"
echo "Container: $CONTAINER_MD5"
echo ""

# Report results
if [ "$LOCAL_MD5" = "$CONTAINER_MD5" ]; then
    echo "✅ FILES MATCH - Container is current"
    exit 0
else
    echo "❌ FILES DIFFER - Container is STALE"
    echo ""
    echo "Recommended fix:"
    echo "  docker-compose build --no-cache $CONTAINER && docker-compose up -d $CONTAINER"
    echo ""
    echo "Or use rebuild script:"
    echo "  ./scripts/rebuild-containers.sh $CONTAINER"
    exit 1
fi
