from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExternalImportModel(BaseModel):
    """Base model for responses from the training API.

    The API returns additional metadata (timestamps, internal IDs of nested
    objects, and so on). Import only needs a subset of those fields.
    """

    model_config = ConfigDict(extra="ignore")


class ExternalImportCampaign(ExternalImportModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    alias: str | None = None
    group_id: int = Field(gt=0)
    traffic_source_id: int = Field(gt=0)
    domain_id: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime


class ExternalImportFilter(ExternalImportModel):
    name: str
    mode: str
    payload: list[str]


class ExternalImportOffer(ExternalImportModel):
    offer_id: int = Field(gt=0)
    share: int = Field(ge=0, le=100)
    state: str
    name: str | None = None


class ExternalImportStream(ExternalImportModel):
    id: int = Field(gt=0)
    campaign_id: int = Field(gt=0)
    position: int | None = Field(default=None, gt=0)
    type: str
    state: str
    schema_name: str = Field(alias="schema")
    action_type: str
    action_payload: str | None = None
    collect_clicks: bool
    filter_or: bool
    offer_selection: str
    filters: list[ExternalImportFilter]
    offers: list[ExternalImportOffer]


class CampaignImportResponse(BaseModel):
    imported_count: int = Field(ge=0)
    message: str | None = None
