import os
from urllib.parse import quote

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    port: int = 8787
    client_origin: str = "http://localhost:5173"

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "history_user"
    mysql_password: str = "history_pass"
    mysql_database: str = "historical_pairing"

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"

    # JWT settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    @model_validator(mode="after")
    def check_jwt_secret(self) -> "Settings":
        if self.jwt_secret_key == "your-secret-key-change-in-production":
            if os.getenv("JWI_SKIP_SECRET_CHECK") is None:
                raise ValueError(
                    "jwt_secret_key must be set via JWI_SKIP_SECRET_CHECK=1 env var to bypass, "
                    "or set a proper secret in .env (JWT_SECRET_KEY=...)"
                )
        return self

    @property
    def database_url(self) -> str:
        encoded_password = quote(self.mysql_password, safe="")
        return (
            f"mysql+pymysql://{self.mysql_user}:{encoded_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )


settings = Settings()
