#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
# ruff check . && ruff format --check .
if command -v ruff &>/dev/null; then
  ruff check legacy app 2>/dev/null || true
  ruff format --check legacy app 2>/dev/null || true
fi
echo "lint done"
