from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import DUMMY_PASSWORD_HASH, hash_password, verify_password, create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserOut, Token
from app.services.banking import create_account_for_user
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Autenticação"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = str(payload.email).lower()  # e-mails são comparados sempre em minúsculas
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Este e-mail já está cadastrado.")
    try:
        user = User(name=payload.name, email=email, password_hash=hash_password(payload.password))
        db.add(user)
        db.flush()
        create_account_for_user(db, user.id)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível cadastrar este e-mail.")
    except Exception:
        db.rollback()
        raise


@router.post("/login", response_model=Token)
@limiter.limit(settings.rate_limit_login)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form_data.username.lower()))
    # Sempre verifica um hash (o do usuário ou um descartável) para que o tempo de resposta
    # não revele se o e-mail existe.
    password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_ok = verify_password(form_data.password, password_hash)
    if user is None or not password_ok:
        raise HTTPException(status_code=401, detail="Credenciais inválidas.", headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_access_token(user.id))
