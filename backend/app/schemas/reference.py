from pydantic import BaseModel


class CountryResponse(BaseModel):
    code: str
    name_ru: str

