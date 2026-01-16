#!/bin/bash
# LICH'S PHYLACTERY - Manual Schema Soul Extraction
#
# Usage: ./scripts/dump-schema.sh [output-file]
#   output-file: optional (default: backend/schema.sql)
#
# Extracts the database's soul (schema) without the flesh (data).
# The phylactery can be used to:
# - Resurrect the database structure
# - Track schema changes over time (diff the souls)
# - Create empty databases with proper structure

set -euo pipefail

# GOTCHA: User is "scheduler", NOT "postgres"
DB_USER="scheduler"
DB_NAME="residency_scheduler"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.local.yml}"

OUTPUT_FILE="${1:-backend/schema.sql}"

echo "💀 Extracting database soul to $OUTPUT_FILE..."

# Schema only - no data, safe to commit
docker compose -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U "$DB_USER" --schema-only "$DB_NAME" > "$OUTPUT_FILE"

# Add header with timestamp
TEMP_FILE=$(mktemp)
{
    echo "-- ╔═══════════════════════════════════════════════════════════════╗"
    echo "-- ║            LICH'S PHYLACTERY - Database Soul                  ║"
    echo "-- ╚═══════════════════════════════════════════════════════════════╝"
    echo "--"
    echo "-- Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "-- Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
    echo "-- Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    echo "--"
    echo "-- Contains NO DATA - just structure. The soul, not the flesh."
    echo "-- Safe to commit. Sacred timeline preserved."
    echo ""
    cat "$OUTPUT_FILE"
} > "$TEMP_FILE"
mv "$TEMP_FILE" "$OUTPUT_FILE"

# Stats
TABLES=$(grep -c "CREATE TABLE" "$OUTPUT_FILE" || echo 0)
INDEXES=$(grep -c "CREATE INDEX" "$OUTPUT_FILE" || echo 0)
SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')

echo ""
echo "💀 Phylactery preserved:"
echo "   File: $OUTPUT_FILE"
echo "   Size: $SIZE"
echo "   Tables: $TABLES"
echo "   Indexes: $INDEXES"
echo ""
echo "The lich may now resurrect: git add $OUTPUT_FILE"
