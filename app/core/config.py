import json
from functools import lru_cache
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Ambientes em que a chave de exemplo é tolerada. Qualquer outro valor (inclusive
# a ausência da variável) é tratado como produção e exige uma SECRET_KEY forte.
LOCAL_ENVIRONMENTS = {"development", "dev", "test", "testing"}

INSECURE_SECRET_KEYS = {
    "development-only-change-this-secret-key-32chars",
    "replace-with-a-long-random-secret-at-least-32-characters",
    "change-me",
    "changeme",
}


class Settings(BaseSettings):
    app_name: str = "Mini Bank API"
    # Falha fechada: sem ENVIRONMENT definido, a aplicação assume produção.
    environment: str = "production"
    database_url: str = "sqlite:///./mini_bank.db"
    secret_key: str = "development-only-change-this-secret-key-32chars"
    access_token_expire_minutes: int = 30
    # NoDecode: o valor chega como texto e é interpretado pelo validador abaixo,
    # aceitando "a,b" (separado por vírgula) ou '["a","b"]' (JSON).
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    max_transaction_cents: int = 100_000_000
    rate_limit_login: str = "5/minute"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_secret_key_for_environment(self):
        environment = self.environment.strip().lower()
        if environment not in LOCAL_ENVIRONMENTS:
            if self.secret_key in INSECURE_SECRET_KEYS or len(self.secret_key) < 32:
                raise ValueError(
                    "SECRET_KEY insegura: defina uma chave aleatória com pelo menos 32 caracteres. "
                    "Para uso local, defina também ENVIRONMENT=development."
                )
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("["):
                return json.loads(value)
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
