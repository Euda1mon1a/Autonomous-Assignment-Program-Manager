#!/bin/bash

# Load Codex-specific environment variables if present.
if [ -f ".env.codex" ]; then
  set -a
  # shellcheck disable=SC1091
  source ".env.codex"
  set +a
fi
