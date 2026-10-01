# streaming-pipeline local development
.DEFAULT_GOAL := help
COMPOSE := docker compose -f docker/docker-compose.yml
SERVICES ?=

.PHONY: help env dev-up dev-down local-up up down build ps logs config lint test smoke smoke-test

help:
	@echo "make dev-up       Build and start the stack (creates .env if missing)"
	@echo "make dev-down     Stop the stack"
	@echo "make build        Build service images"
	@echo "make ps           Show service status"
	@echo "make logs         Follow logs (optional: SERVICES='api stream-worker')"
	@echo "make config       Validate Compose configuration"
	@echo "make lint / test  Run backend lint / tests using uv"
	@echo "make smoke        Run START/GET/STOP smoke checks on the running stack"

env:
	@test -f .env || cp .env.example .env

dev-up local-up up: env
	$(COMPOSE) up -d --build $(SERVICES)

dev-down down:
	$(COMPOSE) down

build: env
	$(COMPOSE) build $(SERVICES)

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs --tail 100 -f $(SERVICES)

config: env
	$(COMPOSE) config --quiet

lint:
	bash scripts/lint.sh

test:
	uv run --extra dev python -m pytest tests

# Requires a running stack. The smoke script restarts the API to check persistence.
smoke smoke-test:
	bash scripts/smoke_test.sh
