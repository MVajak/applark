"""matching module: match_runs

Revision ID: 0004_matching_module
Revises: 0003_jobs_module
Create Date: 2026-05-22

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004_matching_module"
down_revision: str | Sequence[str] | None = "0003_jobs_module"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE match_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            overall_score DOUBLE PRECISION NOT NULL,
            summary TEXT NOT NULL,
            details JSONB NOT NULL,
            llm_model TEXT NOT NULL,
            input_tokens INTEGER,
            output_tokens INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX match_runs_job_id_idx ON match_runs(job_id)")
    op.execute("CREATE INDEX match_runs_score_idx ON match_runs(overall_score DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS match_runs")
