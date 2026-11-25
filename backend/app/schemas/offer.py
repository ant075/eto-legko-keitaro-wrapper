from pydantic import BaseModel, ConfigDict, Field


class AddOfferRequest(BaseModel):
    offer_id: int


class OfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    campaign_id: int
    offer_id: int
    name: str
    weight: int
    is_pinned: bool
    is_deleted: bool
    position: int


class OfferSearchResponse(BaseModel):
    offer_id: int
    name: str


class OfferOperationResponse(BaseModel):
    campaign_id: int
    is_dirty: bool
    offers: list[OfferResponse]

