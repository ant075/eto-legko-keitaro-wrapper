from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.integrations.training_api import TrainingApiClient, TrainingApiError
from app.models import Country
from app.schemas.campaign import CampaignCreate, CampaignResponse
from app.schemas.reference import CountryResponse
from app.services import campaigns

router = APIRouter(prefix="/api")


@router.get("/countries", response_model=list[CountryResponse])
def list_countries(db: Session = Depends(get_db)) -> list[Country]:
    return list(db.scalars(select(Country).order_by(Country.name_ru)))


@router.get("/references/domains")
async def list_domains():
    async with TrainingApiClient() as api:
        return await api.list_domains()


@router.get("/references/groups")
async def list_groups():
    async with TrainingApiClient() as api:
        return await api.list_groups()


@router.get("/references/traffic-sources")
async def list_traffic_sources():
    async with TrainingApiClient() as api:
        return await api.list_traffic_sources()


@router.get("/references/offers")
async def list_offers():
    async with TrainingApiClient() as api:
        return await api.list_offers()


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

