import pytest

from tests.helpers import offer_map


@pytest.mark.asyncio
async def test_offer_editing_recalculates_weights_and_marks_campaign_dirty(client, campaign):
    added = await client.post("/api/campaigns/1/offers", json={"offer_id": 12, "name": "Beta offer"})
    assert added.status_code == 200
    assert added.json()["is_dirty"] is True
    offers = offer_map(added)
    assert offers[11]["weight"] == 50
    assert offers[12]["weight"] == 50

    pinned = await client.post("/api/campaigns/1/offers/11/pin")
    assert pinned.status_code == 200
    assert pinned.json()["is_dirty"] is True
    assert offer_map(pinned)[11]["is_pinned"] is True
    assert offer_map(pinned)[11]["weight"] == 50

    deleted = await client.post("/api/campaigns/1/offers/11/delete")
    assert deleted.status_code == 200
    assert offer_map(deleted)[11]["is_deleted"] is True
    assert offer_map(deleted)[11]["weight"] == 0
    assert offer_map(deleted)[11]["is_pinned"] is False
    assert offer_map(deleted)[12]["weight"] == 100

    restored = await client.post("/api/campaigns/1/offers/11/restore")
    assert restored.status_code == 200
    assert offer_map(restored)[11]["is_deleted"] is False
    assert sum(item["weight"] for item in restored.json()["offers"] if not item["is_deleted"]) == 100


@pytest.mark.asyncio
async def test_pin_does_not_change_dirty_state_or_weights_and_deleted_offer_cannot_pin(client, campaign):
    pinned = await client.post("/api/campaigns/1/offers/11/pin")
    assert pinned.json()["is_dirty"] is False
    assert offer_map(pinned)[11]["weight"] == 100

    await client.post("/api/campaigns/1/offers/11/delete")
    rejected = await client.post("/api/campaigns/1/offers/11/pin")
    assert rejected.status_code == 400


@pytest.mark.asyncio
async def test_search_excludes_offers_already_used_in_campaign(client, campaign, fake_api):
    response = await client.get("/api/campaigns/1/offers/search", params={"q": "offer"})
    assert response.status_code == 200
    assert response.json() == [
        {"offer_id": 12, "name": "Beta offer"},
        {"offer_id": 13, "name": "Gamma offer"},
    ]
