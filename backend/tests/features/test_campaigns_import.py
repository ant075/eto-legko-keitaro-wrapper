import pytest

from app.models import Campaign, CampaignOffer, CampaignOfferPublication


def _external_campaign(campaign_id=10):
    return {
        "id": campaign_id,
        "name": "Imported campaign",
        "alias": "imported-campaign",
        "group_id": 2,
        "traffic_source_id": 3,
        "domain_id": 4,
    }


def _redirect_stream(campaign_id=10, stream_id=301, stream_type="forced"):
    return {
        "id": stream_id,
        "campaign_id": campaign_id,
        "position": 2,
        "type": stream_type,
        "state": "active",
        "schema": "redirect",
        "action_type": "http",
        "action_payload": "https://google.com/",
        "collect_clicks": True,
        "filter_or": False,
        "offer_selection": "before_click",
        "filters": [{"name": "country", "mode": "accept", "payload": ["GM"]}],
        "offers": [],
    }


def _offers_stream(campaign_id=10, stream_id=302, stream_type="regular"):
    return {
        "id": stream_id,
        "campaign_id": campaign_id,
        "position": 1,
        "type": stream_type,
        "state": "active",
        "schema": "landings",
        "action_type": "http",
        "action_payload": None,
        "collect_clicks": True,
        "filter_or": False,
        "offer_selection": "before_click",
        "filters": [],
        "offers": [{"offer_id": 11, "share": 100, "state": "active", "name": "Alpha offer"}],
    }


@pytest.mark.asyncio
async def test_import_campaigns_saves_campaign_and_syncs_offers(client, db_session, fake_api):
    fake_api.campaigns = [_external_campaign()]
    fake_api.streams[301] = _redirect_stream()
    fake_api.streams[302] = _offers_stream()

    response = await client.post("/api/campaigns/import")

    assert response.status_code == 200
    assert response.json() == {"imported_count": 1, "message": None}
    campaign = db_session.get(Campaign, 10)
    assert campaign is not None
    assert campaign.redirect_stream_id == 301
    assert campaign.offers_stream_id == 302
    assert campaign.country_code == "GM"
    assert campaign.is_dirty is False
    assert [offer.offer_id for offer in campaign.offers] == [11]
    assert len(campaign.publications) == 1
    assert ("GET", "/campaigns", {"offset": 0, "limit": 100}) in fake_api.calls
    assert ("GET", "/campaigns/10/streams", None) in fake_api.calls
    assert ("GET", "/streams/302", None) in fake_api.calls


@pytest.mark.asyncio
async def test_import_campaigns_uses_position_one_when_no_forced_stream(client, db_session, fake_api):
    fake_api.campaigns = [_external_campaign()]
    fake_api.streams[301] = _redirect_stream(stream_type="regular")
    fake_api.streams[301]["position"] = 1
    fake_api.streams[302] = _offers_stream()

    response = await client.post("/api/campaigns/import")

    assert response.status_code == 200
    campaign = db_session.get(Campaign, 10)
    assert campaign.redirect_stream_id == 301
    assert campaign.offers_stream_id == 302


@pytest.mark.asyncio
async def test_import_campaigns_reports_no_suitable_campaigns(client, db_session, fake_api):
    fake_api.campaigns = [_external_campaign()]
    fake_api.streams[301] = _redirect_stream()
    fake_api.streams[302] = _offers_stream()
    fake_api.streams[302]["offers"][0]["state"] = "paused"

    response = await client.post("/api/campaigns/import")

    assert response.status_code == 200
    assert response.json() == {"imported_count": 0, "message": "Нет подходящих кампаний"}
    assert db_session.query(Campaign).count() == 0


@pytest.mark.asyncio
async def test_import_campaigns_is_rejected_when_local_campaign_exists(client, campaign, fake_api):
    response = await client.post("/api/campaigns/import")

    assert response.status_code == 409
    assert "только при отсутствии локальных кампаний" in response.json()["detail"]
    assert not any(call[1] == "/campaigns" for call in fake_api.calls)


@pytest.mark.asyncio
async def test_import_campaigns_cleans_up_when_offer_sync_fails(client, db_session, fake_api):
    fake_api.campaigns = [_external_campaign()]
    fake_api.streams[301] = _redirect_stream()
    fake_api.streams[302] = _offers_stream()
    fake_api.fail.add("get_stream")

    response = await client.post("/api/campaigns/import")

    assert response.status_code == 502
    assert db_session.query(Campaign).count() == 0
    assert db_session.query(CampaignOffer).count() == 0
    assert db_session.query(CampaignOfferPublication).count() == 0
