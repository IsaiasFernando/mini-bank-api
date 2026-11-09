import os

# Ambiente de teste hermético: precisa vir ANTES de importar a aplicação, que lê as
# configurações ao ser importada. Assim um .env ou variáveis do seu terminal não
# interferem nos testes.
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["RATE_LIMIT_LOGIN"] = "5/minute"

import pytest  # noqa: E402
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User, Account, Transaction

TEST_DATABASE_URL = "sqlite://"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Evita que o limite de um teste contamine os testes seguintes."""
    limiter = app.state.limiter
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def create_user(client):
    def _create(name="Teste", email="teste@example.com", password="SenhaForte123"):
        response = client.post("/auth/register", json={"name": name, "email": email, "password": password})
        assert response.status_code == 201, response.text
        login = client.post("/auth/login", data={"username": email, "password": password})
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        return {"token": token, "headers": {"Authorization": f"Bearer {token}"}, "user": response.json()}
    return _create
