import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Remove variáveis que poderiam vir do seu terminal ou do ambiente de teste."""
    for name in ("ENVIRONMENT", "SECRET_KEY", "CORS_ORIGINS"):
        monkeypatch.delenv(name, raising=False)


def make_settings(**kwargs):
    # _env_file=None impede a leitura do seu .env real.
    return Settings(_env_file=None, **kwargs)


def test_development_environment_allows_development_secret():
    assert make_settings(environment="development").environment == "development"


def test_test_environment_allows_development_secret():
    assert make_settings(environment="test").environment == "test"


def test_default_environment_is_production_and_rejects_default_secret():
    """Falha fechada: sem ENVIRONMENT definido, a chave padrão não é aceita."""
    with pytest.raises(ValidationError, match="SECRET_KEY insegura"):
        make_settings()


def test_production_rejects_default_secret():
    with pytest.raises(ValidationError, match="SECRET_KEY insegura"):
        make_settings(environment="production")


def test_production_rejects_example_secret():
    with pytest.raises(ValidationError, match="SECRET_KEY insegura"):
        make_settings(environment="production",
                      secret_key="replace-with-a-long-random-secret-at-least-32-characters")


def test_production_rejects_short_secret():
    with pytest.raises(ValidationError, match="SECRET_KEY insegura"):
        make_settings(environment="production", secret_key="curta")


def test_production_accepts_strong_secret():
    settings = make_settings(environment="production", secret_key="a" * 48)
    assert settings.secret_key == "a" * 48


def test_cors_origins_accepts_comma_separated_values(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://a.example.com, http://b.example.com")
    settings = make_settings(environment="test")
    assert settings.cors_origins == ["http://a.example.com", "http://b.example.com"]


def test_cors_origins_accepts_json_list(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["http://a.example.com","http://b.example.com"]')
    settings = make_settings(environment="test")
    assert settings.cors_origins == ["http://a.example.com", "http://b.example.com"]
