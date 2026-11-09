from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.deps import get_current_account
from app.models.account import Account
from app.models.transaction import TransactionType
from app.schemas.banking import AmountInput, AccountOut, StatementOut, TransactionOut
from app.services.banking import deposit, withdraw, get_statement

router = APIRouter(prefix="/accounts", tags=["Contas"])


@router.get("/me", response_model=AccountOut)
def read_account(account: Account = Depends(get_current_account)):
    return account


@router.post("/me/deposit", response_model=AccountOut)
def make_deposit(payload: AmountInput, db: Session = Depends(get_db), account: Account = Depends(get_current_account)):
    return deposit(db, account, payload.amount_cents)


@router.post("/me/withdraw", response_model=AccountOut)
def make_withdrawal(payload: AmountInput, db: Session = Depends(get_db), account: Account = Depends(get_current_account)):
    return withdraw(db, account, payload.amount_cents)


@router.get("/me/statement", response_model=StatementOut)
def statement(start: datetime | None = None, end: datetime | None = None,
              page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
              db: Session = Depends(get_db), account: Account = Depends(get_current_account)):
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="A data inicial deve ser anterior à data final.")
    items, total = get_statement(db, account.id, start, end, page, size)
    output = []
    for item in items:
        direction = "in" if item.to_account_id == account.id else "out"
        output.append(TransactionOut(id=item.id, type=item.type, direction=direction,
            amount_cents=item.amount_cents, description=item.description, created_at=item.created_at))
    return StatementOut(items=output, total=total, page=page, size=size)
