from pydantic import BaseModel, ConfigDict, Field


class AddOfferRequest(BaseModel):
    offer_id: int
    name: str = Field(min_length=1, max_length=255)


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

