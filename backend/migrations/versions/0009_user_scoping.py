"""per-user scoping: add user_id to all owned tables

Revision ID: 0009_user_scoping
Revises: 0008_auth_module
Create Date: 2026-05-28

Adds a NOT NULL user_id FK to every user-owned table. Assumes the owned tables
are empty (dev DB reset) — there is no backfill. cv_chunks / job_requirements
stay parent-scoped (reached only via their owning document/job).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009_user_scoping"
down_revision: str | Sequence[str] | None = "0008_auth_module"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "cv_documents",
    "jobs",
    "match_runs",
    "cover_letter_drafts",
    "cv_tailor_runs",
    "interview_prep_runs",
)


def upgrade() -> None:
    # Job-posting URL uniqueness is now per-user, not global.
    op.execute("ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_source_url_key")

    for table in _TABLES:
        op.execute(
            f"ALTER TABLE {table} "
            "ADD COLUMN user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE"
        )
        op.execute(f"CREATE INDEX {table}_user_id_idx ON {table}(user_id)")

    op.execute(
        "CREATE UNIQUE INDEX jobs_user_source_url_key ON jobs(user_id, source_url) "
        "WHERE source_url IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS jobs_user_source_url_key")
    for table in _TABLES:
        op.execute(f"DROP INDEX IF EXISTS {table}_user_id_idx")
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS user_id")
    op.execute("ALTER TABLE jobs ADD CONSTRAINT jobs_source_url_key UNIQUE (source_url)")
