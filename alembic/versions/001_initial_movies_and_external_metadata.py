"""Initial movies and external_metadata tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "movies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_title", sa.String(length=512), nullable=False),
        sa.Column(
            "media_type",
            sa.Enum("film", name="media_type", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "first_indexed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "external_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movie_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_id", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payload_version", sa.String(length=32), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "provider_id",
            name="uq_external_metadata_provider_provider_id",
        ),
    )
    op.create_index(
        op.f("ix_external_metadata_movie_id"),
        "external_metadata",
        ["movie_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_external_metadata_movie_id"), table_name="external_metadata")
    op.drop_table("external_metadata")
    op.drop_table("movies")
