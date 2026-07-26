from filmcortex.repositories.external_metadata_repository import ExternalMetadataRepository
from filmcortex.repositories.movie_embedding_repository import MovieEmbeddingRepository
from filmcortex.repositories.movie_repository import MovieRepository
from filmcortex.schemas.movie import (
    DEFAULT_PAGE_SIZE,
    MovieListItem,
    MovieListPage,
    MovieStats,
)
from filmcortex.utils.cursor import decode_movie_list_cursor, encode_movie_list_cursor


class MovieQueryService:
    def __init__(
        self,
        metadata_repository: ExternalMetadataRepository,
        movie_repository: MovieRepository,
        embedding_repository: MovieEmbeddingRepository,
    ) -> None:
        self._metadata_repository = metadata_repository
        self._movie_repository = movie_repository
        self._embedding_repository = embedding_repository

    async def list_movies(
        self,
        *,
        cursor: str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> MovieListPage:
        after_title: str | None = None
        after_metadata_id = None
        if cursor is not None:
            after_title, after_metadata_id = decode_movie_list_cursor(cursor)

        rows = await self._metadata_repository.list_active_with_movies(
            limit=page_size + 1,
            after_title=after_title,
            after_metadata_id=after_metadata_id,
        )

        has_more = len(rows) > page_size
        page_rows = rows[:page_size]
        items = [
            MovieListItem(
                id=movie.id,
                canonical_title=movie.canonical_title,
                provider=metadata.provider,
                provider_id=metadata.provider_id,
            )
            for movie, metadata in page_rows
        ]

        next_cursor = None
        if has_more and page_rows:
            last_movie, last_metadata = page_rows[-1]
            next_cursor = encode_movie_list_cursor(
                title=last_movie.canonical_title,
                metadata_id=last_metadata.id,
            )

        return MovieListPage(items=items, next_cursor=next_cursor, page_size=page_size)

    async def get_stats(self) -> MovieStats:
        return MovieStats(
            movies=await self._movie_repository.count(),
            embeddings=await self._embedding_repository.count(),
            pending_embeddings=await self._embedding_repository.count_movies_without_embeddings(),
        )
