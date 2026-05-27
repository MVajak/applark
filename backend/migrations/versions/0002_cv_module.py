"""cv module: cv_documents + cv_chunks

Revision ID: 0002_cv_module
Revises: 0001_init_extensions
Create Date: 2026-05-22

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_cv_module"
down_revision: str | Sequence[str] | None = "0001_init_extensions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TYPE cv_document_kind AS ENUM ('cv', 'cover_letter')")

    op.execute(
        """
        CREATE TABLE cv_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            kind cv_document_kind NOT NULL,
            filename TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TYPE cv_chunk_type AS ENUM (
            'summary', 'experience', 'skill', 'education',
            'project', 'language', 'other'
        )
        """
    )

    op.execute(
        """
        CREATE TABLE cv_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL REFERENCES cv_documents(id) ON DELETE CASCADE,
            chunk_type cv_chunk_type NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            chunk_index INTEGER NOT NULL,
            embedding VECTOR(1536),
            embedding_model TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute("CREATE INDEX cv_chunks_document_id_idx ON cv_chunks(document_id)")
    op.execute("CREATE INDEX cv_chunks_chunk_type_idx ON cv_chunks(chunk_type)")
    op.execute(
        "CREATE INDEX cv_chunks_embedding_idx ON cv_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cv_chunks")
    op.execute("DROP TABLE IF EXISTS cv_documents")
    op.execute("DROP TYPE IF EXISTS cv_chunk_type")
    op.execute("DROP TYPE IF EXISTS cv_document_kind")
