"""interview_prep module: interview_prep_runs

Revision ID: 0007_interview_prep_module
Revises: 0006_cv_tailor_module
Create Date: 2026-05-22

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007_interview_prep_module"
down_revision: str | Sequence[str] | None = "0006_cv_tailor_module"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE interview_prep_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            role_overview TEXT NOT NULL,
            likely_areas_of_focus JSONB NOT NULL,
            questions JSONB NOT NULL,
            questions_to_ask_them JSONB NOT NULL,
            llm_model TEXT NOT NULL,
            input_tokens INTEGER,
            output_tokens INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX interview_prep_runs_job_id_idx ON interview_prep_runs(job_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS interview_prep_runs")
