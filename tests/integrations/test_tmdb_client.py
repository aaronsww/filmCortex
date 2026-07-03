from unittest.mock import AsyncMock, MagicMock

import pytest

from filmcortex.integrations.tmdb.client import TMDbClient


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
