"""jobs module: jobs + job_requirements

Revision ID: 0003_jobs_module
Revises: 0002_cv_module
Create Date: 2026-05-22

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003_jobs_module"
down_revision: str | Sequence[str] | None = "0002_cv_module"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TYPE job_source_kind AS ENUM ('url', 'pasted')")
    op.execute(
        "CREATE TYPE job_status AS ENUM "
        "('pending', 'scraping', 'extracting', 'ready', 'failed')"
    )
    op.execute(
        "CREATE TYPE remote_policy AS ENUM "
        "('onsite', 'hybrid', 'remote', 'unspecified')"
    )
    op.execute(
        "CREATE TYPE seniority AS ENUM "
        "('junior', 'mid', 'senior', 'lead', 'principal', 'unspecified')"
    )

    op.execute(
        """
        CREATE TABLE jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_url TEXT UNIQUE,
            source_kind job_source_kind NOT NULL,
            raw_text TEXT NOT NULL,
            status job_status NOT NULL DEFAULT 'pending',
            error_message TEXT,
            title TEXT,
            company TEXT,
            location TEXT,
            remote_policy remote_policy DEFAULT 'unspecified',
            seniority seniority DEFAULT 'unspecified',
            tech_stack TEXT[] NOT NULL DEFAULT '{}',
            salary_range TEXT,
            summary TEXT,
            raw_extraction JSONB,
            embedding VECTOR(1536),
            embedding_model TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute("CREATE INDEX jobs_status_idx ON jobs(status)")
    op.execute("CREATE INDEX jobs_company_idx ON jobs(company)")
    op.execute("CREATE INDEX jobs_created_at_idx ON jobs(created_at DESC)")
    op.execute(
        "CREATE INDEX jobs_embedding_idx ON jobs "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    op.execute(
        "CREATE TYPE requirement_category AS ENUM "
        "('required', 'nice_to_have', 'responsibility')"
    )

    op.execute(
        """
        CREATE TABLE job_requirements (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            category requirement_category NOT NULL,
            embedding VECTOR(1536),
            embedding_model TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute("CREATE INDEX job_requirements_job_id_idx ON job_requirements(job_id)")
    op.execute(
        "CREATE INDEX job_requirements_embedding_idx ON job_requirements "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS job_requirements")
    op.execute("DROP TYPE IF EXISTS requirement_category")
    op.execute("DROP TABLE IF EXISTS jobs")
    op.execute("DROP TYPE IF EXISTS seniority")
    op.execute("DROP TYPE IF EXISTS remote_policy")
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS job_source_kind")
