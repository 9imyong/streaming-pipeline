# streaming-pipeline Makefile
.PHONY: dev-up dev-down lint smoke-test

dev-up:
	./scripts/dev_up.sh

dev-down:
	./scripts/dev_down.sh

lint:
	./scripts/lint.sh

smoke-test:
	./scripts/smoke_test.sh
