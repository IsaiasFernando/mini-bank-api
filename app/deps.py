import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.models.account import Account

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.", headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = decode_access_token(token)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_error
    user = db.get(User, user_id)
    if user is None:
        raise credentials_error
    return user


def get_current_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Account:
    account = db.scalar(select(Account).where(Account.user_id == current_user.id))
    if account is None:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    return account
