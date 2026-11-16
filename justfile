default:
	@just --list

install:
	uv sync --locked

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run sqlfluff lint transform/ --dialect postgres

lint-sql:
	uv run sqlfluff lint transform/

typecheck:
	uv run pyright

test:
	uv run pytest -m "not integration"

test-int:
	uv run pytest -m integration

check: lint typecheck test

db-up:
	docker compose --env-file .env -f infra/compose.yaml up -d --wait

db-down:
	docker compose --env-file .env -f infra/compose.yaml down

db-reset:
	docker compose --env-file .env -f infra/compose.yaml down -v
	docker compose --env-file .env -f infra/compose.yaml up -d --wait

db-shell:
	docker compose --env-file .env -f infra/compose.yaml exec db \
		psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
