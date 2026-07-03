from unittest.mock import AsyncMock, MagicMock

import pytest

from filmcortex.integrations.tmdb.client import TMDbClient


@pytest.mark.asyncio
async def test_get_movie_requests_credits_and_keywords() -> None:
    client = TMDbClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 550}
    mock_response.raise_for_status.return_value = None
    client._client.get = AsyncMock(return_value=mock_response)

    data = await client.get_movie(550)

    assert data["id"] == 550
    client._client.get.assert_awaited_once_with(
        "/movie/550",
        params={"api_key": "test-key", "append_to_response": "credits,keywords"},
    )
    await client.close()


@pytest.mark.asyncio
async def test_get_popular() -> None:
    client = TMDbClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": [{"id": 1}]}
    mock_response.raise_for_status.return_value = None
    client._client.get = AsyncMock(return_value=mock_response)

    data = await client.get_popular(page=1)

    assert data["results"][0]["id"] == 1
    client._client.get.assert_awaited_once_with(
        "/movie/popular",
        params={"api_key": "test-key", "page": 1},
    )
    await client.close()
