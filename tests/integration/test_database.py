import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import TupleRow

from refdata.config import get_settings

pytestmark = pytest.mark.integration

APP_ROLE = "refdata_app"
RO_ROLE = "refdata_ro"
EXPECTED_EXTENSIONS = {
    "vector",
    "pg_trgm",
    "fuzzystrmatch",
    "unaccent",
    "btree_gist",
    "pg_stat_statements",
}
EXPECTED_SCHEMAS = {"raw", "staging", "core", "marts", "ops"}

Conn = psycopg.Connection[TupleRow]


@pytest.fixture
def app_conn() -> Iterator[Conn]:
    """Connexion en tant que refdata_app (réglages lus par get_settings)."""
    with psycopg.connect(get_settings().app_conninfo) as conn:
        yield conn


@pytest.fixture
def ro_conn() -> Iterator[Conn]:
    password = os.environ.get("REFDATA_RO_PASSWORD")
    if not password:
        pytest.fail(
            "REFDATA_RO_PASSWORD absente de l'environnement: "
            "lancer `uv run --env-file .env pytest -m integration`"
        )
    settings = get_settings()
    conninfo = make_conninfo(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=RO_ROLE,
        password=password,
    )
    with psycopg.connect(conninfo) as conn:
        yield conn


def test_app_role_connects_and_selects(app_conn: Conn) -> None:
    row = app_conn.execute("SELECT 1, current_user").fetchone()
    assert row == (1, APP_ROLE)


def test_expected_schemas_exist(app_conn: Conn) -> None:
    rows = app_conn.execute("SELECT schema_name FROM information_schema.schemata").fetchall()
    existing = {name for (name,) in rows}
    missing = EXPECTED_SCHEMAS - existing
    assert not missing, f"schémas manquans: {sorted(missing)}"


def test_app_role_can_create_raw_but_not_in_public(app_conn: Conn) -> None:
    table = f"it_{uuid.uuid4().hex}"

    app_conn.execute(sql.SQL("CREATE TABLE {} (id integer)").format(sql.Identifier("raw", table)))
    row = app_conn.execute("SELECT to_regclass(%s)", (f"raw.{table}",)).fetchone()
    assert row is not None
    assert row[0] is not None
    app_conn.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier("raw", table)))

    with pytest.raises(errors.InsufficientPrivilege):
        app_conn.execute(
            sql.SQL("CREATE TABLE {} (id integer)").format(sql.Identifier("public", table))
        )


def test_read_only_role_reads_but_cannot_write(ro_conn: Conn) -> None:
    row = ro_conn.execute("SELECT count(*) FROM pg_extension").fetchone()
    assert row is not None
    assert row[0] > 0

    with pytest.raises((errors.InsufficientPrivilege, errors.ReadOnlySqlTransaction)):
        ro_conn.execute(
            sql.SQL("CREATE TABLE {} (id integer)").format(
                sql.Identifier("raw", f"it_{uuid.uuid4().hex}")
            )
        )
