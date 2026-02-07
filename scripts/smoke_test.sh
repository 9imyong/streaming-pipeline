#!/usr/bin/env bash
# E2E 스모크: API → Kafka → Orchestrator, DB 영속성 검증
# 전제: docker compose up -d mysql kafka api orchestrator, DB 초기화 완료
set -e
BASE="${1:-http://localhost:8000}"
CHANNEL="${2:-ch1}"
RESTART_API_FOR_PERSISTENCE="${RESTART_API_FOR_PERSISTENCE:-1}"
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

# GET: 스트림 상태 조회 (DB에서 읽음)
GET_RESP=$(curl -s -w "\n%{http_code}" "$BASE/v1/streams/$CHANNEL")
GET_BODY=$(echo "$GET_RESP" | head -n -1)
GET_CODE=$(echo "$GET_RESP" | tail -n 1)
if [ "$GET_CODE" != "200" ]; then
  echo "FAIL: GET /v1/streams/$CHANNEL expected 200, got $GET_CODE"
  echo "$GET_BODY"
  exit 1
fi
if ! echo "$GET_BODY" | grep -q "\"channel_id\""; then
  echo "FAIL: GET response should contain channel_id (persisted state)"
  echo "$GET_BODY"
  exit 1
fi
echo "OK: GET 200 (state persisted)"

# 재시작 후 상태 유지 검증: API 재시작 후 동일 채널 GET
if [ "$RESTART_API_FOR_PERSISTENCE" = "1" ] && command -v docker &>/dev/null; then
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -q streaming-api; then
    docker restart streaming-api >/dev/null 2>&1 || true
    echo "Waiting for API after restart (5s)..."
    sleep 5
    GET2_RESP=$(curl -s -w "\n%{http_code}" "$BASE/v1/streams/$CHANNEL")
    GET2_CODE=$(echo "$GET2_RESP" | tail -n 1)
    GET2_BODY=$(echo "$GET2_RESP" | head -n -1)
    if [ "$GET2_CODE" != "200" ]; then
      echo "FAIL: GET /v1/streams/$CHANNEL after API restart expected 200, got $GET2_CODE (state should persist in DB)"
      echo "$GET2_BODY"
      exit 1
    fi
    if ! echo "$GET2_BODY" | grep -q "$CHANNEL"; then
      echo "FAIL: After restart, GET response should still contain channel_id=$CHANNEL"
      echo "$GET2_BODY"
      exit 1
    fi
    echo "OK: GET after API restart 200 (state persisted in DB)"
  fi
fi

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

echo "smoke_test done. DB persistence verified (GET after POST, GET after API restart). Check logs: api command_bus.publish; orchestrator handle_start/handle_stop; worker stream.events STARTED/STOPPED"
