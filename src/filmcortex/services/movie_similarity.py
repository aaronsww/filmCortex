import uuid

from filmcortex.repositories.movie_embedding_repository import MovieEmbeddingRepository
from filmcortex.schemas.movie import SimilarMovie


class MovieSimilarityService:
    def __init__(self, embedding_repository: MovieEmbeddingRepository) -> None:
        self._embedding_repository = embedding_repository

    async def find_similar(
        self,
        movie_id: uuid.UUID,
        limit: int = 10,
        include_scores: bool = False,
    ) -> list[SimilarMovie] | None:
        source = await self._embedding_repository.get_by_movie_id(movie_id)
        if source is None:
            return None

        rows = await self._embedding_repository.find_similar(movie_id, limit=limit)
        return [
            SimilarMovie(
                id=movie.id,
                canonical_title=movie.canonical_title,
                provider=metadata.provider,
                provider_id=metadata.provider_id,
                similarity_score=round(score, 6) if include_scores else None,
            )
            for movie, metadata, score in rows
        ]
