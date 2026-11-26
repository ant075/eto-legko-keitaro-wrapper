from pydantic import AliasChoices, BaseModel, Field


class CountryResponse(BaseModel):
    code: str
    name_ru: str


class ExternalReferenceItem(BaseModel):
    id: int = Field(gt=0, validation_alias=AliasChoices("id", "offer_id"))
    name: str = Field(min_length=1)

