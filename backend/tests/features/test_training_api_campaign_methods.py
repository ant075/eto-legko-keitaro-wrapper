import httpx
import pytest

from app.integrations.training_api import TrainingApiClient


@pytest.mark.asyncio
async def test_training_api_client_lists_campaigns_and_campaign_streams():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/campaigns"):
            return httpx.Response(200, json=[{"id": 10}])
        if request.url.path.endswith("/campaigns/10/streams"):
            return httpx.Response(200, json=[])
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url="https://training-api.test/admin_api/v1",
        transport=transport,
    ) as http_client:
        async with TrainingApiClient(http_client) as api:
            campaigns = await api.list_campaigns(offset=100, limit=50)
            streams = await api.get_campaign_streams(10)

    assert campaigns == [{"id": 10}]
    assert streams == []
    assert requests[0].url.path.endswith("/campaigns")
    assert dict(requests[0].url.params) == {"offset": "100", "limit": "50"}
    assert requests[1].url.path.endswith("/campaigns/10/streams")
