import pytest

from tests.helpers import offer_map


@pytest.mark.asyncio
async def test_publish_sends_only_active_offers_and_replaces_snapshot(client, campaign, fake_api):
    await client.post("/api/campaigns/1/offers", json={"offer_id": 12, "name": "Beta offer"})
    await client.post("/api/campaigns/1/offers/11/delete")

    response = await client.post("/api/campaigns/1/offers/publish")
    assert response.status_code == 200
    assert response.json()["is_dirty"] is False
    put = next(call for call in fake_api.calls if call[0:2] == ("PUT", "/streams/202"))
    assert put[2]["offers"] == [{"offer_id": 12, "share": 100, "state": "active"}]


@pytest.mark.asyncio
async def test_failed_publish_keeps_dirty_state_and_snapshot(client, campaign, fake_api):
    await client.post("/api/campaigns/1/offers", json={"offer_id": 12, "name": "Beta offer"})
    fake_api.fail.add("update_stream")

    response = await client.post("/api/campaigns/1/offers/publish")
    assert response.status_code == 502
    listed = await client.get("/api/campaigns/1/offers")
    assert listed.json()["is_dirty"] is True
    assert {item["offer_id"] for item in listed.json()["offers"]} == {11, 12}


@pytest.mark.asyncio
async def test_cancel_restores_last_publication_but_preserves_pin(client, campaign):
    await client.post("/api/campaigns/1/offers/11/pin")
    await client.post("/api/campaigns/1/offers", json={"offer_id": 12, "name": "Beta offer"})

    response = await client.post("/api/campaigns/1/offers/cancel")
    assert response.status_code == 200
    assert response.json()["is_dirty"] is False
    offers = offer_map(response)
    assert set(offers) == {11}
    assert offers[11]["weight"] == 100
    assert offers[11]["is_deleted"] is False
    assert offers[11]["is_pinned"] is True


@pytest.mark.asyncio
async def test_sync_reconciles_external_state_and_creates_snapshot(client, campaign, fake_api):
    fake_api.streams[202] = {
        "id": 202,
        "offers": [
            {"offer_id": 12, "share": 70, "state": "active", "name": "Beta offer"},
            {"offer_id": 13, "share": 30, "state": "active"},
        ],
    }
    response = await client.post("/api/campaigns/1/offers/sync")

    assert response.status_code == 200
    offers = offer_map(response)
    assert offers[11]["is_deleted"] is True
    assert offers[12]["name"] == "Beta offer"
    assert offers[13]["name"] == "Gamma offer"
    assert offers[13]["position"] == 2
    assert response.json()["is_dirty"] is False


@pytest.mark.asyncio
async def test_sync_is_rejected_when_local_changes_are_dirty(client, campaign):
    await client.post("/api/campaigns/1/offers", json={"offer_id": 12, "name": "Beta offer"})
    response = await client.post("/api/campaigns/1/offers/sync")
    assert response.status_code == 400
