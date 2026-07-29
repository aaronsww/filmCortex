import uuid
from unittest.mock import AsyncMock

import pytest

from filmcortex.models.movie import MediaType, Movie
from filmcortex.repositories.external_metadata_repository import ExternalMetadataRecord
from filmcortex.services.tmdb_ingestion import TMDbIngestionService


@pytest.fixture
def tmdb_payload() -> dict:
    return {
        "id": 550,
        "title": "Fight Club",
        "original_title": "Fight Club",
    }


@pytest.fixture
def ingestion_service(tmdb_payload: dict) -> TMDbIngestionService:
    tmdb_client = AsyncMock()
    tmdb_client.get_movie.return_value = tmdb_payload
    tmdb_client.get_top_rated.side_effect = [
        {"results": [{"id": 550}], "total_pages": 1},
    ]
    tmdb_client.get_discover.side_effect = [
        {"results": [{"id": 551}], "total_pages": 1},
    ]
    tmdb_client.get_trending.side_effect = [
        {"results": [{"id": 552}], "total_pages": 1},
    ]
    tmdb_client.get_list.return_value = {"items": [{"id": 553}]}

    movie_repository = AsyncMock()
    created_movie = Movie(
        id=uuid.uuid4(),
        canonical_title="Fight Club",
        media_type=MediaType.FILM,
    )
    movie_repository.create.return_value = created_movie

    metadata_repository = AsyncMock()
    metadata_repository.get_by_provider.return_value = None
    metadata_repository.get_existing_provider_ids.return_value = set()

    return TMDbIngestionService(
        tmdb_client=tmdb_client,
        movie_repository=movie_repository,
        metadata_repository=metadata_repository,
    )


@pytest.mark.asyncio
async def test_ingest_movie_inserts_new_record(
    ingestion_service: TMDbIngestionService,
) -> None:
    result = await ingestion_service.ingest_movie(550)
    assert result == "inserted"
    ingestion_service._movie_repository.create.assert_awaited_once()
    ingestion_service._metadata_repository.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingest_movie_skips_unchanged_payload(
    ingestion_service: TMDbIngestionService,
    tmdb_payload: dict,
) -> None:
    from filmcortex.utils.payload import payload_fingerprint

    ingestion_service._metadata_repository.get_by_provider.return_value = ExternalMetadataRecord(
        id=uuid.uuid4(),
        movie_id=uuid.uuid4(),
        provider="tmdb",
        provider_id="550",
        payload=tmdb_payload,
        payload_fingerprint=payload_fingerprint(tmdb_payload),
    )

    result = await ingestion_service.ingest_movie(550)
    assert result == "skipped"
    ingestion_service._metadata_repository.update_payload.assert_not_called()


@pytest.mark.asyncio
async def test_ingest_movie_updates_changed_payload(
    ingestion_service: TMDbIngestionService,
) -> None:
    ingestion_service._metadata_repository.get_by_provider.return_value = ExternalMetadataRecord(
        id=uuid.uuid4(),
        movie_id=uuid.uuid4(),
        provider="tmdb",
        provider_id="550",
        payload={"id": 550, "title": "Old Title"},
        payload_fingerprint="different",
    )

    result = await ingestion_service.ingest_movie(550)
    assert result == "updated"
    ingestion_service._movie_repository.update_title.assert_awaited_once()
    ingestion_service._metadata_repository.update_payload.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingest_top_rated(ingestion_service: TMDbIngestionService) -> None:
    stats = await ingestion_service.ingest_top_rated()
    assert stats.fetched == 1
    assert stats.inserted == 1
    assert stats.next_page == 1


@pytest.mark.asyncio
async def test_ingest_discover(ingestion_service: TMDbIngestionService) -> None:
    stats = await ingestion_service.ingest_discover(filters={"primary_release_year": 1994})
    assert stats.fetched == 1
    assert stats.inserted == 1


@pytest.mark.asyncio
async def test_ingest_trending(ingestion_service: TMDbIngestionService) -> None:
    stats = await ingestion_service.ingest_trending(time_window="day")
    assert stats.fetched == 1
    assert stats.inserted == 1


@pytest.mark.asyncio
async def test_ingest_from_paged_endpoint_respects_max_movies(
    ingestion_service: TMDbIngestionService,
) -> None:
    ingestion_service._tmdb_client.get_top_rated.side_effect = [
        {"results": [{"id": 1}, {"id": 2}, {"id": 3}], "total_pages": 2},
        {"results": [{"id": 4}], "total_pages": 2},
    ]

    stats = await ingestion_service.ingest_top_rated(max_movies=2)

    assert stats.fetched == 2
    assert stats.next_page == 1
    assert ingestion_service._tmdb_client.get_top_rated.await_count == 1


@pytest.mark.asyncio
async def test_ingest_top_rated_skips_existing_without_detail_fetch(
    ingestion_service: TMDbIngestionService,
) -> None:
    ingestion_service._tmdb_client.get_top_rated.side_effect = [
        {"results": [{"id": 550}, {"id": 551}], "total_pages": 1},
    ]
    ingestion_service._metadata_repository.get_existing_provider_ids.return_value = {"550"}
    ingestion_service._tmdb_client.get_movie.side_effect = [
        {"id": 551, "title": "New Film"},
    ]

    stats = await ingestion_service.ingest_top_rated(skip_existing=True)

    assert stats.skipped == 1
    assert stats.fetched == 1
    assert stats.inserted == 1
    ingestion_service._tmdb_client.get_movie.assert_awaited_once_with(551)
    ingestion_service._metadata_repository.get_existing_provider_ids.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingest_top_rated_resume_cursor_and_wrap(
    ingestion_service: TMDbIngestionService,
) -> None:
    ingestion_service._tmdb_client.get_top_rated.side_effect = [
        {"results": [{"id": 10}], "total_pages": 2},
        {"results": [{"id": 11}], "total_pages": 2},
    ]
    ingestion_service._tmdb_client.get_movie.side_effect = [
        {"id": 10, "title": "A"},
        {"id": 11, "title": "B"},
    ]

    stats = await ingestion_service.ingest_top_rated(
        start_page=2,
        skip_existing=True,
        wrap=True,
    )

    assert stats.fetched == 1
    assert stats.inserted == 1
    assert stats.pages_scanned == 1
    assert stats.next_page == 1
    ingestion_service._tmdb_client.get_top_rated.assert_awaited_once_with(page=2)


@pytest.mark.asyncio
async def test_ingest_top_rated_stops_mid_page_and_resumes_same_page(
    ingestion_service: TMDbIngestionService,
) -> None:
    ingestion_service._tmdb_client.get_top_rated.side_effect = [
        {"results": [{"id": 1}, {"id": 2}, {"id": 3}], "total_pages": 5},
    ]
    ingestion_service._metadata_repository.get_existing_provider_ids.return_value = set()
    ingestion_service._tmdb_client.get_movie.side_effect = [
        {"id": 1, "title": "One"},
        {"id": 2, "title": "Two"},
    ]

    stats = await ingestion_service.ingest_top_rated(
        start_page=3,
        max_movies=2,
        skip_existing=True,
        wrap=True,
    )

    assert stats.fetched == 2
    assert stats.inserted == 2
    assert stats.next_page == 3


@pytest.mark.asyncio
async def test_ingest_list(ingestion_service: TMDbIngestionService) -> None:
    stats = await ingestion_service.ingest_list(634)
    assert stats.fetched == 1
    assert stats.inserted == 1
