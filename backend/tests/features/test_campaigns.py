import pytest

from app.models import Campaign


@pytest.mark.asyncio
async def test_create_campaign_creates_external_resources_and_initial_snapshot(client, db_session, fake_api):
    response = await client.post("/api/campaigns", json={
        "name": "New campaign", "domain_id": 4, "group_id": 2,
        "traffic_source_id": 3, "country_code": "gm", "offer_id": 11,
    })

    assert response.status_code == 201
    body = response.json()
    assert body["country_code"] == "GM"
    assert body["is_dirty"] is False
    assert len(fake_api.campaigns) == 1
    assert [call[0:2] for call in fake_api.calls] == [
        ("POST", "/campaigns"), ("POST", "/streams"),
        ("POST", "/streams"), ("GET", "/offers/11"),
    ]

    campaign = db_session.get(Campaign, 100)
    assert campaign is not None
    assert len(campaign.offers) == 1
    assert len(campaign.publications) == 1


@pytest.mark.asyncio
async def test_create_campaign_compensates_external_campaign_on_stream_failure(client, fake_api):
    fake_api.fail.add("create_stream")

    response = await client.post("/api/campaigns", json={
        "name": "Broken campaign", "domain_id": 4, "group_id": 2,
        "traffic_source_id": 3, "country_code": "GM", "offer_id": 11,
    })

    assert response.status_code == 502
    assert fake_api.campaigns == []
    assert ("DELETE", "/campaigns/100", None) in fake_api.calls


@pytest.mark.asyncio
async def test_delete_campaign_removes_local_data_after_external_success(client, campaign, fake_api, db_engine):
    response = await client.delete("/api/campaigns/1")

    assert response.status_code == 204
    assert ("DELETE", "/campaigns/1", None) in fake_api.calls
    from app.models import Campaign
    from sqlalchemy.orm import Session

    with Session(db_engine) as verification_session:
        assert verification_session.get(Campaign, 1) is None
