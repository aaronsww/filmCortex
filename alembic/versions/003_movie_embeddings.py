"""Add movie_embeddings table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from filmcortex.config.settings import settings

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "movie_embeddings",
        sa.Column("movie_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding", Vector(settings.embedding_dimensions), nullable=False),
        sa.Column("embedded_text", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_revision", sa.String(length=128), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("movie_id"),
    )


def downgrade() -> None:
    op.drop_table("movie_embeddings")
