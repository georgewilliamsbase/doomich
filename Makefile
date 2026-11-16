SHELL := /bin/bash
COMPOSE := docker compose -f infra/compose/compose.dev.yml --env-file infra/compose/.env.dev

.PHONY: help dev dev-down dev-logs seed test test-api test-services test-ml test-admin test-dart lint openapi dart-models licenses

help:
	@echo "make dev        поднять стек разработки (без GPU, ИИ в режиме заглушек)"
	@echo "make dev-down   остановить стек разработки"
	@echo "make seed       создать демо-вуз и код приглашения"
	@echo "make test       все тесты"
	@echo "make lint       линтеры"
	@echo "make openapi    выгрузить docs/api/openapi.json"
	@echo "make dart-models  пересобрать модели Dart из OpenAPI"
	@echo "make licenses   проверить лицензии зависимостей"

infra/compose/.env.dev:
	cp infra/compose/.env.dev.example infra/compose/.env.dev

dev: infra/compose/.env.dev
	infra/compose/dev-secrets.sh
	$(COMPOSE) up -d --build
	$(COMPOSE) exec api doomich-manage migrate
	$(COMPOSE) exec api doomich-manage seed-demo

dev-down:
	$(COMPOSE) down

dev-logs:
	$(COMPOSE) logs -f --tail=100

seed:
	$(COMPOSE) exec api doomich-manage seed-demo

test: test-api test-services test-ml test-admin test-dart

test-api:
	cd services/api && uv run pytest -q

test-services:
	cd services/asr && uv run pytest -q
	cd services/tts && uv run pytest -q
	cd services/nav && uv run pytest -q

test-ml:
	cd ml && uv run pytest -q

test-admin:
	cd apps/admin && npm run typecheck && npm test -- --run

test-dart:
	cd packages/doomich_api && flutter test
	cd packages/doomich_core && flutter test
	cd packages/doomich_ui && flutter test

lint:
	cd services/api && uv run ruff check . && uv run mypy src
	cd apps/admin && npm run lint
	cd apps/mobile && flutter analyze
	cd apps/desktop && flutter analyze

openapi:
	cd services/api && uv run doomich-manage openapi > ../../docs/api/openapi.json

dart-models: openapi
	python3 tools/gen_dart_models.py docs/api/openapi.json packages/doomich_api/lib/src/models.g.dart

licenses:
	python3 tools/check_licenses.py
