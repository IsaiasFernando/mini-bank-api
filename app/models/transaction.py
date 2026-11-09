import enum
from datetime import datetime
from sqlalchemy import BigInteger, CheckConstraint, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRANSFER = "transfer"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_transactions_amount_positive"),
        CheckConstraint(
            "(type = 'deposit' AND from_account_id IS NULL AND to_account_id IS NOT NULL) OR "
            "(type = 'withdraw' AND from_account_id IS NOT NULL AND to_account_id IS NULL) OR "
            "(type = 'transfer' AND from_account_id IS NOT NULL AND to_account_id IS NOT NULL)",
            name="ck_transactions_account_direction",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type: Mapped[TransactionType] = mapped_column(
        Enum(
            TransactionType,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    from_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True, index=True)
    to_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
