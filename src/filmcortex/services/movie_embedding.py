import logging
from dataclasses import dataclass

from filmcortex.config.settings import settings
from filmcortex.models.external_metadata import ExternalMetadata
from filmcortex.models.movie import Movie
from filmcortex.repositories.movie_embedding_repository import MovieEmbeddingRepository
from filmcortex.utils.embedding_text import build_embedding_text

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingStats:
    pending: int = 0
    generated: int = 0
    failed: int = 0


class MovieEmbeddingService:
    def __init__(
        self,
        embedding_repository: MovieEmbeddingRepository,
        model_name: str | None = None,
    ) -> None:
        self._repository = embedding_repository
        self._model_name = model_name or settings.embedding_model_name
        self._model = None
        self._model_revision: str | None = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
            self._model_revision = self._extract_revision(self._model)
        return self._model

    @staticmethod
    def _extract_revision(model) -> str | None:
        # Best-effort only: sentence-transformers has no stable revision API.
        # Leaving this NULL is acceptable for reproducibility purposes.
        card = getattr(model, "model_card_data", None)
        return getattr(card, "base_model_revision", None)

    def embed_text(self, text: str) -> list[float]:
        model = self._load_model()
        vector = model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    async def generate_for_movie(self, movie: Movie, metadata: ExternalMetadata) -> None:
        text = build_embedding_text(metadata.payload)
        embedding = self.embed_text(text)
        await self._repository.upsert(
            movie_id=movie.id,
            embedding=embedding,
            embedded_text=text,
            model_name=self._model_name,
            model_revision=self._model_revision,
        )

    async def generate_all(self, *, limit: int | None = None) -> EmbeddingStats:
        stats = EmbeddingStats()
        stats.pending = await self._repository.count_movies_without_embeddings()
        batch = await self._repository.list_movies_without_embeddings(limit=limit)

        for movie, metadata in batch:
            try:
                await self.generate_for_movie(movie, metadata)
                stats.generated += 1
            except Exception:
                stats.failed += 1
                logger.exception(
                    "embedding_generation_failed",
                    extra={"movie_id": str(movie.id)},
                )

        return stats
