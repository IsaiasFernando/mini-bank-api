from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from app.core.config import settings

_password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"

# Hash descartável usado no login quando o e-mail não existe. Assim o tempo de resposta
# fica parecido com o de uma senha errada e não revela quais e-mails estão cadastrados.
DUMMY_PASSWORD_HASH = _password_hash.hash("senha-descartavel-que-nunca-pertence-a-uma-conta")


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_hash.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    subject = payload.get("sub")
    if not subject or not str(subject).isdigit():
        raise jwt.InvalidTokenError("Invalid token subject")
    return int(subject)
