#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RUN_DIR="$ROOT_DIR/.local/run"

overall=0

print_row() {
  local name="$1"
  local status="$2"
  printf "%-18s %s\n" "$name" "$status"
}

process_status() {
  local name="$1"
  local pid_file="$RUN_DIR/${name}.pid"

  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" >/dev/null 2>&1; then
      print_row "$name" "running (pid=$pid)"
      return
    fi
  fi

  print_row "$name" "stopped"
  overall=1
}

port_status() {
  local label="$1"
  local port="$2"

  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    print_row "$label:$port" "listening"
  else
    print_row "$label:$port" "not listening"
    overall=1
  fi
}

health_check() {
  local label="$1"
  local url="$2"

  if curl -fsS "$url" >/dev/null 2>&1; then
    print_row "$label" "ok"
  else
    print_row "$label" "failed"
    overall=1
  fi
}

echo "Local process status"
echo "--------------------"
process_status "backend"
process_status "worker"
process_status "beat"
process_status "frontend"
process_status "mcp"

echo
echo "Port checks"
echo "-----------"
port_status "postgres" 5432
port_status "redis" 6379
port_status "backend" 8000
port_status "frontend" 3000
port_status "mcp" 8080

echo
echo "HTTP health checks"
echo "------------------"
health_check "backend /health" "http://127.0.0.1:8000/health"
health_check "mcp /health" "http://127.0.0.1:8080/health"

exit "$overall"
