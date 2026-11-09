from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated
from app.models.transaction import TransactionType

Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class AmountInput(BaseModel):
    amount_cents: int = Field(gt=0)


class AccountOut(BaseModel):
    number: str
    balance_cents: int
    currency: str = "BRL"
    model_config = ConfigDict(from_attributes=True)


class TransferCreate(AmountInput):
    to_account_number: Annotated[str, StringConstraints(strip_whitespace=True, min_length=6, max_length=20)]
    description: Description | None = None


class TransferOut(BaseModel):
    message: str = "Transferência realizada com sucesso."
    transaction_id: int
    amount_cents: int
    to_account_number: str


class TransactionOut(BaseModel):
    id: int
    type: TransactionType
    direction: str
    amount_cents: int
    description: str | None
    created_at: datetime


class StatementOut(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    size: int
