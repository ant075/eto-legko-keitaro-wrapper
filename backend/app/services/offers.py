from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.integrations.training_api import TrainingApiClient, TrainingApiError
from app.models import Campaign, CampaignOffer, CampaignOfferPublication
from app.schemas.offer import OfferOperationResponse, OfferResponse, OfferSearchResponse
from app.services.references import reference_cache


class OfferOperationError(RuntimeError):
    pass


def _offer_rows(db: Session, campaign_id: int) -> list[CampaignOffer]:
    return list(db.scalars(
        select(CampaignOffer)
        .where(CampaignOffer.campaign_id == campaign_id)
        .order_by(CampaignOffer.is_deleted, CampaignOffer.position)))


def _response(campaign: Campaign, offers: Iterable[CampaignOffer]) -> OfferOperationResponse:
    return OfferOperationResponse(
        campaign_id=campaign.id,
        is_dirty=campaign.is_dirty,
        offers=[OfferResponse.model_validate(offer) for offer in offers],
    )


def _recalculate_weights(offers: list[CampaignOffer]) -> None:
    active_pinned = [offer for offer in offers if not offer.is_deleted and offer.is_pinned]
    active_unpinned = [offer for offer in offers if not offer.is_deleted and not offer.is_pinned]
    pinned_weight = sum(offer.weight for offer in active_pinned)

    for offer in offers:
        if offer.is_deleted:
            offer.weight = 0

    if not active_unpinned:
        return

    remaining = max(0, 100 - pinned_weight)
    common_weight = remaining // len(active_unpinned)
    first_weight = remaining - common_weight * (len(active_unpinned) - 1)
    active_unpinned[0].weight = first_weight
    for offer in active_unpinned[1:]:
        offer.weight = common_weight


def _require_campaign(db: Session, campaign_id: int) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise OfferOperationError("Кампания не найдена")
    return campaign


def _require_campaign_for_update(db: Session, campaign_id: int) -> Campaign:
    campaign = db.scalar(
        select(Campaign)
        .where(Campaign.id == campaign_id)
        .with_for_update(of=Campaign)
    )
    if campaign is None:
        raise OfferOperationError("Кампания не найдена")
    return campaign


def list_offers(db: Session, campaign_id: int) -> OfferOperationResponse:
    campaign = _require_campaign(db, campaign_id)
    return _response(campaign, _offer_rows(db, campaign_id))


async def search_available_offers(db: Session, campaign_id: int, query: str) -> list[OfferSearchResponse]:
    if len(query.strip()) < 2:
        return []
    _require_campaign(db, campaign_id)
    used_ids = {item.offer_id for item in _offer_rows(db, campaign_id)}
    async with TrainingApiClient() as api:
        try:
            raw_offers = await reference_cache.get("offers", api.list_offers)
        except TrainingApiError as exc:
            raise OfferOperationError("Не удалось получить список офферов из API учебного стенда") from exc
    if isinstance(raw_offers, dict):
        raw_offers = raw_offers.get("offers", [])
    needle = query.strip().casefold()
    result = []
    for item in raw_offers:
        offer_id = item.get("id", item.get("offer_id"))
        name = str(item.get("name", ""))
        if offer_id is not None and int(offer_id) not in used_ids and needle in name.casefold():
            result.append(OfferSearchResponse(offer_id=int(offer_id), name=name))
    return result


def set_pinned(db: Session, campaign_id: int, offer_id: int, is_pinned: bool) -> OfferOperationResponse:
    campaign = _require_campaign_for_update(db, campaign_id)
    offer = db.get(CampaignOffer, (campaign_id, offer_id))
    if offer is None:
        raise OfferOperationError("Оффер не найден в кампании")
    if offer.is_deleted:
        raise OfferOperationError("Удалённый оффер нельзя запинить")
    offer.is_pinned = is_pinned
    db.commit()
    return _response(campaign, _offer_rows(db, campaign_id))


def change_deleted(db: Session, campaign_id: int, offer_id: int, is_deleted: bool) -> OfferOperationResponse:
    campaign = _require_campaign_for_update(db, campaign_id)
    offer = db.get(CampaignOffer, (campaign_id, offer_id))
    if offer is None:
        raise OfferOperationError("Оффер не найден в кампании")
    offer.is_deleted = is_deleted
    if is_deleted:
        offer.weight = 0
        offer.is_pinned = False
    _recalculate_weights(_offer_rows(db, campaign_id))
    campaign.is_dirty = True
    db.commit()
    return _response(campaign, _offer_rows(db, campaign_id))


def add_offer(db: Session, campaign_id: int, offer_id: int, name: str) -> OfferOperationResponse:
    campaign = _require_campaign_for_update(db, campaign_id)
    if db.get(CampaignOffer, (campaign_id, offer_id)) is not None:
        raise OfferOperationError("Оффер уже есть в кампании")
    current = _offer_rows(db, campaign_id)
    offer = CampaignOffer(
        campaign_id=campaign_id,
        offer_id=offer_id,
        name=name,
        weight=0,
        is_pinned=False,
        is_deleted=False,
        position=max((item.position for item in current), default=0) + 1,
    )
    db.add(offer)
    current.append(offer)
    _recalculate_weights(current)
    campaign.is_dirty = True
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise OfferOperationError("Оффер уже добавляется или уже есть в кампании") from exc
    return _response(campaign, _offer_rows(db, campaign_id))


def _replace_publication_snapshot(db: Session, campaign: Campaign, offers: list[CampaignOffer]) -> None:
    db.execute(delete(CampaignOfferPublication).where(CampaignOfferPublication.campaign_id == campaign.id))
    db.flush()
    for offer in offers:
        db.add(CampaignOfferPublication(
            campaign_id=campaign.id,
            offer_id=offer.offer_id,
            name=offer.name,
            weight=offer.weight,
            is_deleted=offer.is_deleted,
            position=offer.position,
        ))


async def publish(db: Session, campaign_id: int) -> OfferOperationResponse:
    campaign = _require_campaign(db, campaign_id)
    offers = _offer_rows(db, campaign_id)
    stream_id = campaign.offers_stream_id
    payload = {
        "filters": [],
        "offers": [{"offer_id": item.offer_id, "share": item.weight, "state": "active"}
                   for item in offers if not item.is_deleted],
    }

    # Завершаем read-транзакцию до внешнего HTTP-запроса, чтобы не удерживать
    # соединение с БД, пока внешний API обрабатывает запрос. При
    # expire_on_commit=False загруженные объекты остаются доступными в памяти.
    db.commit()
    async with TrainingApiClient() as api:
        try:
            await api.update_stream(stream_id, payload)
        except TrainingApiError as exc:
            raise OfferOperationError("Не удалось опубликовать офферы в API учебного стенда") from exc

    # Конкурентные изменения для кампании не поддерживаются: предполагается,
    # что с одной кампанией одновременно работает только один пользователь.
    _replace_publication_snapshot(db, campaign, offers)
    campaign.is_dirty = False
    db.commit()
    return _response(campaign, offers)


def cancel(db: Session, campaign_id: int) -> OfferOperationResponse:
    campaign = _require_campaign_for_update(db, campaign_id)
    snapshots = list(
        db.scalars(select(CampaignOfferPublication).where(CampaignOfferPublication.campaign_id == campaign_id)))
    snapshot_ids = {item.offer_id for item in snapshots}
    for offer in _offer_rows(db, campaign_id):
        if offer.offer_id not in snapshot_ids:
            db.delete(offer)
    db.flush()
    for snapshot in snapshots:
        offer = db.get(CampaignOffer, (campaign_id, snapshot.offer_id))
        offer.name = snapshot.name
        offer.weight = snapshot.weight
        offer.is_deleted = snapshot.is_deleted
        offer.position = snapshot.position
    campaign.is_dirty = False
    db.commit()
    return _response(campaign, _offer_rows(db, campaign_id))


async def sync_from_training_api(db: Session, campaign_id: int) -> OfferOperationResponse:
    campaign = _require_campaign(db, campaign_id)
    if campaign.is_dirty:
        raise OfferOperationError("Нельзя синхронизировать кампанию с неподтверждёнными изменениями")
    stream_id = campaign.offers_stream_id
    offers = _offer_rows(db, campaign_id)

    # Завершаем read-транзакцию до внешнего HTTP-запроса, чтобы не удерживать
    # соединение с БД, пока внешний API обрабатывает запрос. При
    # expire_on_commit=False загруженные объекты остаются доступными в памяти.
    db.commit()
    async with TrainingApiClient() as api:
        try:
            stream = await api.get_stream(stream_id)
        except TrainingApiError as exc:
            raise OfferOperationError("Не удалось получить поток из API учебного стенда") from exc
    current = {offer.offer_id: offer for offer in offers}
    seen: set[int] = set()
    for position, external in enumerate(stream.get("offers", []), start=1):
        offer_id = int(external["offer_id"])
        seen.add(offer_id)
        offer = current.get(offer_id)
        if offer is None:
            offer = CampaignOffer(campaign_id=campaign_id, offer_id=offer_id, name=str(offer_id), position=position,
                                  is_pinned=False, is_deleted=False, weight=0)
            db.add(offer)
            current[offer_id] = offer
            was_pinned = False
            previous_weight = None
        else:
            was_pinned = offer.is_pinned
            previous_weight = offer.weight
        offer.name = str(external.get("name", offer.name))
        external_weight = int(external.get("share", 0))
        offer.is_pinned = was_pinned and previous_weight == external_weight
        offer.weight = external_weight
        offer.position = position
        offer.is_deleted = False
    for offer_id, offer in current.items():
        if offer_id not in seen:
            offer.is_deleted = True
            offer.weight = 0
            offer.is_pinned = False
    offers = sorted(current.values(), key=lambda offer: (offer.is_deleted, offer.position))
    db.flush()
    _replace_publication_snapshot(db, campaign, offers)
    campaign.is_dirty = False
    db.commit()
    return _response(campaign, offers)
