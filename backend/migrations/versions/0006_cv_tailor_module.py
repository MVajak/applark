"""cv_tailor module: cv_tailor_runs

Revision ID: 0006_cv_tailor_module
Revises: 0005_cover_letters_module
Create Date: 2026-05-22

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006_cv_tailor_module"
down_revision: str | Sequence[str] | None = "0005_cover_letters_module"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE cv_tailor_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            job_summary TEXT NOT NULL,
            suggestions JSONB NOT NULL,
            do_not_suggest JSONB NOT NULL,
            llm_model TEXT NOT NULL,
            input_tokens INTEGER,
            output_tokens INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX cv_tailor_runs_job_id_idx ON cv_tailor_runs(job_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cv_tailor_runs")
