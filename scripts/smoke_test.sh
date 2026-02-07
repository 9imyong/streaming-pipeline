#!/usr/bin/env bash
# E2E 스모크: API → Kafka → Orchestrator (command 발행 확인용)
# 전제: docker compose up -d mysql kafka api orchestrator, DB 초기화 완료
set -e
BASE="${1:-http://localhost:8000}"
CHANNEL="${2:-ch1}"
echo "Smoke test: $BASE (channel=$CHANNEL)"

# START: 202 + job_id (trailing slash required: route is POST /v1/streams/)
CURL_EXIT=0
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/v1/streams/" \
  -H "Content-Type: application/json" \
  -d "{\"channel_id\":\"$CHANNEL\",\"source_rtsp\":\"rtsp://example/stream\"}") || CURL_EXIT=$?
if [ "$CURL_EXIT" != "0" ]; then
  echo "FAIL: curl could not reach $BASE (exit $CURL_EXIT). Is the API running? (e.g. docker compose up -d api)"
  exit 1
fi
BODY=$(echo "$RESP" | head -n -1)
CODE=$(echo "$RESP" | tail -n 1)
if [ "$CODE" != "202" ]; then
  echo "FAIL: POST /v1/streams/ expected 202, got $CODE"
  echo "$BODY"
  if [ "$CODE" = "500" ]; then
    echo "Hint: 500 often means DB not initialized or Kafka unreachable. Run: docker exec -i streaming-mysql mysql -uroot -pdevpass streaming_pipeline_dev < app/infrastructure/persistence/migrations/001_streams_jobs_mysql.sql"
    echo "Check API logs: docker logs streaming-api"
  fi
  exit 1
fi
echo "OK: START 202"

# STOP: 202
CURL_EXIT=0
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE/v1/streams/$CHANNEL") || CURL_EXIT=$?
if [ "$CURL_EXIT" != "0" ]; then
  echo "FAIL: curl could not reach $BASE (exit $CURL_EXIT)"
  exit 1
fi
if [ "$CODE" != "202" ]; then
  echo "FAIL: DELETE /v1/streams/$CHANNEL expected 202, got $CODE"
  exit 1
fi
echo "OK: STOP 202"

echo "smoke_test done. Check logs: api 'command_bus.publish'; orchestrator 'handle_start'/'handle_stop'; worker stream.events STARTED/STOPPED"
