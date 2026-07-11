from unittest.mock import AsyncMock, MagicMock

import pytest

from filmcortex.integrations.tmdb.client import TMDbClient
from filmcortex.integrations.tmdb.constants import TMDB_APPEND_TO_RESPONSE


@pytest.mark.asyncio
async def test_get_movie_requests_credits_and_keywords() -> None:
    client = TMDbClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 550}
    mock_response.raise_for_status.return_value = None
    client._client.request = AsyncMock(return_value=mock_response)

    data = await client.get_movie(550)

    assert data["id"] == 550
    client._client.request.assert_awaited_once_with(
        "GET",
        "/movie/550",
        params={"api_key": "test-key", "append_to_response": TMDB_APPEND_TO_RESPONSE},
    )
    await client.close()


@pytest.mark.asyncio
async def test_get_popular() -> None:
    client = TMDbClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [{"id": 1}]}
    mock_response.raise_for_status.return_value = None
    client._client.request = AsyncMock(return_value=mock_response)

    data = await client.get_popular(page=1)

    assert data["results"][0]["id"] == 1
    client._client.request.assert_awaited_once_with(
        "GET",
        "/movie/popular",
        params={"api_key": "test-key", "page": 1},
    )
    await client.close()


@pytest.mark.asyncio
async def test_get_top_rated() -> None:
    client = TMDbClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [{"id": 2}]}
    mock_response.raise_for_status.return_value = None
    client._client.request = AsyncMock(return_value=mock_response)

    data = await client.get_top_rated(page=2)

    assert data["results"][0]["id"] == 2
    client._client.request.assert_awaited_once_with(
        "GET",
        "/movie/top_rated",
        params={"api_key": "test-key", "page": 2},
    )
    await client.close()


@pytest.mark.asyncio
async def test_get_discover_passes_filters() -> None:
    client = TMDbClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status.return_value = None
    client._client.request = AsyncMock(return_value=mock_response)

    await client.get_discover(page=1, primary_release_year=1994, **{"vote_count.gte": 500})

    client._client.request.assert_awaited_once_with(
        "GET",
        "/discover/movie",
        params={
            "api_key": "test-key",
            "page": 1,
            "primary_release_year": 1994,
            "vote_count.gte": 500,
        },
    )
    await client.close()


@pytest.mark.asyncio
async def test_get_trending() -> None:
    client = TMDbClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [{"id": 3}]}
    mock_response.raise_for_status.return_value = None
    client._client.request = AsyncMock(return_value=mock_response)

    await client.get_trending(time_window="week", page=1)

    client._client.request.assert_awaited_once_with(
        "GET",
        "/trending/movie/week",
        params={"api_key": "test-key", "page": 1},
    )
    await client.close()
