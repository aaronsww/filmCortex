import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from filmcortex.models.external_metadata import ExternalMetadata
from filmcortex.models.movie import Movie
from filmcortex.utils.payload import payload_fingerprint


@dataclass
class ExternalMetadataRecord:
    id: uuid.UUID
    movie_id: uuid.UUID
    provider: str
    provider_id: str
    payload: dict
    payload_fingerprint: str


class ExternalMetadataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_provider(
        self,
        provider: str,
        provider_id: str,
    ) -> ExternalMetadataRecord | None:
        result = await self._session.execute(
            select(ExternalMetadata).where(
                ExternalMetadata.provider == provider,
                ExternalMetadata.provider_id == provider_id,
                ExternalMetadata.is_active.is_(True),
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_record(row)

    async def create(
        self,
        movie_id: uuid.UUID,
        provider: str,
        provider_id: str,
        payload: dict,
        payload_version: str,
    ) -> ExternalMetadata:
        metadata = ExternalMetadata(
            movie_id=movie_id,
            provider=provider,
            provider_id=provider_id,
            payload=payload,
            payload_version=payload_version,
            is_active=True,
        )
        self._session.add(metadata)
        await self._session.flush()
        return metadata

    async def update_payload(
        self,
        metadata_id: uuid.UUID,
        payload: dict,
        payload_version: str,
        fetched_at: datetime,
    ) -> None:
        await self._session.execute(
            update(ExternalMetadata)
            .where(ExternalMetadata.id == metadata_id)
            .values(
                payload=payload,
                payload_version=payload_version,
                fetched_at=fetched_at,
                is_active=True,
            )
        )

    async def get_existing_provider_ids(
        self,
        provider: str,
        provider_ids: list[str],
        *,
        chunk_size: int = 1000,
    ) -> set[str]:
        if not provider_ids:
            return set()

        existing: set[str] = set()
        for start in range(0, len(provider_ids), chunk_size):
            chunk = provider_ids[start : start + chunk_size]
            result = await self._session.execute(
                select(ExternalMetadata.provider_id).where(
                    ExternalMetadata.provider == provider,
                    ExternalMetadata.provider_id.in_(chunk),
                    ExternalMetadata.is_active.is_(True),
                )
            )
            existing.update(result.scalars().all())
        return existing

    async def list_active_with_movies(self) -> list[tuple[Movie, ExternalMetadata]]:
        result = await self._session.execute(
            select(Movie, ExternalMetadata)
            .join(ExternalMetadata, ExternalMetadata.movie_id == Movie.id)
            .where(ExternalMetadata.is_active.is_(True))
            .order_by(Movie.canonical_title)
        )
        return list(result.all())

    @staticmethod
    def _to_record(row: ExternalMetadata) -> ExternalMetadataRecord:
        return ExternalMetadataRecord(
            id=row.id,
            movie_id=row.movie_id,
            provider=row.provider,
            provider_id=row.provider_id,
            payload=row.payload,
            payload_fingerprint=payload_fingerprint(row.payload),
        )
