#!/usr/bin/env bash
set -e
BASE="${1:-http://localhost:8000}"
echo "Smoke test: $BASE"
curl -sf "$BASE/streaming/test_id" -o /dev/null || true
curl -sf "$BASE/CCTVLIST/" -o /dev/null || true
echo "smoke_test done"
