"""Create initial banking tables."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=20), nullable=False),
        sa.Column("balance_cents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("balance_cents >= 0", name="ck_accounts_balance_non_negative"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"))
    op.create_index("ix_accounts_id", "accounts", ["id"])
    op.create_index("ix_accounts_number", "accounts", ["number"], unique=True)
    op.create_table("transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("from_account_id", sa.Integer(), nullable=True),
        sa.Column("to_account_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount_cents > 0", name="ck_transactions_amount_positive"),
        sa.CheckConstraint(
            "(type = 'deposit' AND from_account_id IS NULL AND to_account_id IS NOT NULL) OR "
            "(type = 'withdraw' AND from_account_id IS NOT NULL AND to_account_id IS NULL) OR "
            "(type = 'transfer' AND from_account_id IS NOT NULL AND to_account_id IS NOT NULL)",
            name="ck_transactions_account_direction"),
        sa.ForeignKeyConstraint(["from_account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["to_account_id"], ["accounts.id"]))
    op.create_index("ix_transactions_id", "transactions", ["id"])
    op.create_index("ix_transactions_from_account_id", "transactions", ["from_account_id"])
    op.create_index("ix_transactions_to_account_id", "transactions", ["to_account_id"])
    op.create_index("ix_transactions_created_at", "transactions", ["created_at"])


def downgrade():
    op.drop_table("transactions")
    op.drop_table("accounts")
    op.drop_table("users")
