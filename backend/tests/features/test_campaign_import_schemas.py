import pytest
from pydantic import ValidationError

from app.schemas.campaign_import import (
    ExternalImportCampaign,
    ExternalImportStream,
)


def test_import_schemas_validate_required_campaign_and_stream_data():
    campaign = ExternalImportCampaign.model_validate({
        "id": 258,
        "name": "Imported campaign",
        "alias": "imported",
        "group_id": 10332,
        "traffic_source_id": 836,
        "domain_id": 1813,
        "created_at": "2026-11-25 07:27:44",
        "updated_at": "2026-11-25 07:27:44",
    })
    stream = ExternalImportStream.model_validate({
        "id": 508,
        "campaign_id": 258,
        "position": 1,
        "type": "forced",
        "state": "active",
        "schema": "redirect",
        "action_type": "http",
        "action_payload": "https://google.com/",
        "collect_clicks": True,
        "filter_or": False,
        "offer_selection": "before_click",
        "filters": [{
            "id": 279,
            "name": "country",
            "mode": "accept",
            "payload": ["RU"],
        }],
        "offers": [],
        "created_at": "2026-11-25 08:16:45",
    })

    assert campaign.id == 258
    assert campaign.domain_id == 1813
    assert stream.schema_name == "redirect"
    assert stream.filters[0].payload == ["RU"]
    assert stream.offers == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", 0),
        ("name", ""),
        ("group_id", 0),
        ("traffic_source_id", 0),
        ("domain_id", 0),
    ],
)
def test_import_campaign_schema_rejects_invalid_required_values(field, value):
    payload = {
        "id": 258,
        "name": "Imported campaign",
        "group_id": 10332,
        "traffic_source_id": 836,
        "domain_id": 1813,
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        ExternalImportCampaign.model_validate(payload)


def test_import_stream_schema_rejects_invalid_nested_offer_values():
    with pytest.raises(ValidationError):
        ExternalImportStream.model_validate({
            "id": 508,
            "campaign_id": 258,
            "position": 1,
            "type": "regular",
            "state": "active",
            "schema": "landings",
            "action_type": "http",
            "action_payload": None,
            "collect_clicks": True,
            "filter_or": False,
            "offer_selection": "before_click",
            "filters": [],
            "offers": [{"offer_id": 11, "share": 101, "state": "active"}],
        })
