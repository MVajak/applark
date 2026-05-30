"""billing: user tier + credits + credit_ledger

Revision ID: 0010_billing
Revises: 0009_user_scoping
Create Date: 2026-05-29

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010_billing"
down_revision: str | Sequence[str] | None = "0009_user_scoping"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN tier TEXT NOT NULL DEFAULT 'none'")
    op.execute("ALTER TABLE users ADD COLUMN credits INTEGER NOT NULL DEFAULT 0")
    op.execute(
        """
        CREATE TABLE credit_ledger (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            delta INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            reason TEXT NOT NULL,
            feature TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX credit_ledger_user_id_idx ON credit_ledger(user_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS credit_ledger")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS credits")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS tier")
