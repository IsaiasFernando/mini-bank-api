from datetime import datetime
from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("balance_cents >= 0", name="ck_accounts_balance_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    balance_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user: Mapped["User"] = relationship(back_populates="account")
