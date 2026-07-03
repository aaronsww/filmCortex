from filmcortex.config.settings import settings
from filmcortex.models import MovieEmbedding


def test_table_name() -> None:
    assert MovieEmbedding.__tablename__ == "movie_embeddings"


def test_movie_id_is_primary_key() -> None:
    assert MovieEmbedding.__table__.c.movie_id.primary_key is True


def test_embedding_dimension_matches_settings() -> None:
    embedding_column = MovieEmbedding.__table__.c.embedding
    assert embedding_column.type.dim == settings.embedding_dimensions


def test_model_revision_is_nullable() -> None:
    assert MovieEmbedding.__table__.c.model_revision.nullable is True


def test_embedded_text_is_not_nullable() -> None:
    assert MovieEmbedding.__table__.c.embedded_text.nullable is False
