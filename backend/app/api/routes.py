from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.integrations.training_api import TrainingApiClient, TrainingApiError
from app.schemas.campaign import CampaignCreate, CampaignResponse
from app.schemas.reference import CountryResponse
from app.schemas.offer import AddOfferRequest, OfferOperationResponse, OfferSearchResponse
from app.services import campaigns
from app.services import countries
from app.services import offers
from app.services.references import reference_cache
from app.services.references import parse_reference_items, search_offers

router = APIRouter(prefix="/api")


@router.get("/countries", response_model=list[CountryResponse])
def list_countries(db: Session = Depends(get_db)):
    return countries.list_countries(db)


@router.get("/references/domains")
async def list_domains():
    async with TrainingApiClient() as api:
        return parse_reference_items(await reference_cache.get("domains", api.list_domains), "domains")


@router.get("/references/groups")
async def list_groups():
    async with TrainingApiClient() as api:
        return parse_reference_items(await reference_cache.get("groups", api.list_groups), "groups")


@router.get("/references/traffic-sources")
async def list_traffic_sources():
    async with TrainingApiClient() as api:
        return parse_reference_items(
            await reference_cache.get("traffic_sources", api.list_traffic_sources), "traffic_sources"
        )


@router.get("/references/offers")
async def list_offers():
    async with TrainingApiClient() as api:
        return parse_reference_items(await reference_cache.get("offers", api.list_offers), "offers")


@router.get("/references/offers/search")
async def search_reference_offers(q: str = Query(min_length=2)):
    async with TrainingApiClient() as api:
        return await search_offers(api, q)


@router.get("/campaigns", response_model=list[CampaignResponse])
def list_campaigns(db: Session = Depends(get_db)):
    return campaigns.list_campaigns(db)


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(data: CampaignCreate, db: Session = Depends(get_db)):
    try:
        return await campaigns.create_campaign(db, data)
    except campaigns.CampaignCreationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = campaigns.get_campaign(db, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    return campaign


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: int, db: Session = Depends(get_db)) -> None:
    campaign = campaigns.get_campaign(db, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    try:
        await campaigns.delete_campaign(db, campaign)
    except TrainingApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/campaigns/{campaign_id}/offers", response_model=OfferOperationResponse)
def list_campaign_offers(campaign_id: int, db: Session = Depends(get_db)):
    try:
        return offers.list_offers(db, campaign_id)
    except offers.OfferOperationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/offers", response_model=OfferOperationResponse)
def add_campaign_offer(campaign_id: int, data: AddOfferRequest, db: Session = Depends(get_db)):
    try:
        return offers.add_offer(db, campaign_id, data.offer_id, data.name)
    except offers.OfferOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/campaigns/{campaign_id}/offers/search", response_model=list[OfferSearchResponse])
async def search_campaign_offers(
    campaign_id: int,
    q: str = Query(min_length=2),
    db: Session = Depends(get_db),
):
    try:
        return await offers.search_available_offers(db, campaign_id, q)
    except offers.OfferOperationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/offers/{offer_id}/pin", response_model=OfferOperationResponse)
def pin_campaign_offer(campaign_id: int, offer_id: int, db: Session = Depends(get_db)):
    try:
        return offers.set_pinned(db, campaign_id, offer_id, True)
    except offers.OfferOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/offers/{offer_id}/unpin", response_model=OfferOperationResponse)
def unpin_campaign_offer(campaign_id: int, offer_id: int, db: Session = Depends(get_db)):
    try:
        return offers.set_pinned(db, campaign_id, offer_id, False)
    except offers.OfferOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/offers/{offer_id}/delete", response_model=OfferOperationResponse)
def delete_campaign_offer(campaign_id: int, offer_id: int, db: Session = Depends(get_db)):
    try:
        return offers.change_deleted(db, campaign_id, offer_id, True)
    except offers.OfferOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/offers/{offer_id}/restore", response_model=OfferOperationResponse)
def restore_campaign_offer(campaign_id: int, offer_id: int, db: Session = Depends(get_db)):
    try:
        return offers.change_deleted(db, campaign_id, offer_id, False)
    except offers.OfferOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/offers/publish", response_model=OfferOperationResponse)
async def publish_campaign_offers(campaign_id: int, db: Session = Depends(get_db)):
    try:
        return await offers.publish(db, campaign_id)
    except offers.OfferOperationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/offers/cancel", response_model=OfferOperationResponse)
def cancel_campaign_offers(campaign_id: int, db: Session = Depends(get_db)):
    try:
        return offers.cancel(db, campaign_id)
    except offers.OfferOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/offers/sync", response_model=OfferOperationResponse)
async def sync_campaign_offers(campaign_id: int, db: Session = Depends(get_db)):
    try:
        return await offers.sync_from_training_api(db, campaign_id)
    except offers.OfferOperationError as exc:
        status_code = 400 if "неподтверждёнными изменениями" in str(exc) else 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

