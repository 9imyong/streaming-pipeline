# streaming-pipeline Makefile
.PHONY: dev-up dev-down lint smoke smoke-test

dev-up:
	./scripts/dev_up.sh

dev-down:
	./scripts/dev_down.sh

lint:
	./scripts/lint.sh

# E2E 스모크: POST/DELETE /v1/streams → 202. 전제: compose up mysql kafka api orchestrator + DB 초기화
smoke smoke-test:
	./scripts/smoke_test.sh
