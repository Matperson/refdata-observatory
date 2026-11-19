from functools import lru_cache
from typing import Final

from psycopg.conninfo import make_conninfo
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ROLE: Final = "refdata_app"


class Settings(BaseSettings):
    # connection à PostgresSQL - rôle applicatif

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        frozen=True,
    )

    postgres_db: str = Field(min_length=1, validation_alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", min_length=1, validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5433, ge=1, le=65535, validation_alias="POSTGRES_PORT")
    app_password: SecretStr = Field(min_length=1, validation_alias="REFDATA_APP_PASSWORD")

    @property
    def app_conninfo(self) -> str:
        # Paramètres de connexion complets - contient mot de passe - non journalisable
        return make_conninfo(
            host=self.postgres_host,
            port=self.postgres_port,
            dbname=self.postgres_db,
            user=APP_ROLE,
            password=self.app_password.get_secret_value(),
        )

    @property
    def app_conninfo_redacted(self) -> str:
        # Paramètres de connexion sans mot de passe - journalisable
        return make_conninfo(
            host=self.postgres_host, port=self.postgres_port, dbname=self.postgres_db, user=APP_ROLE
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
