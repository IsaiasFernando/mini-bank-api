from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.security import ALGORITHM


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def _make_token(user_id=1, key=None, expires_in=timedelta(minutes=5)):
    payload = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + expires_in}
    return jwt.encode(payload, key or settings.secret_key, algorithm=ALGORITHM)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_login_and_duplicate_email(client, create_user):
    user = create_user()
    assert user["user"]["email"] == "teste@example.com"
    duplicate = client.post("/auth/register", json={"name": "Outro", "email": "teste@example.com", "password": "SenhaForte123"})
    assert duplicate.status_code == 409


def test_login_invalid_credentials(client, create_user):
    create_user()
    response = client.post("/auth/login", data={"username": "teste@example.com", "password": "senha-errada"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas."


def test_protected_route_requires_token(client):
    assert client.get("/users/me").status_code == 401


def test_deposit_withdraw_and_statement(client, create_user):
    user = create_user()
    headers = user["headers"]
    account = client.get("/accounts/me", headers=headers).json()
    assert account["balance_cents"] == 0
    deposit = client.post("/accounts/me/deposit", json={"amount_cents": 10000}, headers=headers)
    assert deposit.status_code == 200
    assert deposit.json()["balance_cents"] == 10000
    withdraw = client.post("/accounts/me/withdraw", json={"amount_cents": 2500}, headers=headers)
    assert withdraw.status_code == 200
    assert withdraw.json()["balance_cents"] == 7500
    statement = client.get("/accounts/me/statement?page=1&size=10", headers=headers)
    assert statement.status_code == 200
    assert statement.json()["total"] == 2
    assert {item["direction"] for item in statement.json()["items"]} == {"in", "out"}


def test_invalid_deposit_and_insufficient_withdrawal(client, create_user):
    user = create_user()
    headers = user["headers"]
    assert client.post("/accounts/me/deposit", json={"amount_cents": 0}, headers=headers).status_code == 422
    response = client.post("/accounts/me/withdraw", json={"amount_cents": 100}, headers=headers)
    assert response.status_code == 422
    assert "Saldo insuficiente" in response.json()["detail"]


def test_transfer_success_and_balances(client, create_user):
    first = create_user(email="first@example.com")
    second = create_user(name="Segundo", email="second@example.com")
    client.post("/accounts/me/deposit", json={"amount_cents": 5000}, headers=first["headers"])
    destination = client.get("/accounts/me", headers=second["headers"]).json()["number"]
    response = client.post("/transfers", json={"to_account_number": destination, "amount_cents": 1700}, headers=first["headers"])
    assert response.status_code == 201, response.text
    assert client.get("/accounts/me", headers=first["headers"]).json()["balance_cents"] == 3300
    assert client.get("/accounts/me", headers=second["headers"]).json()["balance_cents"] == 1700


def test_transfer_rejects_missing_same_and_insufficient(client, create_user):
    first = create_user(email="first@example.com")
    second = create_user(email="second@example.com")
    own_number = client.get("/accounts/me", headers=first["headers"]).json()["number"]
    second_number = client.get("/accounts/me", headers=second["headers"]).json()["number"]
    own = client.post("/transfers", json={"to_account_number": own_number, "amount_cents": 1}, headers=first["headers"])
    assert own.status_code == 422
    missing = client.post("/transfers", json={"to_account_number": "9999999999", "amount_cents": 1}, headers=first["headers"])
    assert missing.status_code == 404
    insufficient = client.post("/transfers", json={"to_account_number": second_number, "amount_cents": 1}, headers=first["headers"])
    assert insufficient.status_code == 422


def test_statement_pagination(client, create_user):
    user = create_user()
    headers = user["headers"]
    for amount in [100, 200, 300]:
        client.post("/accounts/me/deposit", json={"amount_cents": amount}, headers=headers)
    page = client.get("/accounts/me/statement?page=2&size=2", headers=headers).json()
    assert page["total"] == 3
    assert len(page["items"]) == 1


def test_login_rate_limit_returns_429(client):
    """O sexto login no mesmo minuto deve ser bloqueado pelo SlowAPI."""
    responses = [
        client.post("/auth/login", data={"username": "nao-existe@example.com", "password": "senha-invalida"})
        for _ in range(6)
    ]
    assert [response.status_code for response in responses[:5]] == [401] * 5
    assert responses[5].status_code == 429


# --- Autenticação: tokens inválidos -------------------------------------------------

def test_expired_token_is_rejected(client):
    token = _make_token(expires_in=timedelta(minutes=-1))
    assert client.get("/users/me", headers=_bearer(token)).status_code == 401


def test_token_signed_with_wrong_key_is_rejected(client):
    token = _make_token(key="outra-chave-que-nao-e-a-da-aplicacao-123456")
    assert client.get("/users/me", headers=_bearer(token)).status_code == 401


def test_malformed_token_is_rejected(client):
    assert client.get("/users/me", headers=_bearer("isto-nao-e-um-jwt")).status_code == 401


def test_valid_token_for_nonexistent_user_is_rejected(client):
    token = _make_token(user_id=999)
    assert client.get("/users/me", headers=_bearer(token)).status_code == 401


# --- Cadastro e login ---------------------------------------------------------------

@pytest.mark.parametrize("payload", [
    {"name": "Maria", "email": "nao-e-email", "password": "SenhaForte123"},
    {"name": "Maria", "email": "maria@example.com", "password": "curta"},
    {"name": "M", "email": "maria@example.com", "password": "SenhaForte123"},
])
def test_register_rejects_invalid_payload(client, payload):
    assert client.post("/auth/register", json=payload).status_code == 422


def test_email_is_case_insensitive(client, create_user):
    user = create_user(email="Maria@Example.com")
    assert user["user"]["email"] == "maria@example.com"
    duplicate = client.post("/auth/register",
                            json={"name": "Outra", "email": "MARIA@example.com", "password": "SenhaForte123"})
    assert duplicate.status_code == 409


def test_login_error_is_identical_for_unknown_email_and_wrong_password(client, create_user):
    create_user()
    wrong_password = client.post("/auth/login", data={"username": "teste@example.com", "password": "errada-123"})
    unknown_email = client.post("/auth/login", data={"username": "ninguem@example.com", "password": "errada-123"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


# --- Limites de valor ---------------------------------------------------------------

def test_amount_above_operation_limit_is_rejected(client, create_user):
    headers = create_user()["headers"]
    too_much = settings.max_transaction_cents + 1
    deposit = client.post("/accounts/me/deposit", json={"amount_cents": too_much}, headers=headers)
    assert deposit.status_code == 422
    assert "limite" in deposit.json()["detail"]
    withdraw = client.post("/accounts/me/withdraw", json={"amount_cents": too_much}, headers=headers)
    assert withdraw.status_code == 422
    assert "limite" in withdraw.json()["detail"]


def test_amount_at_operation_limit_is_accepted(client, create_user):
    headers = create_user()["headers"]
    limit = settings.max_transaction_cents
    response = client.post("/accounts/me/deposit", json={"amount_cents": limit}, headers=headers)
    assert response.status_code == 200
    assert response.json()["balance_cents"] == limit


def test_balance_can_exceed_32_bit_integer_range(client, create_user):
    """Regressão: com INTEGER (32 bits) o PostgreSQL rejeitaria saldos acima de 2.147.483.647 centavos."""
    headers = create_user()["headers"]
    limit = settings.max_transaction_cents
    deposits = (2**31 // limit) + 2
    for _ in range(deposits):
        assert client.post("/accounts/me/deposit", json={"amount_cents": limit}, headers=headers).status_code == 200
    balance = client.get("/accounts/me", headers=headers).json()["balance_cents"]
    assert balance == deposits * limit
    assert balance > 2**31 - 1


# --- Extrato e transferência --------------------------------------------------------

def test_statement_date_filters_and_invalid_range(client, create_user):
    headers = create_user()["headers"]
    client.post("/accounts/me/deposit", json={"amount_cents": 1000}, headers=headers)
    future, past = "2100-01-01T00:00:00Z", "2000-01-01T00:00:00Z"

    def total(query):
        return client.get(f"/accounts/me/statement?{query}", headers=headers).json()["total"]

    assert total(f"start={future}") == 0
    assert total(f"end={future}") == 1
    assert total(f"start={past}") == 1
    assert total(f"end={past}") == 0
    invalid = client.get(f"/accounts/me/statement?start={future}&end={past}", headers=headers)
    assert invalid.status_code == 422


def test_transfer_response_and_statement_directions(client, create_user):
    first = create_user(email="first@example.com")
    second = create_user(name="Segundo", email="second@example.com")
    client.post("/accounts/me/deposit", json={"amount_cents": 5000}, headers=first["headers"])
    destination = client.get("/accounts/me", headers=second["headers"]).json()["number"]
    response = client.post("/transfers",
                           json={"to_account_number": destination, "amount_cents": 1200, "description": "Aluguel"},
                           headers=first["headers"])
    assert response.status_code == 201
    body = response.json()
    assert body["amount_cents"] == 1200
    assert body["to_account_number"] == destination
    assert isinstance(body["transaction_id"], int)
    sent = client.get("/accounts/me/statement", headers=first["headers"]).json()["items"][0]
    received = client.get("/accounts/me/statement", headers=second["headers"]).json()["items"][0]
    assert (sent["type"], sent["direction"]) == ("transfer", "out")
    assert (received["type"], received["direction"]) == ("transfer", "in")
    assert received["description"] == "Aluguel"
