from pathlib import Path

import pytest
from psycopg.conninfo import conninfo_to_dict
from pydantic import ValidationError

from refdata.config import APP_ROLE, Settings, get_settings

pytestmark = pytest.mark.unit

ENV_VARS = (
    "POSTGRES_DB",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "REFDATA_APP_PASSWORD",
    "REFDATA_RO_PASSWORD",
)
FAKE_PASSWORD = "fake-app-password"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()


@pytest.fixture
def valid_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_DB", "refdata")
    monkeypatch.setenv("REFDATA_APP_PASSWORD", FAKE_PASSWORD)


def load() -> Settings:
    return Settings(_env_file=None)  # pyright: ignore[reportCallIssue]


@pytest.mark.usefixtures("valid_env")
def test_defaults_are_applied() -> None:
    settings = load()
    assert settings.postgres_host == "localhost"
    assert settings.postgres_port == 5433


@pytest.mark.parametrize("missing", ["POSTGRES_DB", "REFDATA_APP_PASSWORD"])
def test_missing_required_variable_raises(
    monkeypatch: pytest.MonkeyPatch, valid_env: None, missing: str
) -> None:
    monkeypatch.delenv(missing)
    with pytest.raises(ValidationError) as exc:
        load()
    assert exc.value.errors()[0]["loc"] == (missing,)


@pytest.mark.parametrize("port", ["1", "5433", "65535"])
def test_valid_port_is_accepted(
    monkeypatch: pytest.MonkeyPatch, valid_env: None, port: str
) -> None:
    monkeypatch.setenv("POSTGRES_PORT", port)
    assert load().postgres_port == int(port)


@pytest.mark.parametrize("port", ["0", "65536", "70000", "-1", "abc", "5433.5", ""])
def test_invalid_port_raises(monkeypatch: pytest.MonkeyPatch, valid_env: None, port: str) -> None:
    monkeypatch.setenv("POSTGRES_PORT", port)
    with pytest.raises(ValidationError) as exc:
        load()
    assert exc.value.errors()[0]["loc"] == ("POSTGRES_PORT",)
    assert FAKE_PASSWORD not in str(exc.value)


def test_empty_database_name_raises(monkeypatch: pytest.MonkeyPatch, valid_env: None) -> None:
    monkeypatch.setenv("POSTGRES_DB", "")
    with pytest.raises(ValidationError):
        load()


@pytest.mark.usefixtures("valid_env")
def test_password_is_hidden_in_text_representations() -> None:
    settings = load()
    assert FAKE_PASSWORD not in repr(settings)
    assert FAKE_PASSWORD not in str(settings)
    assert FAKE_PASSWORD not in settings.model_dump_json()


@pytest.mark.usefixtures("valid_env")
def test_settings_are_immutable() -> None:
    settings = load()
    with pytest.raises(ValidationError):
        settings.postgres_port = 1  # pyright: ignore[reportAttributeAccessIssue]


def test_other_variables_are_ignored(monkeypatch: pytest.MonkeyPatch, valid_env: None) -> None:
    monkeypatch.setenv("POSTGRES_USER", "refdata_owner")
    monkeypatch.setenv("POSTGRES_PASSWORD", "fake-owner-password")
    monkeypatch.setenv("REFDATA_RO_PASSWORD", "fake-ro-password")
    dumped = load().model_dump()
    assert "refdata_ro_password" not in dumped
    assert "fake-ro-password" not in str(dumped)


def test_dotenv_file_with_extra_variables_is_accepted(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "POSTGRES_DB=refdata\n"
        f"REFDATA_APP_PASSWORD={FAKE_PASSWORD}\n"
        "POSTGRES_USER=refdata_owner\n"
        "REFDATA_RO_PASSWORD=fake-ro-password\n"
    )
    settings = Settings()  # pyright: ignore[reportCallIssue]  # lit le .env du dossier courant
    assert settings.postgres_db == "refdata"


@pytest.mark.usefixtures("valid_env")
def test_conninfo_uses_application_role() -> None:
    params = conninfo_to_dict(load().app_conninfo)
    assert params["user"] == APP_ROLE
    assert params["dbname"] == "refdata"
    assert params["host"] == "localhost"
    assert params["port"] == "5433"
    assert params["password"] == FAKE_PASSWORD


def test_conninfo_escapes_special_characters(
    monkeypatch: pytest.MonkeyPatch, valid_env: None
) -> None:
    tricky = "p@ss w'rd:/\\"
    monkeypatch.setenv("REFDATA_APP_PASSWORD", tricky)
    assert conninfo_to_dict(load().app_conninfo)["password"] == tricky


@pytest.mark.usefixtures("valid_env")
def test_redacted_conninfo_has_no_password() -> None:
    redacted = load().app_conninfo_redacted
    assert FAKE_PASSWORD not in redacted
    assert "password" not in conninfo_to_dict(redacted)


@pytest.mark.usefixtures("valid_env")
def test_get_settings_is_cached_until_cleared() -> None:
    first = get_settings()
    assert get_settings() is first
    get_settings.cache_clear()
    assert get_settings() is not first
