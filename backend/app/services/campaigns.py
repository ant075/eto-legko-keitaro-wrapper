import asyncio
import logging
from dataclasses import dataclass
from collections.abc import Mapping

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.training_api import TrainingApiClient, TrainingApiError
from app.models import Campaign, CampaignOffer, CampaignOfferPublication, Country
from app.schemas.campaign import (
    CampaignCreate,
    ExternalCampaignResponse,
    ExternalOfferDetails,
    ExternalStreamCreatedResponse,
)
from app.schemas.campaign_import import ExternalImportCampaign, ExternalImportStream
from app.services import offers


logger = logging.getLogger(__name__)
IMPORT_PAGE_SIZE = 100
NO_SUITABLE_CAMPAIGNS_MESSAGE = "Нет подходящих кампаний"
_import_lock = asyncio.Lock()


class CampaignCreationError(RuntimeError):
    pass


class CampaignImportError(RuntimeError):
    pass


class CampaignImportAlreadyInitialized(CampaignImportError):
    pass


class CampaignImportApiError(CampaignImportError):
    pass


@dataclass(frozen=True)
class CampaignImportResult:
    imported_count: int
    message: str | None = None


@dataclass(frozen=True)
class _ImportCandidate:
    campaign: ExternalImportCampaign
    redirect_stream_id: int
    offers_stream_id: int
    country_code: str


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

    # "type": "forced" выбран сознательно, чтоб фильтр по стране срабатывал гарантировано
    # вне зависимости от очерёдности двух потоков
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
            campaign = ExternalCampaignResponse.model_validate(
                await api.create_campaign(_campaign_payload(data))
            )
            campaign_id = campaign.id
            redirect_payload["campaign_id"] = campaign_id
            redirect_stream = ExternalStreamCreatedResponse.model_validate(
                await api.create_stream(redirect_payload)
            )
            offers_payload["campaign_id"] = campaign_id
            offers_stream = ExternalStreamCreatedResponse.model_validate(
                await api.create_stream(offers_payload)
            )
            external_offer = ExternalOfferDetails.model_validate(await api.get_offer(data.offer_id))
    except (TrainingApiError, ValidationError, TypeError, ValueError) as exc:
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
            name=campaign.name,
            alias=campaign.alias,
            group_id=data.group_id,
            traffic_source_id=data.traffic_source_id,
            domain_id=data.domain_id,
            redirect_stream_id=redirect_stream.id,
            offers_stream_id=offers_stream.id,
            country_code=data.country_code.upper(),
            is_dirty=False,
        )
        local_offer = CampaignOffer(
            campaign_id=campaign_id,
            offer_id=data.offer_id,
            name=external_offer.name,
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
                name=external_offer.name,
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


def _has_local_campaigns(db: Session) -> bool:
    return db.scalar(select(Campaign.id).limit(1)) is not None


def _collection_items(value: object, collection_name: str) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in (collection_name, "data", "items"):
            items = value.get(key)
            if isinstance(items, list):
                return items
    raise ValueError(f"API учебного стенда вернул некорректный список {collection_name}")


async def _list_external_campaigns(api: TrainingApiClient) -> list[ExternalImportCampaign]:
    result: list[ExternalImportCampaign] = []
    offset = 0

    while True:
        page = _collection_items(
            await api.list_campaigns(offset=offset, limit=IMPORT_PAGE_SIZE),
            "campaigns",
        )
        if not page:
            break

        for item in page:
            try:
                result.append(ExternalImportCampaign.model_validate(item))
            except (ValidationError, TypeError, ValueError) as exc:
                logger.warning("Пропущена кампания с некорректными данными API: %r", exc)

        if len(page) < IMPORT_PAGE_SIZE:
            break
        offset += len(page)

    return result


def _select_streams(streams: list[ExternalImportStream]) -> tuple[ExternalImportStream, ExternalImportStream] | None:
    if len(streams) != 2:
        return None

    redirect_index = next(
        (index for index, stream in enumerate(streams) if stream.type == "forced"),
        None,
    )
    if redirect_index is None:
        redirect_index = next(
            (index for index, stream in enumerate(streams) if stream.position == 1),
            None,
        )
    if redirect_index is None:
        return None

    return streams[redirect_index], streams[1 - redirect_index]


def _candidate_from_streams(
    db: Session,
    campaign: ExternalImportCampaign,
    streams: list[ExternalImportStream],
) -> _ImportCandidate | None:
    selected = _select_streams(streams)
    if selected is None:
        return None
    redirect_stream, offers_stream = selected
    redirect_target_url = get_settings().redirect_target_url

    if any(stream.campaign_id != campaign.id for stream in streams):
        return None

    if not (
        redirect_stream.state == "active"
        and redirect_stream.schema_name == "redirect"
        and redirect_stream.action_type == "http"
        and redirect_stream.action_payload == redirect_target_url
        and redirect_stream.collect_clicks is True
        and redirect_stream.filter_or is False
        and redirect_stream.offer_selection == "before_click"
        and not redirect_stream.offers
    ):
        return None

    if len(redirect_stream.filters) != 1:
        return None
    country_filter = redirect_stream.filters[0]
    if country_filter.name != "country" or country_filter.mode != "accept":
        return None
    if len(country_filter.payload) != 1:
        return None
    country_code = country_filter.payload[0].upper()
    if len(country_code) != 2 or not country_code.isalpha():
        return None
    if db.get(Country, country_code) is None:
        return None

    if not (
        offers_stream.type == "regular"
        and offers_stream.state == "active"
        and offers_stream.schema_name == "landings"
        and offers_stream.action_type == "http"
        and offers_stream.action_payload is None
        and offers_stream.collect_clicks is True
        and offers_stream.filter_or is False
        and offers_stream.offer_selection == "before_click"
        and not offers_stream.filters
        and offers_stream.offers
        and any(offer.state == "active" for offer in offers_stream.offers)
    ):
        return None

    return _ImportCandidate(
        campaign=campaign,
        redirect_stream_id=redirect_stream.id,
        offers_stream_id=offers_stream.id,
        country_code=country_code,
    )


async def _find_import_candidates(db: Session, api: TrainingApiClient) -> list[_ImportCandidate]:
    candidates: list[_ImportCandidate] = []
    for campaign in await _list_external_campaigns(api):
        try:
            raw_streams = await api.get_campaign_streams(campaign.id)
            streams = [
                ExternalImportStream.model_validate(item)
                for item in _collection_items(raw_streams, "streams")
            ]
        except (ValidationError, TypeError, ValueError) as exc:
            logger.warning(
                "Пропущена кампания %s: API вернул некорректные потоки: %r",
                campaign.id,
                exc,
            )
            continue

        candidate = _candidate_from_streams(db, campaign, streams)
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def _cleanup_imported_campaigns(db: Session, campaign_ids: list[int]) -> None:
    db.rollback()
    for campaign_id in campaign_ids:
        campaign = db.get(Campaign, campaign_id)
        if campaign is not None:
            db.delete(campaign)
    db.commit()


async def import_campaigns(db: Session) -> CampaignImportResult:
    if _has_local_campaigns(db):
        raise CampaignImportAlreadyInitialized("Импорт доступен только при отсутствии локальных кампаний")

    async with _import_lock:
        if _has_local_campaigns(db):
            raise CampaignImportAlreadyInitialized("Импорт доступен только при отсутствии локальных кампаний")

        try:
            async with TrainingApiClient() as api:
                candidates = await _find_import_candidates(db, api)
        except TrainingApiError as exc:
            raise CampaignImportApiError(
                "Не удалось получить кампании из API учебного стенда"
            ) from exc
        except (TypeError, ValueError) as exc:
            raise CampaignImportApiError(
                "API учебного стенда вернул некорректный список кампаний"
            ) from exc

        if not candidates:
            return CampaignImportResult(0, NO_SUITABLE_CAMPAIGNS_MESSAGE)
        if _has_local_campaigns(db):
            raise CampaignImportAlreadyInitialized("Импорт доступен только при отсутствии локальных кампаний")

        created_ids: list[int] = []
        try:
            for candidate in candidates:
                local_campaign = Campaign(
                    id=candidate.campaign.id,
                    name=candidate.campaign.name,
                    alias=candidate.campaign.alias,
                    group_id=candidate.campaign.group_id,
                    traffic_source_id=candidate.campaign.traffic_source_id,
                    domain_id=candidate.campaign.domain_id,
                    redirect_stream_id=candidate.redirect_stream_id,
                    offers_stream_id=candidate.offers_stream_id,
                    country_code=candidate.country_code,
                    is_dirty=False,
                )
                db.add(local_campaign)
                db.commit()
                created_ids.append(local_campaign.id)
                await offers.sync_from_training_api(db, local_campaign.id)
        except offers.OfferOperationError as exc:
            _cleanup_imported_campaigns(db, created_ids)
            raise CampaignImportApiError(
                "Не удалось импортировать офферы кампании из API учебного стенда"
            ) from exc
        except Exception as exc:
            _cleanup_imported_campaigns(db, created_ids)
            raise CampaignImportError("Не удалось сохранить импортированные кампании") from exc

        return CampaignImportResult(len(created_ids))


def list_campaigns(db: Session) -> list[Campaign]:
    return list(db.scalars(select(Campaign).order_by(Campaign.updated_at.desc())))


def get_campaign(db: Session, campaign_id: int) -> Campaign | None:
    return db.get(Campaign, campaign_id)


async def delete_campaign(db: Session, campaign: Campaign) -> None:
    campaign_id = campaign.id

    # Завершаем read-транзакцию до внешнего HTTP-запроса, чтобы не удерживать
    # соединение с БД, пока внешний API обрабатывает запрос.
    db.commit()
    async with TrainingApiClient() as api:
        await api.delete_campaign(campaign_id)
    db.delete(campaign)
    db.commit()

