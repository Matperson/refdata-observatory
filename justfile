set dotenv-load

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

compose := "podman compose --env-file .env -f infra/compose.yaml"

db-up: db-start db-wait db-bootstrap

db-start:
        {{compose}} up -d

db-wait:
        #!/usr/bin/env bash
        set -euo pipefail
        for i in $(seq 1 30); do
        if podman exec refdata-db pg_isready -q -h 127.0.0.1; then echo "base prête"; exit 0; fi
        sleep 2
        done
        echo "base non prête après 60 s" >&2
        exit 1

db-bootstrap:
        podman exec -i refdata-db psql -v ON_ERROR_STOP=1 -U ${POSTGRES_USER} -d ${POSTGRES_DB} \
        -v app_pw="${REFDATA_APP_PASSWORD}" -v ro_pw="${REFDATA_RO_PASSWORD}" < infra/sql/bootstrap.sql

db-check:
        podman exec -i refdata-db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < infra/sql/check_extensions.sql

db-down:
        {{compose}} down

db-reset: db-destroy db-up

db-destroy:
        {{compose}} down -v

db-shell:
        podman exec -it refdata-db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

db-logs:
        podman logs --tail 50 refdata-db
