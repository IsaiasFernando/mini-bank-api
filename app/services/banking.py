import secrets
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.services.exceptions import InsufficientFunds, AccountNotFound, SameAccount, InvalidAmount
from app.core.config import settings


def generate_account_number(db: Session) -> str:
    # Unique constraint remains the final safeguard against the extremely unlikely collision.
    for _ in range(10):
        number = f"{secrets.randbelow(10**10):010d}"
        if not db.scalar(select(Account.id).where(Account.number == number)):
            return number
    raise RuntimeError("Could not generate a unique account number")


def create_account_for_user(db: Session, user_id: int) -> Account:
    account = Account(user_id=user_id, number=generate_account_number(db), balance_cents=0)
    db.add(account)
    return account


def _validate_amount(amount_cents: int) -> None:
    if amount_cents <= 0:
        raise InvalidAmount("O valor deve ser maior que zero.")
    if amount_cents > settings.max_transaction_cents:
        raise InvalidAmount("O valor excede o limite permitido por operação.")


def deposit(db: Session, account: Account, amount_cents: int, description: str | None = None) -> Account:
    _validate_amount(amount_cents)
    try:
        locked = db.scalar(select(Account).where(Account.id == account.id).with_for_update().execution_options(populate_existing=True))
        if locked is None:
            raise AccountNotFound("Conta não encontrada.")
        locked.balance_cents += amount_cents
        db.add(Transaction(type=TransactionType.DEPOSIT, amount_cents=amount_cents,
                           to_account_id=locked.id, description=description or "Depósito"))
        db.commit()
        db.refresh(locked)
        return locked
    except Exception:
        db.rollback()
        raise


def withdraw(db: Session, account: Account, amount_cents: int, description: str | None = None) -> Account:
    _validate_amount(amount_cents)
    try:
        locked = db.scalar(select(Account).where(Account.id == account.id).with_for_update().execution_options(populate_existing=True))
        if locked is None:
            raise AccountNotFound("Conta não encontrada.")
        if locked.balance_cents < amount_cents:
            raise InsufficientFunds("Saldo insuficiente para realizar o saque.")
        locked.balance_cents -= amount_cents
        db.add(Transaction(type=TransactionType.WITHDRAW, amount_cents=amount_cents,
                           from_account_id=locked.id, description=description or "Saque"))
        db.commit()
        db.refresh(locked)
        return locked
    except Exception:
        db.rollback()
        raise


def transfer(db: Session, from_account: Account, to_number: str, amount_cents: int,
             description: str | None = None) -> Transaction:
    _validate_amount(amount_cents)
    try:
        destination_id = db.scalar(select(Account.id).where(Account.number == to_number))
        if destination_id is None:
            raise AccountNotFound("Conta de destino não encontrada.")
        if destination_id == from_account.id:
            raise SameAccount("Não é permitido transferir para a própria conta.")

        # Lock both rows in a deterministic order to reduce deadlock risk on PostgreSQL.
        ids = sorted([from_account.id, destination_id])
        locked_accounts = db.scalars(
            select(Account).where(Account.id.in_(ids)).order_by(Account.id).with_for_update()
            .execution_options(populate_existing=True)
        ).all()
        accounts = {account.id: account for account in locked_accounts}
        source = accounts.get(from_account.id)
        destination = accounts.get(destination_id)
        if source is None or destination is None:
            raise AccountNotFound("Conta de origem ou destino não encontrada.")
        if source.balance_cents < amount_cents:
            raise InsufficientFunds("Saldo insuficiente para realizar a transferência.")

        source.balance_cents -= amount_cents
        destination.balance_cents += amount_cents
        transaction = Transaction(type=TransactionType.TRANSFER, amount_cents=amount_cents,
                                  from_account_id=source.id, to_account_id=destination.id,
                                  description=description or "Transferência")
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction
    except Exception:
        db.rollback()
        raise


def get_statement(db: Session, account_id: int, start=None, end=None, page: int = 1, size: int = 20):
    conditions = or_(Transaction.from_account_id == account_id, Transaction.to_account_id == account_id)
    query = select(Transaction).where(conditions)
    count_query = select(func.count(Transaction.id)).where(conditions)
    if start is not None:
        query = query.where(Transaction.created_at >= start)
        count_query = count_query.where(Transaction.created_at >= start)
    if end is not None:
        query = query.where(Transaction.created_at <= end)
        count_query = count_query.where(Transaction.created_at <= end)
    total = db.scalar(count_query) or 0
    items = db.scalars(query.order_by(Transaction.created_at.desc(), Transaction.id.desc())
                       .offset((page - 1) * size).limit(size)).all()
    return items, total
