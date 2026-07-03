from filmcortex.repositories.external_metadata_repository import ExternalMetadataRepository
from filmcortex.schemas.movie import MovieListItem


class MovieQueryService:
    def __init__(self, metadata_repository: ExternalMetadataRepository) -> None:
        self._metadata_repository = metadata_repository

    async def list_movies(self) -> list[MovieListItem]:
        rows = await self._metadata_repository.list_active_with_movies()
        return [
            MovieListItem(
                id=movie.id,
                canonical_title=movie.canonical_title,
                provider=metadata.provider,
                provider_id=metadata.provider_id,
            )
            for movie, metadata in rows
        ]
