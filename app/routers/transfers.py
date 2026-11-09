from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.deps import get_current_account
from app.models.account import Account
from app.schemas.banking import TransferCreate, TransferOut
from app.services.banking import transfer

router = APIRouter(prefix="/transfers", tags=["Transferências"])


@router.post("", status_code=201, response_model=TransferOut)
def make_transfer(payload: TransferCreate, db: Session = Depends(get_db), account: Account = Depends(get_current_account)):
    transaction = transfer(db, account, payload.to_account_number, payload.amount_cents, payload.description)
    return TransferOut(transaction_id=transaction.id, amount_cents=transaction.amount_cents,
                       to_account_number=payload.to_account_number)
