"""Usa BIGINT nas colunas de dinheiro (saldo e valor das transações).

Com INTEGER (32 bits) o PostgreSQL rejeita valores acima de 2.147.483.647 centavos
(cerca de R$ 21,4 milhões), o que causaria erro 500 após alguns depósitos altos.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_bigint_amounts"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _is_sqlite() -> bool:
    return op.get_context().dialect.name == "sqlite"


def upgrade():
    if _is_sqlite():
        return  # INTEGER do SQLite já armazena até 64 bits; não há o que alterar.
    op.alter_column("accounts", "balance_cents",
                    existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)
    op.alter_column("transactions", "amount_cents",
                    existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False)


def downgrade():
    if _is_sqlite():
        return
    # Atenção: falha se já existirem valores acima do limite de 32 bits.
    op.alter_column("transactions", "amount_cents",
                    existing_type=sa.BigInteger(), type_=sa.Integer(), existing_nullable=False)
    op.alter_column("accounts", "balance_cents",
                    existing_type=sa.BigInteger(), type_=sa.Integer(), existing_nullable=False)
