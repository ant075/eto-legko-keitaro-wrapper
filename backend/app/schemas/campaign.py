from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain_id: int
    group_id: int
    traffic_source_id: int
    country_code: str = Field(min_length=2, max_length=2)
    offer_id: int


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    alias: str | None
    group_id: int
    traffic_source_id: int
    domain_id: int
    redirect_stream_id: int
    offers_stream_id: int
    country_code: str
    country_name: str
    is_dirty: bool
    created_at: datetime
    updated_at: datetime

