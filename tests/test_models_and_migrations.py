from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import BigInteger

from app.models import Account, Transaction


def test_money_columns_use_bigint():
    """INTEGER (32 bits) estouraria em PostgreSQL com saldos acima de ~R$ 21 milhões."""
    assert isinstance(Account.__table__.c.balance_cents.type, BigInteger)
    assert isinstance(Transaction.__table__.c.amount_cents.type, BigInteger)


def test_migrations_have_a_single_head():
    """Evita duas migrações 'filhas' da mesma origem, o que quebraria `alembic upgrade head`."""
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == ["0002_bigint_amounts"]
