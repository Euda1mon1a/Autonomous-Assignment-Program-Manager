#!/bin/bash
# Quick DB checkpoint for Block 12 handjam session.
#
# Usage: ./checkpoint.sh <label>
# Example: ./checkpoint.sh pre_import
#          ./checkpoint.sh post_hda_sync
#          ./checkpoint.sh pre_assignments_fix
#
# Output: /tmp/block12_<label>_<timestamp>.dump

set -e

LABEL=${1:-snapshot}
TIMESTAMP=$(date +%Y%m%dT%H%M%S)
FILE="/tmp/block12_${LABEL}_${TIMESTAMP}.dump"

/opt/homebrew/opt/postgresql@17/bin/pg_dump -Fc \
  -U scheduler residency_scheduler -f "$FILE"

SIZE=$(du -h "$FILE" | cut -f1)
echo "Checkpoint: $FILE ($SIZE)"
echo ""
echo "Restore with:"
echo "  /opt/homebrew/opt/postgresql@17/bin/pg_restore -U scheduler -d residency_scheduler --clean $FILE"
