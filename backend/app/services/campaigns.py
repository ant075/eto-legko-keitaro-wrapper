from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.training_api import TrainingApiClient, TrainingApiError
from app.models import Campaign, CampaignOffer, CampaignOfferPublication
from app.schemas.campaign import CampaignCreate


class CampaignCreationError(RuntimeError):
    pass


def _campaign_payload(data: CampaignCreate) -> dict[str, object]:
    return {
        "name": data.name,
        "type": "position",
        "state": "active",
        "cost_type": "CPC",
        "cost_value": 0,
        "cost_currency": "USD",
        "cost_auto": True,
        "group_id": data.group_id,
        "traffic_source_id": data.traffic_source_id,
        "domain_id": data.domain_id,
    }


async def create_campaign(db: Session, data: CampaignCreate) -> Campaign:
    settings = get_settings()
    campaign_id: int | None = None

    redirect_payload = {
        "name": "Redirect by country",
        "type": "forced",
        "state": "active",
        "schema": "redirect",
        "action_type": "http",
        "action_payload": settings.redirect_target_url,
        "collect_clicks": True,
        "filter_or": False,
        "offer_selection": "before_click",
        "filters": [{"name": "country", "mode": "accept", "payload": [data.country_code.upper()]}],
        "offers": [],
    }
    offers_payload = {
        "name": "With offers",
        "type": "regular",
        "state": "active",
        "schema": "landings",
        "action_type": "http",
        "action_payload": None,
        "collect_clicks": True,
        "filter_or": False,
        "offer_selection": "before_click",
        "filters": [],
        "offers": [{"offer_id": data.offer_id, "share": 100, "state": "active"}],
    }

    try:
        async with TrainingApiClient() as api:
            campaign = await api.create_campaign(_campaign_payload(data))
            campaign_id = int(campaign["id"])
            redirect_payload["campaign_id"] = campaign_id
            redirect_stream = await api.create_stream(redirect_payload)
            offers_payload["campaign_id"] = campaign_id
            offers_stream = await api.create_stream(offers_payload)
            external_offer = await api.get_offer(data.offer_id)
    except (TrainingApiError, KeyError, TypeError, ValueError) as exc:
        if campaign_id is not None:
            try:
                async with TrainingApiClient() as api:
                    await api.delete_campaign(campaign_id)
            except TrainingApiError as compensation_error:
                raise CampaignCreationError(
                    f"Создание кампании не завершено, а компенсационное удаление тоже завершилось ошибкой: {compensation_error}"
                ) from exc
        raise CampaignCreationError("Не удалось создать кампанию в API учебного стенда") from exc

    try:
        local_campaign = Campaign(
            id=campaign_id,
            name=campaign["name"],
            alias=campaign.get("alias"),
            group_id=data.group_id,
            traffic_source_id=data.traffic_source_id,
            domain_id=data.domain_id,
            redirect_stream_id=int(redirect_stream["id"]),
            offers_stream_id=int(offers_stream["id"]),
            country_code=data.country_code.upper(),
            is_dirty=False,
        )
        local_offer = CampaignOffer(
            campaign_id=campaign_id,
            offer_id=data.offer_id,
            name=str(external_offer.get("name", data.offer_id)),
            weight=100,
            is_pinned=False,
            is_deleted=False,
            position=1,
        )
        local_campaign.offers.append(local_offer)
        local_campaign.publications.append(
            CampaignOfferPublication(
                campaign_id=campaign_id,
                offer_id=data.offer_id,
                name=str(external_offer.get("name", data.offer_id)),
                weight=100,
                is_deleted=False,
                position=1,
            )
        )
        db.add(local_campaign)
        db.commit()
        db.refresh(local_campaign)
        return local_campaign
    except Exception as exc:
        db.rollback()
        try:
            async with TrainingApiClient() as api:
                await api.delete_campaign(campaign_id)
        except TrainingApiError as compensation_error:
            raise CampaignCreationError(
                f"Локальное сохранение не удалось, компенсационное удаление тоже завершилось ошибкой: {compensation_error}"
            ) from exc
        raise CampaignCreationError("Кампания создана во внешнем API, но не сохранена локально") from exc


def list_campaigns(db: Session) -> list[Campaign]:
    return list(db.scalars(select(Campaign).order_by(Campaign.updated_at.desc())))


def get_campaign(db: Session, campaign_id: int) -> Campaign | None:
    return db.get(Campaign, campaign_id)


async def delete_campaign(db: Session, campaign: Campaign) -> None:
    async with TrainingApiClient() as api:
        await api.delete_campaign(campaign.id)
    db.delete(campaign)
    db.commit()

