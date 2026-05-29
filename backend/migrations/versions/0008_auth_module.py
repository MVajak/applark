"""auth module: users + otp_codes

Revision ID: 0008_auth_module
Revises: 0007_interview_prep_module
Create Date: 2026-05-28

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008_auth_module"
down_revision: str | Sequence[str] | None = "0007_interview_prep_module"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE otp_codes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            code_hash TEXT NOT NULL,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            expires_at TIMESTAMPTZ NOT NULL,
            used_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX otp_codes_user_id_idx ON otp_codes(user_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS otp_codes")
    op.execute("DROP TABLE IF EXISTS users")
