"""cv_documents.candidate_name + cover_letter_drafts

Revision ID: 0005_cover_letters_module
Revises: 0004_matching_module
Create Date: 2026-05-22

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_cover_letters_module"
down_revision: str | Sequence[str] | None = "0004_matching_module"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # M1 omission: the CV chunker extracts candidate_name on the agent's
    # CVExtraction output but the column never existed. Add it as nullable
    # so existing rows survive (they'll be NULL until re-uploaded).
    op.execute("ALTER TABLE cv_documents ADD COLUMN candidate_name TEXT")

    op.execute(
        """
        CREATE TABLE cover_letter_drafts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            match_run_id UUID REFERENCES match_runs(id) ON DELETE SET NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            referenced_chunks JSONB NOT NULL DEFAULT '[]'::jsonb,
            tone TEXT,
            llm_model TEXT NOT NULL,
            input_tokens INTEGER,
            output_tokens INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX cover_letter_drafts_job_id_idx ON cover_letter_drafts(job_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cover_letter_drafts")
    op.execute("ALTER TABLE cv_documents DROP COLUMN IF EXISTS candidate_name")
